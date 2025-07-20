"""
Memory Manager for Phase 2 Optimization
Implements memory usage optimization, cleanup, and monitoring
Target: 40-60% memory reduction with intelligent cleanup
"""

import asyncio
import gc
import logging
import psutil
import time
import torch
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from threading import Lock
import weakref

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """Memory statistics snapshot"""
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    memory_percent: float
    process_memory_mb: float
    gpu_memory_mb: float
    swap_memory_mb: float
    timestamp: float

class MemoryManager:
    """
    Memory optimization and management system:
    - Automatic memory cleanup
    - Model memory management
    - Garbage collection optimization
    - Memory leak detection
    - GPU memory management
    """
    
    def __init__(self, 
                 max_memory_mb: int = 4096,
                 cleanup_threshold: float = 0.85,
                 monitoring_interval: int = 60):
        
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold
        self.monitoring_interval = monitoring_interval
        
        # Memory tracking
        self.memory_history: List[MemoryStats] = []
        self.max_history_size = 100
        
        # Cleanup callbacks
        self.cleanup_callbacks: List[Callable] = []
        self.cleanup_lock = Lock()
        
        # Model references for cleanup
        self.model_references: Dict[str, weakref.ref] = {}
        
        # Memory monitoring
        self.monitoring_active = False
        self.monitoring_task = None
        
        # Statistics
        self.stats = {
            "cleanup_count": 0,
            "memory_freed_mb": 0.0,
            "peak_memory_mb": 0.0,
            "average_memory_mb": 0.0,
            "gc_collections": 0,
            "model_unloads": 0
        }
        
        logger.info(f"MemoryManager initialized: max {max_memory_mb}MB, cleanup at {cleanup_threshold*100}%")
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        try:
            # System memory
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # GPU memory (if available)
            gpu_memory = 0.0
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.memory_allocated() / (1024 * 1024)  # MB
            
            return MemoryStats(
                total_memory_mb=memory.total / (1024 * 1024),
                available_memory_mb=memory.available / (1024 * 1024),
                used_memory_mb=memory.used / (1024 * 1024),
                memory_percent=memory.percent,
                process_memory_mb=process_memory,
                gpu_memory_mb=gpu_memory,
                swap_memory_mb=swap.used / (1024 * 1024),
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats(0, 0, 0, 0, 0, 0, 0, time.time())
    
    def add_cleanup_callback(self, callback: Callable) -> None:
        """Add cleanup callback function"""
        with self.cleanup_lock:
            self.cleanup_callbacks.append(callback)
            logger.info(f"Added cleanup callback: {callback.__name__}")
    
    def remove_cleanup_callback(self, callback: Callable) -> None:
        """Remove cleanup callback function"""
        with self.cleanup_lock:
            if callback in self.cleanup_callbacks:
                self.cleanup_callbacks.remove(callback)
                logger.info(f"Removed cleanup callback: {callback.__name__}")
    
    def register_model(self, model_name: str, model_object: Any) -> None:
        """Register model for memory tracking"""
        try:
            # Create weak reference to avoid circular references
            self.model_references[model_name] = weakref.ref(model_object)
            logger.info(f"Registered model for memory tracking: {model_name}")
            
        except Exception as e:
            logger.error(f"Error registering model {model_name}: {e}")
    
    def unregister_model(self, model_name: str) -> bool:
        """Unregister model from memory tracking"""
        try:
            if model_name in self.model_references:
                del self.model_references[model_name]
                logger.info(f"Unregistered model: {model_name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error unregistering model {model_name}: {e}")
            return False
    
    async def cleanup_memory(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform memory cleanup
        
        Args:
            force: Force cleanup regardless of threshold
            
        Returns:
            Cleanup statistics
        """
        cleanup_stats = {
            "cleanup_triggered": False,
            "memory_before_mb": 0.0,
            "memory_after_mb": 0.0,
            "memory_freed_mb": 0.0,
            "actions_taken": [],
            "callbacks_executed": 0,
            "gc_collections": 0,
            "models_unloaded": 0
        }
        
        try:
            # Get memory stats before cleanup
            stats_before = self.get_memory_stats()
            cleanup_stats["memory_before_mb"] = stats_before.process_memory_mb
            
            # Check if cleanup is needed
            memory_usage = stats_before.memory_percent / 100.0
            
            if not force and memory_usage < self.cleanup_threshold:
                logger.debug(f"Memory usage {memory_usage:.1%} below threshold {self.cleanup_threshold:.1%}")
                return cleanup_stats
            
            cleanup_stats["cleanup_triggered"] = True
            logger.info(f"Starting memory cleanup: {memory_usage:.1%} usage")
            
            # 1. Execute cleanup callbacks
            with self.cleanup_lock:
                for callback in self.cleanup_callbacks:
                    try:
                        await callback() if asyncio.iscoroutinefunction(callback) else callback()
                        cleanup_stats["callbacks_executed"] += 1
                        cleanup_stats["actions_taken"].append(f"callback_{callback.__name__}")
                    except Exception as e:
                        logger.error(f"Cleanup callback error: {e}")
            
            # 2. Clean up dead model references
            dead_models = []
            for model_name, model_ref in self.model_references.items():
                if model_ref() is None:
                    dead_models.append(model_name)
            
            for model_name in dead_models:
                del self.model_references[model_name]
                cleanup_stats["models_unloaded"] += 1
                cleanup_stats["actions_taken"].append(f"unload_{model_name}")
            
            # 3. GPU memory cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                cleanup_stats["actions_taken"].append("gpu_cache_clear")
            
            # 4. Garbage collection
            gc_before = len(gc.get_objects())
            
            # Force garbage collection
            collected = gc.collect()
            cleanup_stats["gc_collections"] = collected
            
            if collected > 0:
                cleanup_stats["actions_taken"].append(f"gc_collect_{collected}")
            
            # 5. Clear unreferenced cycles
            gc.collect()
            
            gc_after = len(gc.get_objects())
            objects_freed = gc_before - gc_after
            
            if objects_freed > 0:
                cleanup_stats["actions_taken"].append(f"objects_freed_{objects_freed}")
            
            # Get memory stats after cleanup
            stats_after = self.get_memory_stats()
            cleanup_stats["memory_after_mb"] = stats_after.process_memory_mb
            cleanup_stats["memory_freed_mb"] = stats_before.process_memory_mb - stats_after.process_memory_mb
            
            # Update statistics
            self.stats["cleanup_count"] += 1
            self.stats["memory_freed_mb"] += cleanup_stats["memory_freed_mb"]
            self.stats["gc_collections"] += cleanup_stats["gc_collections"]
            self.stats["model_unloads"] += cleanup_stats["models_unloaded"]
            
            logger.info(f"Memory cleanup completed: {cleanup_stats['memory_freed_mb']:.1f}MB freed")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")
            cleanup_stats["error"] = str(e)
            return cleanup_stats
    
    def optimize_gc(self) -> Dict[str, Any]:
        """
        Optimize garbage collection settings
        
        Returns:
            Optimization statistics
        """
        try:
            optimization_stats = {
                "gc_enabled": gc.isenabled(),
                "thresholds_before": gc.get_threshold(),
                "thresholds_after": None,
                "debug_flags": gc.get_debug(),
                "optimization_applied": False
            }
            
            # Enable garbage collection if disabled
            if not gc.isenabled():
                gc.enable()
                optimization_stats["gc_enabled"] = True
                optimization_stats["optimization_applied"] = True
            
            # Optimize GC thresholds for ML workloads
            # Default is usually (700, 10, 10)
            # For ML: more aggressive gen0, less aggressive gen1/gen2
            current_thresholds = gc.get_threshold()
            
            # Optimize for frequent small objects (tensors, arrays)
            new_thresholds = (
                min(500, current_thresholds[0]),  # More frequent gen0 collection
                max(15, current_thresholds[1]),   # Less frequent gen1
                max(15, current_thresholds[2])    # Less frequent gen2
            )
            
            if new_thresholds != current_thresholds:
                gc.set_threshold(*new_thresholds)
                optimization_stats["thresholds_after"] = new_thresholds
                optimization_stats["optimization_applied"] = True
            
            logger.info(f"GC optimization: thresholds {current_thresholds} -> {new_thresholds}")
            
            return optimization_stats
            
        except Exception as e:
            logger.error(f"GC optimization error: {e}")
            return {"error": str(e)}
    
    async def start_monitoring(self) -> bool:
        """Start memory monitoring task"""
        try:
            if self.monitoring_active:
                logger.warning("Memory monitoring already active")
                return False
            
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("Memory monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting memory monitoring: {e}")
            return False
    
    async def stop_monitoring(self) -> bool:
        """Stop memory monitoring task"""
        try:
            if not self.monitoring_active:
                return False
            
            self.monitoring_active = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                self.monitoring_task = None
            
            logger.info("Memory monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping memory monitoring: {e}")
            return False
    
    async def _monitoring_loop(self) -> None:
        """Memory monitoring loop"""
        try:
            while self.monitoring_active:
                # Get current memory stats
                stats = self.get_memory_stats()
                
                # Add to history
                self.memory_history.append(stats)
                
                # Trim history if too long
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history.pop(0)
                
                # Update statistics
                self.stats["peak_memory_mb"] = max(self.stats["peak_memory_mb"], stats.process_memory_mb)
                
                if len(self.memory_history) > 1:
                    avg_memory = sum(s.process_memory_mb for s in self.memory_history) / len(self.memory_history)
                    self.stats["average_memory_mb"] = avg_memory
                
                # Check if cleanup is needed
                if stats.memory_percent / 100.0 > self.cleanup_threshold:
                    logger.warning(f"Memory usage {stats.memory_percent:.1f}% exceeds threshold")
                    await self.cleanup_memory()
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)
                
        except asyncio.CancelledError:
            logger.info("Memory monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Memory monitoring loop error: {e}")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report"""
        try:
            current_stats = self.get_memory_stats()
            
            report = {
                "current_memory": {
                    "total_mb": current_stats.total_memory_mb,
                    "available_mb": current_stats.available_memory_mb,
                    "used_mb": current_stats.used_memory_mb,
                    "usage_percent": current_stats.memory_percent,
                    "process_mb": current_stats.process_memory_mb,
                    "gpu_mb": current_stats.gpu_memory_mb,
                    "swap_mb": current_stats.swap_memory_mb
                },
                "statistics": self.stats.copy(),
                "configuration": {
                    "max_memory_mb": self.max_memory_mb,
                    "cleanup_threshold": self.cleanup_threshold,
                    "monitoring_interval": self.monitoring_interval,
                    "monitoring_active": self.monitoring_active
                },
                "model_tracking": {
                    "registered_models": len(self.model_references),
                    "active_models": sum(1 for ref in self.model_references.values() if ref() is not None),
                    "cleanup_callbacks": len(self.cleanup_callbacks)
                },
                "garbage_collection": {
                    "enabled": gc.isenabled(),
                    "thresholds": gc.get_threshold(),
                    "counts": gc.get_count(),
                    "objects": len(gc.get_objects())
                }
            }
            
            # Add memory trends if history available
            if len(self.memory_history) >= 2:
                recent_stats = self.memory_history[-10:]  # Last 10 measurements
                
                report["trends"] = {
                    "memory_trend": "increasing" if recent_stats[-1].process_memory_mb > recent_stats[0].process_memory_mb else "decreasing",
                    "average_usage_mb": sum(s.process_memory_mb for s in recent_stats) / len(recent_stats),
                    "peak_usage_mb": max(s.process_memory_mb for s in recent_stats),
                    "min_usage_mb": min(s.process_memory_mb for s in recent_stats)
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating memory report: {e}")
            return {"error": str(e)}
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force immediate memory cleanup"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.cleanup_memory(force=True))
        except Exception as e:
            logger.error(f"Force cleanup error: {e}")
            return {"error": str(e)}
    
    def set_memory_limit(self, max_memory_mb: int) -> bool:
        """Set memory limit"""
        try:
            old_limit = self.max_memory_mb
            self.max_memory_mb = max_memory_mb
            
            logger.info(f"Memory limit updated: {old_limit}MB -> {max_memory_mb}MB")
            return True
            
        except Exception as e:
            logger.error(f"Error setting memory limit: {e}")
            return False
    
    def get_model_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage by registered models"""
        try:
            model_usage = {}
            
            for model_name, model_ref in self.model_references.items():
                model = model_ref()
                if model is not None:
                    try:
                        # Estimate model memory usage
                        memory_mb = 0.0
                        
                        # For PyTorch models
                        if hasattr(model, 'parameters'):
                            for param in model.parameters():
                                memory_mb += param.nelement() * param.element_size() / (1024 * 1024)
                        
                        # For transformers models
                        elif hasattr(model, 'model') and hasattr(model.model, 'parameters'):
                            for param in model.model.parameters():
                                memory_mb += param.nelement() * param.element_size() / (1024 * 1024)
                        
                        model_usage[model_name] = {
                            "memory_mb": memory_mb,
                            "active": True
                        }
                        
                    except Exception as e:
                        model_usage[model_name] = {
                            "memory_mb": 0.0,
                            "active": True,
                            "error": str(e)
                        }
                else:
                    model_usage[model_name] = {
                        "memory_mb": 0.0,
                        "active": False
                    }
            
            return model_usage
            
        except Exception as e:
            logger.error(f"Error getting model memory usage: {e}")
            return {"error": str(e)}
    
    async def cleanup_models(self, model_names: List[str] = None) -> Dict[str, Any]:
        """
        Cleanup specific models or all models
        
        Args:
            model_names: List of model names to cleanup (None for all)
            
        Returns:
            Cleanup statistics
        """
        try:
            cleanup_stats = {
                "models_cleaned": 0,
                "memory_freed_mb": 0.0,
                "errors": []
            }
            
            models_to_cleanup = model_names or list(self.model_references.keys())
            
            for model_name in models_to_cleanup:
                try:
                    if model_name in self.model_references:
                        model_ref = self.model_references[model_name]
                        model = model_ref()
                        
                        if model is not None:
                            # Get memory usage before cleanup
                            memory_before = 0.0
                            if hasattr(model, 'parameters'):
                                for param in model.parameters():
                                    memory_before += param.nelement() * param.element_size() / (1024 * 1024)
                            
                            # Cleanup model
                            if hasattr(model, 'unload_model'):
                                model.unload_model()
                            
                            # Clear reference
                            del self.model_references[model_name]
                            
                            cleanup_stats["models_cleaned"] += 1
                            cleanup_stats["memory_freed_mb"] += memory_before
                            
                            logger.info(f"Cleaned up model {model_name}: {memory_before:.1f}MB freed")
                        
                except Exception as e:
                    cleanup_stats["errors"].append(f"{model_name}: {str(e)}")
                    logger.error(f"Error cleaning up model {model_name}: {e}")
            
            # Force garbage collection after model cleanup
            if cleanup_stats["models_cleaned"] > 0:
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Model cleanup error: {e}")
            return {"error": str(e)}
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            if self.monitoring_active:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.stop_monitoring())
        except Exception as e:
            logger.error(f"Cleanup error in destructor: {e}")