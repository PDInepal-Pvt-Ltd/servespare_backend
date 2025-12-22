from django.contrib import admin
from apps.sales.models import SalesOrder, SalesOrderItem, Bill, Invoice, InvoiceItem, PurchaseItem


class SalesOrderItemInline(admin.TabularInline):
    """Inline admin for SalesOrderItem"""
    model = SalesOrderItem
    extra = 1
    fields = [
        'inventory', 'quantity', 'unit_price', 
        'discount_percentage', 'tax_percentage', 'line_total'
    ]
    readonly_fields = ['line_total']


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    """Admin interface for SalesOrder model"""
    
    list_display = [
        'order_number', 'customer', 'order_date', 'order_status', 
        'total_amount', 'created_by'
    ]
    list_filter = [
        'order_status', 'order_date', 'is_active'
    ]
    search_fields = [
        'order_number', 'customer__username', 'customer__full_name',
        'tracking_number', 'notes'
    ]
    readonly_fields = [
        'order_number', 'order_date', 'subtotal', 'discount_amount',
        'tax_amount', 'total_amount', 'created', 'modified'
    ]
    inlines = [SalesOrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'order_date', 'customer', 'order_status', 'is_active')
        }),
        ('Financial Summary', {
            'fields': (
                'subtotal', 'discount_percentage', 'discount_amount',
                'tax_percentage', 'tax_amount', 'shipping_charges', 'total_amount'
            )
        }),
        ('Delivery Address', {
            'fields': (
                'delivery_address', 'delivery_city', 
                'delivery_state', 'delivery_pincode'
            )
        }),
        ('Delivery Details', {
            'fields': (
                'expected_delivery_date', 'actual_delivery_date',
                'tracking_number', 'courier_partner'
            )
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Staff Information', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by when saving"""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    """Admin interface for SalesOrderItem model"""
    
    list_display = [
        'order', 'item_name', 'quantity', 'unit_price', 
        'discount_amount', 'tax_amount', 'line_total'
    ]
    list_filter = ['order__order_status', 'created']
    search_fields = ['order__order_number', 'item_name', 'part_number']
    readonly_fields = [
        'item_name', 'part_number', 'warranty_period',
        'discount_amount', 'tax_amount', 'line_total', 
        'created', 'modified'
    ]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order',)
        }),
        ('Product Information', {
            'fields': ('inventory', 'item_name', 'part_number')
        }),
        ('Pricing', {
            'fields': (
                'quantity', 'unit_price', 
                'discount_percentage', 'discount_amount',
                'tax_percentage', 'tax_amount', 'line_total'
            )
        }),
        ('Additional Information', {
            'fields': ('warranty_period', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


class InvoiceItemInline(admin.TabularInline):
    """Inline admin for InvoiceItem"""
    model = InvoiceItem
    extra = 1
    fields = [
        'inventory', 'quantity', 'unit_price', 
        'discount_percentage', 'tax_percentage', 'line_total'
    ]
    readonly_fields = ['item_name', 'line_total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoice model"""
    
    list_display = [
        'invoice_number', 'customer', 'invoice_date', 'payment_date',
        'total_amount', 'payment_status', 'payment_method', 'created_by'
    ]
    list_filter = [
        'payment_status', 'payment_method', 'invoice_date', 'tenant', 'is_active'
    ]
    search_fields = [
        'invoice_number', 'customer__username', 'customer__full_name',
        'customer__email'
    ]
    readonly_fields = [
        'invoice_number', 'invoice_date', 'subtotal', 'discount_amount',
        'tax_amount', 'total_amount', 'created', 'modified'
    ]
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'invoice_date', 'due_date', 'customer', 'is_active')
        }),
        ('Related Documents', {
            'fields': ('sales_order', 'bill', 'branch', 'tenant')
        }),
        ('Financial Summary', {
            'fields': (
                'subtotal', 'discount_percentage', 'discount_amount',
                'tax_percentage', 'tax_amount', 'shipping_charges', 'total_amount'
            )
        }),
        ('Payment Information', {
            'fields': (
                'payment_status', 'payment_method', 'payment_date'
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Staff Information', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by when saving"""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Admin interface for InvoiceItem model"""
    
    list_display = [
        'invoice', 'item_name', 'quantity', 'unit_price', 
        'discount_amount', 'tax_amount', 'line_total'
    ]
    list_filter = ['created']
    search_fields = ['invoice__invoice_number', 'item_name', 'part_number']
    readonly_fields = [
        'item_name', 'part_number',
        'discount_amount', 'tax_amount', 'line_total', 
        'created', 'modified'
    ]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice',)
        }),
        ('Product Information', {
            'fields': ('inventory', 'item_name', 'part_number')
        }),
        ('Pricing', {
            'fields': (
                'quantity', 'unit_price', 
                'discount_percentage', 'discount_amount',
                'tax_percentage', 'tax_amount', 'line_total'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


class PurchaseItemInline(admin.TabularInline):
    """Inline admin for PurchaseItem"""
    model = PurchaseItem
    extra = 1
    fields = ['product_name', 'quantity', 'price']
    readonly_fields = []


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """Admin interface for Bill model"""
    
    list_display = [
        'id', 'customer_name', 'customer_type', 'payment_method', 'status', 'created'
    ]
    list_filter = [
        'status', 'payment_method', 'customer_type', 'created'
    ]
    search_fields = [
        'customer_name', 'pan_vat_number', 'phone_numbers'
    ]
    readonly_fields = [
        'created', 'modified'
    ]
    inlines = [PurchaseItemInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_type', 'address', 'phone_numbers', 'pan_vat_number')
        }),
        ('Billing Details', {
            'fields': ('price', 'discount_method', 'discount_value', 'payment_method', 'status')
        }),
        ('Metadata', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    """Admin interface for PurchaseItem model"""
    
    list_display = [
        'id', 'bill', 'product_name', 'quantity', 'price'
    ]
    list_filter = [
        'bill', 'product_name'
    ]
    search_fields = [
        'product_name', 'bill__customer_name'
    ]
    readonly_fields = []
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('bill', 'product_name', 'quantity', 'price')
        }),
    )