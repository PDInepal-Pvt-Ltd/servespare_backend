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
    queryset = BankAccount.objects.all()
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
        
        accounts = self.filter_queryset(BankAccount.objects.filter(
            account_type=account_type,
            is_active=True
        ))

        serializer = self.get_serializer(accounts, many=True)
        return Response(serializer.data)

