"""
GPU Acceleration Manager
Optimizes model loading and inference using GPU acceleration where available
"""

import torch
import logging
import psutil
import platform
from typing import Dict, Any, Optional, List, Tuple
import threading
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GPUVendor(Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"

@dataclass
class GPUInfo:
    """GPU device information"""
    device_id: int
    name: str
    vendor: GPUVendor
    memory_total: int  # in MB
    memory_free: int   # in MB
    memory_used: int   # in MB
    utilization: float # percentage
    temperature: Optional[float] = None
    power_usage: Optional[float] = None

@dataclass
class AccelerationConfig:
    """Configuration for GPU acceleration"""
    prefer_gpu: bool = True
    auto_device_selection: bool = True
    mixed_precision: bool = True
    memory_fraction: float = 0.8
    batch_size_multiplier: float = 1.5
    cache_models: bool = True
    fallback_to_cpu: bool = True
    max_gpu_memory_mb: Optional[int] = None

class GPUAccelerator:
    """
    Manages GPU acceleration for AI Safety System models
    """
    
    def __init__(self, config: AccelerationConfig = None):
        self.config = config or AccelerationConfig()
        self.available_devices = []
        self.active_device = None
        self.device_map = {}
        self.model_cache = {}
        self.memory_monitor = None
        self.is_monitoring = False
        
        # Performance tracking
        self.performance_stats = {
            "cpu_inference_times": [],
            "gpu_inference_times": [],
            "memory_usage": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_events": 0
        }
        
        self._initialize_gpu_support()
    
    def _initialize_gpu_support(self):
        """Initialize GPU support and detect available devices"""
        try:
            logger.info("Initializing GPU acceleration support...")
            
            # Check for CUDA availability
            if torch.cuda.is_available():
                self._detect_nvidia_gpus()
            
            # Check for MPS (Apple Silicon)
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self._detect_apple_silicon()
            
            # Check for Intel GPU support (future)
            # self._detect_intel_gpus()
            
            # Select best device
            self._select_optimal_device()
            
            # Start memory monitoring
            if self.config.auto_device_selection:
                self._start_memory_monitoring()
            
            logger.info(f"GPU Accelerator initialized with {len(self.available_devices)} devices")
            if self.active_device:
                logger.info(f"Active device: {self.active_device}")
            
        except Exception as e:
            logger.warning(f"GPU initialization failed: {e}, falling back to CPU")
            self.active_device = torch.device("cpu")
    
    def _detect_nvidia_gpus(self):
        """Detect NVIDIA GPUs"""
        try:
            device_count = torch.cuda.device_count()
            
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                memory_total = props.total_memory // (1024 * 1024)  # Convert to MB
                memory_free = (props.total_memory - torch.cuda.memory_allocated(i)) // (1024 * 1024)
                memory_used = torch.cuda.memory_allocated(i) // (1024 * 1024)
                
                gpu_info = GPUInfo(
                    device_id=i,
                    name=props.name,
                    vendor=GPUVendor.NVIDIA,
                    memory_total=memory_total,
                    memory_free=memory_free,
                    memory_used=memory_used,
                    utilization=0.0  # Would need nvidia-ml-py for real utilization
                )
                
                self.available_devices.append(gpu_info)
                logger.info(f"Detected NVIDIA GPU {i}: {props.name} ({memory_total}MB)")
                
        except Exception as e:
            logger.warning(f"Failed to detect NVIDIA GPUs: {e}")
    
    def _detect_apple_silicon(self):
        """Detect Apple Silicon MPS"""
        try:
            if platform.system() == "Darwin" and platform.machine() == "arm64":
                # Apple Silicon detected
                gpu_info = GPUInfo(
                    device_id=0,
                    name="Apple Silicon GPU",
                    vendor=GPUVendor.APPLE,
                    memory_total=self._get_apple_gpu_memory(),
                    memory_free=self._get_apple_gpu_memory(),
                    memory_used=0,
                    utilization=0.0
                )
                
                self.available_devices.append(gpu_info)
                logger.info(f"Detected Apple Silicon GPU: {gpu_info.name}")
                
        except Exception as e:
            logger.warning(f"Failed to detect Apple Silicon GPU: {e}")
    
    def _get_apple_gpu_memory(self) -> int:
        """Estimate Apple Silicon GPU memory"""
        try:
            # For Apple Silicon, GPU shares system memory
            total_memory = psutil.virtual_memory().total
            # Estimate GPU can use ~60% of system memory
            gpu_memory = int(total_memory * 0.6) // (1024 * 1024)
            return gpu_memory
        except:
            return 8192  # Default 8GB estimate
    
    def _select_optimal_device(self):
        """Select the best available device"""
        if not self.config.prefer_gpu or not self.available_devices:
            self.active_device = torch.device("cpu")
            logger.info("Using CPU device")
            return
        
        # Sort devices by available memory
        sorted_devices = sorted(
            self.available_devices, 
            key=lambda x: x.memory_free, 
            reverse=True
        )
        
        best_gpu = sorted_devices[0]
        
        # Select device based on vendor
        if best_gpu.vendor == GPUVendor.NVIDIA:
            self.active_device = torch.device(f"cuda:{best_gpu.device_id}")
        elif best_gpu.vendor == GPUVendor.APPLE:
            self.active_device = torch.device("mps")
        else:
            self.active_device = torch.device("cpu")
        
        logger.info(f"Selected optimal device: {self.active_device} ({best_gpu.name})")
    
    def _start_memory_monitoring(self):
        """Start background memory monitoring"""
        def monitor_memory():
            while self.is_monitoring:
                try:
                    self._update_device_memory_stats()
                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
                    time.sleep(10)
        
        self.is_monitoring = True
        self.memory_monitor = threading.Thread(target=monitor_memory, daemon=True)
        self.memory_monitor.start()
        logger.info("Started GPU memory monitoring")
    
    def _update_device_memory_stats(self):
        """Update memory statistics for all devices"""
        for gpu_info in self.available_devices:
            if gpu_info.vendor == GPUVendor.NVIDIA:
                try:
                    device_id = gpu_info.device_id
                    memory_used = torch.cuda.memory_allocated(device_id) // (1024 * 1024)
                    memory_total = torch.cuda.get_device_properties(device_id).total_memory // (1024 * 1024)
                    memory_free = memory_total - memory_used
                    
                    gpu_info.memory_used = memory_used
                    gpu_info.memory_free = memory_free
                    gpu_info.utilization = (memory_used / memory_total) * 100
                    
                except Exception as e:
                    logger.warning(f"Failed to update memory stats for GPU {device_id}: {e}")
    
    def get_optimal_device(self, model_size_mb: Optional[int] = None) -> torch.device:
        """Get optimal device for a model of given size"""
        if not self.config.prefer_gpu:
            return torch.device("cpu")
        
        if model_size_mb and self.available_devices:
            # Find device with enough memory
            for gpu_info in sorted(self.available_devices, key=lambda x: x.memory_free, reverse=True):
                if gpu_info.memory_free > model_size_mb * 1.2:  # 20% buffer
                    if gpu_info.vendor == GPUVendor.NVIDIA:
                        return torch.device(f"cuda:{gpu_info.device_id}")
                    elif gpu_info.vendor == GPUVendor.APPLE:
                        return torch.device("mps")
        
        return self.active_device or torch.device("cpu")
    
    def optimize_model_for_device(self, model, device: torch.device = None) -> torch.Tensor:
        """Optimize model for target device"""
        if device is None:
            device = self.active_device or torch.device("cpu")
        
        try:
            start_time = time.time()
            
            # Move model to device
            model = model.to(device)
            
            # Enable mixed precision if supported
            if self.config.mixed_precision and device.type == "cuda":
                model = model.half()  # Convert to FP16
            
            # Optimize for inference
            model.eval()
            
            # Compile model if using PyTorch 2.0+
            if hasattr(torch, 'compile') and device.type in ["cuda", "mps"]:
                try:
                    model = torch.compile(model, mode="reduce-overhead")
                    logger.info("Model compiled with torch.compile")
                except Exception as e:
                    logger.warning(f"Failed to compile model: {e}")
            
            optimization_time = (time.time() - start_time) * 1000
            logger.info(f"Model optimized for {device} in {optimization_time:.2f}ms")
            
            return model
            
        except Exception as e:
            logger.error(f"Model optimization failed: {e}")
            if self.config.fallback_to_cpu:
                logger.info("Falling back to CPU")
                self.performance_stats["fallback_events"] += 1
                return model.to(torch.device("cpu"))
            raise
    
    def get_optimal_batch_size(self, base_batch_size: int, model_size_mb: Optional[int] = None) -> int:
        """Calculate optimal batch size based on available GPU memory"""
        if not self.active_device or self.active_device.type == "cpu":
            return base_batch_size
        
        try:
            if self.active_device.type == "cuda":
                device_id = self.active_device.index or 0
                available_memory = torch.cuda.get_device_properties(device_id).total_memory
                free_memory = available_memory - torch.cuda.memory_allocated(device_id)
                
                # Estimate memory per sample (rough heuristic)
                memory_per_sample = (model_size_mb or 100) * 1024 * 1024 / base_batch_size
                max_batch_size = int(free_memory * self.config.memory_fraction / memory_per_sample)
                
                # Apply multiplier and bounds
                optimal_batch_size = min(
                    max_batch_size,
                    int(base_batch_size * self.config.batch_size_multiplier)
                )
                
                return max(1, optimal_batch_size)
            
            elif self.active_device.type == "mps":
                # Conservative batch size increase for Apple Silicon
                return int(base_batch_size * 1.2)
            
        except Exception as e:
            logger.warning(f"Failed to calculate optimal batch size: {e}")
        
        return base_batch_size
    
    def cache_model(self, model_name: str, model, device: torch.device = None):
        """Cache optimized model"""
        if not self.config.cache_models:
            return
        
        try:
            cache_key = f"{model_name}_{device or self.active_device}"
            self.model_cache[cache_key] = {
                "model": model,
                "device": device or self.active_device,
                "cached_at": time.time(),
                "access_count": 0
            }
            logger.info(f"Cached model: {cache_key}")
            
        except Exception as e:
            logger.warning(f"Failed to cache model {model_name}: {e}")
    
    def get_cached_model(self, model_name: str, device: torch.device = None):
        """Retrieve cached model"""
        if not self.config.cache_models:
            return None
        
        try:
            cache_key = f"{model_name}_{device or self.active_device}"
            
            if cache_key in self.model_cache:
                cached_item = self.model_cache[cache_key]
                cached_item["access_count"] += 1
                self.performance_stats["cache_hits"] += 1
                logger.debug(f"Cache hit for model: {cache_key}")
                return cached_item["model"]
            
            self.performance_stats["cache_misses"] += 1
            return None
            
        except Exception as e:
            logger.warning(f"Failed to retrieve cached model {model_name}: {e}")
            return None
    
    def clear_cache(self):
        """Clear model cache"""
        try:
            cache_size = len(self.model_cache)
            self.model_cache.clear()
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Cleared model cache ({cache_size} models)")
            
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get comprehensive device information"""
        return {
            "active_device": str(self.active_device),
            "available_devices": [
                {
                    "id": gpu.device_id,
                    "name": gpu.name,
                    "vendor": gpu.vendor.value,
                    "memory_total_mb": gpu.memory_total,
                    "memory_free_mb": gpu.memory_free,
                    "memory_used_mb": gpu.memory_used,
                    "utilization_percent": gpu.utilization,
                    "temperature": gpu.temperature,
                    "power_usage": gpu.power_usage
                }
                for gpu in self.available_devices
            ],
            "config": {
                "prefer_gpu": self.config.prefer_gpu,
                "auto_device_selection": self.config.auto_device_selection,
                "mixed_precision": self.config.mixed_precision,
                "memory_fraction": self.config.memory_fraction,
                "cache_models": self.config.cache_models
            },
            "performance_stats": self.performance_stats.copy(),
            "cache_info": {
                "cached_models": len(self.model_cache),
                "cache_hits": self.performance_stats["cache_hits"],
                "cache_misses": self.performance_stats["cache_misses"],
                "hit_rate": (
                    self.performance_stats["cache_hits"] / 
                    max(1, self.performance_stats["cache_hits"] + self.performance_stats["cache_misses"])
                ) * 100
            }
        }
    
    def benchmark_device(self, device: torch.device = None) -> Dict[str, float]:
        """Benchmark device performance"""
        device = device or self.active_device
        
        try:
            logger.info(f"Benchmarking device: {device}")
            
            # Create test tensors
            sizes = [100, 500, 1000, 2000]
            results = {}
            
            for size in sizes:
                # Matrix multiplication benchmark
                start_time = time.time()
                
                a = torch.randn(size, size, device=device)
                b = torch.randn(size, size, device=device)
                
                for _ in range(10):
                    c = torch.matmul(a, b)
                
                if device.type == "cuda":
                    torch.cuda.synchronize()
                
                end_time = time.time()
                avg_time = (end_time - start_time) / 10 * 1000  # ms
                
                results[f"matmul_{size}x{size}_ms"] = avg_time
            
            logger.info(f"Benchmark completed for {device}")
            return results
            
        except Exception as e:
            logger.error(f"Benchmark failed for {device}: {e}")
            return {}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        memory_info = {
            "system_memory": {
                "total_gb": psutil.virtual_memory().total / (1024**3),
                "available_gb": psutil.virtual_memory().available / (1024**3),
                "used_percent": psutil.virtual_memory().percent
            }
        }
        
        if self.active_device and self.active_device.type == "cuda":
            try:
                device_id = self.active_device.index or 0
                memory_info["gpu_memory"] = {
                    "allocated_mb": torch.cuda.memory_allocated(device_id) / (1024**2),
                    "cached_mb": torch.cuda.memory_reserved(device_id) / (1024**2),
                    "total_mb": torch.cuda.get_device_properties(device_id).total_memory / (1024**2)
                }
            except Exception as e:
                logger.warning(f"Failed to get GPU memory info: {e}")
        
        return memory_info
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up GPU accelerator...")
            
            # Stop monitoring
            self.is_monitoring = False
            if self.memory_monitor and self.memory_monitor.is_alive():
                self.memory_monitor.join(timeout=2)
            
            # Clear cache
            self.clear_cache()
            
            logger.info("GPU accelerator cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global instance
gpu_accelerator = GPUAccelerator()

def get_gpu_accelerator() -> GPUAccelerator:
    """Get the global GPU accelerator instance"""
    return gpu_accelerator