from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q
from django.utils import timezone

from apps.base.pagination import StandardResultsSetPagination
from apps.sales.models import SalesOrder
from apps.sales.serializers import (
    SalesOrderListSerializer,
    SalesOrderDetailSerializer,
    SalesOrderCreateSerializer,
    SalesOrderUpdateSerializer,
    SalesOrderStatusUpdateSerializer,
    AddPaymentSerializer,
)


class SalesOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sales Order CRUD operations.
    
    Provides endpoints for:
    - list: Get all orders
    - retrieve: Get single order
    - create: Create new order
    - update/partial_update: Update order
    - destroy: Cancel order
    - update_status: Update order status
    - add_payment: Add payment to order
    - cancel: Cancel order
    - stats: Get order statistics
    """
    
    queryset = SalesOrder.objects.filter(is_removed=False).select_related('customer', 'created_by')
    filterset_fields = ['customer', 'order_status', 'payment_status', 'payment_method', 'created_by']
    search_fields = ['order_number', 'customer__customer_name', 'customer__phone', 'tracking_number']
    ordering_fields = ['created', 'order_date', 'total_amount', 'order_number']
    ordering = ['-order_date', '-created']
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SalesOrderListSerializer
        elif self.action == 'create':
            return SalesOrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SalesOrderUpdateSerializer
        elif self.action == 'update_status':
            return SalesOrderStatusUpdateSerializer
        elif self.action == 'add_payment':
            return AddPaymentSerializer
        return SalesOrderDetailSerializer
    
    def get_queryset(self):
        """Get queryset with optional date filtering"""
        queryset = super().get_queryset()
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        return queryset
    
    def perform_destroy(self, instance):
        """Cancel order instead of deleting"""
        try:
            instance.cancel_order()
        except Exception as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(e))
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status.
        
        POST /api/sales-orders/{id}/update_status/
        Body: {
            order_status, 
            tracking_number (optional), 
            courier_partner (optional),
            notes (optional)
        }
        """
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return updated order
        response_serializer = SalesOrderDetailSerializer(order)
        return Response({
            'message': f'Order status updated to {order.get_order_status_display()}',
            'order': response_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """
        Add payment to order.
        
        POST /api/sales-orders/{id}/add_payment/
        Body: {amount, payment_method, notes (optional)}
        """
        order = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={'order': order}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return updated order
        response_serializer = SalesOrderDetailSerializer(order)
        return Response({
            'message': f'Payment of {request.data["amount"]} added successfully',
            'order': response_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel order and restore inventory.
        
        POST /api/sales-orders/{id}/cancel/
        """
        order = self.get_object()
        
        try:
            order.cancel_order()
            return Response({
                'message': f'Order {order.order_number} cancelled successfully'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get sales order statistics.
        
        GET /api/sales-orders/stats/
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Calculate statistics
        total_orders = queryset.count()
        total_revenue = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        total_paid = queryset.aggregate(total=Sum('paid_amount'))['total'] or 0
        total_outstanding = total_revenue - total_paid
        
        # Calculate average order value
        avg_order_value = float(total_revenue) / total_orders if total_orders > 0 else 0
        
        # Today's stats
        today = timezone.now().date()
        today_orders = queryset.filter(order_date__date=today)
        today_sales = today_orders.count()
        today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        stats = {
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'total_paid': float(total_paid),
            'total_outstanding': float(total_outstanding),
            'avg_order_value': avg_order_value,
            'today': {
                'sales': today_sales,
                'revenue': float(today_revenue),
            },
            'by_status': {},
            'by_payment_status': {},
            'this_month': {
                'orders': 0,
                'revenue': 0,
            },
        }
        
        # Orders by status
        for status_choice in SalesOrder.ORDER_STATUS_CHOICES:
            status_code = status_choice[0]
            count = queryset.filter(order_status=status_code).count()
            stats['by_status'][status_code] = {
                'count': count,
                'label': status_choice[1]
            }
        
        # Orders by payment status
        for payment_status in SalesOrder.PAYMENT_STATUS_CHOICES:
            status_code = payment_status[0]
            count = queryset.filter(payment_status=status_code).count()
            stats['by_payment_status'][status_code] = {
                'count': count,
                'label': payment_status[1]
            }
        
        # This month's stats
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_orders = queryset.filter(order_date__gte=current_month)
        stats['this_month']['orders'] = month_orders.count()
        stats['this_month']['revenue'] = float(month_orders.aggregate(total=Sum('total_amount'))['total'] or 0)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get pending orders (not delivered or cancelled).
        
        GET /api/sales-orders/pending/
        """
        queryset = self.get_queryset().exclude(
            Q(order_status='delivered') | Q(order_status='cancelled')
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SalesOrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SalesOrderListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unpaid(self, request):
        """
        Get unpaid or partially paid orders.
        
        GET /api/sales-orders/unpaid/
        """
        queryset = self.get_queryset().exclude(payment_status='paid')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SalesOrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SalesOrderListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def invoice(self, request, pk=None):
        """
        Get invoice data for order.
        
        GET /api/sales-orders/{id}/invoice/
        """
        order = self.get_object()
        serializer = SalesOrderDetailSerializer(order)
        
        # You can add additional invoice-specific formatting here
        invoice_data = {
            'invoice_number': order.order_number,
            'invoice_date': order.order_date,
            'order': serializer.data,
        }
        
        return Response(invoice_data)
