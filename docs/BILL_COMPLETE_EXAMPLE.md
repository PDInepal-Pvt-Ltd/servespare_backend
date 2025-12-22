# Bill System - Complete Example

This document shows a complete end-to-end example of how the Bill System works with inventory reduction.

## Scenario

A customer (Ram Kumar) walks into your shop and wants to purchase:
- 2.5 units of Brake Pad Set
- 5 units of Engine Oil 5L

---

## Step 1: Create a Bill

**HTTP Request:**
```bash
POST /api/bills/
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "customer_name": "Ram Kumar",
  "customer_type": "retail",
  "address": "Shop #5, Main Bazaar, Delhi",
  "phone_numbers": "9876543210,9123456789",
  "pan_vat_number": "ABCDE1234F",
  "payment_method": "cash",
  "status": "draft"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "tenant": 1,
  "branch": 1,
  "customer_name": "Ram Kumar",
  "address": "Shop #5, Main Bazaar, Delhi",
  "phone_numbers": "9876543210,9123456789",
  "pan_vat_number": "ABCDE1234F",
  "customer_type": "retail",
  "customer_type_display": "Retail",
  "price": null,
  "discount_method": null,
  "discount_value": "0.00",
  "discount_amount": "0.00",
  "total_after_discount": "0.00",
  "payment_method": "cash",
  "payment_method_display": "Cash",
  "status": "draft",
  "status_display": "Draft",
  "purchase_items": [],
  "is_active": true,
  "created": "2025-12-22T10:30:00Z",
  "modified": "2025-12-22T10:30:00Z"
}
```

**Bill ID: 1** ✅

---

## Step 2: Check Available Inventory

First, let's see what inventory items are available:

**HTTP Request:**
```bash
GET /api/inventory/?search=brake
```

**Response (relevant items):**
```json
{
  "count": 2,
  "results": [
    {
      "id": 5,
      "item_name": "Brake Pad Set",
      "quantity": "100.00",
      "price": "500.00",
      "vehicle_type": "two_wheeler",
      "category": "original"
    },
    {
      "id": 12,
      "item_name": "Engine Oil 5L",
      "quantity": "50.00",
      "price": "200.00",
      "vehicle_type": "two_wheeler",
      "category": "local"
    }
  ]
}
```

---

## Step 3: Add First Product (Brake Pad)

**HTTP Request:**
```bash
POST /api/bills/1/add_purchase_item/
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "inventory": 5,
  "quantity": 2.50,
  "price": 500.00
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "bill": 1,
  "inventory": 5,
  "product_name": "Brake Pad Set",
  "quantity": "2.50",
  "price": "500.00",
  "total_price": "1250.00",
  "created": "2025-12-22T10:31:00Z",
  "modified": "2025-12-22T10:31:00Z"
}
```

✅ **Added 2.5 units of Brake Pad at ₹500 each = ₹1,250**

---

## Step 4: Add Second Product (Engine Oil)

**HTTP Request:**
```bash
POST /api/bills/1/add_purchase_item/
Content-Type: application/json
Authorization: Bearer <your_token>

{
  "inventory": 12,
  "quantity": 5.00,
  "price": 200.00
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "bill": 1,
  "inventory": 12,
  "product_name": "Engine Oil 5L",
  "quantity": "5.00",
  "price": "200.00",
  "total_price": "1000.00",
  "created": "2025-12-22T10:32:00Z",
  "modified": "2025-12-22T10:32:00Z"
}
```

✅ **Added 5 units of Engine Oil at ₹200 each = ₹1,000**

---

## Step 5: View Complete Bill

