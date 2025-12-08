from rest_framework import serializers
from apps.stock_management.models import PurchaseOrder, PurchaseOrderItem
from apps.stock_management.serializers.party import PartySerializer


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseOrderItem model
    """
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id',
            'purchase_order',
            'item_name',
            'part_number',
            'quantity',
            'unit_price',
            'tax',
            'discount_description',
            'subtotal',
            'tax_amount',
            'total_price',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'created', 'modified', 'subtotal', 'tax_amount', 'total_price']
    
    def validate_quantity(self, value):
        """Validate quantity"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    def validate_unit_price(self, value):
        """Validate unit price"""
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative.")
        return value
    
    def validate_tax(self, value):
        """Validate tax"""
        if value < 0:
            raise serializers.ValidationError("Tax cannot be negative.")
        return value


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseOrder model
    """
    supplier_detail = PartySerializer(source='supplier', read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id',
            'po_number',
            'status',
            'supplier',
            'supplier_detail',
            'order_date',
            'expected_delivery_date',
            'purchase_invoice',
            'notes',
            'terms_and_condition',
            'items',
            'total_amount',
            'total_tax',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = [
            'id',
            'created',
            'modified',
            'supplier_detail',
            'items',
            'total_amount',
            'total_tax'
        ]
    
    def validate(self, data):
        """Validate dates"""
        order_date = data.get('order_date', self.instance.order_date if self.instance else None)
        expected_delivery_date = data.get('expected_delivery_date', self.instance.expected_delivery_date if self.instance else None)
        
        if expected_delivery_date and order_date:
            if expected_delivery_date < order_date:
                raise serializers.ValidationError({
                    'expected_delivery_date': 'Expected delivery date cannot be before order date.'
                })
        
        return data

