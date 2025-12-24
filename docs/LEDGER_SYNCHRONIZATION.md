# Ledger Synchronization System Documentation

## Overview

The Ledger Synchronization System automatically syncs purchase and sales transactions to their respective ledgers. This ensures that every paid bill creates a Sales Ledger entry and every received/billed purchase order creates a Purchase Ledger entry.

## Architecture

### Components

1. **LedgerService** (`apps/cashandbank/ledger_service.py`)
   - Service layer handling all ledger creation and synchronization logic
   - Independent of models - can be used throughout the application
   - Provides both atomic creation and intelligent synchronization

2. **Signals**
   - **Sales Signals** (`apps/sales/signals.py`) - Handles Bill → Sales Ledger sync
   - **Stock Management Signals** (`apps/stock_management/signals.py`) - Handles PurchaseOrder → Purchase Ledger sync

3. **Management Command** (`sync_transactions_to_ledgers`)
   - Syncs existing bills and purchase orders to ledgers
   - Supports dry-run mode and filtering by tenant

## How It Works

### Sales Ledger Synchronization

When a Bill is created or updated:

1. **Signal Detection**: `@receiver(post_save, sender='sales.Bill')` catches the event
2. **Service Call**: Calls `LedgerService.sync_bill_to_sales_ledger(bill)`
3. **Status Check**: 
   - If status is `'paid'` or `'credit_sale'`:
     - Creates a new Sales Ledger entry with debit = bill total
     - Running balance is calculated from previous entries
   - If status is anything else:
     - Removes any existing ledger entry (if previously created)
4. **Result**: Bill total is recorded as income in the Sales Ledger

### Purchase Ledger Synchronization

When a PurchaseOrder is created or updated:

1. **Signal Detection**: `@receiver(post_save, sender='stock_management.PurchaseOrder')` catches the event
2. **Service Call**: Calls `LedgerService.sync_purchase_order_to_purchase_ledger(po)`
3. **Status Check**:
   - If status is `'received'` or `'billed'`:
     - Creates a new Purchase Ledger entry with credit = PO total
     - Running balance is calculated from previous entries
   - If status is anything else:
     - Removes any existing ledger entry (if previously created)
4. **Result**: Purchase amount is recorded as an expense in the Purchase Ledger

## Models

### AccountLedger Fields

```python
# For Sales Ledger entries from Bills
ledger_type = 'sales'  # Specific to sales transactions
transaction_type = 'sale'  # Transaction classification
debit = bill.total_after_discount  # Income recorded as debit
credit = Decimal('0.00')
reference_type = 'bill'
reference_id = str(bill.id)
description = f"Sales from Bill #{bill.id} - {customer_name}..."

# For Purchase Ledger entries from POs
ledger_type = 'purchase'  # Specific to purchase transactions
transaction_type = 'purchase'  # Transaction classification
debit = Decimal('0.00')
credit = po.total_amount  # Expense recorded as credit
reference_type = 'purchase_order'
reference_id = str(po.id)
description = f"Purchase Order #{po_number} from {supplier_name}..."
```

## Usage

### Automatic Synchronization (Default)

No action needed! Once bills are created with status `'paid'` or `'credit_sale'`, they are automatically added to the Sales Ledger.

Similarly, once purchase orders reach status `'received'` or `'billed'`, they are automatically added to the Purchase Ledger.

### Manual Synchronization

To manually sync existing data:

```bash
# Sync all existing bills and purchase orders
python manage.py sync_transactions_to_ledgers

# Sync only bills
python manage.py sync_transactions_to_ledgers --bills-only

# Sync only purchase orders
python manage.py sync_transactions_to_ledgers --pos-only

# Sync for a specific tenant
python manage.py sync_transactions_to_ledgers --tenant 5

# Preview what would be synced (dry run)
python manage.py sync_transactions_to_ledgers --dry-run
```

### Programmatic Usage

From any Django module, you can trigger synchronization:

```python
from apps.cashandbank.ledger_service import LedgerService
from apps.sales.models import Bill

# Get a bill
bill = Bill.objects.get(id=123)

# Sync to sales ledger
ledger_entry = LedgerService.sync_bill_to_sales_ledger(bill)

# Or create directly
ledger_entry = LedgerService.create_sales_ledger_entry(bill)
```

Similarly for purchase orders:

```python
from apps.cashandbank.ledger_service import LedgerService
from apps.stock_management.models import PurchaseOrder

# Get a purchase order
po = PurchaseOrder.objects.get(id=456)

# Sync to purchase ledger
ledger_entry = LedgerService.sync_purchase_order_to_purchase_ledger(po)

# Or create directly
ledger_entry = LedgerService.create_purchase_ledger_entry(po)
```

