from .base import *


DEBUG = False

# Performance tests must not send customer or operational email.
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Keep throttling middleware active while raising limits above the intended
# test volume. Normal local and production settings remain unchanged.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        scope: env(
            f'LOAD_TEST_{scope.upper()}_RATE',
            default='1000000/hour',
        )
        for scope in REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    },
}
