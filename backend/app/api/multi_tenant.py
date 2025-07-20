"""
Multi-Tenant API endpoints for Phase 3
Provides tenant management, configuration, and monitoring capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import logging

from app.utils.multi_tenant import (
    get_multi_tenant_manager, 
    get_current_tenant_id,
    require_tenant_context,
    Tenant, 
    TenantStatus, 
    SubscriptionTier,
    TenantLimits,
    TenantConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/multi-tenant", tags=["multi-tenant"])

# Request/Response Models
class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tenant name")
    admin_email: EmailStr = Field(..., description="Admin email address")
    domain: Optional[str] = Field(None, description="Optional custom domain")
    subscription_tier: SubscriptionTier = Field(SubscriptionTier.FREE, description="Subscription tier")
    trial_days: Optional[int] = Field(None, ge=1, le=90, description="Trial period in days")

class UpdateTenantRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    domain: Optional[str] = None
    status: Optional[TenantStatus] = None
    subscription_tier: Optional[SubscriptionTier] = None
    admin_email: Optional[EmailStr] = None
    billing_email: Optional[EmailStr] = None
    support_contact: Optional[EmailStr] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[Set[str]] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str]
    status: TenantStatus
    subscription_tier: SubscriptionTier
    created_at: datetime
    updated_at: datetime
    trial_expires_at: Optional[datetime]
    admin_email: Optional[str]
    billing_email: Optional[str]
    support_contact: Optional[str]
    metadata: Dict[str, Any]
    tags: Set[str]

class TenantListResponse(BaseModel):
    tenants: List[TenantResponse]
    total: int
    offset: int
    limit: int

class TenantUsageResponse(BaseModel):
    tenant_id: str
    subscription_tier: str
    status: str
    usage: Dict[str, Any]
    limits: Dict[str, Any]
    utilization: Dict[str, Any]

class TenantStatsResponse(BaseModel):
    total_tenants: int
    active_tenants: int
    suspended_tenants: int
    trial_tenants: int
    tier_distribution: Dict[str, int]
    total_usage: Dict[str, Any]

class RateLimitResponse(BaseModel):
    allowed: bool
    remaining_hour: Optional[int] = None
    remaining_day: Optional[int] = None
    error: Optional[str] = None
    limit: Optional[int] = None
    used: Optional[int] = None
    reset_time: Optional[str] = None

class FeatureAccessResponse(BaseModel):
    tenant_id: str
    feature: str
    access_granted: bool
    subscription_tier: str

class DetectorAccessResponse(BaseModel):
    tenant_id: str
    detector_name: str
    access_granted: bool
    enabled_detectors: List[str]

# Dependency for admin authentication (placeholder)
async def get_current_admin():
    """Placeholder for admin authentication"""
    # In a real implementation, this would validate admin JWT tokens
    return {"admin_id": "admin_user", "permissions": ["tenant_management"]}

# Tenant Management Endpoints

@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    request: CreateTenantRequest,
    admin: dict = Depends(get_current_admin)
):
    """Create a new tenant"""
    try:
        manager = get_multi_tenant_manager()
        
        tenant = manager.create_tenant(
            name=request.name,
            admin_email=request.admin_email,
            domain=request.domain,
            subscription_tier=request.subscription_tier,
            trial_days=request.trial_days
        )
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            domain=tenant.domain,
            status=tenant.status,
            subscription_tier=tenant.subscription_tier,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            trial_expires_at=tenant.trial_expires_at,
            admin_email=tenant.admin_email,
            billing_email=tenant.billing_email,
            support_contact=tenant.support_contact,
            metadata=tenant.metadata,
            tags=tenant.tags
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tenant")

@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    status: Optional[TenantStatus] = Query(None, description="Filter by tenant status"),
    subscription_tier: Optional[SubscriptionTier] = Query(None, description="Filter by subscription tier"),
    limit: int = Query(50, ge=1, le=100, description="Number of tenants to return"),
    offset: int = Query(0, ge=0, description="Number of tenants to skip"),
    admin: dict = Depends(get_current_admin)
):
    """List tenants with optional filtering"""
    try:
        manager = get_multi_tenant_manager()
        
        tenants = manager.list_tenants(
            status=status,
            subscription_tier=subscription_tier,
            limit=limit,
            offset=offset
        )
        
        tenant_responses = [
            TenantResponse(
                id=tenant.id,
                name=tenant.name,
                domain=tenant.domain,
                status=tenant.status,
                subscription_tier=tenant.subscription_tier,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at,
                trial_expires_at=tenant.trial_expires_at,
                admin_email=tenant.admin_email,
                billing_email=tenant.billing_email,
                support_contact=tenant.support_contact,
                metadata=tenant.metadata,
                tags=tenant.tags
            )
            for tenant in tenants
        ]
        
        # Get total count (simplified - in production, implement efficient counting)
        all_tenants = manager.list_tenants(limit=10000)
        total = len(all_tenants)
        
        return TenantListResponse(
            tenants=tenant_responses,
            total=total,
            offset=offset,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing tenants: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tenants")

@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    admin: dict = Depends(get_current_admin)
):
    """Get a specific tenant by ID"""
    try:
        manager = get_multi_tenant_manager()
        tenant = manager.get_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            domain=tenant.domain,
            status=tenant.status,
            subscription_tier=tenant.subscription_tier,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            trial_expires_at=tenant.trial_expires_at,
            admin_email=tenant.admin_email,
            billing_email=tenant.billing_email,
            support_contact=tenant.support_contact,
            metadata=tenant.metadata,
            tags=tenant.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant")

@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    request: UpdateTenantRequest = ...,
    admin: dict = Depends(get_current_admin)
):
    """Update a tenant"""
    try:
        manager = get_multi_tenant_manager()
        
        # Get current tenant to verify it exists
        tenant = manager.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Prepare updates
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.domain is not None:
            updates["domain"] = request.domain
        if request.status is not None:
            updates["status"] = request.status
        if request.subscription_tier is not None:
            updates["subscription_tier"] = request.subscription_tier
        if request.admin_email is not None:
            updates["admin_email"] = request.admin_email
        if request.billing_email is not None:
            updates["billing_email"] = request.billing_email
        if request.support_contact is not None:
            updates["support_contact"] = request.support_contact
        if request.metadata is not None:
            updates["metadata"] = request.metadata
        if request.tags is not None:
            updates["tags"] = request.tags
        
        success = manager.update_tenant(tenant_id, **updates)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update tenant")
        
        # Return updated tenant
        updated_tenant = manager.get_tenant(tenant_id)
        return TenantResponse(
            id=updated_tenant.id,
            name=updated_tenant.name,
            domain=updated_tenant.domain,
            status=updated_tenant.status,
            subscription_tier=updated_tenant.subscription_tier,
            created_at=updated_tenant.created_at,
            updated_at=updated_tenant.updated_at,
            trial_expires_at=updated_tenant.trial_expires_at,
            admin_email=updated_tenant.admin_email,
            billing_email=updated_tenant.billing_email,
            support_contact=updated_tenant.support_contact,
            metadata=updated_tenant.metadata,
            tags=updated_tenant.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tenant")

@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    soft_delete: bool = Query(True, description="Perform soft delete (suspend) instead of hard delete"),
    admin: dict = Depends(get_current_admin)
):
    """Delete or suspend a tenant"""
    try:
        manager = get_multi_tenant_manager()
        
        success = manager.delete_tenant(tenant_id, soft_delete=soft_delete)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "success": True,
            "message": f"Tenant {'suspended' if soft_delete else 'deleted'} successfully",
            "tenant_id": tenant_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tenant")

# Tenant Usage and Monitoring

@router.get("/tenants/{tenant_id}/usage", response_model=TenantUsageResponse)
async def get_tenant_usage(
    tenant_id: str = Path(..., description="Tenant ID"),
    admin: dict = Depends(get_current_admin)
):
    """Get tenant usage statistics"""
    try:
        manager = get_multi_tenant_manager()
        usage_data = manager.get_tenant_usage(tenant_id)
        
        if not usage_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return TenantUsageResponse(**usage_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant usage {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant usage")

@router.post("/tenants/{tenant_id}/rate-limit/check", response_model=RateLimitResponse)
async def check_rate_limit(
    tenant_id: str = Path(..., description="Tenant ID"),
    increment: bool = Query(True, description="Increment usage counter")
):
    """Check if tenant has exceeded rate limits"""
    try:
        manager = get_multi_tenant_manager()
        allowed, details = manager.check_rate_limit(tenant_id, increment=increment)
        
        return RateLimitResponse(
            allowed=allowed,
            remaining_hour=details.get("remaining_hour"),
            remaining_day=details.get("remaining_day"),
            error=details.get("error"),
            limit=details.get("limit"),
            used=details.get("used"),
            reset_time=details.get("reset_time")
        )
        
    except Exception as e:
        logger.error(f"Error checking rate limit for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check rate limit")

@router.get("/tenants/{tenant_id}/features/{feature}/access", response_model=FeatureAccessResponse)
async def check_feature_access(
    tenant_id: str = Path(..., description="Tenant ID"),
    feature: str = Path(..., description="Feature name")
):
    """Check if tenant has access to a specific feature"""
    try:
        manager = get_multi_tenant_manager()
        tenant = manager.get_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        access_granted = manager.check_feature_access(tenant_id, feature)
        
        return FeatureAccessResponse(
            tenant_id=tenant_id,
            feature=feature,
            access_granted=access_granted,
            subscription_tier=tenant.subscription_tier.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking feature access for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check feature access")

@router.get("/tenants/{tenant_id}/detectors/{detector_name}/access", response_model=DetectorAccessResponse)
async def check_detector_access(
    tenant_id: str = Path(..., description="Tenant ID"),
    detector_name: str = Path(..., description="Detector name")
):
    """Check if tenant has access to a specific detector"""
    try:
        manager = get_multi_tenant_manager()
        tenant = manager.get_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        access_granted = manager.check_detector_access(tenant_id, detector_name)
        
        return DetectorAccessResponse(
            tenant_id=tenant_id,
            detector_name=detector_name,
            access_granted=access_granted,
            enabled_detectors=list(tenant.limits.enabled_detectors)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking detector access for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check detector access")

# Subscription Management

@router.post("/tenants/{tenant_id}/upgrade")
async def upgrade_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    new_tier: SubscriptionTier = Query(..., description="New subscription tier"),
    admin: dict = Depends(get_current_admin)
):
    """Upgrade tenant to a new subscription tier"""
    try:
        manager = get_multi_tenant_manager()
        
        success = manager.upgrade_tenant(tenant_id, new_tier)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant = manager.get_tenant(tenant_id)
        return {
            "success": True,
            "message": f"Tenant upgraded to {new_tier.value}",
            "tenant_id": tenant_id,
            "new_tier": new_tier.value,
            "updated_at": tenant.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upgrade tenant")

# System Statistics

@router.get("/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    admin: dict = Depends(get_current_admin)
):
    """Get overall multi-tenant system statistics"""
    try:
        manager = get_multi_tenant_manager()
        stats = manager.get_tenant_stats()
        
        return TenantStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting tenant stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant stats")

# Tenant Context Utilities (for internal use)

@router.get("/context/current")
async def get_current_tenant():
    """Get current tenant context (for debugging)"""
    tenant_id = get_current_tenant_id()
    
    if not tenant_id:
        return {"tenant_id": None, "message": "No tenant context set"}
    
    manager = get_multi_tenant_manager()
    tenant = manager.get_tenant(tenant_id)
    
    if not tenant:
        return {"tenant_id": tenant_id, "message": "Tenant not found"}
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant.name,
        "subscription_tier": tenant.subscription_tier.value,
        "status": tenant.status.value
    }

# Health Check

@router.get("/health")
async def multi_tenant_health():
    """Multi-tenant system health check"""
    try:
        manager = get_multi_tenant_manager()
        stats = manager.get_tenant_stats()
        
        return {
            "status": "healthy",
            "total_tenants": stats["total_tenants"],
            "active_tenants": stats["active_tenants"],
            "system_status": "operational",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Multi-tenant health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }