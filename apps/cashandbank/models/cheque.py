from django.db import models


class Cheque(models.Model):
    CHEQUE_TYPE_ISSUED = 'issued'
    CHEQUE_TYPE_GIVEN = 'given'
    CHEQUE_TYPE_CHOICES = [
        (CHEQUE_TYPE_ISSUED, 'Issued'),
        (CHEQUE_TYPE_GIVEN, 'Given'),
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

    # Optional bookkeeping fields
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created']
        verbose_name = 'Cheque'
        verbose_name_plural = 'Cheques'

    def __str__(self):
        label = self.cheque_number or "(no number)"
        return f"{self.get_cheque_type_display()} - {label} - {self.amount}"
