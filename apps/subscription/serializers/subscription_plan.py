from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.subscription.models import SubscriptionPlan


class SubscriptionPlanSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    """
    Serializer for SubscriptionPlan model
    """
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'plan_name',
            'plan_price',
            'no_of_user',
            'no_of_branch',
            'no_of_product',
            'no_of_user',
            'is_active',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'created', 'modified']
    
    def validate_plan_price(self, value):
        """Validate that plan_price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Plan price must be greater than zero.")
        return value
    
    def validate_no_of_user(self, value):
        """Validate that no_of_user is positive"""
        if value <= 0:
            raise serializers.ValidationError("Number of users must be greater than zero.")
        return value
    
    def validate_no_of_branch(self, value):
        """Validate that no_of_branch is positive"""
        if value <= 0:
            raise serializers.ValidationError("Number of branches must be greater than zero.")
        return value

