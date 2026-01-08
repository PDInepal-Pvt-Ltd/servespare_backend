# Dashboard Ledger Statistics

Quick access to purchase and sales ledger statistics for your dashboard.

## Quick Start

### Purchase Statistics
```javascript
fetch('/api/account-ledger/purchase-statistics/', {
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
})
.then(res => res.json())
.then(data => {
    console.log('Suppliers:', data.total_suppliers);
    console.log('Net Amount:', data.net_amount);
});
```

### Sales Statistics
```javascript
fetch('/api/account-ledger/sales-statistics/', {
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
})
.then(res => res.json())
.then(data => {
    console.log('Customers:', data.total_customers);
    console.log('Net Amount:', data.net_amount);
});
```

## What You Get

### Purchase Ledger
- Total Suppliers
- Gross Amount
- Return Amount
- Net Amount
- Due Remaining

### Sales Ledger
- Total Customers
- Gross Amount
- Return Amount
- Net Amount
- Due Remaining

## Filters

Add query parameters to filter data:
```
?from_date=2025-01-01&to_date=2025-01-31&branch_id=1
```

## Documentation

📖 **Full Documentation:** [docs/LEDGER_STATISTICS_API.md](docs/LEDGER_STATISTICS_API.md)  
⚡ **Quick Reference:** [docs/LEDGER_STATISTICS_QUICK_REFERENCE.md](docs/LEDGER_STATISTICS_QUICK_REFERENCE.md)  
📝 **Implementation Details:** [LEDGER_STATISTICS_IMPLEMENTATION.md](LEDGER_STATISTICS_IMPLEMENTATION.md)
