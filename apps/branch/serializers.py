from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.branch.models import Branch


class BranchSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
    
    def validate(self, attrs):
        """Validate and auto-set tenant for tenant admins."""
        # Auto-set tenant for tenant admins if not provided
        if not attrs.get('tenant') and self.context.get('request') and self.context['request'].user:
            user = self.context['request'].user
            from apps.base.permission_utils import is_tenant_admin
            
            if is_tenant_admin(user):
                attrs['tenant'] = user.tenant
        
        return super().validate(attrs)
