from rest_framework import serializers
from apps.sales.models import Bill, PurchaseItem


class PurchaseItemSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseItem model
    """
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseItem
        fields = [
            'id',
            'bill',
            'product_name',
            'quantity',
            'price',
            'total_price'
        ]
        read_only_fields = ['id', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()


class BillSerializer(serializers.ModelSerializer):
    """
    Serializer for Bill model with nested purchase items
    """
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_after_discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    purchase_items = PurchaseItemSerializer(many=True, read_only=True)
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    discount_method_display = serializers.CharField(source='get_discount_method_display', read_only=True)
    
    class Meta:
        model = Bill
        fields = [
            'id',
            'tenant',
            'branch',
            'customer_name',
            'address',
            'phone_numbers',
            'pan_vat_number',
            'customer_type',
            'customer_type_display',
            'price',
            'discount_method',
            'discount_method_display',
            'discount_value',
            'discount_amount',
            'total_after_discount',
            'payment_method',
            'payment_method_display',
            'status',
            'status_display',
            'purchase_items',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = [
            'id',
            'tenant',
            'created',
            'modified',
            'discount_amount',
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
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('tenant', None)
        return super().update(instance, validated_data)

