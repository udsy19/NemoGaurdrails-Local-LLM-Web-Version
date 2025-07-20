"""
Multi-Tenant Support System
Provides tenant isolation, resource management, and configuration segregation
"""

import threading
import time
import uuid
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from contextlib import contextmanager
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TenantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    TRIAL = "trial"

class SubscriptionTier(Enum):
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

@dataclass
class TenantLimits:
    """Resource limits for a tenant"""
    max_requests_per_hour: int = 1000
    max_requests_per_day: int = 10000
    max_storage_mb: int = 100
    max_users: int = 10
    max_concurrent_sessions: int = 5
    max_retention_days: int = 30
    enabled_detectors: Set[str] = field(default_factory=lambda: {"toxicity", "pii"})
    custom_models_allowed: bool = False
    api_access_enabled: bool = True
    analytics_enabled: bool = True
    export_enabled: bool = False

@dataclass
class TenantUsage:
    """Current usage statistics for a tenant"""
    requests_this_hour: int = 0
    requests_this_day: int = 0
    requests_this_month: int = 0
    storage_used_mb: float = 0
    active_users: int = 0
    concurrent_sessions: int = 0
    last_activity: Optional[datetime] = None
    hour_reset_time: datetime = field(default_factory=datetime.utcnow)
    day_reset_time: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TenantConfig:
    """Tenant-specific configuration"""
    detector_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    custom_rules: List[Dict[str, Any]] = field(default_factory=list)
    notification_settings: Dict[str, Any] = field(default_factory=dict)
    ui_branding: Dict[str, Any] = field(default_factory=dict)
    integration_settings: Dict[str, Any] = field(default_factory=dict)
    security_settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Tenant:
    """Represents a tenant in the multi-tenant system"""
    id: str
    name: str
    domain: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    trial_expires_at: Optional[datetime] = None
    
    # Tenant resources
    limits: TenantLimits = field(default_factory=TenantLimits)
    usage: TenantUsage = field(default_factory=TenantUsage)
    config: TenantConfig = field(default_factory=TenantConfig)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    
    # Admin details
    admin_email: Optional[str] = None
    billing_email: Optional[str] = None
    support_contact: Optional[str] = None

class TenantContext:
    """Thread-local storage for current tenant context"""
    _local = threading.local()
    
    @classmethod
    def set_current_tenant(cls, tenant_id: str):
        """Set the current tenant for this thread"""
        cls._local.tenant_id = tenant_id
    
    @classmethod
    def get_current_tenant(cls) -> Optional[str]:
        """Get the current tenant ID for this thread"""
        return getattr(cls._local, 'tenant_id', None)
    
    @classmethod
    def clear_current_tenant(cls):
        """Clear the current tenant context"""
        if hasattr(cls._local, 'tenant_id'):
            delattr(cls._local, 'tenant_id')

