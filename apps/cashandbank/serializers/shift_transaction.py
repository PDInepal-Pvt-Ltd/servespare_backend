from rest_framework import serializers
from apps.cashandbank.models import ShiftTransaction


class ShiftTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for ShiftTransaction model.
    """
    
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.username', read_only=True)
    signed_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ShiftTransaction
        fields = [
            'id',
            'shift',
            'tenant',
            'transaction_type',
            'transaction_type_display',
            'amount',
            'signed_amount',
            'description',
            'reference_type',
            'reference_id',
            'transaction_date',
            'performed_by',
            'performed_by_name',
            'is_active',
            'created',
            'modified',
        ]
        read_only_fields = [
            'id',
            'tenant',
            'transaction_type_display',
            'signed_amount',
            'created',
            'modified',
        ]

    def create(self, validated_data):
        """Auto-set tenant and performed_by from request user"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            validated_data.setdefault('performed_by', request.user)
        return super().create(validated_data)
