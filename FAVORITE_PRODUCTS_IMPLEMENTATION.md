# Favorite Products Implementation Guide

## Overview
Complete favorite products feature implementation for customers to save/favorite products with duplicate checking.

## Components Created

### 1. **Model** - `apps/carts/models/favourite_model.py`

#### Favorite Model
- **Fields:**
  - `user` (ForeignKey to User): Customer who favorited the product
  - `inventory` (ForeignKey to Inventory): Product being favorited
  - `is_active` (BooleanField): Soft-delete flag
  - `created` (AutoCreatedField): Timestamp
  - `modified` (AutoLastModifiedField): Last modified timestamp

- **Key Features:**
  - `unique_together`: Ensures each user can only have one active favorite per product
  - **Duplicate Checking**: If product already exists in favorites, returns proper message
  - **Soft Delete**: Uses `is_active` flag instead of hard deletes
  - **Indexes**: Optimized for fast queries

- **Methods:**
  - `add_to_favorites(user, inventory)`: 
    - Adds product to favorites
    - Returns duplicate message if product already favorited
    - Reactivates previously removed favorites
    - Returns: `(favorite_instance, created, message)`
  
  - `remove_from_favorites(user, inventory)`:
    - Soft-deletes favorite entry
    - Returns: `(success, message)`

---

### 2. **Serializers** - `apps/carts/serializers/favourite_serializers.py`

#### FavoriteSerializer
- Full favorite details with inventory information
- Used for create/update operations

#### FavoriteListSerializer
- Read-only serializer for listing favorites
- Includes inventory details and user info

#### AddToFavoriteSerializer
- Input validation for adding to favorites
- Validates inventory exists

#### RemoveFromFavoriteSerializer
- Input validation for removing from favorites
- Validates inventory exists

#### InventoryBasicFavoriteSerializer
- Basic product information with images
- Reusable for nested display

---

### 3. **Views** - `apps/carts/views/favourite_views.py`

#### FavoriteViewSet
Complete REST API endpoints:

**1. List Favorites**
```
GET /favorites/
```
Returns all favorited products for current user

**2. Add to Favorites**
```
POST /favorites/ 
or 
POST /favorites/add/

Body: {
  "inventory_id": <int>
}
```
- Returns 201 if newly added
- Returns 200 with message if already exists (not an error)

**3. Remove Favorite**
```
DELETE /favorites/{id}/
```
Remove favorite by favorite record ID

**4. Remove by Product ID**
```
POST /favorites/remove/

Body: {
  "inventory_id": <int>
}
```
Remove favorite by product/inventory ID

**5. Check if Favorited**
```
GET /favorites/check/?inventory_id=<int>
or
GET /favorites/check/{inventory_id}/
```
Returns: `{ "is_favorite": true/false, "inventory_id": <int> }`

**6. Count Favorites**
```
GET /favorites/count/
```
Returns: `{ "count": <int> }`

---

### 4. **Migration** - `apps/carts/migrations/0003_favorite.py`
- Creates `favorites` database table
- Adds unique constraint on (user, inventory)
- Creates 3 indexes for performance

---

## Key Features

### ✅ Duplicate Product Handling
When adding a product already in favorites:
- **Not treated as error** (returns 200 OK)
- Returns descriptive message: `"'Product Name' is already in your favorites."`
- This is better UX than error handling

### ✅ Soft Delete
- Products removed from favorites keep records (`is_active=False`)
- Can be restored by re-adding
- Provides data history

### ✅ Performance
- Unique constraint prevents duplicates at DB level
- Indexes on:
  - `(user, inventory)` - Fast lookups
  - `(user, -created)` - Fast listing
  - `(is_active)` - Fast active/inactive filtering

### ✅ User Isolation
- Each user only sees/manages their own favorites
- Permission enforced via `IsAuthenticated`

---

## API Response Examples

### Add to Favorites (First Time)
```json
{
  "data": {
    "id": 1,
    "inventory": {...},
    "user_username": "john_doe",
    "is_active": true,
    "created_date": "2025-12-18T10:30:00Z"
  },
  "message": "'Brake Pad Set' added to your favorites.",
  "newly_added": true
}
```
Status: `201 CREATED`

### Add to Favorites (Already Exists)
```json
{
  "data": {
    "id": 1,
    "inventory": {...},
    "user_username": "john_doe",
    "is_active": true,
    "created_date": "2025-12-18T10:30:00Z"
  },
  "message": "'Brake Pad Set' is already in your favorites.",
  "newly_added": false
}
```
Status: `200 OK`

### List Favorites
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "inventory": {
        "id": 10,
        "item_name": "Brake Pad Set",
        "category": "BRAKES",
        "retail_pricing": "2500.00",
        ...
      },
      "user_username": "john_doe",
      "created_date": "2025-12-18T10:30:00Z"
    }
  ],
  "message": "Favorite products retrieved successfully."
}
```

### Check if Favorited
```json
{
  "is_favorite": true,
  "inventory_id": 10
}
```

---

## Database Query Examples

```python
# Add to favorites
from apps.carts.models import Favorite
from apps.stock_management.models import Inventory

inventory = Inventory.objects.get(id=10)
favorite, created, message = Favorite.add_to_favorites(request.user, inventory)
# If duplicate: created = False, message = "... already in your favorites."

# Remove from favorites
success, message = Favorite.remove_from_favorites(request.user, inventory)
# If success: message = "... removed from your favorites."

# List user's favorites
favorites = Favorite.objects.filter(user=request.user, is_active=True)

# Check if product is favorited
is_favorited = Favorite.objects.filter(
    user=request.user,
    inventory_id=10,
    is_active=True
).exists()
```

---

## Integration Steps

### 1. Apply Migration
```bash
python manage.py migrate carts
```

### 2. Update Django Admin (Optional)
Add to `apps/carts/admin.py`:
```python
from apps.carts.models import Favorite

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'inventory', 'is_active', 'created']
    list_filter = ['is_active', 'created']
    search_fields = ['user__username', 'inventory__item_name']
    readonly_fields = ['created', 'modified']
```

### 3. Test Endpoints
```bash
# List favorites
curl -X GET http://localhost:8000/api/favorites/ -H "Authorization: Bearer <token>"

# Add to favorites
curl -X POST http://localhost:8000/api/favorites/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"inventory_id": 10}'

# Check if favorited
curl -X GET http://localhost:8000/api/favorites/check/10/ \
  -H "Authorization: Bearer <token>"

# Remove favorite
curl -X DELETE http://localhost:8000/api/favorites/1/ \
  -H "Authorization: Bearer <token>"
```

---

## Files Modified/Created

```
✅ apps/carts/models/favourite_model.py          (NEW)
✅ apps/carts/serializers/favourite_serializers.py (NEW)
✅ apps/carts/views/favourite_views.py           (NEW)
✅ apps/carts/migrations/0003_favorite.py        (NEW)
✅ apps/carts/models/__init__.py                 (UPDATED)
✅ apps/carts/serializers/__init__.py            (UPDATED)
✅ apps/carts/views/__init__.py                  (UPDATED)
✅ apps/carts/urls.py                            (UPDATED)
```

---

## Summary
A complete, production-ready favorite products feature with:
- ✅ Duplicate checking with proper messaging
- ✅ Soft delete functionality
- ✅ Optimized database queries
- ✅ User isolation/permissions
- ✅ RESTful API design
- ✅ Comprehensive error handling