class MultiTenantManager:
    """
    Manages multi-tenant operations, isolation, and resource allocation
    """
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.domain_mapping: Dict[str, str] = {}  # domain -> tenant_id
        self.tenant_locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()
        
        # Usage tracking
        self.usage_tracker = threading.Thread(target=self._usage_tracking_loop, daemon=True)
        self.usage_tracker_running = False
        
        # Default tier limits
        self.tier_limits = {
            SubscriptionTier.FREE: TenantLimits(
                max_requests_per_hour=100,
                max_requests_per_day=1000,
                max_storage_mb=50,
                max_users=3,
                max_concurrent_sessions=2,
                max_retention_days=7,
                enabled_detectors={"toxicity", "pii"},
                custom_models_allowed=False,
                api_access_enabled=True,
                analytics_enabled=False,
                export_enabled=False
            ),
            SubscriptionTier.BASIC: TenantLimits(
                max_requests_per_hour=500,
                max_requests_per_day=5000,
                max_storage_mb=200,
                max_users=10,
                max_concurrent_sessions=5,
                max_retention_days=30,
                enabled_detectors={"toxicity", "pii", "spam", "prompt_injection"},
                custom_models_allowed=False,
                api_access_enabled=True,
                analytics_enabled=True,
                export_enabled=True
            ),
            SubscriptionTier.PROFESSIONAL: TenantLimits(
                max_requests_per_hour=2000,
                max_requests_per_day=20000,
                max_storage_mb=1000,
                max_users=50,
                max_concurrent_sessions=20,
                max_retention_days=90,
                enabled_detectors={"toxicity", "pii", "spam", "prompt_injection", "topic", "fact_check"},
                custom_models_allowed=True,
                api_access_enabled=True,
                analytics_enabled=True,
                export_enabled=True
            ),
            SubscriptionTier.ENTERPRISE: TenantLimits(
                max_requests_per_hour=10000,
                max_requests_per_day=100000,
                max_storage_mb=10000,
                max_users=500,
                max_concurrent_sessions=100,
                max_retention_days=365,
                enabled_detectors={"toxicity", "pii", "spam", "prompt_injection", "topic", "fact_check"},
                custom_models_allowed=True,
                api_access_enabled=True,
                analytics_enabled=True,
                export_enabled=True
            )
        }
        
        logger.info("Multi-tenant manager initialized")
    
    def start_usage_tracking(self):
        """Start the usage tracking background thread"""
        if not self.usage_tracker_running:
            self.usage_tracker_running = True
            self.usage_tracker.start()
            logger.info("Usage tracking started")
    
    def stop_usage_tracking(self):
        """Stop the usage tracking background thread"""
        self.usage_tracker_running = False
        logger.info("Usage tracking stopped")
    
    def create_tenant(
        self,
        name: str,
        admin_email: str,
        domain: Optional[str] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE,
        trial_days: Optional[int] = None
    ) -> Tenant:
        """Create a new tenant"""
        with self._global_lock:
            tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
            
            # Check domain uniqueness
            if domain and domain in self.domain_mapping:
                raise ValueError(f"Domain {domain} is already registered")
            
            # Set trial expiration if applicable
            trial_expires_at = None
            if trial_days:
                trial_expires_at = datetime.utcnow() + timedelta(days=trial_days)
            
            # Create tenant with tier-specific limits
            tenant = Tenant(
                id=tenant_id,
                name=name,
                domain=domain,
                admin_email=admin_email,
                subscription_tier=subscription_tier,
                limits=self.tier_limits[subscription_tier],
                trial_expires_at=trial_expires_at
            )
            
            # Register tenant
            self.tenants[tenant_id] = tenant
            self.tenant_locks[tenant_id] = threading.RLock()
            
            if domain:
                self.domain_mapping[domain] = tenant_id
            
            logger.info(f"Created tenant: {tenant_id} ({name}) - {subscription_tier.value}")
            return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        tenant_id = self.domain_mapping.get(domain)
        return self.tenants.get(tenant_id) if tenant_id else None
    
    def update_tenant(self, tenant_id: str, **updates) -> bool:
        """Update tenant properties"""
        with self._get_tenant_lock(tenant_id):
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            for key, value in updates.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)
            
            tenant.updated_at = datetime.utcnow()
            logger.info(f"Updated tenant {tenant_id}: {list(updates.keys())}")
            return True
    
    def delete_tenant(self, tenant_id: str, soft_delete: bool = True) -> bool:
        """Delete or suspend a tenant"""
        with self._get_tenant_lock(tenant_id):
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            if soft_delete:
                tenant.status = TenantStatus.DELETED
                tenant.updated_at = datetime.utcnow()
                logger.info(f"Soft deleted tenant: {tenant_id}")
            else:
                # Remove from mappings
                if tenant.domain:
                    self.domain_mapping.pop(tenant.domain, None)
                
                # Remove tenant
                self.tenants.pop(tenant_id, None)
                self.tenant_locks.pop(tenant_id, None)
                logger.info(f"Hard deleted tenant: {tenant_id}")
            
            return True
    
    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with optional filtering"""
        tenants = list(self.tenants.values())
        
        # Apply filters
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        if subscription_tier:
            tenants = [t for t in tenants if t.subscription_tier == subscription_tier]
        
        # Sort by creation date (newest first)
        tenants.sort(key=lambda t: t.created_at, reverse=True)
        
        # Apply pagination
        return tenants[offset:offset + limit]
    
    def check_rate_limit(self, tenant_id: str, increment: bool = True) -> tuple[bool, Dict[str, Any]]:
        """Check if tenant has exceeded rate limits"""
        with self._get_tenant_lock(tenant_id):
            tenant = self.tenants.get(tenant_id)
            if not tenant or tenant.status != TenantStatus.ACTIVE:
                return False, {"error": "Tenant not found or inactive"}
            
            # Reset counters if needed
            self._reset_usage_counters(tenant)
            
            # Check limits
            if tenant.usage.requests_this_hour >= tenant.limits.max_requests_per_hour:
                return False, {
                    "error": "Hourly rate limit exceeded",
                    "limit": tenant.limits.max_requests_per_hour,
                    "used": tenant.usage.requests_this_hour,
                    "reset_time": tenant.usage.hour_reset_time.isoformat()
                }
            
            if tenant.usage.requests_this_day >= tenant.limits.max_requests_per_day:
                return False, {
                    "error": "Daily rate limit exceeded",
                    "limit": tenant.limits.max_requests_per_day,
                    "used": tenant.usage.requests_this_day,
                    "reset_time": tenant.usage.day_reset_time.isoformat()
                }
            
            # Increment counters
            if increment:
                tenant.usage.requests_this_hour += 1
                tenant.usage.requests_this_day += 1
                tenant.usage.requests_this_month += 1
                tenant.usage.last_activity = datetime.utcnow()
            
            return True, {
                "allowed": True,
                "remaining_hour": tenant.limits.max_requests_per_hour - tenant.usage.requests_this_hour,
                "remaining_day": tenant.limits.max_requests_per_day - tenant.usage.requests_this_day
            }
    
    def check_feature_access(self, tenant_id: str, feature: str) -> bool:
        """Check if tenant has access to a specific feature"""
        tenant = self.tenants.get(tenant_id)
        if not tenant or tenant.status != TenantStatus.ACTIVE:
            return False
        
        feature_mapping = {
            "analytics": lambda t: t.limits.analytics_enabled,
            "export": lambda t: t.limits.export_enabled,
            "api_access": lambda t: t.limits.api_access_enabled,
            "custom_models": lambda t: t.limits.custom_models_allowed,
        }
        
        checker = feature_mapping.get(feature)
        return checker(tenant) if checker else False
    
    def check_detector_access(self, tenant_id: str, detector_name: str) -> bool:
        """Check if tenant has access to a specific detector"""
        tenant = self.tenants.get(tenant_id)
        if not tenant or tenant.status != TenantStatus.ACTIVE:
            return False
        
        return detector_name in tenant.limits.enabled_detectors
    
    def get_tenant_usage(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get current usage statistics for a tenant"""
        with self._get_tenant_lock(tenant_id):
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return None
            
            self._reset_usage_counters(tenant)
            
            return {
                "tenant_id": tenant_id,
                "subscription_tier": tenant.subscription_tier.value,
                "status": tenant.status.value,
                "usage": {
                    "requests_this_hour": tenant.usage.requests_this_hour,
                    "requests_this_day": tenant.usage.requests_this_day,
                    "requests_this_month": tenant.usage.requests_this_month,
                    "storage_used_mb": tenant.usage.storage_used_mb,
                    "active_users": tenant.usage.active_users,
                    "concurrent_sessions": tenant.usage.concurrent_sessions,
                    "last_activity": tenant.usage.last_activity.isoformat() if tenant.usage.last_activity else None
                },
                "limits": {
                    "max_requests_per_hour": tenant.limits.max_requests_per_hour,
                    "max_requests_per_day": tenant.limits.max_requests_per_day,
                    "max_storage_mb": tenant.limits.max_storage_mb,
                    "max_users": tenant.limits.max_users,
                    "max_concurrent_sessions": tenant.limits.max_concurrent_sessions,
                    "enabled_detectors": list(tenant.limits.enabled_detectors)
                },
                "utilization": {
                    "requests_hour_pct": (tenant.usage.requests_this_hour / tenant.limits.max_requests_per_hour) * 100,
                    "requests_day_pct": (tenant.usage.requests_this_day / tenant.limits.max_requests_per_day) * 100,
                    "storage_pct": (tenant.usage.storage_used_mb / tenant.limits.max_storage_mb) * 100,
                    "users_pct": (tenant.usage.active_users / tenant.limits.max_users) * 100
                }
            }
    
    def upgrade_tenant(self, tenant_id: str, new_tier: SubscriptionTier) -> bool:
        """Upgrade tenant to a new subscription tier"""
        with self._get_tenant_lock(tenant_id):
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            old_tier = tenant.subscription_tier
            tenant.subscription_tier = new_tier
            tenant.limits = self.tier_limits[new_tier]
            tenant.updated_at = datetime.utcnow()
            
            logger.info(f"Upgraded tenant {tenant_id} from {old_tier.value} to {new_tier.value}")
            return True
    
    def _get_tenant_lock(self, tenant_id: str) -> threading.RLock:
        """Get or create a lock for a tenant"""
        if tenant_id not in self.tenant_locks:
            with self._global_lock:
                if tenant_id not in self.tenant_locks:
                    self.tenant_locks[tenant_id] = threading.RLock()
        return self.tenant_locks[tenant_id]
    
    def _reset_usage_counters(self, tenant: Tenant):
        """Reset usage counters if time periods have elapsed"""
        now = datetime.utcnow()
        
        # Reset hourly counter
        if now - tenant.usage.hour_reset_time >= timedelta(hours=1):
            tenant.usage.requests_this_hour = 0
            tenant.usage.hour_reset_time = now
        
        # Reset daily counter
        if now - tenant.usage.day_reset_time >= timedelta(days=1):
            tenant.usage.requests_this_day = 0
            tenant.usage.day_reset_time = now
    
    def _usage_tracking_loop(self):
        """Background thread for usage tracking and cleanup"""
        while self.usage_tracker_running:
            try:
                current_time = datetime.utcnow()
                
                for tenant in self.tenants.values():
                    with self._get_tenant_lock(tenant.id):
                        # Reset usage counters
                        self._reset_usage_counters(tenant)
                        
                        # Check trial expiration
                        if (tenant.trial_expires_at and 
                            current_time > tenant.trial_expires_at and 
                            tenant.status == TenantStatus.TRIAL):
                            tenant.status = TenantStatus.SUSPENDED
                            logger.warning(f"Trial expired for tenant {tenant.id}")
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in usage tracking loop: {e}")
                time.sleep(60)
    
    @contextmanager
    def tenant_context(self, tenant_id: str):
        """Context manager for tenant operations"""
        old_tenant = TenantContext.get_current_tenant()
        try:
            TenantContext.set_current_tenant(tenant_id)
            yield
        finally:
            if old_tenant:
                TenantContext.set_current_tenant(old_tenant)
            else:
                TenantContext.clear_current_tenant()
    
    def get_tenant_stats(self) -> Dict[str, Any]:
        """Get overall multi-tenant statistics"""
        stats = {
            "total_tenants": len(self.tenants),
            "active_tenants": len([t for t in self.tenants.values() if t.status == TenantStatus.ACTIVE]),
            "suspended_tenants": len([t for t in self.tenants.values() if t.status == TenantStatus.SUSPENDED]),
            "trial_tenants": len([t for t in self.tenants.values() if t.status == TenantStatus.TRIAL]),
            "tier_distribution": {},
            "total_usage": {
                "requests_this_hour": 0,
                "requests_this_day": 0,
                "total_storage_mb": 0,
                "total_users": 0
            }
        }
        
        # Calculate tier distribution
        for tier in SubscriptionTier:
            stats["tier_distribution"][tier.value] = len([
                t for t in self.tenants.values() 
                if t.subscription_tier == tier
            ])
        
        # Calculate total usage
        for tenant in self.tenants.values():
            if tenant.status == TenantStatus.ACTIVE:
                stats["total_usage"]["requests_this_hour"] += tenant.usage.requests_this_hour
                stats["total_usage"]["requests_this_day"] += tenant.usage.requests_this_day
                stats["total_usage"]["total_storage_mb"] += tenant.usage.storage_used_mb
                stats["total_usage"]["total_users"] += tenant.usage.active_users
        
        return stats

# Global multi-tenant manager instance
_multi_tenant_manager: Optional[MultiTenantManager] = None

def get_multi_tenant_manager() -> MultiTenantManager:
    """Get the global multi-tenant manager instance"""
    global _multi_tenant_manager
    if _multi_tenant_manager is None:
        _multi_tenant_manager = MultiTenantManager()
    return _multi_tenant_manager

def get_current_tenant_id() -> Optional[str]:
    """Get the current tenant ID from context"""
    return TenantContext.get_current_tenant()

def require_tenant_context() -> str:
    """Require that a tenant context is set, raise exception if not"""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise ValueError("No tenant context set")
    return tenant_id