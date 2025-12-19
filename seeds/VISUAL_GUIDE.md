# 📊 Serve Spare Seed Data - Visual Guide

## 🎯 What Gets Created in One Command

```
python manage.py seed_all
```

### 📈 Data Distribution

```
    SUBSCRIPTION PLANS (4)
            ↓
        TENANTS (3)
            ↓
    ┌───────┼───────┐
    ↓       ↓       ↓
  TENANT1 TENANT2 TENANT3
    ├─        ├─      ├─
    ├─Users   ├─Users ├─Users
    │ (4)     │ (2)   │ (1)
    │
    ├─Branches(3)
    ├─Inventory(12) ─┐
    │                └─→ Purchase Orders(3)
    ├─Parties(8)  ──────→ Purchase Order Items(4)
    │  ├─Suppliers(4)
    │  └─Customers(4)
    │
    ├─Bank Accounts(4)
    ├─Bills(5)
    │
    └─Sales Orders(3)
       └─Items(6)
       └─Carts(2)
          └─Items(6)

Total: 70+ Records
```

---

## 👥 User Hierarchy

```
SUPER ADMIN (1)
├── Full system access
├── Can manage all tenants
└── Email: superadmin@serveiqdemo.com

ADMIN (3)
├── Per-tenant administration
├── Manage users, branches
└── Per tenant basis

SUB ADMIN (1)
├── Assistant to admin
└── Limited management

CASHIER (2)
├── Financial operations
└── Payment processing

INVENTORY MANAGER (2)
├── Stock management
├── Order handling
└── Warehouse operations

CUSTOMER (4)
├── Browse & purchase
├── View orders
└── Cart management
```

---

## 🏢 Tenant Structure

```
┌─────────────────────────────────────────────┐
│ TENANT 1: ServeIQ Demo Co (Starter Plan)    │
├─────────────────────────────────────────────┤
│ • Subscription: Starter ($9.99/mo)          │
│ • Users Allowed: 1 | Has: 4 (demo)          │
│ • Branches Allowed: 1 | Has: 3 (demo)       │
│ • Support: Email Only                       │
│                                              │
│ BRANCHES: Main HQ, Downtown, Uptown         │
│ USERS: superadmin, admin, cashier1,         │
│        inventory1, customer1, customer2     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ TENANT 2: Parts Center Ltd (Professional)   │
├─────────────────────────────────────────────┤
│ • Subscription: Professional ($29.99/mo)    │
│ • Users Allowed: 5 | Has: 2 (demo)          │
│ • Branches Allowed: 2 | Has: 2 (demo)       │
│ • Support: Email                            │
│                                              │
│ BRANCHES: Parts Center Main, South          │
│ USERS: admin2, inventory3                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ TENANT 3: Auto Spares Global (Business)     │
├─────────────────────────────────────────────┤
│ • Subscription: Business ($99.99/mo)        │
│ • Users Allowed: 20 | Has: 1 (demo)         │
│ • Branches Allowed: 5 | Has: 1 (demo)       │
│ • Support: Phone                            │
│                                              │
│ BRANCHES: Auto Spares Central               │
│ USERS: admin3                               │
└─────────────────────────────────────────────┘
```

---

## 📦 Inventory Pricing Tiers

```
Item: Engine Oil Filter Premium

BASE STRUCTURE:
├─ Base Price: $8.50
├─ MRP: $12.00
│
└─ THREE-TIER PRICING:
   ├─ Retail: $10.50 (end customer)
   ├─ Wholesale: $9.00 (bulk buyer)
   └─ Distributor: $8.50 (large bulk)

OTHER DETAILS:
├─ Category: Original
├─ Vehicle Type: Four Wheeler
├─ Warranty: 3 months
├─ Stock: 150 units
├─ Min Level: 20 units
├─ Storage: Shelf A1
├─ Barcode: 8901234567001
├─ HSN Code: 84211190
├─ Part Number: OIL-FIL-001
└─ SKU: PART001
```

---

## 🛒 Order Flow

