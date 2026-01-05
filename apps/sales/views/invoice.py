from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.apps import apps

from apps.base.pagination import StandardResultsSetPagination
from apps.sales.serializers import (
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    InvoiceCreateSerializer,
    InvoiceUpdatePaymentSerializer,
)
from apps.base.drf import TenantViewSetMixin
from apps.base.permissions import IsSuperAdminOrTenantAdminOrBranchManager, CanViewOwnOrders
from apps.base.permission_utils import get_tenant_queryset_for_user


def get_invoice_model():
    """Lazy load Invoice model"""
    return apps.get_model('sales', 'Invoice')


def get_sales_order_model():
    """Lazy load SalesOrder model"""
    return apps.get_model('sales', 'SalesOrder')


class InvoiceViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Invoice CRUD operations.
    
    Provides endpoints for:
    - list: Get all invoices (management) or own invoices (customer)
    - retrieve: Get single invoice (management) or own invoice (customer)
    - create: Create new invoice (management only)
    - update/partial_update: Update invoice (management only)
    - destroy: Delete invoice (management only)
    - update_payment_status: Update invoice payment status and sync to sales order and bill
    - generate_from_order: Generate invoice from a sales order
    - download_pdf: Download invoice as PDF (not implemented, placeholder)
    
    Permissions:
    - Super Admin, Tenant Admin, Branch Manager: Full CRUD access to all invoices
    - Customer: Can view their own invoices only
    """
    
    filterset_fields = ['customer', 'branch', 'sales_order']
    search_fields = ['invoice_number', 'customer__username', 'customer__email']
    ordering_fields = ['created', 'invoice_date', 'total_amount', 'invoice_number']
    ordering = ['-invoice_date', '-created']
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset with proper prefetching"""
        Invoice = get_invoice_model()
        # Avoid evaluating queryset during schema generation or when request has no authenticated user
        if getattr(self, 'swagger_fake_view', False):
            return get_invoice_model().objects.none()

        queryset = Invoice.objects.filter(is_removed=False).select_related(
            'customer', 'sales_order', 'bill', 'branch', 'created_by'
        ).prefetch_related('items')
        
        user = self.request.user
        # If there's no authenticated user, return empty queryset to avoid filtering by AnonymousUser
        if not hasattr(self.request, 'user') or self.request.user.is_anonymous:
            return Invoice.objects.none()
        
        # Check if user is management (super admin, tenant admin, or branch manager)
        is_management = (
            user.is_superuser or
            getattr(user, 'is_tenant_admin', False) or
            getattr(user, 'is_branch_manager', False)
        )
        
        if is_management:
            # Management can see all invoices in their tenant/branch
            if hasattr(user, 'tenant') and user.tenant:
                queryset = queryset.filter(tenant=user.tenant)
            if hasattr(user, 'branch') and user.branch:
                queryset = queryset.filter(branch=user.branch)
        else:
            # Customers can only see their own invoices
            queryset = queryset.filter(customer=user)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return InvoiceListSerializer
        elif self.action == 'create':
            return InvoiceCreateSerializer
        elif self.action == 'update_payment_status':
            return InvoiceUpdatePaymentSerializer
        else:
            return InvoiceDetailSerializer
    
    def perform_create(self, serializer):
        """Create invoice with tenant and user information"""
        serializer.save(
            tenant=self.request.user.tenant,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Update invoice with modified timestamp"""
        serializer.save(modified=timezone.now())
    
    @action(detail=False, methods=['post'], url_path='generate-from-order')
    def generate_from_order(self, request):
        """
        Generate invoice from a sales order
        
        Body:
        {
            "sales_order_id": 1
        }
        """
        sales_order_id = request.data.get('sales_order_id')
        
        if not sales_order_id:
            return Response(
                {'error': 'sales_order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            SalesOrder = get_sales_order_model()
            sales_order = SalesOrder.objects.get(id=sales_order_id)
            
            # Check if user has permission to generate invoice for this order
            is_management = (
                request.user.is_superuser or
                getattr(request.user, 'is_tenant_admin', False) or
                getattr(request.user, 'is_branch_manager', False)
            )
            
            if not is_management and sales_order.customer != request.user:
                return Response(
                    {'error': 'You do not have permission to generate invoice for this order'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if invoice already exists
            if hasattr(sales_order, 'invoice'):
                return Response(
                    {
                        'message': 'Invoice already exists for this order',
                        'invoice': InvoiceDetailSerializer(sales_order.invoice).data
                    },
                    status=status.HTTP_200_OK
                )
            
            # Generate invoice
            invoice = sales_order.generate_invoice()
            
            return Response(
                {
                    'message': 'Invoice generated successfully',
                    'invoice': InvoiceDetailSerializer(invoice).data
                },
                status=status.HTTP_201_CREATED
            )
            
        except get_sales_order_model().DoesNotExist:
            return Response(
                {'error': 'Sales order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to generate invoice: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'], url_path='update-payment-status')
    def update_payment_status(self, request, pk=None):
        """
        Update invoice payment status and sync to related models
        
        Body:
        {
            "payment_status": "paid|pending|on_hold|credit_sale|cancelled|refunded",
            "paid_amount": 1000.00,
            "payment_method": "cash|card|upi|bank_transfer|credit"
        }
        """
        invoice = self.get_object()
        
        serializer = self.get_serializer(invoice, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        
        return Response(
            {
                'message': 'Payment status updated successfully',
                'invoice': InvoiceDetailSerializer(invoice).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        """
        Download invoice as PDF
        (This is a placeholder - implement actual PDF generation)
        """
        invoice = self.get_object()
        
        return Response(
            {'message': 'PDF download not yet implemented'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
