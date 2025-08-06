"""
Authentication Middleware

This module provides middleware for protecting routes and validating authentication
across the application.
"""

from datetime import datetime
from typing import List, Optional, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from ..services.auth_service import get_auth_manager


# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for protected routes."""
    
    def __init__(self, app, protected_paths: Optional[List[str]] = None, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.protected_paths = protected_paths or []
        self.excluded_paths = excluded_paths or [
            "/auth/login",
            "/auth/logout", 
            "/auth/health",
            "/auth/dev/bypass-status",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static/"
        ]
        self.logger = logger
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process authentication for each request."""
        try:
            path = request.url.path
            method = request.method
            
            # Check if path should be excluded from authentication
            if self._is_excluded_path(path):
                return await call_next(request)
            
            # Check if path requires authentication
            if self._requires_authentication(path):
                auth_result = await self._validate_authentication(request)
                
                if not auth_result['is_authenticated']:
                    return self._create_auth_error_response(auth_result['error'])
                
                # Add user info to request state
                request.state.user = auth_result['user_info']
                request.state.authenticated = True
                
                # Log successful authentication
                self.logger.info(f"Authenticated request: {method} {path}")
            
            # Continue with request processing
            response = await call_next(request)
            return response
            
        except Exception as e:
            self.logger.error(f"Authentication middleware error: {e}")
            return Response(
                content=f"Authentication error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from authentication."""
        for excluded_path in self.excluded_paths:
            if excluded_path.endswith('/'):
                if path.startswith(excluded_path):
                    return True
            elif path == excluded_path:
                return True
        return False
    
    def _requires_authentication(self, path: str) -> bool:
        """Check if path requires authentication."""
        # If no protected paths specified, protect all non-excluded paths
        if not self.protected_paths:
            return True
        
        # Check if path matches any protected pattern
        for protected_path in self.protected_paths:
            if protected_path.endswith('/'):
                if path.startswith(protected_path):
                    return True
            elif path == protected_path:
                return True
        
        return False
    
    async def _validate_authentication(self, request: Request) -> dict:
        """Validate authentication for the request."""
        try:
            # Get authentication manager
            auth_manager = get_auth_manager()
            if not auth_manager:
                return {
                    'is_authenticated': False,
                    'error': 'Authentication service not available',
                    'user_info': None
                }
            
            # Check if user is authenticated
            if not auth_manager.is_authenticated():
                return {
                    'is_authenticated': False,
                    'error': 'User not authenticated',
                    'user_info': None
                }
            
            # Get session info
            session_info = auth_manager.get_session_info()
            if not session_info:
                return {
                    'is_authenticated': False,
                    'error': 'Invalid session',
                    'user_info': None
                }
            
            # Check if license is required and validated
            if not auth_manager.is_license_validated():
                # Allow access to license verification endpoint
                if request.url.path != "/auth/verify-license":
                    return {
                        'is_authenticated': False,
                        'error': 'License verification required',
                        'user_info': None
                    }
            
            return {
                'is_authenticated': True,
                'error': None,
                'user_info': session_info
            }
            
        except Exception as e:
            self.logger.error(f"Authentication validation error: {e}")
            return {
                'is_authenticated': False,
                'error': f'Authentication validation failed: {str(e)}',
                'user_info': None
            }
    
    def _create_auth_error_response(self, error_message: str) -> Response:
        """Create standardized authentication error response."""
        return Response(
            content=f'{{"error": "{error_message}", "status_code": 401}}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            media_type="application/json",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    """
    Dependency to get current authenticated user.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        dict: Current user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        auth_manager = get_auth_manager()
        if not auth_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service not available"
            )
        
        if not auth_manager.is_authenticated():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        session_info = auth_manager.get_session_info()
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return session_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def require_license_validation(current_user: dict = get_current_user):
    """
    Dependency to ensure license is validated.
    
    Args:
        current_user: Current user dependency
        
    Returns:
        dict: Current user information
        
    Raises:
        HTTPException: If license is not validated
    """
    try:
        auth_manager = get_auth_manager()
        if not auth_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service not available"
            )
        
        if not auth_manager.is_license_validated():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="License verification required"
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"License validation check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"License validation error: {str(e)}"
        )


class SessionManager:
    """Manages user sessions and authentication state."""
    
    def __init__(self):
        self.logger = logger
    
    async def create_session(self, user_info: dict) -> str:
        """
        Create a new user session.
        
        Args:
            user_info (dict): User information
            
        Returns:
            str: Session ID
        """
        try:
            # In a real implementation, you might store session in Redis or database
            # For now, we rely on Supabase's session management
            session_id = f"session_{user_info.get('user_id')}_{datetime.utcnow().timestamp()}"
            
            self.logger.info(f"Session created: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Session creation error: {e}")
            raise
    
    async def validate_session(self, session_id: str) -> dict:
        """
        Validate a user session.
        
        Args:
            session_id (str): Session ID to validate
            
        Returns:
            dict: Session validation result
        """
        try:
            # Validate with auth manager
            auth_manager = get_auth_manager()
            if not auth_manager:
                return {'valid': False, 'error': 'Auth service unavailable'}
            
            if auth_manager.is_authenticated():
                session_info = auth_manager.get_session_info()
                return {'valid': True, 'session_info': session_info}
            else:
                return {'valid': False, 'error': 'Session expired'}
                
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return {'valid': False, 'error': str(e)}
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a user session.
        
        Args:
            session_id (str): Session ID to invalidate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            auth_manager = get_auth_manager()
            if auth_manager:
                await auth_manager.logout()
            
            self.logger.info(f"Session invalidated: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Session invalidation error: {e}")
            return False


# Global session manager instance
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return session_manager


def create_auth_middleware(protected_paths: Optional[List[str]] = None, excluded_paths: Optional[List[str]] = None) -> AuthenticationMiddleware:
    """
    Factory function to create authentication middleware.
    
    Args:
        protected_paths: List of paths that require authentication
        excluded_paths: List of paths to exclude from authentication
        
    Returns:
        AuthenticationMiddleware: Configured middleware instance
    """
    return AuthenticationMiddleware(
        app=None,  # Will be set when added to FastAPI app
        protected_paths=protected_paths,
        excluded_paths=excluded_paths
    )