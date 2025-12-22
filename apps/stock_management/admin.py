import csv
import io
from decimal import Decimal, InvalidOperation
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import HttpResponse
from apps.stock_management.models import Party, PurchaseOrder, PurchaseOrderItem, Inventory, InventoryImage
from apps.stock_management.serializers import InventorySerializer


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
        'tenant',
        'branch',
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
        'tenant',
        'branch',
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
    raw_id_fields = ['party', 'tenant', 'branch']
    inlines = [InventoryImageInline]
    
    fieldsets = (
        ('Context', {
            'fields': ('tenant', 'branch')
        }),
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

    # Mirror fieldsets on the add form so tenant/branch are available when creating
    add_fieldsets = fieldsets
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='stock_management_inventory_bulk_upload'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['bulk_upload_url'] = 'admin:stock_management_inventory_bulk_upload'
        return super().changelist_view(request, extra_context=extra_context)
    
    def bulk_upload_view(self, request):
        """
        Custom admin view for bulk CSV upload
        """
        if request.method == 'POST':
            if 'csv_file' not in request.FILES:
                messages.error(request, 'Please select a CSV file to upload.')
                return render(request, 'admin/stock_management/inventory/bulk_upload.html', {
                    'title': 'Bulk Upload Inventory Items',
                    'opts': self.model._meta,
                    'has_view_permission': True,
                })
            
            csv_file = request.FILES['csv_file']
            
            # Check if file is CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Invalid file type. Please upload a CSV file.')
                return render(request, 'admin/stock_management/inventory/bulk_upload.html', {
                    'title': 'Bulk Upload Inventory Items',
                    'opts': self.model._meta,
                    'has_view_permission': True,
                })
            
            # Process CSV
            result = self.process_bulk_upload(csv_file)
            
            # Show messages
            if result['successful'] > 0:
                messages.success(request, f'Successfully imported {result["successful"]} inventory item(s).')
            if result['failed'] > 0:
                messages.warning(request, f'Failed to import {result["failed"]} inventory item(s). Check the details below.')
            
            return render(request, 'admin/stock_management/inventory/bulk_upload_result.html', {
                'title': 'Bulk Upload Results',
                'opts': self.model._meta,
                'has_view_permission': True,
                'result': result,
            })
        
        return render(request, 'admin/stock_management/inventory/bulk_upload.html', {
            'title': 'Bulk Upload Inventory Items',
            'opts': self.model._meta,
            'has_view_permission': True,
        })
    
    def process_bulk_upload(self, csv_file):
        """
        Process CSV file and import inventory items
        """
        # Read CSV file
        try:
            decoded_file = csv_file.read().decode('utf-8-sig')  # Handle BOM
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Check if CSV has any rows
            if not reader.fieldnames:
                return {
                    'total_rows': 0,
                    'successful': 0,
                    'failed': 0,
                    'successful_imports': [],
                    'failed_imports': [{'row': 0, 'errors': ['CSV file is empty or invalid']}]
                }
        except Exception as e:
            return {
                'total_rows': 0,
                'successful': 0,
                'failed': 0,
                'successful_imports': [],
                'failed_imports': [{'row': 0, 'errors': [f'Error reading CSV file: {str(e)}']}]
            }
        
        # Field mapping from CSV column names to model fields
        field_mapping = {
            'Item Name': 'item_name',
            'Item Name*': 'item_name',
            'Part Number': 'part_number',
            'Part Number*': 'part_number',
            'Category': 'category',
            'Category*': 'category',
            'Category (local/original)': 'category',
            'Category* (local/original)': 'category',
            'Vehicle Type': 'vehicle_type',
            'Vehicle Type*': 'vehicle_type',
            'Vehicle Type (two_wheeler/four_wheeler)': 'vehicle_type',
            'Vehicle Type* (two_wheeler/four_wheeler)': 'vehicle_type',
            'Vehicle Name': 'vehicle_bike_details',
            'Bike Model': 'model',
            'Bike Type': 'type',
            'HSN Code': 'hsn_code',
            'Quantity': 'quantity',
            'Quantity*': 'quantity',
            'Min Stock Level': 'min_stock_level',
            'Min Stock Level*': 'min_stock_level',
            'Price': 'price',
            'Price*': 'price',
            'MRP': 'mrp',
            'MRP*': 'mrp',
            'Retail Price': 'retail_pricing',
            'Wholesale Price': 'wholesale_price',
            'Distributor Price': 'distributor_price',
            'Supplier/Party Name': 'party_name',
            'Supplier/Party Name*': 'party_name',
            'Barcode': 'barcode',
            'Location': 'storage_location',
            'Warranty Period (months)': 'warranty_period',
        }
        
        # Required fields
        required_fields = ['item_name', 'part_number', 'category', 'vehicle_type', 'quantity', 'min_stock_level', 'price', 'mrp']
        
        successful_imports = []
        failed_imports = []
        
        # Process each row
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
            try:
                # Skip completely empty rows
                if not any(str(v).strip() if v is not None else '' for v in row.values()):
                    continue
                
                # Map CSV columns to model fields
                inventory_data = {}
                errors = []
                
                # Process each field in the mapping
                for csv_col, model_field in field_mapping.items():
                    if csv_col in row and row[csv_col] is not None:
                        # Handle None and empty strings
                        value_str = str(row[csv_col]).strip() if row[csv_col] else ''
                        if not value_str:
                            continue
                        value = value_str
                        
                        # Special handling for different field types
                        if model_field == 'category':
                            value = value.lower()
                            if value not in ['local', 'original']:
                                errors.append(f"Category must be 'local' or 'original', got '{value}'")
                                continue
                        
                        elif model_field == 'vehicle_type':
                            value = value.lower()
                            if value not in ['two_wheeler', 'four_wheeler']:
                                errors.append(f"Vehicle Type must be 'two_wheeler' or 'four_wheeler', got '{value}'")
                                continue
                        
                        elif model_field in ['quantity', 'min_stock_level', 'price', 'mrp', 'retail_pricing', 'wholesale_price', 'distributor_price']:
                            try:
                                value = Decimal(str(value))
                                if value < 0:
                                    errors.append(f"{csv_col} cannot be negative")
                                    continue
                            except (InvalidOperation, ValueError):
                                errors.append(f"{csv_col} must be a valid number, got '{value}'")
                                continue
                        
                        elif model_field == 'warranty_period':
                            # Convert numeric months to warranty period format
                            try:
                                months = int(value)
                                if months == 0:
                                    value = 'no_warranty'
                                elif months == 1:
                                    value = '1_month'
                                elif months == 2:
                                    value = '2_month'
                                elif months == 3:
                                    value = '3_month'
                                elif months == 4:
                                    value = '4_month'
                                elif months == 5:
                                    value = '5_month'
                                elif months == 6:
                                    value = '6_month'
                                elif months == 9:
                                    value = '9_month'
                                elif months == 12:
                                    value = '12_month'
                                elif months == 24:
                                    value = '24_month'
                                else:
                                    errors.append(f"Warranty Period must be one of: 0, 1, 2, 3, 4, 5, 6, 9, 12, 24 months")
                                    continue
                            except ValueError:
                                # If already in format like "6_month", use as is
                                if value not in [choice[0] for choice in Inventory.WARRANTY_PERIOD_CHOICES]:
                                    errors.append(f"Invalid warranty period format: '{value}'")
                                    continue
                        
                        elif model_field == 'party_name':
                            # Lookup party by name
                            party = Party.objects.filter(party_name__iexact=value, is_active=True).first()
                            if party:
                                inventory_data['party'] = party.id
                            else:
                                errors.append(f"Party/Supplier '{value}' not found")
                            continue
                        
                        inventory_data[model_field] = value
                
                # Check required fields
                for req_field in required_fields:
                    if req_field not in inventory_data:
                        errors.append(f"Required field '{req_field}' is missing")
                
                if errors:
                    failed_imports.append({
                        'row': row_num,
                        'data': dict(row),
                        'errors': errors
                    })
                    continue
                
                # Validate and create inventory item
                serializer = InventorySerializer(data=inventory_data)
                if serializer.is_valid():
                    inventory = serializer.save()
                    successful_imports.append({
                        'row': row_num,
                        'id': inventory.id,
                        'item_name': inventory.item_name,
                        'part_number': inventory.part_number
                    })
                else:
                    failed_imports.append({
                        'row': row_num,
                        'data': dict(row),
                        'errors': serializer.errors
                    })
            
            except Exception as e:
                failed_imports.append({
                    'row': row_num,
                    'data': dict(row),
                    'errors': [f'Unexpected error: {str(e)}']
                })
        
        return {
            'total_rows': len(successful_imports) + len(failed_imports),
            'successful': len(successful_imports),
            'failed': len(failed_imports),
            'successful_imports': successful_imports,
            'failed_imports': failed_imports
        }
    
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
