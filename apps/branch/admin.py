from django.contrib import admin

# Register your models here.
from .models import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_name', 'branch_code', 'tenant', 'city', 'state', 'phone', 'Email')
    search_fields = ('branch_name', 'branch_code', 'tenant__name', 'city', 'state', 'Email')
    list_filter = ('city', 'state', 'tenant')
    ordering = ('branch_name',)



    
