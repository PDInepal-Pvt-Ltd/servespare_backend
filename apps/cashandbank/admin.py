from django.contrib import admin
from apps.cashandbank.models import BankAccount, CashBalance, ManualEntry, CashTransaction
from apps.cashandbank.models import BankTransfer, CashierShift, ShiftTransaction, AccountLedger, SalesLedger, PurchaseLedger


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_name',
        'account_type',
        'balance',
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
            'fields': ('bank_name', 'account_number', 'account_holders_name', 'balance')
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


@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction_type', 'amount', 'transaction_date', 'branch', 'tenant', 'is_active']
    list_filter = ['transaction_type', 'branch', 'tenant', 'is_active']
    search_fields = ['source_description']
    readonly_fields = ['created', 'modified']
    ordering = ['-transaction_date', '-created']
    fieldsets = (
        ('Context', {'fields': ('tenant', 'branch', 'transaction_type', 'is_active')}),
        ('Amount & Timing', {'fields': ('amount', 'transaction_date')}),
        ('Accounts', {'fields': ('from_account', 'to_account')}),
        ('Description', {'fields': ('source_description',)}),
        ('Timestamps', {'fields': ('created', 'modified'), 'classes': ('collapse',)}),
    )


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


@admin.register(BankTransfer)
class BankTransferAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'branch', 'bank_account', 'amount', 'transfer_date', 'is_active']
    list_filter = ['is_active', 'tenant', 'branch']
    search_fields = ['description']
    readonly_fields = ['created', 'modified']
    fieldsets = (
        (None, {'fields': ('bank_account', 'amount', 'description', 'branch', 'tenant')}),
        ('Timestamps', {'fields': ('transfer_date', 'created', 'modified'), 'classes': ('collapse',)}),
    )


@admin.register(CashierShift)
class CashierShiftAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cashier', 'branch', 'status', 'opening_float', 'expected_amount',
        'actual_amount', 'variance_amount', 'is_flagged', 'transferred_to',
        'opened_at', 'closed_at', 'transferred_at'
    ]
    list_filter = ['status', 'is_flagged', 'branch', 'cashier', 'tenant']
    search_fields = ['cashier__username', 'branch__name', 'transferred_to', 'variance_reason', 'notes']
    readonly_fields = ['created', 'modified', 'opened_at', 'closed_at', 'transferred_at']
    ordering = ['-opened_at']

    fieldsets = (
        ('Context', {'fields': ('tenant', 'branch', 'cashier', 'status', 'is_flagged', 'is_active')}),
        ('Opening/Expected', {'fields': ('opening_float', 'expected_amount')}),
        ('Closing/Transfer', {
            'fields': (
                'actual_amount', 'variance_amount', 'variance_reason',
                'transferred_to', 'transferred_by',
            )
        }),
        ('Timestamps', {'fields': ('opened_at', 'closed_at', 'transferred_at', 'created', 'modified'), 'classes': ('collapse',)}),
        ('Notes', {'fields': ('notes',)}),
    )


@admin.register(ShiftTransaction)
class ShiftTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'shift', 'transaction_type', 'amount', 'transaction_date',
        'performed_by', 'reference_type', 'reference_id', 'is_active'
    ]
    list_filter = ['transaction_type', 'is_active', 'shift__tenant']
    search_fields = ['description', 'reference_id', 'shift__id']
    readonly_fields = ['created', 'modified', 'transaction_date']
    ordering = ['-transaction_date']

    fieldsets = (
        ('Context', {'fields': ('shift', 'tenant', 'transaction_type', 'is_active')}),
        ('Details', {'fields': ('amount', 'description', 'reference_type', 'reference_id')}),
        ('Performed By', {'fields': ('performed_by',)}),
        ('Timestamps', {'fields': ('transaction_date', 'created', 'modified'), 'classes': ('collapse',)}),
    )


