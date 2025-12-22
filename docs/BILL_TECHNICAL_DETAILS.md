# Technical Implementation Details - Bill System

This document details all technical changes made to implement the Bill & Inventory reduction system.

---

## Files Modified

### 1. `apps/sales/models/bills.py`

#### Change 1: Updated PurchaseItem Class Definition

**Location:** Lines 231-278

**Old Code:**
```python
class PurchaseItem(models.Model):
    """
    Model to store details of products purchased in a bill
    """
    bill = models.ForeignKey(
        'Bill',
        on_delete=models.CASCADE,
        related_name='purchase_items',
        help_text='Bill associated with this purchase item'
    )
    product_name = models.CharField(max_length=255, help_text='Name of the product')
    quantity = models.PositiveIntegerField(help_text='Quantity of the product')
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text='Price of the product')

    def total_price(self):
        return self.price * self.quantity
```

**New Code:**
```python
class PurchaseItem(models.Model):
    """
    Model to store details of products purchased in a bill
    """
    bill = models.ForeignKey(
        'Bill',
        on_delete=models.CASCADE,
        related_name='purchase_items',
        help_text='Bill associated with this purchase item'
    )
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='purchase_items',
        help_text='Inventory item being purchased'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Quantity of the product'
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Price of the product at the time of purchase'
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchase_item'
        verbose_name = 'Purchase Item'
        verbose_name_plural = 'Purchase Items'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['bill']),
            models.Index(fields=['inventory']),
        ]

    def __str__(self):
        return f"{self.inventory.item_name} x {self.quantity}"

    def total_price(self):
        return self.price * self.quantity
```

**Changes:**
- ✅ Added `inventory` ForeignKey to link purchase items to actual inventory products
- ✅ Removed `product_name` CharField (now read-only from inventory)
- ✅ Changed `quantity` from `PositiveIntegerField` to `DecimalField` for partial units support
- ✅ Added `created` and `modified` DateTimeFields for audit trail
- ✅ Added Meta class with proper table name, ordering, and indexes
- ✅ Added `__str__` method for better admin display

#### Change 2: Updated decrease_inventory() Method

**Location:** Lines 223-228

**Old Code:**
```python
def decrease_inventory(self):
    for item in self.purchase_items.all():
        product = Inventory.objects.get(item_name=item.product_name)  # Assuming product name is unique
        product.quantity -= item.quantity
        product.save()
```

**New Code:**
```python
def decrease_inventory(self):
    """Decrease inventory quantities for all purchase items in this bill"""
    from decimal import Decimal
    for item in self.purchase_items.all():
        if item.inventory and item.quantity > 0:
            item.inventory.quantity = max(
                Decimal('0.00'),
                item.inventory.quantity - item.quantity
            )
            item.inventory.save(update_fields=['quantity', 'modified'])
```

**Changes:**
- ✅ Uses ForeignKey relationship instead of name matching
- ✅ Validates item has inventory and quantity > 0
- ✅ Uses `max()` to prevent negative inventory (floor at 0)
- ✅ Uses `update_fields` for efficient database update
- ✅ Includes docstring for clarity

---

### 2. `apps/sales/serializers/bill.py`

#### Updated PurchaseItemSerializer

**Location:** Lines 5-34

**Old Code:**
```python
class PurchaseItemSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseItem model
    """
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PurchaseItem
        fields = [
            'id',
            'bill',
            'product_name',
            'quantity',
            'price',
            'total_price'
        ]
        read_only_fields = ['id', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()
```

**New Code:**
```python
class PurchaseItemSerializer(serializers.ModelSerializer):
    """
    Serializer for PurchaseItem model with nested inventory information
    """
    total_price = serializers.SerializerMethodField(read_only=True)
    product_name = serializers.CharField(source='inventory.item_name', read_only=True)
    inventory_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = PurchaseItem
        fields = [
            'id',
            'bill',
            'inventory',
            'inventory_id',
            'product_name',
            'quantity',
            'price',
            'total_price',
            'created',
            'modified'
        ]
        read_only_fields = ['id', 'total_price', 'created', 'modified', 'product_name']

    def get_total_price(self, obj):
        return obj.total_price()

    def create(self, validated_data):
        """Handle inventory_id during creation"""
        inventory_id = validated_data.pop('inventory_id', None)
        if inventory_id:
            from apps.stock_management.models import Inventory
            validated_data['inventory_id'] = inventory_id
        return super().create(validated_data)
```

**Changes:**
- ✅ Added `product_name` as read-only field sourced from `inventory.item_name`
- ✅ Added `inventory_id` as write-only integer field for creating items
- ✅ Added `inventory`, `created`, `modified` to fields list
- ✅ Added custom `create()` method to handle inventory_id mapping
- ✅ Updated read_only_fields list
- ✅ Improved docstring

---

### 3. `apps/sales/views/bill.py`

#### Change 1: Enhanced add_purchase_item() Action

**Location:** Lines 143-157

