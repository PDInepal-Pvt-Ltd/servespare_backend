# Bill System Implementation Guide

## Overview

The Bill System is designed for **offline/walk-in customers** who purchase products directly from your shop. When a bill is created and marked as paid, the inventory quantities are automatically decreased.

## Key Features

✅ **Direct Inventory Selection** - Choose products directly from inventory when creating bills  
✅ **Automatic Inventory Reduction** - Inventory quantities automatically decrease when bill is marked as paid  
✅ **Customer Tracking** - Track walk-in customers with their details  
✅ **Multiple Payment Methods** - Support for Cash, Card, Bank Transfer  
✅ **Discounts** - Apply fixed amount or percentage discounts  
✅ **Bill Status Management** - Track bill status (Draft, Pending, Paid, etc.)

---

## Data Model

### Bill Model
Represents a single bill/invoice for a customer.

**Fields:**
- `customer_name` - Name of the customer
- `customer_type` - Type: Retail, Retailer, Wholesaler, Distributor, Workshop
- `address` - Customer address
- `phone_numbers` - Customer contact numbers
- `pan_vat_number` - Tax ID
- `price` - Base price before discount
- `discount_method` - 'amount' or 'percentage'
- `discount_value` - Discount amount or percentage
- `payment_method` - 'cash', 'card', 'bank_transfer'
- `status` - 'draft', 'pending', 'paid', 'on_hold', 'credit_sale', 'cancelled', 'refunded'
- `branch` - Branch that issued the bill

### PurchaseItem Model
Represents individual products/items in a bill (linked to inventory).

**Fields:**
- `bill` - ForeignKey to Bill
- `inventory` - ForeignKey to Inventory (the actual product)
- `quantity` - Quantity purchased (DecimalField)
- `price` - Price at the time of purchase
- `created` - Timestamp when item was added
- `modified` - Timestamp of last modification

---

## API Endpoints

### 1. Create a Bill (Draft)

**Endpoint:** `POST /api/bills/`

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "customer_type": "retail",
  "address": "123 Main St",
  "phone_numbers": "9876543210",
  "pan_vat_number": "ABC123DEF",
  "payment_method": "cash",
  "status": "draft"
}
```

**Response:** Bill created with ID

---

### 2. Add Products to Bill

**Endpoint:** `POST /api/bills/{bill_id}/add_purchase_item/`

**Request Body:**
```json
{
  "inventory": 5,
  "quantity": 2.50,
  "price": 500.00
}
```

**Parameters:**
- `inventory` (required) - ID of the product in inventory
- `quantity` (required) - Quantity to purchase
- `price` (required) - Price per unit

**Response:**
```json
{
  "id": 1,
  "bill": 1,
  "inventory": 5,
  "product_name": "Brake Pad Set",
  "quantity": "2.50",
  "price": "500.00",
  "total_price": "1250.00",
  "created": "2025-12-22T10:30:00Z",
  "modified": "2025-12-22T10:30:00Z"
}
```

---

### 3. Mark Bill as Paid (Reduces Inventory)

**Endpoint:** `POST /api/bills/{bill_id}/mark_paid/`

**Response:** Updated bill with status='paid'

**What Happens:**
- Bill status is set to 'paid'
- For each purchase item in the bill:
  - The inventory quantity is decreased by the item quantity
  - Inventory minimum is 0 (never goes negative)

**Example:**
```
Before: Inventory Item #5 has quantity = 100
Purchase Item: quantity = 2.50

After marking paid: Inventory Item #5 quantity = 97.50
```

---

### 4. Get All Bills

**Endpoint:** `GET /api/bills/`

**Query Parameters:**
- `customer_type=retail` - Filter by customer type
- `status=paid` - Filter by status
- `payment_method=cash` - Filter by payment method
- `search=John` - Search by customer name, phone, or PAN/VAT
- `is_active=true` - Filter by active status

---

### 5. Get Bill Details

**Endpoint:** `GET /api/bills/{bill_id}/`

**Response:** Bill with all purchase items (nested)

---

### 6. Get Purchase Items for a Bill

**Endpoint:** `GET /api/bills/{bill_id}/purchase_items/`

**Response:** List of all purchase items in the bill

---

## Workflow Example

### Step 1: Create a Bill

```bash
curl -X POST http://localhost:8000/api/bills/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "customer_name": "Ram Kumar",
    "customer_type": "retail",
    "address": "Shop #5, Main Bazaar",
    "phone_numbers": "9876543210",
    "payment_method": "cash",
    "status": "draft"
  }'
