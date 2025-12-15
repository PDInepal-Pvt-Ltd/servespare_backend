# ServeIQ Seed Data Documentation

## Overview
Comprehensive seed data for all models in the ServeIQ application. All seed data is idempotent and can be run multiple times safely.

## Run Command
```bash
python manage.py seed_all
```

---

## Seeded Models & Data

### 1. **Subscription Plans** (4 plans)
Seeds 4 subscription tiers:

| Plan Name | Price | Users | Branches | Support |
|-----------|-------|-------|----------|---------|
| Starter | $9.99 | 1 | 1 | Email |
| Professional | $29.99 | 5 | 2 | Email |
| Business | $99.99 | 20 | 5 | Phone |
| Enterprise | $299.99 | 100 | 20 | Ticket |

---

### 2. **Tenants** (3 businesses)
Seeds 3 tenant organizations:

| Business Name | Email | Phone | Package | Status |
|---------------|-------|-------|---------|--------|
| ServeIQ Demo Co | admin@serveiqdemo.com | +1234567890 | Starter | Approved |
| Parts Center Ltd | admin@partscenter.com | +9876543210 | Professional | Approved |
| Auto Spares Global | admin@autospares.com | +1122334455 | Business | Approved |

---

### 3. **Subscriptions**
One active subscription per tenant with:
- Subscription Date: Today
- Finish Date: 365 days from today
- Renew Date: On finish date

---

### 4. **Users** (13 users across 3 roles)

#### Primary Tenant (ServeIQ Demo Co) - 10 users
**Admin Users:**
- **superadmin** | super_admin@serveiqdemo.com | SUPER_ADMIN | is_staff ✓ | is_superuser ✓
- **admin** | admin@serveiqdemo.com | ADMIN | is_staff ✓
- **subadmin** | subadmin@serveiqdemo.com | SUB_ADMIN | is_staff ✓

**Operational Staff:**
- **cashier1** | cashier1@serveiqdemo.com | CASHIER
- **cashier2** | cashier2@serveiqdemo.com | CASHIER
- **inventory1** | inventory1@serveiqdemo.com | INVENTORY_MANAGER
- **inventory2** | inventory2@serveiqdemo.com | INVENTORY_MANAGER

**Customers:**
- **customer1** | customer1@example.com | CUSTOMER
- **customer2** | customer2@example.com | CUSTOMER

#### Secondary Tenant (Parts Center Ltd) - 2 users
- **admin2** | admin@partscenter.com | ADMIN | is_staff ✓
- **inventory3** | inventory@partscenter.com | INVENTORY_MANAGER

#### Tertiary Tenant (Auto Spares Global) - 1 user
- **admin3** | admin@autospares.com | ADMIN | is_staff ✓

**Default Password Pattern:** Role@123 (e.g., Admin@123, Cashier@123)

---

### 5. **Branches** (5 branches)

#### ServeIQ Demo Co (3 branches)
1. **Main Headquarters** (HQ001) - 123 Business Avenue, New York, NY 10001
2. **Downtown Branch** (DT001) - 456 Commerce Street, New York, NY 10002
3. **Uptown Warehouse** (UP001) - 789 Industrial Road, New York, NY 10003

#### Parts Center Ltd (2 branches)
4. **Parts Center Main** (PC001) - 321 Parts Lane, Los Angeles, CA 90001
5. **Parts Center South** (PC002) - 654 Supplier Road, Long Beach, CA 90802

#### Auto Spares Global (1 branch)
6. **Auto Spares Central** (AS001) - 987 Auto Plaza, Chicago, IL 60601

---

### 6. **Parties** (8 parties total)

#### Suppliers (4)
| Party Name | Contact | Email | Location | Payment Terms |
|-----------|---------|-------|----------|---------------|
| Global Auto Parts Supplier | Mr. Kumar | contact@globalauto.com | Newark, NJ | Cash |
| Premium Parts International | Ms. Johnson | sales@premiumparts.com | Jersey City, NJ | 15 Day Credit |
| TechSpares Manufacturing | Dr. Patel | sales@techspares.com | Edison, NJ | 30 Day Credit |
| Economy Parts Ltd | Mr. Singh | info@economyparts.com | Paterson, NJ | 7 Day Credit |

#### Customers (4)
| Party Name | Type | Contact | Email | Location | Payment Terms |
|-----------|------|---------|-------|----------|---------------|
| City Auto Retail Store | Retailer | Mr. Williams | manager@cityauto.com | New York, NY | Cash |
| Quick Fix Auto Workshop | Workshop | Mr. Martinez | quickfix@workshop.com | New York, NY | 15 Day Credit |
| National Auto Distributor | Distributor | Ms. Thompson | sales@nationaldist.com | Newark, NJ | 30 Day Credit |
| Bulk Auto Wholesaler | Wholesaler | Mr. Davis | bulk@wholesaler.com | Paterson, NJ | 45 Day Credit |

