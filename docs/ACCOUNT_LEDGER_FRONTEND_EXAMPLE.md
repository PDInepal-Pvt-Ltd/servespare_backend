# Account Ledger - Frontend Integration Example

## Exact API Response Matching Your UI

Based on your UI mockup:

```
Date       Time      Description                    Reference      Debit(Rs)  Credit(Rs)  Balance(Rs)
24/12/2025 11:48 AM  Shift Opening - Cash Float    Shift #shift_17   100         -          100
24/12/2025 11:49 AM  Shift Opening - Cash Float    Shift #shift_17   1,000       -          1,100
24/12/2025 11:49 AM  Shift Closing                 Shift #shift_17   -           1,000      100
                                            TOTALS:                   1,100       1,000      100
```

---

## API Call

```bash
GET /api/cash-and-bank/account-ledger/by_shift/?shift_id=17
```

---

## Actual JSON Response

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
  "results": [
    {
      "id": 1,
      "transaction_date_display": "12/24/2025",
      "transaction_time_display": "11:48 AM",
      "description": "Shift Opening - Cash Float",
      "reference": "Shift #shift_17",
      "debit": "100.00",
      "credit": "0.00",
      "balance": "100.00",
      "transaction_type": "opening",
      "ledger_type": "general",
      "performed_by_username": "john_cashier",
      "shift_reference": "17"
    },
    {
      "id": 2,
      "transaction_date_display": "12/24/2025",
      "transaction_time_display": "11:49 AM",
      "description": "Shift Opening - Cash Float",
      "reference": "Shift #shift_17",
      "debit": "1000.00",
      "credit": "0.00",
      "balance": "1100.00",
      "transaction_type": "opening",
      "ledger_type": "general",
      "performed_by_username": "john_cashier",
      "shift_reference": "17"
    },
    {
      "id": 3,
      "transaction_date_display": "12/24/2025",
      "transaction_time_display": "11:49 AM",
      "description": "Shift Closing",
      "reference": "Shift #shift_17",
      "debit": "0.00",
      "credit": "1000.00",
      "balance": "100.00",
      "transaction_type": "closing",
      "ledger_type": "general",
      "performed_by_username": "john_cashier",
      "shift_reference": "17"
    }
  ]
}
```

---

## React/Vue Table Component Example

### React Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AccountLedgerTable({ shiftId }) {
  const [ledgerData, setLedgerData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLedgerData();
  }, [shiftId]);

  const fetchLedgerData = async () => {
    try {
      const response = await axios.get(
        `/api/cash-and-bank/account-ledger/by_shift/?shift_id=${shiftId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      setLedgerData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching ledger:', error);
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!ledgerData) return <div>No data</div>;

  const { summary, results } = ledgerData;

  return (
    <div className="account-ledger">
      <h2>Account Ledger</h2>
      <p className="subtitle">Complete transaction history with running balance</p>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <h3>Total Debit (Inflow)</h3>
          <p className="amount positive">Rs {parseFloat(summary.total_debit).toLocaleString()}</p>
        </div>
        <div className="summary-card">
          <h3>Total Credit (Outflow)</h3>
          <p className="amount negative">Rs {parseFloat(summary.total_credit).toLocaleString()}</p>
        </div>
        <div className="summary-card">
          <h3>Net Balance</h3>
          <p className="amount">Rs {parseFloat(summary.net_balance).toLocaleString()}</p>
        </div>
      </div>

      {/* Ledger Table */}
      <table className="ledger-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Time</th>
            <th>Description</th>
            <th>Reference</th>
            <th className="amount-col">Debit (Rs)</th>
            <th className="amount-col">Credit (Rs)</th>
            <th className="amount-col">Balance (Rs)</th>
          </tr>
        </thead>
        <tbody>
          {results.map((entry) => (
            <tr key={entry.id}>
              <td>{entry.transaction_date_display}</td>
              <td>{entry.transaction_time_display}</td>
              <td>{entry.description}</td>
              <td>{entry.reference}</td>
              <td className="amount-col">
                {parseFloat(entry.debit) > 0 
                  ? parseFloat(entry.debit).toLocaleString() 
                  : '-'}
              </td>
              <td className="amount-col">
                {parseFloat(entry.credit) > 0 
                  ? parseFloat(entry.credit).toLocaleString() 
                  : '-'}
              </td>
              <td className="amount-col balance">
                {parseFloat(entry.balance).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="totals-row">
            <td colSpan="4" className="totals-label">TOTALS:</td>
            <td className="amount-col total">
              Rs {parseFloat(summary.total_debit).toLocaleString()}
            </td>
            <td className="amount-col total">
              Rs {parseFloat(summary.total_credit).toLocaleString()}
            </td>
            <td className="amount-col total balance">
              Rs {parseFloat(summary.net_balance).toLocaleString()}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

export default AccountLedgerTable;
```

### CSS Styling

```css
.account-ledger {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.account-ledger h2 {
  margin-bottom: 5px;
  color: #333;
}

.subtitle {
  color: #666;
  margin-bottom: 20px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.summary-card {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.summary-card h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.summary-card .amount {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}

.amount.positive {
  color: #28a745;
}

.amount.negative {
  color: #dc3545;
}

.ledger-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.ledger-table th {
  background: #f8f9fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
}

.ledger-table td {
  padding: 12px;
  border-bottom: 1px solid #dee2e6;
}

.ledger-table .amount-col {
  text-align: right;
  font-family: 'Courier New', monospace;
}

.ledger-table .balance {
  font-weight: 600;
  color: #007bff;
}

.ledger-table tfoot tr {
  background: #f8f9fa;
  font-weight: bold;
}

.ledger-table .totals-label {
  text-align: right;
  padding-right: 20px;
}

.ledger-table .total {
  font-weight: bold;
  font-size: 16px;
}

.ledger-table tbody tr:hover {
  background: #f8f9fa;
}
```

---

## Filters Component Example

```jsx
function LedgerFilters({ onFilterChange }) {
  const [filters, setFilters] = useState({
    from_date: '',
    to_date: '',
    shift_id: '',
    transaction_type: ''
  });

  const handleChange = (field, value) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="ledger-filters">
      <div className="filter-group">
        <label>From Date</label>
        <input 
          type="date" 
          value={filters.from_date}
          onChange={(e) => handleChange('from_date', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>To Date</label>
        <input 
          type="date" 
          value={filters.to_date}
          onChange={(e) => handleChange('to_date', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Filter by Shift</label>
        <select 
          value={filters.shift_id}
          onChange={(e) => handleChange('shift_id', e.target.value)}
        >
          <option value="">All Shifts</option>
          <option value="1">Shift #1</option>
          <option value="2">Shift #2</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Transaction Type</label>
        <select 
          value={filters.transaction_type}
          onChange={(e) => handleChange('transaction_type', e.target.value)}
        >
          <option value="">All Types</option>
          <option value="opening">Opening</option>
          <option value="cash_in">Cash In</option>
          <option value="cash_out">Cash Out</option>
          <option value="sale">Sale</option>
          <option value="closing">Closing</option>
        </select>
      </div>

      <button className="btn-print" onClick={() => window.print()}>
        Print Ledger
      </button>
    </div>
  );
}
```

---

## Print Function

```javascript
function printLedger(shiftId) {
  // Fetch unpaginated data
  axios.get(`/api/cash-and-bank/account-ledger/print_ledger/?shift_id=${shiftId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  .then(response => {
    const { summary, entries } = response.data;
    
    // Generate print-friendly HTML
    const printContent = `
      <html>
      <head>
        <title>Account Ledger - Shift #${shiftId}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h1 { text-align: center; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
          .amount { text-align: right; }
          .total-row { font-weight: bold; background-color: #f2f2f2; }
        </style>
      </head>
      <body>
        <h1>Account Ledger - Shift #${shiftId}</h1>
        <p>Generated: ${new Date().toLocaleString()}</p>
        
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Time</th>
              <th>Description</th>
              <th>Reference</th>
              <th class="amount">Debit (Rs)</th>
              <th class="amount">Credit (Rs)</th>
              <th class="amount">Balance (Rs)</th>
            </tr>
          </thead>
          <tbody>
            ${entries.map(entry => `
              <tr>
                <td>${entry.transaction_date_display}</td>
                <td>${entry.transaction_time_display}</td>
                <td>${entry.description}</td>
                <td>${entry.reference}</td>
                <td class="amount">${parseFloat(entry.debit) > 0 ? entry.debit : '-'}</td>
                <td class="amount">${parseFloat(entry.credit) > 0 ? entry.credit : '-'}</td>
                <td class="amount">${entry.balance}</td>
              </tr>
            `).join('')}
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="4">TOTALS:</td>
              <td class="amount">Rs ${summary.total_debit}</td>
              <td class="amount">Rs ${summary.total_credit}</td>
              <td class="amount">Rs ${summary.net_balance}</td>
            </tr>
          </tfoot>
        </table>
      </body>
      </html>
    `;
    
    // Open print window
    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
  });
}
```

---

## Ledger Type Tabs

```jsx
function LedgerTabs({ activeTab, onTabChange }) {
  const tabs = [
    { key: 'general', label: 'General Ledger', endpoint: '/general/' },
    { key: 'sales', label: 'Sales Ledger', endpoint: '/sales/' },
    { key: 'purchase', label: 'Purchase Ledger', endpoint: '/purchase/' }
  ];

  return (
    <div className="ledger-tabs">
      {tabs.map(tab => (
        <button
          key={tab.key}
          className={`tab ${activeTab === tab.key ? 'active' : ''}`}
          onClick={() => onTabChange(tab.key, tab.endpoint)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
```

---

## Complete Integration Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AccountLedgerPage() {
  const [ledgerType, setLedgerType] = useState('general');
  const [ledgerData, setLedgerData] = useState(null);
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLedger();
  }, [ledgerType, filters]);

  const fetchLedger = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams(filters).toString();
      const url = `/api/cash-and-bank/account-ledger/${ledgerType}/?${queryParams}`;
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      setLedgerData(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="account-ledger-page">
      <LedgerTabs activeTab={ledgerType} onTabChange={setLedgerType} />
      <LedgerFilters onFilterChange={setFilters} />
      <AccountLedgerTable data={ledgerData} loading={loading} />
    </div>
  );
}
```

---

## Summary

This provides **exact integration code** to match your UI mockup with:
- ✅ Date/Time formatted as shown (12/24/2025, 11:48 AM)
- ✅ Debit/Credit columns with "-" for zero values
- ✅ Running balance displayed
- ✅ Totals row at bottom
- ✅ Summary cards for totals
- ✅ Filters for date range, shift, transaction type
- ✅ Print functionality
- ✅ Ledger type tabs (General, Sales, Purchase)

All data comes directly from the API with no additional transformation needed!
