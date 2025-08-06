"""
Authentication API Endpoints

This module provides REST API endpoints for authentication, license verification,
and session management using FastAPI.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, EmailStr, Field
from loguru import logger

from ..services.auth_service import get_auth_manager, AuthenticationManager
from ..utils.system_info import get_system_info_for_auth
from ..utils.certificate_validator import get_certificate_status


# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    use_bypass: bool = Field(default=False, description="Use development bypass (dev only)")

class LoginResponse(BaseModel):
    success: bool
    message: str
    session: Optional[Dict[str, Any]] = None
    requires_license: bool = False
    error: Optional[str] = None

class LicenseVerificationRequest(BaseModel):
    license_uuid: str = Field(..., min_length=36, max_length=36, description="License UUID")
    use_bypass: bool = Field(default=False, description="Use development bypass (dev only)")

class LicenseVerificationResponse(BaseModel):
    success: bool
    message: str
    license_id: Optional[str] = None
    system_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class LogoutResponse(BaseModel):
    success: bool
    message: str

class SessionResponse(BaseModel):
    is_authenticated: bool
    session_info: Optional[Dict[str, Any]] = None
    license_validated: bool = False
    certificate_status: Optional[Dict[str, Any]] = None

class SystemInfoResponse(BaseModel):
    system_info: Dict[str, Any]
    certificate_status: Dict[str, Any]
    timestamp: str


# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service() -> AuthenticationManager:
    """Dependency to get authentication manager."""
    auth_manager = get_auth_manager()
    if not auth_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not initialized"
        )
    return auth_manager


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthenticationManager = Depends(get_auth_service)
):
    """
    Authenticate user with email and password.
    
    Args:
        request: Login credentials
        auth_service: Authentication service dependency
        
    Returns:
        LoginResponse: Authentication result
    """
    try:
        logger.info(f"Login attempt for email: {request.email}")
        
        # Authenticate user
        success, response_data = await auth_service.authenticate(
            email=request.email,
            password=request.password,
            use_bypass=request.use_bypass
        )
        
        if success:
            return LoginResponse(
                success=True,
                message=response_data.get('message', 'Authentication successful'),
                session=response_data.get('session'),
                requires_license=response_data.get('requires_license', False)
            )
        else:
            return LoginResponse(
                success=False,
                message="Authentication failed",
                error=response_data.get('error', 'Invalid credentials')
            )
            
    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@auth_router.post("/verify-license", response_model=LicenseVerificationResponse)
async def verify_license(
    request: LicenseVerificationRequest,
    auth_service: AuthenticationManager = Depends(get_auth_service)
):
    """
    Verify license key for authenticated user.
    
    Args:
        request: License verification request
        auth_service: Authentication service dependency
        
    Returns:
        LicenseVerificationResponse: License verification result
    """
    try:
        # Check if user is authenticated (allow bypass mode)
        if not auth_service.is_authenticated() and not request.use_bypass:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User must be authenticated before license verification"
            )
        
        logger.info(f"License verification attempt: {request.license_uuid}")
        
        # Verify license
        success, response_data = await auth_service.verify_license(
            license_uuid=request.license_uuid,
            use_bypass=request.use_bypass
        )
        
        if success:
            return LicenseVerificationResponse(
                success=True,
                message=response_data.get('message', 'License verified successfully'),
                license_id=response_data.get('license_id'),
                system_info=response_data.get('system_info')
            )
        else:
            return LicenseVerificationResponse(
                success=False,
                message="License verification failed",
                error=response_data.get('error', 'Invalid license')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"License verification endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"License verification error: {str(e)}"
        )


@auth_router.post("/logout", response_model=LogoutResponse)
async def logout(auth_service: AuthenticationManager = Depends(get_auth_service)):
    """
    Logout current user and clear session.
    
    Args:
        auth_service: Authentication service dependency
        
    Returns:
        LogoutResponse: Logout result
    """
    try:
        success = await auth_service.logout()
        
        if success:
            return LogoutResponse(
                success=True,
                message="Logout successful"
            )
        else:
            return LogoutResponse(
                success=False,
                message="Logout failed"
            )
            
    except Exception as e:
        logger.error(f"Logout endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}"
        )


@auth_router.get("/session", response_model=SessionResponse)
async def get_session(auth_service: AuthenticationManager = Depends(get_auth_service)):
    """
    Get current session information.
    
    Args:
        auth_service: Authentication service dependency
        
    Returns:
        SessionResponse: Current session information
    """
    try:
        is_authenticated = auth_service.is_authenticated()
        session_info = auth_service.get_session_info() if is_authenticated else None
        license_validated = auth_service.is_license_validated()
        certificate_status = get_certificate_status()
        
        return SessionResponse(
            is_authenticated=is_authenticated,
            session_info=session_info,
            license_validated=license_validated,
            certificate_status=certificate_status
        )
        
    except Exception as e:
        logger.error(f"Session endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session retrieval error: {str(e)}"
        )


@auth_router.get("/system-info", response_model=SystemInfoResponse)
async def get_system_info(auth_service: AuthenticationManager = Depends(get_auth_service)):
    """
    Get system information for debugging/verification.
    
    Args:
        auth_service: Authentication service dependency
        
    Returns:
        SystemInfoResponse: System information
    """
    try:
        system_info = await get_system_info_for_auth()
        certificate_status = get_certificate_status()
        
        return SystemInfoResponse(
            system_info=system_info,
            certificate_status=certificate_status,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"System info endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System info error: {str(e)}"
        )


@auth_router.get("/health")
async def auth_health_check():
    """
    Health check endpoint for authentication service.
    
    Returns:
        dict: Health status
    """
    try:
        auth_manager = get_auth_manager()
        certificate_status = get_certificate_status()
        
        return {
            "status": "healthy",
            "service": "authentication",
            "auth_manager_initialized": auth_manager is not None,
            "certificate_status": certificate_status.get('status'),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Auth health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "authentication",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Additional endpoints for development/debugging
@auth_router.get("/dev/bypass-status")
async def get_bypass_status(auth_service: AuthenticationManager = Depends(get_auth_service)):
    """
    Get development bypass status (development only).
    
    Args:
        auth_service: Authentication service dependency
        
    Returns:
        dict: Bypass status information
    """
    try:
        bypass_enabled = auth_service.bypass_enabled
        
        return {
            "bypass_enabled": bypass_enabled,
            "environment": "development" if bypass_enabled else "production",
            "warning": "Bypass should be disabled in production" if bypass_enabled else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Bypass status endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bypass status error: {str(e)}"
        )


# Note: Middleware removed as APIRouter doesn't support middleware
# Request logging is handled by the main app middleware