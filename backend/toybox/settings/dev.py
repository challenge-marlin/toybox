"""
Development settings for ToyBox project.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development-specific apps
# Note: django_extensions is optional and may not be installed in all environments
# If you need it, ensure it's installed: pip install django-extensions
# INSTALLED_APPS += [
#     'django_extensions',  # Optional: useful for development
# ]

# Development database (can use SQLite for quick testing)
# DATABASES['default'] = {
#     'ENGINE': 'django.db.backends.sqlite3',
#     'NAME': BASE_DIR / 'db.sqlite3',
# }

# Email backend (console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging (more verbose in development)
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['toybox']['level'] = 'DEBUG'

# Disable cache in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# CORS for development
CORS_ALLOW_ALL_ORIGINS = True

