"""
Centralized Error Handling Utilities
Reduces redundant error handling patterns across the codebase
"""

import functools
import logging
from typing import Callable, Any, Optional
from fastapi import HTTPException
from app.utils.logger import app_logger

class ErrorHandler:
    """Centralized error handling for consistent error responses"""
    
    @staticmethod
    def handle_api_errors(operation_name: str, status_code: int = 500):
        """
        Decorator for consistent API error handling
        
        Args:
            operation_name: Human-readable operation name for error messages
            status_code: HTTP status code to return on error
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except HTTPException:
                    # Re-raise HTTPExceptions as-is
                    raise
                except Exception as e:
                    app_logger.error(f"Failed to {operation_name}: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=status_code, 
                        detail=f"Failed to {operation_name}: {str(e)}"
                    )
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except HTTPException:
                    # Re-raise HTTPExceptions as-is
                    raise
                except Exception as e:
                    app_logger.error(f"Failed to {operation_name}: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=status_code, 
                        detail=f"Failed to {operation_name}: {str(e)}"
                    )
            
            # Return appropriate wrapper based on function type
            return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    @staticmethod
    def handle_service_errors(service_name: str, default_return: Any = None):
        """
        Decorator for service layer error handling with optional default return
        
        Args:
            service_name: Name of the service for logging
            default_return: Value to return on error (None will re-raise)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    app_logger.error(f"{service_name} error in {func.__name__}: {e}", exc_info=True)
                    if default_return is not None:
                        return default_return
                    raise
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    app_logger.error(f"{service_name} error in {func.__name__}: {e}", exc_info=True)
                    if default_return is not None:
                        return default_return
                    raise
            
            return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper
        return decorator

    @staticmethod
    def log_and_ignore(logger: Optional[logging.Logger] = None, message: str = ""):
        """
        Decorator to log errors and continue execution
        
        Args:
            logger: Logger instance to use (defaults to app_logger)
            message: Additional message to include in log
        """
        log = logger or app_logger
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    log.warning(f"{message} {func.__name__} failed: {e}")
                    return None
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    log.warning(f"{message} {func.__name__} failed: {e}")
                    return None
            
            return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper
        return decorator

# Common error response formatters
class APIErrorResponses:
    """Standard API error response formats"""
    
    @staticmethod
    def not_found(resource: str, identifier: str = "") -> HTTPException:
        """Standard 404 response"""
        detail = f"{resource} not found"
        if identifier:
            detail += f": {identifier}"
        return HTTPException(status_code=404, detail=detail)
    
    @staticmethod
    def validation_error(message: str) -> HTTPException:
        """Standard 400 validation error"""
        return HTTPException(status_code=400, detail=f"Validation error: {message}")
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> HTTPException:
        """Standard 401 unauthorized error"""
        return HTTPException(status_code=401, detail=message)
    
    @staticmethod
    def forbidden(message: str = "Forbidden") -> HTTPException:
        """Standard 403 forbidden error"""
        return HTTPException(status_code=403, detail=message)
    
    @staticmethod
    def internal_error(operation: str) -> HTTPException:
        """Standard 500 internal error"""
        return HTTPException(status_code=500, detail=f"Internal error during {operation}")

# Retry decorator for transient failures
class RetryHandler:
    """Retry logic for transient failures"""
    
    @staticmethod
    def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """
        Retry decorator with exponential backoff
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries (seconds)
            backoff: Multiplier for delay on each retry
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            app_logger.warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {current_delay}s..."
                            )
                            import asyncio
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            app_logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                
                raise last_exception
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            app_logger.warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {current_delay}s..."
                            )
                            import time
                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            app_logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                
                raise last_exception
            
            return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper
        return decorator

# Context managers for error handling
class ErrorContext:
    """Context manager for consistent error handling"""
    
    def __init__(self, operation: str, logger: Optional[logging.Logger] = None, 
                 reraise: bool = True, default_return: Any = None):
        self.operation = operation
        self.logger = logger or app_logger
        self.reraise = reraise
        self.default_return = default_return
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Error during {self.operation}: {exc_val}", exc_info=True)
            if not self.reraise:
                return True  # Suppress the exception
        return False

# Validation helpers
class ValidationHelper:
    """Common validation patterns"""
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: list) -> None:
        """Validate that all required fields are present"""
        missing = [field for field in required_fields if field not in data or data[field] is None]
        if missing:
            raise APIErrorResponses.validation_error(f"Missing required fields: {', '.join(missing)}")
    
    @staticmethod
    def validate_range(value: float, min_val: float, max_val: float, field_name: str) -> None:
        """Validate that a value is within a specified range"""
        if not (min_val <= value <= max_val):
            raise APIErrorResponses.validation_error(
                f"{field_name} must be between {min_val} and {max_val}, got {value}"
            )
    
    @staticmethod
    def validate_enum(value: str, valid_values: list, field_name: str) -> None:
        """Validate that a value is one of the allowed enum values"""
        if value not in valid_values:
            raise APIErrorResponses.validation_error(
                f"{field_name} must be one of {valid_values}, got '{value}'"
            )