from rest_framework import serializers
from apps.sales.models import Bill


class BillSerializer(serializers.ModelSerializer):
    """
    Serializer for Bill model
    """
    
    class Meta:
        model = Bill
        fields = [
            'id',
            'customer_name',
            'address',
            'phone_numbers',
            'pan_vat_number',
            'customer_type',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'created', 'modified']

