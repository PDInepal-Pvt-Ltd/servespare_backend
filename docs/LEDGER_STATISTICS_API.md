# Ledger Statistics API Documentation

## Overview
This document describes the statistics API endpoints for Purchase and Sales ledgers, designed specifically for dashboard use.

## Base URL
```
/api/account-ledger/
```

---

## 1. Purchase Ledger Statistics

### Endpoint
```
GET /api/account-ledger/purchase-statistics/
```

### Description
Get comprehensive statistics for purchase ledger including suppliers, amounts, and item counts.

### Authentication
- **Required**: Yes (Bearer Token)
- **Permissions**: `IsAuthenticated`, `CanManageBranchResources`

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `from_date` | string | No | Start date for filtering | `2025-01-01` or `01/01/2025` |
| `to_date` | string | No | End date for filtering | `2025-12-31` or `12/31/2025` |
| `branch_id` | integer | No | Filter by specific branch | `1` |

### Response Format

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

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_suppliers` | integer | Total number of unique suppliers |
| `gross_amount` | string | Total gross purchase amount |
| `return_amount` | string | Total amount of returned purchases |
| `net_amount` | string | Net purchase amount (gross - returns) |
| `due_remaining` | string | Outstanding amount due to suppliers |
| `number_purchased_items` | float | Total quantity of items purchased |
| `number_returned_items` | float | Total quantity of items returned |

### Example Request

```bash
# Basic request
curl -X GET "http://localhost:8000/api/account-ledger/purchase-statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# With date filters
curl -X GET "http://localhost:8000/api/account-ledger/purchase-statistics/?from_date=2025-01-01&to_date=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"

# With branch filter
curl -X GET "http://localhost:8000/api/account-ledger/purchase-statistics/?branch_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example Response (Success - 200 OK)

```json
{
    "total_suppliers": 15,
    "gross_amount": "85000.50",
    "return_amount": "2500.00",
    "net_amount": "82500.50",
    "due_remaining": "0.00",
    "number_purchased_items": 850.0,
    "number_returned_items": 25.0
}
```

### Example Response (No Data - 200 OK)

```json
{
    "total_suppliers": 0,
    "gross_amount": "0.00",
    "return_amount": "0.00",
    "net_amount": "0.00",
    "due_remaining": "0.00",
    "number_purchased_items": 0.0,
    "number_returned_items": 0.0
}
```

---

## 2. Sales Ledger Statistics

### Endpoint
```
GET /api/account-ledger/sales-statistics/
```

### Description
Get comprehensive statistics for sales ledger including customers, amounts, and product counts.

### Authentication
- **Required**: Yes (Bearer Token)
- **Permissions**: `IsAuthenticated`, `CanManageBranchResources`

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `from_date` | string | No | Start date for filtering | `2025-01-01` or `01/01/2025` |
| `to_date` | string | No | End date for filtering | `2025-12-31` or `12/31/2025` |
| `branch_id` | integer | No | Filter by specific branch | `1` |

### Response Format

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

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_customers` | integer | Total number of unique customers |
| `gross_amount` | string | Total gross sales amount |
| `return_amount` | string | Total amount of returned sales |
| `net_amount` | string | Net sales amount (gross - returns) |
| `due_remaining` | string | Outstanding amount due from customers |
| `number_purchased_products` | float | Total quantity of products sold |
| `number_returned_products` | float | Total quantity of products returned |

### Example Request

```bash
# Basic request
curl -X GET "http://localhost:8000/api/account-ledger/sales-statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# With date filters
curl -X GET "http://localhost:8000/api/account-ledger/sales-statistics/?from_date=2025-01-01&to_date=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"

# With branch filter
curl -X GET "http://localhost:8000/api/account-ledger/sales-statistics/?branch_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example Response (Success - 200 OK)

```json
{
    "total_customers": 120,
    "gross_amount": "350000.75",
    "return_amount": "8500.25",
    "net_amount": "341500.50",
    "due_remaining": "0.00",
    "number_purchased_products": 2800.0,
    "number_returned_products": 68.0
}
```

### Example Response (No Data - 200 OK)

```json
{
    "total_customers": 0,
    "gross_amount": "0.00",
    "return_amount": "0.00",
    "net_amount": "0.00",
    "due_remaining": "0.00",
    "number_purchased_products": 0.0,
    "number_returned_products": 0.0
}
```

---

## Common Error Responses

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

## Frontend Integration Example

