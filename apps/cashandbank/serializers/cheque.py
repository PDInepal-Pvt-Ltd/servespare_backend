from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.cashandbank.models import Cheque


class ChequeSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Cheque
        fields = [
            'id',
            'tenant',
            'branch',
            'cheque_type',
            'cheque_number',
            'bank_name',
            'amount',
            'issue_date',
            'due_date',
            'party_name',
            'account_number',
            'ifsc_code',
            'purpose',
            'notes',
            'reminder_setting',
            'is_active',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'tenant', 'created', 'modified']

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
