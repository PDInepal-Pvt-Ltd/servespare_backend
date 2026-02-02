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
    queryset = Party.objects.filter(is_removed=False)
    serializer_class = PartySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Optionally filter by party_type, customer_type, or is_active
        """
        queryset = Party.objects.filter(is_removed=False)
        
        # Filter by party_type
        party_type = self.request.query_params.get('party_type', None)
        if party_type is not None:
            queryset = queryset.filter(party_type=party_type)
        
        # Filter by branch
        branch_id = self.request.query_params.get('branch', None)
        if branch_id is not None:
            queryset = queryset.filter(branch_id=branch_id)
        
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

        queryset = Party.objects.filter(party_type='supplier', is_active=True)
        
        # Filter by branch
        branch_id = request.query_params.get('branch', None)
        if branch_id is not None:
            queryset = queryset.filter(branch_id=branch_id)
        
        suppliers = self.filter_queryset(queryset)
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

        queryset = Party.objects.filter(party_type='customer', is_active=True)
        
        # Filter by branch
        branch_id = request.query_params.get('branch', None)
        if branch_id is not None:
            queryset = queryset.filter(branch_id=branch_id)
        
        customers = self.filter_queryset(queryset)
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='party-names', permission_classes=[IsAuthenticated])
    def party_names(self, request):
        """
        Return distinct party names (suppliers and customers) scoped by tenant and branch.

        Rules:
        - If user has an assigned branch (user.branch), restrict results to that branch.
        - Otherwise, if `branch` query param is provided, ensure the user has access to that branch and filter by it.
        - Tenant filtering is applied automatically via TenantViewSetMixin / filter_queryset.
        """
        # Base queryset: only active parties
        base_qs = Party.objects.filter(is_active=True)

        # Apply tenant-level filtering and other global filters
        qs = self.filter_queryset(base_qs)

        # Apply branch-level permissions
        from apps.base.permission_utils import get_branch_queryset_for_user
        from apps.branch.models import Branch

        # If user has an assigned branch, always restrict to that
        user_branch = getattr(request.user, 'branch', None)
        if user_branch:
            qs = qs.filter(branch=user_branch)
        else:
            # Allow branch query param for users who can access multiple branches
            branch_id = request.query_params.get('branch', None)
            if branch_id:
                # Validate branch exists
                try:
                    branch_obj = Branch.objects.get(pk=branch_id)
                except Branch.DoesNotExist:
                    return Response({'detail': 'Branch not found.'}, status=status.HTTP_404_NOT_FOUND)

                # Ensure branch is within user's allowed branches
                allowed_qs = get_branch_queryset_for_user(request.user, qs)
                if not allowed_qs.filter(branch=branch_obj).exists():
                    return Response({'detail': 'You do not have access to this branch.'}, status=status.HTTP_403_FORBIDDEN)

                qs = qs.filter(branch=branch_obj)
            else:
                # For users like Tenant Admin, restrict to branches they can access
                qs = get_branch_queryset_for_user(request.user, qs)

        party_names = qs.exclude(party_name__isnull=True).exclude(party_name__exact='').values_list('party_name', flat=True).distinct()
        data = [{'party_name': name} for name in party_names]
        return Response(data)

