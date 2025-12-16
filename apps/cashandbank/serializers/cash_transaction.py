from rest_framework import serializers

from apps.cashandbank.models import CashTransaction


class CashTransactionSerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source='get_transaction_type_display', read_only=True)
    signed_amount = serializers.SerializerMethodField()

    class Meta:
        model = CashTransaction
        fields = [
            'id',               # Transaction ID
            'transaction_type',
            'type_label',
            'source_description',
            'amount',
            'signed_amount',
            'transaction_date',
            'is_active',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'signed_amount', 'type_label', 'created', 'modified']

    def get_signed_amount(self, obj):
        return obj.signed_amount

    def validate_amount(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError('Amount must be non-negative.')
        return value
