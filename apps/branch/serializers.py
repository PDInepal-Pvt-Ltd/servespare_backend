from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.branch.models import Branch


class BranchSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        extra_kwargs = {
            'tenant': {'read_only': True},
        }
    
    def validate(self, attrs):
        """Validate subscription branch limits."""
        # Get tenant from context or from attrs
        tenant = None
        if self.context.get('request') and self.context['request'].user:
            user = self.context['request'].user
            from apps.base.permission_utils import is_tenant_admin, is_super_admin
            
            if is_tenant_admin(user):
                tenant = user.tenant
            elif is_super_admin(user):
                # Super admin - check if tenant is in validated data
                tenant = attrs.get('tenant') if hasattr(self, 'initial_data') else None
        
        if tenant:
            # Check if tenant has a subscription package
            if not tenant.package:
                raise serializers.ValidationError(
                    f'Cannot create branch. Your account does not have an active subscription plan. '
                    f'Please contact support to activate a subscription.'
                )
            
            # Check if tenant has reached their branch limit
            if not tenant.can_add_branch():
                allowed = tenant.get_allowed_branches()
                current = tenant.get_branch_count()
                raise serializers.ValidationError(
                    f'Cannot create branch. Your subscription plan \'{tenant.package.plan_name}\' allows {allowed} branch(es), '
                    f'but you already have {current} active branch(es). '
                    f'Please upgrade your subscription or delete existing unused branches.'
                )
        
        return super().validate(attrs)
