

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
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.base',
    'apps.users',
    'apps.otp',
    'apps.subscription',
    'apps.tenant',
    'apps.stock_management',
    'apps.sales',
    'apps.cashandbank',
    'apps.carts',
    'seeds',
    'apps.branch',
]
