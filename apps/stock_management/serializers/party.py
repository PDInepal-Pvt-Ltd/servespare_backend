from rest_framework import serializers
from apps.stock_management.models import Party


class PartySerializer(serializers.ModelSerializer):
    """
    Serializer for Party model
    """
    
    class Meta:
        model = Party
        fields = [
            'id',
            'tenant',
            'branch',
            'party_type',
            'customer_type',
            'party_name',
            'contact_person',
            'phone',
            'email',
            'address',
            'city',
            'state_province',
            'pan_number',
            'payment_terms',
            'credit_limit',
            'opening_balance',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'tenant', 'created', 'modified']
    
    def validate(self, data):
        """Validate that customer_type is set when party_type is customer"""
        party_type = data.get('party_type', self.instance.party_type if self.instance else None)
        customer_type = data.get('customer_type', self.instance.customer_type if self.instance else None)
        
        if party_type == 'customer' and not customer_type:
            raise serializers.ValidationError({
                'customer_type': 'Customer type is required when party type is Customer.'
            })
        
        if party_type == 'supplier' and customer_type:
            raise serializers.ValidationError({
                'customer_type': 'Customer type should not be set for suppliers.'
            })
        
        return data
    
    def validate_credit_limit(self, value):
        """Validate credit limit"""
        if value < 0:
            raise serializers.ValidationError("Credit limit cannot be negative.")
        return value
    
    def validate_opening_balance(self, value):
        """Validate opening balance"""
        return value  # Opening balance can be negative (debit/credit)

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            # If branch not provided and user has a branch, set it
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            # Prevent tenant tampering via serializer
            validated_data.pop('tenant', None)
            # Default branch if none provided
            if 'branch' not in validated_data and getattr(request.user, 'branch', None) and instance.branch is None:
                validated_data['branch'] = request.user.branch
        return super().update(instance, validated_data)

