"""
Dashboard Service for providing analytics and dashboard data
Includes: sales, inventory, revenue, stock flow, alerts, and customer analytics
"""

from django.db.models import Sum, Count, Q, F, DecimalField, Case, When, Value, Max, ExpressionWrapper
from django.db.models.functions import TruncDate, Coalesce
from django.utils import timezone
from django.utils.timezone import now, timedelta
from decimal import Decimal
from datetime import datetime, date

from apps.sales.models import SalesOrder, SalesOrderItem
from apps.stock_management.models import Inventory, PurchaseOrder, PurchaseOrderItem
from apps.users.models import User


class DashboardService:
    """Service to calculate and provide dashboard analytics data"""
    
    def __init__(self, tenant=None, branch=None):
        self.tenant = tenant
        self.branch = branch
        
    def _get_filter_kwargs(self):
        """Get filter kwargs based on tenant and branch"""
        kwargs = {}
        if self.tenant:
            kwargs['tenant'] = self.tenant
        if self.branch:
            kwargs['branch'] = self.branch
        return kwargs
    
    # ============ TODAY'S SALES DATA ============
    
    def get_today_sales(self):
        """Get today's sales statistics"""
        today = timezone.now().date()
        filter_kwargs = self._get_filter_kwargs()
        
        sales = SalesOrder.objects.filter(
            order_date__date=today,
            order_status__in=['confirmed', 'delivered', 'packed', 'ready_to_pack', 'ready_to_depart', 'in_transit'],
            is_removed=False,
            **filter_kwargs
        )
        
        stats = sales.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            total_items=Sum('items__quantity'),
            average_order_value=Sum('total_amount') / Count('id', filter=Q(total_amount__gt=0))
        )
        
        return {
            'total_orders': stats['total_orders'] or 0,
            'total_revenue': float(stats['total_revenue'] or Decimal('0.00')),
            'total_items_sold': float(stats['total_items'] or Decimal('0.00')),
            'average_order_value': float(stats['average_order_value'] or Decimal('0.00')),
            'date': str(today),
        }
    
    # ============ REVENUE ANALYSIS ============
    
    def get_revenue_analysis(self, days=30):
        """Get revenue analysis data for graph (last 30 days by default)"""
        start_date = timezone.now() - timedelta(days=days)
        filter_kwargs = self._get_filter_kwargs()
        
        daily_revenue = SalesOrder.objects.filter(
            order_date__gte=start_date,
            is_removed=False,
            **filter_kwargs
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            revenue=Sum('total_amount'),
            orders=Count('id'),
            items=Sum('items__quantity')
        ).order_by('date')
        
        return [
            {
                'date': str(entry['date']),
                'revenue': float(entry['revenue'] or Decimal('0.00')),
                'orders': entry['orders'],
                'items': float(entry['items'] or Decimal('0.00')),
            }
            for entry in daily_revenue
        ]
    
    def get_revenue_by_category(self, days=30):
        """Get revenue breakdown by inventory category"""
        start_date = timezone.now() - timedelta(days=days)
        filter_kwargs = self._get_filter_kwargs()
        
        category_revenue = SalesOrderItem.objects.filter(
            order__order_date__gte=start_date,
            order__is_removed=False,
            **filter_kwargs
        ).values('inventory__category').annotate(
            total_revenue=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField())),
            total_items=Sum('quantity'),
            total_orders=Count('order', distinct=True)
        ).order_by('-total_revenue')
        
        return [
            {
                'category': entry['inventory__category'] or 'Uncategorized',
                'revenue': float(entry['total_revenue'] or Decimal('0.00')),
                'items_sold': float(entry['total_items'] or Decimal('0.00')),
                'orders': entry['total_orders'],
            }
            for entry in category_revenue
        ]
    
    # ============ STOCK FLOW ============
    
    def get_stock_flow(self, days=30):
        """Get stock flow analysis (inbound and outbound)"""
        start_date = timezone.now() - timedelta(days=days)
        filter_kwargs = self._get_filter_kwargs()
        
        # Outbound (Sales)
        outbound = SalesOrderItem.objects.filter(
            order__order_date__gte=start_date,
            order__is_removed=False,
            **filter_kwargs
        ).annotate(
            date=TruncDate('order__order_date')
        ).values('date').annotate(
            quantity=Sum('quantity'),
            value=Sum('line_total')
        ).order_by('date')
        
        # Inbound (Purchases)
        inbound = PurchaseOrderItem.objects.filter(
            purchase_order__order_date__gte=start_date,
            **filter_kwargs
        ).annotate(
            date=TruncDate('purchase_order__order_date'),
            line_value=ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField())
        ).values('date').annotate(
            quantity=Sum('quantity'),
            value=Sum('line_value')
        ).order_by('date')
        
        return {
            'outbound': [
                {
                    'date': str(entry['date']),
                    'quantity': float(entry['quantity'] or Decimal('0.00')),
                    'value': float(entry['value'] or Decimal('0.00')),
                }
                for entry in outbound
            ],
            'inbound': [
                {
                    'date': str(entry['date']),
                    'quantity': float(entry['quantity'] or Decimal('0.00')),
                    'value': float(entry['value'] or Decimal('0.00')),
                }
                for entry in inbound
            ]
        }
    
    # ============ LOW STOCK ALERTS ============
    
    def get_low_stock_alerts(self, threshold_percentage=20):
        """
        Get items with low stock levels
        Shows items where current quantity is below min_stock_level
        """
        filter_kwargs = self._get_filter_kwargs()
        
        low_stock = Inventory.objects.filter(
            Q(quantity__lte=F('min_stock_level')) | Q(quantity__lt=1),
            is_removed=False,
            **filter_kwargs
        ).select_related('tenant', 'branch', 'party').values(
            'id', 'item_name', 'part_number', 'quantity', 'min_stock_level', 
            'price', 'category', 'party__party_name'
        ).order_by('quantity')
        
        alerts = []
        for item in low_stock:
            current_qty = item['quantity'] or Decimal('0.00')
            min_stock = item['min_stock_level'] or Decimal('0.00')
            
            if current_qty <= min_stock:
                alerts.append({
                    'id': item['id'],
                    'item_name': item['item_name'],
                    'part_number': item['part_number'],
                    'current_quantity': float(current_qty),
                    'minimum_required': float(min_stock),
                    'shortage': float(min_stock - current_qty),
                    'category': item['category'],
                    'supplier': item['party__party_name'] or 'N/A',
                    'estimated_value': float((current_qty * (item['price'] or Decimal('0.00')))),
                    'status': 'critical' if current_qty == 0 else 'warning'
                })
        
        return sorted(alerts, key=lambda x: x['shortage'], reverse=True)
    
    # ============ QUICK STATS / PENDING ORDERS ============
    
    def get_pending_orders(self):
        """Get pending orders (not delivered or cancelled)"""
        filter_kwargs = self._get_filter_kwargs()
        
        pending = SalesOrder.objects.filter(
            order_status__in=['confirmed', 'ready_to_pack', 'packed', 'ready_to_depart', 'in_transit'],
            is_removed=False,
            **filter_kwargs
        ).select_related('customer', 'branch').values(
            'id', 'order_number', 'order_date', 'order_status', 'total_amount',
            'customer__full_name', 'branch__branch_name'
        ).order_by('-order_date')
        
        return [
            {
                'order_id': entry['id'],
                'order_number': entry['order_number'],
                'customer': entry['customer__full_name'],
                'branch': entry['branch__branch_name'],
                'status': entry['order_status'],
                'amount': float(entry['total_amount'] or Decimal('0.00')),
                'order_date': entry['order_date'].isoformat() if entry['order_date'] else None,
            }
            for entry in pending
        ]
    
    def get_quick_stats(self):
        """Get quick statistics for dashboard cards"""
        filter_kwargs = self._get_filter_kwargs()
        
        # Total Orders (This Month)
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total_orders = SalesOrder.objects.filter(
            is_removed=False,
            **filter_kwargs
        ).count()
        
        pending_orders = SalesOrder.objects.filter(
            order_status__in=['confirmed', 'ready_to_pack', 'packed', 'ready_to_depart', 'in_transit'],
            is_removed=False,
            **filter_kwargs
        ).count()
        
        this_month_orders = SalesOrder.objects.filter(
            order_date__gte=month_start,
            is_removed=False,
            **filter_kwargs
        ).count()
        
        # Revenue stats
        total_revenue = SalesOrder.objects.filter(
            is_removed=False,
            **filter_kwargs
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        
        this_month_revenue = SalesOrder.objects.filter(
            order_date__gte=month_start,
            is_removed=False,
            **filter_kwargs
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        
        # Inventory stats
        total_inventory_items = Inventory.objects.filter(
            is_removed=False,
            **filter_kwargs
        ).count()
        
        low_stock_count = Inventory.objects.filter(
            Q(quantity__lte=F('min_stock_level')),
            is_removed=False,
            **filter_kwargs
        ).count()
        
        return {
            'total_orders_all_time': total_orders,
            'pending_orders': pending_orders,
            'this_month_orders': this_month_orders,
            'total_revenue_all_time': float(total_revenue),
            'this_month_revenue': float(this_month_revenue),
            'total_inventory_items': total_inventory_items,
            'low_stock_items': low_stock_count,
        }
    
    # ============ INVENTORY MANAGER STATS ============
    
    def get_inventory_manager_stats(self):
        """Get inventory statistics for Inventory Manager - branch specific"""
        filter_kwargs = self._get_filter_kwargs()
        
        inventory_queryset = Inventory.objects.filter(
            is_removed=False,
            **filter_kwargs
        )
        
        # Total products in branch
        total_products = inventory_queryset.count()
        
        # Low stock items (quantity <= min_stock_level but not zero)
        low_stock_items = inventory_queryset.filter(
            Q(quantity__lte=F('min_stock_level')) & Q(quantity__gt=0)
        ).count()
        
        # Out of stock items (quantity = 0)
        out_of_stock_items = inventory_queryset.filter(
            quantity=0
        ).count()
        
        # Total stock value (quantity * price)
        total_stock_value = inventory_queryset.aggregate(
            total_value=Sum(
                ExpressionWrapper(
                    F('quantity') * F('price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )['total_value'] or Decimal('0.00')
        
        # Active products (quantity > 0)
        active_products = inventory_queryset.filter(quantity__gt=0).count()
        
        return {
            'total_products': total_products,
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'total_stock_value': float(total_stock_value),
            'active_products': active_products,
        }
    
    # ============ ACTIVE CUSTOMERS ============
    
    def get_active_customers(self, days=30, limit=10):
        """Get active customers (those who made recent purchases)"""
        start_date = timezone.now() - timedelta(days=days)
        filter_kwargs = self._get_filter_kwargs()
        
        active_customers = SalesOrder.objects.filter(
            order_date__gte=start_date,
            is_removed=False,
            **filter_kwargs
        ).values('customer__id', 'customer__full_name', 'customer__phone').annotate(
            total_orders=Count('id'),
            total_spent=Sum('total_amount'),
            last_order_date=Max('order_date'),
            total_items=Sum('items__quantity')
        ).order_by('-total_spent')[:limit]
        
        return [
            {
                'customer_id': entry['customer__id'],
                'name': entry['customer__full_name'],
                'phone': entry['customer__phone'],
                'total_orders': entry['total_orders'],
                'total_spent': float(entry['total_spent'] or Decimal('0.00')),
                'last_order_date': entry['last_order_date'].isoformat() if entry['last_order_date'] else None,
                'total_items_purchased': float(entry['total_items'] or Decimal('0.00')),
            }
            for entry in active_customers
        ]
    
    # ============ TOTAL INVENTORY VALUE ============
    
    def get_total_inventory_value(self):
        """Calculate total inventory value (quantity * price)"""
        filter_kwargs = self._get_filter_kwargs()
        
        inventory_value = Inventory.objects.filter(
            is_removed=False,
            **filter_kwargs
        ).aggregate(
            total_value=Sum(ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())),
            total_items=Count('id'),
            total_quantity=Sum('quantity')
        )
        
        # Breakdown by category
        by_category = Inventory.objects.filter(
            is_removed=False,
            **filter_kwargs
        ).values('category').annotate(
            value=Sum(ExpressionWrapper(F('quantity') * F('price'), output_field=DecimalField())),
            items=Count('id'),
            quantity=Sum('quantity')
        ).order_by('-value')
        
        return {
            'total_value': float(inventory_value['total_value'] or Decimal('0.00')),
            'total_items': inventory_value['total_items'],
            'total_quantity': float(inventory_value['total_quantity'] or Decimal('0.00')),
            'by_category': [
                {
                    'category': entry['category'] or 'Uncategorized',
                    'value': float(entry['value'] or Decimal('0.00')),
                    'items': entry['items'],
                    'quantity': float(entry['quantity'] or Decimal('0.00')),
                }
                for entry in by_category
            ]
        }
    
    # ============ COMPLETE DASHBOARD DATA ============
    
    def get_complete_dashboard_data(self, days=30):
        """Get all dashboard data in one call"""
        return {
            'today_sales': self.get_today_sales(),
            'quick_stats': self.get_quick_stats(),
            'pending_orders': self.get_pending_orders(),
            'low_stock_alerts': self.get_low_stock_alerts(),
            'active_customers': self.get_active_customers(days=days),
            'total_inventory_value': self.get_total_inventory_value(),
            'revenue_analysis': self.get_revenue_analysis(days=days),
            'revenue_by_category': self.get_revenue_by_category(days=days),
            'stock_flow': self.get_stock_flow(days=days),
            'generated_at': timezone.now().isoformat(),
        }
