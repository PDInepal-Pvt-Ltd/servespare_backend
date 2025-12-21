# Cart Checkout - Inventory Reduction

## Overview
When customers checkout from their cart, the system now automatically reduces inventory quantities for ordered items.

## Implementation Details

### Updated File
- **[apps/carts/views/cart_views.py](apps/carts/views/cart_views.py)** - `CartViewSet.checkout()` method

### Changes Made
1. **Immediate Inventory Deduction**: When creating a sales order from cart items, the system now calls `order_item.deduct_inventory()` immediately after creating each `SalesOrderItem`.

2. **Stock Validation**: The checkout process validates stock availability before creating the order.

3. **Transaction Safety**: All operations happen within a database transaction, ensuring data consistency.

## Workflow

### 1. Add Items to Cart
```http
POST /carts/cart/add/
Content-Type: application/json

{
  "inventory_id": 1,
  "quantity": 2.00
}
```

### 2. View Cart
```http
GET /carts/cart/
```

Response includes:
- Cart items with details
- Total items count
- Subtotal amount

### 3. Checkout
```http
POST /carts/cart/checkout/
Content-Type: application/json

{
  "payment_method": "cash",
  "delivery_address": "123 Main St",
  "delivery_city": "Mumbai",
  "delivery_state": "Maharashtra",
  "delivery_pincode": "400001",
  "notes": "Please deliver before 5 PM"
}
```

#### What Happens:
1. ✅ Validates cart is not empty
2. ✅ Checks stock availability for all items
3. ✅ Creates a new `SalesOrder`
4. ✅ Creates `SalesOrderItem` for each cart item
5. ✅ **Deducts inventory quantity immediately**
6. ✅ Calculates order totals (subtotal, tax, discount, total)
7. ✅ Removes checked-out items from cart
8. ✅ Returns order details with order number

### 4. Inventory Tracking
Each `SalesOrderItem` has an `inventory_deducted` flag:
- `False` initially (or when restored)
- `True` after `deduct_inventory()` is called
- Prevents double-deduction
- Used for inventory restoration on order cancellation

## User Access Control

### Cart Access
- ✅ Users can only view and manage **their own cart**
- ✅ `CartViewSet.list()` returns only `request.user`'s cart
- ✅ All cart operations are scoped to the authenticated user

### Favorites Access
- ✅ Users can only view **their own favorites**
- ✅ `FavoriteViewSet.list()` filters by `user=request.user`
- ✅ All favorite operations are scoped to the authenticated user

### Authentication
- Both `CartViewSet` and `FavoriteViewSet` require `IsAuthenticated` permission
- Unauthenticated users cannot access any cart or favorites endpoints

## Order Lifecycle

### Order Status Flow
```
confirmed → ready_to_pack → packed → ready_to_depart → in_transit → delivered
           ↓
        cancelled (inventory restored)
```

### Inventory Management
- **At Checkout**: Inventory is deducted immediately
- **On Delivery**: No additional deduction (already done at checkout)
- **On Cancellation**: Inventory is restored via `restore_inventory()`

## Example Test

Run the test script to verify:
```bash
python test_checkout_inventory.py
```

This demonstrates:
1. Creating a cart with items
2. Processing checkout
3. Verifying inventory reduction
4. Rolling back for clean testing

## Error Handling

### Insufficient Stock
```json
{
  "error": "Insufficient stock for Air Filter High Flow",
  "item": "Air Filter High Flow",
  "required": 10.0,
  "available": 5.0
}
```

### Empty Cart
```json
{
  "error": "Cart is empty. Add items before checkout."
}
```

### Transaction Failure
All operations are wrapped in `transaction.atomic()`, so any failure rolls back all changes including:
- Order creation
- Inventory deduction
- Cart item deletion

## Key Files

- **Models**: [apps/carts/models/cart_model.py](apps/carts/models/cart_model.py)
- **Views**: [apps/carts/views/cart_views.py](apps/carts/views/cart_views.py)
- **Serializers**: [apps/carts/serializers/cart_serializers.py](apps/carts/serializers/cart_serializers.py)
- **Sales Order**: [apps/sales/models/sales_order.py](apps/sales/models/sales_order.py)

## Notes

- The `deduct_inventory()` method checks the `inventory_deducted` flag to prevent double-deduction
- The `restore_inventory()` method only restores if `inventory_deducted` is `True`
- All monetary calculations use `Decimal` for precision
- Order numbers are auto-generated with format: `SO-YYYYMMDD-XXXXXX`
