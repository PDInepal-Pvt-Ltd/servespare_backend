from rest_framework import serializers
from apps.otp.models import OTP

class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for verifying the OTP code submitted by the user."""
    otp = serializers.CharField(
        max_length=6, 
        min_length=6, 
        write_only=True,
        error_messages={'min_length': 'OTP must be 6 digits.', 'max_length': 'OTP must be 6 digits.'}
    )


class RecoveryRequestSerializer(serializers.Serializer):
    """
    Serializer to accept either username or email for password recovery.
    """
    identifier = serializers.CharField(
        required=True,
        help_text="Enter your username or email address."
    )


class OTPSerializer(serializers.ModelSerializer):
    # Optional: include a read-only field to show if OTP is still valid
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = OTP
        fields = ["id", "user", "code", "created_at", "expires_at", "is_valid"]
        read_only_fields = ["id", "created_at", "is_valid"]

    def get_is_valid(self, obj):
        """Return True if OTP is still valid, False if expired"""
        return obj.is_valid()
