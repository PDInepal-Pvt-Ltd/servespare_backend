from django.db import models
from apps.base.models import BaseModel


class SubscriberEmail(BaseModel):
    """Simple model to store subscriber emails (public signup).

    This is intentionally minimal: only an email address and timestamps.
    Non-authenticated users may POST to the API to create entries.
    """
    email = models.EmailField(max_length=254, unique=True)

    class Meta:
        db_table = 'subscription_subscriber_email'
        verbose_name = 'Subscriber Email'
        verbose_name_plural = 'Subscriber Emails'
        ordering = ['-created']

    def __str__(self) -> str:
        return self.email
