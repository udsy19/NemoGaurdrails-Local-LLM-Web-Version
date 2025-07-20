"""
Centralized Dependency Injection System
Eliminates duplicate dependency getter functions across API modules
"""

from typing import Any, Optional
from fastapi import Depends, HTTPException
from app.utils.logger import app_logger

class ServiceContainer:
    """Container for application services and dependencies"""
    
    _instance: Optional['ServiceContainer'] = None
    _app = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_app(cls, app):
        """Set the FastAPI app instance"""
        cls._app = app
    
    @classmethod
    def get_app(cls):
        """Get the FastAPI app instance"""
        if cls._app is None:
            raise RuntimeError("FastAPI app not set in ServiceContainer")
        return cls._app
    
    @classmethod
    def get_service(cls, service_name: str) -> Any:
        """Get a service from the app state"""
        app = cls.get_app()
        if not hasattr(app.state, service_name):
            raise HTTPException(
                status_code=503, 
                detail=f"Service {service_name} not available"
            )
        
        service = getattr(app.state, service_name)
        if service is None:
            raise HTTPException(
                status_code=503, 
                detail=f"Service {service_name} not initialized"
            )
        
        return service

# Service dependency functions
def get_model_manager():
    """Get the model manager service"""
    return ServiceContainer.get_service('model_manager')

def get_detection_service():
    """Get the detection service"""
    return ServiceContainer.get_service('detection_service')

def get_chat_service():
    """Get the chat service"""
    return ServiceContainer.get_service('chat_service')

def get_config_service():
    """Get the config service"""
    return ServiceContainer.get_service('config_service')

def get_analytics_service():
    """Get the analytics service"""
    return ServiceContainer.get_service('analytics_service')

def get_health_monitor():
    """Get the health monitor service"""
    return ServiceContainer.get_service('health_monitor')

def get_degradation_manager():
    """Get the degradation manager service"""
    return ServiceContainer.get_service('degradation_manager')

def get_diagnostics():
    """Get the diagnostics service"""
    return ServiceContainer.get_service('diagnostics')

def get_alert_manager():
    """Get the alert manager service"""
    return ServiceContainer.get_service('alert_manager')

def get_performance_monitor():
    """Get the performance monitor service"""
    return ServiceContainer.get_service('performance_monitor')

def get_self_healing_system():
    """Get the self healing system service"""
    return ServiceContainer.get_service('self_healing_system')

def get_multi_tenant_manager():
    """Get the multi-tenant manager service"""
    return ServiceContainer.get_service('multi_tenant_manager')

def get_ab_testing_manager():
    """Get the A/B testing manager service"""
    return ServiceContainer.get_service('ab_testing_manager')

# Common dependency combinations
def get_core_services():
    """Get commonly used core services"""
    return {
        'model_manager': get_model_manager(),
        'detection_service': get_detection_service(),
        'chat_service': get_chat_service(),
        'config_service': get_config_service()
    }

def get_monitoring_services():
    """Get monitoring and diagnostic services"""
    return {
        'health_monitor': get_health_monitor(),
        'performance_monitor': get_performance_monitor(),
        'diagnostics': get_diagnostics(),
        'alert_manager': get_alert_manager()
    }

def get_advanced_services():
    """Get Phase 3 advanced services"""
    return {
        'multi_tenant_manager': get_multi_tenant_manager(),
        'ab_testing_manager': get_ab_testing_manager()
    }

# Authentication and authorization helpers
class AuthDependencies:
    """Common authentication dependency patterns"""
    
    @staticmethod
    def get_current_user():
        """Placeholder for user authentication"""
        # In a real implementation, this would validate JWT tokens
        return {"user_id": "anonymous", "permissions": ["read"]}
    
    @staticmethod
    def get_current_admin():
        """Placeholder for admin authentication"""
        # In a real implementation, this would validate admin tokens
        return {"admin_id": "admin_user", "permissions": ["admin"]}
    
    @staticmethod
    def require_permission(permission: str):
        """Dependency to require specific permission"""
        def permission_checker(user: dict = Depends(AuthDependencies.get_current_user)):
            if permission not in user.get("permissions", []):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Insufficient permissions. Required: {permission}"
                )
            return user
        return permission_checker

