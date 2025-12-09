#!/usr/bin/env python
"""Test email sending."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toybox.settings.dev')

import django
django.setup()

from django.conf import settings
from frontend.email_utils import send_form_email, validate_email_config, get_email_config
import traceback

print('=' * 60)
print('Email Configuration:')
config = get_email_config()
print(f'EMAIL_HOST: {config["host"]}')
print(f'EMAIL_PORT: {config["port"]}')
print(f'EMAIL_BACKEND: {config["backend"]}')
print(f'EMAIL_HOST_USER: {config["user"] or "(empty)"}')
print(f'EMAIL_USE_TLS: {getattr(settings, "EMAIL_USE_TLS", False)}')
print(f'DEFAULT_FROM_EMAIL: {config["from_email"]}')
print(f'CONTACT_EMAIL: {config["to_email"]}')
print('=' * 60)

# Validate configuration
print('\nValidating email configuration...')
is_valid, error_msg = validate_email_config()
if not is_valid:
    print(f'⚠️  Configuration issue: {error_msg}')
else:
    print('✓ Configuration looks good')

print('\nAttempting to send test email...')
success, error_msg = send_form_email(
    subject='Test Subject',
    body='Test body from refactored email utility',
)

if success:
    print('\n✓ SUCCESS: Email sent successfully!')
else:
    print(f'\n✗ ERROR: {error_msg}')
    print('\nFull traceback:')
    traceback.print_exc()
    
    # Additional diagnostic info
    if error_msg and 'Relay access denied' in error_msg:
        print('\n' + '=' * 60)
        print('DIAGNOSIS: Relay access denied')
        print('This usually means:')
        print('1. SMTP authentication is required but not configured')
        print('2. The FROM email address domain does not match the SMTP server domain')
        print('3. The SMTP server requires IP-based authentication')
        print('\nSOLUTION:')
        print('Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env:')
        print('EMAIL_HOST_USER=your-email@ayatori-inc.co.jp')
        print('EMAIL_HOST_PASSWORD=your-password')
        print('=' * 60)

