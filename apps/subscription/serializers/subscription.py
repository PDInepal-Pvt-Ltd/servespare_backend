from rest_framework import serializers
from apps.subscription.models import Subscription
from apps.subscription.serializers.subscription_plan import SubscriptionPlanSerializer
from apps.tenant.models import Tenant


class TenantBasicSerializer(serializers.ModelSerializer):
    """Basic tenant serializer for subscription display"""
    class Meta:
        model = Tenant
        fields = ['id', 'business_name', 'email']


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Subscription model
    """
    tenant_detail = TenantBasicSerializer(source='tenant', read_only=True)
    subscription_plan_detail = SubscriptionPlanSerializer(source='subscription_plan', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id',
            'tenant',
            'tenant_detail',
            'subscription_plan',
            'subscription_plan_detail',
            'subscription_date',
            'finish_date',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'created', 'modified', 'tenant_detail', 'subscription_plan_detail']
    
    def validate(self, data):
        """Validate dates"""
        subscription_date = data.get('subscription_date')
        finish_date = data.get('finish_date')
       
        
        if finish_date and subscription_date:
            if finish_date <= subscription_date:
                raise serializers.ValidationError({
                    'finish_date': 'Finish date must be after subscription date.'
                })
        return data

