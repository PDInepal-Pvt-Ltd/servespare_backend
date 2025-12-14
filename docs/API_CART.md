# Cart API Documentation

## Overview
The Cart API allows customers to manage their shopping cart by adding items, updating quantities, removing items, and viewing their cart.

## Base URL
```
/api/carts/
```

## Authentication
All endpoints require authentication using JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. View Cart
Get the current user's cart with all items.

**Endpoint:** `GET /api/carts/cart/`

**Response:**
```json
{
  "id": 1,
  "user": 5,
  "items": [
    {
      "id": 1,
      "inventory": {
        "id": 10,
        "item_name": "Brake Pad",
        "category": "original",
        "category_display": "Original",
        "vehicle_type": "four_wheeler",
        "vehicle_type_display": "Four Wheeler",
        "part_number": "BP-12345",
        "quantity": "50.00",
        "retail_pricing": "1500.00",
        "mrp": "1800.00",
        "warranty_period": "6_month",
        "warranty_display": "6 Month",
        "primary_image": "http://example.com/media/inventory_images/brake_pad.jpg",
        "barcode": "123456789"
      },
      "quantity": "2.00",
      "price": "1500.00",
      "total_price": "3000.00",
      "created": "2025-12-14T10:30:00Z",
      "modified": "2025-12-14T10:30:00Z"
    }
  ],
  "total_items": 2,
  "subtotal": "3000.00",
  "created": "2025-12-14T10:00:00Z",
  "modified": "2025-12-14T10:30:00Z"
}
```

---

### 2. Add Item to Cart
Add a new item to the cart or update quantity if the item already exists.

**Endpoint:** `POST /api/carts/cart/add/`

**Request Body:**
```json
{
  "inventory_id": 10,
  "quantity": 2.00
}
```

**Response (Success):**
```json
{
  "message": "Item added to cart successfully",
  "cart": {
    "id": 1,
    "user": 5,
    "items": [...],
    "total_items": 2,
    "subtotal": "3000.00",
    "created": "2025-12-14T10:00:00Z",
    "modified": "2025-12-14T10:30:00Z"
  }
}
```

**Response (Insufficient Stock):**
```json
{
  "error": "Insufficient stock",
  "available_quantity": 1.0
}
```

**Response (Item Already Exists - Quantity Updated):**
```json
{
  "message": "Item quantity updated in cart",
  "cart": {...}
}
```

---

### 3. Update Cart Item Quantity
Update the quantity of a specific item in the cart.

**Endpoint:** `PATCH /api/carts/cart/{item_id}/update/`

**Request Body:**
```json
{
  "quantity": 5.00
}
```

**Response:**
```json
{
  "message": "Cart item updated successfully",
  "cart": {
    "id": 1,
    "user": 5,
    "items": [...],
    "total_items": 5,
    "subtotal": "7500.00",
    "created": "2025-12-14T10:00:00Z",
    "modified": "2025-12-14T11:00:00Z"
  }
}
```

---

### 4. Remove Item from Cart
Remove a specific item from the cart (permanent delete).

**Endpoint:** `DELETE /api/carts/cart/{item_id}/remove/`

**Response:**
```json
{
  "message": "Item removed from cart",
  "cart": {
    "id": 1,
    "user": 5,
    "items": [],
    "total_items": 0,
    "subtotal": "0.00",
    "created": "2025-12-14T10:00:00Z",
    "modified": "2025-12-14T11:15:00Z"
  }
}
```

---

### 5. Clear Cart
Remove all items from the cart at once (permanent delete all items).

**Endpoint:** `POST /api/carts/cart/clear/`

**Response:**
```json
{
  "message": "Cart cleared successfully",
  "cart": {
    "id": 1,
    "user": 5,
    "items": [],
    "total_items": 0,
    "subtotal": "0.00",
    "created": "2025-12-14T10:00:00Z",
    "modified": "2025-12-14T11:20:00Z"
  }
}
```

---

## Features

### Automatic Cart Creation
- Cart is automatically created for a user when they add their first item
- Each user can only have one active cart

### Stock Validation
- System checks available inventory before adding/updating items
- Prevents adding more items than available in stock
- Returns clear error messages with available quantity

### Price Locking
- Item price is locked at the time of adding to cart
- Uses retail pricing from inventory by default
- Prevents price changes from affecting existing cart items

### Soft Delete
- Items are permanently deleted from the database when removed or cart is cleared
- Maintains data integrity by preventing orphaned cart items

### Quantity Management
- Supports decimal quantities for items sold by weight or fraction
- Validates positive quantities
- Updates existing cart items when adding duplicate items

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Insufficient stock",
  "available_quantity": 5.0
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Business Logic

1. **One Cart Per User**: Each user has only one active cart at a time
2. **Auto-Merge**: Adding an existing item increases its quantity instead of creating duplicate entries
3. **Stock Validation**: All operations validate against current inventory levels
4. **Retail Pricing**: Cart uses retail_pricing field from inventory
5. **Customer Only**: Designed primarily for customer role users

---

## Usage Example (Python)

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/carts/cart/"
TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# View cart
response = requests.get(BASE_URL, headers=headers)
print(response.json())

# Add item to cart
data = {
    "inventory_id": 10,
    "quantity": 2.00
}
response = requests.post(f"{BASE_URL}add/", json=data, headers=headers)
print(response.json())

# Update cart item
data = {"quantity": 5.00}
response = requests.patch(f"{BASE_URL}1/update/", json=data, headers=headers)
print(response.json())

# Remove item
response = requests.delete(f"{BASE_URL}1/remove/", headers=headers)
print(response.json())

# Clear cart
response = requests.post(f"{BASE_URL}clear/", headers=headers)
print(response.json())
```

---

## Database Schema

### Cart Table
- `id`: Primary key
- `user_id`: Foreign key to User (OneToOne)
- `created`: Timestamp
- `modified`: Timestamp
- `is_active`: Boolean
- `is_removed`: Boolean (soft delete)

### CartItem Table
- `id`: Primary key
- `cart_id`: Foreign key to Cart
- `inventory_id`: Foreign key to Inventory
- `quantity`: Decimal (10, 2)
- `price`: Decimal (10, 2) - locked price
- `created`: Timestamp
- `modified`: Timestamp
- `is_active`: Boolean
- `is_removed`: Boolean (soft delete)
- **Unique Constraint**: (cart_id, inventory_id)

---

## Notes

- All timestamps are in ISO 8601 format with UTC timezone
- Decimal fields use 2 decimal places for precision
- Soft delete allows recovery and maintains data integrity
- Cart automatically calculates totals and item counts
- Authentication required for all endpoints
