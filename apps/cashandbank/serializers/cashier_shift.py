from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.cashandbank.models import CashierShift


class CashierShiftSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """
    Serializer for CashierShift model with read-only computed fields.
    """
    
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    is_balanced = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    transaction_summary = serializers.SerializerMethodField()
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
            'notes',
            'is_flagged',
            'is_balanced',
            'duration_minutes',
            'transaction_summary',
            'is_active',
            'created',
            'modified',
        ]
        read_only_fields = [
            'id',
            'tenant',
            'is_balanced',
            'duration_minutes',
            'transaction_summary',
            'created',
            'modified',
            'transferred_at',
            'transferred_by',
        ]

    def get_is_balanced(self, obj):
        """Return whether shift is balanced"""
        return obj.is_balanced

    def get_duration_minutes(self, obj):
        """Return shift duration in minutes"""
        return obj.duration

    def get_transaction_summary(self, obj):
        """Return transaction summary"""
        return obj.get_transaction_summary()

    def create(self, validated_data):
        """Auto-set tenant from request user"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Prevent tenant modification"""
        validated_data.pop('tenant', None)
        return super().update(instance, validated_data)
