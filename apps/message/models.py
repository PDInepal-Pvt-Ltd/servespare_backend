import re
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.base.models import BaseModel


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


class Message(BaseModel):
    """
    Model to store messages sent by unauthorized users (support inquiries).
    Only admin and support users can view these messages.
    """
    name = models.CharField(max_length=255, help_text="Name of the person sending the message")
    email = models.EmailField(help_text="Email address of the person")
    phone_number = models.CharField(max_length=20, help_text="Phone number of the person")
    company = models.CharField(max_length=255, help_text="Company name")
    message = models.TextField(help_text="The message content")
    is_read = models.BooleanField(default=False, help_text="Whether the message has been read by support")
    
    class Meta:
        ordering = ['-created']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_read']),
            models.Index(fields=['-created']),
        ]
    
    def __str__(self):
        return f"Message from {self.name} - {self.email}"

    def clean(self):
        errors = {}

        if not self.name or not self.name.strip():
            errors['name'] = 'Name is required.'
        elif len(self.name.strip()) > 255:
            errors['name'] = 'Name cannot exceed 255 characters.'

        if not self.email or not self.email.strip():
            errors['email'] = 'Email is required.'

        if not self.phone_number or not self.phone_number.strip():
            errors['phone_number'] = 'Phone number is required.'
        else:
            try:
                validate_phone_number(self.phone_number.strip())
            except ValidationError as exc:
                errors['phone_number'] = '; '.join(exc.messages)

        if not self.company or not self.company.strip():
            errors['company'] = 'Company is required.'
        elif len(self.company.strip()) > 255:
            errors['company'] = 'Company cannot exceed 255 characters.'

        if not self.message or not self.message.strip():
            errors['message'] = 'Message is required.'

        if errors:
            raise ValidationError(errors)
