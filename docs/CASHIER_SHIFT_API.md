# Cashier Shift Management API Documentation

## Overview

The Cashier Shift Management system implements a complete workflow for managing cash drawer operations by cashiers. It tracks opening/closing balances, cash transactions, and automatically posts sales to active shifts.

## Models

### CashierShift

Represents a cashier's shift with complete lifecycle management.

**Fields:**
- `id` - Unique shift identifier
- `tenant` - Tenant that owns the shift
- `branch` - Branch where the shift occurred
- `cashier` - User (cashier) conducting the shift
- `status` - Status: 'open', 'closed', or 'flagged'
- `opening_float` - Cash amount at start of shift (Decimal)
- `opened_at` - Timestamp when shift was opened
- `expected_amount` - Expected cash (opening + sales - adjustments)
- `actual_amount` - Actual counted cash at close (null if open)
- `closed_at` - Timestamp when shift was closed (null if open)
- `variance_amount` - Difference between expected and actual
- `variance_reason` - Reason for variance if close differs from expected
- `notes` - General notes about the shift
- `is_flagged` - Auto-flagged if |variance| > 100
- `is_active` - Soft delete flag
- `created`, `modified` - Timestamps

**Key Properties:**
- `duration` - Shift duration in minutes
- `is_balanced` - Boolean indicating if shift is balanced (within ±0.01)

**Key Methods:**
- `open_shift(opening_float)` - Initialize and open a new shift
- `adjust_expected_amount(amount)` - Adjust expected amount by amount
- `close_shift(actual_amount, variance_reason=None, notes=None)` - Close shift
- `get_transaction_summary()` - Get summary of all transactions in shift

### ShiftTransaction

Individual transactions within a shift.

**Fields:**
- `id` - Unique transaction identifier
- `shift` - Reference to parent shift
- `tenant` - Tenant that owns this transaction
- `transaction_type` - Type: 'opening', 'cash_in', 'cash_out', 'sale', 'closing'
- `amount` - Transaction amount (always positive)
- `description` - Description or reason for transaction
- `reference_type` - Type of reference (e.g., 'bill', 'invoice')
- `reference_id` - ID of referenced object
- `transaction_date` - When the transaction occurred
- `performed_by` - User who performed the transaction
- `is_active` - Soft delete flag
- `created`, `modified` - Timestamps

**Key Properties:**
- `signed_amount` - Amount with appropriate sign (in/opening/sale = +, out/closing = -)

## API Endpoints

### List Shifts

```
GET /api/cashandbank/shifts/
```