```
PURCHASE ORDER FLOW:
┌─────────────────────────────────────────────┐
│ Supplier Creates PO                         │
├─────────────────────────────────────────────┤
│ PO-2025-001: ORDERED                        │
│ ├─ Item: Engine Oil Filter x50              │
│ ├─ Unit Price: $8.50                        │
│ ├─ Tax: 18%                                 │
│ ├─ Subtotal: $425.00                        │
│ └─ Expected Delivery: 7 days                │
│                                              │
│ PO-2025-002: RECEIVED ✓                     │
│ ├─ Item: Brake Pads x30                     │
│ ├─ Unit Price: $45.00                       │
│ └─ Received Date: 5 days ago                │
│                                              │
│ PO-2025-003: DRAFT                          │
│ ├─ Item: Spark Plug x60                     │
│ └─ Status: Awaiting Approval                │
└─────────────────────────────────────────────┘

SALES ORDER FLOW:
┌─────────────────────────────────────────────┐
│ Customer Places Order                       │
├─────────────────────────────────────────────┤
│ SO-001: CONFIRMED                           │
│ ├─ Customer: customer1                      │
│ ├─ Items: 2                                 │
│ ├─ Subtotal: $500.00                        │
│ ├─ Discount: 5% ($25.00)                    │
│ ├─ Tax: 18% ($85.50)                        │
│ ├─ Shipping: $50.00                         │
│ ├─ Total: $610.50                           │
│ └─ Payment Status: PENDING                  │
│                                              │
│ SO-002: PACKED ✓                            │
│ ├─ Customer: customer2                      │
│ ├─ Payment Status: PAID                     │
│ └─ Ready to Ship                            │
│                                              │
│ SO-003: DELIVERED ✓✓                        │
│ ├─ Customer: customer1                      │
│ └─ Payment Status: PAID                     │
└─────────────────────────────────────────────┘

SHOPPING CART FLOW:
┌─────────────────────────────────────────────┐
│ Customer Adds Items to Cart                 │
├─────────────────────────────────────────────┤
│ Cart 1 (customer1):                         │
│ ├─ Engine Oil Filter x2 @ $10.50            │
│ ├─ Air Filter x2 @ $15.50                   │
│ ├─ Brake Pads x2 @ $55.00                   │
│ └─ Cart Total: $161.00                      │
│                                              │
│ Cart 2 (customer2):                         │
│ ├─ Engine Oil Filter x2 @ $10.50            │
│ ├─ Air Filter x2 @ $15.50                   │
│ ├─ Brake Pads x2 @ $55.00                   │
│ └─ Cart Total: $161.00                      │
└─────────────────────────────────────────────┘
```

---

## 💳 Payment Methods

```
BANK ACCOUNTS (6 Total):

PRIMARY TENANT (ServeIQ Demo Co):
├─ [BANK] Main Operating Account
│  └─ First National Bank | ACC-001234567890
├─ [BANK] Savings Account
│  └─ First National Bank | ACC-009876543210
├─ [ESEWA] eSewa Merchant Account
│  └─ ESEWA-123456
└─ [CASH] Main Cash Register
   └─ Manual Management

SECONDARY TENANT (Parts Center Ltd):
├─ [BANK] Parts Center Bank
│  └─ West Coast Bank | ACC-111222333444
└─ [CASH] Store Cash Box
   └─ Manual Management

PAYMENT METHODS IN USE:
├─ Cash
├─ Card/Credit
├─ UPI
├─ Bank Transfer
└─ Digital Wallets (eSewa)
```

---

## 🔐 Test Credentials

