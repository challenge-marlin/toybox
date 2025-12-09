"""
Email utility functions for sending emails from forms.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def get_email_config() -> Dict[str, Any]:
    """
    Get email configuration from Django settings.
    
    Returns:
        Dictionary containing email configuration.
    """
    return {
        'host': getattr(settings, 'EMAIL_HOST', None),
        'port': getattr(settings, 'EMAIL_PORT', None),
        'user': getattr(settings, 'EMAIL_HOST_USER', None),
        'backend': getattr(settings, 'EMAIL_BACKEND', None),
        'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@toybox.local'),
        'to_email': getattr(settings, 'CONTACT_EMAIL', 'maki@ayatori-inc.co.jp'),
    }


def is_console_backend() -> bool:
    """
    Check if email backend is console backend.
    
    Returns:
        True if console backend is used, False otherwise.
    """
    backend = getattr(settings, 'EMAIL_BACKEND', None)
    return backend == 'django.core.mail.backends.console.EmailBackend'


def send_form_email(
    subject: str,
    body: str,
    to_email: Optional[str] = None,
    fail_silently: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Send email from form submission.
    
    Args:
        subject: Email subject
        body: Email body
        to_email: Recipient email address (defaults to CONTACT_EMAIL setting)
        fail_silently: If True, don't raise exceptions on failure
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    config = get_email_config()
    
    # Use provided email or default from settings
    recipient = to_email or config['to_email']
    from_email = config['from_email']
    
    # Log email configuration
    logger.info(
        f'Email sending attempt - '
        f'EMAIL_HOST={config["host"]}, '
        f'EMAIL_PORT={config["port"]}, '
        f'EMAIL_HOST_USER={config["user"]}, '
        f'EMAIL_BACKEND={config["backend"]}, '
        f'FROM={from_email}, '
        f'TO={recipient}'
    )
    
    # Check if console backend is used
    if is_console_backend():
        logger.warning(
            'Email backend is console - email will be logged to console, not sent'
        )
    else:
        logger.info(
            f'Attempting to send email via SMTP: {config["host"]}:{config["port"]}'
        )
    
    try:
        send_mail(
            subject,
            body,
            from_email,
            [recipient],
            fail_silently=fail_silently,
        )
        
        if is_console_backend():
            logger.info('Email logged to console (development mode)')
        else:
            logger.info(f'Email sent successfully to {recipient}')
        
        return True, None
        
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f'Failed to send email: {error_msg}',
            exc_info=True
        )
        
        # Log email content for debugging
        logger.warning(
            f'Email content (sending failed):\n'
            f'Subject: {subject}\n'
            f'To: {recipient}\n'
            f'Body:\n{body}'
        )
        
        return False, error_msg


def validate_email_config() -> Tuple[bool, Optional[str]]:
    """
    Validate email configuration.
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    config = get_email_config()
    
    # Check if SMTP backend is configured but credentials are missing
    if not is_console_backend():
        if config['host'] and not config['user']:
            return False, (
                'SMTP authentication is required but EMAIL_HOST_USER is not set. '
                'Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env file.'
            )
        
        if config['host'] and not config['port']:
            return False, 'EMAIL_PORT is required when EMAIL_HOST is set.'
    
    return True, None

