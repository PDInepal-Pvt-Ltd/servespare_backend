from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from apps.base.permissions import IsSuperAdmin
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
	"""Superadmin-only audit log list/retrieve with filtering and export."""

	queryset = AuditLog.objects.all().select_related('user', 'tenant')
	serializer_class = AuditLogSerializer
	permission_classes = [IsSuperAdmin]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['action', 'entity', 'method', 'status_code', 'tenant', 'user']
	search_fields = ['path', 'entity', 'user__username', 'tenant__business_name', 'ip_address', 'user_agent']
	ordering_fields = ['created', 'status_code', 'method', 'action']
	ordering = ['-created']

	@action(detail=False, methods=['get'], url_path='export')
	def export(self, request):
		"""
		Export audit logs as CSV. Supports same filters via query params.
		"""
		import csv
		from io import StringIO

		qs = self.filter_queryset(self.get_queryset())
		# cap export size to prevent huge downloads
		limit = int(request.query_params.get('limit', 5000))
		qs = qs[:max(0, min(limit, 10000))]

		buffer = StringIO()
		writer = csv.writer(buffer)
		writer.writerow([
			'created', 'user', 'tenant', 'action', 'entity', 'object_id',
			'method', 'path', 'status_code', 'ip_address', 'user_agent'
		])
		for row in qs:
			writer.writerow([
				row.created.isoformat(),
				getattr(row.user, 'username', ''),
				getattr(row.tenant, 'business_name', ''),
				row.action,
				row.entity or '',
				row.object_id or '',
				row.method,
				row.path,
				row.status_code or '',
				row.ip_address or '',
				(row.user_agent or '')[:120],
			])

		buffer.seek(0)
		return Response(
			buffer.getvalue(),
			status=status.HTTP_200_OK,
			content_type='text/csv'
		)

	@action(detail=False, methods=['get'], url_path='statistics')
	def statistics(self, request):
		"""
		Get audit log statistics with filtering options.
		
		Query Parameters:
		- time_range: 'today', 'week', 'month', 'year' (default: all)
		- entity: Filter by entity (e.g., 'inventory', 'user')
		- user: Filter by user ID
		- status_code: Filter by HTTP status code
		- action: Filter by action type
		- tenant: Filter by tenant ID
		"""
		qs = self.filter_queryset(self.get_queryset())
		now = timezone.now()
		
		# Time range filtering
		time_range = request.query_params.get('time_range', 'all')
		if time_range == 'today':
			qs = qs.filter(created__date=now.date())
		elif time_range == 'week':
			qs = qs.filter(created__gte=now - timedelta(days=7))
		elif time_range == 'month':
			qs = qs.filter(created__gte=now - timedelta(days=30))
		elif time_range == 'year':
			qs = qs.filter(created__gte=now - timedelta(days=365))
		
		# Calculate statistics
		total_activities = qs.count()
		successful_activities = qs.filter(
			Q(status_code__gte=200) & Q(status_code__lt=300)
		).count()
		failed_activities = qs.exclude(
			Q(status_code__gte=200) & Q(status_code__lt=300)
		).count()
		
		# Today's activities
		today_activities = AuditLog.objects.filter(
			created__date=now.date()
		).count() if not time_range or time_range == 'today' else None
		
		# Breakdown by status
		status_breakdown = qs.values('status_code').annotate(
			count=Count('id')
		).order_by('-count')
		
		# Breakdown by action
		action_breakdown = qs.values('action').annotate(
			count=Count('id')
		).order_by('-count')
		
		# Breakdown by entity/module
		entity_breakdown = qs.values('entity').annotate(
			count=Count('id')
		).order_by('-count')
		
		# Breakdown by user
		user_breakdown = qs.values('user__username').annotate(
			count=Count('id')
		).order_by('-count')[:10]  # Top 10 users
		
		# Breakdown by method
		method_breakdown = qs.values('method').annotate(
			count=Count('id')
		).order_by('-count')
		
		# Daily activity for the time range
		daily_breakdown = qs.extra(
			select={'date': 'DATE(created)'}
		).values('date').annotate(
			count=Count('id')
		).order_by('-date')[:30]  # Last 30 days max
		
		return Response({
			'summary': {
				'total_activities': total_activities,
				'successful_activities': successful_activities,
				'failed_activities': failed_activities,
				'success_rate': round(
					(successful_activities / total_activities * 100) if total_activities > 0 else 0, 2
				),
				'today_activities': today_activities,
				'time_range': time_range,
			},
			'breakdown': {
				'by_status': list(status_breakdown),
				'by_action': list(action_breakdown),
				'by_module': list(entity_breakdown),
				'by_user': list(user_breakdown),
				'by_method': list(method_breakdown),
				'daily': list(daily_breakdown),
			}
		}, status=status.HTTP_200_OK)