**HTTP Request:**
```bash
GET /api/bills/1/
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "id": 1,
  "tenant": 1,
  "branch": 1,
  "customer_name": "Ram Kumar",
  "address": "Shop #5, Main Bazaar, Delhi",
  "phone_numbers": "9876543210,9123456789",
  "pan_vat_number": "ABCDE1234F",
  "customer_type": "retail",
  "customer_type_display": "Retail",
  "price": null,
  "discount_method": null,
  "discount_value": "0.00",
  "discount_amount": "0.00",
  "total_after_discount": "0.00",
  "payment_method": "cash",
  "payment_method_display": "Cash",
  "status": "draft",
  "status_display": "Draft",
  "purchase_items": [
    {
      "id": 1,
      "bill": 1,
      "inventory": 5,
      "product_name": "Brake Pad Set",
      "quantity": "2.50",
      "price": "500.00",
      "total_price": "1250.00",
      "created": "2025-12-22T10:31:00Z",
      "modified": "2025-12-22T10:31:00Z"
    },
    {
      "id": 2,
      "bill": 1,
      "inventory": 12,
      "product_name": "Engine Oil 5L",
      "quantity": "5.00",
      "price": "200.00",
      "total_price": "1000.00",
      "created": "2025-12-22T10:32:00Z",
      "modified": "2025-12-22T10:32:00Z"
    }
  ],
  "is_active": true,
  "created": "2025-12-22T10:30:00Z",
  "modified": "2025-12-22T10:32:00Z"
}
```

**Bill Summary:**
- Brake Pad: 2.50 × ₹500 = ₹1,250
- Engine Oil: 5.00 × ₹200 = ₹1,000
- **Total: ₹2,250** ✅

---

## Step 6: Check Inventory Before Payment

**HTTP Request:**
```bash
GET /api/inventory/5/
```

**Response:**
```json
{
  "id": 5,
  "item_name": "Brake Pad Set",
  "quantity": "100.00",
  "price": "500.00",
  "vehicle_type": "two_wheeler",
  "category": "original"
}
```

**Inventory BEFORE payment: Brake Pad = 100 units** ⚠️

---

## Step 7: Mark Bill as PAID (Inventory Gets Reduced)

**HTTP Request:**
```bash
POST /api/bills/1/mark_paid/
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "id": 1,
  "tenant": 1,
  "branch": 1,
  "customer_name": "Ram Kumar",
  "status": "paid",  // ✅ Changed from "draft" to "paid"
  "status_display": "Paid",
  ...
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

**Status changed to PAID** ✅

---

## Step 8: Check Inventory After Payment

**HTTP Request:**
```bash
GET /api/inventory/5/
```

**Response:**
```json
{
  "id": 5,
  "item_name": "Brake Pad Set",
  "quantity": "97.50",  // ✅ REDUCED from 100 to 97.50
  "price": "500.00",
  "vehicle_type": "two_wheeler",
  "category": "original"
}
```

**Inventory AFTER payment: Brake Pad = 97.50 units** ✅

**HTTP Request:**
```bash
GET /api/inventory/12/
```

**Response:**
```json
{
  "id": 12,
  "item_name": "Engine Oil 5L",
  "quantity": "45.00",  // ✅ REDUCED from 50 to 45
  "price": "200.00",
  "vehicle_type": "two_wheeler",
  "category": "local"
}
```

**Inventory AFTER payment: Engine Oil = 45 units** ✅

---

## Summary

### What Happened:

1. ✅ **Bill Created** - Draft bill for Ram Kumar
2. ✅ **Products Added** - Selected 2 items from inventory
3. ✅ **Bill Finalized** - Total ₹2,250 ready to pay
4. ✅ **Payment Processed** - Marked bill as PAID
5. ✅ **Inventory Reduced** - Automatic reduction on payment:
   - Brake Pad: 100 → 97.50 (sold 2.50)
   - Engine Oil: 50 → 45 (sold 5)

### Key Points:

- ✅ No manual inventory reduction needed
- ✅ Inventory automatically decreased when bill was marked PAID
- ✅ Products linked via Inventory ForeignKey (secure)
- ✅ Decimal quantities supported (2.50 units)
- ✅ All timestamps tracked

---

## Database State

### Bills Table
```
id  | customer_name | status | payment_method
1   | Ram Kumar     | paid   | cash
```

### Purchase Items Table
```
id  | bill_id | inventory_id | quantity | price
1   | 1       | 5            | 2.50     | 500.00
2   | 1       | 12           | 5.00     | 200.00
```

### Inventory Table (After Payment)
```
id  | item_name          | quantity
5   | Brake Pad Set      | 97.50
12  | Engine Oil 5L      | 45.00
```

---

## Error Handling Examples

### Example 1: Invalid Inventory ID

**Request:**
```bash
POST /api/bills/1/add_purchase_item/
{
  "inventory": 999,  // Does not exist
  "quantity": 1.00,
  "price": 100.00
}
```

**Response (400 Bad Request):**
```json
{
  "inventory": ["Invalid pk \"999\" - object does not exist."]
}
```

### Example 2: Missing Required Field

**Request:**
```bash
POST /api/bills/1/add_purchase_item/
{
  "inventory": 5,
  // Missing quantity
  "price": 100.00
}
```

**Response (400 Bad Request):**
```json
{
  "quantity": ["This field is required."]
}
```

### Example 3: Invalid Quantity (Zero or Negative)

**Request:**
```bash
POST /api/bills/1/add_purchase_item/
{
  "inventory": 5,
  "quantity": 0,  // Zero not allowed
  "price": 100.00
}
```

The system doesn't validate this at serializer level, but it will create an item with 0 quantity which won't affect inventory reduction (only items with quantity > 0 reduce inventory).

---

## Next Steps for Integration

### Frontend Implementation:

1. **Step 1: Inventory Dropdown**
   ```
   Show dropdown/search of all inventory items
   On select → Show item details (name, current price, available quantity)
   ```

2. **Step 2: Quantity Input**
   ```
   Accept decimal quantity (2.5, 3.25, etc.)
   Show warning if quantity > available inventory
   ```

3. **Step 3: Price Field**
   ```
   Auto-fill with current inventory price
   Allow override (for discounts/special prices)
   ```

4. **Step 4: Bill Preview**
   ```
   Show all items added
   Show total quantity and total price
   Display bill summary
   ```

5. **Step 5: Payment**
   ```
   Click "Mark as Paid"
   Show confirmation
   Inventory reduces automatically
   Print receipt
   ```

---

## Testing

### Manual Testing Steps:

```bash
# 1. Create bill
POST /api/bills/
# Check response has id

