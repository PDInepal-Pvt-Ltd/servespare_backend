from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.sales.models import Bill, PurchaseItem


class PurchaseItemSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """
    Serializer for PurchaseItem model with nested inventory information
    Price auto-populates from inventory if not provided
    """
    total_price = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.CharField(source='inventory.item_name', read_only=True)
    inventory_id = serializers.IntegerField(write_only=True, required=False)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    tenant_id = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    branch_id = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseItem
        fields = [
            'id',
            'bill',
            'inventory',
            'inventory_id',
            'product_name',
            'quantity',
            'price',
            'total_price',
            'tenant_id',
            'tenant_name',
            'branch_id',
            'branch_name',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'total_price', 'created', 'modified', 'product_name']

    def get_tenant_id(self, obj):
        """Tenant ID for this item (from inventory)"""
        return obj.inventory.tenant_id if obj.inventory else None

    def get_tenant_name(self, obj):
        """Tenant display name for this item (from inventory)"""
        return obj.inventory.tenant.business_name if obj.inventory and getattr(obj.inventory, 'tenant', None) else None

    def get_branch_id(self, obj):
        """Branch ID for this item (from inventory)"""
        return obj.inventory.branch_id if obj.inventory else None

    def get_branch_name(self, obj):
        """Branch display name for this item (from inventory)"""
        return obj.inventory.branch.branch_name if obj.inventory and getattr(obj.inventory, 'branch', None) else None

    def get_total_price(self, obj):
        return obj.total_price()

    def create(self, validated_data):
        """Handle inventory_id during creation"""
        inventory_id = validated_data.pop('inventory_id', None)
        if inventory_id:
            from apps.stock_management.models import Inventory
            validated_data['inventory_id'] = inventory_id
        
        # Price will be auto-populated in the model's save() method
        return super().create(validated_data)


class BillSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """
    Serializer for Bill model with nested purchase items
    Supports creating purchase items during bill creation via inventory_id field
    """
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_after_discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    purchase_items = PurchaseItemSerializer(many=True, read_only=True)
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    discount_method_display = serializers.CharField(source='get_discount_method_display', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, required=False, allow_null=True)
    
    # Relationship fields
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    sales_order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    
    # Writable field for adding purchase items during creation
    purchase_items_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text='List of items to add to the bill. Each item must have: inventory_id (int) and quantity (decimal). Price is automatically populated from inventory.'
    )
    
    class Meta:
        model = Bill
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'branch',
            'branch_name',
            'created_by',
            'created_by_username',
            'invoice',
            'invoice_number',
            'sales_order',
            'sales_order_number',
            'customer_name',
            'address',
            'phone_numbers',
            'pan_vat_number',
            'customer_type',
            'customer_type_display',
            'price',
            'subtotal',
            'discount_method',
            'discount_method_display',
            'discount_value',
            'discount_amount',
            'tax_percentage',
            'tax_amount',
            'total_after_discount',
            'payment_method',
            'payment_method_display',
            'status',
            'status_display',
            'purchase_items',
            'purchase_items_data',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = [
            'id',
            'tenant',
            'created_by',
            'created',
            'modified',
            'subtotal',
            'discount_amount',
            'tax_amount',
            'total_after_discount',
            'purchase_items',
            'customer_type_display',
            'status_display',
            'payment_method_display',
            'discount_method_display'
        ]

    def validate(self, attrs):
        price = attrs.get('price', getattr(self.instance, 'price', None))
        discount_method = attrs.get('discount_method', getattr(self.instance, 'discount_method', None))
        discount_value = attrs.get('discount_value', getattr(self.instance, 'discount_value', None))

        errors = {}

        if price is not None and price < 0:
            errors['price'] = 'Price cannot be negative.'

        if discount_value is not None and discount_value < 0:
            errors['discount_value'] = 'Discount value cannot be negative.'

        if discount_method == 'percentage':
            if discount_value is not None and discount_value > 100:
                errors['discount_value'] = 'Percentage discount cannot exceed 100%.'
        elif discount_method == 'amount':
            if discount_value is not None and price is not None and discount_value > price:
                errors['discount_value'] = 'Discount amount cannot exceed the price.'

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        """
        Create bill and associated purchase items
        Price is always auto-populated from inventory
        Validates that quantity information is provided for all items
        """
        # Extract purchase items data before creating bill
        purchase_items_data = validated_data.pop('purchase_items_data', [])
        
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            validated_data.setdefault('created_by', request.user)
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        
        # Create the bill
        bill = super().create(validated_data)
        
        # Create purchase items if provided
        if purchase_items_data:
            from apps.stock_management.models import Inventory
            from decimal import Decimal
            
            for item_data in purchase_items_data:
                inventory_id = item_data.get('inventory_id')
                quantity = item_data.get('quantity')
                
                # Validate inventory_id is provided
                if not inventory_id:
                    raise serializers.ValidationError(
                        'Each purchase item must have inventory_id'
                    )
                
                # Check if quantity information is missing
                if quantity is None:
                    raise serializers.ValidationError(
                        'Quantity information is required for all items. Please provide quantity first.'
                    )
                
                # Validate quantity is a valid number and greater than zero
                try:
                    quantity_decimal = Decimal(str(quantity))
                    if quantity_decimal <= 0:
                        raise serializers.ValidationError(
                            'Quantity must be greater than zero'
                        )
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        'Quantity must be a valid number'
                    )
                
                try:
                    inventory = Inventory.objects.get(id=inventory_id)
                except Inventory.DoesNotExist:
                    raise serializers.ValidationError(
                        f'Inventory with id {inventory_id} does not exist'
                    )
                
                    # Check if inventory quantity is null/missing
                    if inventory.quantity is None:
                        raise serializers.ValidationError(
                            f'Product "{inventory.item_name}" does not have quantity information. Please add quantity to inventory first.'
                        )
                
                    # Check if inventory has enough quantity
                    if inventory.quantity < quantity_decimal:
                        raise serializers.ValidationError(
                            f'Product "{inventory.item_name}" has insufficient stock. Available: {inventory.quantity}, Requested: {quantity_decimal}'
                        )
                
                    # Create purchase item without price - it will be auto-populated from inventory in save()
                PurchaseItem.objects.create(
                    bill=bill,
                    inventory=inventory,
                    quantity=quantity
                    # price is NOT set here - will be auto-populated from inventory in model's save()
                )

            # Recalculate tax after adding purchase items so tax_amount reflects current totals
            bill.save(update_fields=['tax_amount', 'modified'])
        
        return bill

    def update(self, instance, validated_data):
        validated_data.pop('tenant', None)
        return super().update(instance, validated_data)

