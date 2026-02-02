from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.tenant.models import Tenant
from apps.branch.models import Branch
from apps.stock_management.models import Party

User = get_user_model()


class PartyNamesAPITestCase(TestCase):
    def setUp(self):
        # Create tenant and branches
        self.tenant = Tenant.objects.create(business_name='Tenant 1', email='t1@example.com', status='approved')
        self.branch1 = Branch.objects.create(branch_name='Branch 1', branch_code='B1', tenant=self.tenant, province='Bagmati', district='Kathmandu', Email='b1@example.com')
        self.branch2 = Branch.objects.create(branch_name='Branch 2', branch_code='B2', tenant=self.tenant, province='Bagmati', district='Kathmandu', Email='b2@example.com')

        # Create users (provide unique emails)
        # Admin with assigned branch (should be restricted to that branch)
        self.admin_branch_user = User.objects.create_user(username='admin_branch', email='admin_branch@example.com', password='pass', role=User.Role.ADMIN, tenant=self.tenant, branch=self.branch1)

        # Tenant admin without branch (can see all tenant branches)
        self.tenant_admin = User.objects.create_user(username='tenant_admin', email='tenant_admin@example.com', password='pass', role=User.Role.ADMIN, tenant=self.tenant)

        # Sub-admin (tenant user) without branch - should see tenant-scoped results
        self.sub_admin = User.objects.create_user(username='sub_admin', email='sub_admin@example.com', password='pass', role=User.Role.SUB_ADMIN, tenant=self.tenant)

        # Create parties
        Party.objects.create(party_type='supplier', party_name='Party A', branch=self.branch1, tenant=self.tenant, is_active=True)
        Party.objects.create(party_type='supplier', party_name='Party B', branch=self.branch2, tenant=self.tenant, is_active=True)
        Party.objects.create(party_type='customer', customer_type='retailer', party_name='Retailer One', branch=self.branch1, tenant=self.tenant, is_active=True)

        self.client = APIClient()

    def test_branch_admin_sees_only_branch_party_names(self):
        self.client.force_authenticate(self.admin_branch_user)
        resp = self.client.get('/api/stock-management/parties/party-names/')
        self.assertEqual(resp.status_code, 200)
        names = sorted([r['party_name'] for r in resp.json()])
        self.assertEqual(names, ['Party A', 'Retailer One'])

    def test_tenant_admin_sees_all_tenant_party_names(self):
        self.client.force_authenticate(self.tenant_admin)
        resp = self.client.get('/api/stock-management/parties/party-names/')
        self.assertEqual(resp.status_code, 200)
        names = sorted([r['party_name'] for r in resp.json()])
        self.assertEqual(names, ['Party A', 'Party B', 'Retailer One'])

    def test_tenant_admin_can_filter_by_branch_param(self):
        self.client.force_authenticate(self.tenant_admin)
        resp = self.client.get(f'/api/stock-management/parties/party-names/?branch={self.branch2.id}')
        self.assertEqual(resp.status_code, 200)
        names = [r['party_name'] for r in resp.json()]
        self.assertEqual(names, ['Party B'])


class PartyNamesDirectViewTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(business_name='Tenant X', email='x@example.com', status='approved')
        self.branch = Branch.objects.create(branch_name='Main', branch_code='M1', tenant=self.tenant, province='Bagmati', district='Kathmandu', Email='main@example.com')
        self.user = User.objects.create_user(username='u1', password='p', role=User.Role.ADMIN, tenant=self.tenant, branch=self.branch)
        Party.objects.create(party_type='supplier', party_name='My Party', branch=self.branch, tenant=self.tenant, is_active=True)

    def test_direct_view_call_returns_party_names(self):
        from rest_framework.test import APIRequestFactory
        from apps.stock_management.views.party import PartyViewSet
        factory = APIRequestFactory()
        request = factory.get('/parties/party-names/')
        from rest_framework.test import force_authenticate
        force_authenticate(request, user=self.user)
        view = PartyViewSet.as_view({'get': 'party_names'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data, [{'party_name': 'My Party'}])
