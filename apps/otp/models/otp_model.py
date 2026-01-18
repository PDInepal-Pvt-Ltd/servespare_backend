import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _


# Get the custom User model defined in settings
User = settings.AUTH_USER_MODEL

class OTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ForeignKey allows multiple OTPs per user (for resend scenarios)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='otp_records'
    )
    code = models.CharField(max_length=6, verbose_name=_("OTP Code"))
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        """Check if OTP is still valid (not expired)"""
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.user}: {self.code}"
    
    class Meta:
        verbose_name = "One-Time Password"
        verbose_name_plural = "One-Time Passwords"
        ordering = ["-created_at"]
