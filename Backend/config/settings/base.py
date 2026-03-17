import json
from pathlib import Path

import environ
from celery.schedules import crontab
from oscar import INSTALLED_APPS as OSCAR_CORE_APPS
from oscar.defaults import *  # noqa: F401,F403

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='change-me')
DEBUG = env('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = [
    host.strip()
    for host in env('DJANGO_ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')
    if host.strip()
]

INSTALLED_APPS = [
    'corsheaders',
    'sorl.thumbnail',
    *OSCAR_CORE_APPS,
    'rest_framework',
    'django_filters',
    'apps.auditlog',
    'apps.accounts',
    'apps.inventory',
    'apps.marketplace',
    'apps.notifications',
    'apps.payments',
    'apps.search',
    'apps.image_search',
    'apps.recommendations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.api.middleware.ApiRequestLoggingMiddleware',
    'apps.api.middleware.ApiExceptionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'oscar.core.context_processors.metadata',
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.apps.communication.notifications.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.common.auth_backends.SafeEmailBackend',
]

SITE_ID = 1

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env('MEDIA_ROOT', default=str(BASE_DIR / 'media')))
FILE_UPLOAD_MAX_MEMORY_SIZE = env.int('FILE_UPLOAD_MAX_MEMORY_SIZE', default=5 * 1024 * 1024)
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int('DATA_UPLOAD_MAX_MEMORY_SIZE', default=15 * 1024 * 1024)
MAX_IMAGE_UPLOAD_BYTES = env.int('MAX_IMAGE_UPLOAD_BYTES', default=5 * 1024 * 1024)
MAX_PRODUCT_IMAGE_BYTES = env.int('MAX_PRODUCT_IMAGE_BYTES', default=10 * 1024 * 1024)
MAX_IMAGE_DIMENSION = env.int('MAX_IMAGE_DIMENSION', default=1600)
MAX_PRODUCT_IMAGE_DIMENSION = env.int('MAX_PRODUCT_IMAGE_DIMENSION', default=2400)
NORMALIZED_IMAGE_FORMAT = env('NORMALIZED_IMAGE_FORMAT', default='WEBP').upper()
NORMALIZED_IMAGE_QUALITY = env.int('NORMALIZED_IMAGE_QUALITY', default=82)
ALLOWED_IMAGE_EXTENSIONS = tuple(
    ext.strip().lower()
    for ext in env('ALLOWED_IMAGE_EXTENSIONS', default='.jpg,.jpeg,.png,.webp').split(',')
    if ext.strip()
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'EXCEPTION_HANDLER': 'apps.api.exceptions.api_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '120/hour',
        'user': '1200/hour',
        'account_csrf': '60/hour',
        'account_register': '5/hour',
        'account_register_identity': '3/hour',
        'account_login': '20/hour',
        'account_login_identity': '8/hour',
        'account_password': '10/hour',
        'quote_request': '8/hour',
        'public_search': '120/hour',
        'image_search': '20/hour',
        'recommendations': '180/hour',
        'supplier_apply': '4/day',
        'payment_init': '20/hour',
    },
    'PAGE_SIZE': 24,
}

OSCAR_SHOP_NAME = env('OSCAR_SHOP_NAME', default='Vortexus Industrial')
OSCAR_ALLOW_ANON_CHECKOUT = True
OSCAR_DEFAULT_CURRENCY = 'USD'
OSCAR_DELETE_IMAGE_FILES = env.bool('OSCAR_DELETE_IMAGE_FILES', default=False)
OSCAR_HOMEPAGE = '/'
THUMBNAIL_FORMAT = 'PNG'

REDIS_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_TASK_EAGER_PROPAGATES = env.bool('CELERY_TASK_EAGER_PROPAGATES', default=True)
CELERY_BEAT_SCHEDULE = {
    'refresh-trending-recommendations-hourly': {
        'task': 'apps.recommendations.tasks.refresh_trending_recommendations',
        'schedule': crontab(minute=0),
        'args': (24,),
    },
}

OPENSEARCH = {
    'HOST': env('OPENSEARCH_HOST', default='http://127.0.0.1:9200'),
    'USER': env('OPENSEARCH_USER', default=''),
    'PASSWORD': env('OPENSEARCH_PASSWORD', default=''),
}

