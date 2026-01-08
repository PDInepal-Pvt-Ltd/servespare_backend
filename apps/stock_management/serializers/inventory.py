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
            'tenant',
            'branch',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'tenant', 'created', 'modified']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
        # Default branch from inventory if not provided
        if 'branch' not in validated_data and validated_data.get('inventory'):
            inv = validated_data['inventory']
            validated_data['branch'] = getattr(inv, 'branch', None)
        return super().create(validated_data)


class InventorySerializer(serializers.ModelSerializer):
    """
    Serializer for Inventory model
    """
    party_detail = PartySerializer(source='party', read_only=True)
    images = InventoryImageSerializer(many=True, required=False)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id',
            'tenant',
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
            'branch',
            'images',
            'is_low_stock',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = [
            'id',
            'tenant',
            'created',
            'modified',
            'party_detail',
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

    def validate_barcode(self, value):
        """Prevent duplicate barcodes from causing 500s on save."""
        if not value:
            return value

        # Exclude current instance during updates
        qs = Inventory.objects.filter(barcode=value, is_removed=False)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        # Narrow by tenant when available to avoid cross-tenant conflicts
        request = self.context.get('request')
        tenant = getattr(getattr(request, 'user', None), 'tenant', None)
        if tenant:
            qs = qs.filter(tenant=tenant)

        if qs.exists():
            raise serializers.ValidationError('Inventory with this Barcode already exists.')
        return value

    def _create_images(self, inventory, images_data):
        """Create inventory images from nested payload."""
        for image_data in images_data:
            serializer = InventoryImageSerializer(context=self.context, data={**image_data, 'inventory': inventory.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        try:
            inventory = super().create(validated_data)
        except Exception as exc:
            # Surface model validation errors (e.g., unique constraints) as DRF validation errors
            from django.core.exceptions import ValidationError as DjangoValidationError

            if isinstance(exc, DjangoValidationError):
                raise serializers.ValidationError(exc.message_dict)
            raise
        if images_data:
            self._create_images(inventory, images_data)
        return inventory

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        # Prevent tenant override through serializer
        validated_data.pop('tenant', None)
        inventory = super().update(instance, validated_data)

        # If images are provided, replace existing set with the new payload
        if images_data is not None:
            instance.images.all().delete()
            if images_data:
                self._create_images(inventory, images_data)

        return inventory

