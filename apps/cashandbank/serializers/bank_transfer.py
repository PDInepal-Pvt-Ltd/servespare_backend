from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin

from apps.cashandbank.models import BankTransfer


class BankTransferSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    bank_name = serializers.CharField(source='bank_account.bank_name', read_only=True)

    class Meta:
        model = BankTransfer
        fields = [
            'id', 'tenant', 'branch', 'bank_account', 'bank_name', 'amount', 'description', 'transfer_date', 'is_active', 'created', 'modified'
        ]
        read_only_fields = ['id', 'tenant', 'bank_name', 'created', 'modified']

    def validate_amount(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError('Amount must be a non-negative value.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # prevent tenant override
        validated_data.pop('tenant', None)
        return super().update(instance, validated_data)
