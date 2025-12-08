from rest_framework import serializers
from apps.tenant.models import Tenant
from apps.subscription.serializers.subscription_plan import SubscriptionPlanSerializer


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model
    """
    package_detail = SubscriptionPlanSerializer(source='package', read_only=True)
    
    class Meta:
        model = Tenant
        fields = [
            'id',
            'business_name',
            'email',
            'phone',
            'package',
            'package_detail',
            'status',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'created', 'modified', 'package_detail']
    
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

