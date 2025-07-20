"""
Distributed Processing API endpoints
Provides dashboard access to distributed processing features
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import time

from app.utils.distributed_processor import (
    get_distributed_processor, DistributedConfig, Priority, WorkerType, TaskStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/distributed", tags=["distributed"])

class DistributedConfigUpdate(BaseModel):
    max_workers: Optional[int] = Field(None, ge=1, le=32)
    worker_type: Optional[str] = None
    task_timeout: Optional[float] = Field(None, gt=0)
    enable_load_balancing: Optional[bool] = None
    enable_auto_scaling: Optional[bool] = None
    min_workers: Optional[int] = Field(None, ge=1)
    scale_up_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)
    scale_down_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)

class TaskSubmission(BaseModel):
    function_name: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    priority: str = "normal"
    timeout: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BulkTaskSubmission(BaseModel):
    tasks: List[TaskSubmission]
    batch_id: Optional[str] = None

@router.get("/status", response_model=Dict[str, Any])
async def get_distributed_status():
    """Get comprehensive distributed processing status"""
    try:
        processor = get_distributed_processor()
        status = await processor.get_system_status()
        
        # Add system health indicators
        status["health"] = {
            "status": "healthy" if processor.is_running else "stopped",
            "uptime": time.time() - status["workers"]["details"][0]["created_at"] if status["workers"]["details"] else 0,
            "queue_health": "good" if status["metrics"]["queue_size"] < processor.config.queue_size * 0.8 else "warning",
            "worker_health": "good" if status["workers"]["active"] <= status["workers"]["total"] * 0.9 else "overloaded",
            "error_rate_health": "good" if status["metrics"]["error_rate"] < 5.0 else "concerning"
        }
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error getting distributed status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=Dict[str, Any])
async def get_distributed_config():
    """Get current distributed processing configuration"""
    try:
        processor = get_distributed_processor()
        config = processor.config
        
        return {
            "success": True,
            "config": {
                "max_workers": config.max_workers,
                "worker_type": config.worker_type.value,
                "queue_size": config.queue_size,
                "task_timeout": config.task_timeout,
                "heartbeat_interval": config.heartbeat_interval,
                "cleanup_interval": config.cleanup_interval,
                "retry_delay": config.retry_delay,
                "enable_load_balancing": config.enable_load_balancing,
                "enable_auto_scaling": config.enable_auto_scaling,
                "min_workers": config.min_workers,
                "scale_up_threshold": config.scale_up_threshold,
                "scale_down_threshold": config.scale_down_threshold,
                "enable_metrics": config.enable_metrics
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting distributed config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_distributed_config(config_update: DistributedConfigUpdate):
    """Update distributed processing configuration"""
    try:
        processor = get_distributed_processor()
        current_config = processor.config
        
        updates = {}
        
        if config_update.max_workers is not None:
            current_config.max_workers = config_update.max_workers
            updates["max_workers"] = config_update.max_workers
        
        if config_update.worker_type is not None:
            try:
                worker_type = WorkerType(config_update.worker_type)
                current_config.worker_type = worker_type
                updates["worker_type"] = config_update.worker_type
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid worker type: {config_update.worker_type}")
        
        if config_update.task_timeout is not None:
            current_config.task_timeout = config_update.task_timeout
            updates["task_timeout"] = config_update.task_timeout
        
        if config_update.enable_load_balancing is not None:
            current_config.enable_load_balancing = config_update.enable_load_balancing
            updates["enable_load_balancing"] = config_update.enable_load_balancing
        
        if config_update.enable_auto_scaling is not None:
            current_config.enable_auto_scaling = config_update.enable_auto_scaling
            updates["enable_auto_scaling"] = config_update.enable_auto_scaling
        
        if config_update.min_workers is not None:
            if config_update.min_workers > current_config.max_workers:
                raise HTTPException(status_code=400, detail="min_workers cannot exceed max_workers")
            current_config.min_workers = config_update.min_workers
            updates["min_workers"] = config_update.min_workers
        
        if config_update.scale_up_threshold is not None:
            current_config.scale_up_threshold = config_update.scale_up_threshold
            updates["scale_up_threshold"] = config_update.scale_up_threshold
        
        if config_update.scale_down_threshold is not None:
            current_config.scale_down_threshold = config_update.scale_down_threshold
            updates["scale_down_threshold"] = config_update.scale_down_threshold
        
        logger.info(f"Updated distributed processing configuration: {updates}")
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_fields": list(updates.keys()),
            "new_config": await get_distributed_config()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating distributed config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/submit")
async def submit_task(task: TaskSubmission):
    """Submit a single task for distributed processing"""
    try:
        processor = get_distributed_processor()
        
        if not processor.is_running:
            raise HTTPException(status_code=503, detail="Distributed processor is not running")
        
        # Validate priority
        try:
            priority = Priority[task.priority.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {task.priority}")
        
        # Submit task
        task_id = await processor.submit_task(
            function_name=task.function_name,
            *task.args,
            priority=priority,
            timeout=task.timeout,
            metadata=task.metadata,
            **task.kwargs
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task submitted successfully: {task_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/submit-bulk")
async def submit_bulk_tasks(bulk_submission: BulkTaskSubmission):
    """Submit multiple tasks for distributed processing"""
    try:
        processor = get_distributed_processor()
        
        if not processor.is_running:
            raise HTTPException(status_code=503, detail="Distributed processor is not running")
        
        task_ids = []
        errors = []
        
        for i, task in enumerate(bulk_submission.tasks):
            try:
                # Validate priority
                priority = Priority[task.priority.upper()]
                
                # Submit task
                task_id = await processor.submit_task(
                    function_name=task.function_name,
                    *task.args,
                    priority=priority,
                    timeout=task.timeout,
                    metadata={**(task.metadata or {}), "batch_id": bulk_submission.batch_id, "batch_index": i},
                    **task.kwargs
                )
                task_ids.append(task_id)
                
            except Exception as e:
                errors.append({"task_index": i, "error": str(e)})
        
        return {
            "success": len(errors) == 0,
            "task_ids": task_ids,
            "submitted_count": len(task_ids),
            "error_count": len(errors),
            "errors": errors,
            "batch_id": bulk_submission.batch_id
        }
        
    except Exception as e:
        logger.error(f"Error submitting bulk tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    try:
        processor = get_distributed_processor()
        task = await processor.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
        return {
            "success": True,
            "task": {
                "id": task.id,
                "function_name": task.function_name,
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "processing_time": (task.completed_at - task.started_at) if task.started_at and task.completed_at else None,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "worker_id": task.worker_id,
                "error": task.error,
                "metadata": task.metadata,
                "result_available": task.result is not None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a pending or processing task"""
    try:
        processor = get_distributed_processor()
        cancelled = await processor.cancel_task(task_id)
        
        if not cancelled:
            task = await processor.get_task_status(task_id)
            if not task:
                raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
            else:
                raise HTTPException(status_code=400, detail=f"Task cannot be cancelled (status: {task.status.value})")
        
        return {
            "success": True,
            "message": f"Task cancelled successfully: {task_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    function_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List tasks with optional filtering"""
    try:
        processor = get_distributed_processor()
        system_status = await processor.get_system_status()
        
        # Get all tasks
        all_tasks = list(processor.tasks.values())
        
        # Apply filters
        filtered_tasks = all_tasks
        
        if status:
            try:
                status_enum = TaskStatus[status.upper()]
                filtered_tasks = [t for t in filtered_tasks if t.status == status_enum]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if function_name:
            filtered_tasks = [t for t in filtered_tasks if t.function_name == function_name]
        
        # Sort by created_at (newest first)
        filtered_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # Apply pagination
        total_tasks = len(filtered_tasks)
        paginated_tasks = filtered_tasks[offset:offset + limit]
        
        return {
            "success": True,
            "tasks": [
                {
                    "id": task.id,
                    "function_name": task.function_name,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "processing_time": (task.completed_at - task.started_at) if task.started_at and task.completed_at else None,
                    "worker_id": task.worker_id,
                    "error": task.error,
                    "retry_count": task.retry_count
                }
                for task in paginated_tasks
            ],
            "pagination": {
                "total": total_tasks,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_tasks
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workers")
async def list_workers():
    """List all workers and their status"""
    try:
        processor = get_distributed_processor()
        system_status = await processor.get_system_status()
        
        return {
            "success": True,
            "workers": system_status["workers"]["details"],
            "summary": {
                "total": system_status["workers"]["total"],
                "active": system_status["workers"]["active"],
                "idle": system_status["workers"]["idle"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics():
    """Get detailed system metrics"""
    try:
        processor = get_distributed_processor()
        system_status = await processor.get_system_status()
        
        # Calculate additional metrics
        metrics = system_status["metrics"].copy()
        
        # Performance analysis
        if metrics["processing_times"]:
            processing_times = metrics["processing_times"]
            metrics["performance_analysis"] = {
                "min_processing_time": min(processing_times),
                "max_processing_time": max(processing_times),
                "median_processing_time": sorted(processing_times)[len(processing_times) // 2],
                "percentile_95": sorted(processing_times)[int(len(processing_times) * 0.95)],
                "percentile_99": sorted(processing_times)[int(len(processing_times) * 0.99)]
            }
        
        # System efficiency
        total_tasks = metrics["tasks_completed"] + metrics["tasks_failed"]
        if total_tasks > 0:
            metrics["efficiency"] = {
                "success_rate": (metrics["tasks_completed"] / total_tasks) * 100,
                "failure_rate": (metrics["tasks_failed"] / total_tasks) * 100,
                "avg_retries": sum(t.retry_count for t in processor.tasks.values()) / len(processor.tasks) if processor.tasks else 0
            }
        
        return {
            "success": True,
            "metrics": metrics,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_distributed_processing(background_tasks: BackgroundTasks):
    """Start the distributed processing system"""
    try:
        processor = get_distributed_processor()
        
        if processor.is_running:
            return {
                "success": True,
                "message": "Distributed processing is already running"
            }
        
        # Start in background
        background_tasks.add_task(processor.start)
        
        return {
            "success": True,
            "message": "Distributed processing system starting..."
        }
        
    except Exception as e:
        logger.error(f"Error starting distributed processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_distributed_processing(background_tasks: BackgroundTasks):
    """Stop the distributed processing system"""
    try:
        processor = get_distributed_processor()
        
        if not processor.is_running:
            return {
                "success": True,
                "message": "Distributed processing is already stopped"
            }
        
        # Stop in background
        background_tasks.add_task(processor.shutdown)
        
        return {
            "success": True,
            "message": "Distributed processing system stopping..."
        }
        
    except Exception as e:
        logger.error(f"Error stopping distributed processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/functions")
async def list_registered_functions():
    """List all registered functions available for distributed processing"""
    try:
        processor = get_distributed_processor()
        
        return {
            "success": True,
            "functions": list(processor.function_registry.keys()),
            "count": len(processor.function_registry)
        }
        
    except Exception as e:
        logger.error(f"Error listing functions: {e}")
        raise HTTPException(status_code=500, detail=str(e))