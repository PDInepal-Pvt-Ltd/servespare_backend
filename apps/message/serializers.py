from rest_framework import serializers
from .models import Message


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating messages (public endpoint - no authentication required).
    """
    class Meta:
        model = Message
        fields = ['name', 'email', 'phone_number', 'company', 'message']
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
            'company': {'required': True},
            'message': {'required': True},
        }


class MessageListSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving messages (admin/support only).
    """
    created = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    modified = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'name', 'email', 'phone_number', 'company', 'message', 'is_read', 'created', 'modified']
        read_only_fields = ['id', 'created', 'modified']
