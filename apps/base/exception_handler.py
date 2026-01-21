"""
Custom exception handler for Django REST Framework.
Handles Django ValidationError from model clean() methods.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError


def custom_exception_handler(exc, context):
    """
    Custom exception handler to convert Django ValidationError to DRF format.
    
    This handles ValidationErrors raised by model.clean() methods and converts
    them into properly formatted API responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If DRF didn't handle it and it's a Django ValidationError
    if response is None and isinstance(exc, DjangoValidationError):
        # Handle ValidationError from model clean() methods
        if hasattr(exc, 'message_dict'):
            # Field-specific errors
            errors = {}
            for field, messages in exc.message_dict.items():
                if isinstance(messages, list):
                    errors[field] = messages
                else:
                    errors[field] = [str(messages)]
            
            return Response(
                errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif hasattr(exc, 'messages'):
            # Non-field errors (general validation errors)
            return Response(
                {'non_field_errors': exc.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Fallback for any other ValidationError format
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return response
