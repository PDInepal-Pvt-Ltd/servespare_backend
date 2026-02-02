"""
Dashboard Views for analytics and admin dashboard data
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now

from apps.base.dashboard_service import DashboardService
from apps.base.dashboard_serializers import (
    CompleteDashboardSerializer,
    TodaySalesSerializer,
    QuickStatsSerializer,
    RevenueAnalysisDataSerializer,
    RevenueByCategorySerializer,
    StockFlowSerializer,
    LowStockAlertSerializer,
    PendingOrderSerializer,
    ActiveCustomerSerializer,
    TotalInventoryValueSerializer,
)
from apps.base.drf import TenantViewSetMixin
from apps.users.models import User


class DashboardViewSet(TenantViewSetMixin, viewsets.ViewSet):
    """
    Dashboard ViewSet for admin analytics
    
    Endpoints:
    - GET /api/dashboard/complete/ - Full dashboard data
    - GET /api/dashboard/today-sales/ - Today's sales
    - GET /api/dashboard/quick-stats/ - Quick statistics cards
    - GET /api/dashboard/revenue-analysis/ - Revenue graph data
    - GET /api/dashboard/revenue-by-category/ - Revenue breakdown by category
    - GET /api/dashboard/stock-flow/ - Stock inbound/outbound flow
    - GET /api/dashboard/low-stock-alerts/ - Low stock alerts
    - GET /api/dashboard/pending-orders/ - Pending orders list
    - GET /api/dashboard/active-customers/ - Active customers
    - GET /api/dashboard/inventory-value/ - Total inventory value
    
    Query Parameters:
    - days: Number of days for historical data (default: 30)
    - branch: Branch ID to filter data by specific branch
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        """Add tenant and branch context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def _get_tenant_and_branch(self):
        """Get tenant and branch from request context - TENANT-BASED DATA"""
        # Get tenant from authenticated user
        tenant = getattr(self.request.user, 'tenant', None)
        
        if not tenant:
            # Super admin can optionally filter by tenant_id param
            tenant_id = self.request.query_params.get('tenant_id')
            if tenant_id:
                from apps.tenant.models import Tenant
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                except Tenant.DoesNotExist:
                    tenant = None
        
        # Get branch from query params or user's branch
        branch_id = self.request.query_params.get('branch')
        branch = None
        if branch_id:
            # Validate branch belongs to tenant
            from apps.branch.models import Branch
            try:
                branch_obj = Branch.objects.get(id=branch_id)
                # Check if branch belongs to this tenant
                if tenant and branch_obj.tenant == tenant:
                    branch = branch_obj
                elif not tenant:
                    branch = branch_obj
            except Branch.DoesNotExist:
                branch = None
        
        # Only admin and management staff can see full dashboard
        # Customers can only see their own data (limited)
        user_role = getattr(self.request.user, 'role', None)
        if user_role == User.Role.CUSTOMER:
            # Customers get empty dashboard
            return None, None
        
        return tenant, branch
    
    @action(detail=False, methods=['get'])
    def complete(self, request):
        """Get complete dashboard data with all metrics"""
        tenant, branch = self._get_tenant_and_branch()
        days = int(request.query_params.get('days', 30))
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_complete_dashboard_data(days=days)
        
        serializer = CompleteDashboardSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def today_sales(self, request):
        """Get today's sales statistics"""
        tenant, branch = self._get_tenant_and_branch()
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_today_sales()
        
        serializer = TodaySalesSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def quick_stats(self, request):
        """Get quick statistics for dashboard cards"""
        tenant, branch = self._get_tenant_and_branch()
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_quick_stats()
        
        serializer = QuickStatsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def revenue_analysis(self, request):
        """Get revenue analysis data for graph"""
        tenant, branch = self._get_tenant_and_branch()
        days = int(request.query_params.get('days', 30))
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_revenue_analysis(days=days)
        
        serializer = RevenueAnalysisDataSerializer(data, many=True)
        return Response({
            'revenue_data': serializer.data,
            'period_days': days,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def revenue_by_category(self, request):
        """Get revenue breakdown by category"""
        tenant, branch = self._get_tenant_and_branch()
        days = int(request.query_params.get('days', 30))
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_revenue_by_category(days=days)
        
        serializer = RevenueByCategorySerializer(data, many=True)
        return Response({
            'revenue_by_category': serializer.data,
            'period_days': days,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def stock_flow(self, request):
        """Get stock flow (inbound/outbound)"""
        tenant, branch = self._get_tenant_and_branch()
        days = int(request.query_params.get('days', 30))
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_stock_flow(days=days)
        
        serializer = StockFlowSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """Get low stock alerts"""
        tenant, branch = self._get_tenant_and_branch()
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_low_stock_alerts()
        
        serializer = LowStockAlertSerializer(data, many=True)
        return Response({
            'alerts': serializer.data,
            'critical_count': len([a for a in data if a['status'] == 'critical']),
            'warning_count': len([a for a in data if a['status'] == 'warning']),
            'total_count': len(data),
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def pending_orders(self, request):
        """Get pending orders"""
        tenant, branch = self._get_tenant_and_branch()
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_pending_orders()
        
        serializer = PendingOrderSerializer(data, many=True)
        return Response({
            'pending_orders': serializer.data,
            'total_pending': len(data),
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def active_customers(self, request):
        """Get active customers"""
        tenant, branch = self._get_tenant_and_branch()
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_active_customers(days=days, limit=limit)
        
        serializer = ActiveCustomerSerializer(data, many=True)
        return Response({
            'active_customers': serializer.data,
            'period_days': days,
            'limit': limit,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def inventory_value(self, request):
        """Get total inventory value"""
        tenant, branch = self._get_tenant_and_branch()
        
        service = DashboardService(tenant=tenant, branch=branch)
        data = service.get_total_inventory_value()
        
        serializer = TotalInventoryValueSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Override list to prevent default behavior
    def list(self, request):
        """Redirect to complete dashboard"""
        return self.complete(request)
