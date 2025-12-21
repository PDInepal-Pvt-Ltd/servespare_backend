from django.contrib import admin
from apps.carts.models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin interface for Cart model"""
    list_display = ['id', 'user', 'total_items', 'subtotal', 'created', 'is_active']
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


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin interface for CartItem model"""
    list_display = [
        'id',
        'cart',
        'inventory',
        'quantity',
        'price',
        'total_price',
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

