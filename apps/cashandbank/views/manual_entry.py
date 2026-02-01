from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.cashandbank.models import ManualEntry
from apps.cashandbank.serializers import ManualEntrySerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources


class ManualEntryViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = ManualEntry.objects.select_related('tenant', 'branch').all()
    serializer_class = ManualEntrySerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = ManualEntry.objects.select_related('tenant', 'branch').all()
        
        # Filter by branch
        branch_id = self.request.query_params.get('branch', None)
        if branch_id is not None:
            qs = qs.filter(branch_id=branch_id)
        
        qs = self.filter_queryset(qs)

        # basic search by description
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(description__icontains=search)

        return qs
