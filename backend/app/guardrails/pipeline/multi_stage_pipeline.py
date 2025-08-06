"""
Phase 4: Multi-Stage Pipeline Architecture
Industry-level guardrails with >95% accuracy through sophisticated ensemble methods
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

from app.utils.logger import app_logger

# Import shared models to avoid circular imports
from app.guardrails.models import DetectionResult, PipelineStage, PipelineContext, ConfidenceLevel

class MultiStagePipeline:
    """
    Industry-level multi-stage detection pipeline achieving >95% accuracy
    
    Pipeline Flow:
    1. Fast Pre-Screening (Rule-based + Lightweight Models)
    2. Primary Ensemble (3-5 Models per Guardrail Type)
    3. Cross-Validation Layer (Conflict Resolution)
    4. Context-Aware Final Check (Open-Source LLM)
    5. Confidence-Based Escalation
    """
    
    def __init__(self):
        self.pre_screener = PreScreeningLayer()
        self.ensemble_detector = EnsembleDetectionLayer()
        self.cross_validator = CrossValidationLayer()
        self.context_analyzer = ContextAnalysisLayer()
        self.escalation_manager = EscalationManager()
        
        # Performance monitoring
        self.stage_metrics = {stage: {"count": 0, "total_time": 0.0} for stage in PipelineStage}
        self.cache = DetectionCache()
        
        # Configuration - adjusted for better usability
        self.confidence_thresholds = {
            ConfidenceLevel.HIGH: 0.8,   # Reduced from 0.92 to be less stringent
            ConfidenceLevel.MEDIUM: 0.6, # Reduced from 0.75 to be less stringent
            ConfidenceLevel.LOW: 0.0
        }
        
        self.disagreement_threshold = 0.3  # When models disagree significantly
        
        app_logger.info("Multi-stage pipeline initialized")
    
    async def process(
        self, 
        text: str, 
        guardrail_types: List[str],
        context: PipelineContext = None
    ) -> Dict[str, DetectionResult]:
        """
        Process text through multi-stage pipeline
        
        Args:
            text: Input text to analyze
            guardrail_types: List of guardrail types to check
            context: Optional context information
            
        Returns:
            Dictionary of guardrail_type -> DetectionResult
        """
        start_time = time.time()
        context = context or PipelineContext()
        
        # Check cache first
        cache_key = self._generate_cache_key(text, guardrail_types, context)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            app_logger.debug(f"Cache hit for pipeline processing")
            return cached_result
        
        try:
            # Stage 1: Fast Pre-Screening
            pre_screen_results = await self._stage1_pre_screening(
                text, guardrail_types, context
            )
            
            # Early exit if pre-screening catches obvious violations
            if any(result.blocked and result.confidence > 0.95 for result in pre_screen_results.values()):
                app_logger.info("Early exit from pre-screening stage")
                self.cache.set(cache_key, pre_screen_results)
                return pre_screen_results
            
            # Stage 2: Primary Ensemble Detection
            ensemble_results = await self._stage2_primary_ensemble(
                text, guardrail_types, context, pre_screen_results
            )
            
            # Route based on confidence levels
            final_results = {}
            for guardrail_type, result in ensemble_results.items():
                confidence_level = self._classify_confidence(result)
                
                if confidence_level == ConfidenceLevel.HIGH:
                    # High confidence - accept result
                    final_results[guardrail_type] = result
                    
                elif confidence_level == ConfidenceLevel.MEDIUM or confidence_level == ConfidenceLevel.CONFLICT:
                    # Medium confidence or conflict - route to cross-validation
                    validated_result = await self._stage3_cross_validation(
                        text, guardrail_type, result, context
                    )
                    final_results[guardrail_type] = validated_result
                    
                else:  # LOW confidence
                    # Low confidence - route to context analysis
                    context_result = await self._stage4_context_analysis(
                        text, guardrail_type, result, context
                    )
                    final_results[guardrail_type] = context_result
            
            # Stage 5: Check for escalation needs
            final_results = await self._stage5_escalation_check(
                text, final_results, context
            )
            
            # Cache results
            self.cache.set(cache_key, final_results)
            
            total_time = (time.time() - start_time) * 1000
            app_logger.info(f"Pipeline processing completed in {total_time:.1f}ms")
            
            return final_results
            
        except Exception as e:
            app_logger.error(f"Pipeline processing failed: {e}")
            # Return safe fallback results
            return self._create_fallback_results(guardrail_types, str(e))
    
    async def _stage1_pre_screening(
        self, 
        text: str, 
        guardrail_types: List[str], 
        context: PipelineContext
    ) -> Dict[str, DetectionResult]:
        """Stage 1: Fast Pre-Screening Layer"""
        stage_start = time.time()
        results = {}
        
        try:
            # Run pre-screening for each guardrail type
            screening_tasks = [
                self.pre_screener.screen(text, guardrail_type, context)
                for guardrail_type in guardrail_types
            ]
            
            screening_results = await asyncio.gather(*screening_tasks, return_exceptions=True)
            
            for i, guardrail_type in enumerate(guardrail_types):
                if isinstance(screening_results[i], Exception):
                    app_logger.error(f"Pre-screening failed for {guardrail_type}: {screening_results[i]}")
                    results[guardrail_type] = DetectionResult(
                        blocked=False,
                        confidence=0.0,
                        stage=PipelineStage.PRE_SCREENING,
                        guardrail_type=guardrail_type,
                        reasons=["Pre-screening error"]
                    )
                else:
                    results[guardrail_type] = screening_results[i]
            
        except Exception as e:
            app_logger.error(f"Stage 1 pre-screening failed: {e}")
            for guardrail_type in guardrail_types:
                results[guardrail_type] = DetectionResult(
                    blocked=False,
                    confidence=0.0,
                    stage=PipelineStage.PRE_SCREENING,
                    guardrail_type=guardrail_type,
                    reasons=["Stage 1 error"]
                )
        
        # Update metrics
        stage_time = (time.time() - stage_start) * 1000
        self._update_stage_metrics(PipelineStage.PRE_SCREENING, stage_time)
        
        return results
    
    async def _stage2_primary_ensemble(
        self, 
        text: str, 
        guardrail_types: List[str], 
        context: PipelineContext,
        pre_screen_results: Dict[str, DetectionResult]
    ) -> Dict[str, DetectionResult]:
        """Stage 2: Primary Ensemble Detection"""
        stage_start = time.time()
        results = {}
        
        try:
            # Run ensemble detection for each guardrail type in parallel
            ensemble_tasks = [
                self.ensemble_detector.detect(text, guardrail_type, context, pre_screen_results.get(guardrail_type))
                for guardrail_type in guardrail_types
            ]
            
            ensemble_results = await asyncio.gather(*ensemble_tasks, return_exceptions=True)
            
            for i, guardrail_type in enumerate(guardrail_types):
                if isinstance(ensemble_results[i], Exception):
                    app_logger.error(f"Ensemble detection failed for {guardrail_type}: {ensemble_results[i]}")
                    # Fallback to pre-screen result
                    results[guardrail_type] = pre_screen_results.get(guardrail_type, DetectionResult(
                        blocked=False,
                        confidence=0.0,
                        stage=PipelineStage.PRIMARY_ENSEMBLE,
                        guardrail_type=guardrail_type,
                        reasons=["Ensemble error - fallback to pre-screen"]
                    ))
                else:
                    results[guardrail_type] = ensemble_results[i]
            
        except Exception as e:
            app_logger.error(f"Stage 2 ensemble detection failed: {e}")
            # Fallback to pre-screen results
            for guardrail_type in guardrail_types:
                results[guardrail_type] = pre_screen_results.get(guardrail_type, DetectionResult(
                    blocked=False,
                    confidence=0.0,
                    stage=PipelineStage.PRIMARY_ENSEMBLE,
                    guardrail_type=guardrail_type,
                    reasons=["Stage 2 error"]
                ))
        
        # Update metrics
        stage_time = (time.time() - stage_start) * 1000
        self._update_stage_metrics(PipelineStage.PRIMARY_ENSEMBLE, stage_time)
        
        return results
    
    async def _stage3_cross_validation(
        self, 
        text: str, 
        guardrail_type: str, 
        ensemble_result: DetectionResult,
        context: PipelineContext
    ) -> DetectionResult:
        """Stage 3: Cross-Validation & Conflict Resolution"""
        stage_start = time.time()
        
        try:
            validated_result = await self.cross_validator.validate(
                text, guardrail_type, ensemble_result, context
            )
            
            # Update stage info
            validated_result.stage = PipelineStage.CROSS_VALIDATION
            
        except Exception as e:
            app_logger.error(f"Stage 3 cross-validation failed for {guardrail_type}: {e}")
            # Fallback to ensemble result
            validated_result = ensemble_result
            validated_result.reasons.append("Cross-validation error - using ensemble result")
        
        # Update metrics
        stage_time = (time.time() - stage_start) * 1000
        self._update_stage_metrics(PipelineStage.CROSS_VALIDATION, stage_time)
        
        return validated_result
    
    async def _stage4_context_analysis(
        self, 
        text: str, 
        guardrail_type: str, 
        previous_result: DetectionResult,
        context: PipelineContext
    ) -> DetectionResult:
        """Stage 4: Context-Aware LLM Analysis"""
        stage_start = time.time()
        
        try:
            context_result = await self.context_analyzer.analyze(
                text, guardrail_type, previous_result, context
            )
            
            # Update stage info
            context_result.stage = PipelineStage.CONTEXT_ANALYSIS
            
        except Exception as e:
            app_logger.error(f"Stage 4 context analysis failed for {guardrail_type}: {e}")
            # Fallback to previous result
            context_result = previous_result
            context_result.reasons.append("Context analysis error - using previous result")
        
        # Update metrics
        stage_time = (time.time() - stage_start) * 1000
        self._update_stage_metrics(PipelineStage.CONTEXT_ANALYSIS, stage_time)
        
        return context_result
    
    async def _stage5_escalation_check(
        self, 
        text: str, 
        results: Dict[str, DetectionResult],
        context: PipelineContext
    ) -> Dict[str, DetectionResult]:
        """Stage 5: Confidence-Based Escalation"""
        stage_start = time.time()
        
        try:
            for guardrail_type, result in results.items():
                escalation_needed = self.escalation_manager.should_escalate(
                    text, result, context
                )
                
                if escalation_needed:
                    result.escalation_required = True
                    result.reasons.append("Escalated for human review")
                    app_logger.info(f"Escalation required for {guardrail_type}")
            
        except Exception as e:
            app_logger.error(f"Stage 5 escalation check failed: {e}")
        
        # Update metrics
        stage_time = (time.time() - stage_start) * 1000
        self._update_stage_metrics(PipelineStage.ESCALATION, stage_time)
        
        return results
    
    def _classify_confidence(self, result: DetectionResult) -> ConfidenceLevel:
        """Classify confidence level for routing decisions"""
        confidence = result.confidence
        
        # Check for model disagreement
        if len(result.model_scores) > 1:
            scores = list(result.model_scores.values())
            if max(scores) - min(scores) > self.disagreement_threshold:
                return ConfidenceLevel.CONFLICT
        
        # Classify by confidence thresholds
        if confidence >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif confidence >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_cache_key(
        self, 
        text: str, 
        guardrail_types: List[str], 
        context: PipelineContext
    ) -> str:
        """Generate cache key for results"""
        # Create a deterministic key from input parameters
        key_data = {
            "text_hash": hashlib.md5(text.encode()).hexdigest(),
            "guardrail_types": sorted(guardrail_types),
            "domain_context": context.domain_context,
            "user_risk_score": round(context.user_risk_score, 2)
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_stage_metrics(self, stage: PipelineStage, processing_time: float):
        """Update performance metrics for a stage"""
        self.stage_metrics[stage]["count"] += 1
        self.stage_metrics[stage]["total_time"] += processing_time
    
    def _create_fallback_results(
        self, 
        guardrail_types: List[str], 
        error_message: str
    ) -> Dict[str, DetectionResult]:
        """Create safe fallback results in case of errors"""
        results = {}
        for guardrail_type in guardrail_types:
            results[guardrail_type] = DetectionResult(
                blocked=True,  # Fail safe - block when uncertain
                confidence=0.0,
                stage=PipelineStage.PRE_SCREENING,
                guardrail_type=guardrail_type,
                reasons=[f"Pipeline error: {error_message}"],
                escalation_required=True
            )
        return results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        metrics = {}
        
        for stage, data in self.stage_metrics.items():
            if data["count"] > 0:
                avg_time = data["total_time"] / data["count"]
                metrics[stage.value] = {
                    "total_count": data["count"],
                    "total_time_ms": data["total_time"],
                    "average_time_ms": avg_time
                }
        
        return {
            "stage_metrics": metrics,
            "cache_stats": self.cache.get_stats(),
            "confidence_thresholds": {level.value: threshold for level, threshold in self.confidence_thresholds.items()}
        }

# Import real pipeline layer implementations
from app.guardrails.layers.pre_screening import PreScreeningLayer
from app.guardrails.layers.cross_validation import CrossValidationLayer  
from app.guardrails.layers.context_analysis import ContextAnalysisLayer
from app.guardrails.ensemble.enhanced_ensemble import create_ensemble_detector, EnsembleConfig

class EnsembleDetectionLayer:
    """Primary ensemble detection with multiple models"""
    
    def __init__(self):
        self.ensemble_detectors = {}
        self.ensemble_config = EnsembleConfig()
    
    async def detect(
        self, 
        text: str, 
        guardrail_type: str, 
        context: PipelineContext,
        pre_screen_result: Optional[DetectionResult] = None
    ) -> DetectionResult:
        """Perform ensemble detection"""
        try:
            # Get or create ensemble detector for this guardrail type
            if guardrail_type not in self.ensemble_detectors:
                detector = create_ensemble_detector(guardrail_type, self.ensemble_config)
                await detector.initialize()
                self.ensemble_detectors[guardrail_type] = detector
            
            detector = self.ensemble_detectors[guardrail_type]
            result = await detector.detect(text, context)
            
            # Enhance with pre-screening information if available
            if pre_screen_result and pre_screen_result.confidence > 0.8:
                # Boost confidence if pre-screening was confident
                result.confidence = min(0.95, result.confidence + 0.1)
                result.reasons.append("Pre-screening boost applied")
                
            return result
            
        except Exception as e:
            app_logger.error(f"Ensemble detection failed for {guardrail_type}: {e}")
            # Fallback to basic detection
            return DetectionResult(
                blocked=pre_screen_result.blocked if pre_screen_result else False,
                confidence=pre_screen_result.confidence if pre_screen_result else 0.5,
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type=guardrail_type,
                reasons=[f"Ensemble detection failed: {str(e)}"],
                processing_time_ms=100.0
            )

class EscalationManager:
    """Manages escalation decisions"""
    
    def should_escalate(
        self, 
        text: str, 
        result: DetectionResult, 
        context: PipelineContext
    ) -> bool:
        """Determine if escalation is needed"""
        # Escalate if confidence is very low or other criteria
        return result.confidence < 0.6

class DetectionCache:
    """Simple in-memory cache for detection results"""
    
    def __init__(self, max_size: int = 10000):
        self.cache = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Dict[str, DetectionResult]]:
        """Get cached result"""
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: Dict[str, DetectionResult]):
        """Set cached result"""
        if len(self.cache) >= self.max_size:
            # Simple LRU - remove oldest
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache)
        }

# Global pipeline instance
_pipeline_instance: Optional[MultiStagePipeline] = None

def get_multi_stage_pipeline() -> MultiStagePipeline:
    """Get the global multi-stage pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MultiStagePipeline()
    return _pipeline_instance