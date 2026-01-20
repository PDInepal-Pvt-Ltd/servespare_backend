from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin

from apps.subscription.models import SubscriberEmail


class SubscriberEmailSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = SubscriberEmail
        fields = ['id', 'email', 'created']
        read_only_fields = ['id', 'created']
