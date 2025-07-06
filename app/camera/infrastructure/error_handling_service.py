import logging
import traceback
import uuid
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime

from ..domain.entities import (
    ErrorType,
    ErrorSeverity,
    ErrorDetails,
    ErrorResponse,
    CameraControlError,
    TimeoutError,
    PermissionError,
    Result,
)


class ErrorHandlingService:
    """Centralized error handling service for the camera module."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._error_handlers: Dict[ErrorType, Any] = {}
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Setup default error handlers for different error types."""
        self._error_handlers = {
            ErrorType.VALIDATION_ERROR: self._handle_validation_error,
            ErrorType.CONFIGURATION_ERROR: self._handle_configuration_error,
            ErrorType.CAMERA_ERROR: self._handle_camera_error,
            ErrorType.CHDKPTP_ERROR: self._handle_chdkptp_error,
            ErrorType.FILE_ERROR: self._handle_file_error,
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.PERMISSION_ERROR: self._handle_permission_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorType.RESOURCE_ERROR: self._handle_resource_error,
            ErrorType.APPLICATION_ERROR: self._handle_application_error,
            ErrorType.UNKNOWN_ERROR: self._handle_unknown_error,
        }

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> ErrorResponse:
        """Handle an error and return a standardized error response."""
        try:
            # Generate request ID if not provided
            if not request_id:
                request_id = str(uuid.uuid4())

            # Determine error type and details
            error_type, error_details = self._analyze_error(error, context)

            # Log the error
            self._log_error(error, error_type, error_details, request_id)

            # Get appropriate handler
            handler = self._error_handlers.get(error_type, self._handle_unknown_error)

            # Create error response
            response = handler(error, error_details, request_id)

            return response

        except Exception as e:
            # Fallback error handling
            self.logger.error(f"Error in error handler: {e}")
            return ErrorResponse(
                success=False,
                error_type=ErrorType.UNKNOWN_ERROR.value,
                message="An unexpected error occurred while handling another error",
                code="ERROR_HANDLER_FAILURE",
                request_id=request_id,
            )

    def _analyze_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> tuple[ErrorType, ErrorDetails]:
        """Analyze an error and determine its type and details."""

        # Handle custom camera control errors
        if isinstance(error, CameraControlError):
            error_type = error.error_type
            details = ErrorDetails(
                error_type=error_type,
                message=str(error),
                code=error.code,
                details=error.details,
                context=context,
            )
            return error_type, details

        # Handle specific exception types
        if isinstance(error, ValueError):
            error_type = ErrorType.VALIDATION_ERROR
        elif isinstance(error, FileNotFoundError):
            error_type = ErrorType.FILE_ERROR
        elif isinstance(error, PermissionError):
            error_type = ErrorType.PERMISSION_ERROR
        elif isinstance(error, TimeoutError):
            error_type = ErrorType.TIMEOUT_ERROR
        elif isinstance(error, OSError):
            error_type = ErrorType.FILE_ERROR
        else:
            error_type = ErrorType.UNKNOWN_ERROR

        details = ErrorDetails(
            error_type=error_type,
            message=str(error),
            code=type(error).__name__,
            details={"exception_type": type(error).__name__},
            context=context,
        )

        return error_type, details

    def _log_error(
        self,
        error: Exception,
        error_type: ErrorType,
        error_details: ErrorDetails,
        request_id: str,
    ):
        """Log error with appropriate level and details."""
        log_message = (
            f"Error [{request_id}] - Type: {error_type.value}, "
            f"Message: {error_details.message}"
        )

        if error_details.code:
            log_message += f", Code: {error_details.code}"

        if error_details.context:
            log_message += f", Context: {error_details.context}"

        # Log with appropriate level based on error type
        if error_type in [ErrorType.VALIDATION_ERROR, ErrorType.CONFIGURATION_ERROR]:
            self.logger.warning(log_message)
        elif error_type in [ErrorType.CAMERA_ERROR, ErrorType.CHDKPTP_ERROR]:
            self.logger.error(log_message)
        else:
            self.logger.error(log_message)

        # Log full traceback for debugging
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(
                f"Full traceback for error [{request_id}]:\n{traceback.format_exc()}"
            )

    def _handle_validation_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle validation errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.VALIDATION_ERROR.value,
            message=details.message,
            code=details.code or "VALIDATION_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=400,
        )

    def _handle_configuration_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle configuration errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.CONFIGURATION_ERROR.value,
            message=details.message,
            code=details.code or "CONFIGURATION_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=500,
        )

    def _handle_camera_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle camera-related errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.CAMERA_ERROR.value,
            message=details.message,
            code=details.code or "CAMERA_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=500,
        )

    def _handle_chdkptp_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle CHDKPTP-related errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.CHDKPTP_ERROR.value,
            message=details.message,
            code=details.code or "CHDKPTP_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=500,
        )

    def _handle_file_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle file operation errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.FILE_ERROR.value,
            message=details.message,
            code=details.code or "FILE_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=500,
        )

    def _handle_network_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle network-related errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.NETWORK_ERROR.value,
            message=details.message,
            code=details.code or "NETWORK_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=503,
        )

    def _handle_permission_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle permission errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.PERMISSION_ERROR.value,
            message=details.message,
            code=details.code or "PERMISSION_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=403,
        )

    def _handle_timeout_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle timeout errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.TIMEOUT_ERROR.value,
            message=details.message,
            code=details.code or "TIMEOUT_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=408,
        )

    def _handle_resource_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle resource-related errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.RESOURCE_ERROR.value,
            message=details.message,
            code=details.code or "RESOURCE_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=503,
        )

    def _handle_application_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle application-related errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.APPLICATION_ERROR.value,
            message=details.message,
            code=details.code or "APPLICATION_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=500,
        )

    def _handle_unknown_error(
        self, error: Exception, details: ErrorDetails, request_id: str
    ) -> ErrorResponse:
        """Handle unknown errors."""
        return ErrorResponse(
            success=False,
            error_type=ErrorType.UNKNOWN_ERROR.value,
            message="An unexpected error occurred",
            code=details.code or "UNKNOWN_ERROR",
            details=details.details,
            request_id=request_id,
            status_code=500,
        )

    def register_error_handler(self, error_type: ErrorType, handler: Any):
        """Register a custom error handler for a specific error type."""
        self._error_handlers[error_type] = handler

    def create_success_response(
        self, data: Any, request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized success response."""
        if not request_id:
            request_id = str(uuid.uuid4())

        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
        }

    def generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())

    def handle_exception(
        self,
        exc: Exception,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorResponse:
        """Handle an exception and return a standardized error response."""
        if not request_id:
            request_id = self.generate_request_id()

        return self.handle_error(exc, context, request_id)

    def record_error(
        self,
        error_type: ErrorType,
        message: str,
        severity: ErrorSeverity,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an error for logging and monitoring purposes."""
        if not request_id:
            request_id = self.generate_request_id()

        # Log the error with appropriate level based on severity
        log_message = (
            f"Error [{request_id}] - Type: {error_type.value}, "
            f"Severity: {severity.value}, Message: {message}"
        )

        if severity.value == "low":
            self.logger.warning(log_message)
        elif severity.value == "medium":
            self.logger.error(log_message)
        elif severity.value == "high":
            self.logger.error(log_message)
        elif severity.value == "critical":
            self.logger.critical(log_message)
        else:
            self.logger.error(log_message)

        if context:
            self.logger.debug(f"Error context [{request_id}]: {context}")

    def wrap_async_function(self, func: Any, context: Optional[Dict[str, Any]] = None):
        """Decorator to wrap async functions with error handling."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_response = self.handle_error(e, context, request_id)
                return Result.failure(error_response.message)

        return wrapper

    def wrap_sync_function(self, func: Any, context: Optional[Dict[str, Any]] = None):
        """Decorator to wrap sync functions with error handling."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_response = self.handle_error(e, context, request_id)
                return Result.failure(error_response.message)

        return wrapper


# Global error handling service instance
_error_handling_service: Optional[ErrorHandlingService] = None


def get_error_handling_service() -> ErrorHandlingService:
    """Get or create the global error handling service instance."""
    global _error_handling_service

    if _error_handling_service is None:
        _error_handling_service = ErrorHandlingService()

    return _error_handling_service


def reset_error_handling_service() -> None:
    """Reset the global error handling service instance."""
    global _error_handling_service
    _error_handling_service = None


# Convenience decorators
def handle_errors(context: Optional[Dict[str, Any]] = None):
    """Decorator to add error handling to async functions."""

    def decorator(func: Any):
        return get_error_handling_service().wrap_async_function(func, context)

    return decorator


def handle_sync_errors(context: Optional[Dict[str, Any]] = None):
    """Decorator to add error handling to sync functions."""

    def decorator(func: Any):
        return get_error_handling_service().wrap_sync_function(func, context)

    return decorator
