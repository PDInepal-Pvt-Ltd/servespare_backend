# Ledger Types - Detailed Explanation & Relationships

## Overview

The system maintains three main types of ledgers for comprehensive financial tracking. All three are derived from the `AccountLedger` model:

---

## 1. **Account Ledger** (General Ledger)

### Purpose
Complete financial record with **running balance** for a cashier shift. Tracks **ALL transactions**.

### Transaction Types Included
- `opening` - Shift Opening (cash float)
- `cash_in` - Manual cash in
- `cash_out` - Manual cash out
- `sale` - Sales from billing
- `closing` - Shift Closing
- `adjustment` - Manual adjustments
- `refund` - Refunds issued

### Key Characteristics
- **Broadest scope** - captures every transaction
- **Running balance** - maintains cumulative balance after each entry
- **Multi-purpose** - used for complete financial audit trail
- **Debit/Credit structure** - debit (inflow), credit (outflow)

### Example Entries
```
Date       | Description          | Debit  | Credit | Balance
-----------+----------------------+--------+--------+----------
09:00 AM   | Shift Opening        | 1000   | -      | 1000
09:15 AM   | Sale - Bill #101     | 500    | -      | 1500
09:30 AM   | Sale - Bill #102     | 300    | -      | 1800
10:00 AM   | Refund - Bill #101   | -      | 100    | 1700
10:15 AM   | Cash Out             | -      | 200    | 1500
```

### Model Implementation
```python
class AccountLedger(BaseModel):
    ledger_type = CharField(['general', 'sales', 'purchase', 'account'])
    transaction_type = CharField(['opening', 'cash_in', 'cash_out', 'sale', 'closing', 'adjustment', 'refund'])
    debit = DecimalField()  # Inflow
    credit = DecimalField() # Outflow
    balance = DecimalField() # Running balance
```

---

## 2. **Sales Ledger**

### Purpose
**Filtered view** of Account Ledger showing **only sales-related transactions**. Tracks revenue from sales.

### Transaction Types Included
- `sale` - Direct sales from billing system
- `refund` - Refunds on sales

### Key Characteristics
- **Narrow scope** - sales transactions only
- **Revenue tracking** - monitors cash inflow from sales
- **Proxy model** - inherits from AccountLedger (not a separate table)
- **Debit entries** - mainly debit entries (cash received)

### Example Entries
```
Date       | Description              | Debit | Credit | Balance
-----------+--------------------------+-------+--------+---------
09:15 AM   | Sale - Bill #101        | 500   | -      | 500
09:30 AM   | Sale - Bill #102        | 300   | -      | 800
10:00 AM   | Refund - Bill #101      | -     | 100    | 700
10:45 AM   | Sale - Bill #103        | 450   | -      | 1150
```

### Model Implementation
```python
class SalesLedger(AccountLedger):
    """Proxy model - same table, filtered ledger_type='sales'"""
    class Meta:
        proxy = True
        verbose_name = 'Sales Ledger'
```

### Use Cases
- Daily sales reports
- Revenue tracking
- Sales performance analysis
- Customer refund tracking

---

## 3. **Purchase Ledger**

### Purpose
**Filtered view** of Account Ledger showing **only purchase-related transactions**. Tracks cash outflow for purchases.

### Transaction Types Included
- `cash_out` - Cash paid for purchases
- Supplier payments
- Inventory purchases

### Key Characteristics
- **Narrow scope** - purchase transactions only
- **Expense tracking** - monitors cash outflow for purchases
- **Proxy model** - inherits from AccountLedger (not a separate table)
- **Credit entries** - mainly credit entries (cash paid out)

### Example Entries
```
Date       | Description                    | Debit | Credit | Balance
-----------+--------------------------------+-------+--------+---------
10:00 AM   | Purchase - Supplier A         | -     | 500    | -500
10:30 AM   | Purchase - Supplier B         | -     | 300    | -800
11:00 AM   | Purchase - Inventory Update   | -     | 200    | -1000
```

### Model Implementation
```python
class PurchaseLedger(AccountLedger):
    """Proxy model - same table, filtered ledger_type='purchase'"""
    class Meta:
        proxy = True
        verbose_name = 'Purchase Ledger'
```

### Use Cases
- Purchase orders tracking
- Supplier payment history
- Expense monitoring
- Cost analysis

---

