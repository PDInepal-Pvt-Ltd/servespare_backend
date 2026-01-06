from django.contrib import admin

from .models import OTP


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
	list_display = ("user", "code", "created_at", "expires_at", "is_valid_display")
	search_fields = ("user__username", "user__email", "code")
	list_filter = ("expires_at",)
	readonly_fields = ("created_at",)

	def is_valid_display(self, obj):
		return obj.is_valid()

	is_valid_display.short_description = "Valid"
	is_valid_display.boolean = True
	
	def has_delete_permission(self, request, obj=None):
		"""
		Allow all authenticated users with specific roles to delete.
		Roles: SUPER_ADMIN, ADMIN, SUB_ADMIN, CASHIER, INVENTORY_MANAGER, CUSTOMER
		"""
		if not request.user or not request.user.is_authenticated:
			return False
		from apps.users.models import User
		allowed_roles = [
			User.Role.SUPER_ADMIN,
			User.Role.ADMIN,
			User.Role.SUB_ADMIN,
			User.Role.CASHIER,
			User.Role.INVENTORY_MANAGER,
			User.Role.CUSTOMER
		]
		return request.user.role in allowed_roles
