from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.subscription.models import SubscriberEmail
from apps.subscription.serializers.subscriber_email import SubscriberEmailSerializer


class SubscriberEmailCreateView(generics.CreateAPIView):
    """Public endpoint to allow anyone (including anonymous users) to submit an email.

    No authentication is required; `AllowAny` is used. Duplicate emails are rejected
    by the model's unique constraint.
    """
    queryset = SubscriberEmail.objects.all()
    serializer_class = SubscriberEmailSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
