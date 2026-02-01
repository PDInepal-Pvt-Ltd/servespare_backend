from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.cashandbank.models import CashBalance
from apps.cashandbank.serializers import CashBalanceSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources


class CashBalanceViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = CashBalance.objects.select_related('tenant', 'branch').all()
    serializer_class = CashBalanceSerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = CashBalance.objects.select_related('tenant', 'branch').all()
        
        # Filter by branch
        branch_id = self.request.query_params.get('branch', None)
        if branch_id is not None:
            qs = qs.filter(branch_id=branch_id)
        
        # tenant/branch filtering applied by TenantViewSetMixin if available
        return self.filter_queryset(qs)
