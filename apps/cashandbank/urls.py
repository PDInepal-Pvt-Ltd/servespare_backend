from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.cashandbank.views import BankAccountViewSet, CashTransactionViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'cash-transactions', CashTransactionViewSet, basename='cash-transaction')

urlpatterns = [
    path('', include(router.urls)),
]

