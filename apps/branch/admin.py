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
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow all authenticated users with specific roles to delete branches.
        Roles: SUPER_ADMIN, ADMIN, SUB_ADMIN, CASHIER, INVENTORY_MANAGER, CUSTOMER
        """
        if not request.user or not request.user.is_authenticated:
            return False
        from apps.users.models import User
        allowed_roles = [
            User.Role.SUPER_ADMIN,
            User.Role.ADMIN,
            User.Role.SUB_ADMIN,
            User.Role.CASHIER,
            User.Role.INVENTORY_MANAGER,
            User.Role.CUSTOMER
        ]
        return request.user.role in allowed_roles



    
