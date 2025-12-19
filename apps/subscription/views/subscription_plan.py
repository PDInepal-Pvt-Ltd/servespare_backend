from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.subscription.models import SubscriptionPlan
from apps.subscription.serializers import SubscriptionPlanSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import IsSuperAdmin


class SubscriptionPlanViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing subscription plans (Super Admin only)
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Optionally filter by is_active status
        """
        queryset = SubscriptionPlan.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active subscription plans
        """
        active_plans = self.filter_queryset(SubscriptionPlan.objects.filter(is_active=True))
        serializer = self.get_serializer(active_plans, many=True)
        return Response(serializer.data)

