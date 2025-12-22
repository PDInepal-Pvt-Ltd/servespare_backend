from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.subscription.views import SubscriptionPlanViewSet, SubscriptionViewSet, SubscriberEmailCreateView

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('subscribe-email/', SubscriberEmailCreateView.as_view(), name='subscribe-email'),
]

