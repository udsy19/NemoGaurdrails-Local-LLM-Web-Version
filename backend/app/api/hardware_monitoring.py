
"""
API endpoints for real-time hardware monitoring.

Provides metrics on CPU, memory, GPU, disk, and network usage.
"""

from fastapi import APIRouter, HTTPException
from ..utils.hardware_monitor import hardware_monitor

router = APIRouter(
    prefix="/api/hardware",
    tags=["hardware-monitoring"],
)

@router.get("/metrics")
async def get_hardware_metrics():
    """
    Get a snapshot of the system's current hardware metrics.
    """
    try:
        metrics = await hardware_monitor.get_metrics()
        return {"success": True, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
