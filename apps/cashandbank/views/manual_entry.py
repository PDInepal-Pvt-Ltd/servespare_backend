from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.cashandbank.models import ManualEntry
from apps.cashandbank.serializers import ManualEntrySerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources


class ManualEntryViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = ManualEntry.objects.filter(deleted_at__isnull=True).select_related('tenant', 'branch')
    serializer_class = ManualEntrySerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = ManualEntry.objects.filter(deleted_at__isnull=True).select_related('tenant', 'branch')
        qs = self.filter_queryset(qs)

        # basic search by description
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(description__icontains=search)

        return qs
