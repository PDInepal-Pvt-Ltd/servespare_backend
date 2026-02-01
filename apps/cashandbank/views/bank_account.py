from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.cashandbank.models import BankAccount
from apps.cashandbank.serializers import BankAccountSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import CanManageBranchResources
from apps.base.permission_utils import get_branch_queryset_for_user


class BankAccountViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing bank accounts with RBAC
    """
    queryset = BankAccount.objects.filter(is_removed=False)
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Optionally filter by account_type or is_active
        """
        queryset = BankAccount.objects.all()
        
        # Filter by account_type
        account_type = self.request.query_params.get('account_type', None)
        if account_type is not None:
            queryset = queryset.filter(account_type=account_type)
        
        # Filter by branch
        branch_id = self.request.query_params.get('branch', None)
        if branch_id is not None:
            queryset = queryset.filter(branch_id=branch_id)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Search by account name or bank name
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(account_name__icontains=search) |
                Q(bank_name__icontains=search) |
                Q(account_holders_name__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Get bank accounts filtered by account type
        """
        account_type = request.query_params.get('account_type', None)
        if not account_type:
            return Response(
                {'error': 'account_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = BankAccount.objects.filter(
            account_type=account_type,
            is_active=True
        )
        
        # Filter by branch
        branch_id = request.query_params.get('branch', None)
        if branch_id is not None:
            queryset = queryset.filter(branch_id=branch_id)
        
        accounts = self.filter_queryset(queryset)

        serializer = self.get_serializer(accounts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='bank-names', permission_classes=[IsAuthenticated])
    def bank_names(self, request):
        """
        Return distinct bank names (for account_type='bank') scoped by tenant and branch.

        Rules:
        - If user has an assigned branch (user.branch), restrict results to that branch.
        - Otherwise, if `branch` query param is provided, ensure the user has access to that branch and filter by it.
        - Tenant filtering is applied automatically via TenantViewSetMixin / filter_queryset.
        """
        # Base queryset: only bank-type accounts and active
        base_qs = BankAccount.objects.filter(account_type='bank', is_active=True)

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

        # Get distinct non-empty bank names (exclude null/empty strings)
        bank_names = qs.exclude(bank_name__isnull=True).exclude(bank_name__exact='').values_list('bank_name', flat=True).distinct()
        data = [{'bank_name': name} for name in bank_names]
        return Response(data)

