from rest_framework import serializers
from decimal import Decimal
from typing import Optional, List


class InvoiceItemSerializer(serializers.Serializer):
    """Serializer for Invoice Items"""
    id = serializers.IntegerField(read_only=True)
    item_name = serializers.CharField(max_length=255)
    part_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)
    inventory_details = serializers.SerializerMethodField()
    
    def get_inventory_details(self, obj):
        """Get basic inventory details"""
        if obj.inventory:
            return {
                'id': obj.inventory.id,
                'name': obj.inventory.item_name,
                'part_number': obj.inventory.part_number,
            }
        return None


class InvoiceListSerializer(serializers.Serializer):
    """Serializer for listing invoices"""
    id = serializers.IntegerField(read_only=True)
    invoice_number = serializers.CharField(max_length=50, read_only=True)
    invoice_date = serializers.DateTimeField(read_only=True)
    payment_date = serializers.DateField(read_only=True, allow_null=True)
    customer = serializers.IntegerField()
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = serializers.SerializerMethodField()
    balance_amount = serializers.SerializerMethodField()
    payment_status = serializers.CharField(read_only=True)
    payment_method = serializers.CharField(read_only=True, allow_null=True)
    tenant = serializers.IntegerField(required=False)
    tenant_name = serializers.SerializerMethodField()
    branch = serializers.IntegerField(required=False)
    branch_name = serializers.SerializerMethodField()
    
    def get_tenant_name(self, obj):
        """Get tenant name"""
        return obj.tenant.name if obj.tenant else None
    
    def get_branch_name(self, obj):
        """Get branch name"""
        return obj.branch.name if obj.branch else None
    
    def get_customer_name(self, obj):
        """Get customer full name"""
        return obj.customer.full_name or obj.customer.username
    
    def get_customer_email(self, obj):
        """Get customer email"""
        return obj.customer.email
    
    def get_paid_amount(self, obj):
        """Calculate total paid amount from payments"""
        from django.db.models import Sum
        total_paid = obj.payments.aggregate(Sum('paid_amount'))['paid_amount__sum']
        return total_paid or Decimal('0.00')
    
    def get_balance_amount(self, obj):
        """Calculate balance amount"""
        paid = self.get_paid_amount(obj)
        return obj.total_amount - paid


class InvoiceDetailSerializer(serializers.Serializer):
    """Serializer for invoice details"""
    id = serializers.IntegerField(read_only=True)
    invoice_number = serializers.CharField(max_length=50, read_only=True)
    invoice_date = serializers.DateTimeField(read_only=True)
    payment_date = serializers.DateField(read_only=True, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    customer = serializers.IntegerField()
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    sales_order_number = serializers.SerializerMethodField()
    tenant = serializers.IntegerField(required=False)
    tenant_name = serializers.SerializerMethodField()
    branch = serializers.IntegerField(required=False)
    branch_name = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tax_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_charges = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    paid_amount = serializers.SerializerMethodField()
    balance_amount = serializers.SerializerMethodField()
    payment_status = serializers.CharField(read_only=True)
    payment_method = serializers.CharField(read_only=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    is_paid = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    
    def get_customer_phone(self, obj):
        """Get customer phone"""
        return obj.customer.phone_number if hasattr(obj.customer, 'phone_number') else None

    def get_customer_name(self, obj) -> Optional[str]:
        """Get customer full name"""
        return getattr(obj.customer, 'full_name', None) or getattr(obj.customer, 'username', None)

    def get_customer_email(self, obj) -> Optional[str]:
        """Get customer email"""
        return getattr(obj.customer, 'email', None)
    
    def get_sales_order_number(self, obj):
        """Get associated sales order number"""
        return obj.sales_order.order_number if obj.sales_order else None
    
    def get_tenant_name(self, obj):
        """Get tenant name"""
        return obj.tenant.name if obj.tenant else None
    
    def get_branch_name(self, obj):
        """Get branch name"""
        return obj.branch.name if obj.branch else None
    
    def get_paid_amount(self, obj):
        """Calculate total paid amount from payments"""
        from django.db.models import Sum
        total_paid = obj.payments.aggregate(Sum('paid_amount'))['paid_amount__sum']
        return total_paid or Decimal('0.00')
    
    def get_balance_amount(self, obj):
        """Calculate balance amount"""
        paid = self.get_paid_amount(obj)
        return obj.total_amount - paid
    
    def get_is_paid(self, obj):
        """Check if fully paid"""
        return obj.payment_status == 'paid'
    
    def get_payments(self, obj):
        """Get all payments for this invoice"""
        # Return empty list if no payments relation exists
        if not hasattr(obj, 'payments'):
            return []
        payments = obj.payments.all().order_by('-created')
        # Return payment data as dictionaries instead of using PaymentSerializer
        return [
            {
                'id': p.id,
                'paid_amount': float(p.paid_amount),
                'payment_date': p.payment_date,
                'payment_method': p.payment_method,
            }
            for p in payments
        ] if payments.exists() else []


class InvoiceCreateSerializer(serializers.Serializer):
    """Serializer for creating invoices"""
    due_date = serializers.DateField(required=False, allow_null=True)
    customer = serializers.IntegerField()
    branch = serializers.IntegerField(required=False, allow_null=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_charges = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)


class InvoiceUpdatePaymentSerializer(serializers.Serializer):
    """Serializer for updating invoice payment status"""
    payment_status = serializers.ChoiceField(choices=[
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('on_hold', 'On Hold'),
        ('credit_sale', 'Credit Sale'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ])
    paid_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    payment_method = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True
    )

    def update(self, instance, validated_data):
        # Update payment fields directly on invoice
        payment_status = validated_data.get('payment_status')
        payment_method = validated_data.get('payment_method')
        
        instance.payment_status = payment_status
        if payment_method:
            instance.payment_method = payment_method
        instance.save()
        
        return instance
