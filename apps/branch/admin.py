from django.contrib import admin
from apps.base.admin import TenantAdminMixin

# Register your models here.
from .models import Branch


@admin.register(Branch)
class BranchAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('branch_name', 'branch_code', 'tenant', 'city', 'state', 'phone', 'Email')
    search_fields = ('branch_name', 'branch_code', 'tenant__name', 'city', 'state', 'Email')
    list_filter = ('city', 'state', 'tenant')
    ordering = ('branch_name',)
    
    def save_model(self, request, obj, form, change):
        """Override save_model to check subscription limits before adding new branches."""
        from apps.users.utils import send_subscription_limit_exceeded_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        # Check subscription limit only when creating new branches
        if not change:  # change=False means we're adding a new branch
            tenant = obj.tenant
            if tenant:
                # Check if tenant has a subscription package
                if not tenant.package:
                    raise DjangoValidationError(
                        f'Cannot create branch. Tenant "{tenant.business_name}" does not have an active subscription plan. '
                        f'Please assign a subscription plan first.'
                    )
                
                # Check if tenant has reached their branch limit
                if not tenant.can_add_branch():
                    allowed = tenant.get_allowed_branches()
                    current = tenant.get_branch_count()
                    # Send limit exceeded email to tenant admin
                    send_subscription_limit_exceeded_email(
                        tenant,
                        'branches',
                        current,
                        allowed
                    )
                    raise DjangoValidationError(
                        f'Cannot create branch. Tenant "{tenant.business_name}" subscription plan (\'{tenant.package.plan_name}\') '
                        f'allows {allowed} branch(es), but already has {current} active branch(es). '
                        f'Please upgrade subscription or delete existing unused branches. '
                        f'Notification email sent to tenant admin.'
                    )
        
        super().save_model(request, obj, form, change) 



    
