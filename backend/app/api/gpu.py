"""
GPU Acceleration API endpoints
Provides dashboard access to GPU acceleration features
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import time

from app.utils.gpu_accelerator import get_gpu_accelerator, AccelerationConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gpu", tags=["gpu"])

class GPUConfigUpdate(BaseModel):
    prefer_gpu: Optional[bool] = None
    auto_device_selection: Optional[bool] = None
    mixed_precision: Optional[bool] = None
    memory_fraction: Optional[float] = None
    batch_size_multiplier: Optional[float] = None
    cache_models: Optional[bool] = None
    fallback_to_cpu: Optional[bool] = None
    max_gpu_memory_mb: Optional[int] = None

class BenchmarkRequest(BaseModel):
    device_id: Optional[int] = None

@router.get("/status", response_model=Dict[str, Any])
async def get_gpu_status():
    """Get comprehensive GPU status and device information"""
    try:
        accelerator = get_gpu_accelerator()
        
        return {
            "success": True,
            "gpu_info": accelerator.get_device_info(),
            "memory_usage": accelerator.get_memory_usage(),
            "active_device": str(accelerator.active_device),
            "available_devices_count": len(accelerator.available_devices),
            "cache_status": {
                "cached_models": len(accelerator.model_cache),
                "cache_enabled": accelerator.config.cache_models
            }
        }
    except Exception as e:
        logger.error(f"Error getting GPU status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=Dict[str, Any])
async def get_gpu_config():
    """Get current GPU acceleration configuration"""
    try:
        accelerator = get_gpu_accelerator()
        config = accelerator.config
        
        return {
            "success": True,
            "config": {
                "prefer_gpu": config.prefer_gpu,
                "auto_device_selection": config.auto_device_selection,
                "mixed_precision": config.mixed_precision,
                "memory_fraction": config.memory_fraction,
                "batch_size_multiplier": config.batch_size_multiplier,
                "cache_models": config.cache_models,
                "fallback_to_cpu": config.fallback_to_cpu,
                "max_gpu_memory_mb": config.max_gpu_memory_mb
            }
        }
    except Exception as e:
        logger.error(f"Error getting GPU config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_gpu_config(config_update: GPUConfigUpdate):
    """Update GPU acceleration configuration"""
    try:
        accelerator = get_gpu_accelerator()
        current_config = accelerator.config
        
        # Update configuration
        updates = {}
        if config_update.prefer_gpu is not None:
            current_config.prefer_gpu = config_update.prefer_gpu
            updates["prefer_gpu"] = config_update.prefer_gpu
            
        if config_update.auto_device_selection is not None:
            current_config.auto_device_selection = config_update.auto_device_selection
            updates["auto_device_selection"] = config_update.auto_device_selection
            
        if config_update.mixed_precision is not None:
            current_config.mixed_precision = config_update.mixed_precision
            updates["mixed_precision"] = config_update.mixed_precision
            
        if config_update.memory_fraction is not None:
            if 0.1 <= config_update.memory_fraction <= 1.0:
                current_config.memory_fraction = config_update.memory_fraction
                updates["memory_fraction"] = config_update.memory_fraction
            else:
                raise HTTPException(status_code=400, detail="Memory fraction must be between 0.1 and 1.0")
                
        if config_update.batch_size_multiplier is not None:
            if 0.5 <= config_update.batch_size_multiplier <= 5.0:
                current_config.batch_size_multiplier = config_update.batch_size_multiplier
                updates["batch_size_multiplier"] = config_update.batch_size_multiplier
            else:
                raise HTTPException(status_code=400, detail="Batch size multiplier must be between 0.5 and 5.0")
                
        if config_update.cache_models is not None:
            current_config.cache_models = config_update.cache_models
            updates["cache_models"] = config_update.cache_models
            
        if config_update.fallback_to_cpu is not None:
            current_config.fallback_to_cpu = config_update.fallback_to_cpu
            updates["fallback_to_cpu"] = config_update.fallback_to_cpu
            
        if config_update.max_gpu_memory_mb is not None:
            current_config.max_gpu_memory_mb = config_update.max_gpu_memory_mb
            updates["max_gpu_memory_mb"] = config_update.max_gpu_memory_mb
        
        # Re-initialize if device selection changed
        if "prefer_gpu" in updates or "auto_device_selection" in updates:
            accelerator._select_optimal_device()
        
        logger.info(f"Updated GPU configuration: {updates}")
        
        return {
            "success": True,
            "message": "GPU configuration updated successfully",
            "updated_fields": list(updates.keys()),
            "new_config": {
                "prefer_gpu": current_config.prefer_gpu,
                "auto_device_selection": current_config.auto_device_selection,
                "mixed_precision": current_config.mixed_precision,
                "memory_fraction": current_config.memory_fraction,
                "batch_size_multiplier": current_config.batch_size_multiplier,
                "cache_models": current_config.cache_models,
                "fallback_to_cpu": current_config.fallback_to_cpu,
                "max_gpu_memory_mb": current_config.max_gpu_memory_mb
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating GPU config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices", response_model=Dict[str, Any])
async def list_gpu_devices():
    """List all available GPU devices with detailed information"""
    try:
        accelerator = get_gpu_accelerator()
        
        devices = []
        for gpu in accelerator.available_devices:
            devices.append({
                "device_id": gpu.device_id,
                "name": gpu.name,
                "vendor": gpu.vendor.value,
                "memory_total_mb": gpu.memory_total,
                "memory_free_mb": gpu.memory_free,
                "memory_used_mb": gpu.memory_used,
                "memory_utilization_percent": (gpu.memory_used / gpu.memory_total) * 100 if gpu.memory_total > 0 else 0,
                "gpu_utilization_percent": gpu.utilization,
                "temperature": gpu.temperature,
                "power_usage": gpu.power_usage,
                "is_active": str(accelerator.active_device).endswith(str(gpu.device_id)) if accelerator.active_device else False
            })
        
        return {
            "success": True,
            "devices": devices,
            "active_device": str(accelerator.active_device),
            "device_count": len(devices)
        }
        
    except Exception as e:
        logger.error(f"Error listing GPU devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/benchmark")
async def benchmark_gpu(request: BenchmarkRequest = None):
    """Run GPU performance benchmark"""
    try:
        accelerator = get_gpu_accelerator()
        
        if request and request.device_id is not None:
            # Benchmark specific device
            import torch
            if request.device_id < len(accelerator.available_devices):
                gpu_info = accelerator.available_devices[request.device_id]
                if gpu_info.vendor.value == "nvidia":
                    device = torch.device(f"cuda:{gpu_info.device_id}")
                elif gpu_info.vendor.value == "apple":
                    device = torch.device("mps")
                else:
                    device = torch.device("cpu")
            else:
                raise HTTPException(status_code=400, detail="Invalid device ID")
        else:
            # Benchmark active device
            device = accelerator.active_device
        
        benchmark_results = accelerator.benchmark_device(device)
        
        return {
            "success": True,
            "device": str(device),
            "benchmark_results": benchmark_results,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running GPU benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_model_cache():
    """Clear GPU model cache"""
    try:
        accelerator = get_gpu_accelerator()
        cache_size_before = len(accelerator.model_cache)
        
        accelerator.clear_cache()
        
        return {
            "success": True,
            "message": f"Cleared {cache_size_before} cached models",
            "models_cleared": cache_size_before
        }
        
    except Exception as e:
        logger.error(f"Error clearing model cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/status")
async def get_cache_status():
    """Get model cache status and statistics"""
    try:
        accelerator = get_gpu_accelerator()
        
        cache_details = []
        for cache_key, cache_item in accelerator.model_cache.items():
            cache_details.append({
                "model_key": cache_key,
                "device": str(cache_item["device"]),
                "cached_at": cache_item["cached_at"],
                "access_count": cache_item["access_count"],
                "age_seconds": time.time() - cache_item["cached_at"]
            })
        
        stats = accelerator.performance_stats
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        hit_rate = (stats["cache_hits"] / max(1, total_requests)) * 100
        
        return {
            "success": True,
            "cache_enabled": accelerator.config.cache_models,
            "cached_models_count": len(accelerator.model_cache),
            "cache_details": cache_details,
            "statistics": {
                "cache_hits": stats["cache_hits"],
                "cache_misses": stats["cache_misses"],
                "hit_rate_percent": hit_rate,
                "total_requests": total_requests
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory")
async def get_memory_info():
    """Get detailed memory usage information"""
    try:
        accelerator = get_gpu_accelerator()
        memory_info = accelerator.get_memory_usage()
        
        # Add more detailed information
        detailed_info = {
            "system_memory": memory_info.get("system_memory", {}),
            "gpu_memory": memory_info.get("gpu_memory", {}),
            "memory_recommendations": []
        }
        
        # Add recommendations based on memory usage
        if "gpu_memory" in memory_info:
            gpu_mem = memory_info["gpu_memory"]
            usage_percent = (gpu_mem["allocated_mb"] / gpu_mem["total_mb"]) * 100
            
            if usage_percent > 90:
                detailed_info["memory_recommendations"].append({
                    "type": "warning",
                    "message": "GPU memory usage is very high (>90%). Consider clearing cache or reducing batch sizes."
                })
            elif usage_percent > 75:
                detailed_info["memory_recommendations"].append({
                    "type": "info", 
                    "message": "GPU memory usage is high (>75%). Monitor for potential issues."
                })
        
        return {
            "success": True,
            **detailed_info
        }
        
    except Exception as e:
        logger.error(f"Error getting memory info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/stats")
async def get_performance_stats():
    """Get comprehensive performance statistics"""
    try:
        accelerator = get_gpu_accelerator()
        stats = accelerator.performance_stats.copy()
        
        # Calculate averages
        if stats["cpu_inference_times"]:
            stats["avg_cpu_inference_ms"] = sum(stats["cpu_inference_times"]) / len(stats["cpu_inference_times"])
        else:
            stats["avg_cpu_inference_ms"] = 0
            
        if stats["gpu_inference_times"]:
            stats["avg_gpu_inference_ms"] = sum(stats["gpu_inference_times"]) / len(stats["gpu_inference_times"])
            speedup = stats["avg_cpu_inference_ms"] / stats["avg_gpu_inference_ms"] if stats["avg_gpu_inference_ms"] > 0 else 1
            stats["gpu_speedup_factor"] = speedup
        else:
            stats["avg_gpu_inference_ms"] = 0
            stats["gpu_speedup_factor"] = 1
        
        return {
            "success": True,
            "performance_stats": stats,
            "device_info": {
                "active_device": str(accelerator.active_device),
                "device_count": len(accelerator.available_devices)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))