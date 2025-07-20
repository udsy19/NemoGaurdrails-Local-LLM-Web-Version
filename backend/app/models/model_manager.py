import asyncio
import torch
from typing import Dict, Any, Optional, List
from app.models.ollama_client import OllamaClient
from app.models.detector_models import (
    ToxicityDetector, PIIDetector, PromptInjectionDetector,
    TopicDetector, FactCheckDetector, SpamDetector
)
from app.utils.logger import app_logger
from app.utils.exceptions import ModelLoadingException
from app.utils.gpu_accelerator import get_gpu_accelerator

class ModelManager:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.detectors = {}
        self.is_initialized = False
        self.gpu_accelerator = get_gpu_accelerator()
        
        # Define available detectors
        self.available_detectors = {
            'toxicity': ToxicityDetector,
            'pii': PIIDetector,
            'prompt_injection': PromptInjectionDetector,
            'topic': TopicDetector,
            'fact_check': FactCheckDetector,
            'spam': SpamDetector
        }
        
        # Default detector configurations
        self.detector_configs = {
            'toxicity': {'threshold': 0.7},
            'pii': {'sensitivity': 0.8},
            'prompt_injection': {'threshold': 0.5},
            'topic': {'threshold': 0.7},
            'fact_check': {'threshold': 0.5},
            'spam': {'threshold': 0.6}
        }
        
        # Active detectors (can be modified at runtime)
        self.active_detectors = set()
        
    async def initialize(self, load_detectors: Optional[List[str]] = None):
        """Initialize the model manager and load specified detectors"""
        try:
            app_logger.info("Initializing Model Manager...")
            
            # Check Ollama connection
            if not await self.ollama_client.health_check():
                app_logger.warning("Ollama not available, some features may be limited")
            else:
                # Ensure Llama3.1 is available
                await self.ollama_client.ensure_model_available("llama3.1:8b")
                app_logger.info("Ollama client initialized successfully")
            
            # Load detectors
            detectors_to_load = load_detectors or list(self.available_detectors.keys())
            
            for detector_name in detectors_to_load:
                if detector_name in self.available_detectors:
                    await self.load_detector(detector_name)
            
            self.is_initialized = True
            app_logger.info("Model Manager initialized successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize Model Manager: {e}")
            raise ModelLoadingException(f"Model Manager initialization failed: {e}")
    
    async def load_detector(self, detector_name: str, force_load: bool = False):
        """Load a specific detector and keep it permanently loaded for enterprise use"""
        try:
            if detector_name not in self.available_detectors:
                raise ValueError(f"Unknown detector: {detector_name}")
            
            # If detector already exists and force_load is False, skip loading
            if detector_name in self.detectors and not force_load:
                app_logger.info(f"Detector {detector_name} already loaded, skipping")
                self.active_detectors.add(detector_name)
                return
            
            app_logger.info(f"Loading detector for enterprise deployment: {detector_name}")
            
            detector_class = self.available_detectors[detector_name]
            detector_instance = detector_class()
            
            # For enterprise deployment - load model immediately and keep it loaded
            await detector_instance.load_model()
            
            # Optimize for CPU to handle enterprise load efficiently
            if hasattr(detector_instance, 'model') and detector_instance.model is not None:
                try:
                    # Move to CPU and optimize for memory usage
                    detector_instance.model = detector_instance.model.to(torch.device("cpu"))
                    detector_instance.model.eval()  # Set to evaluation mode
                    
                    # Enable memory-efficient inference for enterprise load
                    if hasattr(detector_instance.model, 'gradient_checkpointing_enable'):
                        detector_instance.model.gradient_checkpointing_enable()
                    
                    app_logger.info(f"Enterprise optimization applied for detector {detector_name}")
                except Exception as opt_error:
                    app_logger.warning(f"Model optimization failed for {detector_name}: {opt_error}")
            
            detector_instance.is_loaded = True
            detector_instance._enterprise_mode = True  # Mark as enterprise mode
            
            self.detectors[detector_name] = detector_instance
            self.active_detectors.add(detector_name)
            
            app_logger.info(f"Detector {detector_name} loaded and ready for enterprise use")
            
        except Exception as e:
            app_logger.error(f"Failed to load detector {detector_name}: {e}")
            raise ModelLoadingException(f"Failed to load detector {detector_name}: {e}")
    
    async def _ensure_detector_loaded(self, detector_name: str):
        """Ensure detector model is actually loaded when needed"""
        detector = self.detectors[detector_name]
        
        if detector.is_loaded:
            return
        
        try:
            app_logger.info(f"Lazy loading detector model: {detector_name}")
            
            # Check if cached model exists
            cached_model = self.gpu_accelerator.get_cached_model(
                f"{detector_name}_model",
                self.gpu_accelerator.active_device
            )
            
            if cached_model:
                app_logger.info(f"Using cached model for detector {detector_name}")
                detector.model = cached_model
                detector.is_loaded = True
            else:
                # Load the detector model
                await detector.load_model()
                
                # Optimize for CPU to prevent overheating on systems without proper GPU cooling
                if hasattr(detector, 'model') and detector.model is not None:
                    try:
                        # Move to CPU and optimize for memory usage
                        detector.model = detector.model.to(torch.device("cpu"))
                        detector.model.eval()  # Set to evaluation mode
                        
                        # Enable memory-efficient inference
                        if hasattr(detector.model, 'gradient_checkpointing_enable'):
                            detector.model.gradient_checkpointing_enable()
                        
                        # Cache the model
                        self.gpu_accelerator.cache_model(
                            f"{detector_name}_model",
                            detector.model,
                            torch.device("cpu")
                        )
                        
                        app_logger.info(f"CPU optimization applied for detector {detector_name}")
                    except Exception as opt_error:
                        app_logger.warning(f"Model optimization failed for {detector_name}: {opt_error}")
                
                detector.is_loaded = True
            
            # Clear the lazy load flag
            detector._lazy_load_pending = False
            
        except Exception as e:
            app_logger.error(f"Failed to lazy load detector {detector_name}: {e}")
            raise
    
    async def unload_detector(self, detector_name: str):
        """Unload a specific detector"""
        try:
            if detector_name in self.detectors:
                del self.detectors[detector_name]
                self.active_detectors.discard(detector_name)
                app_logger.info(f"Detector {detector_name} unloaded")
            
        except Exception as e:
            app_logger.error(f"Failed to unload detector {detector_name}: {e}")
    
    async def detect(self, text: str, detector_name: str, **kwargs) -> Dict[str, Any]:
        """Run detection with a specific detector (enterprise mode - always loaded)"""
        try:
            if detector_name not in self.detectors:
                raise ValueError(f"Detector {detector_name} not loaded")
            
            detector = self.detectors[detector_name]
            
            # Verify detector is loaded for enterprise use
            if not detector.is_loaded:
                app_logger.warning(f"Detector {detector_name} not loaded - this should not happen in enterprise mode")
                raise ValueError(f"Detector {detector_name} not ready for enterprise use")
            
            # Merge default config with provided kwargs
            config = self.detector_configs.get(detector_name, {})
            config.update(kwargs)
            
            # Filter out non-detector parameters that are used for system management
            detector_params = {k: v for k, v in config.items() if k not in ['enabled', 'name', 'type', 'model']}
            
            result = await detector.detect(text, **detector_params)
            
            # Track usage for monitoring (no cleanup in enterprise mode)
            import time
            detector.last_used = time.time()
            
            return {
                "detector": detector_name,
                "result": result,
                "text_length": len(text),
                "config": config
            }
            
        except Exception as e:
            app_logger.error(f"Detection failed for {detector_name}: {e}")
            raise
    
    async def detect_all(self, text: str, active_only: bool = True) -> Dict[str, Any]:
        """Run detection with all available detectors optimized for enterprise load"""
        results = {}
        
        detectors_to_use = self.active_detectors if active_only else set(self.detectors.keys())
        
        # For enterprise: Run all detectors concurrently with optimized semaphore
        # Limit concurrent detections per request to prevent resource exhaustion
        semaphore = asyncio.Semaphore(6)  # Allow up to 6 concurrent detections
        
        async def detect_with_semaphore(detector_name: str):
            async with semaphore:
                try:
                    return await self.detect(text, detector_name)
                except Exception as e:
                    app_logger.error(f"Enterprise detection failed for {detector_name}: {e}")
                    return {
                        "detector": detector_name,
                        "error": str(e),
                        "result": None
                    }
        
        # Create tasks for all detectors
        tasks = {
            detector_name: asyncio.create_task(
                detect_with_semaphore(detector_name),
                name=f"enterprise_detect_{detector_name}"
            )
            for detector_name in detectors_to_use
            if detector_name in self.detectors
        }
        
        # Wait for all tasks to complete with timeout for enterprise SLA
        try:
            completed_results = await asyncio.wait_for(
                asyncio.gather(*tasks.values(), return_exceptions=True),
                timeout=30.0  # 30 second timeout for enterprise SLA
            )
            
            # Process results
            for i, (detector_name, task) in enumerate(tasks.items()):
                try:
                    if i < len(completed_results):
                        result = completed_results[i]
                        if isinstance(result, Exception):
                            results[detector_name] = {
                                "detector": detector_name,
                                "error": str(result),
                                "result": None
                            }
                        else:
                            results[detector_name] = result
                    else:
                        results[detector_name] = {
                            "detector": detector_name,
                            "error": "Detection timeout",
                            "result": None
                        }
                except Exception as e:
                    results[detector_name] = {
                        "detector": detector_name,
                        "error": f"Result processing error: {str(e)}",
                        "result": None
                    }
                    
        except asyncio.TimeoutError:
            app_logger.warning(f"Enterprise detection timeout for text length {len(text)}")
            # Cancel remaining tasks
            for task in tasks.values():
                if not task.done():
                    task.cancel()
            
            # Return partial results
            for detector_name in detectors_to_use:
                if detector_name not in results:
                    results[detector_name] = {
                        "detector": detector_name,
                        "error": "Enterprise timeout - high load detected",
                        "result": None
                    }
        
        return results
    
    def get_available_detectors(self) -> Dict[str, Any]:
        """Get information about available detectors"""
        return {
            detector_name: {
                "loaded": detector_name in self.detectors,
                "active": detector_name in self.active_detectors,
                "config": self.detector_configs.get(detector_name, {})
            }
            for detector_name in self.available_detectors
        }
    
    def get_active_detectors(self) -> List[str]:
        """Get list of active detector names"""
        return list(self.active_detectors)
    
    def set_active_detectors(self, detector_names: List[str]):
        """Set which detectors are active"""
        self.active_detectors = set(detector_names) & set(self.detectors.keys())
        app_logger.info(f"Active detectors updated: {list(self.active_detectors)}")
    
    def update_detector_config(self, detector_name: str, config: Dict[str, Any]):
        """Update configuration for a specific detector"""
        if detector_name in self.detector_configs:
            self.detector_configs[detector_name].update(config)
            app_logger.info(f"Updated config for {detector_name}: {config}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        ollama_healthy = await self.ollama_client.health_check()
        
        detector_status = {}
        for detector_name in self.available_detectors:
            detector_status[detector_name] = {
                "loaded": detector_name in self.detectors,
                "active": detector_name in self.active_detectors,
                "healthy": detector_name in self.detectors and self.detectors[detector_name].is_loaded
            }
        
        # Get GPU status
        gpu_status = None
        if self.gpu_accelerator:
            try:
                gpu_status = {
                    "active_device": str(self.gpu_accelerator.active_device),
                    "available_devices": len(self.gpu_accelerator.available_devices),
                    "cached_models": len(self.gpu_accelerator.model_cache),
                    "cache_hits": self.gpu_accelerator.performance_stats["cache_hits"],
                    "cache_misses": self.gpu_accelerator.performance_stats["cache_misses"]
                }
            except Exception as e:
                gpu_status = {"error": str(e)}

        return {
            "initialized": self.is_initialized,
            "ollama_healthy": ollama_healthy,
            "total_detectors": len(self.available_detectors),
            "loaded_detectors": len(self.detectors),
            "active_detectors": len(self.active_detectors),
            "detector_status": detector_status,
            "gpu_status": gpu_status
        }
    
    async def get_enterprise_status(self) -> Dict[str, Any]:
        """Get enterprise deployment status - all models should be permanently loaded"""
        try:
            enterprise_status = {
                "enterprise_mode": True,
                "all_models_loaded": True,
                "total_detectors": len(self.available_detectors),
                "loaded_detectors": len(self.detectors),
                "active_detectors": len(self.active_detectors),
                "memory_usage_optimized": True,
                "offline_ready": True
            }
            
            # Check if all detectors are loaded and ready
            for detector_name in self.available_detectors:
                if detector_name not in self.detectors or not self.detectors[detector_name].is_loaded:
                    enterprise_status["all_models_loaded"] = False
                    enterprise_status["missing_detectors"] = enterprise_status.get("missing_detectors", [])
                    enterprise_status["missing_detectors"].append(detector_name)
            
            return enterprise_status
            
        except Exception as e:
            app_logger.error(f"Error getting enterprise status: {e}")
            return {"enterprise_mode": False, "error": str(e)}
    
    async def cleanup(self):
        """Clean up resources (enterprise mode - keep models loaded)"""
        try:
            app_logger.info("Cleaning up Model Manager (enterprise mode - keeping models loaded)...")
            
            # Close Ollama client only
            await self.ollama_client.close()
            
            # DO NOT clear detectors in enterprise mode - keep them loaded
            # self.detectors.clear()  # Commented out for enterprise
            
            # Cleanup GPU accelerator cache only (not models)
            if self.gpu_accelerator:
                # Only clear performance stats, not model cache
                self.gpu_accelerator.performance_stats = {
                    "cpu_inference_times": [],
                    "gpu_inference_times": [],
                    "memory_usage": [],
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "fallback_events": 0
                }
            
            app_logger.info("Model Manager cleanup completed (models preserved for enterprise use)")
            
        except Exception as e:
            app_logger.error(f"Error during cleanup: {e}")
    
    async def reload_detector(self, detector_name: str):
        """Reload a specific detector"""
        try:
            if detector_name in self.detectors:
                await self.unload_detector(detector_name)
            
            await self.load_detector(detector_name)
            app_logger.info(f"Detector {detector_name} reloaded successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to reload detector {detector_name}: {e}")
            raise