**Old Code:**
```python
@action(detail=True, methods=['post'])
def add_purchase_item(self, request, pk=None):
    """
    Add a purchase item to a bill
    """
    bill = self.get_object()
    
    serializer = PurchaseItemSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(bill=bill)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

**New Code:**
```python
@action(detail=True, methods=['post'])
def add_purchase_item(self, request, pk=None):
    """
    Add a purchase item to a bill
    
    Expected request body:
    {
        "inventory": <inventory_id>,
        "quantity": <quantity>,
        "price": <price>
    }
    """
    bill = self.get_object()
    
    serializer = PurchaseItemSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(bill=bill)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

**Changes:**
- ✅ Added detailed docstring with expected request format
- ✅ Clarified the API contract for clients

#### Change 2: Enhanced mark_paid() Action

**Location:** Lines 166-176

**Old Code:**
```python
@action(detail=True, methods=['post'])
def mark_paid(self, request, pk=None):
    """
    Mark a bill as paid
    """
    bill = self.get_object()
    bill.status = 'paid'
    bill.save()
    
    serializer = self.get_serializer(bill)
    return Response(serializer.data)
```

**New Code:**
```python
@action(detail=True, methods=['post'])
def mark_paid(self, request, pk=None):
    """
    Mark a bill as paid and decrease inventory quantities
    """
    bill = self.get_object()
    bill.status = 'paid'
    bill.save()
    
    # Decrease inventory for all purchase items
    bill.decrease_inventory()
    
    serializer = self.get_serializer(bill)
    return Response(serializer.data)
```

**Changes:**
- ✅ Added automatic call to `bill.decrease_inventory()` when marking as paid
- ✅ Updated docstring to reflect new behavior
- ✅ Inventory quantities automatically reduced when payment processed

---

### 4. `apps/sales/migrations/0015_update_purchaseitem_inventory_link.py` (NEW)

**Location:** New file created

**Purpose:** Database migration to update PurchaseItem model structure

**Operations:**
1. Add `inventory` ForeignKey to PurchaseItem
2. Add `created` DateTimeField
3. Add `modified` DateTimeField
4. Convert `quantity` from PositiveIntegerField to DecimalField
5. Remove `product_name` CharField
6. Update model metadata (table name, ordering)
7. Create database indexes for performance

**Key Points:**
- ✅ Migrates existing data safely
- ✅ Maintains foreign key constraints
- ✅ Adds performance indexes
- ✅ Can be rolled back if needed

---

## Data Flow

### Creating a Bill with Items and Paying

```
┌─────────────────────┐
│   Frontend/Client   │
└──────────┬──────────┘
           │
           ├──> 1. POST /api/bills/ ──> Creates Bill (status=draft)
           │
           ├──> 2. POST /api/bills/{id}/add_purchase_item/ 
           │         + inventory=5, qty=2.5, price=500
           │         ──> Creates PurchaseItem (links to Inventory #5)
           │
           ├──> 3. POST /api/bills/{id}/add_purchase_item/
           │         + inventory=12, qty=5, price=200
           │         ──> Creates PurchaseItem (links to Inventory #12)
           │
           └──> 4. POST /api/bills/{id}/mark_paid/
                   ──> Updates status='paid'
                   ──> Calls decrease_inventory()
                       ├─> Inventory #5: 100 → 97.5
                       └─> Inventory #12: 50 → 45
```

---

## Database Schema Changes

### Before (OLD)

```sql
CREATE TABLE purchase_item (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bill_id BIGINT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (bill_id) REFERENCES bill(id)
);
```

### After (NEW)

```sql
CREATE TABLE purchase_item (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bill_id BIGINT NOT NULL,
    inventory_id BIGINT NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    created DATETIME NOT NULL,
    modified DATETIME NOT NULL,
    FOREIGN KEY (bill_id) REFERENCES bill(id),
    FOREIGN KEY (inventory_id) REFERENCES inventory(id),
    INDEX purchase_item_bill_idx (bill_id),
    INDEX purchase_item_inventory_idx (inventory_id)
);
```

**Key Changes:**
- ✅ Removed `product_name` column
- ✅ Added `inventory_id` ForeignKey column
- ✅ Changed `quantity` type to DECIMAL
- ✅ Added `created` and `modified` timestamp columns
- ✅ Added database indexes for performance

---

## API Changes

### Request/Response Format

#### Add Purchase Item - OLD
```json
{
  "product_name": "Brake Pad",
  "quantity": 2,
  "price": 500.00
}
```

#### Add Purchase Item - NEW
```json
{
  "inventory": 5,
  "quantity": 2.50,
  "price": 500.00
}
```

#### Response - OLD
```json
{
  "id": 1,
  "bill": 1,
  "product_name": "Brake Pad",
  "quantity": 2,
  "price": "500.00",
  "total_price": "1000.00"
}
```

#### Response - NEW
```json
{
  "id": 1,
  "bill": 1,
  "inventory": 5,
  "inventory_id": 5,
  "product_name": "Brake Pad Set",
  "quantity": "2.50",
  "price": "500.00",
  "total_price": "1250.00",
  "created": "2025-12-22T10:31:00Z",
  "modified": "2025-12-22T10:31:00Z"
}
```

