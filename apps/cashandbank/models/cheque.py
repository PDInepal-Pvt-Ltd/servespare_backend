from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class Cheque(BaseModel):
    CHEQUE_TYPE_ISSUED = 'issued'
    CHEQUE_TYPE_RECEIVED = 'received'
    CHEQUE_TYPE_CHOICES = [
        (CHEQUE_TYPE_ISSUED, 'Issued'),
        (CHEQUE_TYPE_RECEIVED, 'Received'),
    ]

    REMINDER_SAME_DAY = '0'
    REMINDER_1_DAY = '1'
    REMINDER_3_DAY = '3'
    REMINDER_7_DAY = '7'
    REMINDER_CHOICES = [
        (REMINDER_7_DAY, '7 days before'),
        (REMINDER_3_DAY, '3 days before'),
        (REMINDER_1_DAY, '1 day before'),
        (REMINDER_SAME_DAY, 'Same day'),
    ]

    cheque_type = models.CharField(max_length=10, choices=CHEQUE_TYPE_CHOICES)
    cheque_number = models.CharField(max_length=128, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    issue_date = models.DateField(blank=True, null=True)
    due_date = models.DateField()
    party_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=64, blank=True, null=True)
    ifsc_code = models.CharField(max_length=32, blank=True, null=True)
    purpose = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    reminder_setting = models.CharField(max_length=2, choices=REMINDER_CHOICES, default=REMINDER_7_DAY)

    # Tenant and Branch context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cheques',
        help_text='Tenant that owns this cheque'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cheques',
        help_text='Branch associated with this cheque'
    )

    objects = TenantManager()

    class Meta:
        db_table = 'cheque'
        ordering = ['-due_date', '-created']
        verbose_name = 'Cheque'
        verbose_name_plural = 'Cheques'
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
            models.Index(fields=['due_date']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        label = self.cheque_number or "(no number)"
        return f"{self.get_cheque_type_display()} - {label} - {self.amount}"

    def clean(self):
        errors = {}

        if not self.cheque_type:
            errors['cheque_type'] = 'Cheque type is required.'
        elif self.cheque_type not in dict(self.CHEQUE_TYPE_CHOICES):
            errors['cheque_type'] = 'Invalid cheque type.'

        if not self.reminder_setting:
            errors['reminder_setting'] = 'Reminder setting is required.'
        elif self.reminder_setting not in dict(self.REMINDER_CHOICES):
            errors['reminder_setting'] = 'Invalid reminder setting.'

        if self.amount is None:
            errors['amount'] = 'Amount is required.'
        elif self.amount < Decimal('0.00'):
            errors['amount'] = 'Amount cannot be negative.'

        if not self.due_date:
            errors['due_date'] = 'Due date is required.'

        if self.issue_date and self.due_date and self.due_date < self.issue_date:
            errors['due_date'] = 'Due date cannot be earlier than issue date.'

        if self.cheque_number and len(self.cheque_number.strip()) > 128:
            errors['cheque_number'] = 'Cheque number cannot exceed 128 characters.'

        if self.bank_name and len(self.bank_name.strip()) > 255:
            errors['bank_name'] = 'Bank name cannot exceed 255 characters.'

        if self.party_name and len(self.party_name.strip()) > 255:
            errors['party_name'] = 'Party name cannot exceed 255 characters.'

        if self.account_number and len(self.account_number.strip()) > 64:
            errors['account_number'] = 'Account number cannot exceed 64 characters.'

        if self.ifsc_code and len(self.ifsc_code.strip()) > 32:
            errors['ifsc_code'] = 'IFSC code cannot exceed 32 characters.'

        if self.purpose and len(self.purpose.strip()) > 255:
            errors['purpose'] = 'Purpose cannot exceed 255 characters.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
