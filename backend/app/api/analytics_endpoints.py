"""
Analytics API Endpoints for KPMG Dashboard Integration
Provides REST API access to the comprehensive analytics system
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
import json

from app.services.analytics_service import analytics_service
from app.services.export_scheduler import export_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Pydantic models for API requests/responses
class AnalyticsStatsResponse(BaseModel):
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    error_requests: int
    block_rate: float
    database_stats: Dict[str, Any]

class ExportStatusResponse(BaseModel):
    running: bool
    export_interval_minutes: int
    offline_queue_size: int
    export_directory: str
    kpmg_endpoint: str
    client_id: str
    last_export_files: List[str]

class DashboardExportResponse(BaseModel):
    export_metadata: Dict[str, Any]
    time_ranges: Dict[str, Any]

class UserDataRequest(BaseModel):
    user_ip: str
    timeframe_hours: int = 168  # Default 1 week

@router.get("/stats", response_model=AnalyticsStatsResponse)
async def get_real_time_stats():
    """
    Get real-time analytics statistics.
    Returns current counters and database status.
    """
    try:
        stats = await analytics_service.get_real_time_stats()
        return AnalyticsStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get analytics stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics statistics")

@router.get("/database/stats")
async def get_database_stats():
    """
    Get comprehensive database statistics and health information.
    """
    try:
        stats = await analytics_service.get_database_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database statistics")

@router.get("/export/dashboard", response_model=DashboardExportResponse)
async def get_dashboard_export():
    """
    Generate and return the complete dashboard export for KPMG.
    This endpoint provides the same data that gets automatically transmitted every 5 minutes.
    """
    try:
        export_data = analytics_service.generate_dashboard_export()
        
        if not export_data:
            raise HTTPException(status_code=404, detail="No analytics data available")
        
        return DashboardExportResponse(**export_data)
        
    except Exception as e:
        logger.error(f"Failed to generate dashboard export: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard export")

@router.get("/export/timeframe/{timeframe}")
async def get_timeframe_analytics(
    timeframe: str,
    include_user_details: bool = Query(False, description="Include per-user activity details")
):
    """
    Get analytics for a specific timeframe.
    
    Parameters:
    - timeframe: One of '1h', '6h', '12h', '24h', '3d', '1w'
    - include_user_details: Whether to include per-user activity breakdown
    """
    try:
        valid_timeframes = {"1h": 1, "6h": 6, "12h": 12, "24h": 24, "3d": 72, "1w": 168}
        
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid timeframe. Must be one of: {list(valid_timeframes.keys())}"
            )
        
        hours = valid_timeframes[timeframe]
        
        # Generate full export and extract the requested timeframe
        export_data = analytics_service.generate_dashboard_export()
        
        if timeframe not in export_data.get("time_ranges", {}):
            raise HTTPException(status_code=404, detail=f"No data available for timeframe {timeframe}")
        
        timeframe_data = export_data["time_ranges"][timeframe]
        
        # Optionally exclude user details for privacy
        if not include_user_details and "user_activity" in timeframe_data:
            # Replace detailed user activity with summary counts
            user_activity = timeframe_data["user_activity"]
            timeframe_data["user_activity_summary"] = {
                "total_users": len(user_activity),
                "high_activity_users": len([u for u in user_activity.values() if u["total_requests"] > 10]),
                "blocked_users": len([u for u in user_activity.values() if u["blocked_requests"] > 0])
            }
            del timeframe_data["user_activity"]
        
        return {
            "timeframe": timeframe,
            "timeframe_hours": hours,
            "generated_at": datetime.utcnow().isoformat(),
            **timeframe_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeframe analytics for {timeframe}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeframe analytics")

@router.post("/export/user-data")
async def export_user_data(request: UserDataRequest):
    """
    Export all data for a specific user (for data sovereignty compliance).
    
    This endpoint allows users to request their data for transparency
    and compliance with data protection regulations.
    """
    try:
        user_data = analytics_service.export_user_data(
            user_ip=request.user_ip,
            timeframe_hours=request.timeframe_hours
        )
        
        if "error" in user_data:
            raise HTTPException(status_code=404, detail=user_data["error"])
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export user data for {request.user_ip}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export user data")

@router.get("/export/scheduler/status", response_model=ExportStatusResponse)
async def get_export_scheduler_status():
    """
    Get the current status of the KPMG export scheduler.
    """
    try:
        status = export_scheduler.get_status()
        return ExportStatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get export scheduler status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scheduler status")

@router.post("/export/scheduler/start")
async def start_export_scheduler(background_tasks: BackgroundTasks):
    """
    Start the automated export scheduler.
    This will begin 5-minute automated exports to KPMG dashboard.
    """
    try:
        # Start scheduler in background
        background_tasks.add_task(export_scheduler.start)
        
        return {
            "message": "Export scheduler starting",
            "export_interval_minutes": export_scheduler.config.export_interval_minutes,
            "kpmg_endpoint": export_scheduler.config.kpmg_endpoint
        }
    except Exception as e:
        logger.error(f"Failed to start export scheduler: {e}")
        raise HTTPException(status_code=500, detail="Failed to start export scheduler")

@router.post("/export/scheduler/stop")
async def stop_export_scheduler(background_tasks: BackgroundTasks):
    """
    Stop the automated export scheduler.
    """
    try:
        # Stop scheduler in background
        background_tasks.add_task(export_scheduler.stop)
        
        return {"message": "Export scheduler stopping"}
    except Exception as e:
        logger.error(f"Failed to stop export scheduler: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop export scheduler")

@router.post("/export/force")
async def force_export(background_tasks: BackgroundTasks):
    """
    Force an immediate export to KPMG dashboard.
    Useful for testing or manual data transmission.
    """
    try:
        # Force export in background
        success = await export_scheduler.force_export()
        
        if success:
            return {
                "message": "Export completed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Export failed - check logs for details")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to force export: {e}")
        raise HTTPException(status_code=500, detail="Failed to force export")

@router.delete("/data/cleanup")
async def cleanup_old_data(
    retention_days: int = Query(7, description="Number of days to retain data", ge=1, le=365)
):
    """
    Clean up analytics data older than the specified retention period.
    Default is 7 days as per the privacy policy.
    """
    try:
        analytics_service.cleanup_old_data(retention_days=retention_days)
        
        return {
            "message": f"Data cleanup completed for data older than {retention_days} days",
            "retention_days": retention_days,
            "cleanup_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old data")

@router.get("/guardrails/performance")
async def get_guardrail_performance(
    timeframe_hours: int = Query(24, description="Timeframe in hours", ge=1, le=168)
):
    """
    Get detailed guardrail performance analysis.
    Shows effectiveness, trigger rates, and confidence scores for all guardrails.
    """
    try:
        # Generate export and extract guardrail analysis
        export_data = analytics_service.generate_dashboard_export()
        
        # Find the closest timeframe
        timeframes = {"1h": 1, "6h": 6, "12h": 12, "24h": 24, "3d": 72, "1w": 168}
        closest_timeframe = min(timeframes.items(), key=lambda x: abs(x[1] - timeframe_hours))
        
        timeframe_key = closest_timeframe[0]
        actual_hours = closest_timeframe[1]
        
        if timeframe_key not in export_data.get("time_ranges", {}):
            raise HTTPException(status_code=404, detail="No guardrail data available")
        
        guardrail_analysis = export_data["time_ranges"][timeframe_key].get("guardrail_analysis", {})
        
        return {
            "timeframe_requested": timeframe_hours,
            "timeframe_actual": actual_hours,
            "timeframe_key": timeframe_key,
            "generated_at": datetime.utcnow().isoformat(),
            "guardrail_performance": guardrail_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get guardrail performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve guardrail performance")

@router.get("/providers/performance")
async def get_provider_performance(
    timeframe_hours: int = Query(24, description="Timeframe in hours", ge=1, le=168)
):
    """
    Get detailed AI provider performance analysis.
    Shows response times, error rates, and usage statistics per provider.
    """
    try:
        # Generate export and extract provider analysis
        export_data = analytics_service.generate_dashboard_export()
        
        # Find the closest timeframe
        timeframes = {"1h": 1, "6h": 6, "12h": 12, "24h": 24, "3d": 72, "1w": 168}
        closest_timeframe = min(timeframes.items(), key=lambda x: abs(x[1] - timeframe_hours))
        
        timeframe_key = closest_timeframe[0]
        actual_hours = closest_timeframe[1]
        
        if timeframe_key not in export_data.get("time_ranges", {}):
            raise HTTPException(status_code=404, detail="No provider data available")
        
        provider_performance = export_data["time_ranges"][timeframe_key].get("provider_performance", {})
        
        return {
            "timeframe_requested": timeframe_hours,
            "timeframe_actual": actual_hours,
            "timeframe_key": timeframe_key,
            "generated_at": datetime.utcnow().isoformat(),
            "provider_performance": provider_performance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider performance")

@router.get("/health")
async def analytics_health_check():
    """
    Health check endpoint for the analytics system.
    Returns system status and basic connectivity information.
    """
    try:
        # Check database connectivity
        db_stats = await analytics_service.get_database_stats()
        db_healthy = bool(db_stats and "total_records" in db_stats)
        
        # Check export scheduler status
        scheduler_status = export_scheduler.get_status()
        scheduler_healthy = isinstance(scheduler_status, dict)
        
        health_status = {
            "status": "healthy" if (db_healthy and scheduler_healthy) else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "total_records": db_stats.get("total_records", 0) if db_healthy else 0
                },
                "export_scheduler": {
                    "status": "healthy" if scheduler_healthy else "unhealthy",
                    "running": scheduler_status.get("running", False) if scheduler_healthy else False
                }
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }