from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.cashandbank.views import BankAccountViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')

urlpatterns = [
    path('', include(router.urls)),
]

