"""Quick script to show account-ledger URLs"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.urls import get_resolver
from rest_framework.routers import DefaultRouter
from apps.cashandbank.views import AccountLedgerViewSet

# Show URLs from router
router = DefaultRouter()
router.register(r'account-ledger', AccountLedgerViewSet, basename='account-ledger')

print("\n" + "=" * 70)
print("🎯 CORRECT URLs FOR YOUR NEW STATISTICS ENDPOINTS")
print("=" * 70)
print("\n⚠️  NOTE: Base URL is /api/cash-and-bank/ (not /api/)")
print("\n✅ Purchase Statistics:")
print("   http://localhost:8000/api/cash-and-bank/account-ledger/purchase-statistics/")
print("\n✅ Sales Statistics:")
print("   http://localhost:8000/api/cash-and-bank/account-ledger/sales-statistics/")
print("\n" + "=" * 70)

print("\n📍 All Account Ledger URL Patterns:")
print("=" * 70)
for url in router.urls:
    pattern = str(url.pattern)
    if 'statistics' in pattern:
        full_url = f"account-ledger/{pattern.replace('^', '').replace('$', '')}"
        print(f"  ✅ {full_url}")

print("\n✅ Available Actions on AccountLedgerViewSet:")
print("=" * 70)
# Check the viewset for action methods
import inspect
for name, method in inspect.getmembers(AccountLedgerViewSet, predicate=inspect.isfunction):
    if hasattr(method, 'mapping'):  # This means it's an @action
        if 'statistics' in name:
            print(f"  ✅ {name}")
            if hasattr(method, 'url_path'):
                print(f"     → Full URL: /api/cash-and-bank/account-ledger/{method.url_path}/")

print("\n" + "=" * 70)
print("💡 TIP: Use these URLs in Postman or your frontend!")
print("=" * 70)
print("\n")
