from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources
from apps.cashandbank.models import Cheque
from apps.cashandbank.serializers import ChequeSerializer


class ChequeViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Cheque records"""
    queryset = Cheque.objects.filter(deleted_at__isnull=True)
    serializer_class = ChequeSerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Cheque.objects.filter(deleted_at__isnull=True)
        # Optional filters: type, party_name, bank_name
        cheque_type = self.request.query_params.get('cheque_type')
        if cheque_type:
            qs = qs.filter(cheque_type=cheque_type)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                party_name__icontains=search
            )

        return qs