## Ledger Types & Transaction Types

### Transaction Type Choices (Updated)

The `AccountLedger` model now supports these transaction types:

- `'opening'` - Shift Opening
- `'cash_in'` - Cash In
- `'cash_out'` - Cash Out
- `'sale'` - Sale (used for bill-based sales)
- `'purchase'` - Purchase (used for PO-based purchases)
- `'closing'` - Shift Closing
- `'adjustment'` - Adjustment
- `'refund'` - Refund

### Ledger Type Mapping

| Source | Ledger Type | Transaction Type | Debit/Credit |
|--------|-------------|------------------|--------------|
| Bill (paid/credit_sale) | sales | sale | Debit = bill total |
| PurchaseOrder (received/billed) | purchase | purchase | Credit = PO total |

## Running Balance Calculation

Each ledger entry maintains a `balance` field that represents the cumulative balance up to that point:

```
Running Balance = Previous Balance + Debit - Credit

Example (Sales Ledger):
Entry 1: Debit 1000, Balance = 0 + 1000 - 0 = 1000
Entry 2: Debit 500,  Balance = 1000 + 500 - 0 = 1500
Entry 3: Credit 200, Balance = 1500 + 0 - 200 = 1300
```

## Idempotency

The synchronization system is idempotent:

- If a bill already has a corresponding ledger entry, it won't create a duplicate
- If a purchase order already has a corresponding ledger entry, it won't create a duplicate
- The `reference_type` + `reference_id` combination ensures uniqueness per ledger

## Error Handling

- All operations are wrapped in database transactions for atomicity
- Errors are logged but don't halt the process
- Invalid states (no tenant, no amount) are gracefully skipped
- Management command shows both successes and failures

## Database Performance

### Indexes Created

The system uses indexes on:
- `(shift, ledger_type)` - For shift-specific ledger queries
- `(tenant, branch)` - For multi-tenant ledger queries
- `transaction_date`, `ledger_type` - For date-range queries

### Query Optimization

When calculating running balances:
```python
AccountLedger.objects.filter(
    tenant=bill.tenant,
    branch=bill.branch,
    ledger_type='sales'
).order_by('-transaction_date', '-id').first()
```

## Testing

To test the synchronization:

```python
# Test creating a paid bill
bill = Bill.objects.create(
    tenant=tenant,
    customer_name="Test Customer",
    customer_type="retail",
    status="paid",
    payment_method="cash",
    total_after_discount=Decimal('1000.00')
)

# Check if ledger entry was created
from apps.cashandbank.models import AccountLedger
ledger = AccountLedger.objects.filter(
    reference_type='bill',
    reference_id=str(bill.id),
    ledger_type='sales'
).first()

assert ledger is not None
assert ledger.debit == Decimal('1000.00')
```

## Migration Information

A migration was created: `0015_add_purchase_transaction_type`

This migration:
- Adds `'purchase'` as a valid choice for `transaction_type`
- Creates proxy models for `SalesLedger` and `PurchaseLedger` for easier querying
- Updates database indexes for performance

## Troubleshooting

### Ledger entries not being created

1. Check if the bill status is `'paid'` or `'credit_sale'`
2. Check if the purchase order status is `'received'` or `'billed'`
3. Verify that the tenant is set on the transaction
4. Check the logs: `python manage.py ... 2>&1 | grep -i ledger`

### Duplicate ledger entries

This shouldn't happen due to the idempotency check, but if it does:

```python
from apps.cashandbank.models import AccountLedger

# Find duplicates
AccountLedger.objects.filter(
    reference_type='bill',
    reference_id='123'
).values('id', 'transaction_date').order_by('-transaction_date')

# Delete extras (keep the most recent)
AccountLedger.objects.filter(
    reference_type='bill',
    reference_id='123'
)[1:].delete()
```

### Ledger balance is incorrect

The running balance is calculated at creation time based on the previous entry's balance. If you manually modify ledger entries, the balance chain is broken. Run the management command to recalculate:

```bash
# First backup your data
python manage.py dumpdata cashandbank.AccountLedger > ledger_backup.json

# Then sync again (this will detect and skip duplicates)
python manage.py sync_transactions_to_ledgers
```

## Future Enhancements

Potential improvements:

1. **Batch Processing**: Handle large data sets more efficiently
2. **Ledger Reconciliation**: Periodic checks to ensure accuracy
3. **Audit Trail**: Track who synced what and when
4. **Bulk Status Updates**: When multiple bills change status, batch create ledger entries
5. **Accounting Integration**: Export ledgers to accounting software
6. **Multi-currency**: Support for multi-currency ledgers
7. **Approval Workflow**: Optional approval before ledger entries are finalized
