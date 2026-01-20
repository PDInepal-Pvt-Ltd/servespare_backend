from rest_framework import serializers
from apps.tenant.models import Tenant
from apps.subscription.serializers.subscription_plan import SubscriptionPlanSerializer


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model
    All validation logic is handled in the model's clean() method
    """
    package_detail = SubscriptionPlanSerializer(source='package', read_only=True)
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id',
            'business_name',
            'email',
            'phone',
            'pan_number',
            'location',
            'province',
            'district',
            'package',
            'package_detail',
            'status',
            'is_active',
            'user_count',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'created', 'modified', 'package_detail', 'user_count']
    
    def get_user_count(self, obj):
        """Get the total number of active users in this tenant"""
        return obj.get_user_count()
