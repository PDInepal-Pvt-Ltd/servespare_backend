from rest_framework import serializers
from apps.cashandbank.models import CashBalance


class CashBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashBalance
        fields = [
            'id', 'tenant', 'branch', 'balance', 'last_updated', 'is_active', 'created', 'modified'
        ]
        read_only_fields = ['id', 'last_updated', 'created', 'modified']

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