---

### 7. **Inventory** (12 items with comprehensive pricing)

All inventory includes:
- Item Name, Part Number, SKU
- HSN Code, Category (local/original)
- Vehicle Type (two_wheeler/four_wheeler)
- Quantity, Min Stock Level
- Base Price, MRP, Retail Pricing, Wholesale Price, Distributor Price
- Storage Location
- Warranty Period (1-24 months)
- Barcode, Vehicle Details, Model, Type

#### Inventory Items List:
1. **Engine Oil Filter Premium** (PART001) - Qty: 150, Price: $8.50
2. **Air Filter High Flow** (PART002) - Qty: 200, Price: $12.99
3. **Brake Pads Set Ceramic** (PART003) - Qty: 75, Price: $45.00
4. **Spark Plug Iridium** (PART004) - Qty: 300, Price: $5.99
5. **Battery 12V 50Ah Premium** (PART005) - Qty: 30, Price: $120.00
6. **Alternator 90A Durable** (PART006) - Qty: 20, Price: $350.00
7. **Water Pump Assembly Complete** (PART007) - Qty: 15, Price: $85.00
8. **Clutch Plate Heavy Duty** (PART008) - Qty: 50, Price: $65.00
9. **Tire Tube 17 inch MRF** (PART009) - Qty: 100, Price: $15.00
10. **Wiper Blade Assembly Bosch** (PART010) - Qty: 80, Price: $22.50
11. **Radiator Hose Silicone** (PART011) - Qty: 60, Price: $35.00
12. **Transmission Fluid ATF** (PART012) - Qty: 120, Price: $450.00

---

### 8. **Purchase Orders** (3 POs with items)

| PO Number | Status | Supplier | Order Date | Expected Delivery | Items |
|-----------|--------|----------|------------|------------------|-------|
| PO-2025-001 | Ordered | Global Auto Parts Supplier | Today-7 | Today+7 | 2 items (Engine Oil Filter x50, Air Filter x40) |
| PO-2025-002 | Received | Premium Parts International | Today-20 | Today-5 | 1 item (Brake Pads x30) |
| PO-2025-003 | Draft | Global Auto Parts Supplier | Today | Today+14 | 1 item (Spark Plug x60) |

**Purchase Order Items Include:**
- Item Name, Part Number
- Quantity, Unit Price
- Tax (18%), Discount Description

---

### 9. **Bank Accounts** (6 accounts)

#### ServeIQ Demo Co (4 accounts)
1. **Main Operating Account** - Bank Account | First National Bank | ACC-001234567890
2. **Savings Account** - Bank Account | First National Bank | ACC-009876543210
3. **eSewa Merchant Account** - eSewa | ESEWA-123456
4. **Main Cash Register** - Cash | Manual Management

#### Parts Center Ltd (2 accounts)
5. **Parts Center Bank** - Bank Account | West Coast Bank | ACC-111222333444
6. **Store Cash Box** - Cash | Manual Management

---

### 10. **Bills** (5 invoices)

| Customer Name | Address | Phone | PAN/VAT | Type |
|---------------|---------|-------|---------|------|
| ABC Auto Workshop | 123 Workshop Lane, New York, NY 10001 | +1111111111, +2222222222 | AABBH1234A | Workshop |
| Quick Fix Retail | 456 Retail Plaza, New York, NY 10002 | +3333333333 | CCDDP5678B | Retail |
| Premium Parts Wholesaler | 789 Wholesale Drive, Newark, NJ 07101 | +4444444444, +5555555555 | EEFFM9012C | Wholesaler |
| National Auto Distributor | 321 Distribution Ave, Newark, NJ 07102 | +6666666666 | GGHHR3456D | Distributor |
| Regional Parts Retailer | 654 Retail Road, Jersey City, NJ 07302 | +7777777777, +8888888888 | IIJJS7890E | Retailer |

---

### 11. **Sales Orders** (3 orders with items)

For each of the 3 customer users:

| Order | Customer | Status | Subtotal | Discount | Tax | Shipping | Total | Payment Status | Method |
|-------|----------|--------|----------|----------|-----|----------|-------|----------------|--------|
| SO-001 | customer1 | Confirmed | $500.00 | $25.00 (5%) | $85.50 | $50.00 | $610.50 | Pending | Cash |
| SO-002 | customer2 | Packed | $500.00 | $0.00 | $85.50 | $50.00 | $635.50 | Paid | Card |
| SO-003 | customer1 | Delivered | $500.00 | $25.00 (5%) | $85.50 | $50.00 | $610.50 | Paid | UPI |

