from .base import *

DEBUG = True

# Local development should not require an SMTP server.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
OSCAR_SEND_REGISTRATION_EMAIL = False

# Avoid hard dependency on local Redis during development.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'vortexus-local-cache',
    }
}
