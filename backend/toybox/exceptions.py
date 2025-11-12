"""
Custom exception handlers for DRF.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('toybox')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response data structure
        custom_response_data = {
            'status': response.status_code,
            'code': getattr(exc, 'code', 'ERROR'),
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'details': None,
        }
        
        # Handle validation errors
        if response.status_code == 400:
            if isinstance(exc.detail, dict):
                custom_response_data['code'] = 'VALIDATION_ERROR'
                custom_response_data['details'] = exc.detail
            elif isinstance(exc.detail, list):
                custom_response_data['code'] = 'VALIDATION_ERROR'
                custom_response_data['details'] = exc.detail
        
        # Log errors
        if response.status_code >= 500:
            logger.error('request.error: %s %s - %s', 
                        context['request'].method,
                        context['request'].path,
                        custom_response_data['code'],
                        extra={
                            'method': context['request'].method,
                            'url': context['request'].path,
                            'code': custom_response_data['code'],
                            'error_msg': custom_response_data['message'],
                        })
        elif response.status_code >= 400:
            logger.warning('request.client_error: %s %s - %s', 
                          context['request'].method,
                          context['request'].path,
                          custom_response_data['code'],
                          extra={
                              'method': context['request'].method,
                              'url': context['request'].path,
                              'code': custom_response_data['code'],
                              'error_msg': custom_response_data['message'],
                          },
                          exc_info=False)
        
        response.data = custom_response_data
    
    return response

