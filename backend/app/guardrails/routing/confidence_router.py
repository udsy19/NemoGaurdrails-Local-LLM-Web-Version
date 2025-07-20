"""
Phase 4: Confidence-Based Routing System
Intelligent routing based on prediction confidence levels and model agreement
"""

import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import statistics
from abc import ABC, abstractmethod

from app.utils.logger import app_logger
from app.guardrails.models import DetectionResult, PipelineStage, PipelineContext, ConfidenceLevel

class RoutingDecision(Enum):
    """Routing decisions based on confidence analysis"""
    ACCEPT_RESULT = "accept_result"           # High confidence - accept immediately
    CROSS_VALIDATE = "cross_validate"        # Medium confidence or conflict - validate
    CONTEXT_ANALYZE = "context_analyze"      # Low confidence - deep analysis
    ESCALATE_HUMAN = "escalate_human"        # Very low confidence - human review
    RETRY_ANALYSIS = "retry_analysis"        # Error recovery

class ConflictType(Enum):
    """Types of conflicts between models"""
    NO_CONFLICT = "no_conflict"
    THRESHOLD_CONFLICT = "threshold_conflict"     # Models disagree on threshold
    BINARY_CONFLICT = "binary_conflict"           # Models disagree on prediction
    CONFIDENCE_CONFLICT = "confidence_conflict"   # High variance in confidence
    SYSTEMATIC_CONFLICT = "systematic_conflict"   # Consistent model disagreement

@dataclass
class RoutingMetrics:
    """Metrics for routing decisions"""
    confidence_variance: float
    prediction_agreement: float
    confidence_range: float
    average_confidence: float
    model_count: int
    processing_time_ms: float
    conflict_type: ConflictType
    uncertainty_score: float

@dataclass
class RoutingConfig:
    """Configuration for confidence-based routing"""
    # Confidence thresholds
    high_confidence_threshold: float = 0.92
    medium_confidence_threshold: float = 0.75
    low_confidence_threshold: float = 0.50
    
    # Conflict detection
    disagreement_threshold: float = 0.3
    variance_threshold: float = 0.15
    
    # Routing preferences
    enable_early_accept: bool = True
    enable_context_analysis: bool = True
    enable_human_escalation: bool = True
    
    # Performance tuning
    max_cross_validation_time_ms: float = 1000.0
    max_context_analysis_time_ms: float = 2000.0
    
    # Domain-specific adjustments
    domain_confidence_adjustments: Dict[str, float] = field(default_factory=dict)
    high_risk_domains: List[str] = field(default_factory=list)

