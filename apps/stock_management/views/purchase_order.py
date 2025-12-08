from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from apps.stock_management.models import PurchaseOrder, PurchaseOrderItem
from apps.stock_management.serializers import PurchaseOrderSerializer, PurchaseOrderItemSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders
    """
    queryset = PurchaseOrder.objects.select_related('supplier').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    
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
        
        purchase_orders = PurchaseOrder.objects.filter(
            status=status_filter
        ).select_related('supplier').prefetch_related('items')
        
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


class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase order items
    """
    queryset = PurchaseOrderItem.objects.select_related('purchase_order').all()
    serializer_class = PurchaseOrderItemSerializer
    
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

