"""
Clear seed data from the database.
Run with: python manage.py clear_data
"""

from django.core.management.base import BaseCommand
from apps.stock_management.models import Party, PurchaseOrder, PurchaseOrderItem, Inventory, InventoryImage
from apps.sales.models import SalesOrder, SalesOrderItem, Bill
from apps.cashandbank.models import BankAccount, CashTransaction
from apps.carts.models import Cart, CartItem
from apps.otp.models import OTP


class Command(BaseCommand):
    help = 'Clear seed data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete ALL data including users, branches, and tenants (careful!)',
        )

    def handle(self, *args, **options):
        if options.get('all'):
            self.clear_all_data()
        else:
            self.clear_app_data()

    def clear_app_data(self):
        """Clear only app data (not users, branches, tenants)"""
        self.stdout.write('Clearing application data...')

        models_to_clear = [
            ('OTP', OTP),
            ('CartItem', CartItem),
            ('Cart', Cart),
            ('SalesOrderItem', SalesOrderItem),
            ('SalesOrder', SalesOrder),
            ('CashTransaction', CashTransaction),
            ('Bill', Bill),
            ('BankAccount', BankAccount),
            ('PurchaseOrderItem', PurchaseOrderItem),
            ('PurchaseOrder', PurchaseOrder),
            ('InventoryImage', InventoryImage),
            ('Inventory', Inventory),
            ('Party', Party),
        ]

        for model_name, model in models_to_clear:
            # Hard delete by bypassing soft delete
            count = model._base_manager.all().count()
            model._base_manager.all().delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count} {model_name} records"))

        self.stdout.write(self.style.SUCCESS('\n✓ All application data cleared successfully!'))
        self.stdout.write(self.style.WARNING('Note: Users, Branches, and Tenants remain in the database.'))

    def clear_all_data(self):
        """Clear ALL data including users, branches, and tenants"""
        self.stdout.write(self.style.WARNING('⚠ WARNING: This will delete ALL data from the database!'))
        confirmation = input('Type "yes" to confirm: ')

        if confirmation.lower() != 'yes':
            self.stdout.write(self.style.ERROR('✗ Cancelled.'))
            return

        from apps.users.models import User
        from apps.branch.models import Branch
        from apps.tenant.models import Tenant
        from apps.subscription.models import Subscription, SubscriptionPlan

        models_to_clear = [
            ('OTP', OTP),
            ('CartItem', CartItem),
            ('Cart', Cart),
            ('SalesOrderItem', SalesOrderItem),
            ('SalesOrder', SalesOrder),
            ('CashTransaction', CashTransaction),
            ('Bill', Bill),
            ('BankAccount', BankAccount),
            ('PurchaseOrderItem', PurchaseOrderItem),
            ('PurchaseOrder', PurchaseOrder),
            ('InventoryImage', InventoryImage),
            ('Inventory', Inventory),
            ('Party', Party),
            ('User', User),
            ('Subscription', Subscription),
            ('Branch', Branch),
            ('Tenant', Tenant),
            ('SubscriptionPlan', SubscriptionPlan),
        ]

        for model_name, model in models_to_clear:
            count = model._base_manager.all().count()
            model._base_manager.all().delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {count} {model_name} records"))

        self.stdout.write(self.style.SUCCESS('\n✓ All data cleared successfully!'))
