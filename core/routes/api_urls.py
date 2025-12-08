from django.urls import path, include

urlpatterns = [
    path('subscription/', include('apps.subscription.urls')),
]

