from rest_framework import serializers
from decimal import Decimal
from apps.carts.models import Cart, CartItem
from apps.stock_management.models import Inventory


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
        """Get the primary image URL"""
        primary_image = obj.images.filter(is_primary=True, is_removed=False).first()
        if primary_image and primary_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    inventory = InventoryBasicSerializer(read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
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
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
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
    
    
