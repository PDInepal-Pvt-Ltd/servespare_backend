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
