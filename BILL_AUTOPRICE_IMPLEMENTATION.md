# Bill Purchase Item Auto-Price Implementation

## Changes Made

### 1. **PurchaseItem Model** (`apps/sales/models/bills.py`)
- Made `price` field optional (`null=True, blank=True`)
- Added `save()` method to auto-populate price from inventory:
  - Uses `retail_pricing` if available
  - Falls back to base `price` if retail_pricing is not set
  - Defaults to 0 if no price is found

```python
def save(self, *args, **kwargs):
    """Auto-populate price from inventory if not provided"""
    if not self.price and self.inventory:
        # Use retail_pricing if available, otherwise use base price
        self.price = self.inventory.retail_pricing or self.inventory.price or 0
    super().save(*args, **kwargs)
```

### 2. **Django Admin Interface** (`apps/sales/admin.py`)

#### A. Custom Form (`PurchaseItemForm`)
- Makes price field optional
- Adds help text: "Auto-populated from inventory. Leave blank to auto-fill."
- Cleans the form to auto-populate price from inventory if not provided

#### B. PurchaseItemInline
- Uses `PurchaseItemForm`
- Shows 3 fields: inventory, quantity, price
- Price auto-fills when item is saved

#### C. BillAdmin
- Added `save_formset()` method
- Ensures prices are auto-populated for all purchase items before saving
- Falls back to model-level auto-population as secondary mechanism

**Result: When user selects inventory and leaves price blank, it auto-populates from inventory retail_pricing**

### 3. **PurchaseItemSerializer** (`apps/sales/serializers/bill.py`)
- Made price field optional (`required=False, allow_null=True`)
- API will also auto-populate via model save() method

### 4. **Inventory API Endpoint** (`apps/stock_management/views/inventory.py`)
- Added `pricing` action to fetch inventory pricing:
  - Endpoint: `GET /api/stock-management/inventory/{id}/pricing/`
  - Returns all pricing tiers (price, mrp, retail_pricing, wholesale_price, distributor_price)
  - Can be used by frontend if needed

---

## How It Works

### In Django Admin:
1. User creates a Bill
2. User adds Purchase Items in the inline table
3. User selects inventory item
4. User enters quantity
5. **Price field is left blank OR auto-fills from inventory**
6. On save:
   - `PurchaseItemForm.clean()` auto-populates price
   - `BillAdmin.save_formset()` ensures price is set
   - `PurchaseItem.save()` final check and auto-population
7. Bill is saved with all items having prices

### In API:
1. Create bill with purchase_items_data
2. If price is not provided, model will auto-populate from inventory
3. Bill subtotal automatically calculates from all items

---

## Price Priority (Auto-Population Order)
1. ✅ Use provided price (if user enters one)
2. ✅ Use inventory `retail_pricing` 
3. ✅ Use inventory base `price`
4. ✅ Default to 0

---

## Database Migration Required
Since we changed the `price` field from required to optional:

```bash
python manage.py makemigrations sales
python manage.py migrate
```

---

## Testing

### Admin Panel Test:
1. Go to Bills admin
2. Create a new bill
3. Add purchase items inline
4. Select an inventory item (with pricing set)
5. Leave price blank
6. Click Save
7. ✅ Price should be auto-filled from inventory retail_pricing

### API Test:
```bash
POST /api/sales/bills/
{
    "customer_name": "John Doe",
    "customer_type": "retail",
    "payment_method": "cash",
    "status": "draft",
    "purchase_items_data": [
        {
            "inventory_id": 1,
            "quantity": "5.00"
            // Price left blank - will auto-populate
        }
    ]
}
```

---

## Summary Table

| Feature | Before | After |
|---------|--------|-------|
| Price required in admin | ❌ Yes | ✅ Optional |
| Auto-populate from inventory | ❌ No | ✅ Yes |
| Manual price override | ✅ Yes | ✅ Yes |
| JavaScript needed | ❌ Yes | ✅ No (Django native) |
| Works in admin | ✅ Partial | ✅ Full |
| Works in API | ❌ No | ✅ Yes |
