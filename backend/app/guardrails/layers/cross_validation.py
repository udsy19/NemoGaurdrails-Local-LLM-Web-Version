"""
Phase 4: Cross-Validation Layer
Advanced conflict resolution and model agreement analysis for ensemble decisions
"""

import time
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import statistics
from abc import ABC, abstractmethod

from app.utils.logger import app_logger
from app.guardrails.models import DetectionResult, PipelineStage, PipelineContext
from app.guardrails.ensemble.enhanced_ensemble import EnsembleStrategy, ModelPrediction, BaseEnsembleModel

class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicts between models"""
    WEIGHTED_MAJORITY = "weighted_majority"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    META_CLASSIFIER = "meta_classifier"
    BAYESIAN_ENSEMBLE = "bayesian_ensemble"
    UNCERTAINTY_WEIGHTING = "uncertainty_weighting"

class ValidationMethod(Enum):
    """Cross-validation methods"""
    BOOTSTRAP_VALIDATION = "bootstrap_validation"
    MONTE_CARLO_DROPOUT = "monte_carlo_dropout"
    ENSEMBLE_VOTING = "ensemble_voting"
    CONFIDENCE_CALIBRATION = "confidence_calibration"

@dataclass
class ConflictAnalysis:
    """Analysis of conflicts between model predictions"""
    conflict_detected: bool
    conflict_severity: float  # 0.0 to 1.0
    disagreement_patterns: List[str]
    model_clusters: Dict[str, List[str]]  # Groups of agreeing models
    uncertainty_score: float
    resolution_confidence: float

@dataclass
class ValidationConfig:
    """Configuration for cross-validation layer"""
    resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.WEIGHTED_MAJORITY
    validation_method: ValidationMethod = ValidationMethod.ENSEMBLE_VOTING
    confidence_threshold: float = 0.75
    disagreement_threshold: float = 0.3
    min_agreement_ratio: float = 0.6
    enable_uncertainty_quantification: bool = True
    enable_bootstrap_validation: bool = True
    bootstrap_samples: int = 100
    timeout_ms: float = 2000.0

class CrossValidationLayer:
    """
    Advanced cross-validation and conflict resolution layer
    
    Features:
    - Multi-strategy conflict resolution
    - Uncertainty quantification
    - Bootstrap validation
    - Confidence calibration
    - Meta-classification for complex conflicts
    """
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        self.meta_classifiers = {}
        self.validation_history = []
        self.calibration_data = {}
        
        # Performance tracking
        self.validation_stats = {
            "total_validations": 0,
            "conflicts_resolved": 0,
            "confidence_improvements": 0,
            "average_processing_time": 0.0,
            "resolution_strategy_performance": {}
        }
        
        app_logger.info("Cross-validation layer initialized with advanced conflict resolution")
    
    async def validate(
        self,
        text: str,
        guardrail_type: str,
        ensemble_result: DetectionResult,
        context: PipelineContext
    ) -> DetectionResult:
        """
        Perform cross-validation and conflict resolution
        
        Args:
            text: Input text
            guardrail_type: Type of guardrail
            ensemble_result: Result from ensemble detection
            context: Pipeline context
            
        Returns:
            Validated and potentially improved DetectionResult
        """
        start_time = time.time()
        
        try:
            self.validation_stats["total_validations"] += 1
            
            # Analyze conflicts in ensemble result
            conflict_analysis = await self._analyze_conflicts(ensemble_result, text, context)
            
            if not conflict_analysis.conflict_detected:
                # No significant conflict - validate confidence and return
                validated_result = await self._validate_confidence(ensemble_result, text, context)
                app_logger.debug(f"No conflict detected for {guardrail_type}, confidence validated")
                return validated_result
            
            # Conflict detected - apply resolution strategy
            self.validation_stats["conflicts_resolved"] += 1
            app_logger.info(f"Conflict detected for {guardrail_type}, severity: {conflict_analysis.conflict_severity:.3f}")
            
            # Resolve conflict based on configured strategy
            resolved_result = await self._resolve_conflict(
                text, guardrail_type, ensemble_result, conflict_analysis, context
            )
            
            # Apply additional validation if enabled
            if self.config.enable_bootstrap_validation:
                final_result = await self._bootstrap_validation(
                    text, guardrail_type, resolved_result, context
                )
            else:
                final_result = resolved_result
            
            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000
            self._update_validation_stats(processing_time, conflict_analysis)
            
            # Record validation for future analysis
            self._record_validation(text, ensemble_result, final_result, conflict_analysis)
            
            final_result.stage = PipelineStage.CROSS_VALIDATION
            final_result.processing_time_ms = processing_time
            
            return final_result
            
        except Exception as e:
            app_logger.error(f"Cross-validation failed for {guardrail_type}: {e}")
            # Return original result with error annotation
            ensemble_result.reasons.append(f"Cross-validation error: {str(e)}")
            return ensemble_result
    
    async def _analyze_conflicts(
        self,
        ensemble_result: DetectionResult,
        text: str,
        context: PipelineContext
    ) -> ConflictAnalysis:
        """Analyze conflicts between model predictions"""
        
        if not ensemble_result.model_scores or len(ensemble_result.model_scores) < 2:
            return ConflictAnalysis(
                conflict_detected=False,
                conflict_severity=0.0,
                disagreement_patterns=[],
                model_clusters={},
                uncertainty_score=0.0,
                resolution_confidence=1.0
            )
        
        scores = list(ensemble_result.model_scores.values())
        model_names = list(ensemble_result.model_scores.keys())
        
        # Calculate disagreement metrics
        score_range = max(scores) - min(scores)
        score_variance = np.var(scores)
        score_std = np.std(scores)
        
        # Binary prediction disagreement
        threshold = 0.5
        binary_predictions = [score > threshold for score in scores]
        positive_count = sum(binary_predictions)
        agreement_ratio = max(positive_count, len(binary_predictions) - positive_count) / len(binary_predictions)
        
        # Detect conflict
        conflict_detected = (
            score_range > self.config.disagreement_threshold or
            score_variance > 0.1 or
            agreement_ratio < self.config.min_agreement_ratio
        )
        
        # Calculate conflict severity
        conflict_severity = min(1.0, (score_range + score_variance) / 2.0)
        
        # Analyze disagreement patterns
        disagreement_patterns = []
        if score_range > 0.5:
            disagreement_patterns.append("Wide confidence range")
        if score_variance > 0.15:
            disagreement_patterns.append("High variance in predictions")
        if agreement_ratio < 0.7:
            disagreement_patterns.append("Binary disagreement")
        
        # Cluster models by agreement
        model_clusters = self._cluster_models_by_agreement(model_names, scores, threshold)
        
        # Calculate uncertainty score
        uncertainty_score = self._calculate_uncertainty_score(scores, ensemble_result)
        
        # Estimate resolution confidence
        resolution_confidence = 1.0 - conflict_severity
        
        return ConflictAnalysis(
            conflict_detected=conflict_detected,
            conflict_severity=conflict_severity,
            disagreement_patterns=disagreement_patterns,
            model_clusters=model_clusters,
            uncertainty_score=uncertainty_score,
            resolution_confidence=resolution_confidence
        )
    
    async def _resolve_conflict(
        self,
        text: str,
        guardrail_type: str,
        ensemble_result: DetectionResult,
        conflict_analysis: ConflictAnalysis,
        context: PipelineContext
    ) -> DetectionResult:
        """Resolve conflicts using the configured strategy"""
        
        strategy = self.config.resolution_strategy
        
        if strategy == ConflictResolutionStrategy.WEIGHTED_MAJORITY:
            return await self._weighted_majority_resolution(ensemble_result, conflict_analysis)
        elif strategy == ConflictResolutionStrategy.CONFIDENCE_THRESHOLD:
            return await self._confidence_threshold_resolution(ensemble_result, conflict_analysis)
        elif strategy == ConflictResolutionStrategy.META_CLASSIFIER:
            return await self._meta_classifier_resolution(text, guardrail_type, ensemble_result, conflict_analysis)
        elif strategy == ConflictResolutionStrategy.BAYESIAN_ENSEMBLE:
            return await self._bayesian_ensemble_resolution(ensemble_result, conflict_analysis)
        elif strategy == ConflictResolutionStrategy.UNCERTAINTY_WEIGHTING:
            return await self._uncertainty_weighted_resolution(ensemble_result, conflict_analysis)
        else:
            # Default to weighted majority
            return await self._weighted_majority_resolution(ensemble_result, conflict_analysis)
    
    async def _weighted_majority_resolution(
        self,
        ensemble_result: DetectionResult,
        conflict_analysis: ConflictAnalysis
    ) -> DetectionResult:
        """Resolve using weighted majority voting with confidence weighting"""
        
        scores = list(ensemble_result.model_scores.values())
        model_names = list(ensemble_result.model_scores.keys())
        
        # Weight by confidence and historical performance
        weighted_sum = 0.0
        total_weight = 0.0
        
        for model_name, score in ensemble_result.model_scores.items():
            # Base weight from confidence
            confidence_weight = score
            
            # Historical performance weight (if available)
            historical_weight = self._get_model_performance_weight(model_name)
            
            # Combined weight
            combined_weight = confidence_weight * historical_weight
            
            # Binary vote weighted by confidence
            vote = 1.0 if score > 0.5 else 0.0
            weighted_sum += vote * combined_weight
            total_weight += combined_weight
        
        final_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        final_prediction = final_score > 0.5
        
        # Adjust confidence based on agreement
        confidence_adjustment = 1.0 - conflict_analysis.conflict_severity * 0.3
        final_confidence = final_score * confidence_adjustment
        
        resolved_result = DetectionResult(
            blocked=final_prediction,
            confidence=final_confidence,
            stage=PipelineStage.CROSS_VALIDATION,
            guardrail_type=ensemble_result.guardrail_type,
            reasons=ensemble_result.reasons + [
                f"Conflict resolved via weighted majority (severity: {conflict_analysis.conflict_severity:.3f})"
            ],
            metadata={
                **ensemble_result.metadata,
                "conflict_resolution": {
                    "strategy": "weighted_majority",
                    "conflict_severity": conflict_analysis.conflict_severity,
                    "original_confidence": ensemble_result.confidence,
                    "resolution_confidence": conflict_analysis.resolution_confidence
                }
            },
            model_scores=ensemble_result.model_scores
        )
        
        return resolved_result
    
    async def _confidence_threshold_resolution(
        self,
        ensemble_result: DetectionResult,
        conflict_analysis: ConflictAnalysis
    ) -> DetectionResult:
        """Resolve using adaptive confidence thresholds"""
        
        scores = list(ensemble_result.model_scores.values())
        
        # Adaptive threshold based on conflict severity
        base_threshold = self.config.confidence_threshold
        threshold_adjustment = conflict_analysis.conflict_severity * 0.1
        adaptive_threshold = base_threshold + threshold_adjustment
        
        # Count models above threshold
        high_confidence_models = [score for score in scores if score > adaptive_threshold]
        low_confidence_models = [score for score in scores if score <= (1.0 - adaptive_threshold)]
        
        if len(high_confidence_models) > len(low_confidence_models):
            final_prediction = True
            final_confidence = np.mean(high_confidence_models)
        elif len(low_confidence_models) > len(high_confidence_models):
            final_prediction = False
            final_confidence = 1.0 - np.mean(low_confidence_models)
        else:
            # Tie - use ensemble average
            final_prediction = np.mean(scores) > 0.5
            final_confidence = max(np.mean(scores), 1.0 - np.mean(scores))
        
        resolved_result = DetectionResult(
            blocked=final_prediction,
            confidence=final_confidence,
            stage=PipelineStage.CROSS_VALIDATION,
            guardrail_type=ensemble_result.guardrail_type,
            reasons=ensemble_result.reasons + [
                f"Conflict resolved via adaptive threshold ({adaptive_threshold:.3f})"
            ],
            metadata={
                **ensemble_result.metadata,
                "conflict_resolution": {
                    "strategy": "confidence_threshold",
                    "adaptive_threshold": adaptive_threshold,
                    "high_confidence_count": len(high_confidence_models),
                    "low_confidence_count": len(low_confidence_models)
                }
            },
            model_scores=ensemble_result.model_scores
        )
        
        return resolved_result
    
    async def _meta_classifier_resolution(
        self,
        text: str,
        guardrail_type: str,
        ensemble_result: DetectionResult,
        conflict_analysis: ConflictAnalysis
    ) -> DetectionResult:
        """Resolve using meta-classifier approach"""
        
        # For now, implement a simple rule-based meta-classifier
        # In production, this would be a trained model
        
        scores = list(ensemble_result.model_scores.values())
        
        # Meta-features for decision
        meta_features = {
            "score_mean": np.mean(scores),
            "score_std": np.std(scores),
            "score_range": max(scores) - min(scores),
            "text_length": len(text),
            "conflict_severity": conflict_analysis.conflict_severity
        }
        
        # Simple rule-based meta-classifier
        if meta_features["conflict_severity"] < 0.3:
            # Low conflict - trust ensemble mean
            final_confidence = meta_features["score_mean"]
            final_prediction = final_confidence > 0.5
        elif meta_features["score_std"] < 0.15:
            # Low variance but high conflict - conservative approach
            final_confidence = 0.6
            final_prediction = meta_features["score_mean"] > 0.6
        else:
            # High variance - use majority with penalty
            majority_vote = sum(1 for score in scores if score > 0.5) > len(scores) / 2
            final_prediction = majority_vote
            final_confidence = 0.7 if majority_vote else 0.3
        
        resolved_result = DetectionResult(
            blocked=final_prediction,
            confidence=final_confidence,
            stage=PipelineStage.CROSS_VALIDATION,
            guardrail_type=ensemble_result.guardrail_type,
            reasons=ensemble_result.reasons + [
                f"Conflict resolved via meta-classifier"
            ],
            metadata={
                **ensemble_result.metadata,
                "conflict_resolution": {
                    "strategy": "meta_classifier",
                    "meta_features": meta_features,
                    "decision_logic": "rule_based"
                }
            },
            model_scores=ensemble_result.model_scores
        )
        
        return resolved_result
    
    async def _bayesian_ensemble_resolution(
        self,
        ensemble_result: DetectionResult,
        conflict_analysis: ConflictAnalysis
    ) -> DetectionResult:
        """Resolve using Bayesian ensemble approach"""
        
        scores = list(ensemble_result.model_scores.values())
        
        # Bayesian Model Averaging (simplified)
        # Prior belief (can be adjusted based on domain knowledge)
        prior_prob = 0.5
        
        # Likelihood from each model (treat as independent)
        posterior_prob = prior_prob
        
        for score in scores:
            # Update posterior using Bayes' rule (simplified)
            likelihood = score if score > 0.5 else (1.0 - score)
            posterior_prob = (likelihood * posterior_prob) / (
                likelihood * posterior_prob + (1.0 - likelihood) * (1.0 - posterior_prob)
            )
        
        # Adjust for uncertainty
        uncertainty_penalty = conflict_analysis.uncertainty_score * 0.1
        final_confidence = max(0.1, posterior_prob - uncertainty_penalty)
        final_prediction = final_confidence > 0.5
        
        resolved_result = DetectionResult(
            blocked=final_prediction,
            confidence=final_confidence,
            stage=PipelineStage.CROSS_VALIDATION,
            guardrail_type=ensemble_result.guardrail_type,
            reasons=ensemble_result.reasons + [
                f"Conflict resolved via Bayesian ensemble"
            ],
            metadata={
                **ensemble_result.metadata,
                "conflict_resolution": {
                    "strategy": "bayesian_ensemble",
                    "posterior_probability": posterior_prob,
                    "uncertainty_penalty": uncertainty_penalty,
                    "prior_probability": prior_prob
                }
            },
            model_scores=ensemble_result.model_scores
        )
        
        return resolved_result
    
    async def _uncertainty_weighted_resolution(
        self,
        ensemble_result: DetectionResult,
        conflict_analysis: ConflictAnalysis
    ) -> DetectionResult:
        """Resolve using uncertainty-weighted voting"""
        
        scores = list(ensemble_result.model_scores.values())
        
        # Calculate uncertainty for each prediction
        uncertainties = []
        for score in scores:
            # Uncertainty is higher near 0.5 (decision boundary)
            uncertainty = 1.0 - abs(score - 0.5) * 2.0
            uncertainties.append(uncertainty)
        
        # Weight votes by inverse uncertainty
        weighted_sum = 0.0
        total_weight = 0.0
        
        for score, uncertainty in zip(scores, uncertainties):
            weight = 1.0 / (uncertainty + 0.01)  # Add small epsilon to avoid division by zero
            vote = 1.0 if score > 0.5 else 0.0
            weighted_sum += vote * weight
            total_weight += weight
        
        final_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        final_prediction = final_score > 0.5
        
        # Confidence adjusted by overall uncertainty
        overall_uncertainty = np.mean(uncertainties)
        final_confidence = final_score * (1.0 - overall_uncertainty * 0.3)
        
        resolved_result = DetectionResult(
            blocked=final_prediction,
            confidence=final_confidence,
            stage=PipelineStage.CROSS_VALIDATION,
            guardrail_type=ensemble_result.guardrail_type,
            reasons=ensemble_result.reasons + [
                f"Conflict resolved via uncertainty weighting"
            ],
            metadata={
                **ensemble_result.metadata,
                "conflict_resolution": {
                    "strategy": "uncertainty_weighting",
                    "overall_uncertainty": overall_uncertainty,
                    "model_uncertainties": uncertainties,
                    "uncertainty_weighted_score": final_score
                }
            },
            model_scores=ensemble_result.model_scores
        )
        
        return resolved_result
    
    async def _validate_confidence(
        self,
        ensemble_result: DetectionResult,
        text: str,
        context: PipelineContext
    ) -> DetectionResult:
        """Validate and potentially improve confidence when no conflict is detected"""
        
        # Simple confidence validation for now
        original_confidence = ensemble_result.confidence
        
        # Boost confidence if models are in strong agreement
        if ensemble_result.model_scores:
            scores = list(ensemble_result.model_scores.values())
            if len(scores) > 1:
                score_std = np.std(scores)
                if score_std < 0.1:  # Strong agreement
                    confidence_boost = min(0.1, (0.1 - score_std) * 2)
                    ensemble_result.confidence = min(0.99, original_confidence + confidence_boost)
                    self.validation_stats["confidence_improvements"] += 1
        
        ensemble_result.reasons.append("Confidence validated - no conflicts detected")
        return ensemble_result
    
    async def _bootstrap_validation(
        self,
        text: str,
        guardrail_type: str,
        resolved_result: DetectionResult,
        context: PipelineContext
    ) -> DetectionResult:
        """Apply bootstrap validation for additional confidence"""
        
        if not self.config.enable_bootstrap_validation:
            return resolved_result
        
        # Simplified bootstrap - would normally resample training data
        # For now, add small random noise to existing scores to simulate bootstrap
        
        original_scores = list(resolved_result.model_scores.values())
        bootstrap_predictions = []
        
        for _ in range(min(10, self.config.bootstrap_samples)):  # Limit for performance
            # Add small random noise to simulate bootstrap resampling
            noise = np.random.normal(0, 0.05, len(original_scores))
            noisy_scores = np.clip(np.array(original_scores) + noise, 0.0, 1.0)
            
            # Calculate bootstrap prediction
            bootstrap_pred = np.mean(noisy_scores) > 0.5
            bootstrap_predictions.append(bootstrap_pred)
        
        # Calculate bootstrap confidence
        bootstrap_agreement = np.mean(bootstrap_predictions)
        bootstrap_confidence = max(bootstrap_agreement, 1.0 - bootstrap_agreement)
        
        # Combine with original confidence
        combined_confidence = (resolved_result.confidence + bootstrap_confidence) / 2.0
        
        resolved_result.confidence = combined_confidence
        resolved_result.metadata["bootstrap_validation"] = {
            "bootstrap_samples": len(bootstrap_predictions),
            "bootstrap_agreement": bootstrap_agreement,
            "bootstrap_confidence": bootstrap_confidence
        }
        
        return resolved_result
    
    def _cluster_models_by_agreement(
        self,
        model_names: List[str],
        scores: List[float],
        threshold: float
    ) -> Dict[str, List[str]]:
        """Cluster models by their prediction agreement"""
        
        positive_models = []
        negative_models = []
        uncertain_models = []
        
        for name, score in zip(model_names, scores):
            if score > threshold + 0.1:
                positive_models.append(name)
            elif score < threshold - 0.1:
                negative_models.append(name)
            else:
                uncertain_models.append(name)
        
        return {
            "positive": positive_models,
            "negative": negative_models,
            "uncertain": uncertain_models
        }
    
    def _calculate_uncertainty_score(
        self,
        scores: List[float],
        ensemble_result: DetectionResult
    ) -> float:
        """Calculate overall uncertainty score"""
        
        if len(scores) < 2:
            return 0.0
        
        # Variance-based uncertainty
        variance_uncertainty = np.var(scores)
        
        # Boundary uncertainty (scores near 0.5)
        boundary_uncertainty = np.mean([abs(score - 0.5) for score in scores])
        boundary_uncertainty = 1.0 - (boundary_uncertainty * 2.0)  # Invert so higher = more uncertain
        
        # Combine uncertainties
        combined_uncertainty = (variance_uncertainty + boundary_uncertainty) / 2.0
        
        return min(1.0, combined_uncertainty)
    
    def _get_model_performance_weight(self, model_name: str) -> float:
        """Get historical performance weight for a model"""
        # Placeholder - would normally use historical performance data
        default_weights = {
            "unitary_toxic_bert": 1.2,
            "martin_ha_toxic": 1.1,
            "nicholaskluge_toxicity": 1.0,
            "custom_distilbert": 0.9
        }
        return default_weights.get(model_name, 1.0)
    
    def _update_validation_stats(self, processing_time: float, conflict_analysis: ConflictAnalysis):
        """Update validation performance statistics"""
        
        # Update average processing time
        total_validations = self.validation_stats["total_validations"]
        current_avg = self.validation_stats["average_processing_time"]
        
        if total_validations == 1:
            self.validation_stats["average_processing_time"] = processing_time
        else:
            self.validation_stats["average_processing_time"] = (
                (current_avg * (total_validations - 1) + processing_time) / total_validations
            )
    
    def _record_validation(
        self,
        text: str,
        original_result: DetectionResult,
        final_result: DetectionResult,
        conflict_analysis: ConflictAnalysis
    ):
        """Record validation for future analysis"""
        
        record = {
            "timestamp": time.time(),
            "text_hash": hash(text),
            "original_confidence": original_result.confidence,
            "final_confidence": final_result.confidence,
            "conflict_detected": conflict_analysis.conflict_detected,
            "conflict_severity": conflict_analysis.conflict_severity,
            "resolution_strategy": self.config.resolution_strategy.value
        }
        
        self.validation_history.append(record)
        
        # Keep only last 1000 records
        if len(self.validation_history) > 1000:
            self.validation_history.pop(0)
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get cross-validation performance statistics"""
        
        total_validations = self.validation_stats["total_validations"]
        conflicts_resolved = self.validation_stats["conflicts_resolved"]
        
        return {
            "total_validations": total_validations,
            "conflicts_resolved": conflicts_resolved,
            "conflict_rate": conflicts_resolved / total_validations if total_validations > 0 else 0,
            "confidence_improvements": self.validation_stats["confidence_improvements"],
            "average_processing_time_ms": self.validation_stats["average_processing_time"],
            "resolution_strategy": self.config.resolution_strategy.value,
            "recent_validation_count": len(self.validation_history)
        }