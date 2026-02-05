from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import ValidationError, PermissionDenied
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    # If DRF didn't handle the exception, create a custom response
    if response is None:
        if isinstance(exc, Http404):
            response = Response(
                {
                    "error": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "details": str(exc)
                },
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, PermissionDenied):
            response = Response(
                {
                    "error": "PERMISSION_DENIED",
                    "message": "You do not have permission to perform this action.",
                    "details": str(exc)
                },
                status=status.HTTP_403_FORBIDDEN
            )
        elif isinstance(exc, ValidationError):
            response = Response(
                {
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid data provided.",
                    "details": getattr(exc, 'message_dict', str(exc))
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # Log unexpected errors
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            response = Response(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": str(exc) if settings.DEBUG else "Internal server error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Customize the response format
    if response is not None:
        custom_response_data = {
            "error": get_error_code(exc, response),
            "message": get_error_message(exc, response),
            "details": get_error_details(exc, response)
        }
        
        # Add request ID for debugging
        if hasattr(context.get('request'), 'id'):
            custom_response_data['request_id'] = context['request'].id
        
        response.data = custom_response_data
    
    return response


def get_error_code(exc, response):
    """Get standardized error code"""
    if hasattr(exc, 'default_code'):
        return exc.default_code.upper()
    elif response.status_code == 400:
        return "BAD_REQUEST"
    elif response.status_code == 401:
        return "UNAUTHORIZED"
    elif response.status_code == 403:
        return "FORBIDDEN"
    elif response.status_code == 404:
        return "NOT_FOUND"
    elif response.status_code == 405:
        return "METHOD_NOT_ALLOWED"
    elif response.status_code == 429:
        return "RATE_LIMITED"
    elif response.status_code >= 500:
        return "INTERNAL_SERVER_ERROR"
    else:
        return "UNKNOWN_ERROR"


def get_error_message(exc, response):
    """Get user-friendly error message"""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Handle field-specific errors
            if 'non_field_errors' in exc.detail:
                return exc.detail['non_field_errors'][0]
            elif 'detail' in exc.detail:
                return exc.detail['detail']
            else:
                return "Validation failed."
        else:
            return str(exc.detail)
    elif hasattr(exc, 'message'):
        return exc.message
    else:
        return response.reason_phrase


def get_error_details(exc, response):
    """Get detailed error information"""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Return field-specific errors
            return {k: v if isinstance(v, list) else [v] for k, v in exc.detail.items()}
        return str(exc.detail)
    elif hasattr(exc, 'message_dict'):
        return exc.message_dict
    else:
        return None


class APIError(Exception):
    """Base API error class"""
    def __init__(self, message, error_code=None, status_code=400, details=None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class InsufficientFundsError(APIError):
    """Raised when account has insufficient funds"""
    def __init__(self, message="Insufficient funds for this operation."):
        super().__init__(message, "INSUFFICIENT_FUNDS", 400)


class AccountNotFoundError(APIError):
    """Raised when account is not found"""
    def __init__(self, message="Account not found."):
        super().__init__(message, "ACCOUNT_NOT_FOUND", 404)


class TransactionNotFoundError(APIError):
    """Raised when transaction is not found"""
    def __init__(self, message="Transaction not found."):
        super().__init__(message, "TRANSACTION_NOT_FOUND", 404)


class InvalidTransactionStateError(APIError):
    """Raised when transaction is in invalid state"""
    def __init__(self, message="Transaction is in invalid state for this operation."):
        super().__init__(message, "INVALID_TRANSACTION_STATE", 400)


class DailyLimitExceededError(APIError):
    """Raised when daily transaction limit is exceeded"""
    def __init__(self, message="Daily transaction limit exceeded."):
        super().__init__(message, "DAILY_LIMIT_EXCEEDED", 429)


class AccountFrozenError(APIError):
    """Raised when account is frozen"""
    def __init__(self, message="Account is frozen and cannot perform operations."):
        super().__init__(message, "ACCOUNT_FROZEN", 403)
