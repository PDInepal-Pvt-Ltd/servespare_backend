from django.contrib import admin
from apps.base.admin import TenantAdminMixin

# Register your models here.
from .models import Branch


@admin.register(Branch)
class BranchAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('branch_name', 'branch_code', 'tenant', 'city', 'state', 'phone', 'Email')
    search_fields = ('branch_name', 'branch_code', 'tenant__name', 'city', 'state', 'Email')
    list_filter = ('city', 'state', 'tenant')
    ordering = ('branch_name',) 



    
