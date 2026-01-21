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
        
        if tenant and not tenant.can_add_branch():
            raise serializers.ValidationError(
                f'Cannot create branch. Your subscription plan allows {tenant.get_allowed_branches()} branches, '
                f'but you already have {tenant.get_branch_count()} active branches. '
                f'Please upgrade your subscription or delete existing unused branches.'
            )
        
        return super().validate(attrs)
