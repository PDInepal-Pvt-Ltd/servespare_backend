# Sales Invoice & Payment Status Management

## Overview

This implementation adds a comprehensive invoice generation and payment status synchronization system to the ServeIQ backend. The system automatically generates invoices during checkout and maintains bidirectional payment status synchronization across Sales Orders, Invoices, and Bills.

## Features

### 1. Invoice Generation
- **Automatic Invoice Creation**: Invoices are automatically generated during the checkout process
- **Unique Invoice Numbers**: Each invoice has a unique ID in format `INV-YYYYMMDD-XXXXXX`
- **Complete Item Details**: Invoices include detailed line items with quantity, pricing, taxes, and discounts
- **From Sales Orders**: Invoices can also be manually generated from existing sales orders

### 2. Payment Status Management
The system supports the following payment statuses:
- **Paid**: Invoice is fully paid
- **Pending**: Payment is awaited
- **On Hold**: Payment is temporarily suspended
- **Credit Sale**: Sale on credit/deferred payment
- **Cancelled**: Invoice has been cancelled
- **Refunded**: Invoice has been refunded

### 3. Bidirectional Payment Status Synchronization
Payment status changes are automatically synchronized across three models:
- **Invoice** ↔ **SalesOrder** ↔ **Bill**

When you update the payment status in any one of these:
- The change automatically propagates to the related models
- Prevents infinite loops using `skip_signal` flags
- Ensures data consistency across the system

## Models

### Invoice Model

```python
class Invoice(BaseModel):
    # Invoice Information
    invoice_number: CharField (unique, auto-generated)
    invoice_date: DateTimeField (auto_now_add)
    due_date: DateField (optional)
    
    # References
    sales_order: OneToOneField (optional)
    bill: OneToOneField (optional)
    customer: ForeignKey (User)
    branch: ForeignKey (Branch, optional)
    tenant: ForeignKey (Tenant)
    
    # Financial Information
    subtotal: DecimalField
    discount_percentage: DecimalField (0-100)
    discount_amount: DecimalField
    tax_percentage: DecimalField (0-100)
    tax_amount: DecimalField
    shipping_charges: DecimalField
    total_amount: DecimalField
    
    # Payment Information
    payment_status: CharField (choices: paid, pending, on_hold, credit_sale, cancelled, refunded)
    payment_method: CharField (choices: cash, card, upi, bank_transfer, credit)
    paid_amount: DecimalField
    
    # Additional
    notes: TextField (optional)
    created_by: ForeignKey (User)
```

### InvoiceItem Model

```python
class InvoiceItem(BaseModel):
    # References
    invoice: ForeignKey (Invoice)
    inventory: ForeignKey (Inventory)
    tenant: ForeignKey (Tenant)
    
    # Item Details
    item_name: CharField (snapshot from inventory)
    part_number: CharField (snapshot)
    quantity: DecimalField
    unit_price: DecimalField
    
    # Pricing
    discount_percentage: DecimalField (0-100)
    discount_amount: DecimalField
    tax_percentage: DecimalField (0-100)
    tax_amount: DecimalField
    line_total: DecimalField
    
    # Additional
    notes: TextField (optional)
```

## API Endpoints

### List Invoices
```
GET /api/sales/invoices/
```
**Filters**: customer, payment_status, payment_method, branch, sales_order  
**Search**: invoice_number, customer__username, customer__email  
**Ordering**: created, invoice_date, total_amount, invoice_number

### Retrieve Invoice
```
GET /api/sales/invoices/{id}/
```

### Create Invoice
```
POST /api/sales/invoices/
```

**Body**:
```json
{
    "customer": 1,
    "branch": 1,
    "subtotal": 1000.00,
    "discount_percentage": 5,
    "discount_amount": 50,
    "tax_percentage": 10,
    "tax_amount": 95,
    "shipping_charges": 50,
    "total_amount": 1145,
    "payment_status": "pending",
    "payment_method": "cash",
    "due_date": "2025-12-31",
    "notes": "Special order"
}
```

