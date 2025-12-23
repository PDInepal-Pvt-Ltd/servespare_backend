from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, F, DecimalField, Q
from django.db.models.functions import Coalesce
from apps.stock_management.models import PurchaseOrder, PurchaseOrderItem
from apps.stock_management.serializers import PurchaseOrderSerializer, PurchaseOrderItemSerializer
from apps.base.drf import TenantViewSetMixin
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import IsSuperAdminOrTenantAdminOrBranchManager
from apps.base.permission_utils import get_tenant_queryset_for_user, get_branch_queryset_for_user


class PurchaseOrderViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders with RBAC
    """
    queryset = PurchaseOrder.objects.select_related('supplier').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdminOrBranchManager]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Optionally filter by supplier, status, or date ranges
        """
        queryset = PurchaseOrder.objects.select_related('supplier').prefetch_related('items').all()
        
        # Filter by supplier
        supplier_id = self.request.query_params.get('supplier', None)
        if supplier_id is not None:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Search by PO number
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(po_number__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """
        Get purchase orders grouped by status
        """
        status_filter = request.query_params.get('status', None)
        if not status_filter:
            return Response(
                {'error': 'status parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        purchase_orders = self.filter_queryset(PurchaseOrder.objects.filter(
            status=status_filter
        ).select_related('supplier').prefetch_related('items'))

        serializer = self.get_serializer(purchase_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """
        Add an item to a purchase order
        """
        purchase_order = self.get_object()
        serializer = PurchaseOrderItemSerializer(data={
            **request.data,
            'purchase_order': purchase_order.id
        })
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get purchase order statistics:
        - Total POs: count of all purchase orders
        - Total Value: sum of all purchase order values
        - Pending: count of draft and ordered POs
        - Received: count of received POs
        """
        queryset = self.filter_queryset(PurchaseOrder.objects.all())
        
        # Total POs count
        total_pos = queryset.count()
        
        # Total Value - sum of all PO items
        total_value = PurchaseOrderItem.objects.filter(
            purchase_order__in=queryset
        ).aggregate(
            total=Coalesce(
                Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
                0,
                output_field=DecimalField()
            )
        )['total']
        
        # Pending count (draft + ordered)
        pending_count = queryset.filter(status__in=['draft', 'ordered']).count()
        
        # Received count
        received_count = queryset.filter(status='received').count()
        
        # Billed count
        billed_count = queryset.filter(status='billed').count()
        
        return Response({
            'total_pos': total_pos,
            'total_value': float(total_value) if total_value else 0.0,
            'pending': pending_count,
            'received': received_count,
            'billed': billed_count,
            'status_breakdown': {
                'draft': queryset.filter(status='draft').count(),
                'ordered': queryset.filter(status='ordered').count(),
                'received': received_count,
                'billed': billed_count,
            }
        })


class PurchaseOrderItemViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing purchase order items
    """
    queryset = PurchaseOrderItem.objects.select_related('purchase_order').all()
    serializer_class = PurchaseOrderItemSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Optionally filter by purchase_order
        """
        queryset = PurchaseOrderItem.objects.select_related('purchase_order').all()
        
        # Filter by purchase_order
        po_id = self.request.query_params.get('purchase_order', None)
        if po_id is not None:
            queryset = queryset.filter(purchase_order_id=po_id)
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset

    @action(detail=False, methods=['get'])
    def returned(self, request):
        """
        List purchase order items whose parent purchase order has status 'returned'.
        Supports `search` query param (searches item_name, part_number, PO number, supplier name).
        """
        queryset = PurchaseOrderItem.objects.select_related('purchase_order', 'purchase_order__supplier').filter(
            purchase_order__status='returned'
        )

        # Apply tenant/branch filters and any global filters
        queryset = self.filter_queryset(queryset)

        # Search across item_name, part_number, purchase_order.po_number, supplier name
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(item_name__icontains=search) |
                Q(part_number__icontains=search) |
                Q(purchase_order__po_number__icontains=search) |
                Q(purchase_order__supplier__party_name__icontains=search)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

