from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel, SoftDeletableModel

class BaseModel(TimeStampedModel, SoftDeletableModel):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AuditLog(BaseModel):
    """
    Minimal audit log for tracking who did what, where, and when.

    Captures write operations and authentication-related requests via middleware.
    """

    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        AUTH = 'auth', 'Auth'
        OTHER = 'other', 'Other'

    # Actor and tenant context
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    # Request metadata
    method = models.CharField(max_length=10, db_index=True)
    path = models.CharField(max_length=512, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)

    # Domain info
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.OTHER, db_index=True)
    entity = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    object_id = models.CharField(max_length=100, null=True, blank=True)

    # Request/response payload snapshot (truncated in middleware)
    payload = models.JSONField(null=True, blank=True)
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'audit_log'
        indexes = [
            models.Index(fields=['created'], name='audit_created_idx'),
            models.Index(fields=['action', 'entity'], name='audit_action_entity_idx'),
            models.Index(fields=['method', 'status_code'], name='audit_method_status_idx'),
        ]
        ordering = ['-created']

    def __str__(self) -> str:
        user = getattr(self.user, 'username', 'anonymous')
        return f"[{self.created:%Y-%m-%d %H:%M:%S}] {user} {self.method} {self.path} ({self.status_code})"