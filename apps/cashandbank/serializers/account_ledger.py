from rest_framework import serializers
from apps.cashandbank.models import AccountLedger


class AccountLedgerSerializer(serializers.ModelSerializer):
    """
    Serializer for Account Ledger with complete transaction history and running balance.
    """
    
    performed_by_username = serializers.CharField(
        source='performed_by.username',
        read_only=True,
        allow_null=True
    )

    performed_by_full_name = serializers.CharField(
        source='performed_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    shift_number = serializers.CharField(
        source='shift.id',
        read_only=True,
        allow_null=True
    )

    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True,
        allow_null=True
    )

    # Format date and time separately for frontend
    transaction_date_display = serializers.SerializerMethodField()
    transaction_time_display = serializers.SerializerMethodField()

    class Meta:
        model = AccountLedger
        fields = [
            'id',
            'tenant',
            'branch',
            'branch_name',
            'shift',
            'shift_number',
            'ledger_type',
            'transaction_type',
            'debit',
            'credit',
            'balance',
            'description',
            'reference',
            'reference_type',
            'reference_id',
            'transaction_date',
            'transaction_date_display',
            'transaction_time_display',
            'performed_by',
            'performed_by_username',
            'performed_by_full_name',
            'is_manual_entry',
            'notes',
            'created',
            'modified',
        ]
        read_only_fields = [
            'id',
            'balance',
            'created',
            'modified',
            'performed_by_username',
            'performed_by_full_name',
            'shift_number',
            'branch_name',
            'transaction_date_display',
            'transaction_time_display',
        ]

    def get_transaction_date_display(self, obj):
        """Format date as mm/dd/yyyy"""
        if not obj.transaction_date:
            return None
        return obj.transaction_date.strftime('%m/%d/%Y')

    def get_transaction_time_display(self, obj):
        """Format time as HH:MM AM/PM"""
        if not obj.transaction_date:
            return None
        return obj.transaction_date.strftime('%I:%M %p')


class AccountLedgerListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views with summary data.
    """
    
    performed_by_username = serializers.CharField(
        source='performed_by.username',
        read_only=True,
        allow_null=True
    )

    transaction_date_display = serializers.SerializerMethodField()
    transaction_time_display = serializers.SerializerMethodField()
    shift_reference = serializers.CharField(
        source='shift.id',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = AccountLedger
        fields = [
            'id',
            'ledger_type',
            'transaction_type',
            'description',
            'reference',
            'debit',
            'credit',
            'balance',
            'transaction_date_display',
            'transaction_time_display',
            'performed_by_username',
            'shift_reference',
        ]
        read_only_fields = fields

    def get_transaction_date_display(self, obj):
        """Format date as mm/dd/yyyy"""
        return obj.transaction_date.strftime('%m/%d/%Y')

    def get_transaction_time_display(self, obj):
        """Format time as HH:MM AM/PM"""
        return obj.transaction_date.strftime('%I:%M %p')


class LedgerSummarySerializer(serializers.Serializer):
    """
    Serializer for ledger summary data (totals and statistics).
    """
    
    total_debit = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Total debit (inflow)'
    )
    
    total_credit = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Total credit (outflow)'
    )
    
    net_balance = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Net balance (debit - credit)'
    )
    
    transaction_count = serializers.IntegerField(
        help_text='Total number of transactions'
    )
    
    from_date = serializers.CharField(
        help_text='From date in mm/dd/yyyy format'
    )
    
    to_date = serializers.CharField(
        help_text='To date in mm/dd/yyyy format'
    )
    
    ledger_type = serializers.CharField(
        help_text='Type of ledger'
    )
    
    filtered_by_shift = serializers.BooleanField(
        help_text='Whether filtered by specific shift'
    )
    
    currency = serializers.CharField(
        help_text='Currency code (e.g., Rs)',
        required=False
    )


class SalesSummarySerializer(serializers.Serializer):
    """
    Serializer for sales ledger summary data.
    """
    
    total_customers = serializers.IntegerField(
        help_text='Total number of unique customers'
    )
    
    gross_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Gross sales amount'
    )
    
    return_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Total return/refund amount'
    )
    
    net_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Net sales amount (gross - returns)'
    )
    
    due_remaining = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Outstanding due amount'
    )
    
    number_purchased_products = serializers.FloatField(
        help_text='Total quantity of products purchased/sold'
    )
    
    number_returned_products = serializers.FloatField(
        help_text='Total quantity of products returned'
    )


class PurchaseSummarySerializer(serializers.Serializer):
    """
    Serializer for purchase ledger summary data.
    """
    
    total_suppliers = serializers.IntegerField(
        help_text='Total number of unique suppliers'
    )
    
    gross_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Gross purchase amount'
    )
    
    return_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Total return/refund amount'
    )
    
    net_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Net purchase amount (gross - returns)'
    )
    
    due_remaining = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Outstanding due amount to suppliers'
    )
    
    number_purchased_items = serializers.FloatField(
        help_text='Total quantity of items purchased'
    )
    
    number_returned_items = serializers.FloatField(
        help_text='Total quantity of items returned'
    )


class PurchaseStatisticsSerializer(serializers.Serializer):
    """
    Serializer for purchase ledger statistics for dashboard.
    """
    
    total_suppliers = serializers.IntegerField(
        help_text='Total number of unique suppliers'
    )
    
    gross_amount = serializers.CharField(
        help_text='Gross purchase amount'
    )
    
    return_amount = serializers.CharField(
        help_text='Total return/refund amount'
    )
    
    net_amount = serializers.CharField(
        help_text='Net purchase amount (gross - returns)'
    )
    
    due_remaining = serializers.CharField(
        help_text='Outstanding due amount to suppliers'
    )
    
    number_purchased_items = serializers.FloatField(
        required=False,
        help_text='Total quantity of items purchased'
    )
    
    number_returned_items = serializers.FloatField(
        required=False,
        help_text='Total quantity of items returned'
    )


class SalesStatisticsSerializer(serializers.Serializer):
    """
    Serializer for sales ledger statistics for dashboard.
    """
    
    total_customers = serializers.IntegerField(
        help_text='Total number of unique customers'
    )
    
    gross_amount = serializers.CharField(
        help_text='Gross sales amount'
    )
    
    return_amount = serializers.CharField(
        help_text='Total return/refund amount'
    )
    
    net_amount = serializers.CharField(
        help_text='Net sales amount (gross - returns)'
    )
    
    due_remaining = serializers.CharField(
        help_text='Outstanding due amount from customers'
    )
    
    number_purchased_products = serializers.FloatField(
        required=False,
        help_text='Total quantity of products purchased/sold'
    )
    
    number_returned_products = serializers.FloatField(
        required=False,
        help_text='Total quantity of products returned'
    )
