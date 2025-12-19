from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.branch.models import Branch
from apps.branch.serializers import BranchSerializer
from apps.base.pagination import StandardResultsSetPagination
from apps.base.permissions import IsSuperAdminOrTenantAdmin
from apps.base.permission_utils import is_super_admin, is_tenant_admin


class BranchViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for Branch model with RBAC.

	- Super Admin: Can create/manage all branches globally
	- Tenant Admin: Can create/manage branches only in their tenant
	- Others: Read-only access to their tenant's branches
	"""
	queryset = Branch.objects.all()
	serializer_class = BranchSerializer
	permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
	pagination_class = StandardResultsSetPagination

	def get_queryset(self):
		user = self.request.user
		qs = Branch.objects.all()
		
		# Super Admin sees all branches
		if is_super_admin(user):
			return qs
		
		# Tenant Admin sees only their tenant's branches
		if is_tenant_admin(user):
			return qs.filter(tenant=user.tenant)
		
		# Other authenticated users see their tenant's branches (if they have a tenant)
		user_tenant = getattr(user, 'tenant', None)
		if user_tenant is None:
			return qs.none()
		return qs.filter(tenant=user_tenant)

	def perform_create(self, serializer):
		user = self.request.user
		
		# Only Super Admin and Tenant Admin can create branches
		if not is_super_admin(user) and not is_tenant_admin(user):
			raise PermissionDenied('Only Super Admin or Tenant Admin can create branches.')
		
		# Tenant Admin can only create in their tenant
		if is_tenant_admin(user):
			serializer.save(tenant=user.tenant)
		else:
			# Super Admin must specify tenant in the request
			serializer.save()
	
	def perform_update(self, serializer):
		user = self.request.user
		branch = serializer.instance
		
		# Only Super Admin and Tenant Admin can update branches
		if is_super_admin(user):
			serializer.save()
		elif is_tenant_admin(user) and branch.tenant == user.tenant:
			serializer.save()
		else:
			raise PermissionDenied('You do not have permission to update this branch.')
