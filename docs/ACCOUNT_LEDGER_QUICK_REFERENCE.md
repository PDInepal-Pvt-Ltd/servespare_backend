# Account Ledger Quick Reference

## Quick Links

- **Full Documentation**: [ACCOUNT_LEDGER_API.md](ACCOUNT_LEDGER_API.md)
- **Models**: `apps/cashandbank/models/account_ledger.py`
- **Serializers**: `apps/cashandbank/serializers/account_ledger.py`
- **Views**: `apps/cashandbank/views/account_ledger.py`
- **Signals**: `apps/cashandbank/signals.py`

---

## API Endpoints Cheat Sheet

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/cashandbank/account-ledger/` | GET | List with filters + summary |
| `/api/cashandbank/account-ledger/{id}/` | GET | Get entry details |
| `/api/cashandbank/account-ledger/summary/` | GET | Get summary only |
| `/api/cashandbank/account-ledger/general/` | GET | General Ledger |
| `/api/cashandbank/account-ledger/sales/` | GET | Sales Ledger |
| `/api/cashandbank/account-ledger/purchase/` | GET | Purchase Ledger |
| `/api/cashandbank/account-ledger/by_shift/` | GET | Get by shift (requires shift_id) |
| `/api/cashandbank/account-ledger/create_entry/` | POST | Create manual entry |
| `/api/cashandbank/account-ledger/print_ledger/` | GET | Get unparated data for printing |

---

## Filter Parameters

```
?ledger_type=general           # Filter by ledger type
?transaction_type=opening      # Filter by transaction type
?shift_id=17                   # Filter by shift
?from_date=2025-12-24         # Start date
?to_date=2025-12-24           # End date
?branch_id=1                  # Filter by branch
?performed_by_id=5            # Filter by user
?reference_type=shift         # Filter by reference
?search=opening               # Search description/reference
?page=1&page_size=50         # Pagination
```

---

## Quick Examples

### Get Today's General Ledger
```bash
curl "http://localhost:8000/api/cashandbank/account-ledger/general/?from_date=2025-12-24&to_date=2025-12-24" \
  -H "Authorization: Bearer TOKEN"
```

### Get Shift Ledger
```bash
curl "http://localhost:8000/api/cashandbank/account-ledger/by_shift/?shift_id=17" \
  -H "Authorization: Bearer TOKEN"
```

### Get Summary Stats
```bash
curl "http://localhost:8000/api/cashandbank/account-ledger/summary/?shift_id=17" \
  -H "Authorization: Bearer TOKEN"
```

### Export for Printing
```bash
curl "http://localhost:8000/api/cashandbank/account-ledger/print_ledger/?shift_id=17" \
  -H "Authorization: Bearer TOKEN"
```

### Create Manual Entry
```bash
curl -X POST "http://localhost:8000/api/cashandbank/account-ledger/create_entry/" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ledger_type": "general",
    "transaction_type": "adjustment",
    "debit": 50.00,
    "credit": 0.00,
    "description": "Adjustment note",
    "shift_id": 17
  }'