## Relationships & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      AccountLedger (Base)                       │
│  (All transactions: sales, purchases, cash in/out, adjustments) │
└─────────────────────────────────────────────────────────────────┘
                    ↙                    ↓                  ↘
         ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
         │  SalesLedger     │  │ AccountLedger   │  │ PurchaseLedger   │
         │ (Proxy Filter)   │  │   (Full View)   │  │  (Proxy Filter)  │
         │                  │  │                 │  │                  │
         │ Shows only:      │  │ Shows all:      │  │ Shows only:      │
         │ - Sales          │  │ - Sales         │  │ - Purchases      │
         │ - Refunds        │  │ - Purchases     │  │ - Cash out       │
         │                  │  │ - Cash in/out   │  │                  │
         │ Query Filter:    │  │ - Adjustments   │  │ Query Filter:    │
         │ ledger_type=     │  │ - All types     │  │ ledger_type=     │
         │ 'sales'          │  │                 │  │ 'purchase'       │
         └──────────────────┘  └─────────────────┘  └──────────────────┘
```

---

## Key Differences - Quick Reference

| Feature | Account Ledger | Sales Ledger | Purchase Ledger |
|---------|----------------|--------------|-----------------|
| **Scope** | All transactions | Sales only | Purchases only |
| **Table** | account_ledger | account_ledger | account_ledger |
| **Model Type** | Base model | Proxy model | Proxy model |
| **Primary Flow** | In & Out | In (↑) | Out (↓) |
| **Main Purpose** | Complete audit trail | Revenue tracking | Expense tracking |
| **Typical Debit** | All types | Sales amounts | Refund amounts |
| **Typical Credit** | All types | Refund amounts | Purchase amounts |
| **Filtering** | None (or by type) | ledger_type='sales' | ledger_type='purchase' |
| **Separate Table** | Yes (account_ledger) | No (proxy) | No (proxy) |

---

## Data Storage

All three ledger types store data in a **single table**: `account_ledger`

The differentiation is achieved through:
1. **`ledger_type` field** - Specifies which ledger type ('general', 'sales', 'purchase', 'account')
2. **Proxy models** - SalesLedger and PurchaseLedger automatically filter by ledger_type
3. **Query filters** - API endpoints filter results based on ledger_type

---

## Database Schema

```sql
CREATE TABLE account_ledger (
    id BIGINT PRIMARY KEY,
    tenant_id INT,
    branch_id INT,
    shift_id INT,
    ledger_type VARCHAR(20),  -- 'general', 'sales', 'purchase', 'account'
    transaction_type VARCHAR(20),  -- 'opening', 'cash_in', 'cash_out', 'sale', 'closing', 'adjustment', 'refund'
    debit DECIMAL(14,2),  -- Inflow/Cash In
    credit DECIMAL(14,2),  -- Outflow/Cash Out
    balance DECIMAL(14,2),  -- Running balance
    description TEXT,
    reference VARCHAR(100),
    reference_type VARCHAR(50),
    reference_id VARCHAR(100),
    transaction_date DATETIME,
    performed_by_id INT,
    is_manual_entry BOOLEAN,
    notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    INDEX (shift_id),
    INDEX (ledger_type),
    INDEX (transaction_date),
    UNIQUE (shift_id, transaction_date, ledger_type)
);
```

---

## API Usage Examples

### Get All Transactions (Account Ledger)
```
GET /api/cashandbank/account-ledger/?ledger_type=general
```

### Get Only Sales
```
GET /api/cashandbank/sales-ledger/
OR
GET /api/cashandbank/account-ledger/?ledger_type=sales
```

### Get Only Purchases
```
GET /api/cashandbank/purchase-ledger/
OR
GET /api/cashandbank/account-ledger/?ledger_type=purchase
```

---

## Practical Example - Complete Day Scenario

**Shift Data:**
- Opening Balance: 1000
- 3 Sales: 500, 300, 450 (Total: 1250)
- 2 Refunds: 100, 50 (Total: 150)
- 2 Purchases: 200, 300 (Total: 500)
- Closing Balance: 1100

**Account Ledger** shows all 9 entries
**Sales Ledger** shows 5 entries (3 sales + 2 refunds)
**Purchase Ledger** shows 2 entries (2 purchases)

---

## Model Methods & Properties

### Available on All Ledger Types

```python
# Properties
account_ledger.total_inflow  # Returns debit amount
account_ledger.total_outflow  # Returns credit amount
account_ledger.net_amount  # Returns debit - credit

# QuerySet Filters
AccountLedger.objects.filter(ledger_type='sales')
AccountLedger.objects.filter(ledger_type='purchase')
SalesLedger.objects.all()  # Auto-filters to sales only
PurchaseLedger.objects.all()  # Auto-filters to purchase only
```

---

## Summary

- **AccountLedger** = Complete transaction history (all ledger types)
- **SalesLedger** = Filtered view of sales transactions (proxy)
- **PurchaseLedger** = Filtered view of purchase transactions (proxy)
- All share the **same database table** with different filter logic
- Each serves a specific reporting and analysis purpose
