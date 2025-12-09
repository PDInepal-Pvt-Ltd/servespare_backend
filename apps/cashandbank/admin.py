from django.contrib import admin
from apps.cashandbank.models import BankAccount


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