# Validation dependencies
class ValidationDependencies:
    """Common validation dependency patterns"""
    
    @staticmethod
    def validate_tenant_id(tenant_id: str):
        """Validate tenant ID format and existence"""
        if not tenant_id or not tenant_id.startswith("tenant_"):
            raise HTTPException(status_code=400, detail="Invalid tenant ID format")
        
        # Additional validation could be added here
        return tenant_id
    
    @staticmethod
    def validate_experiment_id(experiment_id: str):
        """Validate experiment ID format"""
        if not experiment_id or not experiment_id.startswith("exp_"):
            raise HTTPException(status_code=400, detail="Invalid experiment ID format")
        
        return experiment_id
    
    @staticmethod
    def validate_pagination_params(limit: int = 50, offset: int = 0):
        """Validate pagination parameters"""
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        return {"limit": limit, "offset": offset}

# Rate limiting dependencies
class RateLimitDependencies:
    """Rate limiting dependency patterns"""
    
    @staticmethod
    def check_rate_limit(tenant_id: str = None):
        """Check rate limits for tenant or global user"""
        def rate_limit_checker():
            if tenant_id:
                manager = get_multi_tenant_manager()
                allowed, details = manager.check_rate_limit(tenant_id)
                if not allowed:
                    raise HTTPException(
                        status_code=429, 
                        detail=details.get("error", "Rate limit exceeded")
                    )
            # Global rate limiting logic could be added here
            return True
        return rate_limit_checker

# Health check dependencies
class HealthDependencies:
    """Health check dependency patterns"""
    
    @staticmethod
    def check_service_health(service_name: str):
        """Check if a specific service is healthy"""
        def health_checker():
            try:
                service = ServiceContainer.get_service(service_name)
                # Basic health check - service exists and is not None
                if service is None:
                    raise HTTPException(
                        status_code=503, 
                        detail=f"Service {service_name} is not healthy"
                    )
                return True
            except HTTPException:
                raise
            except Exception as e:
                app_logger.error(f"Health check failed for {service_name}: {e}")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Service {service_name} health check failed"
                )
        return health_checker

# Context dependencies
class ContextDependencies:
    """Context-aware dependency patterns"""
    
    @staticmethod
    def with_tenant_context(tenant_id: str = None):
        """Set tenant context for request"""
        def context_setter():
            if tenant_id:
                # Set tenant context
                from app.utils.multi_tenant import TenantContext
                TenantContext.set_current_tenant(tenant_id)
            return tenant_id
        return context_setter
    
    @staticmethod
    def with_correlation_id(correlation_id: str = None):
        """Set correlation ID for request tracing"""
        def correlation_setter():
            if correlation_id:
                from app.utils.correlation_context import CorrelationContextManager
                CorrelationContextManager.set_correlation_id(correlation_id)
            return correlation_id
        return correlation_setter

# Factory for common dependency combinations
class DependencyFactory:
    """Factory for creating common dependency combinations"""
    
    @staticmethod
    def create_api_dependencies(
        require_auth: bool = False,
        require_admin: bool = False,
        check_health: bool = True,
        tenant_aware: bool = False
    ):
        """Create a set of dependencies for API endpoints"""
        deps = {}
        
        if require_admin:
            deps['admin'] = Depends(AuthDependencies.get_current_admin)
        elif require_auth:
            deps['user'] = Depends(AuthDependencies.get_current_user)
        
        if check_health:
            deps['health_check'] = Depends(HealthDependencies.check_service_health('detection_service'))
        
        if tenant_aware:
            deps['tenant_context'] = Depends(ContextDependencies.with_tenant_context)
        
        return deps
    
    @staticmethod
    def create_service_dependencies(service_names: list):
        """Create dependencies for specific services"""
        deps = {}
        for service_name in service_names:
            deps[service_name] = Depends(lambda s=service_name: ServiceContainer.get_service(s))
        return deps

# Initialize function to be called from main.py
def initialize_dependencies(app):
    """Initialize the dependency injection system"""
    ServiceContainer.set_app(app)
    app_logger.info("Dependency injection system initialized")