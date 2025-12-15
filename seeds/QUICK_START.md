# Quick Start Guide - Seed Data

## One Command to Rule Them All

```bash
python manage.py seed_all
```

This single command will populate your entire database with realistic test data across 13 different models.

---

## What Gets Created

```
✓ 4 Subscription Plans (Starter → Enterprise)
✓ 3 Tenant Organizations
✓ 3 Active Subscriptions
✓ 13 Users (Super Admin, Admin, Cashier, Inventory, Customers)
✓ 6 Branches
✓ 8 Parties (4 Suppliers + 4 Customers)
✓ 12 Inventory Items with 3-tier pricing
✓ 3 Purchase Orders with line items
✓ 6 Bank Accounts
✓ 5 Bills/Invoices
✓ 3 Sales Orders with items
✓ 2 Shopping Carts with cart items
✓ 3 OTP Records
```

**Total: 70+ Records Created**

---

## Test User Accounts

### Login with these credentials:

#### Super Admin (Full Access)
```
Username: superadmin
Password: Admin@123
Role: Super Admin
Email: superadmin@serveiqdemo.com
```

#### Admin (Tenant Admin)
```
Username: admin
Password: Admin@123
Role: Admin
Email: admin@serveiqdemo.com
```

#### Cashier (Operational)
```
Username: cashier1
Password: Cashier@123
Role: Cashier
Email: cashier1@serveiqdemo.com
```

#### Inventory Manager (Operations)
```
Username: inventory1
Password: Inventory@123
Role: Inventory Manager
Email: inventory1@serveiqdemo.com
```

#### Customer (Buyer)
```
Username: customer1
Password: Customer@123
Role: Customer
Email: customer1@example.com
```

---

## All Generated Data By Category

### Subscription Plans
- Starter ($9.99/mo, 1 user, 1 branch)
- Professional ($29.99/mo, 5 users, 2 branches)
- Business ($99.99/mo, 20 users, 5 branches)
- Enterprise ($299.99/mo, 100 users, 20 branches)

### Tenants
- ServeIQ Demo Co (Starter plan)
- Parts Center Ltd (Professional plan)
- Auto Spares Global (Business plan)

### Users (13 Total)
**ServeIQ Demo Co:**
- 1 Super Admin (superadmin)
- 1 Admin (admin)
- 1 Sub Admin (subadmin)
- 2 Cashiers (cashier1, cashier2)
- 2 Inventory Managers (inventory1, inventory2)
- 2 Customers (customer1, customer2)

**Parts Center Ltd:**
- 1 Admin (admin2)
- 1 Inventory Manager (inventory3)

**Auto Spares Global:**
- 1 Admin (admin3)

### Branches (6 Total)
- ServeIQ Demo Co: Main HQ, Downtown, Uptown Warehouse
- Parts Center Ltd: Main, South
- Auto Spares Global: Central

### Inventory (12 Items)
All with realistic pricing tiers:
1. Engine Oil Filter - $8.50
2. Air Filter - $12.99
3. Brake Pads Set - $45.00
4. Spark Plug - $5.99
5. Battery 12V - $120.00
6. Alternator - $350.00
7. Water Pump - $85.00
8. Clutch Plate - $65.00
9. Tire Tube - $15.00
10. Wiper Blade - $22.50
11. Radiator Hose - $35.00
12. Transmission Fluid - $450.00

### Parties (8 Total)
**Suppliers:**
- Global Auto Parts Supplier
- Premium Parts International
- TechSpares Manufacturing
- Economy Parts Ltd

**Customers:**
- City Auto Retail Store
- Quick Fix Auto Workshop
- National Auto Distributor
- Bulk Auto Wholesaler

### Purchase Orders (3)
- PO-2025-001: Ordered (Engine Oil Filter x50, Air Filter x40)
- PO-2025-002: Received (Brake Pads x30)
- PO-2025-003: Draft (Spark Plug x60)

### Sales Orders (3)
- SO-001 (customer1): Confirmed, $610.50, Pending
- SO-002 (customer2): Packed, $635.50, Paid
- SO-003 (customer1): Delivered, $610.50, Paid

### Shopping Carts (2)
- customer1's cart: 3 items, $161.00
- customer2's cart: 3 items, $161.00

### Bank Accounts (6)
- Main Operating Account (Bank)
- Savings Account (Bank)
- eSewa Merchant Account
- Main Cash Register (Cash)
- Parts Center Bank (Bank)
- Store Cash Box (Cash)

### Bills (5)
- ABC Auto Workshop
- Quick Fix Retail
- Premium Parts Wholesaler
- National Auto Distributor
- Regional Parts Retailer

### OTP Records (3)
- 123456 (customer1)
- 654321 (customer2)
- 999888 (admin)

---

## Reset & Re-seed

To clear everything and start fresh:

```bash
# Clear database
python manage.py flush

# Run migrations
python manage.py migrate

# Re-seed
python manage.py seed_all
```

---

## File Locations

```
seeds/
├── management/
│   └── commands/
│       └── seed_all.py           ← Main seeding command
├── seed_data.json                ← Data configuration (reference)
├── README.md                     ← Full documentation
└── SEED_DATA_DOCUMENTATION.md    ← Detailed model info
```

---

## Key Features

✅ **Idempotent** - Safe to run multiple times  
✅ **Comprehensive** - All 13 models seeded  
✅ **Realistic** - Business-like test data  
✅ **Multi-tenant** - 3 complete tenant setups  
✅ **Related Data** - Proper foreign key relationships  
✅ **Pricing Tiers** - Retail, wholesale, distributor pricing  
✅ **Status Variety** - Orders in different statuses  
✅ **Real Scenarios** - Actual business use cases  

---

## Customization

Edit seed values in the seed method before running:

```python
# Example: in seed_all.py
inventory_items = [
    {
        'item_name': 'Your Part Name',
        'price': Decimal('99.99'),
        # ... other fields
    }
]
```

Then run `python manage.py seed_all`

---

## Support

For detailed information about each model, see:
- [SEED_DATA_DOCUMENTATION.md](SEED_DATA_DOCUMENTATION.md) - Complete model reference
- [README.md](README.md) - General documentation
- [seed_all.py](management/commands/seed_all.py) - Source code

---

Generated: December 15, 2025
Version: 1.0 - Complete Seed System
