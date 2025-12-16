from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.branch.views import BranchViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'', BranchViewSet, basename='branch')

urlpatterns = [
    path('', include(router.urls)),
]
