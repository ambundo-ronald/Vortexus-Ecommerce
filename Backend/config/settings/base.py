import json
from pathlib import Path

import environ
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
    'apps.accounts',
    'apps.marketplace',
    'apps.notifications',
    'apps.search',
    'apps.image_search',
    'apps.recommendations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
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
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'EXCEPTION_HANDLER': 'apps.api.exceptions.api_exception_handler',
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

ENABLE_ASYNC_TASKS = env.bool('ENABLE_ASYNC_TASKS', default=False)

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

