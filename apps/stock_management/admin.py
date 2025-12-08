from django.contrib import admin
from apps.stock_management.models import Party, PurchaseOrder, PurchaseOrderItem, Inventory, InventoryImage


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = [
        'party_name',
        'party_type',
        'customer_type',
        'contact_person',
        'phone',
        'email',
        'city',
        'payment_terms',
        'is_active',
        'created',
        'modified'
    ]
    list_filter = [
        'party_type',
        'customer_type',
        'payment_terms',
        'is_active',
        'city',
        'state_province',
        'created',
        'modified'
    ]
    search_fields = [
        'party_name',
        'contact_person',
        'phone',
        'email',
        'pan_number',
        'city'
    ]
    readonly_fields = ['created', 'modified']
    
    fieldsets = (
        ('Party Type', {
            'fields': ('party_type', 'customer_type', 'is_active')
        }),
        ('Basic Information', {
            'fields': ('party_name', 'contact_person')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address', 'city', 'state_province')
        }),
        ('Financial Information', {
            'fields': ('pan_number', 'payment_terms', 'credit_limit', 'opening_balance')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to show/hide customer_type based on party_type"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add JavaScript to show/hide customer_type field based on party_type
        if 'party_type' in form.base_fields:
            form.base_fields['party_type'].widget.attrs.update({
                'onchange': 'toggleCustomerType()'
            })
        
        return form
    
    class Media:
        js = ('admin/js/party_admin.js',)


class PurchaseOrderItemInline(admin.TabularInline):
    """Inline admin for Purchase Order Items"""
    model = PurchaseOrderItem
    extra = 1
    fields = [
        'item_name',
        'part_number',
        'quantity',
        'unit_price',
        'tax',
        'discount_description',
        'is_active'
    ]
    readonly_fields = []


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number',
        'supplier',
        'status',
        'order_date',
        'expected_delivery_date',
        'total_amount',
        'is_active',
        'created',
        'modified'
    ]
    list_filter = [
        'status',
        'order_date',
        'is_active',
        'supplier',
        'created',
        'modified'
    ]
    search_fields = [
        'po_number',
        'supplier__party_name',
        'notes'
    ]
    readonly_fields = ['created', 'modified', 'total_amount']
    raw_id_fields = ['supplier']
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('po_number', 'status', 'supplier', 'is_active')
        }),
        ('Dates', {
            'fields': ('order_date', 'expected_delivery_date')
        }),
        ('Documents', {
            'fields': ('purchase_invoice',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_and_condition')
        }),
        ('Summary', {
            'fields': ('total_amount',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def total_amount(self, obj):
        """Display total amount"""
        if obj.pk:
            return f"${obj.total_amount:.2f}"
        return "-"
    total_amount.short_description = 'Total Amount'


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'purchase_order',
        'item_name',
        'part_number',
        'quantity',
        'unit_price',
        'tax',
        'total_price',
        'is_active'
    ]
    list_filter = [
        'is_active',
        'purchase_order__status',
        'purchase_order',
        'created',
        'modified'
    ]
    search_fields = [
        'item_name',
        'part_number',
        'purchase_order__po_number'
    ]
    readonly_fields = ['created', 'modified', 'subtotal', 'tax_amount', 'total_price']
    raw_id_fields = ['purchase_order']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('purchase_order', 'item_name', 'part_number', 'is_active')
        }),
        ('Pricing', {
            'fields': ('quantity', 'unit_price', 'tax', 'discount_description')
        }),
        ('Calculations', {
            'fields': ('subtotal', 'tax_amount', 'total_price'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def subtotal(self, obj):
        """Display subtotal"""
        if obj.pk:
            return f"${obj.subtotal:.2f}"
        return "-"
    subtotal.short_description = 'Subtotal'
    
    def tax_amount(self, obj):
        """Display tax amount"""
        if obj.pk:
            return f"${obj.tax_amount:.2f}"
        return "-"
    tax_amount.short_description = 'Tax Amount'
    
    def total_price(self, obj):
        """Display total price"""
        if obj.pk:
            return f"${obj.total_price:.2f}"
        return "-"
    total_price.short_description = 'Total Price'


class InventoryImageInline(admin.TabularInline):
    """Inline admin for Inventory Images"""
    model = InventoryImage
    extra = 1
    fields = ['image', 'description', 'is_primary', 'is_active']
    readonly_fields = []


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = [
        'item_name',
        'category',
        'vehicle_type',
        'part_number',
        'quantity',
        'min_stock_level',
        'mrp',
        'is_low_stock',
        'is_active',
        'created',
        'modified'
    ]
    list_filter = [
        'category',
        'vehicle_type',
        'warranty_period',
        'is_active',
        'party',
        'created',
        'modified'
    ]
    search_fields = [
        'item_name',
        'part_number',
        'hsn_code',
        'barcode',
        'model',
        'type'
    ]
    readonly_fields = ['created', 'modified', 'is_low_stock']
    raw_id_fields = ['party']
    inlines = [InventoryImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('item_name', 'category', 'vehicle_type', 'party', 'is_active')
        }),
        ('Part Information', {
            'fields': ('part_number', 'hsn_code', 'barcode')
        }),
        ('Stock Information', {
            'fields': ('quantity', 'min_stock_level', 'storage_location', 'is_low_stock')
        }),
        ('Pricing Information', {
            'fields': ('price', 'mrp')
        }),
        ('Three Tier Pricing', {
            'fields': ('distributor_price', 'wholesale_price', 'retail_pricing'),
            'description': 'Pricing Tip: Distributor < Wholesale < Retail < MRP'
        }),
        ('Warranty', {
            'fields': ('warranty_period',)
        }),
        ('Vehicle Details', {
            'fields': ('vehicle_bike_details', 'model', 'type')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def is_low_stock(self, obj):
        """Display low stock status"""
        if obj.pk:
            return obj.is_low_stock
        return False
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'


@admin.register(InventoryImage)
class InventoryImageAdmin(admin.ModelAdmin):
    list_display = [
        'inventory',
        'image',
        'is_primary',
        'is_active',
        'created',
        'modified'
    ]
    list_filter = [
        'is_primary',
        'is_active',
        'created',
        'modified'
    ]
    search_fields = [
        'inventory__item_name',
        'description'
    ]
    readonly_fields = ['created', 'modified']
    raw_id_fields = ['inventory']
    
    fieldsets = (
        ('Image Information', {
            'fields': ('inventory', 'image', 'description', 'is_primary', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
