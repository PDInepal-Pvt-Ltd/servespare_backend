from django.contrib import admin
from apps.carts.models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin interface for Cart model"""
    list_display = ['id', 'user', 'items_count', 'subtotal_display', 'created', 'is_active']
    list_filter = ['is_active', 'created', 'modified']
    search_fields = ['user__username', 'user__email', 'user__full_name']
    readonly_fields = ['created', 'modified', 'total_items', 'subtotal']
    date_hierarchy = 'created'
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('user', 'total_items', 'subtotal')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'

    def subtotal_display(self, obj):
        from decimal import Decimal, ROUND_HALF_UP
        total = (obj.subtotal or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{total:.2f}"
    subtotal_display.short_description = 'Subtotal'
    
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


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin interface for CartItem model"""
    list_display = [
        'id',
        'cart',
        'inventory',
        'quantity',
        'price_display',
        'total_price_display',
        'created',
        'is_active'
    ]
    list_filter = ['is_active', 'created', 'modified']
    search_fields = [
        'cart__user__username',
        'inventory__item_name',
        'inventory__part_number'
    ]
    readonly_fields = ['created', 'modified', 'price', 'total_price']
    date_hierarchy = 'created'
    
    fieldsets = (
        ('Cart Item Information', {
            'fields': ('cart', 'inventory', 'quantity', 'price', 'total_price')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        from decimal import Decimal, ROUND_HALF_UP
        value = (obj.price or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"
    price_display.short_description = 'Unit Price'

    def total_price_display(self, obj):
        from decimal import Decimal, ROUND_HALF_UP
        value = (obj.total_price or Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{value:.2f}"
    total_price_display.short_description = 'Total'
    
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

