from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    tenant_name = serializers.CharField(source='tenant.business_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'created', 'modified',
            'user', 'user_username', 'tenant', 'tenant_name',
            'action', 'entity', 'object_id',
            'method', 'path', 'status_code', 'ip_address', 'user_agent',
            'payload', 'extra',
        ]
        read_only_fields = fields
