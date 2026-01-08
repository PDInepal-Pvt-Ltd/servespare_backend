# Ledger Statistics API - Quick Reference

## Endpoints

#\\\// Fetch both statistics
const [purchase, sales] = await Promise.all([
    fetch('/api/account-ledger/purchase-statistics/', {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json()),
    fetch('/api/account-ledger/sales-statistics/', {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json())
]);

console.log('Purchase Stats:', purchase);
// { total_suppliers: 15, gross_amount: "85000.50", ... }

console.log('Sales Stats:', sales);
// { total_customers: 120, gross_amount: "350000.75", ... }## 1. Purchase Ledger Statistics
\```
GET /api/account-ledger/purchase-statistics/
```

**Returns:**
- Total Suppliers
- Gross Amount
- Return Amount
- Net Amount
- Due Remaining

**Filters:** `from_date`, `to_date`, `branch_id`

---

### 2. Sales Ledger Statistics
```
GET /api/account-ledger/sales-statistics/
```

**Returns:**
- Total Customers
- Gross Amount
- Return Amount
- Net Amount
- Due Remaining

**Filters:** `from_date`, `to_date`, `branch_id`

---

## Quick Usage

### cURL Examples

```bash
# Purchase Statistics
curl -X GET "http://localhost:8000/api/account-ledger/purchase-statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Sales Statistics
curl -X GET "http://localhost:8000/api/account-ledger/sales-statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# With Date Range
curl -X GET "http://localhost:8000/api/account-ledger/purchase-statistics/?from_date=2025-01-01&to_date=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### JavaScript/Fetch

```javascript
// Purchase Statistics
const purchaseStats = await fetch('/api/account-ledger/purchase-statistics/', {
    headers: { 'Authorization': `Bearer ${token}` }
}).then(res => res.json());

// Sales Statistics
const salesStats = await fetch('/api/account-ledger/sales-statistics/', {
    headers: { 'Authorization': `Bearer ${token}` }
}).then(res => res.json());
```

### Python/Requests

```python
import requests

headers = {'Authorization': f'Bearer {token}'}

# Purchase Statistics
purchase_stats = requests.get(
    'http://localhost:8000/api/account-ledger/purchase-statistics/',
    headers=headers
).json()

# Sales Statistics
sales_stats = requests.get(
    'http://localhost:8000/api/account-ledger/sales-statistics/',
    headers=headers
).json()
```

---

## Response Format

### Purchase Statistics Response
```json
{
    "total_suppliers": 25,
    "gross_amount": "150000.00",
    "return_amount": "5000.00",
    "net_amount": "145000.00",
    "due_remaining": "0.00",
    "number_purchased_items": 1250.0,
    "number_returned_items": 50.0
}
```

### Sales Statistics Response
```json
{
    "total_customers": 150,
    "gross_amount": "500000.00",
    "return_amount": "15000.00",
    "net_amount": "485000.00",
    "due_remaining": "0.00",
    "number_purchased_products": 3500.0,
    "number_returned_products": 105.0
}
```

---

## Dashboard Integration

```javascript
// Fetch both statistics
const [purchase, sales] = await Promise.all([
    fetch('/api/account-ledger/purchase-statistics/', {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json()),
    fetch('/api/account-ledger/sales-statistics/', {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json())
]);

console.log('Purchase Stats:', purchase);
// { total_suppliers: 15, gross_amount: "85000.50", ... }

console.log('Sales Stats:', sales);
// { total_customers: 120, gross_amount: "350000.75", ... }
```

---

## Common Filters

| Filter | Format | Example |
|--------|--------|---------|
| Date | yyyy-mm-dd or mm/dd/yyyy | `from_date=2025-01-01` |
| Branch | Integer | `branch_id=1` |

---

## Tips

1. ✅ Both endpoints support the same filtering parameters
2. ✅ Date ranges are inclusive (from_date to to_date)
3. ✅ Returns zero values if no data exists (never null)
4. ✅ All amounts are strings for precision
5. ✅ Automatically filtered by authenticated user's tenant
