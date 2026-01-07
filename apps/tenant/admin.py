from django.contrib import admin
from apps.tenant.models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone', 'pan_number', 'location', 'package', 'status', 'is_active', 'created', 'modified']
    list_filter = ['status', 'is_active', 'package', 'created', 'modified']
    search_fields = ['business_name', 'email', 'phone', 'pan_number', 'location']
    readonly_fields = ['created', 'modified']
    fieldsets = (
        ('Business Information', {
            'fields': ('business_name', 'email', 'phone', 'pan_number', 'location', 'is_active')
        }),
        ('Subscription', {
            'fields': ('package', 'status')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow all authenticated users with specific roles to delete tenants.
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

