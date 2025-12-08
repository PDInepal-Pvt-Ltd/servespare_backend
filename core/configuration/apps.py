

PRELOAD_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'allauth',
    'allauth.account',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'drf_spectacular',

]

LOCAL_APPS = [
    'apps.base',
    'apps.users',
    'apps.subscription',
#     'apps.tenant',
#     'apps.subscription_plan',
#     'apps.properties',
#     'apps.hotel.apps.HotelConfig',
#     'apps.resturant.apps.RestaurantConfig',
#     'apps.otp',
#     'apps.accounts',
#     'apps.support_and_ticket',
#     'apps.global_announcement.apps.GlobalAnnouncementConfig',
#     'apps.inventory.apps.InventoryConfig',
#     'apps.delivery.apps.DeliveryConfig',
]