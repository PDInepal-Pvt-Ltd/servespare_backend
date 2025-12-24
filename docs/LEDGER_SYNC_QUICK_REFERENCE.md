# Ledger Synchronization - Quick Reference

## What Was Implemented

A complete ledger synchronization system that automatically syncs:

1. **Sales Bills** → **Sales Ledger** (when status = 'paid' or 'credit_sale')
2. **Purchase Orders** → **Purchase Ledger** (when status = 'received' or 'billed')

## Key Features

✅ **Automatic Synchronization** - Signals automatically create ledger entries when transactions change  
✅ **Idempotent** - No duplicates; existing entries are never recreated  
✅ **Running Balance** - Each entry maintains cumulative balance  
✅ **Multi-tenant** - Supports multiple tenants with proper isolation  
✅ **Reversible** - Removes entries if transaction status changes  
✅ **Bulk Sync** - Management command to sync existing data  
✅ **Dry Run** - Preview changes before applying  

## Files Created/Modified

### New Files
- `apps/cashandbank/ledger_service.py` - Service layer for ledger operations
- `apps/stock_management/signals.py` - PurchaseOrder synchronization signals
- `apps/cashandbank/management/commands/sync_transactions_to_ledgers.py` - Bulk sync command
- `docs/LEDGER_SYNCHRONIZATION.md` - Complete documentation

### Modified Files
- `apps/sales/signals.py` - Added Bill → Sales Ledger sync
- `apps/cashandbank/models/account_ledger.py` - Added 'purchase' transaction type
- `apps/stock_management/apps.py` - Registered signal handlers

### Database
- Migration: `0015_add_purchase_transaction_type` - Adds 'purchase' transaction type

## Quick Commands

```bash
# Sync all existing data
python manage.py sync_transactions_to_ledgers

# Sync with preview (no changes)
python manage.py sync_transactions_to_ledgers --dry-run

# Sync only bills
python manage.py sync_transactions_to_ledgers --bills-only

# Sync only purchase orders
python manage.py sync_transactions_to_ledgers --pos-only

# Sync for specific tenant
python manage.py sync_transactions_to_ledgers --tenant 5

# View help
python manage.py help sync_transactions_to_ledgers
```

## Data Flow

### Sales Bill Flow
```
Bill Created/Updated
    ↓
Signal Triggered: post_save
    ↓
LedgerService.sync_bill_to_sales_ledger()
    ↓
Status Check
├─ paid/credit_sale → Create SalesLedger entry (debit)
└─ other → Remove entry if exists
    ↓
AccountLedger Entry Created (ledger_type='sales')
```

### Purchase Order Flow
```
PurchaseOrder Created/Updated
    ↓
Signal Triggered: post_save
    ↓
LedgerService.sync_purchase_order_to_purchase_ledger()
    ↓
Status Check
├─ received/billed → Create PurchaseLedger entry (credit)
└─ other → Remove entry if exists
    ↓
AccountLedger Entry Created (ledger_type='purchase')
```

## Example Usage in Code

```python
from apps.cashandbank.ledger_service import LedgerService
from apps.sales.models import Bill

# Create a bill
bill = Bill.objects.create(
    tenant=tenant,
    customer_name="John Doe",
    status="paid",
    total_after_discount=1000.00
)

# Ledger entry is automatically created via signal
# But you can also manually sync anytime
ledger = LedgerService.sync_bill_to_sales_ledger(bill)
```

## Ledger Entry Structure

### Sales Ledger Entry
```
{
    'ledger_type': 'sales',
    'transaction_type': 'sale',
    'debit': bill.total_after_discount,  # Income as debit
    'credit': 0,
    'balance': running_balance,
    'description': 'Sales from Bill #123 - John Doe (Retail)',
    'reference_type': 'bill',
    'reference_id': '123',
    'reference': 'Bill #123'
}
```

### Purchase Ledger Entry
```
{
    'ledger_type': 'purchase',
    'transaction_type': 'purchase',
    'debit': 0,
    'credit': po.total_amount,  # Expense as credit
    'balance': running_balance,
    'description': 'Purchase Order #PO-001 from Supplier Name',
    'reference_type': 'purchase_order',
    'reference_id': '456',
    'reference': 'PO #PO-001'
}
```

## Querying Ledgers

```python
from apps.cashandbank.models import AccountLedger

# Get all sales ledger entries for a tenant
sales = AccountLedger.objects.filter(
    ledger_type='sales',
    tenant=tenant
).order_by('transaction_date')

# Get all purchase ledger entries
purchases = AccountLedger.objects.filter(
    ledger_type='purchase',
    tenant=tenant
).order_by('transaction_date')

# Get entries related to a specific bill
bill_entries = AccountLedger.objects.filter(
    reference_type='bill',
    reference_id='123'
)

# Get entries related to a specific PO
po_entries = AccountLedger.objects.filter(
    reference_type='purchase_order',
    reference_id='456'
)

# Get recent ledger entries with balance
recent = AccountLedger.objects.filter(
    tenant=tenant,
    ledger_type='sales'
).order_by('-transaction_date')[:10]

for entry in recent:
    print(f"{entry.transaction_date}: {entry.description} → Balance: {entry.balance}")
```

## Testing

To verify it's working:

```python
from django.test import TestCase
from apps.sales.models import Bill
from apps.cashandbank.models import AccountLedger
from apps.tenant.models import Tenant
from decimal import Decimal

class LedgerSyncTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
    
    def test_bill_sync_to_sales_ledger(self):
        # Create a paid bill
        bill = Bill.objects.create(
            tenant=self.tenant,
            customer_name="Test Customer",
            customer_type="retail",
            status="paid",
            total_after_discount=Decimal('1000.00')
        )
        
        # Verify ledger entry was created
        ledger = AccountLedger.objects.filter(
            reference_type='bill',
            reference_id=str(bill.id),
            ledger_type='sales'
        ).first()
        
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger.debit, Decimal('1000.00'))
        self.assertEqual(ledger.transaction_type, 'sale')
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ledger entries not created | Check bill/PO status is 'paid'/'credit_sale' (bills) or 'received'/'billed' (POs) |
| Duplicate entries | Run `sync_transactions_to_ledgers` with `--dry-run` first |
| Wrong balance | Balance is calculated from previous entries in order |
| Missing historical data | Run `python manage.py sync_transactions_to_ledgers` |

## Performance Notes

- Ledger creation happens asynchronously via signals
- Indexes optimize queries on (shift, ledger_type) and (tenant, branch)
- Running balance calculation queries only the most recent entry per ledger
- Management command batches processing for large datasets

## Next Steps

Consider implementing:
- REST API endpoints to query ledgers
- Ledger reconciliation reports
- Export to PDF/Excel
- Integration with accounting systems
- Automated reversal of entries
- Approval workflow for ledger entries
