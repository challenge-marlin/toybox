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

# Email backend (use SMTP if EMAIL_HOST is configured, otherwise console for development)
# Support both EMAIL_* and SMTP_* environment variable names for compatibility
EMAIL_HOST = os.environ.get('EMAIL_HOST') or os.environ.get('SMTP_HOST', '')
if EMAIL_HOST and EMAIL_HOST != 'localhost':
    # Use SMTP if EMAIL_HOST is configured
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT') or os.environ.get('SMTP_PORT', '587'))
    EMAIL_USE_TLS = (os.environ.get('EMAIL_USE_TLS') or os.environ.get('SMTP_USE_TLS', 'true')).lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER') or os.environ.get('SMTP_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD') or os.environ.get('SMTP_PASS', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL') or os.environ.get('MAIL_FROM', 'noreply@toybox.local')
else:
    # Use console backend for development if EMAIL_HOST is not configured
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

