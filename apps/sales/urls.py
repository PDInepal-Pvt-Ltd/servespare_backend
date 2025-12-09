from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sales.views import SalesOrderViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'orders', SalesOrderViewSet, basename='sales-order')

urlpatterns = [
    path('', include(router.urls)),
]
