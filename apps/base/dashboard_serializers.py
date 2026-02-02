"""
Serializers for Dashboard data
"""

from rest_framework import serializers


class TodaySalesSerializer(serializers.Serializer):
    """Serializer for today's sales data"""
    total_orders = serializers.IntegerField()
    total_revenue = serializers.FloatField()
    total_items_sold = serializers.FloatField()
    average_order_value = serializers.FloatField()
    date = serializers.CharField()


class QuickStatsSerializer(serializers.Serializer):
    """Serializer for quick statistics"""
    total_orders_all_time = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    this_month_orders = serializers.IntegerField()
    total_revenue_all_time = serializers.FloatField()
    this_month_revenue = serializers.FloatField()
    total_inventory_items = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()


class PendingOrderSerializer(serializers.Serializer):
    """Serializer for pending orders"""
    order_id = serializers.IntegerField()
    order_number = serializers.CharField()
    customer = serializers.CharField()
    branch = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    amount = serializers.FloatField()
    order_date = serializers.CharField(allow_null=True)


class LowStockAlertSerializer(serializers.Serializer):
    """Serializer for low stock alerts"""
    id = serializers.IntegerField()
    item_name = serializers.CharField()
    part_number = serializers.CharField(allow_null=True)
    current_quantity = serializers.FloatField()
    minimum_required = serializers.FloatField()
    shortage = serializers.FloatField()
    category = serializers.CharField()
    supplier = serializers.CharField()
    estimated_value = serializers.FloatField()
    status = serializers.CharField()


class ActiveCustomerSerializer(serializers.Serializer):
    """Serializer for active customers"""
    customer_id = serializers.IntegerField()
    name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    total_orders = serializers.IntegerField()
    total_spent = serializers.FloatField()
    last_order_date = serializers.CharField(allow_null=True)
    total_items_purchased = serializers.FloatField()


class InventoryValueByCategorySerializer(serializers.Serializer):
    """Serializer for inventory value by category"""
    category = serializers.CharField()
    value = serializers.FloatField()
    items = serializers.IntegerField()
    quantity = serializers.FloatField()


class TotalInventoryValueSerializer(serializers.Serializer):
    """Serializer for total inventory value"""
    total_value = serializers.FloatField()
    total_items = serializers.IntegerField()
    total_quantity = serializers.FloatField()
    by_category = InventoryValueByCategorySerializer(many=True)


class RevenueAnalysisDataSerializer(serializers.Serializer):
    """Serializer for daily revenue analysis"""
    date = serializers.CharField()
    revenue = serializers.FloatField()
    orders = serializers.IntegerField()
    items = serializers.FloatField()


class RevenueByCategorySerializer(serializers.Serializer):
    """Serializer for revenue breakdown by category"""
    category = serializers.CharField()
    revenue = serializers.FloatField()
    items_sold = serializers.FloatField()
    orders = serializers.IntegerField()


class StockFlowDataSerializer(serializers.Serializer):
    """Serializer for stock flow data"""
    date = serializers.CharField()
    quantity = serializers.FloatField()
    value = serializers.FloatField()


class StockFlowSerializer(serializers.Serializer):
    """Serializer for stock flow (inbound/outbound)"""
    outbound = StockFlowDataSerializer(many=True)
    inbound = StockFlowDataSerializer(many=True)


class CompleteDashboardSerializer(serializers.Serializer):
    """Serializer for complete dashboard data"""
    today_sales = TodaySalesSerializer()
    quick_stats = QuickStatsSerializer()
    pending_orders = PendingOrderSerializer(many=True)
    low_stock_alerts = LowStockAlertSerializer(many=True)
    active_customers = ActiveCustomerSerializer(many=True)
    total_inventory_value = TotalInventoryValueSerializer()
    revenue_analysis = RevenueAnalysisDataSerializer(many=True)
    revenue_by_category = RevenueByCategorySerializer(many=True)
    stock_flow = StockFlowSerializer()
    generated_at = serializers.CharField()
