from rest_framework import serializers
from decimal import Decimal
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.carts.models import Cart, CartItem
from apps.stock_management.models import Inventory
from apps.sales.models import SalesOrder, Bill


class InventoryBasicSerializer(serializers.ModelSerializer):
    """Basic inventory information for cart items"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    warranty_display = serializers.CharField(source='get_warranty_period_display', read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = [
            'id',
            'item_name',
            'category',
            'category_display',
            'vehicle_type',
            'vehicle_type_display',
            'part_number',
            'quantity',
            'retail_pricing',
            'mrp',
            'warranty_period',
            'warranty_display',
            'primary_image',
            'barcode',
        ]
    
    def get_primary_image(self, obj):
        """Get the first active image URL"""
        first_image = obj.images.filter(is_removed=False).first()
        if first_image and first_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None


class CartItemSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """Serializer for cart items"""
    inventory = InventoryBasicSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    
    def get_total_price(self, obj):
        """Get total price for this cart item as string with 2 decimals"""
        from decimal import Decimal, ROUND_HALF_UP
        total = (obj.total_price or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{total:.2f}"

    def get_price(self, obj):
        """Return unit price as string with 2 decimals for consistency"""
        from decimal import Decimal, ROUND_HALF_UP
        value = (obj.price or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"
    
    class Meta:
        model = CartItem
        fields = [
            'id',
            'inventory',
            'quantity',
            'price',
            'total_price',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'price', 'created', 'modified']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for cart with all items"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    
    def get_total_items(self, obj):
        """Get total items; return count of distinct items"""
        # Some UIs expect an integer count, not decimal sum of quantities
        return obj.items.count()
    
    def get_subtotal(self, obj):
        """Get cart subtotal as string with 2 decimals"""
        from decimal import Decimal, ROUND_HALF_UP
        total = (obj.subtotal or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{total:.2f}"
    
    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'items',
            'total_items',
            'subtotal',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'user', 'created', 'modified']


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    inventory_id = serializers.IntegerField(required=True)
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        min_value=Decimal('0.01')
    )
    
    def validate_inventory_id(self, value):
        """Validate that inventory item exists and is active"""
        if not Inventory.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Inventory item not found or not available.")
        return value
    
    def validate(self, data):
        """Validate quantity against available stock"""
        inventory = Inventory.objects.get(id=data['inventory_id'])
        if data['quantity'] > inventory.quantity:
            raise serializers.ValidationError({
                'quantity': f'Insufficient stock. Only {inventory.quantity} available.'
            })
        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.01')
    )
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value
    
    def validate(self, data):
        """Validate quantity against available stock"""
        # Get the cart item instance being updated from context
        instance = self.instance
        if instance and hasattr(instance, 'inventory'):
            inventory = instance.inventory
            if data['quantity'] > inventory.quantity:
                raise serializers.ValidationError({
                    'quantity': f'Insufficient stock. Only {inventory.quantity} available.'
                })
        return data
    

class CheckoutSerializer(serializers.Serializer):
    """Validate checkout details before creating an order from the cart"""

    payment_method = serializers.CharField(required=False, allow_blank=True)
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    delivery_city = serializers.CharField(required=False, allow_blank=True)
    delivery_province = serializers.CharField(required=False, allow_blank=True)
    delivery_district = serializers.CharField(required=False, allow_blank=True)
    delivery_pincode = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    selected_item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text='Optional list of cart item IDs to checkout. If omitted, all items are used.'
    )

    def validate_payment_method(self, value):
        """Ensure provided payment method is supported"""
        if not value:
            return 'cash'
        valid_methods = {choice[0] for choice in Bill.PAYMENT_METHOD_CHOICES}
        if value not in valid_methods:
            raise serializers.ValidationError(
                f"Invalid payment method. Choose from: {', '.join(sorted(valid_methods))}."
            )
        return value

    def validate(self, data):
        """Fill optional fields with safe defaults"""
        data.setdefault('payment_method', 'cash')
        data.setdefault('delivery_address', '')
        data.setdefault('delivery_city', '')
        data.setdefault('delivery_province', '')
        data.setdefault('delivery_district', '')
        data.setdefault('delivery_pincode', '')
        data.setdefault('notes', '')
        # Normalize selected_item_ids if provided
        if 'selected_item_ids' in data and data['selected_item_ids'] is None:
            data['selected_item_ids'] = []
        return data


