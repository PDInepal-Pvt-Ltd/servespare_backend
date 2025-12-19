from rest_framework import serializers
from apps.cashandbank.models import BankAccount


class BankAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for BankAccount model
    """
    
    class Meta:
        model = BankAccount
        fields = [
            'id',
            'tenant',
            'branch',
            'account_type',
            'account_name',
            'bank_name',
            'account_number',
            'account_holders_name',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'tenant', 'created', 'modified']
    
    def validate(self, data):
        """Validate that bank_name is provided for bank_account type"""
        account_type = data.get('account_type', self.instance.account_type if self.instance else None)
        bank_name = data.get('bank_name', self.instance.bank_name if self.instance else None)
        
        if account_type == 'bank_account' and not bank_name:
            raise serializers.ValidationError({
                'bank_name': 'Bank name is required when account type is Bank Account.'
            })
        
        return data

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

