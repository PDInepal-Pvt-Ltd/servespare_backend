from django.contrib import admin
from django import forms
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
        'order_number', 'tenant', 'branch', 'customer', 'order_date', 'order_status', 
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
        'order', 'tenant', 'branch', 'item_name', 'quantity', 'unit_price', 
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
        'invoice_number', 'tenant', 'branch', 'customer', 'invoice_date', 'payment_date',
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
        'invoice', 'tenant', 'get_branch', 'item_name', 'quantity', 'unit_price', 
        'discount_amount', 'tax_amount', 'line_total'
    ]
    list_filter = ['created']
    search_fields = ['invoice__invoice_number', 'item_name', 'part_number']
    readonly_fields = [
        'item_name', 'part_number',
        'discount_amount', 'tax_amount', 'line_total', 
        'created', 'modified'
    ]
    
    def get_branch(self, obj):
        """Get branch from parent invoice"""
        return obj.invoice.branch if obj.invoice and obj.invoice.branch else '-'
    get_branch.short_description = 'Branch'
    get_branch.admin_order_field = 'invoice__branch'
    
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


class PurchaseItemForm(forms.ModelForm):
    """Custom form for PurchaseItem with price auto-population"""
    
    class Meta:
        model = PurchaseItem
        fields = ['bill', 'inventory', 'quantity', 'price']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make price field optional since it will be auto-populated
        self.fields['price'].required = False
        self.fields['price'].help_text = 'Auto-populated from inventory. Leave blank to auto-fill.'
        self.fields['quantity'].help_text = 'Quantity of items'
        
    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data
        
        # Auto-populate price from inventory if not provided
        if 'inventory' in cleaned_data and cleaned_data.get('inventory'):
            inventory = cleaned_data['inventory']
            if not cleaned_data.get('price'):
                # Use retail_pricing if available, otherwise use base price
                cleaned_data['price'] = inventory.retail_pricing or inventory.price or 0
        
        return cleaned_data


class PurchaseItemInline(admin.TabularInline):
    """Inline admin for PurchaseItem with auto-price from inventory"""
    model = PurchaseItem
    form = PurchaseItemForm
    extra = 1
    fields = ['inventory', 'quantity', 'price']
    readonly_fields = []


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    """Admin interface for Bill model with purchase items inline and ledger integration"""
    
    list_display = [
        'id', 'tenant', 'branch', 'customer_name', 'customer_type', 'subtotal',
        'discount_amount', 'total_after_discount', 'payment_method', 'status', 
        'get_purchase_count', 'created_by', 'created'
    ]
    list_filter = [
        'status', 'payment_method', 'customer_type', 'created'
    ]
    search_fields = [
        'customer_name', 'pan_vat_number', 'phone_numbers'
    ]
    readonly_fields = [
        'created', 'modified', 'subtotal', 'discount_amount', 'total_after_discount', 'created_by'
    ]
    inlines = [PurchaseItemInline]
    
    fieldsets = (
        ('Tenant & Branch', {
            'fields': ('tenant', 'branch', 'created_by')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_type', 'address', 'phone_numbers', 'pan_vat_number')
        }),
        ('Billing Details', {
            'fields': ('price', 'discount_method', 'discount_value', 'subtotal', 'discount_amount', 'total_after_discount', 'payment_method', 'status')
        }),
        ('Ledger Information', {
            'fields': ('is_active',),
            'description': 'Bill automatically syncs to Sales Ledger when created or status changes.'
        }),
        ('Metadata', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def get_purchase_count(self, obj):
        """Display the number of items purchased in this bill"""
        count = obj.purchase_items.count()
        total_qty = sum(float(item.quantity) for item in obj.purchase_items.all())
        return f"{count} items ({total_qty:.1f} qty)"
    get_purchase_count.short_description = 'Items'
    
    def save_formset(self, request, form, formset, change):
        """Auto-populate prices for purchase items before saving"""
        instances = formset.save(commit=False)
        
        for instance in instances:
            # Auto-populate price from inventory if not provided
            if not instance.price and instance.inventory:
                # Use retail_pricing if available, otherwise use base price
                instance.price = instance.inventory.retail_pricing or instance.inventory.price or 0
            instance.save()
        
        formset.save_m2m()
        super().save_formset(request, form, formset, change)
    
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


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    """Admin interface for PurchaseItem model with auto-price from inventory"""
    
    form = PurchaseItemForm
    list_display = [
        'id', 'bill', 'get_tenant', 'get_branch', 'product_name', 'quantity', 'price', 'get_total_price'
    ]
    list_filter = [
        'bill', 'inventory__item_name'
    ]
    search_fields = [
        'inventory__item_name', 'bill__customer_name'
    ]
    readonly_fields = ['get_total_price']
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('bill', 'inventory', 'quantity', 'price', 'get_total_price')
        }),
    )
    
    def get_tenant(self, obj):
        """Get tenant from parent bill"""
        return obj.bill.tenant if obj.bill and obj.bill.tenant else '-'
    get_tenant.short_description = 'Tenant'
    get_tenant.admin_order_field = 'bill__tenant'
    
    def get_branch(self, obj):
        """Get branch from parent bill"""
        return obj.bill.branch if obj.bill and obj.bill.branch else '-'
    get_branch.short_description = 'Branch'
    get_branch.admin_order_field = 'bill__branch'
    
    def product_name(self, obj):
        """Display the product name from related inventory"""
        return obj.inventory.item_name if obj.inventory else '-'
    product_name.short_description = 'Product Name'
    
    def get_total_price(self, obj):
        """Display the calculated total price (quantity × price)"""
        if obj.id:
            return f"₹{obj.total_price()}"
        return '-'
    get_total_price.short_description = 'Total Price (Qty × Price)'
    
    def save_model(self, request, obj, form, change):
        """Auto-populate price from inventory if not provided"""
        if not obj.price and obj.inventory:
            # Use retail_pricing if available, otherwise use base price
            obj.price = obj.inventory.retail_pricing or obj.inventory.price or 0
        super().save_model(request, obj, form, change)
    
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