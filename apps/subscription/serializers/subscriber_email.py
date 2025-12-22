from rest_framework import serializers

from apps.subscription.models import SubscriberEmail


class SubscriberEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberEmail
        fields = ['id', 'email', 'created']
        read_only_fields = ['id', 'created']
