from django.contrib import admin
from apps.subscription.models import SubscriptionPlan, Subscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_name', 'plan_price', 'no_of_user', 'no_of_branch', 'is_active', 'created', 'modified']
    list_filter = ['is_active',  'created', 'modified']
    search_fields = ['plan_name']
    readonly_fields = ['created', 'modified']
    fieldsets = (
        ('Plan Information', {
            'fields': ('plan_name', 'plan_price', 'is_active')
        }),
        ('Limits', {
            'fields': ('no_of_user', 'no_of_branch')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'subscription_plan', 'subscription_date', 'finish_date', 'renew_date', 'is_active', 'created', 'modified']
    list_filter = ['is_active', 'subscription_date', 'finish_date', 'created', 'modified']
    search_fields = ['tenant__business_name', 'tenant__email', 'subscription_plan__plan_name']
    readonly_fields = ['created', 'modified']
    fieldsets = (
        ('Subscription Information', {
            'fields': ('tenant', 'subscription_plan', 'is_active')
        }),
        ('Dates', {
            'fields': ('subscription_date', 'finish_date', 'renew_date')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ['tenant', 'subscription_plan']
