from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.stock_management.views import (
    PartyViewSet,
    PurchaseOrderViewSet,
    PurchaseOrderItemViewSet,
    InventoryViewSet,
    InventoryImageViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'parties', PartyViewSet, basename='party')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-items', PurchaseOrderItemViewSet, basename='purchase-order-item')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'inventory-images', InventoryImageViewSet, basename='inventory-image')

urlpatterns = [
    path('', include(router.urls)),
]