### Generate Invoice from Sales Order
```
POST /api/sales/invoices/generate-from-order/
```

**Body**:
```json
{
    "sales_order_id": 1
}
```

**Response**:
```json
{
    "message": "Invoice generated successfully",
    "invoice": {
        "id": 1,
        "invoice_number": "INV-20251221-ABC123",
        "invoice_date": "2025-12-21T10:30:00Z",
        "customer": 1,
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "sales_order_number": "SO-20251221-XYZ789",
        "total_amount": "1145.00",
        "paid_amount": "0.00",
        "balance_amount": "1145.00",
        "payment_status": "pending",
        "items": [...]
    }
}
```

### Update Payment Status
```
PATCH /api/sales/invoices/{id}/update-payment-status/
```

**Body**:
```json
{
    "payment_status": "paid",
    "paid_amount": 1145.00,
    "payment_method": "card"
}
```

**Example Statuses**:
- `"paid"` - Mark invoice as fully paid
- `"pending"` - Payment awaited
- `"on_hold"` - Payment on hold
- `"credit_sale"` - Credit sale
- `"cancelled"` - Cancel invoice
- `"refunded"` - Mark as refunded

### Add Payment
```
POST /api/sales/invoices/{id}/add-payment/
```

**Body**:
```json
{
    "amount": 500.00,
    "payment_method": "card"
}
```

**Response**: Returns updated invoice with new payment status

### Cancel Invoice
```
POST /api/sales/invoices/{id}/cancel/
```

### Update Invoice
```
PATCH /api/sales/invoices/{id}/
```

### Delete Invoice
```
DELETE /api/sales/invoices/{id}/
```

## Checkout Process (Updated)

During checkout, the system now:

1. **Creates SalesOrder** from cart items
2. **Generates Invoice** from the SalesOrder
3. **Deducts Inventory** from stock
4. **Clears Cart** items

**Response** now includes:
```json
{
    "message": "Order placed successfully!",
    "order": {...},
    "order_number": "SO-20251221-ABC123",
    "invoice_number": "INV-20251221-XYZ789",
    "items_count": 0
}
```

## Bidirectional Synchronization

### Signal Connections

The system uses Django signals to maintain synchronization:

1. **Invoice → SalesOrder**
   - When invoice payment_status changes, SalesOrder is updated
   - Mapping: paid→paid, pending/on_hold/credit_sale/cancelled/refunded→pending

2. **Invoice → Bill**
   - When invoice payment_status changes, Bill is updated
   - Mapping: paid→paid, cancelled/refunded→draft, others→pending

3. **SalesOrder → Invoice**
   - When SalesOrder payment_status changes, Invoice is updated
   - Mapping: paid→paid, partial→pending, others mapped directly

4. **Bill → Invoice**
   - When Bill status changes, Invoice payment_status is updated
   - Automatic synchronization ensures consistency

### Preventing Circular Updates

Each signal includes a `skip_signal=True` parameter to prevent infinite loops:

```python
# This prevents the signal from firing again
instance.save(update_fields=['payment_status', 'modified'], skip_signal=True)
```

## Payment Status Model Updates

### SalesOrder
**Previous statuses**:
- pending, partial, paid

**New statuses** (added):
- on_hold, credit_sale, cancelled, refunded

### Bill
**Previous statuses**:
- draft, pending, paid

**New statuses** (added):
- on_hold, credit_sale, cancelled, refunded

## Usage Examples

### Example 1: Checkout and Generate Invoice
```bash
# User completes checkout
POST /api/carts/cart/checkout/
{
    "payment_method": "card",
    "delivery_address": "123 Main St",
    "delivery_city": "New York"
}

# Response includes both order and invoice
{
    "message": "Order placed successfully!",
    "order_number": "SO-20251221-ABC123",
    "invoice_number": "INV-20251221-XYZ789"
}
```

