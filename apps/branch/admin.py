from django import forms
from django.contrib import admin
from apps.base.admin import TenantAdminMixin

# Register your models here.
from .models import Branch, NEPAL_PROVINCE_DISTRICTS


class BranchAdminForm(forms.ModelForm):
    """Custom form for Branch admin with dropdown fields"""
    
    # Province dropdown
    province = forms.ChoiceField(
        choices=[('', '--- Select Province ---')] + [(p, p) for p in NEPAL_PROVINCE_DISTRICTS.keys()],
        widget=forms.Select(attrs={
            'class': 'django-admin-form-select',
            'onchange': 'updateDistrictDropdown(this.value);'
        }),
        required=True
    )
    
    # District dropdown
    district = forms.ChoiceField(
        choices=[('', '--- Select District ---')],
        widget=forms.Select(attrs={
            'id': 'id_district',
            'class': 'django-admin-form-select'
        }),
        required=True
    )
    
    class Meta:
        model = Branch
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If the instance has a province, populate district choices accordingly
        if self.instance.pk and self.instance.province:
            province = self.instance.province
            if province in NEPAL_PROVINCE_DISTRICTS:
                districts = NEPAL_PROVINCE_DISTRICTS[province]
                self.fields['district'].choices = [('', '--- Select District ---')] + [(d, d) for d in districts]
        
        # If form data is being submitted, use the province value to set district choices
        elif self.data and 'province' in self.data:
            province = self.data['province']
            if province and province in NEPAL_PROVINCE_DISTRICTS:
                districts = NEPAL_PROVINCE_DISTRICTS[province]
                self.fields['district'].choices = [('', '--- Select District ---')] + [(d, d) for d in districts]
        
        # Make tenant read-only for existing branches
        if self.instance.pk:
            self.fields['tenant'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        district = cleaned_data.get('district')
        
        # Validate that if province is selected, district must match
        if province and district:
            if province in NEPAL_PROVINCE_DISTRICTS:
                if district not in NEPAL_PROVINCE_DISTRICTS[province]:
                    raise forms.ValidationError(
                        f'District "{district}" does not belong to province "{province}".'
                    )
        
        return cleaned_data


@admin.register(Branch)
class BranchAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = BranchAdminForm
    list_display = ('branch_name', 'branch_code', 'tenant', 'city', 'province', 'district', 'phone', 'Email')
    search_fields = ('branch_name', 'branch_code', 'tenant__name', 'city', 'province', 'district', 'Email')
    list_filter = ('city', 'province', 'district', 'tenant')
    ordering = ('branch_name',)
    
    class Media:
        js = ('admin/js/branch_admin.js',)
    
    def save_model(self, request, obj, form, change):
        """Override save_model to check subscription limits before adding new branches."""
        from apps.users.utils import send_subscription_limit_exceeded_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        # Check subscription limit only when creating new branches
        if not change:  # change=False means we're adding a new branch
            tenant = obj.tenant
            if tenant:
                # Check if tenant has a subscription package
                if not tenant.package:
                    raise DjangoValidationError(
                        f'Cannot create branch. Tenant "{tenant.business_name}" does not have an active subscription plan. '
                        f'Please assign a subscription plan first.'
                    )
                
                # Check if tenant has reached their branch limit
                if not tenant.can_add_branch():
                    allowed = tenant.get_allowed_branches()
                    current = tenant.get_branch_count()
                    # Send limit exceeded email to tenant admin
                    send_subscription_limit_exceeded_email(
                        tenant,
                        'branches',
                        current,
                        allowed
                    )
                    raise DjangoValidationError(
                        f'Cannot create branch. Tenant "{tenant.business_name}" subscription plan (\'{tenant.package.plan_name}\') '
                        f'allows {allowed} branch(es), but already has {current} active branch(es). '
                        f'Please upgrade subscription or delete existing unused branches. '
                        f'Notification email sent to tenant admin.'
                    )
        
        super().save_model(request, obj, form, change) 



    
