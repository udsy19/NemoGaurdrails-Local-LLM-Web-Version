"""
A/B Testing Framework for Phase 3
Provides experiment management, variant allocation, and results tracking
"""

import uuid
import time
import random
import threading
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class AllocationStrategy(Enum):
    RANDOM = "random"
    HASH_BASED = "hash_based"
    WEIGHTED = "weighted"
    GEOGRAPHIC = "geographic"
    BEHAVIORAL = "behavioral"

class MetricType(Enum):
    COUNTER = "counter"
    TIMER = "timer"
    GAUGE = "gauge"
    RATE = "rate"
    BOOLEAN = "boolean"

@dataclass
class Variant:
    """Represents a test variant in an A/B experiment"""
    id: str
    name: str
    description: str
    allocation_percentage: float
    config: Dict[str, Any] = field(default_factory=dict)
    is_control: bool = False
    
    def __post_init__(self):
        if self.allocation_percentage < 0 or self.allocation_percentage > 100:
            raise ValueError("Allocation percentage must be between 0 and 100")

@dataclass
class Metric:
    """Represents a metric to track in experiments"""
    name: str
    type: MetricType
    description: str
    aggregation_function: str = "sum"  # sum, avg, count, min, max
    success_criteria: Optional[Dict[str, Any]] = None

@dataclass
class ExperimentConfig:
    """Configuration for an A/B experiment"""
    traffic_percentage: float = 100.0  # Percentage of total traffic to include
    allocation_strategy: AllocationStrategy = AllocationStrategy.RANDOM
    sticky_sessions: bool = True  # Keep users in same variant
    geographic_targeting: Optional[List[str]] = None
    user_attributes_filter: Optional[Dict[str, Any]] = None
    minimum_sample_size: int = 100
    confidence_level: float = 0.95
    duration_days: int = 7

@dataclass
class Experiment:
    """Represents an A/B experiment"""
    id: str
    name: str
    description: str
    status: ExperimentStatus
    variants: List[Variant]
    metrics: List[Metric]
    config: ExperimentConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_by: str = "system"
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        # Validate variant allocation percentages
        total_allocation = sum(v.allocation_percentage for v in self.variants)
        if abs(total_allocation - 100.0) > 0.01:
            raise ValueError(f"Variant allocations must sum to 100%, got {total_allocation}%")

@dataclass
class ExperimentResult:
    """Represents results for a user's participation in an experiment"""
    experiment_id: str
    user_id: str
    variant_id: str
    session_id: str
    allocated_at: datetime
    metrics_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExperimentAnalysis:
    """Statistical analysis results for an experiment"""
    experiment_id: str
    variant_results: Dict[str, Dict[str, Any]]
    statistical_significance: Dict[str, Dict[str, float]]
    recommendations: List[str]
    confidence_intervals: Dict[str, Dict[str, tuple]]
    sample_sizes: Dict[str, int]
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)

