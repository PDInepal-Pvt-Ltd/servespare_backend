from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import date
from apps.subscription.models import Subscription
from apps.subscription.serializers import SubscriptionSerializer
from apps.base.drf import TenantViewSetMixin


class SubscriptionViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing subscriptions
    """
    queryset = Subscription.objects.select_related('tenant', 'subscription_plan').all()
    serializer_class = SubscriptionSerializer
    
    def get_queryset(self):
        """
        Optionally filter by tenant, subscription_plan, or date ranges
        """
        queryset = Subscription.objects.select_related('tenant', 'subscription_plan').all()
        
        # Filter by tenant
        tenant_id = self.request.query_params.get('tenant', None)
        if tenant_id is not None:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Filter by subscription_plan
        plan_id = self.request.query_params.get('plan', None)
        if plan_id is not None:
            queryset = queryset.filter(subscription_plan_id=plan_id)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Filter by active subscriptions (not expired)
        active_only = self.request.query_params.get('active_only', None)
        if active_only and active_only.lower() == 'true':
            today = date.today()
            queryset = queryset.filter(
                subscription_date__lte=today,
                finish_date__gte=today
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active (non-expired) subscriptions
        """
        today = date.today()
        active_subscriptions = self.filter_queryset(Subscription.objects.filter(
            is_active=True,
            subscription_date__lte=today,
            finish_date__gte=today
        ).select_related('tenant', 'subscription_plan'))

        serializer = self.get_serializer(active_subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """
        Get all expired subscriptions
        """
        today = date.today()
        expired_subscriptions = self.filter_queryset(Subscription.objects.filter(
            finish_date__lt=today
        ).select_related('tenant', 'subscription_plan'))

        serializer = self.get_serializer(expired_subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_tenant(self, request):
        """
        Get subscriptions grouped by tenant
        """
        tenant_id = request.query_params.get('tenant_id', None)
        if not tenant_id:
            return Response(
                {'error': 'tenant_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscriptions = self.filter_queryset(Subscription.objects.filter(
            tenant_id=tenant_id
        ).select_related('tenant', 'subscription_plan'))

        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)

