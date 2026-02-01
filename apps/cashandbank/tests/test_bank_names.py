from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.tenant.models import Tenant
from apps.branch.models import Branch
from apps.cashandbank.models import BankAccount

User = get_user_model()


class BankNamesAPITestCase(TestCase):
    def setUp(self):
        # Create tenant and branches
        self.tenant = Tenant.objects.create(business_name='Tenant 1', email='t1@example.com')
        self.branch1 = Branch.objects.create(branch_name='Branch 1', branch_code='B1', tenant=self.tenant)
        self.branch2 = Branch.objects.create(branch_name='Branch 2', branch_code='B2', tenant=self.tenant)

        # Create users
        # Admin with assigned branch (should be restricted to that branch)
        self.admin_branch_user = User.objects.create_user(username='admin_branch', password='pass', role=User.Role.ADMIN, tenant=self.tenant, branch=self.branch1)

        # Tenant admin without branch (can see all tenant branches)
        self.tenant_admin = User.objects.create_user(username='tenant_admin', password='pass', role=User.Role.ADMIN, tenant=self.tenant)

        # Sub-admin (tenant user) without branch - should see tenant-scoped results
        self.sub_admin = User.objects.create_user(username='sub_admin', password='pass', role=User.Role.SUB_ADMIN, tenant=self.tenant)

        # Create bank accounts
        BankAccount.objects.create(account_type='bank', account_name='Acct 1', bank_name='Bank A', branch=self.branch1, tenant=self.tenant, is_active=True)
        BankAccount.objects.create(account_type='bank', account_name='Acct 2', bank_name='Bank B', branch=self.branch2, tenant=self.tenant, is_active=True)
        BankAccount.objects.create(account_type='esewa', account_name='E1', bank_name=None, branch=self.branch1, tenant=self.tenant, is_active=True)

        self.client = APIClient()

    def test_branch_admin_sees_only_branch_bank_names(self):
        self.client.force_authenticate(self.admin_branch_user)
        resp = self.client.get('/cash-and-bank/bank-accounts/bank-names/')
        self.assertEqual(resp.status_code, 200)
        names = [r['bank_name'] for r in resp.json()]
        self.assertEqual(names, ['Bank A'])

    def test_tenant_admin_sees_all_tenant_bank_names(self):
        self.client.force_authenticate(self.tenant_admin)
        resp = self.client.get('/cash-and-bank/bank-accounts/bank-names/')
        self.assertEqual(resp.status_code, 200)
        names = sorted([r['bank_name'] for r in resp.json()])
        self.assertEqual(names, ['Bank A', 'Bank B'])

    def test_tenant_admin_can_filter_by_branch_param(self):
        self.client.force_authenticate(self.tenant_admin)
        resp = self.client.get(f'/cash-and-bank/bank-accounts/bank-names/?branch={self.branch2.id}')
        self.assertEqual(resp.status_code, 200)
        names = [r['bank_name'] for r in resp.json()]
        self.assertEqual(names, ['Bank B'])


class BankNamesDirectViewTestCase(TestCase):
    """Call the view directly using APIRequestFactory to avoid URL conf issues."""

    def setUp(self):
        self.factory = APIClient()
        self.tenant = Tenant.objects.create(business_name='Tenant X', email='x@example.com')
        self.branch = Branch.objects.create(branch_name='Main', branch_code='M1', tenant=self.tenant)
        self.user = User.objects.create_user(username='u1', password='p', role=User.Role.ADMIN, tenant=self.tenant, branch=self.branch)
        BankAccount.objects.create(account_type='bank', account_name='BAcc', bank_name='My Bank', branch=self.branch, tenant=self.tenant, is_active=True)

    def test_direct_view_call_returns_bank_names(self):
        from rest_framework.test import APIRequestFactory
        from apps.cashandbank.views.bank_account import BankAccountViewSet
        factory = APIRequestFactory()
        request = factory.get('/bank-accounts/bank-names/')
        request.user = self.user
        view = BankAccountViewSet.as_view({'get': 'bank_names'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data, [{'bank_name': 'My Bank'}])
