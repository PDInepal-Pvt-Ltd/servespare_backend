from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.carts.views import CartViewSet

app_name = 'carts'

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
