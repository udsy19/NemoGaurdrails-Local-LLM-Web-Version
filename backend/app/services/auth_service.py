"""
Supabase Authentication Service

This module provides comprehensive authentication services using Supabase,
including user authentication, JWT token management, and license verification.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import httpx
from supabase import create_client, Client
from jose import jwt, JWTError
from loguru import logger

from ..utils.system_info import get_system_info_for_auth
from ..utils.certificate_validator import verify_license_signature, security_utils


class SupabaseAuthService:
    """Main authentication service using Supabase backend."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
        self._supabase_client: Optional[Client] = None
        self._current_session = None
        self._refresh_task = None
        self._license_validated = False
        
        # Initialize Supabase client
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize the Supabase client with configuration."""
        try:
            supabase_url = self.config.get('supabase', {}).get('url')
            anon_key = self.config.get('supabase', {}).get('anon_key')
            
            if not supabase_url or not anon_key:
                raise ValueError("Missing Supabase URL or anon key in configuration")
            
            self._supabase_client = create_client(supabase_url, anon_key)
            self.logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Authenticate user with Supabase.
        
        Args:
            email (str): User email address
            password (str): User password
            
        Returns:
            tuple: (success, response_data)
        """
        try:
            # Sanitize inputs
            email = security_utils.sanitize_input(email)
            
            if not email or not password:
                return False, {'error': 'Email and password are required'}
            
            # Authenticate with Supabase
            response = self._supabase_client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if response.user and response.session:
                self._current_session = response.session
                
                # Store session info
                session_data = {
                    'user_id': response.user.id,
                    'email': response.user.email,
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'expires_at': response.session.expires_at,
                    'authenticated_at': datetime.utcnow().isoformat()
                }
                
                # Start automatic token refresh
                self._start_token_refresh()
                
                self.logger.info(f"User authenticated successfully: {email}")
                
                return True, {
                    'success': True,
                    'message': 'Authentication successful',
                    'session': session_data,
                    'requires_license': not self._license_validated
                }
            else:
                return False, {'error': 'Invalid credentials'}
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, {'error': f'Authentication failed: {str(e)}'}
    
    async def verify_license(self, license_uuid: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify license with the license verification endpoint.
        
        Args:
            license_uuid (str): License UUID to verify
            
        Returns:
            tuple: (success, response_data)
        """
        try:
            # Validate license UUID format
            if not security_utils.validate_license_uuid_format(license_uuid):
                return False, {'error': 'Invalid license UUID format'}
            
            # Get current session token
            if not self._current_session:
                return False, {'error': 'User not authenticated'}
            
            # Get system information
            system_info = await get_system_info_for_auth()
            
            # Prepare license verification request
            verification_endpoint = self.config.get('license', {}).get('verification_endpoint')
            if not verification_endpoint:
                return False, {'error': 'License verification endpoint not configured'}
            
            request_data = {
                'licenseUUID': license_uuid,
                'macAddress': system_info.get('macAddress'),
                'ipAddress': system_info.get('ipAddress'),
                'systemFingerprint': system_info.get('fingerprint'),
                'platform': system_info.get('platform'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Make license verification request
            headers = {
                'Authorization': f'Bearer {self._current_session.access_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'LLMinate-Auth-Client/1.0'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    verification_endpoint,
                    json=request_data,
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Verify response signature if present
                if response_data.get('signature'):
                    signature_valid = await verify_license_signature(response_data)
                    if not signature_valid:
                        self.logger.warning("License response signature verification failed")
                        return False, {'error': 'Invalid license response signature'}
                
                # Check license status
                if response_data.get('status') == 'success':
                    self._license_validated = True
                    
                    self.logger.info(f"License verified successfully: {license_uuid}")
                    
                    return True, {
                        'success': True,
                        'message': 'License verified successfully',
                        'license_id': response_data.get('License ID'),
                        'system_info': system_info
                    }
                else:
                    return False, {
                        'error': response_data.get('message', 'License verification failed')
                    }
            else:
                self.logger.error(f"License verification failed: HTTP {response.status_code}")
                return False, {'error': f'License verification failed: HTTP {response.status_code}'}
                
        except httpx.TimeoutException:
            return False, {'error': 'License verification request timed out'}
        except Exception as e:
            self.logger.error(f"License verification error: {e}")
            return False, {'error': f'License verification failed: {str(e)}'}
    
    async def refresh_session(self) -> bool:
        """
        Refresh the current Supabase session.
        
        Returns:
            bool: True if refresh successful, False otherwise
        """
        try:
            if not self._current_session:
                return False
            
            # Refresh session with Supabase
            response = self._supabase_client.auth.refresh_session(
                self._current_session.refresh_token
            )
            
            if response.session:
                self._current_session = response.session
                self.logger.info("Session refreshed successfully")
                return True
            else:
                self.logger.error("Session refresh failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Session refresh error: {e}")
            return False
    
    def _start_token_refresh(self):
        """Start automatic token refresh background task."""
        if self._refresh_task:
            self._refresh_task.cancel()
        
        refresh_interval = self.config.get('jwt', {}).get('refresh_interval_minutes', 20)
        self._refresh_task = asyncio.create_task(self._token_refresh_loop(refresh_interval))
    
    async def _token_refresh_loop(self, interval_minutes: int):
        """Background task for automatic token refresh."""
        try:
            while True:
                await asyncio.sleep(interval_minutes * 60)  # Convert to seconds
                
                if self._current_session:
                    success = await self.refresh_session()
                    if not success:
                        self.logger.warning("Automatic token refresh failed")
                        # Could trigger re-authentication here if needed
                
        except asyncio.CancelledError:
            self.logger.info("Token refresh task cancelled")
        except Exception as e:
            self.logger.error(f"Token refresh loop error: {e}")
    
    async def logout(self) -> bool:
        """
        Logout the current user and cleanup session.
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        try:
            # Cancel refresh task
            if self._refresh_task:
                self._refresh_task.cancel()
                self._refresh_task = None
            
            # Sign out from Supabase
            if self._current_session:
                self._supabase_client.auth.sign_out()
            
            # Clear session data
            self._current_session = None
            self._license_validated = False
            
            self.logger.info("User logged out successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            return False
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        Get current session information.
        
        Returns:
            dict: Current session data or None if not authenticated
        """
        if not self._current_session:
            return None
        
        return {
            'user_id': self._current_session.user.id if self._current_session.user else None,
            'access_token': self._current_session.access_token,
            'expires_at': self._current_session.expires_at,
            'is_authenticated': True,
            'license_validated': self._license_validated
        }
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self._current_session is not None
    
    def is_license_validated(self) -> bool:
        """Check if license has been validated."""
        return self._license_validated
    
    async def validate_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a JWT token.
        
        Args:
            token (str): JWT token to validate
            
        Returns:
            tuple: (is_valid, payload)
        """
        try:
            # Use Supabase client to verify the token
            user = self._supabase_client.auth.get_user(token)
            
            if user:
                return True, {
                    'user_id': user.user.id,
                    'email': user.user.email,
                    'validated_at': datetime.utcnow().isoformat()
                }
            else:
                return False, None
                
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return False, None


class AuthenticationManager:
    """High-level authentication manager."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
        
        # Development bypass settings
        self.bypass_enabled = config.get('development', {}).get('bypass_enabled', False)
        self.test_email = config.get('development', {}).get('test_user_email')
        self.test_password = config.get('development', {}).get('test_user_password')
        
        # Try to initialize Supabase service, but allow bypass mode if it fails
        try:
            self.auth_service = SupabaseAuthService(config)
            self.supabase_available = True
            logger.info("Supabase authentication service initialized successfully")
        except Exception as e:
            self.auth_service = None
            self.supabase_available = False
            logger.warning(f"Supabase authentication failed to initialize: {e}")
            if self.bypass_enabled:
                logger.info("Bypass mode is enabled - authentication will work in development mode")
            else:
                logger.error("Authentication service unavailable and bypass mode is disabled")
    
    async def authenticate(self, email: str, password: str, use_bypass: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Authenticate user with optional development bypass.
        
        Args:
            email (str): User email
            password (str): User password
            use_bypass (bool): Whether to use development bypass
            
        Returns:
            tuple: (success, response_data)
        """
        try:
            # Check if bypass is requested and enabled
            if use_bypass and self.bypass_enabled:
                self.logger.warning("Using development authentication bypass")
                
                # Create mock session data for development bypass
                session_data = {
                    'user_id': 'dev-bypass-user',
                    'email': self.test_email or 'dev@example.com',
                    'access_token': 'dev-bypass-token',
                    'refresh_token': 'dev-bypass-refresh',
                    'expires_at': (datetime.utcnow() + timedelta(hours=1)).timestamp(),
                    'authenticated_at': datetime.utcnow().isoformat()
                }
                
                return True, {
                    'success': True,
                    'message': 'Authentication successful (development bypass)',
                    'session': session_data,
                    'requires_license': True  # Still require license verification
                }
            
            # Check if Supabase is available for normal authentication
            if not self.supabase_available or not self.auth_service:
                return False, {'error': 'Authentication service unavailable'}
            
            # Normal authentication
            return await self.auth_service.authenticate_user(email, password)
            
        except Exception as e:
            self.logger.error(f"Authentication manager error: {e}")
            return False, {'error': f'Authentication failed: {str(e)}'}
    
    async def verify_license(self, license_uuid: str, use_bypass: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify license with optional development bypass.
        
        Args:
            license_uuid (str): License UUID
            use_bypass (bool): Whether to bypass license verification
            
        Returns:
            tuple: (success, response_data)
        """
        try:
            # Check if bypass is requested and enabled
            if use_bypass and self.bypass_enabled:
                self.logger.warning("Using development license bypass")
                
                # Mock successful license verification
                system_info = await get_system_info_for_auth()
                return True, {
                    'success': True,
                    'message': 'License verified (development bypass)',
                    'license_id': 'dev-bypass-license',
                    'system_info': system_info
                }
            
            # Normal license verification
            return await self.auth_service.verify_license(license_uuid)
            
        except Exception as e:
            self.logger.error(f"License verification manager error: {e}")
            return False, {'error': f'License verification failed: {str(e)}'}
    
    async def logout(self) -> bool:
        """Logout current user."""
        if self.supabase_available and self.auth_service:
            return await self.auth_service.logout()
        return True  # In bypass mode, always succeed
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information."""
        if self.supabase_available and self.auth_service:
            return self.auth_service.get_current_session()
        return None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        if self.supabase_available and self.auth_service:
            return self.auth_service.is_authenticated()
        return False  # In bypass mode, authentication is per-request
    
    def is_license_validated(self) -> bool:
        """Check if license is validated."""
        if self.supabase_available and self.auth_service:
            return self.auth_service.is_license_validated()
        return False  # License validation is per-request in bypass mode


# Global instance will be initialized in main app
auth_manager: Optional[AuthenticationManager] = None


def get_auth_manager() -> Optional[AuthenticationManager]:
    """Get the global authentication manager instance."""
    return auth_manager


def initialize_auth_manager(config: Dict[str, Any]) -> AuthenticationManager:
    """Initialize the global authentication manager."""
    global auth_manager
    auth_manager = AuthenticationManager(config)
    return auth_manager