### Example 2: Update Invoice Payment Status
```bash
# Mark invoice as paid
PATCH /api/sales/invoices/1/update-payment-status/
{
    "payment_status": "paid",
    "paid_amount": 1145.00,
    "payment_method": "card"
}

# This automatically updates:
# - Invoice: payment_status = "paid"
# - SalesOrder: payment_status = "paid"
# - Bill (if linked): status = "paid"
```

### Example 3: Add Partial Payment
```bash
# Customer makes partial payment
POST /api/sales/invoices/1/add-payment/
{
    "amount": 500.00,
    "payment_method": "card"
}

# Invoice is updated:
# - paid_amount = 500.00
# - payment_status = "pending" (still owed)
# - balance_amount = 645.00
```

### Example 4: Generate Invoice from Existing Order
```bash
# Generate invoice for an existing sales order
POST /api/sales/invoices/generate-from-order/
{
    "sales_order_id": 5
}

# Response
{
    "message": "Invoice generated successfully",
    "invoice": {...}
}
```

## Database Schema

### invoice table
```sql
-- Main invoice records
- id (pk)
- invoice_number (unique)
- invoice_date
- due_date
- sales_order_id (fk, unique)
- bill_id (fk, unique)
- customer_id (fk)
- branch_id (fk)
- tenant_id (fk)
- subtotal
- discount_percentage
- discount_amount
- tax_percentage
- tax_amount
- shipping_charges
- total_amount
- payment_status (indexed)
- payment_method
- paid_amount
- notes
- created_by_id (fk)
- created
- modified
- is_active
- is_removed
```

### invoice_item table
```sql
-- Invoice line items
- id (pk)
- invoice_id (fk, indexed)
- inventory_id (fk, indexed)
- tenant_id (fk)
- item_name
- part_number
- quantity
- unit_price
- discount_percentage
- discount_amount
- tax_percentage
- tax_amount
- line_total
- notes
- created
- modified
- is_active
- is_removed
```

## Admin Interface

The Invoice and InvoiceItem models are registered in Django Admin for easy management:

```python
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'total_amount', 'payment_status', 'invoice_date']
    list_filter = ['payment_status', 'payment_method', 'invoice_date', 'tenant']
    search_fields = ['invoice_number', 'customer__username']
    readonly_fields = ['invoice_number', 'invoice_date', 'subtotal', 'total_amount']
```

## Implementation Details

### Automatic Invoice Generation
When a customer checks out:

```python
# In checkout view
order = SalesOrder.objects.create(...)
invoice = order.generate_invoice()  # New method
```

### Syncing Payment Status
Any of these trigger automatic synchronization:

```python
# Update invoice
invoice.update_payment_status('paid')  # Syncs to SalesOrder and Bill

# Add payment to invoice
invoice.add_payment(500.00, 'card')  # Syncs if payment_status changes

# Update sales order
sales_order.update_payment_status('paid')  # Syncs to Invoice

# Add payment to sales order
sales_order.add_payment(500.00, 'card')  # Syncs if payment_status changes
```

## Permissions

- **Super Admin/Tenant Admin/Branch Manager**: Full CRUD access to all invoices
- **Customers**: Can only view their own invoices

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK`: Successful operation
- `201 CREATED`: Invoice successfully created
- `400 BAD REQUEST`: Invalid input data
- `403 FORBIDDEN`: Permission denied
- `404 NOT FOUND`: Resource not found
- `501 NOT IMPLEMENTED`: Feature not yet implemented (PDF download)

## Future Enhancements

1. **PDF Generation**: Download invoices as PDF
2. **Email Notifications**: Send invoices via email
3. **Payment Reminders**: Automated payment reminder emails
4. **Invoice Templates**: Customizable invoice layouts
5. **Partial Payments**: Enhanced partial payment tracking
6. **Refund Management**: Detailed refund tracking and audit trail
