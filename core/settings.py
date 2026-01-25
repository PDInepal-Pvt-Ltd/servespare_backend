from pathlib import Path
from decouple import config
import os

# Check DEV_MODE first to conditionally import pymysql
DEV_MODE = config('DEV_MODE', default=False, cast=bool)

# Only import pymysql for MySQL (when not in dev mode)
if not DEV_MODE:
    import pymysql
    pymysql.install_as_MySQLdb()



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    'backend.servespare.xyz',
    'www.backend.servespare.xyz',
    'www.imspravidhi.vercel.app',
    'servespare.xyz',
    'localhost',
    '127.0.0.1',
    'unopinionated-kiddingly-verline.ngrok-free.dev',
    'imspravidhi.vercel.app',
    'api-demo.servespare.xyz',
    'api.servespare.xyz',
]

# Allow localhost and ngrok host for CSRF and CORS (used by corsheaders middleware)
# Include the scheme (https/http) as required by Django for CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'https://unopinionated-kiddingly-verline.ngrok-free.dev',
    'https://imspravidhi.vercel.app',
    'https://backend.servespare.xyz',
    'https://servespare.xyz',
    'https://api-demo.servespare.xyz',
    'https://api.servespare.xyz',
]

# If you need cross-origin requests from frontend, explicitly allow it via django-cors-headers settings.
# Consolidated to avoid duplicate assignments.
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'https://unopinionated-kiddingly-verline.ngrok-free.dev',
    'https://imspravidhi.vercel.app',
    'https://backend.servespare.xyz',
    'https://servespare.xyz',
    'https://api-demo.servespare.xyz',
    'https://api.servespare.xyz',
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning',
]

# If you'd rather allow any origin during development, you can set
CORS_ALLOW_ALL_ORIGINS = True


# Application definition
from core.configuration.apps import PRELOAD_APPS, THIRD_PARTY_APPS, LOCAL_APPS
from core.configuration.rest import REST_FRAMEWORK, SPECTACULAR_SETTINGS
from core.configuration.auth import SIMPLE_JWT, AUTHENTICATION_BACKENDS, SITE_ID

INSTALLED_APPS = PRELOAD_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.base.middleware.TenantMiddleware',
    'apps.base.middleware.AuditMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# Database configuration based on DEV_MODE
if DEV_MODE:
    # SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
    }
}
    # MySQL for production
    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.mysql',
    #         'NAME': 'servesp1_servespare',
    #         'HOST': 'localhost',
    #         'PORT': '3306',
    #         'USER': 'servesp1_admin',
    #         'PASSWORD': 'DB2026@sp'
    #     }
    # }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==========================================
# PDF GENERATION SETTINGS
# ==========================================

# Company Information for PDF Headers
COMPANY_NAME = "Servespare"
COMPANY_LOGO_URL = "/static/images/logo.png"
COMPANY_ADDRESS = "Srijana Chowk"
COMPANY_PHONE = "9800000000"
COMPANY_EMAIL = "servespare@gmail.com"

# Tax Label (VAT, GST, TAX, etc.)
TAX_LABEL = "VAT"

# PDF Generation Settings
PDF_SETTINGS = {
    'DEFAULT_PAGE_SIZE': 'A4',
    'MARGIN_TOP': '20mm',
    'MARGIN_BOTTOM': '20mm',
    'MARGIN_LEFT': '20mm',
    'MARGIN_RIGHT': '20mm',
}

# Currency Settings
CURRENCY_SYMBOL = "Rs."
CURRENCY_CODE = "NPR"  # Nepalese Rupee

# Default primary key type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
# https://docs.djangoproject.com/en/6.0/topics/auth/customizing/#substituting-a-custom-user-model

AUTH_USER_MODEL = 'users.User'

EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='no-reply@servespare.xyz'
)

if DEBUG and (not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