### React/JavaScript Example

```javascript
// Fetch Purchase Statistics
async function fetchPurchaseStatistics(fromDate, toDate, branchId) {
    const params = new URLSearchParams();
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (branchId) params.append('branch_id', branchId);

    const response = await fetch(
        `/api/account-ledger/purchase-statistics/?${params.toString()}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        }
    );

    if (!response.ok) {
        throw new Error('Failed to fetch purchase statistics');
    }

    return await response.json();
}

// Fetch Sales Statistics
async function fetchSalesStatistics(fromDate, toDate, branchId) {
    const params = new URLSearchParams();
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (branchId) params.append('branch_id', branchId);

    const response = await fetch(
        `/api/account-ledger/sales-statistics/?${params.toString()}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        }
    );

    if (!response.ok) {
        throw new Error('Failed to fetch sales statistics');
    }

    return await response.json();
}

// Usage example
async function loadDashboardStats() {
    try {
        const [purchaseStats, salesStats] = await Promise.all([
            fetchPurchaseStatistics('2025-01-01', '2025-01-31'),
            fetchSalesStatistics('2025-01-01', '2025-01-31'),
        ]);

        console.log('Purchase Statistics:', purchaseStats);
        console.log('Sales Statistics:', salesStats);

        // Update dashboard UI with the data
        updateDashboard(purchaseStats, salesStats);
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const DashboardStats = () => {
    const [purchaseStats, setPurchaseStats] = useState(null);
    const [salesStats, setSalesStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            setLoading(true);
            const [purchase, sales] = await Promise.all([
                fetchPurchaseStatistics(),
                fetchSalesStatistics(),
            ]);
            setPurchaseStats(purchase);
            setSalesStats(sales);
        } catch (error) {
            console.error('Error loading stats:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div className="dashboard-stats">
            {/* Purchase Statistics Card */}
            <div className="stats-card">
                <h2>Purchase Ledger</h2>
                <div className="stat-item">
                    <label>Total Suppliers:</label>
                    <span>{purchaseStats.total_suppliers}</span>
                </div>
                <div className="stat-item">
                    <label>Gross Amount:</label>
                    <span>Rs. {purchaseStats.gross_amount}</span>
                </div>
                <div className="stat-item">
                    <label>Return Amount:</label>
                    <span>Rs. {purchaseStats.return_amount}</span>
                </div>
                <div className="stat-item">
                    <label>Net Amount:</label>
                    <span>Rs. {purchaseStats.net_amount}</span>
                </div>
                <div className="stat-item">
                    <label>Due Remaining:</label>
                    <span>Rs. {purchaseStats.due_remaining}</span>
                </div>
            </div>

            {/* Sales Statistics Card */}
            <div className="stats-card">
                <h2>Sales Ledger</h2>
                <div className="stat-item">
                    <label>Total Customers:</label>
                    <span>{salesStats.total_customers}</span>
                </div>
                <div className="stat-item">
                    <label>Gross Amount:</label>
                    <span>Rs. {salesStats.gross_amount}</span>
                </div>
                <div className="stat-item">
                    <label>Return Amount:</label>
                    <span>Rs. {salesStats.return_amount}</span>
                </div>
                <div className="stat-item">
                    <label>Net Amount:</label>
                    <span>Rs. {salesStats.net_amount}</span>
                </div>
                <div className="stat-item">
                    <label>Due Remaining:</label>
                    <span>Rs. {salesStats.due_remaining}</span>
                </div>
            </div>
        </div>
    );
};

export default DashboardStats;
```

---

## Notes

1. **Date Formats**: Both `yyyy-mm-dd` and `mm/dd/yyyy` formats are supported
2. **Tenant Isolation**: All data is automatically filtered by the authenticated user's tenant
3. **Branch Filtering**: If no `branch_id` is provided, data from all branches is included
4. **Performance**: These endpoints are optimized for dashboard use with aggregated queries
5. **Currency**: All amounts are in the system's default currency (Rs)
6. **Due Remaining**: Currently returns `0.00` (can be enhanced with payment tracking)

---

## Related Endpoints

- `GET /api/account-ledger/` - List all ledger entries
- `GET /api/account-ledger/summary/` - Get detailed ledger summary
- `GET /api/account-ledger/sales/` - Get sales ledger entries
- `GET /api/account-ledger/purchase/` - Get purchase ledger entries

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-08 | Initial release of statistics endpoints |
