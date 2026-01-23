from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.cashandbank.models import BankAccount


class BankAccountSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """
    Serializer for BankAccount model with multi-type account support.
    
    Validation rules:
    - BANK: Requires bank_name, account_number
    - ESEWA/FONEPAY: Requires wallet_id
    - CASH: Only account_name required
    """
    
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    account_display_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = BankAccount
        fields = [
            'id',
            'tenant',
            'branch',
            'account_type',
            'account_type_display',
            'account_name',
            'bank_name',
            'account_number',
            'account_holder_name',
            'wallet_id',
            'balance',
            'account_display_info',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'tenant', 'created', 'modified', 'balance', 'account_type_display']
    
    def get_account_display_info(self, obj):
        """Get formatted display information for the account"""
        return obj.get_account_display_info()
    
    def validate(self, data):
        """
        Validate account based on account_type.
        Type-specific field requirements are enforced here.
        """
        account_type = data.get('account_type', self.instance.account_type if self.instance else None)
        
        if not account_type:
            raise serializers.ValidationError({
                'account_type': 'Account type is required.'
            })
        
        # BANK account validation
        if account_type == 'bank':
            bank_name = data.get('bank_name', self.instance.bank_name if self.instance else None)
            account_number = data.get('account_number', self.instance.account_number if self.instance else None)
            
            if not bank_name or not bank_name.strip():
                raise serializers.ValidationError({
                    'bank_name': 'Bank name is required for bank accounts.'
                })
            
            if not account_number or not account_number.strip():
                raise serializers.ValidationError({
                    'account_number': 'Account number is required for bank accounts.'
                })
        
        # ESEWA/FONEPAY wallet validation
        elif account_type in ['esewa', 'fonepay']:
            wallet_id = data.get('wallet_id', self.instance.wallet_id if self.instance else None)
            
            if not wallet_id or not wallet_id.strip():
                account_type_display = dict(BankAccount.ACCOUNT_TYPE_CHOICES).get(account_type, account_type)
                raise serializers.ValidationError({
                    'wallet_id': f'Wallet ID is required for {account_type_display} accounts.'
                })
        
        # CASH account validation (minimal)
        elif account_type == 'cash':
            pass  # Only account_name is required (validated in model)
        
        return data

    def validate_account_name(self, value):
        """Validate account name"""
        if not value or not value.strip():
            raise serializers.ValidationError('Account name is required.')
        if len(value.strip()) > 255:
            raise serializers.ValidationError('Account name cannot exceed 255 characters.')
        return value
    
    def validate_bank_name(self, value):
        """Validate bank name"""
        if value and len(value.strip()) > 255:
            raise serializers.ValidationError('Bank name cannot exceed 255 characters.')
        return value
    
    def validate_account_number(self, value):
        """Validate account number"""
        if value and len(value.strip()) > 100:
            raise serializers.ValidationError('Account number cannot exceed 100 characters.')
        return value
    
    def validate_account_holder_name(self, value):
        """Validate account holder name"""
        if value and len(value.strip()) > 255:
            raise serializers.ValidationError('Account holder name cannot exceed 255 characters.')
        return value
    
    def validate_wallet_id(self, value):
        """Validate wallet ID"""
        if value and len(value.strip()) > 100:
            raise serializers.ValidationError('Wallet ID cannot exceed 100 characters.')
        return value
    
    def validate_balance(self, value):
        """Validate balance"""
        if value is not None and value < 0:
            raise serializers.ValidationError('Balance cannot be negative.')
        return value

    def create(self, validated_data):
        """Create a new bank account with tenant context"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update bank account (prevent tenant override)"""
        validated_data.pop('tenant', None)
        return super().update(instance, validated_data)
