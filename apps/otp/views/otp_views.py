from rest_framework import viewsets, status,permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from apps.otp.throttling import OTPResendRateThrottle
from apps.users.models import User
from django.db.models import Q
from apps.otp.serializers import RecoveryRequestSerializer, OTPVerificationSerializer
from apps.otp.utils import generate_and_save_otp, send_otp_email
from apps.users.tokens import create_recovery_token
from apps.otp.models import OTP
from apps.otp.serializers import OTPSerializer
from apps.base.pagination import StandardResultsSetPagination


class RequestOtpViewSet(viewsets.ViewSet):
    """
    Handles OTP requests for password recovery with resend rate limiting.
    """

    permission_classes = [AllowAny]
    throttle_classes = [OTPResendRateThrottle]
    serializer_class = RecoveryRequestSerializer

    @action(detail=False, methods=["post"], url_path="request")
    def trigger_otp(self, request):
        serializer = RecoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]

        try:
            user = User.objects.get(Q(username=identifier) | Q(email=identifier))
        except User.DoesNotExist:
            return Response({"message": "If an account exists, a recovery code has been sent."}, status=200)

        otp = generate_and_save_otp(user)
        if not send_otp_email(user, otp.code):
            return Response({"error": "Failed to send OTP."}, status=500)

        return Response(
            {
                "message": "If an account exists, a recovery code has been sent.",
            },
            status=200,
        )

class VerifyOtpViewSet(viewsets.ViewSet):
    """
    Step 2 — Verify OTP directly with identifier and OTP code, then issue a JWT token for password reset.
    No authentication required - verify using identifier + OTP code.
    After successful OTP verification, a secure password reset token is generated.
    """
    permission_classes = [AllowAny]
    serializer_class = OTPVerificationSerializer

    @action(detail=False, methods=["post"], url_path="verify")
    def verify_otp(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["otp"]

        try:
            user = User.objects.get(Q(username=identifier) | Q(email=identifier))
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = OTP.objects.filter(user=user, code=code).first()
        if not otp:
            return Response(
                {"error": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp.is_valid():
            otp.delete()
            return Response(
                {"error": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp.delete()

        token_data = create_recovery_token(
            user=user,
            purpose='password_reset',
            expires_in=15  # 15 minutes
        )

        return Response(
            {
                "message": "OTP verified successfully. Use the token to reset your password.",
                "token": token_data["access"],
                "expires_at": token_data["expires_at"],
                "expires_in": token_data["expires_in"],
            },
            status=status.HTTP_200_OK,
        )

class OTPViewSet(viewsets.ViewSet):
    """
    ViewSet to list OTPs.
    Restricted to admin users for monitoring or debugging purposes.
    """
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    serializer_class = OTPSerializer

    def list(self, request):
        """
        List all OTPs in the system.
        Supports optional query params to filter by user or validity.
        """
        user_id = request.query_params.get("user_id", None)
        show_valid = request.query_params.get("valid", None)

        otps = OTP.objects.filter(deleted_at__isnull=True).order_by("-created_at")

        if user_id:
            otps = otps.filter(user__id=user_id)
        if show_valid is not None:
            if show_valid.lower() == "true":
                otps = [otp for otp in otps if otp.is_valid()]
            elif show_valid.lower() == "false":
                otps = [otp for otp in otps if not otp.is_valid()]

        serializer = OTPSerializer(otps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)