SEARCH_INDEX_PRODUCTS = 'products'
SEARCH_INDEX_IMAGE_EMBEDDINGS = 'product_image_embeddings'
EMBEDDING_DIMENSION = 512

IMAGE_EMBEDDING = {
    'BACKEND': env('IMAGE_EMBEDDING_BACKEND', default='clip'),
    'CLIP_MODEL_NAME': env('CLIP_MODEL_NAME', default='openai/clip-vit-base-patch32'),
    'CLIP_DEVICE': env('CLIP_DEVICE', default='cpu'),
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    }
}
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'

ENABLE_ASYNC_TASKS = env.bool('ENABLE_ASYNC_TASKS', default=False)

INDUSTRIAL_SHIPPING_RULES = [
    {
        'code': 'dispatch-hub-pickup',
        'name': 'Dispatch Hub Pickup',
        'description': 'Collect stocked parts and equipment from the Vortexus dispatch hub.',
        'carrier_code': 'vortexus',
        'service_code': 'pickup',
        'method_type': 'pickup',
        'countries': ['KE'],
        'is_pickup': True,
        'charge': '0.00',
        'min_eta_days': 0,
        'max_eta_days': 1,
        'max_supplier_groups': 1,
    },
    {
        'code': 'standard-freight',
        'name': 'Standard Freight',
        'description': 'Standard freight for stocked pumps, filters, treatment systems, and accessories.',
        'carrier_code': 'vortexus',
        'service_code': 'standard',
        'method_type': 'freight',
        'countries': ['KE', 'UG', 'TZ', 'RW', 'ET'],
        'charge': '35.00',
        'international_charge': '95.00',
        'free_subtotal_threshold': '1500.00',
        'min_eta_days': 2,
        'max_eta_days': 5,
        'max_weight_kg': '250.00',
    },
    {
        'code': 'priority-dispatch',
        'name': 'Priority Dispatch',
        'description': 'Priority dispatch for urgent replacements and service-critical equipment.',
        'carrier_code': 'vortexus',
        'service_code': 'priority',
        'method_type': 'express',
        'countries': ['KE'],
        'charge': '85.00',
        'free_subtotal_threshold': '2500.00',
        'min_eta_days': 1,
        'max_eta_days': 2,
        'max_weight_kg': '80.00',
        'max_supplier_groups': 1,
    },
    {
        'code': 'project-logistics',
        'name': 'Project Logistics',
        'description': 'Coordinated site delivery for larger borehole, pumping, and treatment projects.',
        'carrier_code': 'vortexus',
        'service_code': 'project',
        'method_type': 'project',
        'countries': ['KE', 'UG', 'TZ', 'RW', 'ET'],
        'charge': '180.00',
        'international_charge': '260.00',
        'reduced_charge_threshold': '3000.00',
        'reduced_charge': '120.00',
        'reduced_international_charge': '180.00',
        'min_eta_days': 3,
        'max_eta_days': 10,
        'project_only': True,
    },
]

INDUSTRIAL_TAX_RULES = {
    'KE': {
        'default_rate': '0.16',
        'shipping_rate': '0.16',
        'product_profile_rates': {
            'accessory': '0.16',
            'standard': '0.16',
            'project': '0.16',
            'water_treatment_chemical': '0.00',
            'service': '0.00',
        },
        'shipping_profile_rates': {
            'pickup': '0.00',
            'freight': '0.16',
            'express': '0.16',
            'project': '0.16',
        },
    },
    'UG': {
        'default_rate': '0.18',
        'shipping_rate': '0.18',
        'product_profile_rates': {
            'accessory': '0.18',
            'standard': '0.18',
            'project': '0.18',
            'water_treatment_chemical': '0.00',
            'service': '0.00',
        },
        'shipping_profile_rates': {
            'pickup': '0.00',
            'freight': '0.18',
            'express': '0.18',
            'project': '0.18',
        },
    },
    'TZ': {
        'default_rate': '0.18',
        'shipping_rate': '0.18',
        'product_profile_rates': {
            'accessory': '0.18',
            'standard': '0.18',
            'project': '0.18',
            'water_treatment_chemical': '0.00',
            'service': '0.00',
        },
        'shipping_profile_rates': {
            'pickup': '0.00',
            'freight': '0.18',
            'express': '0.18',
            'project': '0.18',
        },
    },
    'RW': {
        'default_rate': '0.18',
        'shipping_rate': '0.18',
        'product_profile_rates': {
            'accessory': '0.18',
            'standard': '0.18',
            'project': '0.18',
            'water_treatment_chemical': '0.00',
            'service': '0.00',
        },
        'shipping_profile_rates': {
            'pickup': '0.00',
            'freight': '0.18',
            'express': '0.18',
            'project': '0.18',
        },
    },
    'ET': {
        'default_rate': '0.15',
        'shipping_rate': '0.15',
        'product_profile_rates': {
            'accessory': '0.15',
            'standard': '0.15',
            'project': '0.15',
            'water_treatment_chemical': '0.00',
            'service': '0.00',
        },
        'shipping_profile_rates': {
            'pickup': '0.00',
            'freight': '0.15',
            'express': '0.15',
            'project': '0.15',
        },
    },
}

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in env(
        'CORS_ALLOWED_ORIGINS',
        default='http://127.0.0.1:5173,http://localhost:5173',
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in env(
        'CSRF_TRUSTED_ORIGINS',
        default='http://127.0.0.1:5173,http://localhost:5173',
    ).split(',')
    if origin.strip()
]