# 2. Add products
POST /api/bills/{id}/add_purchase_item/
# Repeat for multiple items

# 3. View bill
GET /api/bills/{id}/
# Verify all items are there

# 4. Check inventory before
GET /api/inventory/{id}/
# Note the quantity

# 5. Mark paid
POST /api/bills/{id}/mark_paid/
# Verify status changed

# 6. Check inventory after
GET /api/inventory/{id}/
# Verify quantity decreased
```

### Automated Testing:

```python
from apps.sales.models import Bill, PurchaseItem
from apps.stock_management.models import Inventory

# Get inventory
inv = Inventory.objects.get(id=5)
initial_qty = inv.quantity

# Create bill
bill = Bill.objects.create(
    customer_name="Test",
    customer_type="retail",
    payment_method="cash"
)

# Add item
item = PurchaseItem.objects.create(
    bill=bill,
    inventory=inv,
    quantity=2.50,
    price=500.00
)

# Mark paid
bill.status = 'paid'
bill.save()
bill.decrease_inventory()

# Check
inv.refresh_from_db()
assert inv.quantity == initial_qty - 2.50, "Inventory not reduced!"
print("✅ Test passed!")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Product doesn't show when adding item | Use correct inventory ID, verify inventory exists |
| Inventory not decreasing | Call `mark_paid()` endpoint, not just update status |
| Negative inventory | System prevents it (minimum = 0) |
| Duplicate products in bill | Allowed by design; can add same product multiple times |
| Can't find bill by customer name | Use exact name or search by phone/PAN |

---

## Related Documentation

- 📖 [Bill System Guide](./BILL_SYSTEM_GUIDE.md) - Complete API reference
- 📖 [Implementation Summary](../BILL_IMPLEMENTATION_SUMMARY.md) - Technical changes
- 📖 [Inventory Documentation](./API_STOCK_MANAGEMENT.md) - Inventory API details

