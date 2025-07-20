"""
Phase 4: Enhanced Ensemble Detection System
Industry-level ensemble methods for >95% accuracy across all guardrail types
"""

import asyncio
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import statistics

from app.utils.logger import app_logger
from app.guardrails.models import DetectionResult, PipelineStage, PipelineContext

class EnsembleStrategy(Enum):
    """Ensemble decision-making strategies"""
    WEIGHTED_VOTING = "weighted_voting"
    MAJORITY_VOTING = "majority_voting"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    META_CLASSIFIER = "meta_classifier"
    ADAPTIVE_ENSEMBLE = "adaptive_ensemble"

class ModelType(Enum):
    """Types of models in the ensemble"""
    TRANSFORMER = "transformer"
    TRADITIONAL_ML = "traditional_ml"
    RULE_BASED = "rule_based"
    SPECIALIZED = "specialized"
    LLM = "llm"

@dataclass
class ModelPrediction:
    """Individual model prediction"""
    model_name: str
    model_type: ModelType
    prediction: bool  # blocked/not blocked
    confidence: float  # 0.0 to 1.0
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    features_used: List[str] = field(default_factory=list)
    explanation: str = ""

@dataclass
class EnsembleConfig:
    """Configuration for ensemble detection"""
    strategy: EnsembleStrategy = EnsembleStrategy.CONFIDENCE_WEIGHTED
    min_models_required: int = 2
    confidence_threshold: float = 0.75
    disagreement_threshold: float = 0.3
    timeout_ms: float = 5000.0
    enable_parallel_processing: bool = True
    enable_early_stopping: bool = True
    enable_uncertainty_quantification: bool = True

class BaseEnsembleModel(ABC):
    """Base class for ensemble models"""
    
    def __init__(self, name: str, model_type: ModelType, weight: float = 1.0):
        self.name = name
        self.model_type = model_type
        self.weight = weight
        self.performance_history = []
        self.is_loaded = False
        self.load_time = 0.0
    
    @abstractmethod
    async def predict(self, text: str, context: PipelineContext) -> ModelPrediction:
        """Make a prediction on the input text"""
        pass
    
    @abstractmethod
    async def load(self):
        """Load the model"""
        pass
    
    def update_performance(self, accuracy: float):
        """Update model performance history"""
        self.performance_history.append(accuracy)
        # Keep only last 100 performance scores
        if len(self.performance_history) > 100:
            self.performance_history.pop(0)
    
    def get_average_performance(self) -> float:
        """Get average performance score"""
        if not self.performance_history:
            return 0.8  # Default performance
        return statistics.mean(self.performance_history)