COUNTRY_CURRENCY_MAP = json.loads(
    env(
        'COUNTRY_CURRENCY_MAP',
        default='{"US":"USD","KE":"KES","UG":"UGX","TZ":"TZS","RW":"RWF","ET":"ETB"}',
    )
)

DISPLAY_CURRENCY_RATES = json.loads(
    env(
        'DISPLAY_CURRENCY_RATES',
        default='{"USD":1,"KES":129.25,"UGX":3719.0,"TZS":2588.0,"RWF":1466.79,"ETB":155.44}',
    )
)

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='no-reply@vortexus.local')
NOTIFICATION_REPLY_TO_EMAIL = env('NOTIFICATION_REPLY_TO_EMAIL', default='')
SALES_NOTIFICATION_RECIPIENTS = [
    recipient.strip()
    for recipient in env('SALES_NOTIFICATION_RECIPIENTS', default='sales@vortexus.local').split(',')
    if recipient.strip()
]

PAYMENT_METHODS = [
    {'code': 'mpesa', 'name': 'M-Pesa', 'provider': 'mpesa', 'requires_phone': True, 'requires_prepayment': True},
    {'code': 'airtel_money', 'name': 'Airtel Money', 'provider': 'airtel_money', 'requires_phone': True, 'requires_prepayment': True},
    {'code': 'credit_card', 'name': 'Credit Card', 'provider': 'card', 'requires_phone': False, 'requires_prepayment': True},
    {'code': 'debit_card', 'name': 'Debit Card', 'provider': 'card', 'requires_phone': False, 'requires_prepayment': True},
    {'code': 'bank_transfer', 'name': 'Bank Transfer', 'provider': 'bank_transfer', 'requires_phone': False, 'requires_prepayment': False},
    {'code': 'cash_on_delivery', 'name': 'Cash on Delivery', 'provider': 'cash_on_delivery', 'requires_phone': False, 'requires_prepayment': False},
]

MPESA_BASE_URL = env('MPESA_BASE_URL', default='https://sandbox.safaricom.co.ke')
MPESA_CONSUMER_KEY = env('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = env('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = env('MPESA_SHORTCODE', default='')
MPESA_PASSKEY = env('MPESA_PASSKEY', default='')
MPESA_CALLBACK_URL = env('MPESA_CALLBACK_URL', default='')
MPESA_TRANSACTION_TYPE = env('MPESA_TRANSACTION_TYPE', default='CustomerPayBillOnline')
MPESA_TIMEOUT_SECONDS = env.int('MPESA_TIMEOUT_SECONDS', default=30)
AIRTEL_MONEY_SANDBOX_ENABLED = env.bool('AIRTEL_MONEY_SANDBOX_ENABLED', default=True)
AIRTEL_MONEY_PROVIDER_NAME = env('AIRTEL_MONEY_PROVIDER_NAME', default='sandbox_airtel_money')
CARD_SANDBOX_ENABLED = env.bool('CARD_SANDBOX_ENABLED', default=True)
CARD_PROVIDER_NAME = env('CARD_PROVIDER_NAME', default='sandbox_card')

