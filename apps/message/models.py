from django.db import models
from apps.base.models import BaseModel


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
