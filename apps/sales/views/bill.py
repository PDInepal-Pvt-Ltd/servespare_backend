from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.sales.models import Bill
from apps.sales.serializers import BillSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.permissions import IsSuperAdminOrTenantAdminOrBranchManager
from apps.base.permission_utils import get_tenant_queryset_for_user, get_branch_queryset_for_user


class BillViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing bills with RBAC
    """
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdminOrBranchManager]
    
    def get_queryset(self):
        """
        Optionally filter by customer_type, is_active, status, payment_method and search
        """
        queryset = Bill.objects.all()
        
        # Filter by customer_type
        customer_type = self.request.query_params.get('customer_type', None)
        if customer_type is not None:
            queryset = queryset.filter(customer_type=customer_type)
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)

        # Filter by payment_method
        payment_method = self.request.query_params.get('payment_method', None)
        if payment_method is not None:
            queryset = queryset.filter(payment_method=payment_method)

        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Search by customer name, phone, or PAN/VAT number
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(customer_name__icontains=search) |
                Q(phone_numbers__icontains=search) |
                Q(pan_vat_number__icontains=search) |
                Q(address__icontains=search)
            )
         
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Get bills filtered by customer type
        """
        customer_type = request.query_params.get('customer_type', None)
        if not customer_type:
            return Response(
                {'error': 'customer_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bills = self.filter_queryset(Bill.objects.filter(
            customer_type=customer_type,
            is_active=True
        ))

        serializer = self.get_serializer(bills, many=True)
        return Response(serializer.data)

