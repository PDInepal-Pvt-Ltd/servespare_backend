from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

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