```
┌─────────────────────────────────────────────────────────────┐
│ ADMIN ACCESS (Full Control)                                 │
├─────────────────────────────────────────────────────────────┤
│ USERNAME:     superadmin                                    │
│ PASSWORD:     Admin@123                                     │
│ EMAIL:        superadmin@serveiqdemo.com                    │
│ ROLE:         Super Admin                                   │
│ TENANT:       ServeIQ Demo Co                               │
│ PERMISSIONS:  System-wide                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TENANT ADMIN (Tenant Control)                               │
├─────────────────────────────────────────────────────────────┤
│ USERNAME:     admin                                         │
│ PASSWORD:     Admin@123                                     │
│ EMAIL:        admin@serveiqdemo.com                         │
│ ROLE:         Admin                                         │
│ TENANT:       ServeIQ Demo Co                               │
│ PERMISSIONS:  Tenant-level management                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STAFF ACCESS (Operations)                                   │
├─────────────────────────────────────────────────────────────┤
│ USERNAME:     cashier1                                      │
│ PASSWORD:     Cashier@123                                   │
│ EMAIL:        cashier1@serveiqdemo.com                      │
│ ROLE:         Cashier                                       │
│ PERMISSIONS:  Payment & transaction processing              │
├─────────────────────────────────────────────────────────────┤
│ USERNAME:     inventory1                                    │
│ PASSWORD:     Inventory@123                                 │
│ EMAIL:        inventory1@serveiqdemo.com                    │
│ ROLE:         Inventory Manager                             │
│ PERMISSIONS:  Stock & order management                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CUSTOMER ACCESS (Purchasing)                                │
├─────────────────────────────────────────────────────────────┤
│ USERNAME:     customer1                                     │
│ PASSWORD:     Customer@123                                  │
│ EMAIL:        customer1@example.com                         │
│ ROLE:         Customer                                      │
│ PERMISSIONS:  Browse, cart, orders                          │
├─────────────────────────────────────────────────────────────┤
│ USERNAME:     customer2                                     │
│ PASSWORD:     Customer@123                                  │
│ EMAIL:        customer2@example.com                         │
│ ROLE:         Customer                                      │
│ PERMISSIONS:  Browse, cart, orders                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Model Relationships

```
                    ┌──────────────────┐
                    │ Subscription     │
                    │ Plans (4)        │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Tenant (3)       │
                    │ (Business Org)   │
                    └────┬──────┬──────┘
                         │      │
            ┌────────────┘      └────────────┐
            │                                 │
    ┌───────▼────────┐             ┌────────▼────────┐
    │ Users (13)     │             │ Subscriptions(3)│
    │ All roles      │             │ 365-day plans   │
    └────┬───────────┘             └─────────────────┘
         │
    ┌────┼─────┐
    │    │     │
    ▼    ▼     ▼
  OTP  Cart  SalesOrder
  (3)  (2)    (3)
       │       │
       ▼       ▼
    Items   Items
    (6)      (6)


    ┌──────────────────┐
    │ Branches (6)     │
    │ Locations        │
    └──────────────────┘

    ┌──────────────────┐
    │ Inventory (12)   │
    │ Auto spare parts │
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │ Party (8)        │
    │ Suppliers(4)     │
    │ Customers(4)     │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ PurchaseOrder(3) │
    │ + Items (4)      │
    └──────────────────┘

    ┌──────────────────┐
    │ BankAccount (6)  │
    │ Payment methods  │
    └──────────────────┘

    ┌──────────────────┐
    │ Bills (5)        │
    │ Invoices         │
    └──────────────────┘
```

---

## 🚀 Execution Flow

```
START
  │
  ├─→ seed_subscription_plans() ──→ 4 plans
  │
  ├─→ seed_tenants() ──────────────→ 3 orgs
  │
  ├─→ seed_subscriptions() ────────→ 3 active
  │
  ├─→ seed_users() ────────────────→ 13 users
  │
  ├─→ seed_branches() ─────────────→ 6 locations
  │
  ├─→ seed_parties() ──────────────→ 8 suppliers+customers
  │
  ├─→ seed_inventory() ────────────→ 12 items (with pricing)
  │
  ├─→ seed_purchase_orders() ──────→ 3 POs (+ 4 items)
  │
  ├─→ seed_bank_accounts() ────────→ 6 accounts
  │
  ├─→ seed_bills() ────────────────→ 5 invoices
  │
  ├─→ seed_sales_orders() ─────────→ 3 SOs (+ 6 items)
  │
  ├─→ seed_carts() ────────────────→ 2 carts (+ 6 items)
  │
  ├─→ seed_otp() ──────────────────→ 3 OTP codes
  │
  └─→ SUCCESS! ✓
     (70+ records created)
```

---

## 📈 Data Statistics

```
┌─────────────────────────────────────────────┐
│ TOTAL SEEDED DATA                           │
├─────────────────────────────────────────────┤
│ Models Covered:         13                  │
│ Total Records:          70+                 │
│ Relationships:          Multi-tenant        │
│ Execution Time:         2-5 seconds         │
│ Idempotent:             ✓ Yes              │
│ Database Size:          ~2-3 MB             │
│ Ready for Testing:      ✓ Yes              │
│ Can be Customized:      ✓ Yes              │
└─────────────────────────────────────────────┘
```

---

## 🎯 What You Can Test

```
✓ Multi-tenancy isolation
✓ User role-based access
✓ Inventory management
✓ Order lifecycle
✓ Payment processing
✓ Cart operations
✓ Subscription limits
✓ Branch management
✓ Supplier relationships
✓ Customer interactions
✓ OTP authentication
✓ Bill generation
✓ Reports & analytics
```

---

## 🏃 Quick Action

```bash
# SEED THE DATABASE
python manage.py seed_all

# RESULT: 70+ realistic records created instantly!

# LOGIN WITH
Username: superadmin
Password: Admin@123

# EXPLORE
- Dashboard with all data
- Inventory with pricing
- Orders and transactions
- Users and roles
- Branches and locations
- Parties and contracts
```

---

**Visual Guide Complete! 🎨**

For detailed information, see: `COMPLETE_SUMMARY.md`
