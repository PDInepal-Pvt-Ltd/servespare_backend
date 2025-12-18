from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.carts.views import CartViewSet

from apps.carts.views import CartViewSet, FavoriteViewSet

app_name = 'carts'

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
]
