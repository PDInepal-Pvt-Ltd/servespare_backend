from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.cashandbank.views import BankAccountViewSet, CashTransactionViewSet
from apps.cashandbank.views import CashBalanceViewSet, ManualEntryViewSet
from apps.cashandbank.views import BankTransferViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'cash-transactions', CashTransactionViewSet, basename='cash-transaction')
router.register(r'cash-balances', CashBalanceViewSet, basename='cash-balance')
router.register(r'manual-entries', ManualEntryViewSet, basename='manual-entry')
router.register(r'bank-transfers', BankTransferViewSet, basename='bank-transfer')

urlpatterns = [
    path('', include(router.urls)),
]

