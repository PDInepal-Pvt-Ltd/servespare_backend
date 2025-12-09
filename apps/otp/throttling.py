from rest_framework.throttling import UserRateThrottle

class OTPResendRateThrottle(UserRateThrottle):
    """
    Limits the number of times an authenticated user can request a new OTP.
    Uses the 'otp_resend' rate defined in settings.py.
    """
    scope = 'otp_resend'
