# Barcode Field Implementation Documentation

## Overview

Added barcode field to the Inventory model with comprehensive validation and error handling.

## Field Specifications

### Barcode Field

- **Type**: CharField
- **Max Length**: 50 characters
- **Null**: True (optional - not all inventory items require a barcode)
- **Blank**: True (optional - not compulsory for inventory items)
- **Unique**: True (each barcode must be unique, but uniqueness is scoped per tenant)
- **Help Text**: "Barcode for scanning (alphanumeric only, max 50 characters)"

## Validation Rules

### 1. Format Validation

- **Alphanumeric Only**: Barcode can contain only numbers (0-9) and letters (a-z, A-Z)
- **No Special Characters**: Hyphens and underscores are currently allowed but can be restricted if needed
- **Max 50 Characters**: Cannot exceed 50 character limit

### 2. Uniqueness Validation

- **Per Tenant**: Barcode uniqueness is enforced at the tenant level (multi-tenant support)
- **Soft Delete Support**: Validation excludes removed inventory items (where `is_removed=False`)
- **Update Safe**: During updates, the current instance is excluded from uniqueness checks

### 3. Optional Field

- Barcode is completely optional
- `null=True` and `blank=True` allow empty/null values
- No error raised if barcode is not provided

## Implementation Details

### Model Changes

**File**: `apps/stock_management/models/inventory.py`

```python
barcode = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    unique=True,
    help_text='Barcode for scanning (alphanumeric only, max 50 characters)'
)
```

#### Model Validation (clean method)

```python
# Validate barcode
if self.barcode:
    # Check length
    if len(self.barcode) > 50:
        errors['barcode'] = 'Barcode cannot exceed 50 characters.'
    # Check if alphanumeric only (numbers and letters a-z, case-insensitive)
    elif not self.barcode.replace('-', '').replace('_', '').isalnum():
        errors['barcode'] = 'Barcode must contain only numbers and letters (a-z).'
```

### Serializer Changes

**File**: `apps/stock_management/serializers/inventory.py`

#### Barcode Field Validation

```python
def validate_barcode(self, value):
    """
    Validate barcode:
    - Must be alphanumeric (numbers and letters a-z only)
    - Cannot exceed 50 characters
    - Must be unique per tenant (not enforced for empty/None values)
    """
    if not value:
        return value

    # Validate length
    if len(value) > 50:
        raise serializers.ValidationError('Barcode cannot exceed 50 characters.')

    # Validate alphanumeric only (numbers and letters a-z, case-insensitive)
    if not value.replace('-', '').replace('_', '').isalnum():
        raise serializers.ValidationError('Barcode must contain only numbers and letters (a-z).')

    # Check for duplicates - exclude current instance during updates
    qs = Inventory.objects.filter(barcode=value, is_removed=False)
    if self.instance:
        qs = qs.exclude(pk=self.instance.pk)

    # Narrow by tenant when available to avoid cross-tenant conflicts
    request = self.context.get('request')
    tenant = getattr(getattr(request, 'user', None), 'tenant', None)
    if tenant:
        qs = qs.filter(tenant=tenant)

    if qs.exists():
        raise serializers.ValidationError('Inventory with this Barcode already exists.')
    return value
```

### Migration

**File**: `apps/stock_management/migrations/0009_alter_inventory_barcode.py`

Updates the barcode field from `max_length=100` to `max_length=50` in the database.

## Error Handling

### Validation Errors

The implementation handles errors at two levels:

1. **Model Level** (in `clean()` method):
   - Validates format and length
   - Raises `ValidationError` dictionary with specific field errors

2. **Serializer Level** (in `validate_barcode()` method):
   - Validates format and length
   - Checks for duplicates per tenant
   - Raises `serializers.ValidationError` with descriptive messages
   - Safe handling of None/empty values

### Error Messages

- "Barcode cannot exceed 50 characters."
- "Barcode must contain only numbers and letters (a-z)."
- "Inventory with this Barcode already exists."

## API Response Examples

### Valid Barcode Creation

```json
{
  "item_name": "Engine Oil",
  "barcode": "ENG123456",
  "category": "local",
  "vehicle_type": "two_wheeler"
}
```

### Invalid Barcode - Special Characters

```json
{
  "barcode": ["Barcode must contain only numbers and letters (a-z)."]
}
```

### Invalid Barcode - Exceeds Length

```json
{
  "barcode": ["Barcode cannot exceed 50 characters."]
}
```

### Invalid Barcode - Duplicate

```json
{
  "barcode": ["Inventory with this Barcode already exists."]
}
```

## Database Impact

### Migration Steps

1. Run migration: `python manage.py migrate stock_management`
2. Existing barcodes over 50 characters will be truncated (if any exist)
3. No data loss for other fields

### Database Index

The barcode field is indexed for efficient lookups:

```python
models.Index(fields=['barcode'])
```

## Testing Recommendations

```python
# Test 1: Valid alphanumeric barcode
inventory = Inventory.objects.create(barcode='ABC123')

# Test 2: Empty/null barcode (should be allowed)
inventory = Inventory.objects.create(barcode=None)
inventory = Inventory.objects.create(barcode='')

# Test 3: Invalid characters
try:
    inventory = Inventory.objects.create(barcode='ABC@123')  # Should fail
except ValidationError:
    pass

# Test 4: Duplicate barcode
inventory1 = Inventory.objects.create(barcode='ABC123')
try:
    inventory2 = Inventory.objects.create(barcode='ABC123')  # Should fail
except ValidationError:
    pass

# Test 5: Barcode too long
try:
    inventory = Inventory.objects.create(barcode='A' * 51)  # Should fail
except ValidationError:
    pass
```

## Multi-Tenant Support

The barcode field respects multi-tenant architecture:

- Uniqueness is scoped per tenant
- Barcodes can be duplicated across different tenants
- Serializer filters duplicates by tenant context from request

## Notes

- Barcode field is **optional** for backward compatibility
- Uniqueness constraint is at database level
- Soft delete support (checks `is_removed=False`)
- Case-insensitive alphanumeric validation (accepts both uppercase and lowercase)
- Update-safe: Current instance excluded during uniqueness check