```

---

## Ledger Types

| Type | Purpose | Includes |
|------|---------|----------|
| `general` | All transactions | Everything |
| `sales` | Sales only | Sale transactions |
| `purchase` | Purchases/Expenses | Cash out transactions |
| `account` | Account history | All transactions |

---

## Transaction Types

| Type | Debit | Credit | Effect |
|------|-------|--------|--------|
| `opening` | ✓ | | Initializes balance |
| `cash_in` | ✓ | | Adds cash |
| `sale` | ✓ | | Adds cash from sales |
| `cash_out` | | ✓ | Removes cash |
| `closing` | | ✓ | Settles balance |
| `adjustment` | ✓/✓ | | Manual correction |
| `refund` | | ✓ | Refund amount |

---

## Response Structure

### List Response
```json
{
  "summary": { ... },
  "count": 10,
  "next": "...",
  "previous": "...",
  "results": [ ... ]
}
```

### Summary Response
```json
{
  "total_debit": "1100.00",
  "total_credit": "1000.00",
  "net_balance": "100.00",
  "transaction_count": 3,
  "from_date": "12/24/2025",
  "to_date": "12/24/2025",
  "ledger_type": "general",
  "filtered_by_shift": false,
  "currency": "Rs"
}
```

### Entry Fields
- `id` - Entry ID
- `ledger_type` - Type of ledger
- `transaction_type` - Type of transaction
- `debit` - Inflow amount
- `credit` - Outflow amount
- `balance` - Running balance
- `description` - Transaction description
- `reference` - Reference identifier
- `transaction_date_display` - Formatted date (MM/DD/YYYY)
- `transaction_time_display` - Formatted time (HH:MM AM/PM)
- `performed_by_username` - User who performed it
- `shift_reference` - Associated shift ID

---

## Automatic Features

✅ **Auto-Created from Shift Transactions**: Ledger entries created automatically when shift transactions occur

✅ **Running Balance**: Automatically calculated from previous transactions

✅ **Multi-Ledger Sync**: Sales and purchase ledgers auto-populated based on transaction type

✅ **Tenant Filtered**: All data automatically filtered to user's tenant

✅ **Audit Trail**: All entries immutable for compliance

---

## Common Workflows

### Daily Reconciliation
1. Get ledger by shift: `by_shift/?shift_id=17`
2. Check summary totals
3. Print ledger for records

### Period Reporting
1. List with date range: `?from_date=2025-12-01&to_date=2025-12-31`
2. View summary for totals
3. Export for reporting

### Transaction Tracking
1. Search by description: `?search=cash_in`
2. Filter by user: `?performed_by_id=5`
3. View transaction details

### Manual Adjustments
1. Create entry: `create_entry/`
2. Specify adjustment type and amount
3. Entry synced to all ledgers

---

## Data Format Notes

- **Amounts**: Decimal with 2 decimal places (e.g., "1000.00")
- **Dates**: ISO format in API, displayed as MM/DD/YYYY
- **Times**: Displayed as HH:MM AM/PM
- **Currency**: Rupees (Rs)
- **Balance**: Running total of debit - credit

---

## Integration Points

### With ShiftTransaction
- Automatically created when shift transaction occurs
- Linked via `shift` foreign key
- Debit/Credit calculated from transaction type

### With CashierShift
- Each ledger entry linked to a shift
- Can view complete ledger for a shift
- Summary shows shift-specific totals

### With Users
- `performed_by` field tracks who performed transaction
- Can filter by user
- Supports user lookup in responses

### With Branches
- Automatic branch context
- Can filter by branch
- Branch info included in responses

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid query parameter | Check parameter format |
| 404 Not Found | Shift/entry doesn't exist | Verify ID |
| 401 Unauthorized | No authentication token | Include auth header |
| 403 Forbidden | No permission | Check user permissions |

---

## Pagination

Default page size: 20 results

Customize:
```
?page=1&page_size=50
```

---

## Ordering

Entries ordered by:
1. `transaction_date` (ascending)
2. `id` (ascending)

This ensures proper running balance calculation.

---

## Performance Notes

- Indexed on: `shift`, `tenant`, `ledger_type`, `transaction_type`, `transaction_date`, `branch`
- Use date ranges for better performance with large datasets
- Shift filtering is fastest for single-shift queries

---

## Testing the API

```bash
# List all entries (today)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/cashandbank/account-ledger/"

# Get specific shift ledger
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/cashandbank/account-ledger/by_shift/?shift_id=17"

# Get summary
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/cashandbank/account-ledger/summary/?shift_id=17"

# Create manual entry
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ledger_type": "general", "transaction_type": "adjustment", "debit": 100, "credit": 0, "description": "Test", "shift_id": 17}' \
  "http://localhost:8000/api/cashandbank/account-ledger/create_entry/"
```

---

## Admin Interface

Access at: `/admin/cashandbank/accountledger/`

Features:
- View all ledger entries
- Filter by type, date, user, status
- Search by description/reference
- View transaction details
- Read-only (no direct edits)

---

## Related Documentation

- [Cashier Shift Management](CASHIER_SHIFT_API.md)
- [Bill System](BILL_SYSTEM_GUIDE.md)
- [API Stock Management](API_STOCK_MANAGEMENT.md)
