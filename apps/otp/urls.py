from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.otp.views import RequestOtpViewSet, VerifyOtpViewSet, OTPViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'', OTPViewSet, basename='otp-list')

urlpatterns = [
    # OTP request and verify endpoints (custom actions)
    path('request/', RequestOtpViewSet.as_view({'post': 'trigger_otp'}), name='otp-request'),
    path('verify/', VerifyOtpViewSet.as_view({'post': 'verify_otp'}), name='otp-verify'),
    
    # Router endpoints (admin OTP listing)
    path('', include(router.urls)),
]