class ConfidenceRouter:
    """
    Intelligent routing system based on confidence levels and model agreement
    
    Routing Logic:
    - High Confidence (>92%): Accept result immediately
    - Medium Confidence (75-92%): Route to cross-validation
    - Low Confidence (<75%): Route to context analysis
    - Conflicts: Route based on conflict type and severity
    - Very Low/Error: Escalate to human review
    """
    
    def __init__(self, config: RoutingConfig = None):
        self.config = config or RoutingConfig()
        self.routing_history = []
        self.performance_metrics = {
            "total_routed": 0,
            "accepted_directly": 0,
            "cross_validated": 0,
            "context_analyzed": 0,
            "escalated": 0,
            "routing_time_ms": []
        }
        
        app_logger.info("Confidence router initialized")
    
    def route_decision(
        self, 
        result: DetectionResult, 
        context: PipelineContext,
        additional_context: Dict[str, Any] = None
    ) -> Tuple[RoutingDecision, RoutingMetrics]:
        """
        Determine routing decision based on confidence analysis
        
        Args:
            result: Detection result from ensemble
            context: Pipeline context
            additional_context: Additional routing context
            
        Returns:
            Tuple of routing decision and metrics
        """
        start_time = time.time()
        
        try:
            # Calculate routing metrics
            metrics = self._calculate_routing_metrics(result, context)
            
            # Apply domain-specific adjustments
            adjusted_confidence = self._apply_domain_adjustments(
                result.confidence, context.domain_context
            )
            
            # Determine confidence level
            confidence_level = self._classify_confidence_level(
                adjusted_confidence, metrics
            )
            
            # Make routing decision
            routing_decision = self._make_routing_decision(
                confidence_level, metrics, result, context
            )
            
            # Record routing decision
            self._record_routing_decision(routing_decision, metrics, result)
            
            # Update performance metrics
            routing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(routing_decision, routing_time)
            
            app_logger.debug(
                f"Routed {result.guardrail_type} with confidence {adjusted_confidence:.3f} "
                f"to {routing_decision.value}"
            )
            
            return routing_decision, metrics
            
        except Exception as e:
            app_logger.error(f"Confidence routing failed: {e}")
            # Safe fallback - escalate on error
            return RoutingDecision.ESCALATE_HUMAN, RoutingMetrics(
                confidence_variance=1.0,
                prediction_agreement=0.0,
                confidence_range=1.0,
                average_confidence=0.0,
                model_count=0,
                processing_time_ms=0.0,
                conflict_type=ConflictType.SYSTEMATIC_CONFLICT,
                uncertainty_score=1.0
            )
    
    def _calculate_routing_metrics(
        self, 
        result: DetectionResult, 
        context: PipelineContext
    ) -> RoutingMetrics:
        """Calculate metrics for routing decision"""
        
        model_scores = list(result.model_scores.values()) if result.model_scores else [result.confidence]
        
        # Basic statistics
        confidence_variance = np.var(model_scores) if len(model_scores) > 1 else 0.0
        confidence_range = max(model_scores) - min(model_scores) if model_scores else 0.0
        average_confidence = np.mean(model_scores) if model_scores else result.confidence
        
        # Prediction agreement calculation
        prediction_agreement = self._calculate_prediction_agreement(result)
        
        # Conflict detection
        conflict_type = self._detect_conflict_type(model_scores, result)
        
        # Uncertainty quantification
        uncertainty_score = self._calculate_uncertainty_score(result, model_scores)
        
        return RoutingMetrics(
            confidence_variance=confidence_variance,
            prediction_agreement=prediction_agreement,
            confidence_range=confidence_range,
            average_confidence=average_confidence,
            model_count=len(model_scores),
            processing_time_ms=result.processing_time_ms,
            conflict_type=conflict_type,
            uncertainty_score=uncertainty_score
        )
    
    def _classify_confidence_level(
        self, 
        confidence: float, 
        metrics: RoutingMetrics
    ) -> ConfidenceLevel:
        """Classify confidence level considering metrics"""
        
        # Check for conflicts first
        if metrics.conflict_type != ConflictType.NO_CONFLICT:
            return ConfidenceLevel.CONFLICT
        
        # High variance indicates uncertainty
        if metrics.confidence_variance > self.config.variance_threshold:
            return ConfidenceLevel.LOW
        
        # Standard confidence classification
        if confidence >= self.config.high_confidence_threshold:
            return ConfidenceLevel.HIGH
        elif confidence >= self.config.medium_confidence_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _make_routing_decision(
        self, 
        confidence_level: ConfidenceLevel,
        metrics: RoutingMetrics,
        result: DetectionResult,
        context: PipelineContext
    ) -> RoutingDecision:
        """Make the final routing decision"""
        
        # Check for error conditions first
        if metrics.model_count == 0 or metrics.uncertainty_score > 0.9:
            return RoutingDecision.ESCALATE_HUMAN
        
        # High-risk domain special handling
        if context.domain_context in self.config.high_risk_domains:
            if confidence_level == ConfidenceLevel.HIGH:
                return RoutingDecision.CROSS_VALIDATE  # Extra validation for high-risk
            else:
                return RoutingDecision.CONTEXT_ANALYZE
        
        # Standard routing logic
        if confidence_level == ConfidenceLevel.HIGH:
            if self.config.enable_early_accept:
                return RoutingDecision.ACCEPT_RESULT
            else:
                return RoutingDecision.CROSS_VALIDATE
        
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return RoutingDecision.CROSS_VALIDATE
        
        elif confidence_level == ConfidenceLevel.CONFLICT:
            # Route conflicts based on type and severity
            return self._route_conflict(metrics, result, context)
        
        else:  # LOW confidence
            if self.config.enable_context_analysis:
                return RoutingDecision.CONTEXT_ANALYZE
            else:
                return RoutingDecision.ESCALATE_HUMAN
    
    def _route_conflict(
        self, 
        metrics: RoutingMetrics, 
        result: DetectionResult,
        context: PipelineContext
    ) -> RoutingDecision:
        """Route conflicts based on conflict type and severity"""
        
        if metrics.conflict_type == ConflictType.BINARY_CONFLICT:
            # Models disagree on basic prediction - needs context analysis
            return RoutingDecision.CONTEXT_ANALYZE
        
        elif metrics.conflict_type == ConflictType.CONFIDENCE_CONFLICT:
            # High variance in confidence - cross-validate
            return RoutingDecision.CROSS_VALIDATE
        
        elif metrics.conflict_type == ConflictType.THRESHOLD_CONFLICT:
            # Near-threshold disagreement - cross-validate
            return RoutingDecision.CROSS_VALIDATE
        
        elif metrics.conflict_type == ConflictType.SYSTEMATIC_CONFLICT:
            # Systematic disagreement - escalate
            return RoutingDecision.ESCALATE_HUMAN
        
        else:
            # Default for unknown conflicts
            return RoutingDecision.CROSS_VALIDATE
    
    def _apply_domain_adjustments(
        self, 
        confidence: float, 
        domain: str
    ) -> float:
        """Apply domain-specific confidence adjustments"""
        
        adjustment = self.config.domain_confidence_adjustments.get(domain, 0.0)
        adjusted_confidence = confidence + adjustment
        
        # Keep within valid range
        return max(0.0, min(1.0, adjusted_confidence))
    
    def _calculate_prediction_agreement(self, result: DetectionResult) -> float:
        """Calculate how much models agree on prediction"""
        
        if not result.model_scores or len(result.model_scores) < 2:
            return 1.0  # Single model - perfect agreement
        
        # Convert confidences to binary predictions
        threshold = 0.5
        predictions = [
            1 if score > threshold else 0 
            for score in result.model_scores.values()
        ]
        
        # Calculate agreement rate
        if not predictions:
            return 1.0
        
        majority_prediction = 1 if sum(predictions) > len(predictions) / 2 else 0
        agreement_count = sum(1 for pred in predictions if pred == majority_prediction)
        
        return agreement_count / len(predictions)
    
    def _detect_conflict_type(
        self, 
        model_scores: List[float], 
        result: DetectionResult
    ) -> ConflictType:
        """Detect the type of conflict between models"""
        
        if len(model_scores) < 2:
            return ConflictType.NO_CONFLICT
        
        # Calculate statistics
        score_range = max(model_scores) - min(model_scores)
        variance = np.var(model_scores)
        
        # Binary prediction conflict
        threshold = 0.5
        predictions = [1 if score > threshold else 0 for score in model_scores]
        unique_predictions = len(set(predictions))
        
        if unique_predictions > 1 and score_range > self.config.disagreement_threshold:
            return ConflictType.BINARY_CONFLICT
        
        # High confidence variance
        if variance > self.config.variance_threshold:
            return ConflictType.CONFIDENCE_CONFLICT
        
        # Threshold boundary conflict
        near_threshold_count = sum(
            1 for score in model_scores 
            if abs(score - threshold) < 0.1
        )
        if near_threshold_count > len(model_scores) / 2:
            return ConflictType.THRESHOLD_CONFLICT
        
        # Check for systematic disagreement pattern
        if self._detect_systematic_disagreement(model_scores):
            return ConflictType.SYSTEMATIC_CONFLICT
        
        return ConflictType.NO_CONFLICT
    
    def _detect_systematic_disagreement(self, model_scores: List[float]) -> bool:
        """Detect if there's a systematic disagreement pattern"""
        
        # Simple check - if scores are consistently split into two groups
        if len(model_scores) < 4:
            return False
        
        sorted_scores = sorted(model_scores)
        mid_point = len(sorted_scores) // 2
        
        lower_group = sorted_scores[:mid_point]
        upper_group = sorted_scores[mid_point:]
        
        lower_mean = np.mean(lower_group)
        upper_mean = np.mean(upper_group)
        
        # Systematic disagreement if groups are far apart
        return (upper_mean - lower_mean) > self.config.disagreement_threshold
    
    def _calculate_uncertainty_score(
        self, 
        result: DetectionResult, 
        model_scores: List[float]
    ) -> float:
        """Calculate overall uncertainty score"""
        
        factors = []
        
        # Confidence uncertainty
        if result.uncertainty_bounds and result.uncertainty_bounds != (0.0, 1.0):
            bound_range = result.uncertainty_bounds[1] - result.uncertainty_bounds[0]
            factors.append(bound_range)
        
        # Model agreement uncertainty
        if len(model_scores) > 1:
            variance_uncertainty = min(1.0, np.var(model_scores) * 4)  # Scale variance
            factors.append(variance_uncertainty)
        
        # Processing time uncertainty (longer time may indicate uncertainty)
        if result.processing_time_ms > 0:
            time_uncertainty = min(1.0, result.processing_time_ms / 1000.0)  # Normalize
            factors.append(time_uncertainty * 0.1)  # Low weight
        
        if not factors:
            return 0.0
        
        # Combine uncertainty factors
        return min(1.0, np.mean(factors))
    
    def _record_routing_decision(
        self, 
        decision: RoutingDecision, 
        metrics: RoutingMetrics,
        result: DetectionResult
    ):
        """Record routing decision for analysis"""
        
        record = {
            "timestamp": time.time(),
            "decision": decision.value,
            "guardrail_type": result.guardrail_type,
            "confidence": result.confidence,
            "metrics": metrics,
            "stage": result.stage.value if result.stage else None
        }
        
        self.routing_history.append(record)
        
        # Keep only last 1000 records
        if len(self.routing_history) > 1000:
            self.routing_history.pop(0)
    
    def _update_performance_metrics(
        self, 
        decision: RoutingDecision, 
        routing_time: float
    ):
        """Update performance tracking metrics"""
        
        self.performance_metrics["total_routed"] += 1
        self.performance_metrics["routing_time_ms"].append(routing_time)
        
        # Update decision-specific counters
        if decision == RoutingDecision.ACCEPT_RESULT:
            self.performance_metrics["accepted_directly"] += 1
        elif decision == RoutingDecision.CROSS_VALIDATE:
            self.performance_metrics["cross_validated"] += 1
        elif decision == RoutingDecision.CONTEXT_ANALYZE:
            self.performance_metrics["context_analyzed"] += 1
        elif decision == RoutingDecision.ESCALATE_HUMAN:
            self.performance_metrics["escalated"] += 1
        
        # Keep only last 1000 timing records
        if len(self.performance_metrics["routing_time_ms"]) > 1000:
            self.performance_metrics["routing_time_ms"].pop(0)
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing performance statistics"""
        
        if not self.routing_history:
            return {"message": "No routing history available"}
        
        total_routed = self.performance_metrics["total_routed"]
        
        stats = {
            "total_decisions": total_routed,
            "decision_distribution": {
                "accepted_directly": self.performance_metrics["accepted_directly"] / total_routed,
                "cross_validated": self.performance_metrics["cross_validated"] / total_routed,
                "context_analyzed": self.performance_metrics["context_analyzed"] / total_routed,
                "escalated": self.performance_metrics["escalated"] / total_routed
            },
            "routing_performance": {
                "average_routing_time_ms": np.mean(self.performance_metrics["routing_time_ms"]),
                "p95_routing_time_ms": np.percentile(self.performance_metrics["routing_time_ms"], 95)
            },
            "recent_patterns": self._analyze_recent_patterns()
        }
        
        return stats
    
    def _analyze_recent_patterns(self) -> Dict[str, Any]:
        """Analyze recent routing patterns"""
        
        recent_records = self.routing_history[-100:]  # Last 100 decisions
        
        if not recent_records:
            return {}
        
        # Analyze confidence trends
        confidences = [record["confidence"] for record in recent_records]
        
        # Analyze decision patterns by guardrail type
        by_guardrail = {}
        for record in recent_records:
            guardrail_type = record["guardrail_type"]
            if guardrail_type not in by_guardrail:
                by_guardrail[guardrail_type] = []
            by_guardrail[guardrail_type].append(record)
        
        patterns = {
            "average_confidence": np.mean(confidences),
            "confidence_trend": "stable",  # Could implement trend analysis
            "most_escalated_guardrail": max(
                by_guardrail.keys(),
                key=lambda g: sum(1 for r in by_guardrail[g] if r["decision"] == "escalate_human")
            ) if by_guardrail else None,
            "guardrail_performance": {
                guardrail: {
                    "total": len(records),
                    "escalation_rate": sum(1 for r in records if r["decision"] == "escalate_human") / len(records)
                }
                for guardrail, records in by_guardrail.items()
            }
        }
        
        return patterns
    
    def optimize_thresholds(self, feedback_data: List[Dict[str, Any]]):
        """Optimize confidence thresholds based on feedback"""
        
        # This would implement threshold optimization based on actual performance data
        # For now, it's a placeholder for future implementation
        
        app_logger.info("Threshold optimization would be implemented here")
        pass

# Global router instance
_confidence_router: Optional[ConfidenceRouter] = None

def get_confidence_router() -> ConfidenceRouter:
    """Get the global confidence router instance"""
    global _confidence_router
    if _confidence_router is None:
        _confidence_router = ConfidenceRouter()
    return _confidence_router