from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.tenant.models import Tenant
from apps.tenant.serializers import TenantSerializer
from django.db.models import Count


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants
    """
    queryset = Tenant.objects.select_related('package').all()
    serializer_class = TenantSerializer
    
    def get_queryset(self):
        """
        Optionally filter by status, package, or is_active
        """
        queryset = Tenant.objects.select_related('package').all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by package
        package_id = self.request.query_params.get('package', None)
        if package_id is not None:
            queryset = queryset.filter(package_id=package_id)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Search by business name or email
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                business_name__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active tenants
        """
        active_tenants = Tenant.objects.filter(
            is_active=True,
            status='active'
        ).select_related('package')
        
        serializer = self.get_serializer(active_tenants, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """
        Get tenants grouped by status
        """
        status_filter = request.query_params.get('status', None)
        if not status_filter:
            return Response(
                {'error': 'status parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tenants = Tenant.objects.filter(
            status=status_filter
        ).select_related('package')
        
        serializer = self.get_serializer(tenants, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trial(self, request):
        """
        Get all trial tenants
        """
        trial_tenants = Tenant.objects.filter(
            status='trial'
        ).select_related('package')
        
        serializer = self.get_serializer(trial_tenants, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def counts(self, request):
        """
        Get counts of tenants grouped by status, or a single status via `?status=`.
        """
        status_filter = request.query_params.get('status', None)
        qs = Tenant.objects.all()

        if status_filter:
            count = qs.filter(status=status_filter).count()
            return Response({'status': status_filter, 'count': count})

        counts = qs.values('status').annotate(count=Count('id'))
        return Response({item['status']: item['count'] for item in counts})

