"""
Base Ensemble Framework for Industry-Grade Guardrails
Implements multi-stage pipeline with confidence-based routing
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence levels for routing decisions"""
    HIGH = "high"      # >92% confidence
    MEDIUM = "medium"  # 75-92% confidence  
    LOW = "low"        # <75% confidence

class DetectionStage(Enum):
    """Multi-stage pipeline stages"""
    FAST_PRESCREENING = "fast_prescreening"
    PRIMARY_ENSEMBLE = "primary_ensemble"
    CROSS_VALIDATION = "cross_validation"
    CONTEXT_AWARE_LLM = "context_aware_llm"
    CONFIDENCE_ESCALATION = "confidence_escalation"

@dataclass
class DetectionResult:
    """Standardized detection result format"""
    blocked: bool
    confidence: float
    blocking_reasons: List[str]
    model_name: str
    processing_time_ms: float
    metadata: Dict[str, Any]
    stage: DetectionStage
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocked": self.blocked,
            "confidence": self.confidence,
            "blocking_reasons": self.blocking_reasons,
            "model_name": self.model_name,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "stage": self.stage.value
        }

@dataclass
class EnsembleResult:
    """Final ensemble decision with detailed analysis"""
    blocked: bool
    final_confidence: float
    blocking_reasons: List[str]
    model_results: List[DetectionResult]
    consensus_level: str
    processing_stages: List[DetectionStage]
    total_processing_time_ms: float
    escalation_triggered: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocked": self.blocked,
            "final_confidence": self.final_confidence,
            "blocking_reasons": self.blocking_reasons,
            "model_results": [result.to_dict() for result in self.model_results],
            "consensus_level": self.consensus_level,
            "processing_stages": [stage.value for stage in self.processing_stages],
            "total_processing_time_ms": self.total_processing_time_ms,
            "escalation_triggered": self.escalation_triggered
        }

class BaseDetector(ABC):
    """Abstract base class for all detectors"""
    
    def __init__(self, name: str, weight: float = 1.0, confidence_threshold: float = 0.5):
        self.name = name
        self.weight = weight
        self.confidence_threshold = confidence_threshold
        self.is_loaded = False
        
    @abstractmethod
    async def load_model(self) -> bool:
        """Load the model/detector"""
        pass
        
    @abstractmethod
    async def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> DetectionResult:
        """Perform detection on input text"""
        pass
        
    @abstractmethod
    def unload_model(self) -> bool:
        """Unload the model to free memory"""
        pass

