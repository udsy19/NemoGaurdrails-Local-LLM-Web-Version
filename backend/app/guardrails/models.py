"""
Shared models and data structures for Phase 4 guardrails implementation
Prevents circular imports between pipeline components
"""

import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

class PipelineStage(Enum):
    """Pipeline processing stages"""
    PRE_SCREENING = "pre_screening"
    PRIMARY_ENSEMBLE = "primary_ensemble"
    CROSS_VALIDATION = "cross_validation"
    CONTEXT_ANALYSIS = "context_analysis"
    ESCALATION = "escalation"

class ConfidenceLevel(Enum):
    """Confidence levels for routing decisions"""
    HIGH = "high"        # >92%
    MEDIUM = "medium"    # 75-92%
    LOW = "low"         # <75%
    CONFLICT = "conflict"  # Models disagree significantly

@dataclass
class DetectionResult:
    """Unified detection result structure"""
    blocked: bool
    confidence: float
    stage: PipelineStage
    guardrail_type: str
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    model_scores: Dict[str, float] = field(default_factory=dict)
    escalation_required: bool = False
    uncertainty_bounds: Tuple[float, float] = (0.0, 1.0)

@dataclass
class PipelineContext:
    """Context information for pipeline processing"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[str] = field(default_factory=list)
    user_risk_score: float = 0.0
    domain_context: str = "general"
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)