from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.carts.models import Favorite
from apps.stock_management.models import Inventory


class InventoryBasicFavoriteSerializer(serializers.ModelSerializer):
    """Basic inventory information for favorite items"""
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


class FavoriteSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """Serializer for favorite products"""
    inventory = InventoryBasicFavoriteSerializer(read_only=True)
    inventory_id = serializers.IntegerField(write_only=True, required=False)
    user_username = serializers.CharField(source='user.username', read_only=True)
    created_date = serializers.DateTimeField(source='created', read_only=True)
    
    class Meta:
        model = Favorite
        fields = [
            'id',
            'inventory',
            'inventory_id',
            'user_username',
            'is_active',
            'created_date',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'created', 'modified']
    
    def validate_inventory_id(self, value):
        """Validate that inventory exists"""
        try:
            inventory = Inventory.objects.get(id=value)
        except Inventory.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
        return value


class AddToFavoriteSerializer(serializers.Serializer):
    """Serializer for adding product to favorites"""
    inventory_id = serializers.IntegerField(required=True)
    
    def validate_inventory_id(self, value):
        """Validate that inventory exists"""
        try:
            Inventory.objects.get(id=value)
        except Inventory.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
        return value


class FavoriteListSerializer(serializers.ModelSerializer):
    """Serializer for listing favorite products"""
    inventory = InventoryBasicFavoriteSerializer(read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    created_date = serializers.DateTimeField(source='created', read_only=True)
    
    class Meta:
        model = Favorite
        fields = [
            'id',
            'inventory',
            'user_username',
            'is_active',
            'created_date',
        ]


class RemoveFromFavoriteSerializer(serializers.Serializer):
    """Serializer for removing product from favorites"""
    inventory_id = serializers.IntegerField(required=True)
    
    def validate_inventory_id(self, value):
        """Validate that inventory exists"""
        try:
            Inventory.objects.get(id=value)
        except Inventory.DoesNotExist:
            raise serializers.ValidationError("Product not found.")
        return value