@admin.register(AccountLedger)
class AccountLedgerAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'shift', 'ledger_type', 'transaction_type', 'debit', 'credit',
        'balance', 'description', 'reference', 'transaction_date', 'performed_by',
        'is_manual_entry', 'is_active'
    ]
    list_filter = [
        'ledger_type', 'transaction_type', 'is_manual_entry', 'is_active',
        'tenant', 'branch', 'transaction_date'
    ]
    search_fields = [
        'description', 'reference', 'reference_id', 'shift__id',
        'performed_by__username'
    ]
    readonly_fields = [
        'created', 'modified', 'transaction_date', 'balance', 'net_amount'
    ]
    ordering = ['-transaction_date', '-id']

    fieldsets = (
        ('Context', {
            'fields': ('tenant', 'branch', 'shift', 'ledger_type', 'transaction_type', 'is_active')
        }),
        ('Transaction Details', {
            'fields': ('debit', 'credit', 'balance')
        }),
        ('Description & Reference', {
            'fields': ('description', 'reference', 'reference_type', 'reference_id')
        }),
        ('Performed By', {
            'fields': ('performed_by', 'is_manual_entry')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('transaction_date', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )


class SalesLedgerAdmin(admin.ModelAdmin):
    """Admin interface for Sales Ledger - Read-only view of sales transactions"""
    
    list_display = [
        'id', 'shift', 'transaction_type', 'debit', 'credit',
        'balance', 'description', 'reference', 'transaction_date', 'performed_by',
        'is_active'
    ]
    list_filter = [
        'transaction_type', 'is_active', 'tenant', 'branch',
        'transaction_date'
    ]
    search_fields = [
        'description', 'reference', 'reference_id', 'shift__id',
        'performed_by__username'
    ]
    readonly_fields = [
        'created', 'modified', 'transaction_date', 'balance', 'debit', 'credit',
        'ledger_type', 'transaction_type', 'description', 'reference', 'reference_type',
        'reference_id', 'performed_by', 'is_manual_entry', 'shift', 'tenant', 'branch', 'notes'
    ]
    ordering = ['-transaction_date', '-id']

    fieldsets = (
        ('Context', {
            'fields': ('tenant', 'branch', 'shift', 'transaction_type', 'is_active')
        }),
        ('Transaction Details', {
            'fields': ('debit', 'credit', 'balance')
        }),
        ('Description & Reference', {
            'fields': ('description', 'reference', 'reference_type', 'reference_id')
        }),
        ('Performed By', {
            'fields': ('performed_by', 'is_manual_entry')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('transaction_date', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter to show only sales ledger entries"""
        qs = super().get_queryset(request)
        return qs.filter(ledger_type='sales')

    def has_add_permission(self, request):
        """Disable adding new entries through admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion through admin"""
        return False


class PurchaseLedgerAdmin(admin.ModelAdmin):
    """Admin interface for Purchase Ledger - Read-only view of purchase transactions"""
    
    list_display = [
        'id', 'shift', 'transaction_type', 'debit', 'credit',
        'balance', 'description', 'reference', 'transaction_date', 'performed_by',
        'is_active'
    ]
    list_filter = [
        'transaction_type', 'is_active', 'tenant', 'branch',
        'transaction_date'
    ]
    search_fields = [
        'description', 'reference', 'reference_id', 'shift__id',
        'performed_by__username'
    ]
    readonly_fields = [
        'created', 'modified', 'transaction_date', 'balance', 'debit', 'credit',
        'ledger_type', 'transaction_type', 'description', 'reference', 'reference_type',
        'reference_id', 'performed_by', 'is_manual_entry', 'shift', 'tenant', 'branch', 'notes'
    ]
    ordering = ['-transaction_date', '-id']

    fieldsets = (
        ('Context', {
            'fields': ('tenant', 'branch', 'shift', 'transaction_type', 'is_active')
        }),
        ('Transaction Details', {
            'fields': ('debit', 'credit', 'balance')
        }),
        ('Description & Reference', {
            'fields': ('description', 'reference', 'reference_type', 'reference_id')
        }),
        ('Performed By', {
            'fields': ('performed_by', 'is_manual_entry')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('transaction_date', 'created', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter to show only purchase ledger entries"""
        qs = super().get_queryset(request)
        return qs.filter(ledger_type='purchase')

    def has_add_permission(self, request):
        """Disable adding new entries through admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion through admin"""
        return False


# Register the specialized ledger admin interfaces
# Using proxy models to allow multiple admin registrations for different ledger types

admin.site.register(SalesLedger, SalesLedgerAdmin)
admin.site.register(PurchaseLedger, PurchaseLedgerAdmin)