class ABTestingManager:
    """
    Manages A/B testing experiments, variant allocation, and results tracking
    """
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.user_allocations: Dict[str, Dict[str, str]] = {}  # user_id -> {experiment_id -> variant_id}
        self.experiment_results: Dict[str, List[ExperimentResult]] = defaultdict(list)
        self._locks = defaultdict(threading.RLock)
        self._global_lock = threading.RLock()
        
        # Analytics tracking
        self.allocation_history = []
        self.metric_events = []
        
        logger.info("A/B Testing Manager initialized")
    
    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Variant],
        metrics: List[Metric],
        config: ExperimentConfig = None,
        created_by: str = "system"
    ) -> Experiment:
        """Create a new A/B experiment"""
        with self._global_lock:
            experiment_id = f"exp_{uuid.uuid4().hex[:12]}"
            
            # Validate variants
            if len(variants) < 2:
                raise ValueError("Experiment must have at least 2 variants")
            
            # Ensure variant IDs are unique
            variant_ids = [v.id for v in variants]
            if len(set(variant_ids)) != len(variant_ids):
                raise ValueError("Variant IDs must be unique")
            
            # Validate metrics
            if not metrics:
                raise ValueError("Experiment must have at least one metric")
            
            experiment = Experiment(
                id=experiment_id,
                name=name,
                description=description,
                status=ExperimentStatus.DRAFT,
                variants=variants,
                metrics=metrics,
                config=config or ExperimentConfig(),
                created_by=created_by
            )
            
            self.experiments[experiment_id] = experiment
            self._locks[experiment_id] = threading.RLock()
            
            logger.info(f"Created experiment: {experiment_id} ({name}) with {len(variants)} variants")
            return experiment
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        with self._locks[experiment_id]:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if experiment.status != ExperimentStatus.DRAFT:
                logger.warning(f"Cannot start experiment {experiment_id} - status: {experiment.status}")
                return False
            
            experiment.status = ExperimentStatus.RUNNING
            experiment.started_at = datetime.utcnow()
            
            logger.info(f"Started experiment: {experiment_id}")
            return True
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment"""
        with self._locks[experiment_id]:
            experiment = self.experiments.get(experiment_id)
            if not experiment:
                return False
            
            if experiment.status != ExperimentStatus.RUNNING:
                logger.warning(f"Cannot stop experiment {experiment_id} - status: {experiment.status}")
                return False
            
            experiment.status = ExperimentStatus.COMPLETED
            experiment.ended_at = datetime.utcnow()
            
            logger.info(f"Stopped experiment: {experiment_id}")
            return True
    
    def allocate_variant(
        self,
        experiment_id: str,
        user_id: str,
        session_id: str = None,
        user_attributes: Dict[str, Any] = None
    ) -> Optional[str]:
        """Allocate a variant for a user in an experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None
        
        # Check if user already allocated (sticky sessions)
        if experiment.config.sticky_sessions and user_id in self.user_allocations:
            if experiment_id in self.user_allocations[user_id]:
                return self.user_allocations[user_id][experiment_id]
        
        # Check traffic percentage
        if random.random() * 100 > experiment.config.traffic_percentage:
            return None
        
        # Apply filters
        if not self._passes_filters(experiment, user_attributes):
            return None
        
        # Allocate variant based on strategy
        variant_id = self._allocate_variant_by_strategy(experiment, user_id, user_attributes)
        
        if variant_id:
            # Store allocation
            if user_id not in self.user_allocations:
                self.user_allocations[user_id] = {}
            self.user_allocations[user_id][experiment_id] = variant_id
            
            # Record allocation
            result = ExperimentResult(
                experiment_id=experiment_id,
                user_id=user_id,
                variant_id=variant_id,
                session_id=session_id or f"session_{int(time.time())}",
                allocated_at=datetime.utcnow(),
                metadata=user_attributes or {}
            )
            
            self.experiment_results[experiment_id].append(result)
            
            # Track allocation for analytics
            self.allocation_history.append({
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.debug(f"Allocated user {user_id} to variant {variant_id} in experiment {experiment_id}")
        
        return variant_id
    
    def record_metric(
        self,
        experiment_id: str,
        user_id: str,
        metric_name: str,
        value: Any,
        timestamp: datetime = None
    ) -> bool:
        """Record a metric value for a user in an experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False
        
        # Find user's allocation
        user_allocation = self.user_allocations.get(user_id, {})
        variant_id = user_allocation.get(experiment_id)
        
        if not variant_id:
            logger.debug(f"User {user_id} not allocated to experiment {experiment_id}")
            return False
        
        # Find the user's result record
        user_result = None
        for result in self.experiment_results[experiment_id]:
            if result.user_id == user_id and result.variant_id == variant_id:
                user_result = result
                break
        
        if not user_result:
            logger.warning(f"No allocation record found for user {user_id} in experiment {experiment_id}")
            return False
        
        # Record the metric
        if metric_name not in user_result.metrics_data:
            user_result.metrics_data[metric_name] = []
        
        metric_entry = {
            "value": value,
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        user_result.metrics_data[metric_name].append(metric_entry)
        
        # Track metric for analytics
        self.metric_events.append({
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "user_id": user_id,
            "metric_name": metric_name,
            "value": value,
            "timestamp": metric_entry["timestamp"]
        })
        
        logger.debug(f"Recorded metric {metric_name}={value} for user {user_id} in experiment {experiment_id}")
        return True
    
    def get_experiment_results(self, experiment_id: str) -> Optional[ExperimentAnalysis]:
        """Get statistical analysis results for an experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        
        results = self.experiment_results.get(experiment_id, [])
        if not results:
            return ExperimentAnalysis(
                experiment_id=experiment_id,
                variant_results={},
                statistical_significance={},
                recommendations=["No data available for analysis"],
                confidence_intervals={},
                sample_sizes={}
            )
        
        # Aggregate results by variant
        variant_metrics = defaultdict(lambda: defaultdict(list))
        sample_sizes = defaultdict(int)
        
        for result in results:
            sample_sizes[result.variant_id] += 1
            for metric_name, metric_values in result.metrics_data.items():
                for metric_entry in metric_values:
                    variant_metrics[result.variant_id][metric_name].append(metric_entry["value"])
        
        # Calculate statistics
        variant_results = {}
        statistical_significance = {}
        confidence_intervals = {}
        
        for variant_id in variant_metrics:
            variant_results[variant_id] = {}
            for metric_name, values in variant_metrics[variant_id].items():
                if values:
                    variant_results[variant_id][metric_name] = {
                        "count": len(values),
                        "sum": sum(values) if all(isinstance(v, (int, float)) for v in values) else len(values),
                        "mean": sum(values) / len(values) if all(isinstance(v, (int, float)) for v in values) else 0,
                        "min": min(values) if all(isinstance(v, (int, float)) for v in values) else 0,
                        "max": max(values) if all(isinstance(v, (int, float)) for v in values) else 0
                    }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(experiment, variant_results, sample_sizes)
        
        return ExperimentAnalysis(
            experiment_id=experiment_id,
            variant_results=variant_results,
            statistical_significance=statistical_significance,
            recommendations=recommendations,
            confidence_intervals=confidence_intervals,
            sample_sizes=dict(sample_sizes)
        )
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        created_by: Optional[str] = None
    ) -> List[Experiment]:
        """List experiments with optional filtering"""
        experiments = list(self.experiments.values())
        
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        if created_by:
            experiments = [e for e in experiments if e.created_by == created_by]
        
        # Sort by creation date (newest first)
        experiments.sort(key=lambda e: e.created_at, reverse=True)
        
        return experiments
    
    def get_user_experiments(self, user_id: str) -> Dict[str, str]:
        """Get all experiment allocations for a user"""
        return self.user_allocations.get(user_id, {})
    
    def get_experiment_stats(self) -> Dict[str, Any]:
        """Get overall A/B testing statistics"""
        total_experiments = len(self.experiments)
        running_experiments = len([e for e in self.experiments.values() if e.status == ExperimentStatus.RUNNING])
        completed_experiments = len([e for e in self.experiments.values() if e.status == ExperimentStatus.COMPLETED])
        
        total_allocations = len(self.allocation_history)
        total_metric_events = len(self.metric_events)
        
        return {
            "total_experiments": total_experiments,
            "running_experiments": running_experiments,
            "completed_experiments": completed_experiments,
            "total_allocations": total_allocations,
            "total_metric_events": total_metric_events,
            "unique_users": len(self.user_allocations),
            "system_status": "operational"
        }
    
    def _passes_filters(self, experiment: Experiment, user_attributes: Dict[str, Any] = None) -> bool:
        """Check if user passes experiment filters"""
        if not user_attributes:
            return True
        
        # Geographic targeting
        if experiment.config.geographic_targeting:
            user_location = user_attributes.get("country") or user_attributes.get("region")
            if user_location not in experiment.config.geographic_targeting:
                return False
        
        # User attributes filter
        if experiment.config.user_attributes_filter:
            for key, expected_value in experiment.config.user_attributes_filter.items():
                if user_attributes.get(key) != expected_value:
                    return False
        
        return True
    
    def _allocate_variant_by_strategy(
        self,
        experiment: Experiment,
        user_id: str,
        user_attributes: Dict[str, Any] = None
    ) -> Optional[str]:
        """Allocate variant based on experiment's allocation strategy"""
        
        if experiment.config.allocation_strategy == AllocationStrategy.RANDOM:
            return self._random_allocation(experiment.variants)
        
        elif experiment.config.allocation_strategy == AllocationStrategy.HASH_BASED:
            return self._hash_based_allocation(experiment.variants, user_id)
        
        elif experiment.config.allocation_strategy == AllocationStrategy.WEIGHTED:
            return self._weighted_allocation(experiment.variants)
        
        else:
            # Default to random
            return self._random_allocation(experiment.variants)
    
    def _random_allocation(self, variants: List[Variant]) -> str:
        """Random variant allocation"""
        rand_value = random.random() * 100
        cumulative = 0
        
        for variant in variants:
            cumulative += variant.allocation_percentage
            if rand_value <= cumulative:
                return variant.id
        
        # Fallback to last variant
        return variants[-1].id
    
    def _hash_based_allocation(self, variants: List[Variant], user_id: str) -> str:
        """Hash-based deterministic allocation"""
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
        cumulative = 0
        
        for variant in variants:
            cumulative += variant.allocation_percentage
            if hash_value < cumulative:
                return variant.id
        
        # Fallback to last variant
        return variants[-1].id
    
    def _weighted_allocation(self, variants: List[Variant]) -> str:
        """Weighted random allocation"""
        weights = [v.allocation_percentage for v in variants]
        return random.choices(variants, weights=weights)[0].id
    
    def _generate_recommendations(
        self,
        experiment: Experiment,
        variant_results: Dict[str, Any],
        sample_sizes: Dict[str, int]
    ) -> List[str]:
        """Generate recommendations based on experiment results"""
        recommendations = []
        
        # Check sample sizes
        min_sample_size = experiment.config.minimum_sample_size
        for variant_id, size in sample_sizes.items():
            if size < min_sample_size:
                recommendations.append(f"Variant {variant_id} has insufficient sample size ({size} < {min_sample_size})")
        
        # Check for clear winners
        if len(variant_results) >= 2:
            # Simple heuristic for now - in production, use proper statistical tests
            control_variant = next((v for v in experiment.variants if v.is_control), experiment.variants[0])
            
            for metric in experiment.metrics:
                if metric.name in variant_results.get(control_variant.id, {}):
                    control_value = variant_results[control_variant.id][metric.name].get("mean", 0)
                    
                    for variant in experiment.variants:
                        if variant.id != control_variant.id and variant.id in variant_results:
                            variant_value = variant_results[variant.id][metric.name].get("mean", 0)
                            improvement = ((variant_value - control_value) / max(control_value, 0.001)) * 100
                            
                            if abs(improvement) > 10:  # 10% threshold
                                direction = "increased" if improvement > 0 else "decreased"
                                recommendations.append(
                                    f"Variant {variant.id} {direction} {metric.name} by {abs(improvement):.1f}% vs control"
                                )
        
        if not recommendations:
            recommendations.append("No significant differences detected between variants")
        
        return recommendations

# Global A/B testing manager instance
_ab_testing_manager: Optional[ABTestingManager] = None

def get_ab_testing_manager() -> ABTestingManager:
    """Get the global A/B testing manager instance"""
    global _ab_testing_manager
    if _ab_testing_manager is None:
        _ab_testing_manager = ABTestingManager()
    return _ab_testing_manager

# Utility functions for easy integration

def run_experiment(
    experiment_name: str,
    user_id: str,
    variants_config: Dict[str, Any],
    default_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Simple function to run an experiment and return the configuration for the user
    
    Args:
        experiment_name: Name of the experiment
        user_id: User identifier
        variants_config: Dictionary mapping variant names to their configurations
        default_config: Default configuration if user not in experiment
    
    Returns:
        Configuration dictionary for the user
    """
    manager = get_ab_testing_manager()
    
    # Find experiment by name
    experiment = None
    for exp in manager.experiments.values():
        if exp.name == experiment_name and exp.status == ExperimentStatus.RUNNING:
            experiment = exp
            break
    
    if not experiment:
        return default_config or {}
    
    # Get user's variant
    variant_id = manager.allocate_variant(experiment.id, user_id)
    
    if not variant_id:
        return default_config or {}
    
    # Find variant configuration
    for variant in experiment.variants:
        if variant.id == variant_id:
            return variants_config.get(variant.name, default_config or {})
    
    return default_config or {}

def track_metric(experiment_name: str, user_id: str, metric_name: str, value: Any) -> bool:
    """
    Simple function to track a metric for a user in an experiment
    
    Args:
        experiment_name: Name of the experiment
        user_id: User identifier
        metric_name: Name of the metric to track
        value: Value to record
    
    Returns:
        True if metric was recorded, False otherwise
    """
    manager = get_ab_testing_manager()
    
    # Find experiment by name
    experiment = None
    for exp in manager.experiments.values():
        if exp.name == experiment_name:
            experiment = exp
            break
    
    if not experiment:
        return False
    
    return manager.record_metric(experiment.id, user_id, metric_name, value)