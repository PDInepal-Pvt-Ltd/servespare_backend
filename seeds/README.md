# Seed Data Module

This folder contains centralized seed data for all models in the ServeIQ application.

## Structure

```
seeds/
├── management/
│   └── commands/
│       └── seed_all.py          # Django management command to seed all models
├── seed_data.json               # JSON file with seed data configuration
└── README.md                    # This file
```

## Running Seed Data

### Seed All Models

To seed all models in the database with demo data:

```bash
python manage.py seed_all
```

This will create:
- Subscription Plans (Starter, Professional, Business, Enterprise)
- Tenants (Demo Company 1 & 2)
- Users with different roles (Super Admin, Admin, Cashier, Inventory Manager, Customer)
- Branches
- Parties (Suppliers)
- Inventory Items
- Bank Accounts

## Seed Data Files

### seed_data.json
Contains all seed data configuration in JSON format. You can customize the values here and the `seed_all` command will use them.

### seed_all.py
Django management command that handles the seeding process. It includes:
- `seed_subscription_plans()` - Creates subscription plans
- `seed_tenants()` - Creates tenant/business records
- `seed_users()` - Creates users with different roles
- `seed_branches()` - Creates branches
- `seed_parties()` - Creates suppliers/parties
- `seed_inventory()` - Creates inventory items
- `seed_bank_accounts()` - Creates bank accounts

## Default Credentials

After running `seed_all`, the following test users are created:

| Username | Email | Password | Role |
|----------|-------|----------|------|
| superadmin | superadmin@demo.com | Admin@123 | Super Admin |
| admin | admin@demo.com | Admin@123 | Admin |
| cashier | cashier@demo.com | Cashier@123 | Cashier |
| inventory | inventory@demo.com | Inventory@123 | Inventory Manager |
| customer | customer@demo.com | Customer@123 | Customer |

## Database Constraints

The seeding process is idempotent - you can run `seed_all` multiple times safely:
- Uses `get_or_create()` to avoid duplicate entries
- Only creates new records if they don't already exist
- Updates only happen if you explicitly modify the code

## Customization

To customize seed data:

1. Edit `seed_data.json` with your desired values
2. Update the corresponding seed method in `seed_all.py`
3. Run `python manage.py seed_all`

## Clearing Seed Data

To remove all seed data and reset the database:

```bash
python manage.py flush
python manage.py migrate
python manage.py seed_all
```

## Models Covered

This seed system covers the following models:
- `apps.subscription.models.SubscriptionPlan`
- `apps.tenant.models.Tenant`
- `apps.users.models.User`
- `apps.branch.models.Branch`
- `apps.stock_management.models.Parties`
- `apps.stock_management.models.Inventory`
- `apps.cashandbank.models.BankAccount`

## Future Enhancements

Potential additions:
- Add more complex seeding scenarios (SalesOrders, Bills, PurchaseOrders)
- Create a factory-based seeding system using factory_boy
- Add bulk data generation
- Add CSV import/export functionality
