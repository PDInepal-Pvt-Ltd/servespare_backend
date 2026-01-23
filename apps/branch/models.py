import re
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


def validate_phone_number(value):
    """
    Validate Nepali phone number format.
    Accepts:
    - Mobile: 10 digits starting with 97 or 98 (e.g., 9841234567)
    - Landline: 6-8 digits with area code (e.g., 01-4445678)
    - International format: +977 followed by mobile/landline
    - Formats accepted: with/without spaces, hyphens, parentheses
    """
    if not value:
        return

    cleaned = re.sub(r'[\s\-\(\)]', '', value)

    if cleaned.startswith('+977'):
        cleaned = cleaned[4:]
    elif cleaned.startswith('977'):
        cleaned = cleaned[3:]

    if not cleaned.isdigit():
        raise ValidationError(
            _('Phone number must contain only digits, spaces, hyphens, parentheses, or +977 for international format.'),
            code='invalid_phone_format'
        )

    if len(cleaned) == 10:
        if not (cleaned.startswith('97') or cleaned.startswith('98')):
            raise ValidationError(
                _('Nepali mobile number must start with 97 or 98.'),
                code='invalid_mobile_prefix'
            )
    elif 6 <= len(cleaned) <= 8:
        pass
    else:
        raise ValidationError(
            _('Phone number must be either 10 digits (mobile) or 6-8 digits (landline).'),
            code='invalid_phone_length'
        )


NEPAL_PROVINCE_DISTRICTS = {
    'Koshi': ['Bhojpur', 'Dhankuta', 'Ilam', 'Jhapa', 'Khotang', 'Morang', 'Okhaldhunga', 'Panchthar', 'Sankhuwasabha', 'Solukhumbu', 'Sunsari', 'Taplejung', 'Terhathum', 'Udayapur'],
    'Madhesh': ['Bara', 'Dhanusha', 'Mahottari', 'Parsa', 'Rautahat', 'Saptari', 'Sarlahi', 'Siraha'],
    'Bagmati': ['Bhaktapur', 'Chitwan', 'Dhading', 'Dolakha', 'Kathmandu', 'Kavrepalanchok', 'Lalitpur', 'Makwanpur', 'Nuwakot', 'Ramechhap', 'Rasuwa', 'Sindhuli', 'Sindhupalchok'],
    'Gandaki': ['Baglung', 'Gorkha', 'Kaski', 'Lamjung', 'Manang', 'Mustang', 'Myagdi', 'Nawalpur', 'Parbat', 'Syangja', 'Tanahun'],
    'Lumbini': ['Arghakhanchi', 'Banke', 'Bardiya', 'Dang', 'Gulmi', 'Kapilvastu', 'Palpa', 'Pyuthan', 'Rolpa', 'Rupandehi', 'Rukum East', 'Nawalparasi West'],
    'Karnali': ['Dailekh', 'Dolpa', 'Humla', 'Jajarkot', 'Jumla', 'Kalikot', 'Mugu', 'Rukum West', 'Salyan', 'Surkhet'],
    'Sudurpashchim': ['Achham', 'Baitadi', 'Bajhang', 'Bajura', 'Dadeldhura', 'Darchula', 'Doti', 'Kailali', 'Kanchanpur'],
}


def validate_province(value):
    """Validate that province is in NEPAL_PROVINCE_DISTRICTS"""
    if not value:
        raise ValidationError(
            _('Province is required.'),
            code='province_required'
        )
    if value not in NEPAL_PROVINCE_DISTRICTS:
        valid_provinces = ', '.join(NEPAL_PROVINCE_DISTRICTS.keys())
        raise ValidationError(
            _(f'Invalid province. Must be one of: {valid_provinces}'),
            code='invalid_province'
        )


def validate_district(value):
    """Validate that district is provided"""
    if not value:
        raise ValidationError(
            _('District is required.'),
            code='district_required'
        )


class Branch(BaseModel):
    """
    Model to store branch /business information
    """
    
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='branches'
    )
    branch_name = models.CharField(max_length=255 , unique=True)
    branch_code = models.CharField(max_length=50, unique=True)
    Address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        validators=[validate_province],
        help_text='Province/Region in Nepal'
    )
    district = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        validators=[validate_district],
        help_text='District in the selected province'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    Email = models.EmailField(unique=True)
    
    objects = TenantManager()
    
    class Meta:
        ordering = ["branch_name"]

    def __str__(self):
        return self.branch_name

    def clean(self):
        errors = {}

        if not self.tenant_id and not self.tenant:
            errors['tenant'] = 'Tenant is required.'

        if not self.branch_name or not self.branch_name.strip():
            errors['branch_name'] = 'Branch name is required.'
        elif len(self.branch_name.strip()) < 2:
            errors['branch_name'] = 'Branch name must be at least 2 characters.'
        elif len(self.branch_name.strip()) > 255:
            errors['branch_name'] = 'Branch name cannot exceed 255 characters.'

        if not self.branch_code or not self.branch_code.strip():
            errors['branch_code'] = 'Branch code is required.'
        elif len(self.branch_code.strip()) < 2:
            errors['branch_code'] = 'Branch code must be at least 2 characters.'
        elif len(self.branch_code.strip()) > 50:
            errors['branch_code'] = 'Branch code cannot exceed 50 characters.'

        if self.Address:
            addr = self.Address.strip()
            if len(addr) < 5:
                errors['Address'] = 'Address must be at least 5 characters when provided.'
            elif len(addr) > 1000:
                errors['Address'] = 'Address cannot exceed 1000 characters.'

        if self.city and len(self.city.strip()) > 100:
            errors['city'] = 'City cannot exceed 100 characters.'

        # Validate province
        if not self.province or not self.province.strip():
            errors['province'] = 'Province is required.'
        elif self.province not in NEPAL_PROVINCE_DISTRICTS:
            valid_provinces = ', '.join(NEPAL_PROVINCE_DISTRICTS.keys())
            errors['province'] = f'Invalid province. Must be one of: {valid_provinces}'

        # Validate district
        if not self.district or not self.district.strip():
            errors['district'] = 'District is required.'
        elif self.province in NEPAL_PROVINCE_DISTRICTS:
            if self.district not in NEPAL_PROVINCE_DISTRICTS[self.province]:
                valid_districts = ', '.join(NEPAL_PROVINCE_DISTRICTS[self.province])
                errors['district'] = f'Invalid district for {self.province}. Must be one of: {valid_districts}'

        if self.phone:
            try:
                validate_phone_number(self.phone.strip())
            except ValidationError as exc:
                errors['phone'] = '; '.join(exc.messages)

        if not self.Email or not self.Email.strip():
            errors['Email'] = 'Email is required.'

        # Check subscription limit for new branches only
        if not self.pk and self.tenant:  # not self.pk means this is a new instance
            if not self.tenant.package:
                errors['tenant'] = (
                    f'Cannot create branch. Tenant does not have an active subscription plan. '
                    f'Please assign a subscription plan first.'
                )
            elif not self.tenant.can_add_branch():
                allowed = self.tenant.get_allowed_branches()
                current = self.tenant.get_branch_count()
                errors['tenant'] = (
                    f'Cannot create branch. Tenant subscription plan allows {allowed} branch(es), '
                    f'but already has {current} active branch(es). '
                    f'Please upgrade subscription or delete existing unused branches.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)