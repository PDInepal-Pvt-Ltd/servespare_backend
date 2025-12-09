from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.users.views import UserViewSet, AuthViewSet, CustomTokenObtainPairView

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'users', UserViewSet, basename='user')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # JWT Token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Router endpoints (users, auth, etc.)
    path('', include(router.urls)),
    
    # OTP endpoints
    path('otp/', include('apps.otp.urls')),
    
    # Other apps
    path('subscription/', include('apps.subscription.urls')),
    path('stock-management/', include('apps.stock_management.urls')),
    path('tenant/', include('apps.tenant.urls')),
    path('sales/', include('apps.sales.urls')),
    path('cash-and-bank/', include('apps.cashandbank.urls')),
]
    


