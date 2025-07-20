"""
A/B Testing API endpoints for Phase 3
Provides experiment management and results tracking
"""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import logging

from app.utils.ab_testing import (
    get_ab_testing_manager,
    Experiment,
    Variant,
    Metric,
    ExperimentConfig,
    ExperimentStatus,
    AllocationStrategy,
    MetricType,
    ExperimentAnalysis,
    run_experiment,
    track_metric
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ab-testing", tags=["ab-testing"])

# Request/Response Models

class VariantRequest(BaseModel):
    id: str = Field(..., description="Unique variant identifier")
    name: str = Field(..., description="Variant name")
    description: str = Field(..., description="Variant description")
    allocation_percentage: float = Field(..., ge=0, le=100, description="Allocation percentage")
    config: Dict[str, Any] = Field(default_factory=dict, description="Variant configuration")
    is_control: bool = Field(False, description="Whether this is the control variant")

class MetricRequest(BaseModel):
    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Metric type")
    description: str = Field(..., description="Metric description")
    aggregation_function: str = Field("sum", description="Aggregation function")
    success_criteria: Optional[Dict[str, Any]] = Field(None, description="Success criteria")

class ExperimentConfigRequest(BaseModel):
    traffic_percentage: float = Field(100.0, ge=0, le=100, description="Traffic percentage")
    allocation_strategy: AllocationStrategy = Field(AllocationStrategy.RANDOM, description="Allocation strategy")
    sticky_sessions: bool = Field(True, description="Sticky sessions")
    geographic_targeting: Optional[List[str]] = Field(None, description="Geographic targeting")
    user_attributes_filter: Optional[Dict[str, Any]] = Field(None, description="User attributes filter")
    minimum_sample_size: int = Field(100, ge=1, description="Minimum sample size")
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Confidence level")
    duration_days: int = Field(7, ge=1, description="Duration in days")

class CreateExperimentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Experiment name")
    description: str = Field(..., description="Experiment description")
    variants: List[VariantRequest] = Field(..., min_items=2, description="Experiment variants")
    metrics: List[MetricRequest] = Field(..., min_items=1, description="Metrics to track")
    config: Optional[ExperimentConfigRequest] = Field(None, description="Experiment configuration")

class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: str
    status: ExperimentStatus
    variants: List[Dict[str, Any]]
    metrics: List[Dict[str, Any]]
    config: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_by: str
    tags: Set[str]

class AllocationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_attributes: Optional[Dict[str, Any]] = Field(None, description="User attributes")

class AllocationResponse(BaseModel):
    experiment_id: str
    user_id: str
    variant_id: Optional[str]
    allocated: bool
    variant_config: Dict[str, Any] = Field(default_factory=dict)

class MetricRecordRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    metric_name: str = Field(..., description="Metric name")
    value: Any = Field(..., description="Metric value")
    timestamp: Optional[datetime] = Field(None, description="Timestamp")

class SimpleExperimentRequest(BaseModel):
    experiment_name: str = Field(..., description="Experiment name")
    user_id: str = Field(..., description="User identifier")
    variants_config: Dict[str, Any] = Field(..., description="Variants configuration")
    default_config: Optional[Dict[str, Any]] = Field(None, description="Default configuration")

class SimpleMetricRequest(BaseModel):
    experiment_name: str = Field(..., description="Experiment name")
    user_id: str = Field(..., description="User identifier")
    metric_name: str = Field(..., description="Metric name")
    value: Any = Field(..., description="Metric value")

# Dependency for admin authentication (placeholder)
async def get_current_admin():
    """Placeholder for admin authentication"""
    return {"admin_id": "admin_user", "permissions": ["experiment_management"]}

# Experiment Management Endpoints

@router.post("/experiments", response_model=ExperimentResponse)
async def create_experiment(
    request: CreateExperimentRequest,
    admin: dict = Depends(get_current_admin)
):
    """Create a new A/B experiment"""
    try:
        manager = get_ab_testing_manager()
        
        # Convert request to internal models
        variants = [
            Variant(
                id=v.id,
                name=v.name,
                description=v.description,
                allocation_percentage=v.allocation_percentage,
                config=v.config,
                is_control=v.is_control
            )
            for v in request.variants
        ]
        
        metrics = [
            Metric(
                name=m.name,
                type=m.type,
                description=m.description,
                aggregation_function=m.aggregation_function,
                success_criteria=m.success_criteria
            )
            for m in request.metrics
        ]
        
        config = ExperimentConfig()
        if request.config:
            config = ExperimentConfig(
                traffic_percentage=request.config.traffic_percentage,
                allocation_strategy=request.config.allocation_strategy,
                sticky_sessions=request.config.sticky_sessions,
                geographic_targeting=request.config.geographic_targeting,
                user_attributes_filter=request.config.user_attributes_filter,
                minimum_sample_size=request.config.minimum_sample_size,
                confidence_level=request.config.confidence_level,
                duration_days=request.config.duration_days
            )
        
        experiment = manager.create_experiment(
            name=request.name,
            description=request.description,
            variants=variants,
            metrics=metrics,
            config=config,
            created_by=admin["admin_id"]
        )
        
        return ExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            status=experiment.status,
            variants=[vars(v) for v in experiment.variants],
            metrics=[vars(m) for m in experiment.metrics],
            config=vars(experiment.config),
            created_at=experiment.created_at,
            started_at=experiment.started_at,
            ended_at=experiment.ended_at,
            created_by=experiment.created_by,
            tags=experiment.tags
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create experiment")

@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    status: Optional[ExperimentStatus] = Query(None, description="Filter by status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    admin: dict = Depends(get_current_admin)
):
    """List all experiments with optional filtering"""
    try:
        manager = get_ab_testing_manager()
        experiments = manager.list_experiments(status=status, created_by=created_by)
        
        return [
            ExperimentResponse(
                id=exp.id,
                name=exp.name,
                description=exp.description,
                status=exp.status,
                variants=[vars(v) for v in exp.variants],
                metrics=[vars(m) for m in exp.metrics],
                config=vars(exp.config),
                created_at=exp.created_at,
                started_at=exp.started_at,
                ended_at=exp.ended_at,
                created_by=exp.created_by,
                tags=exp.tags
            )
            for exp in experiments
        ]
        
    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list experiments")

@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str = Path(..., description="Experiment ID"),
    admin: dict = Depends(get_current_admin)
):
    """Get a specific experiment"""
    try:
        manager = get_ab_testing_manager()
        experiment = manager.experiments.get(experiment_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return ExperimentResponse(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            status=experiment.status,
            variants=[vars(v) for v in experiment.variants],
            metrics=[vars(m) for m in experiment.metrics],
            config=vars(experiment.config),
            created_at=experiment.created_at,
            started_at=experiment.started_at,
            ended_at=experiment.ended_at,
            created_by=experiment.created_by,
            tags=experiment.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get experiment")

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str = Path(..., description="Experiment ID"),
    admin: dict = Depends(get_current_admin)
):
    """Start an experiment"""
    try:
        manager = get_ab_testing_manager()
        success = manager.start_experiment(experiment_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot start experiment")
        
        return {
            "success": True,
            "message": "Experiment started successfully",
            "experiment_id": experiment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start experiment")

@router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str = Path(..., description="Experiment ID"),
    admin: dict = Depends(get_current_admin)
):
    """Stop an experiment"""
    try:
        manager = get_ab_testing_manager()
        success = manager.stop_experiment(experiment_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot stop experiment")
        
        return {
            "success": True,
            "message": "Experiment stopped successfully",
            "experiment_id": experiment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop experiment")

# Variant Allocation Endpoints

@router.post("/experiments/{experiment_id}/allocate", response_model=AllocationResponse)
async def allocate_variant(
    experiment_id: str = Path(..., description="Experiment ID"),
    request: AllocationRequest = ...
):
    """Allocate a variant for a user"""
    try:
        manager = get_ab_testing_manager()
        
        variant_id = manager.allocate_variant(
            experiment_id=experiment_id,
            user_id=request.user_id,
            session_id=request.session_id,
            user_attributes=request.user_attributes
        )
        
        # Get variant configuration
        variant_config = {}
        if variant_id:
            experiment = manager.experiments.get(experiment_id)
            if experiment:
                for variant in experiment.variants:
                    if variant.id == variant_id:
                        variant_config = variant.config
                        break
        
        return AllocationResponse(
            experiment_id=experiment_id,
            user_id=request.user_id,
            variant_id=variant_id,
            allocated=variant_id is not None,
            variant_config=variant_config
        )
        
    except Exception as e:
        logger.error(f"Error allocating variant for experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to allocate variant")

@router.post("/experiments/{experiment_id}/metrics")
async def record_metric(
    experiment_id: str = Path(..., description="Experiment ID"),
    request: MetricRecordRequest = ...
):
    """Record a metric for a user in an experiment"""
    try:
        manager = get_ab_testing_manager()
        
        success = manager.record_metric(
            experiment_id=experiment_id,
            user_id=request.user_id,
            metric_name=request.metric_name,
            value=request.value,
            timestamp=request.timestamp
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to record metric")
        
        return {
            "success": True,
            "message": "Metric recorded successfully",
            "experiment_id": experiment_id,
            "user_id": request.user_id,
            "metric_name": request.metric_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording metric for experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metric")

# Results and Analytics Endpoints

@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str = Path(..., description="Experiment ID"),
    admin: dict = Depends(get_current_admin)
):
    """Get experiment results and analysis"""
    try:
        manager = get_ab_testing_manager()
        analysis = manager.get_experiment_results(experiment_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return {
            "success": True,
            "experiment_id": analysis.experiment_id,
            "analysis": {
                "variant_results": analysis.variant_results,
                "statistical_significance": analysis.statistical_significance,
                "recommendations": analysis.recommendations,
                "confidence_intervals": analysis.confidence_intervals,
                "sample_sizes": analysis.sample_sizes,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results for experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get experiment results")

@router.get("/users/{user_id}/experiments")
async def get_user_experiments(
    user_id: str = Path(..., description="User ID")
):
    """Get all experiment allocations for a user"""
    try:
        manager = get_ab_testing_manager()
        user_experiments = manager.get_user_experiments(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "experiments": user_experiments,
            "total_experiments": len(user_experiments)
        }
        
    except Exception as e:
        logger.error(f"Error getting experiments for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user experiments")

# Simple Integration Endpoints

@router.post("/simple/run-experiment")
async def simple_run_experiment(
    request: SimpleExperimentRequest
):
    """Simple endpoint to run an experiment and get user configuration"""
    try:
        config = run_experiment(
            experiment_name=request.experiment_name,
            user_id=request.user_id,
            variants_config=request.variants_config,
            default_config=request.default_config
        )
        
        return {
            "success": True,
            "user_id": request.user_id,
            "experiment_name": request.experiment_name,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Error running simple experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to run experiment")

@router.post("/simple/track-metric")
async def simple_track_metric(
    request: SimpleMetricRequest
):
    """Simple endpoint to track a metric"""
    try:
        success = track_metric(
            experiment_name=request.experiment_name,
            user_id=request.user_id,
            metric_name=request.metric_name,
            value=request.value
        )
        
        return {
            "success": success,
            "message": "Metric tracked successfully" if success else "Failed to track metric",
            "user_id": request.user_id,
            "experiment_name": request.experiment_name,
            "metric_name": request.metric_name
        }
        
    except Exception as e:
        logger.error(f"Error tracking simple metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to track metric")

# System Statistics

@router.get("/stats")
async def get_ab_testing_stats(
    admin: dict = Depends(get_current_admin)
):
    """Get A/B testing system statistics"""
    try:
        manager = get_ab_testing_manager()
        stats = manager.get_experiment_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting A/B testing stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

# Health Check

@router.get("/health")
async def ab_testing_health():
    """A/B testing system health check"""
    try:
        manager = get_ab_testing_manager()
        stats = manager.get_experiment_stats()
        
        return {
            "status": "healthy",
            "total_experiments": stats["total_experiments"],
            "running_experiments": stats["running_experiments"],
            "system_status": stats["system_status"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"A/B testing health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }