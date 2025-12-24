from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.cashandbank.views import (
    BankAccountViewSet,
    CashTransactionViewSet,
    CashBalanceViewSet,
    ManualEntryViewSet,
    BankTransferViewSet,
    CashierShiftViewSet,
    AccountLedgerViewSet,
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'cash-transactions', CashTransactionViewSet, basename='cash-transaction')
router.register(r'cash-balances', CashBalanceViewSet, basename='cash-balance')
router.register(r'manual-entries', ManualEntryViewSet, basename='manual-entry')
router.register(r'bank-transfers', BankTransferViewSet, basename='bank-transfer')
router.register(r'shifts', CashierShiftViewSet, basename='cashier-shift')
router.register(r'account-ledger', AccountLedgerViewSet, basename='account-ledger')

urlpatterns = [
    path('', include(router.urls)),
]

