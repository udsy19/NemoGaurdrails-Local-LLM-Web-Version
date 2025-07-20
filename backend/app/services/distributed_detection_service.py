"""
Distributed Detection Service
Integrates the distributed processing system with AI safety detection
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass

from app.utils.distributed_processor import get_distributed_processor, Priority
from app.services.detection_service import DetectionService
from app.models.model_manager import ModelManager
from app.utils.logger import app_logger

logger = logging.getLogger(__name__)

@dataclass
class DistributedDetectionConfig:
    """Configuration for distributed detection"""
    enable_parallel_detection: bool = True
    max_concurrent_detections: int = 10
    batch_size: int = 5
    priority_mapping: Dict[str, Priority] = None
    timeout_per_detector: float = 30.0
    enable_result_caching: bool = True
    cache_ttl: int = 300  # 5 minutes

class DistributedDetectionService:
    """
    Enhanced detection service with distributed processing capabilities
    """
    
    def __init__(self, 
                 detection_service: DetectionService, 
                 model_manager: ModelManager,
                 config: DistributedDetectionConfig = None):
        self.detection_service = detection_service
        self.model_manager = model_manager
        self.config = config or DistributedDetectionConfig()
        self.distributed_processor = get_distributed_processor()
        
        # Result cache for distributed detection
        self.result_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        
        # Performance metrics
        self.metrics = {
            "distributed_detections": 0,
            "parallel_detections": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_detection_time": 0.0,
            "detection_times": [],
            "detector_performance": {},
            "batch_processing_stats": {
                "batches_processed": 0,
                "total_items": 0,
                "avg_batch_time": 0.0
            }
        }
        
        # Initialize default priority mapping
        if self.config.priority_mapping is None:
            self.config.priority_mapping = {
                "toxicity": Priority.HIGH,
                "pii": Priority.CRITICAL,
                "prompt_injection": Priority.HIGH,
                "spam": Priority.NORMAL,
                "topic": Priority.NORMAL,
                "fact_check": Priority.LOW
            }
        
        self._register_detection_functions()
        app_logger.info("Distributed Detection Service initialized")
    
    def _register_detection_functions(self):
        """Register detection functions with the distributed processor"""
        
        def detect_toxicity(text: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
            """Distributed toxicity detection function"""
            try:
                if 'toxicity' not in self.model_manager.detectors:
                    return {"error": "Toxicity detector not loaded", "detected": False}
                
                detector = self.model_manager.detectors['toxicity']
                result = detector.detect(text, config or {})
                return {
                    "detector": "toxicity",
                    "text_length": len(text),
                    "result": result,
                    "detected": result.get("detected", False),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time", 0.0)
                }
            except Exception as e:
                logger.error(f"Distributed toxicity detection failed: {e}")
                return {"error": str(e), "detected": False}
        
        def detect_pii(text: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
            """Distributed PII detection function"""
            try:
                if 'pii' not in self.model_manager.detectors:
                    return {"error": "PII detector not loaded", "detected": False}
                
                detector = self.model_manager.detectors['pii']
                result = detector.detect(text, config or {})
                return {
                    "detector": "pii",
                    "text_length": len(text),
                    "result": result,
                    "detected": result.get("detected", False),
                    "entities": result.get("entities", []),
                    "processing_time": result.get("processing_time", 0.0)
                }
            except Exception as e:
                logger.error(f"Distributed PII detection failed: {e}")
                return {"error": str(e), "detected": False}
        
        def detect_prompt_injection(text: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
            """Distributed prompt injection detection function"""
            try:
                if 'prompt_injection' not in self.model_manager.detectors:
                    return {"error": "Prompt injection detector not loaded", "detected": False}
                
                detector = self.model_manager.detectors['prompt_injection']
                result = detector.detect(text, config or {})
                return {
                    "detector": "prompt_injection",
                    "text_length": len(text),
                    "result": result,
                    "detected": result.get("detected", False),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time", 0.0)
                }
            except Exception as e:
                logger.error(f"Distributed prompt injection detection failed: {e}")
                return {"error": str(e), "detected": False}
        
        def detect_spam(text: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
            """Distributed spam detection function"""
            try:
                if 'spam' not in self.model_manager.detectors:
                    return {"error": "Spam detector not loaded", "detected": False}
                
                detector = self.model_manager.detectors['spam']
                result = detector.detect(text, config or {})
                return {
                    "detector": "spam",
                    "text_length": len(text),
                    "result": result,
                    "detected": result.get("detected", False),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time", 0.0)
                }
            except Exception as e:
                logger.error(f"Distributed spam detection failed: {e}")
                return {"error": str(e), "detected": False}
        
        def detect_topic(text: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
            """Distributed topic detection function"""
            try:
                if 'topic' not in self.model_manager.detectors:
                    return {"error": "Topic detector not loaded", "detected": False}
                
                detector = self.model_manager.detectors['topic']
                result = detector.detect(text, config or {})
                return {
                    "detector": "topic",
                    "text_length": len(text),
                    "result": result,
                    "detected": result.get("detected", False),
                    "topic": result.get("topic", "unknown"),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time", 0.0)
                }
            except Exception as e:
                logger.error(f"Distributed topic detection failed: {e}")
                return {"error": str(e), "detected": False}
        
        def detect_fact_check(text: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
            """Distributed fact checking function"""
            try:
                if 'fact_check' not in self.model_manager.detectors:
                    return {"error": "Fact check detector not loaded", "detected": False}
                
                detector = self.model_manager.detectors['fact_check']
                result = detector.detect(text, config or {})
                return {
                    "detector": "fact_check",
                    "text_length": len(text),
                    "result": result,
                    "detected": result.get("detected", False),
                    "factual": result.get("factual", True),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time", 0.0)
                }
            except Exception as e:
                logger.error(f"Distributed fact check detection failed: {e}")
                return {"error": str(e), "detected": False}
        
        # Register functions with distributed processor
        self.distributed_processor.register_function("detect_toxicity", detect_toxicity)
        self.distributed_processor.register_function("detect_pii", detect_pii)
        self.distributed_processor.register_function("detect_prompt_injection", detect_prompt_injection)
        self.distributed_processor.register_function("detect_spam", detect_spam)
        self.distributed_processor.register_function("detect_topic", detect_topic)
        self.distributed_processor.register_function("detect_fact_check", detect_fact_check)
        
        app_logger.info("Registered 6 detection functions with distributed processor")
    
    def _get_cache_key(self, text: str, detectors: List[str], configs: Dict[str, Dict]) -> str:
        """Generate cache key for detection results"""
        import hashlib
        
        key_data = f"{text}:{sorted(detectors)}:{str(sorted(configs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached detection result if available and not expired"""
        if not self.config.enable_result_caching:
            return None
        
        if cache_key in self.result_cache:
            timestamp, result = self.result_cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                self.metrics["cache_hits"] += 1
                return result
            else:
                # Remove expired cache entry
                del self.result_cache[cache_key]
        
        self.metrics["cache_misses"] += 1
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache detection result"""
        if not self.config.enable_result_caching:
            return
        
        self.result_cache[cache_key] = (time.time(), result)
        
        # Clean up old cache entries (keep only last 1000 entries)
        if len(self.result_cache) > 1000:
            # Remove oldest 100 entries
            oldest_keys = sorted(self.result_cache.keys(), 
                               key=lambda k: self.result_cache[k][0])[:100]
            for key in oldest_keys:
                del self.result_cache[key]
    
    async def detect_distributed(
        self, 
        text: str, 
        detectors: Optional[List[str]] = None,
        configs: Optional[Dict[str, Dict[str, Any]]] = None,
        use_parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Perform distributed detection across multiple detectors
        """
        start_time = time.time()
        
        try:
            # Get active detectors if not specified
            if detectors is None:
                detectors = list(self.model_manager.active_detectors)
            
            if not detectors:
                return {
                    "success": False,
                    "error": "No active detectors available",
                    "results": {},
                    "processing_time": time.time() - start_time
                }
            
            # Prepare configs
            if configs is None:
                configs = {}
            
            # Check cache
            cache_key = self._get_cache_key(text, detectors, configs)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return {
                    **cached_result,
                    "from_cache": True,
                    "processing_time": time.time() - start_time
                }
            
            # Ensure distributed processor is running
            if not self.distributed_processor.is_running:
                app_logger.warning("Distributed processor not running, falling back to sequential detection")
                return await self._fallback_detection(text, detectors, configs)
            
            # Submit tasks for distributed processing
            task_ids = []
            detector_task_map = {}
            
            for detector_name in detectors:
                if detector_name in self.model_manager.detectors:
                    priority = self.config.priority_mapping.get(detector_name, Priority.NORMAL)
                    config = configs.get(detector_name, {})
                    
                    try:
                        task_id = await self.distributed_processor.submit_task(
                            f"detect_{detector_name}",
                            text,
                            config,
                            priority=priority,
                            timeout=self.config.timeout_per_detector,
                            metadata={
                                "detector": detector_name,
                                "text_length": len(text),
                                "submitted_at": time.time()
                            }
                        )
                        task_ids.append(task_id)
                        detector_task_map[task_id] = detector_name
                        
                    except Exception as e:
                        logger.error(f"Failed to submit task for {detector_name}: {e}")
            
            if not task_ids:
                return {
                    "success": False,
                    "error": "No detection tasks could be submitted",
                    "results": {},
                    "processing_time": time.time() - start_time
                }
            
            # Wait for results with timeout
            results = {}
            timeout = max(self.config.timeout_per_detector * 2, 60.0)  # Extra buffer
            end_time = time.time() + timeout
            
            while task_ids and time.time() < end_time:
                for task_id in list(task_ids):
                    task = await self.distributed_processor.get_task_status(task_id)
                    
                    if task and task.status.value in ["completed", "failed", "cancelled"]:
                        detector_name = detector_task_map[task_id]
                        
                        if task.status.value == "completed" and task.result:
                            results[detector_name] = task.result
                        else:
                            results[detector_name] = {
                                "error": task.error or f"Task {task.status.value}",
                                "detected": False,
                                "detector": detector_name
                            }
                        
                        task_ids.remove(task_id)
                
                if task_ids:
                    await asyncio.sleep(0.1)
            
            # Handle any remaining incomplete tasks
            for task_id in task_ids:
                detector_name = detector_task_map[task_id]
                results[detector_name] = {
                    "error": "Task timeout",
                    "detected": False,
                    "detector": detector_name
                }
                
                # Cancel the task
                await self.distributed_processor.cancel_task(task_id)
            
            # Aggregate results
            final_result = {
                "success": True,
                "results": results,
                "summary": self._create_detection_summary(results),
                "processing_time": time.time() - start_time,
                "distributed": True,
                "detectors_used": len(results),
                "metadata": {
                    "text_length": len(text),
                    "cache_key": cache_key,
                    "parallel_processing": use_parallel
                }
            }
            
            # Cache the result
            self._cache_result(cache_key, final_result)
            
            # Update metrics
            self.metrics["distributed_detections"] += 1
            if use_parallel:
                self.metrics["parallel_detections"] += 1
            
            detection_time = time.time() - start_time
            self.metrics["detection_times"].append(detection_time)
            if len(self.metrics["detection_times"]) > 100:
                self.metrics["detection_times"] = self.metrics["detection_times"][-100:]
            
            self.metrics["avg_detection_time"] = sum(self.metrics["detection_times"]) / len(self.metrics["detection_times"])
            
            return final_result
            
        except Exception as e:
            logger.error(f"Distributed detection failed: {e}")
            
            # Fallback to sequential detection
            app_logger.warning("Falling back to sequential detection due to error")
            return await self._fallback_detection(text, detectors, configs)
    
    async def _fallback_detection(
        self, 
        text: str, 
        detectors: List[str], 
        configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback to regular sequential detection"""
        try:
            start_time = time.time()
            
            # Use the original detection service
            results = await self.model_manager.detect_all(text, active_only=False)
            
            # Filter results to requested detectors
            if detectors:
                filtered_results = {k: v for k, v in results.items() if k in detectors}
            else:
                filtered_results = results
            
            return {
                "success": True,
                "results": filtered_results,
                "summary": self._create_detection_summary(filtered_results),
                "processing_time": time.time() - start_time,
                "distributed": False,
                "fallback": True,
                "detectors_used": len(filtered_results)
            }
            
        except Exception as e:
            logger.error(f"Fallback detection also failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": {},
                "processing_time": time.time() - start_time,
                "fallback": True
            }
    
    def _create_detection_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of detection results"""
        summary = {
            "total_detectors": len(results),
            "detections_found": 0,
            "errors": 0,
            "highest_confidence": 0.0,
            "detected_by": [],
            "error_detectors": [],
            "processing_times": {}
        }
        
        for detector_name, result in results.items():
            if isinstance(result, dict):
                if result.get("error"):
                    summary["errors"] += 1
                    summary["error_detectors"].append(detector_name)
                elif result.get("detected", False):
                    summary["detections_found"] += 1
                    summary["detected_by"].append(detector_name)
                    
                    confidence = result.get("confidence", 0.0)
                    if confidence > summary["highest_confidence"]:
                        summary["highest_confidence"] = confidence
                
                processing_time = result.get("processing_time", 0.0)
                if processing_time > 0:
                    summary["processing_times"][detector_name] = processing_time
        
        summary["overall_threat_detected"] = summary["detections_found"] > 0
        summary["reliability"] = (summary["total_detectors"] - summary["errors"]) / max(1, summary["total_detectors"]) * 100
        
        return summary
    
    async def detect_batch(
        self, 
        texts: List[str], 
        detectors: Optional[List[str]] = None,
        configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple texts in batch using distributed processing
        """
        start_time = time.time()
        
        try:
            if not texts:
                return {
                    "success": True,
                    "results": [],
                    "processing_time": 0,
                    "batch_size": 0
                }
            
            # Process in chunks
            batch_size = min(self.config.batch_size, self.config.max_concurrent_detections)
            results = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Process batch concurrently
                batch_tasks = [
                    self.detect_distributed(text, detectors, configs)
                    for text in batch
                ]
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Handle exceptions
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        results.append({
                            "success": False,
                            "error": str(result),
                            "text_index": i + j,
                            "text": batch[j][:100] + "..." if len(batch[j]) > 100 else batch[j]
                        })
                    else:
                        result["text_index"] = i + j
                        results.append(result)
            
            # Update batch processing metrics
            self.metrics["batch_processing_stats"]["batches_processed"] += 1
            self.metrics["batch_processing_stats"]["total_items"] += len(texts)
            
            batch_time = time.time() - start_time
            current_avg = self.metrics["batch_processing_stats"]["avg_batch_time"]
            batches_count = self.metrics["batch_processing_stats"]["batches_processed"]
            self.metrics["batch_processing_stats"]["avg_batch_time"] = (
                (current_avg * (batches_count - 1) + batch_time) / batches_count
            )
            
            return {
                "success": True,
                "results": results,
                "processing_time": batch_time,
                "batch_size": len(texts),
                "successful_detections": len([r for r in results if r.get("success", False)]),
                "failed_detections": len([r for r in results if not r.get("success", False)]),
                "distributed": True
            }
            
        except Exception as e:
            logger.error(f"Batch detection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "batch_size": len(texts) if texts else 0
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for distributed detection"""
        processor_status = await self.distributed_processor.get_system_status()
        
        return {
            "distributed_detection_metrics": self.metrics.copy(),
            "distributed_processor_metrics": processor_status["metrics"],
            "cache_stats": {
                "cache_size": len(self.result_cache),
                "cache_hit_rate": (
                    self.metrics["cache_hits"] / 
                    max(1, self.metrics["cache_hits"] + self.metrics["cache_misses"])
                ) * 100,
                "cache_enabled": self.config.enable_result_caching
            },
            "configuration": {
                "parallel_detection_enabled": self.config.enable_parallel_detection,
                "max_concurrent_detections": self.config.max_concurrent_detections,
                "batch_size": self.config.batch_size,
                "cache_ttl": self.config.cache_ttl,
                "timeout_per_detector": self.config.timeout_per_detector
            },
            "system_status": {
                "distributed_processor_running": processor_status["is_running"],
                "workers_available": processor_status["workers"]["total"],
                "active_workers": processor_status["workers"]["active"],
                "queue_size": processor_status["metrics"]["queue_size"]
            }
        }
    
    def clear_cache(self):
        """Clear the detection result cache"""
        cache_size = len(self.result_cache)
        self.result_cache.clear()
        app_logger.info(f"Cleared detection cache ({cache_size} entries)")
        return cache_size

# Global instance
_distributed_detection_service: Optional[DistributedDetectionService] = None

def get_distributed_detection_service() -> Optional[DistributedDetectionService]:
    """Get the global distributed detection service instance"""
    return _distributed_detection_service

def initialize_distributed_detection_service(
    detection_service: DetectionService, 
    model_manager: ModelManager,
    config: DistributedDetectionConfig = None
) -> DistributedDetectionService:
    """Initialize the distributed detection service"""
    global _distributed_detection_service
    _distributed_detection_service = DistributedDetectionService(
        detection_service, model_manager, config
    )
    return _distributed_detection_service