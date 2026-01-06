from datetime import date
import calendar

from django.contrib import admin, messages
from django.utils.translation import ngettext

from apps.subscription.models import SubscriptionPlan, Subscription
from apps.subscription.models import SubscriberEmail


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
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow all authenticated users with specific roles to delete.
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


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'subscription_plan', 'subscription_date', 'finish_date', 'is_active', 'created', 'modified']
    list_filter = ['is_active', 'subscription_date', 'finish_date', 'created', 'modified']
    search_fields = ['tenant__business_name', 'tenant__email', 'subscription_plan__plan_name']
    readonly_fields = ['created', 'modified']
    fieldsets = (
        ('Subscription Information', {
            'fields': ('tenant', 'subscription_plan', 'is_active')
        }),
        ('Dates', {
            'fields': ('subscription_date', 'finish_date')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    raw_id_fields = ['tenant', 'subscription_plan']

    actions = ['renew_6_months', 'renew_12_months', 'renew_24_months']

    def _add_months(self, original_date: date, months: int) -> date:
        """Return a date with `months` added to `original_date`.

        Handles month overflow and end-of-month correctly.
        """
        if original_date is None:
            return None
        year = original_date.year
        month = original_date.month + months
        # normalize year/month
        year += (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = original_date.day
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)
        return date(year, month, day)

    def _renew_months(self, request, queryset, months: int):
        updated = 0
        for subscription in queryset:
            base_date = subscription.finish_date or subscription.subscription_date
            if not base_date:
                continue
            subscription.finish_date = self._add_months(base_date, months)
            subscription.save()
            updated += 1

        self.message_user(request,
                          ngettext(
                              '%d subscription was successfully renewed by %d months.',
                              '%d subscriptions were successfully renewed by %d months.',
                              updated
                          ) % (updated, months),
                          messages.SUCCESS)

    def renew_6_months(self, request, queryset):
        return self._renew_months(request, queryset, 6)

    renew_6_months.short_description = 'Renew selected subscriptions by 6 months'

    def renew_12_months(self, request, queryset):
        return self._renew_months(request, queryset, 12)

    renew_12_months.short_description = 'Renew selected subscriptions by 12 months'

    def renew_24_months(self, request, queryset):
        return self._renew_months(request, queryset, 24)

    renew_24_months.short_description = 'Renew selected subscriptions by 24 months'
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow all authenticated users with specific roles to delete.
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


@admin.register(SubscriberEmail)
class SubscriberEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'created', 'modified']
    search_fields = ['email']
    readonly_fields = ['created', 'modified']
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow all authenticated users with specific roles to delete.
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
