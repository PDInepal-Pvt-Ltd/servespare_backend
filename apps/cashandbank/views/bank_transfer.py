from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cashandbank.models import BankTransfer
from apps.cashandbank.serializers import BankTransferSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources


class BankTransferViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = BankTransfer.objects.all()
    serializer_class = BankTransferSerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = BankTransfer.objects.all()
        # Optionally filter by branch or bank_account
        branch = self.request.query_params.get('branch')
        if branch:
            qs = qs.filter(branch_id=branch)
        bank_account = self.request.query_params.get('bank_account')
        if bank_account:
            qs = qs.filter(bank_account_id=bank_account)
        return qs
