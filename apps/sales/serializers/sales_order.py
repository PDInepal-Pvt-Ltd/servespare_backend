from rest_framework import serializers
from django.db import transaction
from apps.sales.models import SalesOrder, SalesOrderItem


class SalesOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for sales order items"""
    
    inventory_name = serializers.CharField(source='inventory.item_name', read_only=True)
    available_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'tenant', 'branch', 'inventory', 'inventory_name', 'item_name', 'part_number',
            'quantity', 'unit_price', 'discount_percentage', 'discount_amount',
            'tax_percentage', 'tax_amount', 'line_total', 'warranty_period',
            'notes', 'available_stock'
        ]
        read_only_fields = [
            'id', 'tenant', 'item_name', 'part_number', 'discount_amount', 
            'tax_amount', 'line_total', 'warranty_period'
        ]
    
    def get_available_stock(self, obj):
        """Get available stock for the inventory item"""
        if obj.inventory:
            return float(obj.inventory.quantity)
        return 0
    
    def validate(self, attrs):
        """Validate item data"""
        inventory = attrs.get('inventory')
        quantity = attrs.get('quantity', 0)
        
        # Check if inventory has sufficient stock
        if inventory and quantity > 0:
            if inventory.quantity < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Insufficient stock. Available: {inventory.quantity}'
                })
        
        return attrs


class SalesOrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing sales orders"""
    
    customer_name = serializers.CharField(source='customer.customer_name', read_only=True)
    order_status_display = serializers.CharField(source='get_order_status_display', read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'tenant', 'branch', 'order_number', 'order_date', 'customer', 'customer_name',
            'order_status', 'order_status_display',
            'total_amount',
            'total_items', 'total_quantity',
            'expected_delivery_date', 'created', 'modified'
        ]
        read_only_fields = ['id', 'tenant', 'order_number', 'order_date', 'created', 'modified']


class SalesOrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed sales order information"""
    
    customer_name = serializers.CharField(source='customer.customer_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_type = serializers.CharField(source='customer.customer_type', read_only=True)
    order_status_display = serializers.CharField(source='get_order_status_display', read_only=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status_display_description = serializers.CharField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'tenant', 'branch', 'order_number', 'order_date', 
            'customer', 'customer_name', 'customer_phone', 'customer_type',
            'order_status', 'order_status_display', 'status_display_description',
            'subtotal', 'discount_percentage', 'discount_amount',
            'tax_percentage', 'tax_amount', 'shipping_charges', 'total_amount',
            'delivery_address', 'delivery_city', 'delivery_state', 'delivery_pincode',
            'expected_delivery_date', 'actual_delivery_date',
            'tracking_number', 'courier_partner',
            'notes', 'internal_notes',
            'items', 'total_items', 'total_quantity',
            'created_by', 'created_by_name',
            'created', 'modified', 'is_active'
        ]
        read_only_fields = [
            'id', 'tenant', 'order_number', 'order_date', 'subtotal', 'discount_amount',
            'tax_amount', 'total_amount', 'created', 'modified'
        ]


class SalesOrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sales order items"""
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'inventory', 'quantity', 'unit_price', 'branch',
            'discount_percentage', 'tax_percentage', 'notes'
        ]
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class SalesOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sales orders"""
    
    items = SalesOrderItemCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'customer', 'order_status', 'branch',
            'discount_percentage', 'tax_percentage', 'shipping_charges',
            'delivery_address', 'delivery_city', 'delivery_state', 'delivery_pincode',
            'expected_delivery_date', 'tracking_number', 'courier_partner',
            'notes', 'internal_notes', 'items'
        ]
    
    def validate_items(self, value):
        """Validate that at least one item is provided"""
        if not value:
            raise serializers.ValidationError("At least one item is required")
        return value
    
    def validate(self, attrs):
        """Validate order data"""
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Create order with items"""
        items_data = validated_data.pop('items')
        
        # Get created_by from context
        created_by = self.context['request'].user if 'request' in self.context else None
        if created_by:
            validated_data['created_by'] = created_by
            validated_data.setdefault('tenant', created_by.tenant)
            if 'branch' not in validated_data and getattr(created_by, 'branch', None):
                validated_data['branch'] = created_by.branch
        
        # Create order
        order = SalesOrder.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            SalesOrderItem.objects.create(order=order, tenant=order.tenant, branch=item_data.get('branch') or order.branch, **{k: v for k, v in item_data.items() if k not in ['branch']})
        
        # Calculate totals
        order.calculate_totals()
        
        return order


class SalesOrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating sales orders"""
    
    class Meta:
        model = SalesOrder
        fields = [
            'order_status', 'discount_percentage', 'tax_percentage', 'shipping_charges',
            'delivery_address', 'delivery_city', 'delivery_state', 'delivery_pincode',
            'expected_delivery_date', 'actual_delivery_date',
            'tracking_number', 'courier_partner',
            'notes', 'internal_notes', 'is_active'
        ]
    
    def validate(self, attrs):
        """Validate update data"""
        # Prevent changing order status to delivered without actual delivery date
        if attrs.get('order_status') == 'delivered' and not attrs.get('actual_delivery_date'):
            if not self.instance.actual_delivery_date:
                from django.utils import timezone
                attrs['actual_delivery_date'] = timezone.now().date()
        
        return attrs
    
    def update(self, instance, validated_data):
        """Update order and recalculate totals if needed"""
        # Check if financial fields changed
        financial_fields = ['discount_percentage', 'tax_percentage', 'shipping_charges']
        recalculate = any(field in validated_data for field in financial_fields)
        
        # Update instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Recalculate totals if needed
        if recalculate:
            instance.calculate_totals()
        
        return instance


class SalesOrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status"""
    
    order_status = serializers.ChoiceField(
        choices=SalesOrder.ORDER_STATUS_CHOICES,
        required=True
    )
    tracking_number = serializers.CharField(required=False, allow_blank=True)
    courier_partner = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        """Update order status"""
        order_status = validated_data.get('order_status')
        tracking_number = validated_data.get('tracking_number')
        courier_partner = validated_data.get('courier_partner')
        notes = validated_data.get('notes')
        
        # Update tracking info if provided
        if tracking_number:
            instance.tracking_number = tracking_number
        if courier_partner:
            instance.courier_partner = courier_partner
        if notes:
            instance.internal_notes = f"{instance.internal_notes or ''}\n{notes}".strip()
        
        # Update status
        instance.update_order_status(order_status)
        
        return instance