---

## Backward Compatibility

⚠️ **BREAKING CHANGES:**

The following are breaking changes and require frontend updates:

1. **Request Format** - Must send `inventory` ID instead of `product_name`
2. **Field Changes** - `product_name` is now read-only, sourced from inventory
3. **Quantity Type** - Now supports decimals (e.g., 2.50)
4. **New Response Fields** - `created`, `modified`, `inventory_id` added

✅ **To Handle Existing Data:**

When migration is applied:
- Old `product_name` field is removed
- New `inventory` ForeignKey is added (nullable=True initially)
- Existing purchase items will have `inventory=NULL`
- These items become orphaned (product_name is lost)

**Recommendation:** 
- Back up database before migration
- Run migration on staging first
- Clear old purchase items if not needed
- Update frontend to use new API format

---

## Performance Implications

### Positive ✅
- **Database Indexes** - New indexes on `bill_id` and `inventory_id` improve query speed
- **Efficient Updates** - `update_fields` parameter reduces data transfer
- **Decimal Type** - Better for financial calculations than Integer

### Negative ⚠️
- **ForeignKey Lookup** - One extra join when retrieving inventory details (minimal impact)
- **Migration Time** - May take time on large existing tables

### Optimization Tips:

```python
# Good - Use select_related() to avoid N+1 queries
bills = Bill.objects.prefetch_related('purchase_items__inventory')

# Good - Filter with F objects
from django.db.models import F
items = PurchaseItem.objects.filter(quantity__gt=F('bill__discount_value'))

# Bad - Avoid
for bill in Bill.objects.all():
    for item in bill.purchase_items.all():  # N+1 queries!
        print(item.inventory.item_name)
```

---

## Testing Checklist

### Unit Tests to Add

```python
# Test 1: PurchaseItem creation with inventory
def test_purchase_item_creation():
    inv = Inventory.objects.create(...)
    bill = Bill.objects.create(...)
    item = PurchaseItem.objects.create(
        bill=bill,
        inventory=inv,
        quantity=Decimal('2.50'),
        price=Decimal('500.00')
    )
    assert item.inventory == inv
    assert item.total_price() == Decimal('1250.00')

# Test 2: Inventory decrease on bill payment
def test_inventory_decrease():
    inv = Inventory.objects.create(quantity=Decimal('100.00'), ...)
    bill = Bill.objects.create(...)
    PurchaseItem.objects.create(
        bill=bill,
        inventory=inv,
        quantity=Decimal('2.50'),
        price=Decimal('500.00')
    )
    bill.decrease_inventory()
    inv.refresh_from_db()
    assert inv.quantity == Decimal('97.50')

# Test 3: Inventory won't go below zero
def test_inventory_floor_at_zero():
    inv = Inventory.objects.create(quantity=Decimal('1.00'), ...)
    bill = Bill.objects.create(...)
    PurchaseItem.objects.create(
        bill=bill,
        inventory=inv,
        quantity=Decimal('5.00'),
        price=Decimal('500.00')
    )
    bill.decrease_inventory()
    inv.refresh_from_db()
    assert inv.quantity == Decimal('0.00')  # Not negative!
```

### Integration Tests

```bash
# Create bill
curl -X POST http://localhost:8000/api/bills/ \
  -d '{"customer_name":"Test","customer_type":"retail"}'

# Add item
curl -X POST http://localhost:8000/api/bills/1/add_purchase_item/ \
  -d '{"inventory":5,"quantity":2.50,"price":500}'

# Verify item added
curl -X GET http://localhost:8000/api/bills/1/purchase_items/

# Check inventory before
curl -X GET http://localhost:8000/api/inventory/5/

# Mark paid
curl -X POST http://localhost:8000/api/bills/1/mark_paid/

# Check inventory after
curl -X GET http://localhost:8000/api/inventory/5/
# Should see quantity decreased
```

---

## Deployment Steps

1. **Backup Database**
   ```bash
   python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
   ```

2. **Run Migration**
   ```bash
   python manage.py migrate sales
   ```

3. **Verify Migration**
   ```bash
   python manage.py sqlmigrate sales 0015
   python manage.py check
   ```

4. **Update Frontend**
   - Change product input from text to dropdown
   - Update API calls to send `inventory` ID
   - Update response parsing for new fields

5. **Test Thoroughly**
   - Create test bill
   - Add products
   - Mark as paid
   - Verify inventory decreased

6. **Monitor**
   - Check application logs
   - Monitor database performance
   - Watch for API errors

---

## Rollback Plan

If issues occur:

```bash
# Rollback migration
python manage.py migrate sales 0014

# Restore database
python manage.py loaddata backup_YYYYMMDD_HHMMSS.json
```

**Note:** Rollback will lose any purchase items created after migration.

---

## Related Files

- [Bill System Guide](./BILL_SYSTEM_GUIDE.md) - User/API documentation
- [Complete Example](./BILL_COMPLETE_EXAMPLE.md) - End-to-end workflow example
- [Implementation Summary](../BILL_IMPLEMENTATION_SUMMARY.md) - High-level overview

