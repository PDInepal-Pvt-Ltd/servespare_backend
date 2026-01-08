#!/usr/bin/env python
"""
Debug script to test purchase order creation and ledger entry generation.
Run: python debug_purchase_ledger.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.utils import timezone
from decimal import Decimal
from datetime import date

# Import models
from apps.tenant.models import Tenant
from apps.branch.models import Branch
from apps.stock_management.models import PurchaseOrder, PurchaseOrderItem, Party
from apps.cashandbank.models import AccountLedger
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("\n" + "="*60)
print("PURCHASE LEDGER DEBUG SCRIPT")
print("="*60)

# Get or create test tenant
try:
    tenant = Tenant.objects.first()
    if not tenant:
        print("\n❌ ERROR: No tenant found in database")
        print("Please create a tenant first using admin panel or fixtures")
        sys.exit(1)
    
    print(f"\n✓ Using Tenant: {tenant.business_name} (ID: {tenant.id})")
    
    # Get or create test branch
    branch = Branch.objects.filter(tenant=tenant).first()
    if not branch:
        print("❌ ERROR: No branch found for tenant")
        sys.exit(1)
    print(f"✓ Using Branch: {branch.branch_name} (ID: {branch.id})")
    
    # Get or create test supplier
    supplier = Party.objects.filter(party_type='supplier', tenant=tenant).first()
    if not supplier:
        print("❌ ERROR: No supplier found for tenant")
        sys.exit(1)
    print(f"✓ Using Supplier: {supplier} (ID: {supplier.id})")
    
    # Clear existing test POs and ledgers
    print("\n📋 Clearing test data...")
    test_pos = PurchaseOrder.objects.filter(po_number__startswith='DEBUG-')
    test_ledgers = AccountLedger.objects.filter(reference__startswith='DEBUG-')
    print(f"  - Deleting {test_pos.count()} test purchase orders")
    print(f"  - Deleting {test_ledgers.count()} test ledger entries")
    test_pos.delete()
    test_ledgers.delete()
    
    # Create a test purchase order
    print("\n📝 Creating Test Purchase Order...")
    po = PurchaseOrder.objects.create(
        tenant=tenant,
        branch=branch,
        supplier=supplier,
        po_number=f"DEBUG-{timezone.now().timestamp()}",
        status='draft',
        order_date=date.today(),
        notes="Debug test PO"
    )
    print(f"✓ Created PO: {po.po_number} (ID: {po.id})")
    print(f"  - Tenant: {po.tenant}")
    print(f"  - Branch: {po.branch}")
    print(f"  - Status: {po.status}")
    print(f"  - Total Amount (before items): {po.total_amount}")
    
    # Add items to PO
    print("\n➕ Adding Items to Purchase Order...")
    item1 = PurchaseOrderItem.objects.create(
        tenant=tenant,
        purchase_order=po,
        branch=branch,
        item_name="Brake Pad Set",
        part_number="BP-001",
        quantity=Decimal('10'),
        unit_price=Decimal('500.00'),
        tax=Decimal('18.00')
    )
    print(f"✓ Added Item 1: {item1.item_name}")
    print(f"  - Quantity: {item1.quantity}, Unit Price: {item1.unit_price}")
    print(f"  - Subtotal: {item1.subtotal}, Tax: {item1.tax_amount}, Total: {item1.total_price}")
    
    item2 = PurchaseOrderItem.objects.create(
        tenant=tenant,
        purchase_order=po,
        branch=branch,
        item_name="Air Filter",
        part_number="AF-002",
        quantity=Decimal('5'),
        unit_price=Decimal('250.00'),
        tax=Decimal('18.00')
    )
    print(f"✓ Added Item 2: {item2.item_name}")
    print(f"  - Quantity: {item2.quantity}, Unit Price: {item2.unit_price}")
    print(f"  - Subtotal: {item2.subtotal}, Tax: {item2.tax_amount}, Total: {item2.total_price}")
    
    # Refresh PO to get updated total
    po.refresh_from_db()
    print(f"\n✓ Updated PO Total Amount: {po.total_amount}")

    # Move PO to a ledger-eligible status and save to trigger sync
    print("\n🔄 Updating PO status to 'received' to trigger ledger sync...")
    po.status = 'received'
    po.save()
    
    # Check if ledger entry was created
    print("\n🔍 Checking for Ledger Entry...")
    ledger_entries = AccountLedger.objects.filter(
        reference_id=str(po.id),
        reference_type='purchase_order'
    )
    
    if ledger_entries.exists():
        print(f"✓ Found {ledger_entries.count()} ledger entry/entries:")
        for entry in ledger_entries:
            print(f"  - ID: {entry.id}")
            print(f"    Ledger Type: {entry.ledger_type}")
            print(f"    Transaction Type: {entry.transaction_type}")
            print(f"    Debit: {entry.debit}")
            print(f"    Credit: {entry.credit}")
            print(f"    Description: {entry.description}")
            print(f"    Reference: {entry.reference}")
    else:
        print("❌ NO LEDGER ENTRY CREATED!")
        print("\nDebugging Info:")
        print(f"  - PO ID: {po.id}")
        print(f"  - PO Total Amount: {po.total_amount}")
        print(f"  - Tenant is set: {po.tenant is not None}")
        print(f"  - Created: {po.created}")
        
        # Check signal logs
        print("\n📊 Checking all ledger entries for this PO:")
        all_entries = AccountLedger.objects.filter(reference_id=str(po.id))
        if all_entries.exists():
            print(f"  Found {all_entries.count()} entries:")
            for entry in all_entries:
                print(f"    - {entry.reference_type}: {entry.reference}")
        else:
            print("  No entries found with this PO ID")
    
    print("\n" + "="*60)
    print("✅ Debug Complete")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