**Query Parameters:**
- `status` - Filter by status (open, closed, flagged)
- `cashier_id` - Filter by cashier ID
- `is_flagged` - Filter flagged shifts (true/false)

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "cashier": 5,
      "cashier_name": "john_doe",
      "branch": 1,
      "branch_name": "Main Branch",
      "status": "closed",
      "opening_float": "1000.00",
      "opened_at": "2025-12-24T08:00:00Z",
      "expected_amount": "2150.50",
      "actual_amount": "2150.50",
      "closed_at": "2025-12-24T16:00:00Z",
      "variance_amount": "0.00",
      "is_balanced": true,
      "duration_minutes": 480.0,
      "transaction_summary": {
        "total_cash_in": "100.00",
        "total_cash_out": "50.00",
        "total_sales": "1200.50",
        "total_adjustments": "50.00",
        "transaction_count": 12
      }
    }
  ]
}
```

### Get Active Shift

```
GET /api/cashandbank/shifts/active/
```

Returns the current open shift for the authenticated user, or 404 if none exists.

**Response:**
```json
{
  "id": 1,
  "cashier": 5,
  "cashier_name": "john_doe",
  "status": "open",
  "opening_float": "1000.00",
  "opened_at": "2025-12-24T08:00:00Z",
  "expected_amount": "1200.00",
  "actual_amount": null,
  "closed_at": null,
  "variance_amount": null,
  "is_balanced": null,
  "duration_minutes": 30.0,
  "transaction_summary": {
    "total_cash_in": "0.00",
    "total_cash_out": "0.00",
    "total_sales": "200.00",
    "total_adjustments": "0.00",
    "transaction_count": 2
  }
}
```

### Open Shift

```
POST /api/cashandbank/shifts/open/
```

Create and open a new shift for the current user.

**Request Body:**
```json
{
  "opening_float": 1000.00,
  "branch_id": 1,
  "notes": "Opening shift on 2025-12-24"
}
```

**Response:** 201 Created (CashierShift serialized)

**Error Responses:**
- 400: Missing opening_float
- 400: User already has open shift
- 400: Invalid opening_float (negative or non-numeric)

### Cash In

```
POST /api/cashandbank/shifts/{shift_id}/cash_in/
```

Add cash to the shift (increment expected amount).

**Request Body:**
```json
{
  "amount": 500.00,
  "description": "Customer refund"
}
```

**Response:** 200 OK (updated CashierShift)

**Error Responses:**
- 400: Shift is not open
- 400: Missing or invalid amount

### Cash Out

```
POST /api/cashandbank/shifts/{shift_id}/cash_out/
```

Remove cash from the shift (decrement expected amount).

**Request Body:**
```json
{
  "amount": 250.00,
  "description": "Reimbursement to manager"
}
```

**Response:** 200 OK (updated CashierShift)

**Error Responses:**
- 400: Shift is not open
- 400: Missing or invalid amount

### Close Shift (Balanced)

```
POST /api/cashandbank/shifts/{shift_id}/close_balanced/
```

Close a shift when the actual amount matches expected (balanced).

**Request Body:**
```json
{
  "actual_amount": 2000.00,
  "notes": "Perfect balance"
}
```

**Response:** 200 OK (closed CashierShift with variance_amount=0)

**Error Responses:**
- 400: Shift is not open
- 400: Actual amount is not balanced (differs by more than ±0.01)
- 400: Missing or invalid actual_amount

### Close Shift (With Variance)

```
POST /api/cashandbank/shifts/{shift_id}/close_variance/
```

Close a shift when the actual amount differs from expected.

**Request Body:**
```json
{
  "actual_amount": 1950.00,
  "variance_reason": "Miscounted during count",
  "notes": "Recounted and confirmed"
}
```

**Response:** 200 OK (closed CashierShift with variance data)

**Auto-Flagging:** If |variance| > 100, the shift is automatically flagged.

**Error Responses:**
- 400: Shift is not open
- 400: Missing or invalid actual_amount

### Get Shift Transactions

```
GET /api/cashandbank/shifts/{shift_id}/transactions/
```

Get all transactions for a specific shift.

**Response:**
```json
[
  {
    "id": 1,
    "shift": 1,
    "transaction_type": "opening",
    "transaction_type_display": "Opening",
    "amount": "1000.00",
    "signed_amount": "1000.00",
    "description": "Shift opening float",
    "reference_type": null,
    "reference_id": null,
    "transaction_date": "2025-12-24T08:00:00Z",
    "performed_by": 5,
    "performed_by_name": "john_doe"
  },
  {
    "id": 2,
    "shift": 1,
    "transaction_type": "sale",
    "transaction_type_display": "Sale",
    "amount": "200.00",
    "signed_amount": "200.00",
    "description": "Sale from bill 42 to John Smith",
    "reference_type": "bill",
    "reference_id": "42",
    "transaction_date": "2025-12-24T09:30:00Z",
    "performed_by": 5,
    "performed_by_name": "john_doe"
  },
  {
    "id": 3,
    "shift": 1,
    "transaction_type": "cash_in",
    "transaction_type_display": "Cash In",
    "amount": "100.00",
    "signed_amount": "100.00",
    "description": "Customer refund",
    "reference_type": null,
    "reference_id": null,
    "transaction_date": "2025-12-24T10:15:00Z",
    "performed_by": 5,
    "performed_by_name": "john_doe"
  },
  {
    "id": 4,
    "shift": 1,
    "transaction_type": "closing",
    "transaction_type_display": "Closing",
    "amount": "1300.00",
    "signed_amount": "-1300.00",
    "description": "Shift closing (variance: 0.00)",
    "reference_type": null,
    "reference_id": null,
    "transaction_date": "2025-12-24T16:00:00Z",
    "performed_by": 5,
    "performed_by_name": "john_doe"
  }
]
```

## Shift Flow Workflow

### 1. Identify Active Shift

```
GET /api/cashandbank/shifts/active/
```

- Returns the open shift for the current user/branch
- Returns 404 if no active shift exists

### 2. Open Shift

```
POST /api/cashandbank/shifts/open/
{
  "opening_float": 1000.00,
  "branch_id": 1
}
```

- Validates opening float > 0
- Creates shift record with status='open'
- Seeds opening transaction
- Sets expected_amount to opening_float

### 3. Adjust Cash During Shift

**Cash In:**
```
POST /api/cashandbank/shifts/{id}/cash_in/
{
  "amount": 500.00,
  "description": "Refund"
}
```
- Increments expected_amount
- Creates cash_in transaction

**Cash Out:**
```
POST /api/cashandbank/shifts/{id}/cash_out/
{
  "amount": 250.00,
  "description": "Reimbursement"
}
```
- Decrements expected_amount
- Creates cash_out transaction

### 4. Auto Sales Posting

When a Bill is created with:
- `payment_method = 'cash'`
- `status = 'paid'`

The system automatically:
- Finds active shift for the cashier/branch
- Adds sale transaction to shift
- Increments expected_amount by bill total

### 5. Close Shift (Balanced)

```
POST /api/cashandbank/shifts/{id}/close_balanced/
{
  "actual_amount": 2000.00,
  "notes": "Perfect balance"
}
```

- Validates closing amount ≥ 0
- Checks if actual ≈ expected (±0.01)
- If balanced:
  - Creates closing transaction
  - Sets status='closed'
  - variance_amount = 0
  - Clears variance fields
  - Saves and clears active shift

### 6. Close Shift (With Variance)

```
POST /api/cashandbank/shifts/{id}/close_variance/
{
  "actual_amount": 1950.00,
  "variance_reason": "Miscounted",
  "notes": "Recounted"
}
```

- Validates closing amount ≥ 0
- Allows actual ≠ expected
- Requires variance_reason
- Creates closing transaction
- Sets status='closed'
- Stores variance_amount and reason
- Auto-flags if |variance| > 100
- Saves and clears active shift

## Transaction Types

| Type | Direction | Sign | Description |
|------|-----------|------|-------------|
| opening | In | + | Initial float when shift opens |
| cash_in | In | + | Manual cash addition |
| sale | In | + | Auto-posted from bill creation |
| cash_out | Out | - | Manual cash removal |
| closing | Out | - | Final count when shift closes |

## Authentication & Permissions

All endpoints require:
- `IsAuthenticated` - User must be logged in
- `CanManageBranchResources` - User must have branch management permission

Tenant scoping is automatic based on request user's tenant.

## Error Handling

All errors follow standard HTTP status codes:
- 400: Bad Request (validation errors, business logic violations)
- 401: Unauthorized (not authenticated)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (shift doesn't exist or no active shift)
- 500: Server Error

## Example Complete Flow

```bash
# 1. Open shift
POST /api/cashandbank/shifts/open/
{
  "opening_float": 1000.00,
  "branch_id": 1,
  "notes": "Start of day"
}
# Response: { id: 1, status: "open", expected_amount: "1000.00", ... }

# 2. Get active shift
GET /api/cashandbank/shifts/active/
# Response: { id: 1, status: "open", ... }

# 3. Add cash in (refund)
POST /api/cashandbank/shifts/1/cash_in/
{
  "amount": 100.00,
  "description": "Customer refund"
}
# Response: { id: 1, expected_amount: "1100.00", ... }

# 4. System auto-posts sales from bills
# (automatic when bills are created with payment_method='cash')

# 5. Add cash out (reimbursement)
POST /api/cashandbank/shifts/1/cash_out/
{
  "amount": 50.00,
  "description": "Float to manager"
}
# Response: { id: 1, expected_amount: "1050.00", ... }

# 6. Get transactions
GET /api/cashandbank/shifts/1/transactions/
# Response: [ opening, sale, cash_in, cash_out, ... ]

# 7. Close shift (balanced)
POST /api/cashandbank/shifts/1/close_balanced/
{
  "actual_amount": 1250.00,
  "notes": "Perfect"
}
# Response: { id: 1, status: "closed", variance_amount: "0.00", ... }
```
