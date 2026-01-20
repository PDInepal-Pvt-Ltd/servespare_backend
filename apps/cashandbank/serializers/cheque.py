from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.cashandbank.models import Cheque


class ChequeSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Cheque
        fields = [
            'id',
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
