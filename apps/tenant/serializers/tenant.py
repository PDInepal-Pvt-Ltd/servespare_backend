from rest_framework import serializers
from apps.tenant.models import Tenant
from apps.subscription.serializers.subscription_plan import SubscriptionPlanSerializer


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model
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
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        queryset = Tenant.objects.filter(email=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A tenant with this email already exists.")
        return value
    
    def validate_business_name(self, value):
        """Validate business name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Business name cannot be empty.")
        return value.strip()

