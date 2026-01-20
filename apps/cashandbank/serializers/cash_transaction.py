from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin

from apps.cashandbank.models import CashTransaction


class CashTransactionSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    type_label = serializers.CharField(source='get_transaction_type_display', read_only=True)
    signed_amount = serializers.SerializerMethodField()

    class Meta:
        model = CashTransaction
        fields = [
            'id',               # Transaction ID
            'tenant',
            'branch',
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
        read_only_fields = ['id', 'tenant', 'signed_amount', 'type_label', 'created', 'modified']

    def get_signed_amount(self, obj):
        return obj.signed_amount

    def validate_amount(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError('Amount must be non-negative.')
        return value

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