**Sales Order Items Include:**
- Inventory Item Reference
- Quantity (2+ items per order)
- Unit Price (retail pricing)
- Auto-calculated totals

---

### 12. **Shopping Carts** (2 carts with items)

For the first 2 customer users:

**Cart 1:** customer1
- Engine Oil Filter (Qty: 2) @ $10.50
- Air Filter (Qty: 2) @ $15.50
- Brake Pads Set (Qty: 2) @ $55.00
- **Cart Subtotal:** $161.00

**Cart 2:** customer2
- Engine Oil Filter (Qty: 2) @ $10.50
- Air Filter (Qty: 2) @ $15.50
- Brake Pads Set (Qty: 2) @ $55.00
- **Cart Subtotal:** $161.00

---

### 13. **OTP (One-Time Passwords)** (3 OTP records)

| User | Username | OTP Code | Expires In |
|------|----------|----------|-----------|
| customer1 | customer1 | 123456 | 10 minutes |
| customer2 | customer2 | 654321 | 10 minutes |
| admin | admin | 999888 | 10 minutes |

---

## Data Statistics

| Model | Count | Description |
|-------|-------|-------------|
| Subscription Plans | 4 | Different pricing tiers |
| Tenants | 3 | Business organizations |
| Subscriptions | 3 | Active subscriptions (1 per tenant) |
| Users | 13 | Different roles (Admin, Staff, Customers) |
| Branches | 6 | Distribution centers |
| Parties | 8 | 4 Suppliers + 4 Customers |
| Inventory Items | 12 | Auto spare parts with full pricing |
| Purchase Orders | 3 | With 4 total PO items |
| Sales Orders | 3 | With 6 total SO items |
| Bills | 5 | Customer invoices |
| Carts | 2 | With 6 total cart items |
| Bank Accounts | 6 | Different payment methods |
| OTP Records | 3 | For user authentication |
| **TOTAL RECORDS** | **~70+** | **Complete test dataset** |

---

## Data Relationships

```
Tenant (3)
├── SubscriptionPlan (linked via package)
├── Subscription (1 per tenant)
├── Branch (6 total across all)
├── User (13 total across all)
├── Inventory (12 items)
├── Party (8 parties)
│   ├── PurchaseOrder (3 POs from suppliers)
│   │   └── PurchaseOrderItem (4 items)
│   └── Customer parties (4)
├── BankAccount (6 accounts)
├── Bill (5 bills)
└── SalesOrder (from users)
    ├── SalesOrderItem (6 items)
    └── Cart (2 carts)
        └── CartItem (6 items)

OTP (3 records)
└── User (authentication)
```

---

## Testing Credentials

### Admin Access
- **Username:** superadmin
- **Password:** Admin@123
- **Role:** Super Admin
- **Tenant:** ServeIQ Demo Co

### Staff Access
- **Username:** admin
- **Password:** Admin@123
- **Role:** Admin
- **Tenant:** ServeIQ Demo Co

### Customer Access
- **Username:** customer1
- **Password:** Customer@123
- **Role:** Customer
- **Tenant:** ServeIQ Demo Co

---

## Notes

1. **Idempotent Seeding:** All seed methods use `get_or_create()` to prevent duplicates
2. **Decimal Precision:** All monetary values use `Decimal` for accuracy
3. **Date Handling:** Uses relative dates for validity (today, today±N days)
4. **Relationships:** All foreign keys are properly maintained
5. **Multi-tenancy:** Complete data setup for 3 different tenants
6. **Comprehensive Testing:** Covers all major models and relationships
7. **Real-world Data:** Uses realistic business scenarios and pricing

---

## How to Customize

To modify seed data:

1. Open [seeds/management/commands/seed_all.py](seed_all.py)
2. Find the seed method for the model you want to customize
3. Modify the data in the list/dictionary
4. Run `python manage.py seed_all` again

All existing data will remain unchanged due to idempotent queries.

---

## Troubleshooting

**Issue:** "ModuleNotFoundError" when running seed command
- **Solution:** Ensure all app imports are correct and apps are in INSTALLED_APPS

**Issue:** "Unique constraint violated"
- **Solution:** Data with same SKU/email already exists. Run flush to reset.

**Issue:** Foreign key errors
- **Solution:** Ensure seed methods are called in correct order (as done in handle method)

---

## Future Enhancements

- Add more complex order scenarios
- Implement factory-based seeding using factory_boy
- Add CSV import/export functionality
- Create periodic seeding for demo environments
- Add payment transaction history
- Add delivery tracking data
