# Account Ledger API Documentation

## Overview

The Account Ledger provides **complete financial records with running balances** for cashier shifts. It tracks all transactions (cash in/out, sales, adjustments) with detailed information and multiple ledger views.

## Features

✅ **Complete Transaction History** - Every transaction with date, time, amount, and running balance
✅ **Multiple Ledger Types** - General, Sales, Purchase, and Account ledgers
✅ **Advanced Filtering** - By date range, shift, transaction type, user, etc.
✅ **Running Balance Calculation** - Automatic balance tracking throughout the shift
✅ **Print Support** - Export ledger data for printing/reporting
✅ **Auto-Sync** - Automatically synced with shift transactions
✅ **Summary Statistics** - Total inflow, outflow, and net balance

## API Endpoints

### List Account Ledger Entries
```
GET /api/cashandbank/account-ledger/
```

Returns paginated list of ledger entries with summary data.

**Query Parameters:**
- `ledger_type` - Filter by ledger type: `general`, `sales`, `purchase`, `account`
- `transaction_type` - Filter by transaction type: `opening`, `cash_in`, `cash_out`, `sale`, `closing`, `adjustment`, `refund`
- `shift_id` - Filter by specific shift ID
- `from_date` - Start date (mm/dd/yyyy or yyyy-mm-dd)
- `to_date` - End date (mm/dd/yyyy or yyyy-mm-dd)
- `reference_type` - Filter by reference type: `shift`, `bill`, `invoice`, `manual`, etc.
- `performed_by_id` - Filter by user ID who performed transaction
- `branch_id` - Filter by branch ID
- `search` - Search in description, reference, or reference_id
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 20)

**Response Example:**
```json
{
  "summary": {
    "total_debit": "1100.00",
    "total_credit": "1000.00",
    "net_balance": "100.00",
    "transaction_count": 3,
    "from_date": "12/24/2025",
    "to_date": "12/24/2025",
    "ledger_type": "general",
    "filtered_by_shift": false,
    "currency": "Rs"
  },
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "ledger_type": "general",
      "transaction_type": "opening",
      "description": "Shift Opening - Cash Float",
      "reference": "Shift #shift_17",
      "debit": "100.00",
      "credit": "0.00",
      "balance": "100.00",
      "transaction_date_display": "12/24/2025",
      "transaction_time_display": "11:48 AM",
      "performed_by_username": "cashier_user",
      "shift_reference": "17"
    },
    ...
  ]
}
```

---

### Get Ledger Entry Details
```
GET /api/cashandbank/account-ledger/{id}/
```

Returns detailed information for a specific ledger entry.

**Response Example:**
```json
{
  "id": 1,
  "tenant": 1,
  "branch": 1,
  "branch_name": "Main Branch",
  "shift": 17,
  "shift_number": "17",
  "ledger_type": "general",
  "transaction_type": "opening",
  "debit": "100.00",
  "credit": "0.00",
  "balance": "100.00",
  "description": "Shift Opening - Cash Float",
  "reference": "Shift #shift_17",
  "reference_type": "shift",
  "reference_id": "17",
  "transaction_date": "2025-12-24T11:48:00Z",
  "transaction_date_display": "12/24/2025",
  "transaction_time_display": "11:48 AM",
  "performed_by": 5,
  "performed_by_username": "cashier_user",
  "performed_by_full_name": "John Cashier",
  "is_manual_entry": false,
  "notes": "Auto-synced from ShiftTransaction 42",
  "created_at": "2025-12-24T11:48:00Z",
  "updated_at": "2025-12-24T11:48:00Z"
}
```

---

### Get Ledger Summary
```
GET /api/cashandbank/account-ledger/summary/
```

Returns summary statistics for the filtered ledger data.

**Query Parameters:**
- Same filtering parameters as list endpoint

**Response Example:**
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

---

### Get General Ledger
```
GET /api/cashandbank/account-ledger/general/
```

Returns all transactions (cash in/out, sales, adjustments, opening/closing).

**Query Parameters:**
- Same filtering parameters as list endpoint

---

