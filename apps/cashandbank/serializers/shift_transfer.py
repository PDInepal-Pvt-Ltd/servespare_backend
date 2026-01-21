from rest_framework import serializers
from decimal import Decimal
from apps.cashandbank.models import CashierShift
from apps.users.models import User


class ShiftTransferInputSerializer(serializers.Serializer):
    """
    Serializer for validating shift transfer input.
    
    Accepts:
    - counted_cash: Decimal amount of cash counted before transfer
    - transferred_to_id: ID of target cashier (User)
    - variance_reason: Optional reason if variance occurs
    """
    
    counted_cash = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=True,
        help_text='Amount of cash counted before transfer'
    )
    
    transferred_to_id = serializers.IntegerField(
        required=True,
        help_text='ID of the target cashier user'
    )
    
    variance_reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='Optional reason for variance'
    )

    def validate_counted_cash(self, value):
        """Validate that counted_cash is non-negative"""
        if value <= 0:
            raise serializers.ValidationError('Counted cash must be greater than zero')
        return value

    def validate_transferred_to_id(self, value):
        """Validate that transferred_to_id user exists and is a cashier"""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Target cashier user does not exist')
        
        if user.role != User.Role.CASHIER:
            raise serializers.ValidationError('Target user must be a cashier')
        
        if user.status != User.Status.ACTIVE:
            raise serializers.ValidationError('Target cashier must be active')
        
        return user


class ShiftTransferVarianceSerializer(serializers.Serializer):
    """
    Serializer for variance response when transfer has variance.
    
    Used to alert the caller that variance exists before completing transfer.
    """
    
    expected_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
        help_text='Expected amount before transfer'
    )
    
    counted_cash = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
        help_text='Actual counted cash'
    )
    
    variance_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
        help_text='Difference between counted and expected'
    )
    
    has_variance = serializers.BooleanField(
        read_only=True,
        help_text='Whether variance exists'
    )
    
    will_be_flagged = serializers.BooleanField(
        read_only=True,
        help_text='Whether shift will be auto-flagged (|variance| > 100)'
    )


class ShiftTransferOutputSerializer(serializers.ModelSerializer):
    """
    Serializer for completed shift transfer.
    
    Returns the updated shift with transfer details.
    """
    
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    transferred_by_name = serializers.CharField(source='transferred_by.username', read_only=True)

    class Meta:
        model = CashierShift
        fields = [
            'id',
            'tenant',
            'branch',
            'branch_name',
            'cashier',
            'cashier_name',
            'status',
            'opening_float',
            'opened_at',
            'expected_amount',
            'actual_amount',
            'closed_at',
            'variance_amount',
            'variance_reason',
            'transferred_to',
            'transferred_at',
            'transferred_by',
            'transferred_by_name',
            'is_flagged',
            'notes',
            'created',
            'modified',
        ]
        read_only_fields = [
            'id',
            'tenant',
            'created',
            'modified',
            'status',
            'closed_at',
            'transferred_at',
        ]
