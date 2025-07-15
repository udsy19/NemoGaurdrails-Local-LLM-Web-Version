"""
Analytics API endpoints for request tracking and monitoring
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from app.services.analytics_service import analytics_service, RequestStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

class RequestTrackingData(BaseModel):
    message: str
    status: str
    blocking_reasons: Optional[List[str]] = None
    detection_results: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None

@router.get("/summary")
async def get_analytics_summary(hours: int = 24):
    """Get comprehensive analytics summary"""
    try:
        if hours <= 0 or hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        summary = analytics_service.get_analytics_summary(hours)
        
        return {
            "success": True,
            "summary": {
                "timeframe_hours": summary.timeframe_hours,
                "total_requests": summary.total_requests,
                "blocked_requests": summary.blocked_requests,
                "allowed_requests": summary.allowed_requests,
                "unique_users": summary.unique_users,
                "unique_ips": summary.unique_ips,
                "top_blocking_reasons": summary.top_blocking_reasons,
                "detector_stats": [
                    {
                        "name": stat.name,
                        "total_detections": stat.total_detections,
                        "blocked_count": stat.blocked_count,
                        "allowed_count": stat.allowed_count,
                        "avg_confidence": round(stat.avg_confidence, 3),
                        "last_triggered": stat.last_triggered.isoformat() if stat.last_triggered else None,
                        "block_rate": round(stat.blocked_count / stat.total_detections * 100, 1) if stat.total_detections > 0 else 0
                    }
                    for stat in summary.detector_stats
                ],
                "request_timeline": summary.request_timeline,
                "user_activity": summary.user_activity,
                "geographic_data": summary.geographic_data,
                "error_rate": round(summary.error_rate, 2),
                "avg_response_time": round(summary.avg_response_time, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realtime")
async def get_realtime_stats():
    """Get real-time statistics"""
    try:
        stats = analytics_service.get_real_time_stats()
        
        return {
            "success": True,
            "stats": {
                "total_requests": stats["total_requests"],
                "blocked_requests": stats["blocked_requests"],
                "allowed_requests": stats["allowed_requests"],
                "error_requests": stats["error_requests"],
                "recent_requests_5min": stats["recent_requests_5min"],
                "unique_users_total": stats["unique_users_total"],
                "avg_response_time": round(stats["avg_response_time"], 2),
                "block_rate": round(stats["block_rate"], 1),
                "requests_per_minute": round(stats["requests_per_minute"], 1),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting real-time stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track")
async def track_request(request: Request, tracking_data: RequestTrackingData):
    """Track a new request event"""
    try:
        # Get client IP and user agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Convert status string to enum
        try:
            status = RequestStatus(tracking_data.status.lower())
        except ValueError:
            status = RequestStatus.ERROR
        
        # Track the request
        event_id = analytics_service.track_request(
            ip_address=client_ip,
            user_agent=user_agent,
            message=tracking_data.message,
            status=status,
            blocking_reasons=tracking_data.blocking_reasons,
            detection_results=tracking_data.detection_results,
            response_time_ms=tracking_data.response_time_ms or 0.0,
            provider=tracking_data.provider,
            model=tracking_data.model,
            session_id=tracking_data.session_id
        )
        
        return {
            "success": True,
            "event_id": event_id,
            "message": "Request tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error tracking request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detectors")
async def get_detector_analytics():
    """Get detector-specific analytics"""
    try:
        summary = analytics_service.get_analytics_summary(24)
        
        detector_analytics = []
        for stat in summary.detector_stats:
            detector_analytics.append({
                "name": stat.name,
                "display_name": stat.name.replace("_", " ").title(),
                "total_detections": stat.total_detections,
                "blocked_count": stat.blocked_count,
                "allowed_count": stat.allowed_count,
                "block_rate": round(stat.blocked_count / stat.total_detections * 100, 1) if stat.total_detections > 0 else 0,
                "avg_confidence": round(stat.avg_confidence, 3),
                "last_triggered": stat.last_triggered.isoformat() if stat.last_triggered else None,
                "effectiveness": "high" if stat.blocked_count > 0 else "low"
            })
        
        return {
            "success": True,
            "detectors": detector_analytics,
            "total_detectors": len(detector_analytics)
        }
        
    except Exception as e:
        logger.error(f"Error getting detector analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def get_user_analytics(limit: int = 50):
    """Get user activity analytics"""
    try:
        if limit <= 0 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        summary = analytics_service.get_analytics_summary(24)
        
        # Limit user activity results
        user_activity = summary.user_activity[:limit]
        
        return {
            "success": True,
            "users": user_activity,
            "total_unique_ips": summary.unique_ips,
            "total_unique_users": summary.unique_users
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline")
async def get_request_timeline(hours: int = 24):
    """Get request timeline data"""
    try:
        if hours <= 0 or hours > 168:
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        summary = analytics_service.get_analytics_summary(hours)
        
        return {
            "success": True,
            "timeline": summary.request_timeline,
            "timeframe_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Error getting request timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/geographic")
async def get_geographic_analytics():
    """Get geographic distribution of requests"""
    try:
        summary = analytics_service.get_analytics_summary(24)
        
        return {
            "success": True,
            "geographic_data": summary.geographic_data,
            "total_locations": len(summary.geographic_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting geographic analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_analytics_data():
    """Export analytics data for backup or analysis"""
    try:
        data = analytics_service.to_dict()
        
        return {
            "success": True,
            "export_data": data,
            "exported_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_old_data(hours: int = 168):
    """Clean up old analytics data"""
    try:
        if hours < 24 or hours > 8760:  # Min 1 day, max 1 year
            raise HTTPException(status_code=400, detail="Hours must be between 24 and 8760")
        
        analytics_service.clear_old_data(hours)
        
        return {
            "success": True,
            "message": f"Cleaned up data older than {hours} hours"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up analytics data: {e}")
        raise HTTPException(status_code=500, detail=str(e))