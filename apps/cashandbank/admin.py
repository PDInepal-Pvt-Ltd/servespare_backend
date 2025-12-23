from django.contrib import admin
from apps.cashandbank.models import BankAccount, CashBalance, ManualEntry


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_name',
        'account_type',
        'bank_name',
        'account_number',
        'account_holders_name',
        'is_active',
        'created',
        'modified'
    ]
    list_filter = [
        'account_type',
        'is_active',
        'created',
        'modified'
    ]
    search_fields = [
        'account_name',
        'bank_name',
        'account_number',
        'account_holders_name'
    ]
    readonly_fields = ['created', 'modified']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_type', 'account_name', 'is_active')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_number', 'account_holders_name')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CashBalance)
class CashBalanceAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'branch', 'balance', 'last_updated', 'is_active']
    list_filter = ['is_active', 'tenant', 'branch']
    search_fields = ['tenant__name', 'branch__name']
    readonly_fields = ['last_updated', 'created', 'modified']


@admin.register(ManualEntry)
class ManualEntryAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'amount', 'branch', 'tenant', 'entry_date', 'is_active']
    list_filter = ['transaction_type', 'is_active', 'tenant', 'branch']
    search_fields = ['description']
    readonly_fields = ['created', 'modified']
    fieldsets = (
        (None, {'fields': ('transaction_type', 'amount', 'description', 'branch', 'tenant')}),
        ('Timestamps', {'fields': ('entry_date', 'created', 'modified'), 'classes': ('collapse',)}),
    )