```

**Response:**
```json
{
  "id": 1,
  "customer_name": "Ram Kumar",
  "status": "draft",
  ...
}
```

### Step 2: Add Products to Bill

```bash
# Add Brake Pad (Inventory ID: 5)
curl -X POST http://localhost:8000/api/bills/1/add_purchase_item/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "inventory": 5,
    "quantity": 2.50,
    "price": 500.00
  }'

# Add Engine Oil (Inventory ID: 12)
curl -X POST http://localhost:8000/api/bills/1/add_purchase_item/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "inventory": 12,
    "quantity": 5.00,
    "price": 200.00
  }'
```

### Step 3: View Bill with Items

```bash
curl -X GET http://localhost:8000/api/bills/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "customer_name": "Ram Kumar",
  "status": "draft",
  "price": null,
  "discount_method": null,
  "discount_value": 0,
  "payment_method": "cash",
  "purchase_items": [
    {
      "id": 1,
      "inventory": 5,
      "product_name": "Brake Pad Set",
      "quantity": "2.50",
      "price": "500.00",
      "total_price": "1250.00"
    },
    {
      "id": 2,
      "inventory": 12,
      "product_name": "Engine Oil 5L",
      "quantity": "5.00",
      "price": "200.00",
      "total_price": "1000.00"
    }
  ]
}
```

### Step 4: Mark Bill as Paid (Reduce Inventory)

```bash
curl -X POST http://localhost:8000/api/bills/1/mark_paid/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**What Happens Behind the Scenes:**
- Bill #1 status → 'paid'
- Inventory #5 (Brake Pad): 100 → 97.50
- Inventory #12 (Engine Oil): 50 → 45.00

---

## Database Migration

Run the following command to apply the changes:

```bash
python manage.py migrate sales
```

This will:
1. Add the `inventory` ForeignKey to PurchaseItem
2. Remove the old `product_name` field
3. Add timestamp fields (`created`, `modified`)
4. Update the table structure and indexes

---

## Important Notes

⚠️ **Inventory Validation**
- When adding a purchase item, ensure the inventory ID exists
- The system doesn't validate available stock before adding (implement this if needed)
- Inventory can go to 0 but never below (automatic floor)

⚠️ **Bill Modifications**
- Only mark bills as paid once - inventory reduction happens immediately
- Cancelled bills should not reduce inventory (add logic if needed)

⚠️ **Data Integrity**
- Product name is now read-only (retrieved from inventory)
- Always use the inventory ID to link products
- No duplicate checks on purchase items yet (same product can be added multiple times)

---

## Configuration

No additional configuration required. The system uses:
- Django ORM for database operations
- DRF serializers for API responses
- TenantManager for multi-tenant support

---

## Testing

```python
# Create a test bill
bill = Bill.objects.create(
    customer_name="Test Customer",
    customer_type="retail",
    payment_method="cash"
)

# Create a purchase item
item = PurchaseItem.objects.create(
    bill=bill,
    inventory_id=5,
    quantity=2.50,
    price=500.00
)

# Mark as paid (decreases inventory)
bill.mark_paid()
bill.decrease_inventory()
```

---

## Future Enhancements

- [ ] Add stock validation before adding items to bill
- [ ] Add bill cancellation logic to reverse inventory changes
- [ ] Add bill printing/PDF generation
- [ ] Add customer history and repeat customer features
- [ ] Add barcode scanning support
- [ ] Add GST/Tax calculation
- [ ] Add payment receipts