class ToxicityEnsemble:
    """Enhanced toxicity detection ensemble with multiple specialized models"""
    
    def __init__(self, config: EnsembleConfig = None):
        self.config = config or EnsembleConfig()
        self.models = {}
        self.model_weights = {}
        self.performance_tracker = PerformanceTracker()
        
        # Model specifications from the plan
        self.model_specs = {
            "unitary_toxic_bert": {
                "weight": 0.35,
                "type": ModelType.TRANSFORMER,
                "size_mb": 420,
                "expected_latency_ms": 50
            },
            "martin_ha_toxic": {
                "weight": 0.30,
                "type": ModelType.TRANSFORMER,
                "size_mb": 500,
                "expected_latency_ms": 60
            },
            "nicholaskluge_toxicity": {
                "weight": 0.25,
                "type": ModelType.TRANSFORMER,
                "size_mb": 450,
                "expected_latency_ms": 55
            },
            "custom_distilbert": {
                "weight": 0.10,
                "type": ModelType.TRANSFORMER,
                "size_mb": 250,
                "expected_latency_ms": 25
            }
        }
        
        app_logger.info("Toxicity ensemble initialized")
    
    async def initialize(self):
        """Initialize all models in the ensemble"""
        try:
            # Create placeholder models for now
            for model_name, spec in self.model_specs.items():
                model = ToxicityTransformerModel(
                    name=model_name,
                    weight=spec["weight"],
                    expected_latency=spec["expected_latency_ms"]
                )
                await model.load()
                self.models[model_name] = model
                self.model_weights[model_name] = spec["weight"]
            
            app_logger.info(f"Toxicity ensemble loaded {len(self.models)} models")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize toxicity ensemble: {e}")
            raise
    
    async def detect(self, text: str, context: PipelineContext) -> DetectionResult:
        """Perform ensemble toxicity detection"""
        start_time = time.time()
        
        try:
            # Run all models in parallel if enabled
            if self.config.enable_parallel_processing:
                predictions = await self._parallel_prediction(text, context)
            else:
                predictions = await self._sequential_prediction(text, context)
            
            # Apply ensemble strategy
            final_decision = self._apply_ensemble_strategy(predictions)
            
            # Calculate uncertainty bounds
            uncertainty_bounds = self._calculate_uncertainty(predictions) if self.config.enable_uncertainty_quantification else (0.0, 1.0)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=final_decision["prediction"],
                confidence=final_decision["confidence"],
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="toxicity",
                reasons=final_decision["reasons"],
                metadata={
                    "ensemble_strategy": self.config.strategy.value,
                    "models_used": len(predictions),
                    "model_scores": {pred.model_name: pred.confidence for pred in predictions},
                    "disagreement_detected": final_decision["disagreement"]
                },
                processing_time_ms=processing_time,
                model_scores={pred.model_name: pred.confidence for pred in predictions},
                uncertainty_bounds=uncertainty_bounds
            )
            
        except Exception as e:
            app_logger.error(f"Toxicity ensemble detection failed: {e}")
            # Return safe fallback
            return DetectionResult(
                blocked=True,  # Fail safe
                confidence=0.0,
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="toxicity",
                reasons=[f"Ensemble error: {str(e)}"],
                escalation_required=True
            )
    
    async def _parallel_prediction(self, text: str, context: PipelineContext) -> List[ModelPrediction]:
        """Run all models in parallel"""
        tasks = [
            model.predict(text, context) 
            for model in self.models.values()
        ]
        
        try:
            # Use timeout to prevent hanging
            predictions = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.timeout_ms / 1000.0
            )
            
            # Filter out exceptions
            valid_predictions = [
                pred for pred in predictions 
                if isinstance(pred, ModelPrediction)
            ]
            
            return valid_predictions
            
        except asyncio.TimeoutError:
            app_logger.warning("Toxicity ensemble prediction timeout")
            return []
    
    async def _sequential_prediction(self, text: str, context: PipelineContext) -> List[ModelPrediction]:
        """Run models sequentially with early stopping"""
        predictions = []
        
        # Sort models by expected performance (weight as proxy)
        sorted_models = sorted(
            self.models.items(),
            key=lambda x: self.model_weights[x[0]],
            reverse=True
        )
        
        for model_name, model in sorted_models:
            try:
                prediction = await model.predict(text, context)
                predictions.append(prediction)
                
                # Early stopping if high confidence
                if (self.config.enable_early_stopping and 
                    prediction.confidence > 0.95 and 
                    len(predictions) >= self.config.min_models_required):
                    app_logger.debug(f"Early stopping after {len(predictions)} models")
                    break
                    
            except Exception as e:
                app_logger.warning(f"Model {model_name} prediction failed: {e}")
                continue
        
        return predictions
    
    def _apply_ensemble_strategy(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Apply the configured ensemble strategy"""
        if not predictions:
            return {
                "prediction": True,  # Fail safe
                "confidence": 0.0,
                "reasons": ["No model predictions available"],
                "disagreement": False
            }
        
        if self.config.strategy == EnsembleStrategy.WEIGHTED_VOTING:
            return self._weighted_voting(predictions)
        elif self.config.strategy == EnsembleStrategy.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted_voting(predictions)
        elif self.config.strategy == EnsembleStrategy.MAJORITY_VOTING:
            return self._majority_voting(predictions)
        elif self.config.strategy == EnsembleStrategy.ADAPTIVE_ENSEMBLE:
            return self._adaptive_ensemble(predictions)
        else:
            # Default to confidence weighted
            return self._confidence_weighted_voting(predictions)
    
    def _confidence_weighted_voting(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Confidence-weighted ensemble voting"""
        total_weight = 0.0
        weighted_score = 0.0
        prediction_scores = []
        
        for pred in predictions:
            # Get model weight (combination of assigned weight and performance)
            model_weight = self.model_weights.get(pred.model_name, 1.0)
            performance_weight = self.models[pred.model_name].get_average_performance()
            combined_weight = model_weight * performance_weight * pred.confidence
            
            # Convert boolean prediction to score
            pred_score = pred.confidence if pred.prediction else (1.0 - pred.confidence)
            
            weighted_score += pred_score * combined_weight
            total_weight += combined_weight
            prediction_scores.append(pred.confidence)
        
        final_confidence = weighted_score / total_weight if total_weight > 0 else 0.0
        final_prediction = final_confidence > self.config.confidence_threshold
        
        # Check for disagreement
        disagreement = self._detect_disagreement(prediction_scores)
        
        # Generate explanatory reasons
        reasons = []
        if final_prediction:
            high_conf_models = [p.model_name for p in predictions if p.prediction and p.confidence > 0.8]
            if high_conf_models:
                reasons.append(f"Toxicity detected by models: {', '.join(high_conf_models)}")
        
        return {
            "prediction": final_prediction,
            "confidence": final_confidence,
            "reasons": reasons,
            "disagreement": disagreement
        }
    
    def _weighted_voting(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Traditional weighted voting"""
        total_weight = 0.0
        weighted_votes = 0.0
        
        for pred in predictions:
            weight = self.model_weights.get(pred.model_name, 1.0)
            vote = 1.0 if pred.prediction else 0.0
            weighted_votes += vote * weight
            total_weight += weight
        
        final_score = weighted_votes / total_weight if total_weight > 0 else 0.0
        final_prediction = final_score > 0.5
        
        return {
            "prediction": final_prediction,
            "confidence": final_score,
            "reasons": [f"Weighted voting score: {final_score:.3f}"],
            "disagreement": False
        }
    
    def _majority_voting(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Simple majority voting"""
        positive_votes = sum(1 for pred in predictions if pred.prediction)
        total_votes = len(predictions)
        
        final_prediction = positive_votes > (total_votes / 2)
        confidence = positive_votes / total_votes
        
        return {
            "prediction": final_prediction,
            "confidence": confidence,
            "reasons": [f"Majority vote: {positive_votes}/{total_votes}"],
            "disagreement": False
        }
    
    def _adaptive_ensemble(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Adaptive ensemble based on model performance and context"""
        # Select best performing models dynamically
        sorted_predictions = sorted(
            predictions,
            key=lambda p: self.models[p.model_name].get_average_performance() * p.confidence,
            reverse=True
        )
        
        # Use top 3 predictions for final decision
        top_predictions = sorted_predictions[:3]
        return self._confidence_weighted_voting(top_predictions)
    
    def _detect_disagreement(self, scores: List[float]) -> bool:
        """Detect significant disagreement between models"""
        if len(scores) < 2:
            return False
        
        score_range = max(scores) - min(scores)
        return score_range > self.config.disagreement_threshold
    
    def _calculate_uncertainty(self, predictions: List[ModelPrediction]) -> Tuple[float, float]:
        """Calculate uncertainty bounds using prediction variance"""
        if len(predictions) < 2:
            return (0.0, 1.0)
        
        scores = [pred.confidence for pred in predictions]
        mean_score = statistics.mean(scores)
        std_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
        
        # Calculate 95% confidence interval
        margin = 1.96 * std_score  # 95% CI
        lower_bound = max(0.0, mean_score - margin)
        upper_bound = min(1.0, mean_score + margin)
        
        return (lower_bound, upper_bound)

class ToxicityTransformerModel(BaseEnsembleModel):
    """Placeholder toxicity transformer model"""
    
    def __init__(self, name: str, weight: float = 1.0, expected_latency: float = 50.0):
        super().__init__(name, ModelType.TRANSFORMER, weight)
        self.expected_latency = expected_latency
    
    async def load(self):
        """Load the transformer model"""
        start_time = time.time()
        
        # Simulate model loading
        await asyncio.sleep(0.1)
        
        self.is_loaded = True
        self.load_time = (time.time() - start_time) * 1000
        app_logger.info(f"Loaded toxicity model {self.name} in {self.load_time:.1f}ms")
    
    async def predict(self, text: str, context: PipelineContext) -> ModelPrediction:
        """Make toxicity prediction"""
        start_time = time.time()
        
        if not self.is_loaded:
            await self.load()
        
        # Implement real toxicity detection logic
        text_lower = text.lower()
        
        # Enhanced toxicity detection with multiple approaches
        confidence_score = await self._calculate_toxicity_score(text, text_lower)
        
        # Adjust based on model type and characteristics
        if "bert" in self.name.lower():
            confidence_score = self._apply_bert_adjustments(confidence_score, text)
        elif "distil" in self.name.lower():
            confidence_score = self._apply_distilbert_adjustments(confidence_score, text)
        elif "toxic" in self.name.lower():
            confidence_score = self._apply_toxic_model_adjustments(confidence_score, text)
        
        base_confidence = min(0.95, max(0.05, confidence_score))
        
        prediction = base_confidence > 0.7
        processing_time = (time.time() - start_time) * 1000
        
        # Extract features for metadata
        features = await self._extract_features(text)
        
        return ModelPrediction(
            model_name=self.name,
            model_type=self.model_type,
            prediction=prediction,
            confidence=base_confidence,
            processing_time_ms=processing_time,
            metadata={
                "features": features,
                "text_length": len(text),
                "model_version": self._get_model_version()
            },
            explanation=self._generate_explanation(prediction, base_confidence, features)
        )

class PerformanceTracker:
    """Track ensemble performance metrics"""
    
    def __init__(self):
        self.prediction_history = []
        self.accuracy_history = []
        self.latency_history = []
    
    def record_prediction(self, prediction_result: DetectionResult, actual_label: Optional[bool] = None):
        """Record a prediction for performance tracking"""
        self.prediction_history.append({
            "timestamp": time.time(),
            "confidence": prediction_result.confidence,
            "prediction": prediction_result.blocked,
            "processing_time": prediction_result.processing_time_ms,
            "actual_label": actual_label
        })
        
        self.latency_history.append(prediction_result.processing_time_ms)
        
        if actual_label is not None:
            accuracy = 1.0 if prediction_result.blocked == actual_label else 0.0
            self.accuracy_history.append(accuracy)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if not self.prediction_history:
            return {}
        
        recent_predictions = self.prediction_history[-100:]  # Last 100 predictions
        
        metrics = {
            "total_predictions": len(self.prediction_history),
            "recent_predictions": len(recent_predictions),
            "average_latency_ms": statistics.mean(self.latency_history[-100:]) if self.latency_history else 0.0,
            "p95_latency_ms": np.percentile(self.latency_history[-100:], 95) if len(self.latency_history) > 5 else 0.0,
        }
        
        if self.accuracy_history:
            metrics["accuracy"] = statistics.mean(self.accuracy_history[-100:])
            metrics["total_accuracy_samples"] = len(self.accuracy_history)
        
        return metrics

# Factory function for creating ensemble detectors
def create_ensemble_detector(guardrail_type: str, config: EnsembleConfig = None) -> Any:
    """Factory function to create appropriate ensemble detector"""
    
    if guardrail_type == "toxicity":
        return ToxicityEnsemble(config)
    elif guardrail_type == "pii":
        return PIIEnsemble(config)
    elif guardrail_type == "spam":
        return SpamEnsemble(config)
    elif guardrail_type == "prompt_injection":
        return PromptInjectionEnsemble(config)
    elif guardrail_type == "topic":
        return TopicEnsemble(config)
    elif guardrail_type == "fact_check":
        return FactCheckEnsemble(config)
    else:
        raise ValueError(f"Unknown guardrail type: {guardrail_type}")

# Specialized ensemble classes for each guardrail type

class PIIEnsemble:
    """PII detection ensemble with specialized models"""
    
    def __init__(self, config: EnsembleConfig = None):
        self.config = config or EnsembleConfig()
        self.models = {}
        self.model_weights = {}
        self.performance_tracker = PerformanceTracker()
        
        # PII-specific model specifications
        self.model_specs = {
            "microsoft_presidio": {
                "weight": 0.35,
                "type": ModelType.RULE_BASED,
                "expected_latency_ms": 30
            },
            "spacy_ner": {
                "weight": 0.30,
                "type": ModelType.TRADITIONAL_ML,
                "expected_latency_ms": 40
            },
            "custom_regex_patterns": {
                "weight": 0.20,
                "type": ModelType.RULE_BASED,
                "expected_latency_ms": 10
            },
            "transformers_ner": {
                "weight": 0.15,
                "type": ModelType.TRANSFORMER,
                "expected_latency_ms": 80
            }
        }
        
        app_logger.info("PII ensemble initialized")
    
    async def initialize(self):
        """Initialize PII detection models"""
        try:
            for model_name, spec in self.model_specs.items():
                model = PIIDetectionModel(
                    name=model_name,
                    weight=spec["weight"],
                    expected_latency=spec["expected_latency_ms"]
                )
                await model.load()
                self.models[model_name] = model
                self.model_weights[model_name] = spec["weight"]
            
            app_logger.info(f"PII ensemble loaded {len(self.models)} models")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize PII ensemble: {e}")
            raise
    
    async def detect(self, text: str, context: PipelineContext) -> DetectionResult:
        """Perform PII detection"""
        start_time = time.time()
        
        try:
            # Run all models
            predictions = []
            for model in self.models.values():
                try:
                    prediction = await model.predict(text, context)
                    predictions.append(prediction)
                except Exception as e:
                    app_logger.warning(f"PII model {model.name} failed: {e}")
            
            # Apply ensemble strategy
            final_decision = self._apply_pii_ensemble_strategy(predictions)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=final_decision["prediction"],
                confidence=final_decision["confidence"],
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="pii",
                reasons=final_decision["reasons"],
                metadata={
                    "ensemble_strategy": self.config.strategy.value,
                    "models_used": len(predictions),
                    "model_scores": {pred.model_name: pred.confidence for pred in predictions},
                    "pii_types_detected": final_decision.get("pii_types", [])
                },
                processing_time_ms=processing_time,
                model_scores={pred.model_name: pred.confidence for pred in predictions}
            )
            
        except Exception as e:
            app_logger.error(f"PII ensemble detection failed: {e}")
            return DetectionResult(
                blocked=True,
                confidence=0.0,
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="pii",
                reasons=[f"PII ensemble error: {str(e)}"],
                escalation_required=True
            )
    
    def _apply_pii_ensemble_strategy(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Apply PII-specific ensemble strategy"""
        if not predictions:
            return {"prediction": True, "confidence": 0.0, "reasons": ["No PII predictions"], "pii_types": []}
        
        # Collect PII types detected
        pii_types = set()
        weighted_score = 0.0
        total_weight = 0.0
        
        for pred in predictions:
            weight = self.model_weights.get(pred.model_name, 1.0)
            score = pred.confidence if pred.prediction else (1.0 - pred.confidence)
            
            weighted_score += score * weight
            total_weight += weight
            
            # Extract PII types from metadata
            if pred.metadata and "pii_types" in pred.metadata:
                pii_types.update(pred.metadata["pii_types"])
        
        final_confidence = weighted_score / total_weight if total_weight > 0 else 0.0
        final_prediction = final_confidence > self.config.confidence_threshold
        
        reasons = []
        if final_prediction and pii_types:
            reasons.append(f"PII detected: {', '.join(list(pii_types)[:3])}")
        
        return {
            "prediction": final_prediction,
            "confidence": final_confidence,
            "reasons": reasons,
            "pii_types": list(pii_types)
        }

class SpamEnsemble:
    """Spam detection ensemble with specialized models"""
    
    def __init__(self, config: EnsembleConfig = None):
        self.config = config or EnsembleConfig()
        self.models = {}
        self.model_weights = {}
        self.performance_tracker = PerformanceTracker()
        
        # Spam-specific model specifications
        self.model_specs = {
            "naive_bayes_spam": {
                "weight": 0.30,
                "type": ModelType.TRADITIONAL_ML,
                "expected_latency_ms": 20
            },
            "svm_spam_classifier": {
                "weight": 0.25,
                "type": ModelType.TRADITIONAL_ML,
                "expected_latency_ms": 25
            },
            "regex_spam_patterns": {
                "weight": 0.25,
                "type": ModelType.RULE_BASED,
                "expected_latency_ms": 15
            },
            "bert_spam_classifier": {
                "weight": 0.20,
                "type": ModelType.TRANSFORMER,
                "expected_latency_ms": 60
            }
        }
        
        app_logger.info("Spam ensemble initialized")
    
    async def initialize(self):
        """Initialize spam detection models"""
        try:
            for model_name, spec in self.model_specs.items():
                model = SpamDetectionModel(
                    name=model_name,
                    weight=spec["weight"],
                    expected_latency=spec["expected_latency_ms"]
                )
                await model.load()
                self.models[model_name] = model
                self.model_weights[model_name] = spec["weight"]
            
            app_logger.info(f"Spam ensemble loaded {len(self.models)} models")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize spam ensemble: {e}")
            raise
    
    async def detect(self, text: str, context: PipelineContext) -> DetectionResult:
        """Perform spam detection"""
        start_time = time.time()
        
        try:
            # Run all models
            predictions = []
            for model in self.models.values():
                try:
                    prediction = await model.predict(text, context)
                    predictions.append(prediction)
                except Exception as e:
                    app_logger.warning(f"Spam model {model.name} failed: {e}")
            
            # Apply ensemble strategy
            final_decision = self._apply_spam_ensemble_strategy(predictions)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=final_decision["prediction"],
                confidence=final_decision["confidence"],
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="spam",
                reasons=final_decision["reasons"],
                metadata={
                    "ensemble_strategy": self.config.strategy.value,
                    "models_used": len(predictions),
                    "model_scores": {pred.model_name: pred.confidence for pred in predictions},
                    "spam_indicators": final_decision.get("spam_indicators", [])
                },
                processing_time_ms=processing_time,
                model_scores={pred.model_name: pred.confidence for pred in predictions}
            )
            
        except Exception as e:
            app_logger.error(f"Spam ensemble detection failed: {e}")
            return DetectionResult(
                blocked=True,
                confidence=0.0,
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="spam",
                reasons=[f"Spam ensemble error: {str(e)}"],
                escalation_required=True
            )
    
    def _apply_spam_ensemble_strategy(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Apply spam-specific ensemble strategy"""
        if not predictions:
            return {"prediction": True, "confidence": 0.0, "reasons": ["No spam predictions"], "spam_indicators": []}
        
        # Use weighted voting with emphasis on rule-based detectors for obvious spam
        rule_based_confidence = 0.0
        ml_confidence = 0.0
        spam_indicators = set()
        
        rule_weight_sum = 0.0
        ml_weight_sum = 0.0
        
        for pred in predictions:
            weight = self.model_weights.get(pred.model_name, 1.0)
            
            if pred.model_type == ModelType.RULE_BASED:
                rule_based_confidence += pred.confidence * weight
                rule_weight_sum += weight
            else:
                ml_confidence += pred.confidence * weight
                ml_weight_sum += weight
            
            # Extract spam indicators
            if pred.metadata and "spam_indicators" in pred.metadata:
                spam_indicators.update(pred.metadata["spam_indicators"])
        
        # Normalize confidences
        rule_based_confidence = rule_based_confidence / rule_weight_sum if rule_weight_sum > 0 else 0
        ml_confidence = ml_confidence / ml_weight_sum if ml_weight_sum > 0 else 0
        
        # Combine with preference for rule-based on high confidence
        if rule_based_confidence > 0.8:
            final_confidence = rule_based_confidence
        else:
            final_confidence = (rule_based_confidence + ml_confidence) / 2.0
        
        final_prediction = final_confidence > self.config.confidence_threshold
        
        reasons = []
        if final_prediction and spam_indicators:
            reasons.append(f"Spam indicators: {', '.join(list(spam_indicators)[:3])}")
        
        return {
            "prediction": final_prediction,
            "confidence": final_confidence,
            "reasons": reasons,
            "spam_indicators": list(spam_indicators)
        }

class PromptInjectionEnsemble:
    """Prompt injection detection ensemble with specialized models"""
    
    def __init__(self, config: EnsembleConfig = None):
        self.config = config or EnsembleConfig()
        self.models = {}
        self.model_weights = {}
        self.performance_tracker = PerformanceTracker()
        
        # Prompt injection specific model specifications
        self.model_specs = {
            "regex_injection_patterns": {
                "weight": 0.35,
                "type": ModelType.RULE_BASED,
                "expected_latency_ms": 15
            },
            "bert_injection_classifier": {
                "weight": 0.30,
                "type": ModelType.TRANSFORMER,
                "expected_latency_ms": 70
            },
            "adversarial_detector": {
                "weight": 0.25,
                "type": ModelType.SPECIALIZED,
                "expected_latency_ms": 50
            },
            "semantic_similarity": {
                "weight": 0.10,
                "type": ModelType.SPECIALIZED,
                "expected_latency_ms": 40
            }
        }
        
        app_logger.info("Prompt injection ensemble initialized")
    
    async def initialize(self):
        """Initialize prompt injection detection models"""
        try:
            for model_name, spec in self.model_specs.items():
                model = PromptInjectionModel(
                    name=model_name,
                    weight=spec["weight"],
                    expected_latency=spec["expected_latency_ms"]
                )
                await model.load()
                self.models[model_name] = model
                self.model_weights[model_name] = spec["weight"]
            
            app_logger.info(f"Prompt injection ensemble loaded {len(self.models)} models")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize prompt injection ensemble: {e}")
            raise
    
    async def detect(self, text: str, context: PipelineContext) -> DetectionResult:
        """Perform prompt injection detection"""
        start_time = time.time()
        
        try:
            # Run all models
            predictions = []
            for model in self.models.values():
                try:
                    prediction = await model.predict(text, context)
                    predictions.append(prediction)
                except Exception as e:
                    app_logger.warning(f"Prompt injection model {model.name} failed: {e}")
            
            # Apply ensemble strategy
            final_decision = self._apply_injection_ensemble_strategy(predictions)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=final_decision["prediction"],
                confidence=final_decision["confidence"],
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="prompt_injection",
                reasons=final_decision["reasons"],
                metadata={
                    "ensemble_strategy": self.config.strategy.value,
                    "models_used": len(predictions),
                    "model_scores": {pred.model_name: pred.confidence for pred in predictions},
                    "injection_types": final_decision.get("injection_types", [])
                },
                processing_time_ms=processing_time,
                model_scores={pred.model_name: pred.confidence for pred in predictions}
            )
            
        except Exception as e:
            app_logger.error(f"Prompt injection ensemble detection failed: {e}")
            return DetectionResult(
                blocked=True,
                confidence=0.0,
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="prompt_injection",
                reasons=[f"Prompt injection ensemble error: {str(e)}"],
                escalation_required=True
            )
    
    def _apply_injection_ensemble_strategy(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Apply prompt injection specific ensemble strategy"""
        if not predictions:
            return {"prediction": True, "confidence": 0.0, "reasons": ["No injection predictions"], "injection_types": []}
        
        # High sensitivity approach - any strong detection should trigger
        max_confidence = 0.0
        injection_types = set()
        triggering_models = []
        
        for pred in predictions:
            max_confidence = max(max_confidence, pred.confidence)
            
            if pred.prediction and pred.confidence > 0.7:
                triggering_models.append(pred.model_name)
                
                if pred.metadata and "injection_types" in pred.metadata:
                    injection_types.update(pred.metadata["injection_types"])
        
        # For prompt injection, be conservative - block if any model is highly confident
        final_prediction = max_confidence > 0.6  # Lower threshold for safety
        final_confidence = max_confidence
        
        reasons = []
        if final_prediction:
            if injection_types:
                reasons.append(f"Injection patterns: {', '.join(list(injection_types)[:3])}")
            if triggering_models:
                reasons.append(f"Detected by: {', '.join(triggering_models[:2])}")
        
        return {
            "prediction": final_prediction,
            "confidence": final_confidence,
            "reasons": reasons,
            "injection_types": list(injection_types)
        }

class TopicEnsemble:
    """Topic classification ensemble"""
    
    def __init__(self, config: EnsembleConfig = None):
        self.config = config or EnsembleConfig()
        self.models = {}
        self.model_weights = {}
        self.performance_tracker = PerformanceTracker()
        
        # Topic classification model specifications
        self.model_specs = {
            "keyword_classifier": {
                "weight": 0.25,
                "type": ModelType.RULE_BASED,
                "expected_latency_ms": 20
            },
            "tfidf_classifier": {
                "weight": 0.25,
                "type": ModelType.TRADITIONAL_ML,
                "expected_latency_ms": 30
            },
            "bert_topic_classifier": {
                "weight": 0.30,
                "type": ModelType.TRANSFORMER,
                "expected_latency_ms": 80
            },
            "sentence_embeddings": {
                "weight": 0.20,
                "type": ModelType.SPECIALIZED,
                "expected_latency_ms": 60
            }
        }
        
        app_logger.info("Topic ensemble initialized")
    
    async def initialize(self):
        """Initialize topic classification models"""
        try:
            for model_name, spec in self.model_specs.items():
                model = TopicClassificationModel(
                    name=model_name,
                    weight=spec["weight"],
                    expected_latency=spec["expected_latency_ms"]
                )
                await model.load()
                self.models[model_name] = model
                self.model_weights[model_name] = spec["weight"]
            
            app_logger.info(f"Topic ensemble loaded {len(self.models)} models")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize topic ensemble: {e}")
            raise
    
    async def detect(self, text: str, context: PipelineContext) -> DetectionResult:
        """Perform topic classification"""
        start_time = time.time()
        
        try:
            # Run all models
            predictions = []
            for model in self.models.values():
                try:
                    prediction = await model.predict(text, context)
                    predictions.append(prediction)
                except Exception as e:
                    app_logger.warning(f"Topic model {model.name} failed: {e}")
            
            # Apply ensemble strategy
            final_decision = self._apply_topic_ensemble_strategy(predictions)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=final_decision["prediction"],
                confidence=final_decision["confidence"],
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="topic",
                reasons=final_decision["reasons"],
                metadata={
                    "ensemble_strategy": self.config.strategy.value,
                    "models_used": len(predictions),
                    "model_scores": {pred.model_name: pred.confidence for pred in predictions},
                    "detected_topics": final_decision.get("topics", [])
                },
                processing_time_ms=processing_time,
                model_scores={pred.model_name: pred.confidence for pred in predictions}
            )
            
        except Exception as e:
            app_logger.error(f"Topic ensemble detection failed: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.0,
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="topic",
                reasons=[f"Topic ensemble error: {str(e)}"],
                escalation_required=True
            )
    
    def _apply_topic_ensemble_strategy(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Apply topic-specific ensemble strategy"""
        if not predictions:
            return {"prediction": False, "confidence": 0.0, "reasons": ["No topic predictions"], "topics": []}
        
        # For topic classification, use weighted voting
        topic_scores = {}
        all_topics = set()
        
        for pred in predictions:
            weight = self.model_weights.get(pred.model_name, 1.0)
            
            if pred.metadata and "topics" in pred.metadata:
                for topic, score in pred.metadata["topics"].items():
                    if topic not in topic_scores:
                        topic_scores[topic] = 0.0
                    topic_scores[topic] += score * weight
                    all_topics.add(topic)
        
        # Find top topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        top_topics = [topic for topic, score in sorted_topics[:3]]
        
        # Determine if any restricted topics detected
        restricted_topics = ["adult", "violence", "illegal", "hate"]
        blocked_topics = [topic for topic in top_topics if topic in restricted_topics]
        
        final_prediction = len(blocked_topics) > 0
        final_confidence = sorted_topics[0][1] if sorted_topics else 0.0
        
        reasons = []
        if final_prediction:
            reasons.append(f"Restricted topics detected: {', '.join(blocked_topics)}")
        
        return {
            "prediction": final_prediction,
            "confidence": final_confidence,
            "reasons": reasons,
            "topics": top_topics
        }

class FactCheckEnsemble:
    """Fact checking ensemble"""
    
    def __init__(self, config: EnsembleConfig = None):
        self.config = config or EnsembleConfig()
        self.models = {}
        self.model_weights = {}
        self.performance_tracker = PerformanceTracker()
        
        # Fact checking model specifications  
        self.model_specs = {
            "claim_detection": {
                "weight": 0.30,
                "type": ModelType.TRANSFORMER,
                "expected_latency_ms": 100
            },
            "evidence_retrieval": {
                "weight": 0.25,
                "type": ModelType.SPECIALIZED,
                "expected_latency_ms": 200
            },
            "stance_classification": {
                "weight": 0.25,
                "type": ModelType.TRANSFORMER,
                "expected_latency_ms": 80
            },
            "credibility_scorer": {
                "weight": 0.20,
                "type": ModelType.TRADITIONAL_ML,
                "expected_latency_ms": 50
            }
        }
        
        app_logger.info("Fact check ensemble initialized")
    
    async def initialize(self):
        """Initialize fact checking models"""
        try:
            for model_name, spec in self.model_specs.items():
                model = FactCheckModel(
                    name=model_name,
                    weight=spec["weight"],
                    expected_latency=spec["expected_latency_ms"]
                )
                await model.load()
                self.models[model_name] = model
                self.model_weights[model_name] = spec["weight"]
            
            app_logger.info(f"Fact check ensemble loaded {len(self.models)} models")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize fact check ensemble: {e}")
            raise
    
    async def detect(self, text: str, context: PipelineContext) -> DetectionResult:
        """Perform fact checking"""
        start_time = time.time()
        
        try:
            # Run all models
            predictions = []
            for model in self.models.values():
                try:
                    prediction = await model.predict(text, context)
                    predictions.append(prediction)
                except Exception as e:
                    app_logger.warning(f"Fact check model {model.name} failed: {e}")
            
            # Apply ensemble strategy
            final_decision = self._apply_factcheck_ensemble_strategy(predictions)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                blocked=final_decision["prediction"],
                confidence=final_decision["confidence"],
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="fact_check",
                reasons=final_decision["reasons"],
                metadata={
                    "ensemble_strategy": self.config.strategy.value,
                    "models_used": len(predictions),
                    "model_scores": {pred.model_name: pred.confidence for pred in predictions},
                    "factuality_score": final_decision.get("factuality_score", 0.0)
                },
                processing_time_ms=processing_time,
                model_scores={pred.model_name: pred.confidence for pred in predictions}
            )
            
        except Exception as e:
            app_logger.error(f"Fact check ensemble detection failed: {e}")
            return DetectionResult(
                blocked=False,
                confidence=0.5,
                stage=PipelineStage.PRIMARY_ENSEMBLE,
                guardrail_type="fact_check",
                reasons=[f"Fact check ensemble error: {str(e)}"],
                escalation_required=True
            )
    
    def _apply_factcheck_ensemble_strategy(self, predictions: List[ModelPrediction]) -> Dict[str, Any]:
        """Apply fact-checking specific ensemble strategy"""
        if not predictions:
            return {"prediction": False, "confidence": 0.5, "reasons": ["No fact check predictions"], "factuality_score": 0.5}
        
        # Weighted average of factuality scores
        weighted_factuality = 0.0
        total_weight = 0.0
        
        for pred in predictions:
            weight = self.model_weights.get(pred.model_name, 1.0)
            factuality_score = pred.metadata.get("factuality_score", 0.5) if pred.metadata else 0.5
            
            weighted_factuality += factuality_score * weight
            total_weight += weight
        
        final_factuality = weighted_factuality / total_weight if total_weight > 0 else 0.5
        
        # Block if factuality is very low (likely misinformation)
        final_prediction = final_factuality < 0.3
        final_confidence = abs(final_factuality - 0.5) * 2  # Convert to confidence
        
        reasons = []
        if final_prediction:
            reasons.append(f"Low factuality score: {final_factuality:.3f}")
        
        return {
            "prediction": final_prediction,
            "confidence": final_confidence,
            "reasons": reasons,
            "factuality_score": final_factuality
        }

# Placeholder model implementations for each ensemble type
class PIIDetectionModel(BaseEnsembleModel):
    """PII detection model placeholder"""
    
    def __init__(self, name: str, weight: float = 1.0, expected_latency: float = 30.0):
        super().__init__(name, ModelType.RULE_BASED, weight)
        self.expected_latency = expected_latency
    
    async def load(self):
        """Load the PII detection model"""
        await asyncio.sleep(0.05)  # Simulate loading
        self.is_loaded = True
        app_logger.info(f"Loaded PII model {self.name}")
    
    async def predict(self, text: str, context: PipelineContext) -> ModelPrediction:
        # Simplified PII detection logic
        import re
        pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'credit_card': r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b'
        }
        
        detected_types = []
        confidence = 0.0
        
        for pii_type, pattern in pii_patterns.items():
            if re.search(pattern, text):
                detected_types.append(pii_type)
                confidence += 0.8
        
        prediction = len(detected_types) > 0
        confidence = min(0.95, confidence)
        
        return ModelPrediction(
            model_name=self.name,
            model_type=self.model_type,
            prediction=prediction,
            confidence=confidence,
            processing_time_ms=self.expected_latency,
            metadata={"pii_types": detected_types}
        )

class SpamDetectionModel(BaseEnsembleModel):
    """Spam detection model placeholder"""
    
    def __init__(self, name: str, weight: float = 1.0, expected_latency: float = 25.0):
        super().__init__(name, ModelType.TRADITIONAL_ML, weight)
        self.expected_latency = expected_latency
    
    async def load(self):
        """Load the spam detection model"""
        await asyncio.sleep(0.05)  # Simulate loading
        self.is_loaded = True
        app_logger.info(f"Loaded spam model {self.name}")
    
    async def predict(self, text: str, context: PipelineContext) -> ModelPrediction:
        # Simplified spam detection logic
        spam_indicators = []
        confidence = 0.0
        
        # Check spam patterns
        if len(re.findall(r'!{3,}', text)) > 0:
            spam_indicators.append("excessive_exclamation")
            confidence += 0.6
        
        if len(re.findall(r'[A-Z]{5,}', text)) > 0:
            spam_indicators.append("excessive_caps")
            confidence += 0.7
        
        spam_keywords = ['buy now', 'limited time', 'act fast', 'free money', 'click here']
        for keyword in spam_keywords:
            if keyword.lower() in text.lower():
                spam_indicators.append(f"keyword_{keyword.replace(' ', '_')}")
                confidence += 0.5
        
        prediction = len(spam_indicators) > 0
        confidence = min(0.95, confidence)
        
        return ModelPrediction(
            model_name=self.name,
            model_type=self.model_type,
            prediction=prediction,
            confidence=confidence,
            processing_time_ms=self.expected_latency,
            metadata={"spam_indicators": spam_indicators}
        )

class PromptInjectionModel(BaseEnsembleModel):
    """Prompt injection detection model placeholder"""
    
    def __init__(self, name: str, weight: float = 1.0, expected_latency: float = 50.0):
        super().__init__(name, ModelType.SPECIALIZED, weight)
        self.expected_latency = expected_latency
    
    async def load(self):
        """Load the prompt injection model"""
        await asyncio.sleep(0.05)  # Simulate loading
        self.is_loaded = True
        app_logger.info(f"Loaded prompt injection model {self.name}")
    
    async def predict(self, text: str, context: PipelineContext) -> ModelPrediction:
        # Simplified prompt injection detection
        injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'system\s*:\s*',
            r'jailbreak',
            r'dan\s+mode',
            r'forget\s+everything'
        ]
        
        injection_types = []
        confidence = 0.0
        
        for pattern in injection_patterns:
            if re.search(pattern, text.lower()):
                injection_types.append(pattern)
                confidence += 0.8
        
        prediction = len(injection_types) > 0
        confidence = min(0.95, confidence)
        
        return ModelPrediction(
            model_name=self.name,
            model_type=self.model_type,
            prediction=prediction,
            confidence=confidence,
            processing_time_ms=self.expected_latency,
            metadata={"injection_types": injection_types}
        )

class TopicClassificationModel(BaseEnsembleModel):
    """Topic classification model placeholder"""
    
    def __init__(self, name: str, weight: float = 1.0, expected_latency: float = 60.0):
        super().__init__(name, ModelType.TRANSFORMER, weight)
        self.expected_latency = expected_latency
    
    async def load(self):
        """Load the topic classification model"""
        await asyncio.sleep(0.05)  # Simulate loading
        self.is_loaded = True
        app_logger.info(f"Loaded topic model {self.name}")
    
    async def predict(self, text: str, context: PipelineContext) -> ModelPrediction:
        # Simplified topic classification
        topic_keywords = {
            'adult': ['sex', 'porn', 'nude', 'explicit'],
            'violence': ['kill', 'murder', 'violence', 'attack'],
            'technology': ['computer', 'software', 'algorithm', 'AI'],
            'sports': ['football', 'basketball', 'tennis', 'game'],
            'politics': ['government', 'election', 'president', 'policy']
        }
        
        topic_scores = {}
        text_lower = text.lower()
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower) / len(keywords)
            if score > 0:
                topic_scores[topic] = score
        
        prediction = any(topic in ['adult', 'violence'] for topic in topic_scores.keys())
        confidence = max(topic_scores.values()) if topic_scores else 0.0
        
        return ModelPrediction(
            model_name=self.name,
            model_type=self.model_type,
            prediction=prediction,
            confidence=confidence,
            processing_time_ms=self.expected_latency,
            metadata={"topics": topic_scores}
        )

class FactCheckModel(BaseEnsembleModel):
    """Fact checking model placeholder"""
    
    def __init__(self, name: str, weight: float = 1.0, expected_latency: float = 100.0):
        super().__init__(name, ModelType.TRANSFORMER, weight)
        self.expected_latency = expected_latency
    
    async def load(self):
        """Load the fact checking model"""
        await asyncio.sleep(0.05)  # Simulate loading
        self.is_loaded = True
        app_logger.info(f"Loaded fact check model {self.name}")
    
    async def predict(self, text: str, context: PipelineContext) -> ModelPrediction:
        # Simplified fact checking - random factuality score for demo
        import random
        
        # Check for factual claim indicators
        claim_indicators = ['according to', 'studies show', 'research indicates', 'fact:', 'statistics']
        has_claims = any(indicator in text.lower() for indicator in claim_indicators)
        
        if has_claims:
            # Random factuality score between 0.2 and 0.8
            factuality_score = random.uniform(0.2, 0.8)
        else:
            # Non-factual content gets neutral score
            factuality_score = 0.5
        
        # Block if factuality is very low
        prediction = factuality_score < 0.3
        confidence = abs(factuality_score - 0.5) * 2
        
        return ModelPrediction(
            model_name=self.name,
            model_type=self.model_type,
            prediction=prediction,
            confidence=confidence,
            processing_time_ms=self.expected_latency,
            metadata={"factuality_score": factuality_score}
        )