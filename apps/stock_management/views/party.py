from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.stock_management.models import Party
from apps.stock_management.serializers import PartySerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.permission_utils import get_tenant_queryset_for_user
from apps.base.pagination import StandardResultsSetPagination


class PartyViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing parties (suppliers and customers) with RBAC (all authenticated users)
    """
    queryset = Party.objects.filter(deleted_at__isnull=True)
    serializer_class = PartySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Optionally filter by party_type, customer_type, or is_active
        """
        queryset = Party.objects.filter(deleted_at__isnull=True)
        
        # Filter by party_type
        party_type = self.request.query_params.get('party_type', None)
        if party_type is not None:
            queryset = queryset.filter(party_type=party_type)
        
        # Filter by customer_type
        customer_type = self.request.query_params.get('customer_type', None)
        if customer_type is not None:
            queryset = queryset.filter(customer_type=customer_type)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(party_name__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def suppliers(self, request):
        """Get all suppliers. Allow access for super admin, tenant admin, and inventory manager."""
        from apps.users.models import User

        if not (request.user and request.user.is_authenticated):
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in [User.Role.SUPER_ADMIN, User.Role.ADMIN, User.Role.INVENTORY_MANAGER]:
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        suppliers = self.filter_queryset(Party.objects.filter(party_type='supplier', is_active=True))
        serializer = self.get_serializer(suppliers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def customers(self, request):
        """Get all customers. Allow access for super admin, tenant admin, and inventory manager."""
        from apps.users.models import User

        if not (request.user and request.user.is_authenticated):
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in [User.Role.SUPER_ADMIN, User.Role.ADMIN, User.Role.INVENTORY_MANAGER]:
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        customers = self.filter_queryset(Party.objects.filter(party_type='customer', is_active=True))
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)

