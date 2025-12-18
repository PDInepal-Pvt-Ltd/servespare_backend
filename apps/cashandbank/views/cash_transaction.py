from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.cashandbank.models import CashTransaction
from apps.cashandbank.serializers import CashTransactionSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.permissions import CanManageBranchResources
from apps.base.permission_utils import get_branch_queryset_for_user


class CashTransactionViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing cash transactions with branch-level access control.
    
    Permissions:
    - Super Admin: Can manage transactions in all branches
    - Tenant Admin: Can manage transactions in all branches of their tenant
    - Cashier: Can manage transactions only in their assigned branch
    - Others: No access
    """
    queryset = CashTransaction.objects.all()
    serializer_class = CashTransactionSerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]

    def get_queryset(self):
        """
        Filter transactions based on user's role and branch access.
        
        - Super Admin: See all transactions
        - Tenant Admin: See transactions from all branches in their tenant
        - Cashier: See only transactions in their branch
        """
        qs = CashTransaction.objects.all()
        
        # Apply branch-level filtering based on user role
        qs = get_branch_queryset_for_user(self.request.user, qs)
        
        # Filters
        ttype = self.request.query_params.get('transaction_type')
        if ttype:
            qs = qs.filter(transaction_type=ttype)

        # Date range filter: ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(transaction_date__date__gte=date_from)
        if date_to:
            qs = qs.filter(transaction_date__date__lte=date_to)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(source_description__icontains=search))

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            qs = qs.filter(is_active=is_active_bool)

        return qs

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Return total balance with optional same filters as list."""
        qs = self.get_queryset()
        total = qs.total_balance()
        return Response({'total': total})
