"""
Seed data for all models in the ServeIQ application.
Run with: python manage.py seed_all
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from apps.users.models import User
from apps.tenant.models import Tenant
from apps.subscription.models import SubscriptionPlan, Subscription
from apps.branch.models import Branch
from apps.stock_management.models import Inventory, Party, PurchaseOrder
from apps.sales.models import SalesOrder, Bill
from apps.cashandbank.models import BankAccount
from apps.carts.models import Cart, CartItem
from apps.otp.models import OTP


class Command(BaseCommand):
    help = 'Seed the database with initial data for all models'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting seed data process...'))
        
        # Seed Subscription Plans
        self.seed_subscription_plans()
        
        # Seed Tenants
        self.seed_tenants()

        # Seed Branches
        self.seed_branches()
        
        # Seed Subscriptions
        self.seed_subscriptions()
        
        # Seed Users
        self.seed_users()
        
        # Seed Parties (Suppliers & Customers)
        self.seed_parties()
        
        # Seed Inventory
        self.seed_inventory()
        
        # Seed Purchase Orders
        self.seed_purchase_orders()
        
        # Seed Bank Accounts
        self.seed_bank_accounts()
        
        # Seed Bills
        self.seed_bills()
        
        # Seed Sales Orders
        self.seed_sales_orders()
        
        # Seed Carts
        self.seed_carts()
        
        # Seed OTP
        self.seed_otp()
        
        self.stdout.write(self.style.SUCCESS('✓ All seed data has been created successfully!'))

    def seed_branches(self):
        """Seed branches for tenants"""
        self.stdout.write('Seeding Branches...')

        tenants = Tenant.objects.all()

        if not tenants:
            self.stdout.write("  - No tenants found, skipping branches seeding")
            return

        primary_tenant = tenants[0]
        secondary_tenant = tenants[1] if len(tenants) > 1 else primary_tenant

        branches_data = [
            {
                'tenant': primary_tenant,
                'branch_name': 'Main Branch',
                'branch_code': 'MAIN001',
                'Address': '123 Main Street, New York, NY',
                'city': 'New York',
                'state': 'NY',
                'phone': '+1234567890',
                'Email': 'main@serveiqdemo.com'
            },
            {
                'tenant': primary_tenant,
                'branch_name': 'Warehouse A',
                'branch_code': 'WH001',
                'Address': '456 Warehouse Road, Newark, NJ',
                'city': 'Newark',
                'state': 'NJ',
                'phone': '+1231231234',
                'Email': 'warehouse@serveiqdemo.com'
            }
        ]

        if len(tenants) > 1:
            branches_data.append({
                'tenant': secondary_tenant,
                'branch_name': 'Parts Center Branch',
                'branch_code': 'PC001',
                'Address': '789 Parts Ave, Los Angeles, CA',
                'city': 'Los Angeles',
                'state': 'CA',
                'phone': '+1987654321',
                'Email': 'branch@partscenter.com'
            })

        for branch_data in branches_data:
            branch, created = Branch.objects.get_or_create(
                branch_code=branch_data['branch_code'],
                defaults=branch_data
            )
            if created:
                self.stdout.write(f"  ✓ Created branch: {branch.branch_name}")
            else:
                self.stdout.write(f"  - Branch already exists: {branch.branch_name}")

    def seed_subscription_plans(self):
        """Seed subscription plans"""
        self.stdout.write('Seeding Subscription Plans...')
        
        plans = [
            {
                'plan_name': 'Starter',
                'plan_price': Decimal('9.99'),
                'no_of_user': 1,
                'no_of_branch': 1,
                'support_type': 'email'
            },
            {
                'plan_name': 'Professional',
                'plan_price': Decimal('29.99'),
                'no_of_user': 5,
                'no_of_branch': 2,
                'support_type': 'email'
            },
            {
                'plan_name': 'Business',
                'plan_price': Decimal('99.99'),
                'no_of_user': 20,
                'no_of_branch': 5,
                'support_type': 'phone'
            },
            {
                'plan_name': 'Enterprise',
                'plan_price': Decimal('299.99'),
                'no_of_user': 100,
                'no_of_branch': 20,
                'support_type': 'ticket'
            }
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                plan_name=plan_data['plan_name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f"  ✓ Created plan: {plan.plan_name}")
            else:
                self.stdout.write(f"  - Plan already exists: {plan.plan_name}")

    def seed_tenants(self):
        """Seed tenants"""
        self.stdout.write('Seeding Tenants...')
        
        starter_plan = SubscriptionPlan.objects.filter(plan_name='Starter').first()
        pro_plan = SubscriptionPlan.objects.filter(plan_name='Professional').first()
        business_plan = SubscriptionPlan.objects.filter(plan_name='Business').first()
        
        tenants = [
            {
                'business_name': 'ServeIQ Demo Co',
                'email': 'admin@serveiqdemo.com',
                'phone': '+1234567890',
                'package': starter_plan,
                'status': 'approved'
            },
            {
                'business_name': 'Parts Center Ltd',
                'email': 'admin@partscenter.com',
                'phone': '+9876543210',
                'package': pro_plan,
                'status': 'approved'
            },
            {
                'business_name': 'Auto Spares Global',
                'email': 'admin@autospares.com',
                'phone': '+1122334455',
                'package': business_plan,
                'status': 'approved'
            }
        ]
        
        for tenant_data in tenants:
            tenant, created = Tenant.objects.get_or_create(
                email=tenant_data['email'],
                defaults=tenant_data
            )
            if created:
                self.stdout.write(f"  ✓ Created tenant: {tenant.business_name}")
            else:
                self.stdout.write(f"  - Tenant already exists: {tenant.business_name}")

    def seed_subscriptions(self):
        """Seed subscriptions"""
        self.stdout.write('Seeding Subscriptions...')
        
        tenants = Tenant.objects.all()
        plans = SubscriptionPlan.objects.all()
        
        if not tenants or not plans:
            self.stdout.write("  - No tenants or plans found, skipping subscriptions")
            return
        
        for tenant in tenants:
            plan = tenant.package or plans.first()
            subscription_date = date.today()
            finish_date = subscription_date + timedelta(days=365)
            renew_date = finish_date
            
            subscription, created = Subscription.objects.get_or_create(
                tenant=tenant,
                subscription_plan=plan,
                subscription_date=subscription_date,
                defaults={
                    'finish_date': finish_date,
                    'renew_date': renew_date
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created subscription for {tenant.business_name}")
            else:
                self.stdout.write(f"  - Subscription already exists for {tenant.business_name}")

    def seed_users(self):
        """Seed users with different roles"""
        self.stdout.write('Seeding Users...')
        
        tenants = list(Tenant.objects.all())
        if not tenants:
            self.stdout.write("  - No tenants found, skipping user seeding")
            return
        
        primary_tenant = tenants[0]
        secondary_tenant = tenants[1] if len(tenants) > 1 else tenants[0]
        tertiary_tenant = tenants[2] if len(tenants) > 2 else tenants[0]
        
        users_data = [
            # Primary Tenant - Admin Users
            {
                'username': 'superadmin',
                'email': 'superadmin@serveiqdemo.com',
                'password': 'SuperAdmin@123',
                'first_name': 'Super',
                'last_name': 'Admin',
                'full_name': 'Super Admin User',
                'phone': '+1111111111',
                'location': 'Headquarters',
                'role': User.Role.SUPER_ADMIN,
                'status': User.Status.ACTIVE,
                'is_staff': True,
                'is_superuser': True,
                'tenant': primary_tenant,
                'must_change_password': False
            },
            {
                'username': 'admin',
                'email': 'admin@serveiqdemo.com',
                'password': 'Admin@123',
                'first_name': 'John',
                'last_name': 'Manager',
                'full_name': 'John Manager',
                'phone': '+2222222222',
                'location': 'Downtown Office',
                'role': User.Role.ADMIN,
                'status': User.Status.ACTIVE,
                'is_staff': True,
                'tenant': primary_tenant,
                'must_change_password': True
            },
            {
                'username': 'subadmin',
                'email': 'subadmin@serveiqdemo.com',
                'password': 'SubAdmin@123',
                'first_name': 'Sarah',
                'last_name': 'Supervisor',
                'full_name': 'Sarah Supervisor',
                'phone': '+1515151515',
                'location': 'Main Branch',
                'role': User.Role.SUB_ADMIN,
                'status': User.Status.ACTIVE,
                'is_staff': True,
                'tenant': primary_tenant,
                'must_change_password': True
            },
            {
                'username': 'cashier1',
                'email': 'cashier1@serveiqdemo.com',
                'password': 'Cashier@123',
                'first_name': 'Mike',
                'last_name': 'Cash',
                'full_name': 'Mike Cash Manager',
                'phone': '+3333333333',
                'location': 'Main Office',
                'role': User.Role.CASHIER,
                'status': User.Status.ACTIVE,
                'tenant': primary_tenant,
                'must_change_password': True
            },
            {
                'username': 'cashier2',
                'email': 'cashier2@serveiqdemo.com',
                'password': 'Cashier@123',
                'first_name': 'Emma',
                'last_name': 'Finance',
                'full_name': 'Emma Finance Officer',
                'phone': '+3344445555',
                'location': 'Branch Office',
                'role': User.Role.CASHIER,
                'status': User.Status.ACTIVE,
                'tenant': primary_tenant,
                'must_change_password': True
            },
            {
                'username': 'inventory1',
                'email': 'inventory1@serveiqdemo.com',
                'password': 'Inventory@123',
                'first_name': 'David',
                'last_name': 'Stock',
                'full_name': 'David Stock Manager',
                'phone': '+4444444444',
                'location': 'Warehouse A',
                'role': User.Role.INVENTORY_MANAGER,
                'status': User.Status.ACTIVE,
                'tenant': primary_tenant,
                'must_change_password': True
            },
            {
                'username': 'inventory2',
                'email': 'inventory2@serveiqdemo.com',
                'password': 'Inventory@123',
                'first_name': 'Lisa',
                'last_name': 'Inventory',
                'full_name': 'Lisa Inventory Officer',
                'phone': '+4455556666',
                'location': 'Warehouse B',
                'role': User.Role.INVENTORY_MANAGER,
                'status': User.Status.ACTIVE,
                'tenant': primary_tenant,
                'must_change_password': True
            },
            {
                'username': 'customer1',
                'email': 'customer1@example.com',
                'password': 'Customer@123',
                'first_name': 'Robert',
                'last_name': 'Brown',
                'full_name': 'Robert Brown',
                'phone': '+5555555555',
                'location': 'City Center',
                'role': User.Role.CUSTOMER,
                'status': User.Status.ACTIVE,
                'tenant': primary_tenant,
                'must_change_password': False
            },
            {
                'username': 'customer2',
                'email': 'customer2@example.com',
                'password': 'Customer@123',
                'first_name': 'Patricia',
                'last_name': 'Garcia',
                'full_name': 'Patricia Garcia',
                'phone': '+5566667777',
                'location': 'Downtown',
                'role': User.Role.CUSTOMER,
                'status': User.Status.ACTIVE,
                'tenant': primary_tenant,
                'must_change_password': False
            },
            # Secondary Tenant
            {
                'username': 'admin2',
                'email': 'admin@partscenter.com',
                'password': 'Admin@123',
                'first_name': 'Tom',
                'last_name': 'Wilson',
                'full_name': 'Tom Wilson',
                'phone': '+6666666666',
                'location': 'Parts Center HQ',
                'role': User.Role.ADMIN,
                'status': User.Status.ACTIVE,
                'is_staff': True,
                'tenant': secondary_tenant,
                'must_change_password': True
            },
            {
                'username': 'inventory3',
                'email': 'inventory@partscenter.com',
                'password': 'Inventory@123',
                'first_name': 'James',
                'last_name': 'Stewart',
                'full_name': 'James Stewart',
                'phone': '+7777777777',
                'location': 'Parts Storage',
                'role': User.Role.INVENTORY_MANAGER,
                'status': User.Status.ACTIVE,
                'tenant': secondary_tenant,
                'must_change_password': True
            },
            # Tertiary Tenant
            {
                'username': 'admin3',
                'email': 'admin@autospares.com',
                'password': 'Admin@123',
                'first_name': 'Chris',
                'last_name': 'Anderson',
                'full_name': 'Chris Anderson',
                'phone': '+8888888888',
                'location': 'Auto Spares Office',
                'role': User.Role.ADMIN,
                'status': User.Status.ACTIVE,
                'is_staff': True,
                'tenant': tertiary_tenant,
                'must_change_password': True
            }
        ]
        
        for user_data in users_data:
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"  ✓ Created user: {user.get_full_name()} ({user.get_role_display()})")
            else:
                self.stdout.write(f"  - User already exists: {user.get_full_name()}")

    def seed_parties(self):
        """Seed parties (suppliers and customers)"""
        self.stdout.write('Seeding Parties...')
        
        tenants = Tenant.objects.all()
        
        if not tenants:
            self.stdout.write("  - No tenants found, skipping parties seeding")
            return
        
        primary_tenant = tenants[0]
        secondary_tenant = tenants[1] if len(tenants) > 1 else tenants[0]
        
        main_branch = Branch.objects.filter(branch_code='MAIN001').first()
        warehouse_branch = Branch.objects.filter(branch_code='WH001').first() or main_branch
        secondary_branch = Branch.objects.filter(branch_code='PC001').first() or main_branch

        parties_data = [
            # Suppliers for Primary Tenant
            {
                'party_type': 'supplier',
                'party_name': 'Global Auto Parts Supplier',
                'contact_person': 'Mr. Kumar',
                'email': 'contact@globalauto.com',
                'phone': '+1111111111',
                'address': '100 Supplier Lane',
                'city': 'Newark',
                'state_province': 'NJ',
                'pan_number': 'AABBH1234A',
                'payment_terms': 'cash',
                'branch': warehouse_branch
            },
            {
                'party_type': 'supplier',
                'party_name': 'Premium Parts International',
                'contact_person': 'Ms. Johnson',
                'email': 'sales@premiumparts.com',
                'phone': '+2222222222',
                'address': '200 Industrial Ave',
                'city': 'Jersey City',
                'state_province': 'NJ',
                'pan_number': 'CCDDP5678B',
                'payment_terms': '15_day_credit',
                'branch': warehouse_branch
            },
            {
                'party_type': 'supplier',
                'party_name': 'TechSpares Manufacturing',
                'contact_person': 'Dr. Patel',
                'email': 'sales@techspares.com',
                'phone': '+3333333333',
                'address': '300 Tech Park',
                'city': 'Edison',
                'state_province': 'NJ',
                'pan_number': 'EEFFM9012C',
                'payment_terms': '30_day_credit',
                'branch': warehouse_branch
            },
            {
                'party_type': 'supplier',
                'party_name': 'Economy Parts Ltd',
                'contact_person': 'Mr. Singh',
                'email': 'info@economyparts.com',
                'phone': '+4444444444',
                'address': '400 Budget Road',
                'city': 'Paterson',
                'state_province': 'NJ',
                'pan_number': 'GGHHR3456D',
                'payment_terms': '7_day_credit',
                'branch': warehouse_branch
            },
            # Customers for Primary Tenant
            {
                'party_type': 'customer',
                'customer_type': 'retailer',
                'party_name': 'City Auto Retail Store',
                'contact_person': 'Mr. Williams',
                'email': 'manager@cityauto.com',
                'phone': '+5555555555',
                'address': '500 Retail Plaza',
                'city': 'New York',
                'state_province': 'NY',
                'payment_terms': 'cash',
                'branch': main_branch
            },
            {
                'party_type': 'customer',
                'customer_type': 'workshop',
                'party_name': 'Quick Fix Auto Workshop',
                'contact_person': 'Mr. Martinez',
                'email': 'quickfix@workshop.com',
                'phone': '+6666666666',
                'address': '600 Service Road',
                'city': 'New York',
                'state_province': 'NY',
                'payment_terms': '15_day_credit',
                'branch': main_branch
            },
            {
                'party_type': 'customer',
                'customer_type': 'distributor',
                'party_name': 'National Auto Distributor',
                'contact_person': 'Ms. Thompson',
                'email': 'sales@nationaldist.com',
                'phone': '+7777777777',
                'address': '700 Distribution Ave',
                'city': 'Newark',
                'state_province': 'NJ',
                'payment_terms': '30_day_credit',
                'branch': warehouse_branch
            },
            {
                'party_type': 'customer',
                'customer_type': 'wholesaler',
                'party_name': 'Bulk Auto Wholesaler',
                'contact_person': 'Mr. Davis',
                'email': 'bulk@wholesaler.com',
                'phone': '+8888888888',
                'address': '800 Wholesale Drive',
                'city': 'Paterson',
                'state_province': 'NJ',
                'payment_terms': '45_day_credit',
                'branch': warehouse_branch
            }
        ]
        
        if len(tenants) > 1:
            parties_data.extend([
                {
                    'party_type': 'supplier',
                    'party_name': 'West Coast Auto Supplies',
                    'contact_person': 'Mr. Anderson',
                    'email': 'supply@westcoast.com',
                    'phone': '+9999999999',
                    'address': '900 Supply Lane',
                    'city': 'Los Angeles',
                    'state_province': 'CA',
                    'pan_number': 'IIJES7890E',
                    'payment_terms': 'cash',
                    'branch': secondary_branch
                }
            ])
        
        for party_data in parties_data:
            party, created = Party.objects.get_or_create(
                party_name=party_data['party_name'],
                defaults=party_data
            )
            if created:
                self.stdout.write(f"  ✓ Created party: {party.party_name} ({party.get_party_type_display()})")
            else:
                self.stdout.write(f"  - Party already exists: {party.party_name}")

    def seed_inventory(self):
        """Seed inventory items with comprehensive data"""
        self.stdout.write('Seeding Inventory...')
        
        tenants = Tenant.objects.all()
        suppliers = Party.objects.filter(party_type='supplier')
        main_branch = Branch.objects.filter(branch_code='MAIN001').first()
        warehouse_branch = Branch.objects.filter(branch_code='WH001').first() or main_branch
        
        if not tenants or not suppliers:
            self.stdout.write("  - No tenants or suppliers found, skipping inventory seeding")
            return
        
        inventory_items = [
            {
                'item_name': 'Engine Oil Filter Premium',
                'part_number': 'OIL-FIL-001',
                'barcode': '8901234567001',
                'hsn_code': '84211190',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('150.00'),
                'min_stock_level': Decimal('20.00'),
                'price': Decimal('8.50'),
                'mrp': Decimal('12.00'),
                'retail_pricing': Decimal('10.50'),
                'wholesale_price': Decimal('9.00'),
                'distributor_price': Decimal('8.50'),
                'storage_location': 'Shelf A1',
                'warranty_period': '3_month',
                'vehicle_bike_details': 'Maruti Swift, Hyundai i20',
                'model': 'Standard Filter',
                'type': 'Engine Component',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Air Filter High Flow',
                'part_number': 'AIR-FIL-002',
                'barcode': '8901234567002',
                'hsn_code': '84211210',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('200.00'),
                'min_stock_level': Decimal('25.00'),
                'price': Decimal('12.99'),
                'mrp': Decimal('18.00'),
                'retail_pricing': Decimal('15.50'),
                'wholesale_price': Decimal('14.00'),
                'distributor_price': Decimal('12.99'),
                'storage_location': 'Shelf A2',
                'warranty_period': '6_month',
                'vehicle_bike_details': 'Honda CR-V, Toyota Innova',
                'model': 'High Flow',
                'type': 'Air Intake',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Brake Pads Set Ceramic',
                'part_number': 'BRAKE-PAD-003',
                'barcode': '8901234567003',
                'hsn_code': '87083090',
                'category': 'local',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('75.00'),
                'min_stock_level': Decimal('10.00'),
                'price': Decimal('45.00'),
                'mrp': Decimal('65.00'),
                'retail_pricing': Decimal('55.00'),
                'wholesale_price': Decimal('48.00'),
                'distributor_price': Decimal('45.00'),
                'storage_location': 'Shelf B1',
                'warranty_period': '12_month',
                'vehicle_bike_details': 'Tata Nexon, Mahindra XUV',
                'model': 'Ceramic Pro',
                'type': 'Braking System',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Spark Plug Iridium',
                'part_number': 'SPARK-001',
                'barcode': '8901234567004',
                'hsn_code': '85019090',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('300.00'),
                'min_stock_level': Decimal('50.00'),
                'price': Decimal('5.99'),
                'mrp': Decimal('9.00'),
                'retail_pricing': Decimal('7.50'),
                'wholesale_price': Decimal('6.50'),
                'distributor_price': Decimal('5.99'),
                'storage_location': 'Shelf C1',
                'warranty_period': '9_month',
                'vehicle_bike_details': 'Honda Civic, Hyundai Elantra',
                'model': 'Iridium',
                'type': 'Ignition',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Battery 12V 50Ah Premium',
                'part_number': 'BATT-12V-001',
                'barcode': '8901234567005',
                'hsn_code': '85072090',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('30.00'),
                'min_stock_level': Decimal('5.00'),
                'price': Decimal('120.00'),
                'mrp': Decimal('180.00'),
                'retail_pricing': Decimal('150.00'),
                'wholesale_price': Decimal('135.00'),
                'distributor_price': Decimal('120.00'),
                'storage_location': 'Storage D1',
                'warranty_period': '24_month',
                'vehicle_bike_details': 'Sedan, SUV (all models)',
                'model': 'Premium 50Ah',
                'type': 'Electrical',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Alternator 90A Durable',
                'part_number': 'ALT-90-001',
                'barcode': '8901234567006',
                'hsn_code': '85041900',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('20.00'),
                'min_stock_level': Decimal('3.00'),
                'price': Decimal('350.00'),
                'mrp': Decimal('550.00'),
                'retail_pricing': Decimal('475.00'),
                'wholesale_price': Decimal('400.00'),
                'distributor_price': Decimal('350.00'),
                'storage_location': 'Storage D2',
                'warranty_period': '24_month',
                'vehicle_bike_details': 'Heavy vehicles, Trucks',
                'model': '90A Standard',
                'type': 'Charging System',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Water Pump Assembly Complete',
                'part_number': 'PUMP-WATER-001',
                'barcode': '8901234567007',
                'hsn_code': '84131000',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('15.00'),
                'min_stock_level': Decimal('2.00'),
                'price': Decimal('85.00'),
                'mrp': Decimal('140.00'),
                'retail_pricing': Decimal('115.00'),
                'wholesale_price': Decimal('98.00'),
                'distributor_price': Decimal('85.00'),
                'storage_location': 'Storage E1',
                'warranty_period': '12_month',
                'vehicle_bike_details': 'Diesel engines, Petrol engines',
                'model': 'Complete Assembly',
                'type': 'Cooling System',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Clutch Plate Heavy Duty',
                'part_number': 'CLUTCH-001',
                'barcode': '8901234567008',
                'hsn_code': '87083011',
                'category': 'local',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('50.00'),
                'min_stock_level': Decimal('8.00'),
                'price': Decimal('65.00'),
                'mrp': Decimal('110.00'),
                'retail_pricing': Decimal('85.00'),
                'wholesale_price': Decimal('72.00'),
                'distributor_price': Decimal('65.00'),
                'storage_location': 'Shelf B2',
                'warranty_period': '6_month',
                'vehicle_bike_details': 'Manual transmission vehicles',
                'model': 'Heavy Duty',
                'type': 'Transmission',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Tire Tube 17 inch MRF',
                'part_number': 'TIRE-17-001',
                'barcode': '8901234567009',
                'hsn_code': '40121100',
                'category': 'local',
                'vehicle_type': 'two_wheeler',
                'quantity': Decimal('100.00'),
                'min_stock_level': Decimal('15.00'),
                'price': Decimal('15.00'),
                'mrp': Decimal('25.00'),
                'retail_pricing': Decimal('20.00'),
                'wholesale_price': Decimal('17.50'),
                'distributor_price': Decimal('15.00'),
                'storage_location': 'Shelf C2',
                'warranty_period': '3_month',
                'vehicle_bike_details': 'Motorcycles, Scooters',
                'model': '17 inch',
                'type': 'Tires & Tubes',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Wiper Blade Assembly Bosch',
                'part_number': 'WIPER-001',
                'barcode': '8901234567010',
                'hsn_code': '87083030',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('80.00'),
                'min_stock_level': Decimal('12.00'),
                'price': Decimal('22.50'),
                'mrp': Decimal('35.00'),
                'retail_pricing': Decimal('28.00'),
                'wholesale_price': Decimal('25.00'),
                'distributor_price': Decimal('22.50'),
                'storage_location': 'Shelf F1',
                'warranty_period': '1_month',
                'vehicle_bike_details': 'All car models',
                'model': 'Bosch Premium',
                'type': 'Wipers',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Radiator Hose Silicone',
                'part_number': 'RAD-HOSE-001',
                'barcode': '8901234567011',
                'hsn_code': '87089090',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('60.00'),
                'min_stock_level': Decimal('10.00'),
                'price': Decimal('35.00'),
                'mrp': Decimal('60.00'),
                'retail_pricing': Decimal('48.00'),
                'wholesale_price': Decimal('40.00'),
                'distributor_price': Decimal('35.00'),
                'storage_location': 'Shelf D1',
                'warranty_period': '6_month',
                'vehicle_bike_details': 'All vehicles',
                'model': 'Silicone',
                'type': 'Cooling',
                'party': suppliers.first(),
                'branch': warehouse_branch
            },
            {
                'item_name': 'Transmission Fluid ATF',
                'part_number': 'TRANS-FLUID-001',
                'barcode': '8901234567012',
                'hsn_code': '27101990',
                'category': 'original',
                'vehicle_type': 'four_wheeler',
                'quantity': Decimal('120.00'),
                'min_stock_level': Decimal('20.00'),
                'price': Decimal('450.00'),
                'mrp': Decimal('800.00'),
                'retail_pricing': Decimal('650.00'),
                'wholesale_price': Decimal('550.00'),
                'distributor_price': Decimal('450.00'),
                'storage_location': 'Storage F1',
                'warranty_period': 'no_warranty',
                'vehicle_bike_details': 'Automatic transmission vehicles',
                'model': 'Premium ATF',
                'type': 'Fluids',
                'party': suppliers.first(),
                'branch': warehouse_branch
            }
        ]
        
        for item_data in inventory_items:
            item, created = Inventory.objects.get_or_create(
                part_number=item_data['part_number'],
                defaults=item_data
            )
            if created:
                self.stdout.write(f"  ✓ Created inventory: {item.item_name} ({item.part_number})")
            else:
                self.stdout.write(f"  - Inventory already exists: {item.item_name}")

    def seed_purchase_orders(self):
        """Seed purchase orders with items"""
        self.stdout.write('Seeding Purchase Orders...')
        
        from apps.stock_management.models import PurchaseOrderItem
        
        suppliers = Party.objects.filter(party_type='supplier')
        inventory = Inventory.objects.all()
        main_branch = Branch.objects.filter(branch_code='MAIN001').first()
        warehouse_branch = Branch.objects.filter(branch_code='WH001').first() or main_branch
        
        if not suppliers or not inventory:
            self.stdout.write("  - No suppliers or inventory found, skipping purchase orders seeding")
            return
        
        po_data = [
            {
                'po_number': 'PO-2025-001',
                'status': 'ordered',
                'supplier': suppliers.first(),
                'branch': warehouse_branch,
                'order_date': date.today() - timedelta(days=7),
                'expected_delivery_date': date.today() + timedelta(days=7),
                'notes': 'Urgent order for stock replenishment',
                'terms_and_condition': 'Net 30 payment terms',
                'items': [
                    {
                        'item_name': inventory[0].item_name,
                        'part_number': inventory[0].part_number,
                        'quantity': Decimal('50.00'),
                        'unit_price': inventory[0].price,
                        'tax': Decimal('18.00'),
                        'discount_description': 'Bulk discount 5%',
                        'branch': warehouse_branch
                    },
                    {
                        'item_name': inventory[1].item_name,
                        'part_number': inventory[1].part_number,
                        'quantity': Decimal('40.00'),
                        'unit_price': inventory[1].price,
                        'tax': Decimal('18.00'),
                        'discount_description': None,
                        'branch': warehouse_branch
                    }
                ]
            },
            {
                'po_number': 'PO-2025-002',
                'status': 'received',
                'supplier': suppliers.last() if suppliers.count() > 1 else suppliers.first(),
                'branch': warehouse_branch,
                'order_date': date.today() - timedelta(days=20),
                'expected_delivery_date': date.today() - timedelta(days=5),
                'notes': 'Regular stock replenishment',
                'terms_and_condition': 'Net 30 payment terms',
                'items': [
                    {
                        'item_name': inventory[2].item_name,
                        'part_number': inventory[2].part_number,
                        'quantity': Decimal('30.00'),
                        'unit_price': inventory[2].price,
                        'tax': Decimal('18.00'),
                        'discount_description': None,
                        'branch': warehouse_branch
                    }
                ]
            },
            {
                'po_number': 'PO-2025-003',
                'status': 'draft',
                'supplier': suppliers.first(),
                'branch': warehouse_branch,
                'order_date': date.today(),
                'expected_delivery_date': date.today() + timedelta(days=14),
                'notes': 'Draft order pending approval',
                'terms_and_condition': 'Net 45 payment terms',
                'items': [
                    {
                        'item_name': inventory[3].item_name,
                        'part_number': inventory[3].part_number,
                        'quantity': Decimal('60.00'),
                        'unit_price': inventory[3].price,
                        'tax': Decimal('18.00'),
                        'discount_description': None,
                        'branch': warehouse_branch
                    }
                ]
            }
        ]
        
        for po in po_data:
            items_data = po.pop('items', [])
            
            purchase_order, created = PurchaseOrder.objects.get_or_create(
                po_number=po['po_number'],
                defaults=po
            )
            
            if created:
                self.stdout.write(f"  ✓ Created purchase order: {purchase_order.po_number}")
                
                # Create PO items
                for item_data in items_data:
                    PurchaseOrderItem.objects.get_or_create(
                        purchase_order=purchase_order,
                        item_name=item_data['item_name'],
                        part_number=item_data['part_number'],
                        defaults={
                            'quantity': item_data['quantity'],
                            'unit_price': item_data['unit_price'],
                            'tax': item_data['tax'],
                            'discount_description': item_data.get('discount_description'),
                            'branch': item_data.get('branch')
                        }
                    )
                    self.stdout.write(f"    - Added item: {item_data['item_name']}")
            else:
                self.stdout.write(f"  - Purchase order already exists: {purchase_order.po_number}")

    def seed_bank_accounts(self):
        """Seed bank accounts"""
        self.stdout.write('Seeding Bank Accounts...')
        
        tenants = Tenant.objects.all()
        main_branch = Branch.objects.filter(branch_code='MAIN001').first()
        warehouse_branch = Branch.objects.filter(branch_code='WH001').first() or main_branch
        
        if not tenants:
            self.stdout.write("  - No tenants found, skipping bank accounts seeding")
            return
        
        primary_tenant = tenants[0]
        secondary_tenant = tenants[1] if len(tenants) > 1 else tenants[0]
        
        accounts = [
            {
                'account_type': 'bank_account',
                'account_name': 'Main Operating Account',
                'bank_name': 'First National Bank',
                'account_number': 'ACC-001234567890',
                'account_holders_name': 'ServeIQ Demo Co',
                'branch': main_branch
            },
            {
                'account_type': 'bank_account',
                'account_name': 'Savings Account',
                'bank_name': 'First National Bank',
                'account_number': 'ACC-009876543210',
                'account_holders_name': 'ServeIQ Demo Co',
                'branch': main_branch
            },
            {
                'account_type': 'esewa',
                'account_name': 'eSewa Merchant Account',
                'account_number': 'ESEWA-123456',
                'account_holders_name': 'ServeIQ Demo Co',
                'branch': main_branch
            },
            {
                'account_type': 'cash',
                'account_name': 'Main Cash Register',
                'account_holders_name': 'Cash Management',
                'branch': main_branch
            }
        ]
        
        if len(tenants) > 1:
            accounts.extend([
                {
                    'account_type': 'bank_account',
                    'account_name': 'Parts Center Bank',
                    'bank_name': 'West Coast Bank',
                    'account_number': 'ACC-111222333444',
                    'account_holders_name': 'Parts Center Ltd',
                    'branch': warehouse_branch
                },
                {
                    'account_type': 'cash',
                    'account_name': 'Store Cash Box',
                    'account_holders_name': 'Parts Center Ltd',
                    'branch': warehouse_branch
                }
            ])
        
        for account_data in accounts:
            account, created = BankAccount.objects.get_or_create(
                account_number=account_data.get('account_number', account_data['account_name']),
                defaults=account_data
            )
            if created:
                self.stdout.write(f"  ✓ Created bank account: {account.account_name}")
            else:
                self.stdout.write(f"  - Bank account already exists: {account.account_name}")

    def seed_bills(self):
        """Seed bills/invoices"""
        self.stdout.write('Seeding Bills...')
        
        main_branch = Branch.objects.filter(branch_code='MAIN001').first()

        bills_data = [
            {
                'customer_name': 'ABC Auto Workshop',
                'address': '123 Workshop Lane, New York, NY 10001',
                'phone_numbers': '+1111111111, +2222222222',
                'pan_vat_number': 'AABBH1234A',
                'customer_type': 'workshop',
                'branch': main_branch
            },
            {
                'customer_name': 'Quick Fix Retail',
                'address': '456 Retail Plaza, New York, NY 10002',
                'phone_numbers': '+3333333333',
                'pan_vat_number': 'CCDDP5678B',
                'customer_type': 'retail',
                'branch': main_branch
            },
            {
                'customer_name': 'Premium Parts Wholesaler',
                'address': '789 Wholesale Drive, Newark, NJ 07101',
                'phone_numbers': '+4444444444, +5555555555',
                'pan_vat_number': 'EEFFM9012C',
                'customer_type': 'wholesaler',
                'branch': main_branch
            },
            {
                'customer_name': 'National Auto Distributor',
                'address': '321 Distribution Ave, Newark, NJ 07102',
                'phone_numbers': '+6666666666',
                'pan_vat_number': 'GGHHR3456D',
                'customer_type': 'distributor',
                'branch': main_branch
            },
            {
                'customer_name': 'Regional Parts Retailer',
                'address': '654 Retail Road, Jersey City, NJ 07302',
                'phone_numbers': '+7777777777, +8888888888',
                'pan_vat_number': 'IIJJS7890E',
                'customer_type': 'retailer',
                'branch': main_branch
            }
        ]
        
        for bill_data in bills_data:
            bill, created = Bill.objects.get_or_create(
                customer_name=bill_data['customer_name'],
                defaults=bill_data
            )
            if created:
                self.stdout.write(f"  ✓ Created bill: {bill.customer_name} ({bill.get_customer_type_display()})")
            else:
                self.stdout.write(f"  - Bill already exists: {bill.customer_name}")

    def seed_sales_orders(self):
        """Seed sales orders with items"""
        self.stdout.write('Seeding Sales Orders...')
        
        from apps.sales.models import SalesOrderItem
        
        customers = User.objects.filter(role=User.Role.CUSTOMER)
        inventory = Inventory.objects.all()
        main_branch = Branch.objects.filter(branch_code='MAIN001').first()
        
        if not customers or not inventory:
            self.stdout.write("  - No customers or inventory found, skipping sales orders seeding")
            return
        
        for idx, customer in enumerate(customers[:3]):
            order_status_list = ['confirmed', 'packed', 'delivered']
            payment_status_list = ['pending', 'paid', 'paid']
            payment_methods = ['cash', 'card', 'upi']
            
            order_data = {
                'customer': customer,
                'order_status': order_status_list[idx % len(order_status_list)],
                'subtotal': Decimal('500.00'),
                'discount_percentage': Decimal('5.00') if idx % 2 == 0 else Decimal('0.00'),
                'discount_amount': Decimal('25.00') if idx % 2 == 0 else Decimal('0.00'),
                'tax_percentage': Decimal('18.00'),
                'tax_amount': Decimal('85.50'),
                'shipping_charges': Decimal('50.00'),
                'total_amount': Decimal('610.50'),
                'payment_status': payment_status_list[idx % len(payment_status_list)],
                'payment_method': payment_methods[idx % len(payment_methods)],
                'paid_amount': Decimal('610.50') if idx % 2 == 0 else Decimal('300.00'),
                'delivery_address': f'{customer.location}, {customer.phone}',
                'delivery_city': 'New York',
                'delivery_state': 'NY',
                'delivery_pincode': '10001',
                'expected_delivery_date': date.today() + timedelta(days=5),
                'branch': main_branch
            }
            
            sales_order, created = SalesOrder.objects.get_or_create(
                customer=customer,
                order_status=order_data['order_status'],
                defaults=order_data
            )
            
            if created:
                self.stdout.write(f"  ✓ Created sales order: {sales_order.order_number}")
                
                # Create Sales Order Items
                for item_idx, inv_item in enumerate(inventory[:2]):
                    SalesOrderItem.objects.get_or_create(
                        order=sales_order,
                        inventory=inv_item,
                        defaults={
                            'quantity': Decimal('2.00') + Decimal(item_idx),
                            'unit_price': inv_item.retail_pricing,
                            'is_active': True,
                            'branch': main_branch
                        }
                    )
                    self.stdout.write(f"    - Added item: {inv_item.item_name}")
            else:
                self.stdout.write(f"  - Sales order already exists for {customer.username}")

    def seed_carts(self):
        """Seed shopping carts with items"""
        self.stdout.write('Seeding Carts...')
        
        customers = User.objects.filter(role=User.Role.CUSTOMER)
        inventory_items = Inventory.objects.all()
        
        if not customers or not inventory_items:
            self.stdout.write("  - No customers or inventory found, skipping carts seeding")
            return
        
        for customer in customers[:2]:
            cart, created = Cart.objects.get_or_create(
                user=customer,
                defaults={'is_active': True}
            )
            
            if created:
                self.stdout.write(f"  ✓ Created cart for: {customer.get_full_name()}")
                
                # Add items to cart
                for item in inventory_items[:3]:
                    cart_item, item_created = CartItem.objects.get_or_create(
                        cart=cart,
                        inventory=item,
                        defaults={
                            'quantity': Decimal('2.00'),
                            'price': item.retail_pricing,
                            'is_active': True
                        }
                    )
                    if item_created:
                        self.stdout.write(f"    - Added {item.item_name} to cart (Price: {item.retail_pricing})")
            else:
                self.stdout.write(f"  - Cart already exists for: {customer.get_full_name()}")

    def seed_otp(self):
        """Seed OTP records for users"""
        self.stdout.write('Seeding OTP Records...')
        
        users = User.objects.filter(role__in=[User.Role.CUSTOMER, User.Role.ADMIN])[:3]
        
        if not users:
            self.stdout.write("  - No users found, skipping OTP seeding")
            return
        
        otp_codes = ['123456', '654321', '999888']
        
        for idx, user in enumerate(users):
            otp_record, created = OTP.objects.get_or_create(
                user=user,
                defaults={
                    'code': otp_codes[idx],
                    'expires_at': timezone.now() + timedelta(minutes=10)
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ Created OTP for user: {user.username} (Code: {otp_record.code})")
            else:
                self.stdout.write(f"  - OTP already exists for user: {user.username}")
