# Cashier Shift Management - Quick Reference

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Shift** | A time period during which a cashier handles cash transactions |
| **Opening Float** | Cash amount given to cashier at start of shift |
| **Expected Amount** | opening_float + sales - cash_out + cash_in |
| **Variance** | Difference between expected and actual closing amounts |
| **Signed Amount** | Amount with appropriate sign based on transaction type |

## Transaction Types

| Type | Effect | Example |
|------|--------|---------|
| **opening** | +Amount | Cashier receives opening float |
| **cash_in** | +Amount | Customer refund, cash received |
| **sale** | +Amount | Auto-posted from bill creation |
| **cash_out** | -Amount | Reimbursement to manager |
| **closing** | -Amount | Final count when shift ends |

## Shift Statuses

| Status | Meaning | Can Adjust? |
|--------|---------|------------|
| **open** | Shift is active | Yes (cash_in/out) |
| **closed** | Shift ended | No |
| **flagged** | Variance > 100 | No |

## API Quick Commands

### Open Shift
```bash
POST /api/cashandbank/shifts/open/
{
  "opening_float": 1000.00,
  "branch_id": 1,
  "notes": "Optional notes"
}
```

### Get Active Shift
```bash
GET /api/cashandbank/shifts/active/
```

### Add Cash
```bash
POST /api/cashandbank/shifts/{id}/cash_in/
{ "amount": 500.00, "description": "Refund" }

POST /api/cashandbank/shifts/{id}/cash_out/
{ "amount": 250.00, "description": "Reimbursement" }
```

### Close Shift
```bash
# Balanced (actual = expected ±0.01)
POST /api/cashandbank/shifts/{id}/close_balanced/
{ "actual_amount": 2000.00, "notes": "Optional" }

# With Variance (actual ≠ expected)
POST /api/cashandbank/shifts/{id}/close_variance/
{
  "actual_amount": 1950.00,
  "variance_reason": "Miscounted",
  "notes": "Optional"
}
```

### View Shift Details
```bash
GET /api/cashandbank/shifts/{id}/
GET /api/cashandbank/shifts/{id}/transactions/
```

## Key Rules

1. **Opening Float** must be > 0
2. **One Open Shift** per cashier at a time
3. **Cash Adjustments** only on open shifts
4. **Balanced Close** requires actual ≈ expected (±0.01)
5. **Variance Close** requires variance_reason
6. **Auto-Flag** when |variance| > 100
7. **Auto Sales** only when bill payment='cash' AND status='paid'

## Common Workflows

### Perfect Day (Balanced)
```
1. open_shift(1000) → expected: 1000
2. auto post sales: +500 → expected: 1500
3. cash_in(100) → expected: 1600
4. cash_out(50) → expected: 1550
5. auto post more sales: +450 → expected: 2000
6. close_balanced(2000) → variance: 0 ✓
```

### Variance Day (Over)
```
1. open_shift(1000) → expected: 1000
2. auto post sales: +500 → expected: 1500
3. close_variance(1510) 
   → variance: +10 (over by 10)
   → reason: "Extra tip"
   → status: closed
```

### Variance Day (Under)
```
1. open_shift(1000) → expected: 1000
2. auto post sales: +500 → expected: 1500
3. close_variance(1480)
   → variance: -20 (under by 20)
   → reason: "Broke a coin"
   → status: closed
```

### Large Variance (Flagged)
```
1. open_shift(1000) → expected: 1000
2. auto post sales: +500 → expected: 1500
3. close_variance(1650)
   → variance: +150 (over by 150)
   → reason: "Counted wrong initially"
   → status: closed
   → is_flagged: true ⚠️
```

## Database Queries

### Get Open Shifts
```python
from apps.cashandbank.models import CashierShift
CashierShift.objects.filter(status='open', tenant=tenant)
```

### Get Flagged Shifts
```python
CashierShift.objects.filter(is_flagged=True, tenant=tenant)
```

### Get Today's Shifts
```python
from django.utils import timezone
from datetime import timedelta

today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
CashierShift.objects.filter(
    opened_at__gte=today,
    tenant=tenant
)
```

### Get Shift Transactions
```python
shift = CashierShift.objects.get(id=1)
transactions = shift.shift_transactions.all()
for txn in transactions:
    print(f"{txn.transaction_type}: {txn.signed_amount}")
```

### Get Shift Summary
```python
shift = CashierShift.objects.get(id=1)
summary = shift.get_transaction_summary()
# {
#   'total_cash_in': Decimal('100.00'),
#   'total_cash_out': Decimal('50.00'),
#   'total_sales': Decimal('1200.00'),
#   'total_adjustments': Decimal('50.00'),
#   'transaction_count': 5
# }
```

## Field Reference

### CashierShift
- `opening_float` - Starting amount
- `expected_amount` - Calculated expected total
- `actual_amount` - Counted at close
- `variance_amount` - actual - expected
- `is_balanced` - Property: |variance| ≤ 0.01
- `duration` - Property: minutes since open
- `is_flagged` - Auto-flagged if |variance| > 100

### ShiftTransaction
- `amount` - Always positive value
- `signed_amount` - Property: with sign based on type
- `reference_type` - 'bill', 'invoice', etc.
- `reference_id` - ID of referenced object

## Permissions

All endpoints require:
- **Authentication** - User must be logged in
- **Branch Permission** - CanManageBranchResources
- **Tenant Scoping** - Auto-filtered by user's tenant

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400: No active shift | User has no open shift | Open a shift first |
| 400: Already has open shift | User has multiple open shifts | Close the other shift |
| 400: Invalid opening_float | negative or non-numeric | Use positive decimal |
| 400: Shift not open | Trying to adjust closed shift | Can't adjust closed shifts |
| 400: Not balanced | Close requires exact match ±0.01 | Use close_variance instead |
| 400: Missing variance_reason | close_variance requires reason | Provide variance_reason |
| 404: No active shift | No open shift found | Open a shift first |

## Performance Tips

1. **Use select_for_update()** when modifying shift/transactions to avoid races
2. **Index frequently queried fields** - already indexed: tenant, branch, cashier, status
3. **Paginate shift lists** - use offset/limit for large datasets
4. **Cache active shifts** - GET /active/ checks once per request
5. **Batch transaction retrieval** - get all with /transactions/ endpoint

## Testing Checklist

- [ ] Open shift with valid amount
- [ ] Prevent opening shift with negative amount
- [ ] Prevent multiple open shifts per user
- [ ] Add cash_in increments expected
- [ ] Add cash_out decrements expected
- [ ] Auto-post sales to active shift
- [ ] Close balanced only if actual ≈ expected
- [ ] Close variance with variance_reason
- [ ] Auto-flag when |variance| > 100
- [ ] Prevent adjustments on closed shift
- [ ] Prevent adjustments on flagged shift
- [ ] Verify tenant scoping
- [ ] Verify permission checks
- [ ] Verify concurrent access with locks
