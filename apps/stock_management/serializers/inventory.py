from rest_framework import serializers
from apps.stock_management.models import Inventory, InventoryImage
from apps.stock_management.serializers.party import PartySerializer


class InventoryImageSerializer(serializers.ModelSerializer):
    """
    Serializer for InventoryImage model
    """
    
    class Meta:
        model = InventoryImage
        fields = [
            'id',
            'inventory',
            'image',
            'description',
            'is_primary',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'created', 'modified']


class InventorySerializer(serializers.ModelSerializer):
    """
    Serializer for Inventory model
    """
    party_detail = PartySerializer(source='party', read_only=True)
    images = InventoryImageSerializer(many=True, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id',
            'item_name',
            'category',
            'vehicle_type',
            'party',
            'party_detail',
            'part_number',
            'hsn_code',
            'quantity',
            'min_stock_level',
            'price',
            'mrp',
            'distributor_price',
            'wholesale_price',
            'retail_pricing',
            'storage_location',
            'warranty_period',
            'barcode',
            'vehicle_bike_details',
            'model',
            'type',
            'images',
            'is_low_stock',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = [
            'id',
            'created',
            'modified',
            'party_detail',
            'images',
            'is_low_stock'
        ]
    
    def validate(self, data):
        """Validate pricing hierarchy: Distributor < Wholesale < Retail < MRP"""
        distributor_price = data.get('distributor_price', self.instance.distributor_price if self.instance else 0)
        wholesale_price = data.get('wholesale_price', self.instance.wholesale_price if self.instance else 0)
        retail_pricing = data.get('retail_pricing', self.instance.retail_pricing if self.instance else 0)
        mrp = data.get('mrp', self.instance.mrp if self.instance else 0)
        
        if distributor_price > 0 and wholesale_price > 0:
            if distributor_price >= wholesale_price:
                raise serializers.ValidationError({
                    'distributor_price': 'Distributor price must be less than Wholesale price.'
                })
        
        if wholesale_price > 0 and retail_pricing > 0:
            if wholesale_price >= retail_pricing:
                raise serializers.ValidationError({
                    'wholesale_price': 'Wholesale price must be less than Retail price.'
                })
        
        if retail_pricing > 0 and mrp > 0:
            if retail_pricing >= mrp:
                raise serializers.ValidationError({
                    'retail_pricing': 'Retail price must be less than MRP.'
                })
        
        return data
    
    def validate_quantity(self, value):
        """Validate quantity"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
    def validate_min_stock_level(self, value):
        """Validate min stock level"""
        if value < 0:
            raise serializers.ValidationError("Minimum stock level cannot be negative.")
        return value

