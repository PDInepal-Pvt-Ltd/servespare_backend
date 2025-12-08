from django.contrib import admin
from apps.tenant.models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone', 'package', 'status', 'is_active', 'created', 'modified']
    list_filter = ['status', 'is_active', 'package', 'created', 'modified']
    search_fields = ['business_name', 'email', 'phone']
    readonly_fields = ['created', 'modified']
    fieldsets = (
        ('Business Information', {
            'fields': ('business_name', 'email', 'phone', 'is_active')
        }),
        ('Subscription', {
            'fields': ('package', 'status')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )

