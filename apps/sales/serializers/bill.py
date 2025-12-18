from rest_framework import serializers
from apps.sales.models import Bill


class BillSerializer(serializers.ModelSerializer):
    """
    Serializer for Bill model
    """
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_after_discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
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
            'price',
            'discount_method',
            'discount_value',
            'discount_amount',
            'total_after_discount',
            'payment_method',
            'status',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'tenant', 'created', 'modified', 'discount_amount', 'total_after_discount']

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

