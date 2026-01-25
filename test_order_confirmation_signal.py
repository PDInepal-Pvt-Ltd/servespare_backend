"""Test script to verify order confirmation email signal."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core import mail
from django.test import override_settings
from apps.sales.models import SalesOrder
from apps.users.models import User
from apps.tenant.models import Tenant
from apps.branch.models import Branch
from decimal import Decimal

print("Testing Order Confirmation Email Signal...")
print("-" * 50)

# Use test email backend to capture emails
with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
    try:
        # Get first tenant
        tenant = Tenant.objects.first()
        if not tenant:
            print("✗ No tenant found in database!")
            exit(1)
        print(f"✓ Using tenant: {tenant.business_name}")
        
        # Get first branch for this tenant
        branch = tenant.branches.first()
        if not branch:
            print("✗ No branch found for this tenant!")
            exit(1)
        print(f"✓ Using branch: {branch.branch_name}")
        
        # Get or create test customer
        customer, created = User.objects.get_or_create(
            username='signaltestcustomer',
            defaults={
                'email': 'signaltest@example.com',
                'full_name': 'Signal Test Customer',
                'role': 'customer'
            }
        )
        print(f"✓ Using customer: {customer.full_name} ({customer.email})")
        
        # Clear previous emails
        mail.outbox = []
        
        # Create a new SalesOrder with confirmed status
        order = SalesOrder.objects.create(
            tenant=tenant,
            branch=branch,
            customer=customer,
            order_status='confirmed',
            delivery_address='123 Test Street',
            delivery_city='Test City',
            subtotal=Decimal('1000.00'),
            discount_amount=Decimal('0.00'),
            tax_amount=Decimal('130.00'),
            total_amount=Decimal('1130.00'),
        )
        print(f"✓ Created SalesOrder: {order.order_number}")
        
        # Check if email was sent
        if len(mail.outbox) > 0:
            print(f"\n✓ Email sent successfully!")
            print(f"  To: {mail.outbox[0].to}")
            print(f"  Subject: {mail.outbox[0].subject}")
            print(f"  Body preview: {mail.outbox[0].body[:150]}...")
        else:
            print(f"\n✗ No email was sent!")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("-" * 50)
print("Test completed!")
