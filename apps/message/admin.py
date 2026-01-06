from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone_number', 'company', 'is_read', 'created']
    list_filter = ['is_read', 'created', 'modified']
    search_fields = ['name', 'email', 'phone_number', 'company', 'message']
    readonly_fields = ['id', 'created', 'modified']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone_number', 'company')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent direct creation from admin panel"""
        return False

