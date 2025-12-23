from rest_framework import serializers
from apps.cashandbank.models import ManualEntry


class ManualEntrySerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = ManualEntry
        fields = [
            'id', 'tenant', 'branch', 'transaction_type', 'type_label', 'amount', 'description', 'entry_date', 'is_active', 'created', 'modified'
        ]
        read_only_fields = ['id', 'type_label', 'created', 'modified']

    def validate_amount(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError('Amount must be a non-negative value.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('tenant', request.user.tenant)
            if 'branch' not in validated_data and getattr(request.user, 'branch', None):
                validated_data['branch'] = request.user.branch
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # prevent tenant override
        validated_data.pop('tenant', None)
        return super().update(instance, validated_data)
