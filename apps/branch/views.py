from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.branch.models import Branch
from apps.branch.serializers import BranchSerializer


class BranchViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for Branch model.

	- Limits queryset to the requesting user's tenant (unless superuser).
	- Sets `tenant` to `request.user.tenant` on create.
	"""
	queryset = Branch.objects.all()
	serializer_class = BranchSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		qs = Branch.objects.all()
		if user.is_superuser:
			return qs
		user_tenant = getattr(user, 'tenant', None)
		if user_tenant is None:
			return qs.none()
		return qs.filter(tenant=user_tenant)

	def perform_create(self, serializer):
		user = self.request.user
		tenant = getattr(user, 'tenant', None)
		if tenant is None and not user.is_superuser:
			raise PermissionDenied('User does not belong to a tenant.')
		serializer.save(tenant=tenant)
