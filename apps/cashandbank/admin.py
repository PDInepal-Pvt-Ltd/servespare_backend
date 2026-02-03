from django.contrib import admin
from apps.cashandbank.models import BankAccount, CashBalance, ManualEntry, CashTransaction
from apps.cashandbank.models import BankTransfer, CashierShift, ShiftTransaction, AccountLedger
from apps.cashandbank.models import Cheque


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """
    Admin interface for BankAccount with multi-type support.
    Displays type-specific fields based on account_type selection.
    """
    list_display = [
        'account_name',
        'account_type',
        'balance',
        'get_account_identifier',
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
        'account_holder_name',
        'wallet_id'
    ]
    readonly_fields = ['created', 'modified', 'get_account_display_info']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'branch', 'account_type', 'account_name', 'is_active')
        }),
        ('Bank Account Details', {
            'fields': ('bank_name', 'account_number', 'account_holder_name'),
            'description': 'Required for Bank Account type',
            'classes': ('collapse',)
        }),
        ('Digital Wallet Details', {
            'fields': ('wallet_id',),
            'description': 'Required for eSewa or FonePay account types',
            'classes': ('collapse',)
        }),
        ('Account Status', {
            'fields': ('balance', 'get_account_display_info')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = ['tenant', 'branch']
    
    def get_account_identifier(self, obj):
        """Display account identifier based on type"""
        if obj.account_type == 'bank':
            return obj.account_number or '-'
        elif obj.account_type in ['esewa', 'fonepay']:
            return obj.wallet_id or '-'
        return '-'
    get_account_identifier.short_description = 'Account Identifier'
    
    def get_account_display_info(self, obj):
        """Display formatted account information"""
        if not obj.pk:
            return 'Save the account to view details'
        
        info = obj.get_account_display_info()
        if info:
            details = f"Type: {info['type']}\n"
            if info['identifier']:
                details += f"Identifier: {info['identifier']}\n"
            if info['bank']:
                details += f"Bank: {info['bank']}\n"
            if info['holder']:
                details += f"Holder: {info['holder']}\n"
            return details
        return 'N/A'
    get_account_display_info.short_description = 'Account Information'
    
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


@admin.register(CashBalance)
class CashBalanceAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'branch', 'balance', 'last_updated', 'is_active']
    list_filter = ['is_active', 'tenant', 'branch']
    search_fields = ['tenant__name', 'branch__name']
    readonly_fields = ['last_updated', 'created', 'modified']
    
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
        'created', 'modified', 'transaction_date', 'balance'
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




@admin.register(Cheque)
class ChequeAdmin(admin.ModelAdmin):
    list_display = ['cheque_number', 'cheque_type', 'bank_name', 'amount', 'due_date', 'party_name', 'branch', 'tenant', 'is_active', 'created']
    list_filter = ['cheque_type', 'is_active', 'due_date', 'tenant', 'branch']
    search_fields = ['cheque_number', 'party_name', 'bank_name', 'account_number']
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['tenant', 'branch']
    fieldsets = (
        ('Basic Information', {'fields': ('tenant', 'branch', 'cheque_type', 'cheque_number', 'bank_name', 'amount', 'issue_date', 'due_date', 'party_name', 'is_active')}),
        ('Details', {'fields': ('account_number', 'ifsc_code', 'purpose', 'notes', 'reminder_setting'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created', 'modified'), 'classes': ('collapse',)}),
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