### Get Sales Ledger
```
GET /api/cashandbank/account-ledger/sales/
```

Returns only sales-related transactions.

**Query Parameters:**
- Same filtering parameters as list endpoint

---

### Get Purchase Ledger
```
GET /api/cashandbank/account-ledger/purchase/
```

Returns only purchase-related transactions (cash out for purchases/expenses).

**Query Parameters:**
- Same filtering parameters as list endpoint

---

### Get Ledger by Shift
```
GET /api/cashandbank/account-ledger/by_shift/?shift_id=17
```

Returns complete ledger for a specific shift with shift details.

**Query Parameters:**
- `shift_id` - **Required** - ID of the shift
- `from_date` - Optional - Filter from date
- `to_date` - Optional - Filter to date

**Response Example:**
```json
{
  "shift": {
    "id": 17,
    "cashier": "john_cashier",
    "opening_float": "1000.00",
    "opened_at": "2025-12-24T11:48:00Z",
    "status": "open"
  },
  "summary": {
    "total_debit": "1100.00",
    "total_credit": "1000.00",
    "net_balance": "100.00",
    "transaction_count": 3,
    "from_date": "12/24/2025",
    "to_date": "12/24/2025",
    "ledger_type": "general",
    "filtered_by_shift": true,
    "currency": "Rs"
  },
  "results": [...]
}
```

---

### Create Manual Ledger Entry
```
POST /api/cashandbank/account-ledger/create_entry/
```

Create a manual ledger entry for special transactions or adjustments.

**Request Body:**
```json
{
  "ledger_type": "general",
  "transaction_type": "adjustment",
  "debit": 50.00,
  "credit": 0.00,
  "description": "Damaged goods adjustment",
  "reference": "ADJ-001",
  "reference_type": "adjustment",
  "shift_id": 17,
  "notes": "Broken item found during shift"
}
```

**Response:** Returns created ledger entry (201 Created)

---

### Print Ledger
```
GET /api/cashandbank/account-ledger/print_ledger/
```

Returns complete ledger data formatted for printing (no pagination).

**Query Parameters:**
- Same filtering parameters as list endpoint

**Response Example:**
```json
{
  "summary": {
    "total_debit": "1100.00",
    "total_credit": "1000.00",
    "net_balance": "100.00",
    "transaction_count": 3,
    "from_date": "12/24/2025",
    "to_date": "12/24/2025",
    "ledger_type": "general",
    "filtered_by_shift": false,
    "currency": "Rs"
  },
  "entries": [...],
  "print_metadata": {
    "generated_at": "2025-12-24T15:30:00Z",
    "total_entries": 3
  }
}
```

---

## Sample Usage Examples

### Get General Ledger for Today
```bash
curl -X GET "http://localhost:8000/api/cashandbank/account-ledger/general/?from_date=2025-12-24&to_date=2025-12-24" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Sales Ledger for a Specific Shift
```bash
curl -X GET "http://localhost:8000/api/cashandbank/account-ledger/sales/?shift_id=17" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Ledger with Date Range and Branch Filter
```bash
curl -X GET "http://localhost:8000/api/cashandbank/account-ledger/?from_date=2025-12-20&to_date=2025-12-24&branch_id=1&ledger_type=general" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search Transactions
```bash
curl -X GET "http://localhost:8000/api/cashandbank/account-ledger/?search=cash_in" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Summary Only
```bash
curl -X GET "http://localhost:8000/api/cashandbank/account-ledger/summary/?shift_id=17" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Export for Printing
```bash
curl -X GET "http://localhost:8000/api/cashandbank/account-ledger/print_ledger/?shift_id=17" \
  -H "Authorization: Bearer YOUR_TOKEN" > ledger.json
