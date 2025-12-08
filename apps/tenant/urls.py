from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tenant.views import TenantViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    path('', include(router.urls)),
]

