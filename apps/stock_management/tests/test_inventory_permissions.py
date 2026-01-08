from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from django.test import TestCase

from apps.tenant.models import Tenant
from apps.branch.models import Branch
from apps.users.models import User
from apps.stock_management.models import Inventory


class InventoryPermissionsTest(TestCase):
    def setUp(self):
        # Tenants
        self.tenant1 = Tenant.objects.create(business_name='T1', email='t1@example.com')
        self.tenant2 = Tenant.objects.create(business_name='T2', email='t2@example.com')

        # Branches
        self.branch1 = Branch.objects.create(tenant=self.tenant1, branch_name='B1', branch_code='B1', Email='b1@example.com')
        self.branch2 = Branch.objects.create(tenant=self.tenant2, branch_name='B2', branch_code='B2', Email='b2@example.com')

        # Inventory items
        self.inv1 = Inventory.objects.create(item_name='Item T1', category='local', vehicle_type='two_wheeler', quantity=Decimal('10.00'), min_stock_level=Decimal('1.00'), price=Decimal('100.00'), mrp=Decimal('120.00'), tenant=self.tenant1, branch=self.branch1)
        self.inv2 = Inventory.objects.create(item_name='Item T2', category='original', vehicle_type='four_wheeler', quantity=Decimal('5.00'), min_stock_level=Decimal('1.00'), price=Decimal('200.00'), mrp=Decimal('220.00'), tenant=self.tenant2, branch=self.branch2)

        # Users
        self.admin = User.objects.create_user(username='admin', password='pass', role=User.Role.ADMIN, tenant=self.tenant1)
        self.inv_manager = User.objects.create_user(username='invman', password='pass', role=User.Role.INVENTORY_MANAGER, tenant=self.tenant1, branch=self.branch1)
        self.cashier = User.objects.create_user(username='cash', password='pass', role=User.Role.CASHIER, tenant=self.tenant1, branch=self.branch1)
        self.customer = User.objects.create_user(username='cust', password='pass', role=User.Role.CUSTOMER)
        self.superuser = User.objects.create_superuser(username='root', password='pass', email='root@example.com')

        self.client = APIClient()
        self.list_url = '/api/stock-management/inventory/'

    def _auth_client(self, user):
        # Force authenticate and set a dummy Authorization header so view uses permissions
        self.client.force_authenticate(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test')

    def test_customer_sees_all_inventories(self):
        self._auth_client(self.customer)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data.get('results', data)
        ids = [i['id'] for i in items]
        # customer should be able to see both inventories
        self.assertIn(self.inv1.id, ids)
        self.assertIn(self.inv2.id, ids)

    def test_admin_sees_only_their_tenant_inventory(self):
        self._auth_client(self.admin)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data.get('results', data)
        ids = [i['id'] for i in items]
        self.assertIn(self.inv1.id, ids)
        self.assertNotIn(self.inv2.id, ids)

    def test_inventory_manager_sees_only_branch_inventory(self):
        self._auth_client(self.inv_manager)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data.get('results', data)
        ids = [i['id'] for i in items]
        # Inventory manager limited to their branch
        self.assertIn(self.inv1.id, ids)
        self.assertNotIn(self.inv2.id, ids)

    def test_cashier_sees_only_branch_inventory(self):
        self._auth_client(self.cashier)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        items = data.get('results', data)
        ids = [i['id'] for i in items]
        self.assertIn(self.inv1.id, ids)
        self.assertNotIn(self.inv2.id, ids)

    def test_admin_can_delete_their_tenant_item_but_not_other(self):
        self._auth_client(self.admin)
        # delete own tenant item
        resp = self.client.delete(f'{self.list_url}{self.inv1.id}/')
        self.assertIn(resp.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK))
        self.inv1.refresh_from_db()
        self.assertTrue(self.inv1.is_removed)

        # try delete other tenant item
        resp2 = self.client.delete(f'{self.list_url}{self.inv2.id}/')
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_manager_can_delete_branch_item(self):
        self._auth_client(self.inv_manager)
        resp = self.client.delete(f'{self.list_url}{self.inv1.id}/')
        self.assertIn(resp.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK))
        self.inv1.refresh_from_db()
        self.assertTrue(self.inv1.is_removed)

    def test_superuser_can_delete_any_item(self):
        self._auth_client(self.superuser)
        resp = self.client.delete(f'{self.list_url}{self.inv2.id}/')
        self.assertIn(resp.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK))
        self.inv2.refresh_from_db()
        self.assertTrue(self.inv2.is_removed)