```

---

## Data Models

### AccountLedger Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique identifier |
| `tenant` | FK | Tenant context |
| `branch` | FK | Branch context |
| `shift` | FK | Associated shift |
| `ledger_type` | Choice | general, sales, purchase, account |
| `transaction_type` | Choice | opening, cash_in, cash_out, sale, closing, adjustment, refund |
| `debit` | Decimal | Inflow amount (cash in) |
| `credit` | Decimal | Outflow amount (cash out) |
| `balance` | Decimal | Running balance after this transaction |
| `description` | Text | Transaction description |
| `reference` | Char | Reference identifier (e.g., Shift #17) |
| `reference_type` | Char | Type of reference (shift, bill, invoice, etc.) |
| `reference_id` | Char | ID of referenced object |
| `transaction_date` | DateTime | When transaction occurred |
| `performed_by` | FK | User who performed transaction |
| `is_manual_entry` | Boolean | Whether manually created |
| `notes` | Text | Additional notes |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Record last update timestamp |

---

## Transaction Types and Amounts

### Opening Transaction
- **Type**: `opening`
- **Debit**: Opening float amount
- **Credit**: 0
- **Effect**: Initializes shift balance

### Cash In
- **Type**: `cash_in`
- **Debit**: Amount received
- **Credit**: 0
- **Effect**: Increases balance

### Sale
- **Type**: `sale`
- **Debit**: Sale amount
- **Credit**: 0
- **Effect**: Increases balance, appears in Sales Ledger + General Ledger

### Cash Out
- **Type**: `cash_out`
- **Debit**: 0
- **Credit**: Amount paid out
- **Effect**: Decreases balance, appears in Purchase Ledger + General Ledger

### Closing Transaction
- **Type**: `closing`
- **Debit**: 0
- **Credit**: Amount counted
- **Effect**: Settles final balance

### Adjustment
- **Type**: `adjustment`
- **Debit/Credit**: As specified
- **Effect**: Manual correction to balance

---

## Running Balance Calculation

The running balance is calculated as:

```
Balance = Previous Balance + Debit - Credit
```

For a shift with:
1. Opening: +100 → Balance: 100
2. Sale: +1,000 → Balance: 1,100
3. Closing: -1,000 → Balance: 100

---

## Summary Metrics

- **Total Debit (Inflow)**: Sum of all debit amounts
- **Total Credit (Outflow)**: Sum of all credit amounts
- **Net Balance**: Total Debit - Total Credit
- **Transaction Count**: Total number of transactions
- **Currency**: Display currency (Rs for Rupees)

---

## Permissions

- **Authentication**: Required (IsAuthenticated)
- **Authorization**: User must have `CanManageBranchResources` permission
- **Tenant Filtering**: Automatically filtered to user's tenant

---

## Automatic Ledger Sync

Account Ledger entries are **automatically created** when:

1. **ShiftTransaction** is created
   - Debit/Credit amounts calculated based on transaction type
   - Running balance computed from previous transactions
   - Appropriate ledger types updated (general, sales, purchase)

2. **Signals**: `sync_shift_transaction_to_ledger` ensures synchronization

Example transaction flow:
```
ShiftTransaction (type: sale, amount: 100)
  ↓
AccountLedger entry created
  ├─ general ledger (debit: 100)
  └─ sales ledger (debit: 100)
```

---

## Example Shift Ledger Output

```
ACCOUNT LEDGER - Shift #shift_17
Generated: 24/12/2025 15:30 AM

Date       Time      Description              Reference    Debit(Rs)  Credit(Rs)  Balance(Rs)
═════════════════════════════════════════════════════════════════════════════════════════════
24/12/2025 11:48 AM  Shift Opening - Cash     Shift #17    100        -           100
24/12/2025 11:49 AM  Shift Opening - Cash     Shift #17    1,000      -           1,100
24/12/2025 11:49 AM  Shift Closing            Shift #17    -          1,000       100
                                        TOTALS: 1,100      1,000       100
═════════════════════════════════════════════════════════════════════════════════════════════
Total Debit (Inflow):   Rs 1,100
Total Credit (Outflow): Rs 1,000
Net Balance:            Rs 100
```

---

## Notes

- All amounts are stored with 2 decimal places
- Dates are formatted as MM/DD/YYYY for display
- Times are formatted as HH:MM AM/PM
- Ledger entries are read-only (no updates/deletes to maintain audit trail)
- Running balance updates are atomic to prevent inconsistencies
- All queries are tenant-filtered for security
