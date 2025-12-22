from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import date
import calendar
from apps.subscription.models import Subscription
from apps.subscription.serializers import SubscriptionSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import IsSuperAdminOrTenantAdmin
from apps.base.permission_utils import get_tenant_queryset_for_user


class SubscriptionViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing subscriptions with RBAC
    """
    queryset = Subscription.objects.select_related('tenant', 'subscription_plan').all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
    pagination_class = StandardResultsSetPagination
    
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

    def _add_months(self, original_date: date, months: int) -> date:
        """Add months to a date, handling month overflow and end-of-month."""
        if original_date is None:
            return None
        year = original_date.year
        month = original_date.month + months
        year += (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = original_date.day
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)
        return date(year, month, day)
    
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

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew a single subscription by a number of months.

        Request body should include JSON: {"months": 6} where months is one of [6,12,24].
        """
        subscription = self.get_object()
        months = request.data.get('months')
        try:
            months = int(months)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid 'months' value."}, status=status.HTTP_400_BAD_REQUEST)

        if months not in (6, 12, 24):
            return Response({"detail": "Allowed months are 6, 12, or 24."}, status=status.HTTP_400_BAD_REQUEST)

        base_date = subscription.finish_date or subscription.subscription_date
        if not base_date:
            return Response({"detail": "Subscription has no valid base date to renew from."}, status=status.HTTP_400_BAD_REQUEST)

        subscription.finish_date = self._add_months(base_date, months)
        subscription.save()

        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def change_plan(self, request):
        """Change the active subscription plan for a tenant.

        Request JSON: {
            "tenant_id": <int>,
            "new_plan_id": <int>,
            "months": <int, optional>  # length of new subscription in months (default 12)
        }

        Behavior:
        - Deactivates the tenant's current active subscription (if any).
        - Creates a new Subscription starting today for the given months.
        """
        from apps.tenant.models import Tenant
        from apps.subscription.models import SubscriptionPlan

        tenant_id = request.data.get('tenant_id')
        new_plan_id = request.data.get('new_plan_id')
        months = request.data.get('months', 12)

        if not tenant_id or not new_plan_id:
            return Response({"detail": "Both 'tenant_id' and 'new_plan_id' are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            months = int(months)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid 'months' value."}, status=status.HTTP_400_BAD_REQUEST)

        if months <= 0:
            return Response({"detail": "'months' must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tenant = Tenant.objects.get(pk=tenant_id)
        except Tenant.DoesNotExist:
            return Response({"detail": "Tenant not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            plan = SubscriptionPlan.objects.get(pk=new_plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"detail": "Subscription plan not found."}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()

        # Deactivate any currently active subscription for the tenant
        active_sub = Subscription.objects.filter(
            tenant=tenant,
            is_active=True,
            subscription_date__lte=today,
            finish_date__gte=today
        ).first()

        if active_sub:
            active_sub.is_active = False
            active_sub.save()

        # Create new subscription starting today — reuse existing same-day record if present
        finish_date = self._add_months(today, months)

        existing_same_day = Subscription.objects.filter(
            tenant=tenant,
            subscription_plan=plan,
            subscription_date=today
        ).first()

        if existing_same_day:
            # Update existing record instead of creating a duplicate
            existing_same_day.finish_date = finish_date
            existing_same_day.is_active = True
            existing_same_day.save()
            new_subscription = existing_same_day
        else:
            new_subscription = Subscription.objects.create(
                tenant=tenant,
                subscription_plan=plan,
                subscription_date=today,
                finish_date=finish_date
            )

        serializer = self.get_serializer(new_subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

