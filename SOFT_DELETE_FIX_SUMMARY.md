# Soft Delete Fix - Complete Summary

## Problem
After soft deletion of data, records were still appearing in API responses because querysets were using `.all()` which includes soft-deleted records.

## Solution
Updated all ViewSets and querysets to explicitly filter out soft-deleted records using `deleted_at__isnull=True`.

## Changes Made

### Core Manager (Most Important)
- **apps/base/managers.py** - Updated `TenantQuerySet._maybe_filter()` to always exclude soft-deleted records by filtering `deleted_at__isnull=True`

### Base Views
- **apps/base/views.py** - `AuditLogViewSet` - Added `.filter(deleted_at__isnull=True)` to queryset

### Branch Views
- **apps/branch/views.py** - `BranchViewSet` - Updated queryset and get_queryset() to filter deleted records

### Stock Management Views
- **apps/stock_management/views/inventory.py**
  - `InventoryViewSet` - Updated queryset and get_queryset()
  - `InventoryImageViewSet` - Updated queryset and get_queryset()
  
- **apps/stock_management/views/party.py** - `PartyViewSet` - Updated queryset and get_queryset()

- **apps/stock_management/views/purchase_order.py**
  - `PurchaseOrderViewSet` - Updated queryset, get_queryset(), by_status(), and statistics() actions
  - `PurchaseOrderItemViewSet` - Updated queryset, get_queryset(), and returned() action

### Sales Views
- **apps/sales/views/bill.py** - `BillViewSet` - Updated queryset and get_queryset()

### Cash & Bank Views
- **apps/cashandbank/views/account_ledger.py** - `AccountLedgerViewSet` - Updated queryset
- **apps/cashandbank/views/bank_transfer.py** - `BankTransferViewSet` - Updated queryset and get_queryset()
- **apps/cashandbank/views/bank_account.py** - `BankAccountViewSet` - Updated queryset and get_queryset()
- **apps/cashandbank/views/cashier_shift.py** - `CashierShiftViewSet` - Updated queryset and get_queryset()
- **apps/cashandbank/views/cheque.py** - `ChequeViewSet` - Updated queryset and get_queryset()
- **apps/cashandbank/views/cash_transaction.py** - `CashTransactionViewSet` - Updated queryset and get_queryset()
- **apps/cashandbank/views/cash_balance.py** - `CashBalanceViewSet` - Updated queryset and get_queryset()
- **apps/cashandbank/views/manual_entry.py** - `ManualEntryViewSet` - Updated queryset and get_queryset()

### Tenant Views
- **apps/tenant/views/tenant.py** - `TenantViewSet` - Updated queryset, get_queryset(), and counts() action

### Subscription Views
- **apps/subscription/views/subscription_plan.py** - `SubscriptionPlanViewSet` - Updated queryset and get_queryset()
- **apps/subscription/views/subscriber_email.py** - `SubscriberEmailCreateView` - Updated queryset
- **apps/subscription/views/subscription.py** - `SubscriptionViewSet` - Updated queryset and get_queryset()

### Message Views
- **apps/message/views.py** - `MessageViewSet` - Updated queryset

### OTP Views
- **apps/otp/views/otp_views.py** - `OTPViewSet.list()` - Updated to filter deleted records

## Implementation Pattern

All changes follow this pattern:
```python
# Before (includes soft-deleted)
queryset = Model.objects.all()
# or
queryset = Model.objects.select_related(...).all()

# After (excludes soft-deleted)
queryset = Model.objects.filter(deleted_at__isnull=True)
# or
queryset = Model.objects.filter(deleted_at__isnull=True).select_related(...)
```

## How It Works

The `SoftDeletableModel` from `django-model-utils` automatically adds:
- A `deleted_at` field (initially NULL)
- When soft-deleted, `deleted_at` is set to the current timestamp

By filtering `deleted_at__isnull=True`, we only return records that haven't been soft-deleted.

## Testing
All modified files have been validated for syntax errors - no errors found.

## Impact
- Soft-deleted records will no longer appear in any API GET requests
- Soft-deleted records are properly hidden from users
- The fix is applied at the queryset level, ensuring consistency across all endpoints