class EnsembleFramework:
    """
    Core ensemble framework implementing multi-stage pipeline
    with confidence-based routing as per the implementation plan
    """
    
    def __init__(self, 
                 high_confidence_threshold: float = 0.92,
                 medium_confidence_threshold: float = 0.75,
                 enable_parallel_processing: bool = True):
        """
        Initialize ensemble framework
        
        Args:
            high_confidence_threshold: Threshold for high confidence (accept decision)
            medium_confidence_threshold: Threshold for medium confidence (cross-validate)
            enable_parallel_processing: Enable parallel model execution
        """
        self.high_confidence_threshold = high_confidence_threshold
        self.medium_confidence_threshold = medium_confidence_threshold
        self.enable_parallel_processing = enable_parallel_processing
        
        # Stage processors
        self.stage_processors = {
            DetectionStage.FAST_PRESCREENING: self._fast_prescreening,
            DetectionStage.PRIMARY_ENSEMBLE: self._primary_ensemble,
            DetectionStage.CROSS_VALIDATION: self._cross_validation,
            DetectionStage.CONTEXT_AWARE_LLM: self._context_aware_llm,
            DetectionStage.CONFIDENCE_ESCALATION: self._confidence_escalation
        }
        
        # Detector collections by guardrail type
        self.detectors = {
            "toxicity": [],
            "pii": [],
            "spam": [],
            "topic": [],
            "fact_check": [],
            "prompt_injection": []
        }
        
        # Performance tracking
        self.performance_stats = {
            "total_requests": 0,
            "stage_usage": {stage: 0 for stage in DetectionStage},
            "average_processing_time": 0.0,
            "consensus_rates": {"high": 0, "medium": 0, "low": 0}
        }
        
        logger.info(f"Ensemble framework initialized with thresholds: high={high_confidence_threshold}, medium={medium_confidence_threshold}")
    
    def register_detector(self, guardrail_type: str, detector: BaseDetector) -> bool:
        """Register a detector for a specific guardrail type"""
        if guardrail_type not in self.detectors:
            logger.error(f"Unknown guardrail type: {guardrail_type}")
            return False
            
        self.detectors[guardrail_type].append(detector)
        logger.info(f"Registered detector {detector.name} for {guardrail_type}")
        return True
    
    async def load_all_models(self) -> Dict[str, bool]:
        """Load all registered models"""
        results = {}
        
        for guardrail_type, detectors in self.detectors.items():
            for detector in detectors:
                try:
                    success = await detector.load_model()
                    results[f"{guardrail_type}_{detector.name}"] = success
                    if success:
                        logger.info(f"Loaded {detector.name} for {guardrail_type}")
                    else:
                        logger.warning(f"Failed to load {detector.name} for {guardrail_type}")
                except Exception as e:
                    logger.error(f"Error loading {detector.name}: {e}")
                    results[f"{guardrail_type}_{detector.name}"] = False
        
        return results
    
    async def process_text(self, 
                          text: str, 
                          guardrail_types: List[str],
                          context: Optional[Dict[str, Any]] = None) -> EnsembleResult:
        """
        Process text through multi-stage pipeline
        
        Args:
            text: Input text to analyze
            guardrail_types: List of guardrail types to apply
            context: Optional context information
            
        Returns:
            EnsembleResult with final decision and detailed analysis
        """
        start_time = time.time()
        processing_stages = []
        all_results = []
        
        try:
            # Stage 1: Fast Pre-screening
            prescreening_result = await self._fast_prescreening(text, guardrail_types, context)
            processing_stages.append(DetectionStage.FAST_PRESCREENING)
            
            if prescreening_result.blocked and prescreening_result.confidence > self.high_confidence_threshold:
                # High confidence block from prescreening
                return self._create_final_result(
                    [prescreening_result], processing_stages, start_time, 
                    blocked=True, escalation=False
                )
            
            # Stage 2: Primary Ensemble
            ensemble_results = await self._primary_ensemble(text, guardrail_types, context)
            processing_stages.append(DetectionStage.PRIMARY_ENSEMBLE)
            all_results.extend(ensemble_results)
            
            # Calculate ensemble confidence
            ensemble_confidence = self._calculate_ensemble_confidence(ensemble_results)
            ensemble_blocked = self._calculate_ensemble_decision(ensemble_results)
            
            # Confidence-based routing
            confidence_level = self._determine_confidence_level(ensemble_confidence)
            
            if confidence_level == ConfidenceLevel.HIGH:
                # High confidence - accept decision
                return self._create_final_result(
                    all_results, processing_stages, start_time,
                    blocked=ensemble_blocked, escalation=False
                )
            
            elif confidence_level == ConfidenceLevel.MEDIUM:
                # Medium confidence - cross-validation
                cross_validation_results = await self._cross_validation(text, guardrail_types, context, ensemble_results)
                processing_stages.append(DetectionStage.CROSS_VALIDATION)
                all_results.extend(cross_validation_results)
                
                # Recalculate with cross-validation
                final_confidence = self._calculate_ensemble_confidence(all_results)
                final_blocked = self._calculate_ensemble_decision(all_results)
                
                if final_confidence > self.medium_confidence_threshold:
                    return self._create_final_result(
                        all_results, processing_stages, start_time,
                        blocked=final_blocked, escalation=False
                    )
            
            # Low confidence or still uncertain - Context-aware LLM analysis
            llm_results = await self._context_aware_llm(text, guardrail_types, context, all_results)
            processing_stages.append(DetectionStage.CONTEXT_AWARE_LLM)
            all_results.extend(llm_results)
            
            # Final decision
            final_confidence = self._calculate_ensemble_confidence(all_results)
            final_blocked = self._calculate_ensemble_decision(all_results)
            
            # Check if escalation is needed
            escalation_needed = final_confidence < self.medium_confidence_threshold
            if escalation_needed:
                escalation_result = await self._confidence_escalation(text, guardrail_types, context, all_results)
                processing_stages.append(DetectionStage.CONFIDENCE_ESCALATION)
                if escalation_result:
                    all_results.append(escalation_result)
            
            return self._create_final_result(
                all_results, processing_stages, start_time,
                blocked=final_blocked, escalation=escalation_needed
            )
            
        except Exception as e:
            logger.error(f"Error in ensemble processing: {e}")
            # Return safe default (block with low confidence)
            error_result = DetectionResult(
                blocked=True,
                confidence=0.1,
                blocking_reasons=[f"Processing error: {str(e)}"],
                model_name="ensemble_framework",
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": True},
                stage=DetectionStage.CONFIDENCE_ESCALATION
            )
            
            return self._create_final_result(
                [error_result], processing_stages, start_time,
                blocked=True, escalation=True
            )
    
    async def _fast_prescreening(self, text: str, guardrail_types: List[str], context: Optional[Dict[str, Any]]) -> DetectionResult:
        """Stage 1: Fast pre-screening with lightweight checks"""
        start_time = time.time()
        
        # Character-level analysis
        if self._check_character_attacks(text):
            return DetectionResult(
                blocked=True,
                confidence=0.95,
                blocking_reasons=["Character-level attack detected"],
                model_name="character_analyzer",
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"attack_type": "character_injection"},
                stage=DetectionStage.FAST_PRESCREENING
            )
        
        # Basic format validation
        if not self._validate_input_format(text):
            return DetectionResult(
                blocked=True,
                confidence=0.90,
                blocking_reasons=["Invalid input format"],
                model_name="format_validator",
                processing_time_ms=(time.time() - start_time) * 1000,
                metadata={"validation_error": True},
                stage=DetectionStage.FAST_PRESCREENING
            )
        
        # Passed prescreening
        return DetectionResult(
            blocked=False,
            confidence=0.8,
            blocking_reasons=[],
            model_name="fast_prescreening",
            processing_time_ms=(time.time() - start_time) * 1000,
            metadata={"prescreening_passed": True},
            stage=DetectionStage.FAST_PRESCREENING
        )
    
    async def _primary_ensemble(self, text: str, guardrail_types: List[str], context: Optional[Dict[str, Any]]) -> List[DetectionResult]:
        """Stage 2: Primary ensemble detection with parallel processing"""
        results = []
        
        if self.enable_parallel_processing:
            # Run all detectors in parallel
            tasks = []
            for guardrail_type in guardrail_types:
                for detector in self.detectors.get(guardrail_type, []):
                    if detector.is_loaded:
                        tasks.append(detector.detect(text, context))
            
            if tasks:
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in parallel_results:
                    if isinstance(result, DetectionResult):
                        results.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Detector error: {result}")
        else:
            # Sequential processing
            for guardrail_type in guardrail_types:
                for detector in self.detectors.get(guardrail_type, []):
                    if detector.is_loaded:
                        try:
                            result = await detector.detect(text, context)
                            results.append(result)
                        except Exception as e:
                            logger.error(f"Detector {detector.name} error: {e}")
        
        return results
    
    async def _cross_validation(self, text: str, guardrail_types: List[str], 
                               context: Optional[Dict[str, Any]],
                               primary_results: List[DetectionResult]) -> List[DetectionResult]:
        """Stage 3: Cross-validation for conflicting results"""
        # Identify conflicts
        blocked_count = sum(1 for r in primary_results if r.blocked)
        total_count = len(primary_results)
        
        if total_count == 0:
            return []
        
        disagreement_ratio = abs(blocked_count - (total_count - blocked_count)) / total_count
        
        if disagreement_ratio < 0.3:  # Significant disagreement
            # Run additional validation with different model types
            logger.info("Significant disagreement detected, running cross-validation")
            
            # This would run alternative models or different approaches
            # For now, return a meta-analysis result
            cross_val_result = DetectionResult(
                blocked=blocked_count > total_count / 2,
                confidence=0.7,  # Medium confidence
                blocking_reasons=["Cross-validation analysis"],
                model_name="cross_validator",
                processing_time_ms=50.0,  # Simulated processing time
                metadata={"disagreement_ratio": disagreement_ratio, "method": "meta_analysis"},
                stage=DetectionStage.CROSS_VALIDATION
            )
            return [cross_val_result]
        
        return []
    
    async def _context_aware_llm(self, text: str, guardrail_types: List[str],
                                context: Optional[Dict[str, Any]],
                                previous_results: List[DetectionResult]) -> List[DetectionResult]:
        """Stage 4: Context-aware LLM analysis for complex cases"""
        # This would integrate with Llama-3.1-8B for sophisticated analysis
        # For now, return a simulated sophisticated analysis
        
        llm_result = DetectionResult(
            blocked=any(r.blocked for r in previous_results if r.confidence > 0.6),
            confidence=0.85,
            blocking_reasons=["Context-aware analysis"],
            model_name="llama_3_1_8b",
            processing_time_ms=300.0,  # Typical LLM processing time
            metadata={
                "context_analysis": True,
                "reasoning": "Advanced contextual evaluation",
                "previous_results_count": len(previous_results)
            },
            stage=DetectionStage.CONTEXT_AWARE_LLM
        )
        
        return [llm_result]
    
    async def _confidence_escalation(self, text: str, guardrail_types: List[str],
                                   context: Optional[Dict[str, Any]],
                                   all_results: List[DetectionResult]) -> Optional[DetectionResult]:
        """Stage 5: Confidence-based escalation for human review"""
        escalation_result = DetectionResult(
            blocked=False,  # Don't block, but flag for review
            confidence=0.5,
            blocking_reasons=["Requires human review"],
            model_name="escalation_handler",
            processing_time_ms=10.0,
            metadata={
                "escalation_triggered": True,
                "review_priority": "medium",
                "uncertainty_level": "high"
            },
            stage=DetectionStage.CONFIDENCE_ESCALATION
        )
        
        logger.info(f"Escalation triggered for text: {text[:100]}...")
        return escalation_result
    
    def _calculate_ensemble_confidence(self, results: List[DetectionResult]) -> float:
        """Calculate weighted ensemble confidence"""
        if not results:
            return 0.0
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for result in results:
            # Use model weight (default 1.0) and confidence
            weight = 1.0  # Would be detector.weight in real implementation
            total_weight += weight
            weighted_confidence += result.confidence * weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _calculate_ensemble_decision(self, results: List[DetectionResult]) -> bool:
        """Calculate ensemble decision using weighted voting"""
        if not results:
            return False
        
        blocked_weight = 0.0
        total_weight = 0.0
        
        for result in results:
            weight = 1.0  # Would be detector.weight in real implementation
            total_weight += weight
            
            if result.blocked:
                blocked_weight += weight * result.confidence
        
        return (blocked_weight / total_weight) > 0.5 if total_weight > 0 else False
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level for routing decisions"""
        if confidence >= self.high_confidence_threshold:
            return ConfidenceLevel.HIGH
        elif confidence >= self.medium_confidence_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _create_final_result(self, results: List[DetectionResult], 
                           stages: List[DetectionStage], 
                           start_time: float,
                           blocked: bool, 
                           escalation: bool) -> EnsembleResult:
        """Create final ensemble result"""
        total_time = (time.time() - start_time) * 1000
        
        # Determine consensus level
        if len(results) == 0:
            consensus = "no_data"
        else:
            blocked_count = sum(1 for r in results if r.blocked)
            agreement_ratio = max(blocked_count, len(results) - blocked_count) / len(results)
            
            if agreement_ratio >= 0.8:
                consensus = "strong"
            elif agreement_ratio >= 0.6:
                consensus = "moderate"
            else:
                consensus = "weak"
        
        # Collect all blocking reasons
        all_blocking_reasons = []
        for result in results:
            all_blocking_reasons.extend(result.blocking_reasons)
        
        # Update performance stats
        self.performance_stats["total_requests"] += 1
        for stage in stages:
            self.performance_stats["stage_usage"][stage] += 1
        
        final_confidence = self._calculate_ensemble_confidence(results)
        confidence_level = self._determine_confidence_level(final_confidence)
        self.performance_stats["consensus_rates"][confidence_level.value] += 1
        
        return EnsembleResult(
            blocked=blocked,
            final_confidence=final_confidence,
            blocking_reasons=list(set(all_blocking_reasons)),  # Remove duplicates
            model_results=results,
            consensus_level=consensus,
            processing_stages=stages,
            total_processing_time_ms=total_time,
            escalation_triggered=escalation
        )
    
    def _check_character_attacks(self, text: str) -> bool:
        """Check for character-level attacks"""
        # Check for invisible characters
        invisible_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
        if any(char in text for char in invisible_chars):
            return True
        
        # Check for excessive Unicode escapes (but allow normal escapes)
        unicode_escape_count = text.count('\\u')
        if unicode_escape_count > 10 and unicode_escape_count > len(text) * 0.05:  # More than 5% of text
            return True
        
        # Check for homograph attacks (basic)
        suspicious_chars = ['а', 'е', 'о', 'р', 'с', 'х']  # Cyrillic that look like Latin
        if any(char in text for char in suspicious_chars):
            return True
        
        return False
    
    def _validate_input_format(self, text: str) -> bool:
        """Validate basic input format"""
        # Check length limits
        if len(text) > 10000:  # 10KB limit
            return False
        
        # Check for null bytes
        if '\x00' in text:
            return False
        
        # Check for excessive newlines (potential format manipulation)
        if text.count('\n') > 100:
            return False
        
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return self.performance_stats.copy()
    
    def reset_performance_stats(self) -> None:
        """Reset performance statistics"""
        self.performance_stats = {
            "total_requests": 0,
            "stage_usage": {stage: 0 for stage in DetectionStage},
            "average_processing_time": 0.0,
            "consensus_rates": {"high": 0, "medium": 0, "low": 0}
        }