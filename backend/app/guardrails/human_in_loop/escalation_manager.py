"""
Escalation Manager
Intelligent escalation system for human review of uncertain or edge case decisions
"""

import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
from datetime import datetime, timedelta

from app.utils.logger import app_logger
from app.guardrails.models import DetectionResult, PipelineContext

class EscalationPriority(Enum):
    """Priority levels for escalation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"

class EscalationReason(Enum):
    """Reasons for escalation"""
    LOW_CONFIDENCE = "low_confidence"
    MODEL_DISAGREEMENT = "model_disagreement"
    ADVERSARIAL_DETECTED = "adversarial_detected"
    HIGH_RISK_USER = "high_risk_user"
    SENSITIVE_CONTENT = "sensitive_content"
    SYSTEM_ERROR = "system_error"
    POLICY_VIOLATION = "policy_violation"
    UNCERTAIN_CLASSIFICATION = "uncertain_classification"

@dataclass
class EscalationConfig:
    """Configuration for escalation system"""
    # Confidence thresholds for escalation
    low_confidence_threshold: float = 0.6
    disagreement_threshold: float = 0.3
    
    # Risk-based escalation
    high_risk_user_threshold: float = 0.8
    sensitive_content_types: List[str] = field(default_factory=lambda: ["pii", "financial", "medical"])
    
    # Escalation criteria
    enable_confidence_based: bool = True
    enable_disagreement_based: bool = True
    enable_risk_based: bool = True
    enable_adversarial_escalation: bool = True
    
    # Queue management
    max_queue_size: int = 1000
    auto_expire_hours: int = 24
    priority_boost_hours: int = 4
    
    # Human reviewer settings
    min_reviewers_per_item: int = 1
    max_reviewers_per_item: int = 3
    reviewer_agreement_threshold: float = 0.8

@dataclass
class EscalationItem:
    """Item requiring human review"""
    id: str
    text: str
    detection_results: Dict[str, DetectionResult]
    context: PipelineContext
    escalation_reasons: List[EscalationReason]
    priority: EscalationPriority
    created_at: datetime
    expires_at: datetime
    status: str = "pending"
    assigned_reviewers: List[str] = field(default_factory=list)
    reviews: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class EscalationManager:
    """
    Advanced escalation management system
    
    Features:
    - Intelligent escalation criteria
    - Priority-based queue management
    - Multi-reviewer consensus
    - Feedback integration
    - Performance analytics
    - Automated expiration
    """
    
    def __init__(self, config: EscalationConfig = None):
        self.config = config or EscalationConfig()
        self.escalation_queue: Dict[str, EscalationItem] = {}
        self.completed_escalations: List[EscalationItem] = []
        
        # Performance tracking
        self.escalation_stats = {
            "total_escalations": 0,
            "escalations_by_reason": {reason.value: 0 for reason in EscalationReason},
            "escalations_by_priority": {priority.value: 0 for priority in EscalationPriority},
            "average_resolution_time_hours": 0.0,
            "reviewer_performance": {},
            "false_escalation_rate": 0.0
        }
        
        app_logger.info("Escalation manager initialized")
    
    async def evaluate_escalation(
        self,
        text: str,
        detection_results: Dict[str, DetectionResult],
        context: PipelineContext
    ) -> Tuple[bool, List[EscalationReason], EscalationPriority]:
        """
        Evaluate whether content should be escalated for human review
        
        Args:
            text: Input text
            detection_results: Results from all detection stages
            context: Pipeline context
            
        Returns:
            Tuple of (should_escalate, reasons, priority)
        """
        
        escalation_reasons = []
        priority = EscalationPriority.LOW
        
        try:
            # 1. Confidence-based escalation
            if self.config.enable_confidence_based:
                confidence_reasons, confidence_priority = self._evaluate_confidence_escalation(detection_results)
                escalation_reasons.extend(confidence_reasons)
                priority = max(priority, confidence_priority, key=lambda x: list(EscalationPriority).index(x))
            
            # 2. Model disagreement escalation
            if self.config.enable_disagreement_based:
                disagreement_reasons, disagreement_priority = self._evaluate_disagreement_escalation(detection_results)
                escalation_reasons.extend(disagreement_reasons)
                priority = max(priority, disagreement_priority, key=lambda x: list(EscalationPriority).index(x))
            
            # 3. Risk-based escalation
            if self.config.enable_risk_based:
                risk_reasons, risk_priority = self._evaluate_risk_escalation(context, detection_results)
                escalation_reasons.extend(risk_reasons)
                priority = max(priority, risk_priority, key=lambda x: list(EscalationPriority).index(x))
            
            # 4. Adversarial detection escalation
            if self.config.enable_adversarial_escalation:
                adversarial_reasons, adversarial_priority = self._evaluate_adversarial_escalation(detection_results)
                escalation_reasons.extend(adversarial_reasons)
                priority = max(priority, adversarial_priority, key=lambda x: list(EscalationPriority).index(x))
            
            # 5. Content sensitivity escalation
            sensitivity_reasons, sensitivity_priority = self._evaluate_content_sensitivity(text, detection_results)
            escalation_reasons.extend(sensitivity_reasons)
            priority = max(priority, sensitivity_priority, key=lambda x: list(EscalationPriority).index(x))
            
            should_escalate = len(escalation_reasons) > 0
            
            if should_escalate:
                app_logger.info(f"Escalation recommended: {len(escalation_reasons)} reasons, priority: {priority.value}")
                
                # Update statistics
                self.escalation_stats["total_escalations"] += 1
                for reason in escalation_reasons:
                    self.escalation_stats["escalations_by_reason"][reason.value] += 1
                self.escalation_stats["escalations_by_priority"][priority.value] += 1
            
            return should_escalate, escalation_reasons, priority
            
        except Exception as e:
            app_logger.error(f"Escalation evaluation failed: {e}")
            # Fail safe - escalate on error
            return True, [EscalationReason.SYSTEM_ERROR], EscalationPriority.HIGH
    
    async def create_escalation(
        self,
        text: str,
        detection_results: Dict[str, DetectionResult],
        context: PipelineContext,
        reasons: List[EscalationReason],
        priority: EscalationPriority
    ) -> str:
        """
        Create new escalation item for human review
        
        Returns:
            Escalation item ID
        """
        
        try:
            # Check queue capacity
            if len(self.escalation_queue) >= self.config.max_queue_size:
                await self._cleanup_expired_escalations()
                
                if len(self.escalation_queue) >= self.config.max_queue_size:
                    app_logger.warning("Escalation queue at capacity, removing oldest low-priority items")
                    self._remove_low_priority_items()
            
            # Create escalation item
            escalation_id = str(uuid.uuid4())
            current_time = datetime.now()
            
            escalation_item = EscalationItem(
                id=escalation_id,
                text=text,
                detection_results=detection_results,
                context=context,
                escalation_reasons=reasons,
                priority=priority,
                created_at=current_time,
                expires_at=current_time + timedelta(hours=self.config.auto_expire_hours),
                metadata={
                    "text_length": len(text),
                    "guardrails_triggered": sum(1 for result in detection_results.values() if result.blocked),
                    "max_confidence": max((result.confidence for result in detection_results.values()), default=0.0),
                    "user_risk_score": context.user_risk_score if context else 0.0
                }
            )
            
            # Add to queue
            self.escalation_queue[escalation_id] = escalation_item
            
            app_logger.info(f"Escalation created: {escalation_id} (priority: {priority.value})")
            
            return escalation_id
            
        except Exception as e:
            app_logger.error(f"Failed to create escalation: {e}")
            raise
    
    async def assign_reviewer(self, escalation_id: str, reviewer_id: str) -> bool:
        """Assign reviewer to escalation item"""
        
        if escalation_id not in self.escalation_queue:
            app_logger.warning(f"Escalation {escalation_id} not found")
            return False
        
        escalation_item = self.escalation_queue[escalation_id]
        
        if len(escalation_item.assigned_reviewers) >= self.config.max_reviewers_per_item:
            app_logger.warning(f"Maximum reviewers already assigned to {escalation_id}")
            return False
        
        if reviewer_id not in escalation_item.assigned_reviewers:
            escalation_item.assigned_reviewers.append(reviewer_id)
            escalation_item.status = "in_review"
            app_logger.info(f"Reviewer {reviewer_id} assigned to escalation {escalation_id}")
            return True
        
        return False
    
    async def submit_review(
        self,
        escalation_id: str,
        reviewer_id: str,
        decision: bool,
        confidence: float,
        reasoning: str,
        additional_data: Dict[str, Any] = None
    ) -> bool:
        """Submit review decision for escalation item"""
        
        if escalation_id not in self.escalation_queue:
            app_logger.warning(f"Escalation {escalation_id} not found")
            return False
        
        escalation_item = self.escalation_queue[escalation_id]
        
        if reviewer_id not in escalation_item.assigned_reviewers:
            app_logger.warning(f"Reviewer {reviewer_id} not assigned to {escalation_id}")
            return False
        
        # Check if reviewer already submitted
        existing_review = next((r for r in escalation_item.reviews if r["reviewer_id"] == reviewer_id), None)
        if existing_review:
            app_logger.warning(f"Reviewer {reviewer_id} already submitted review for {escalation_id}")
            return False
        
        # Create review
        review = {
            "reviewer_id": reviewer_id,
            "decision": decision,  # True = block, False = allow
            "confidence": confidence,
            "reasoning": reasoning,
            "submitted_at": datetime.now(),
            "additional_data": additional_data or {}
        }
        
        escalation_item.reviews.append(review)
        
        # Update reviewer performance stats
        if reviewer_id not in self.escalation_stats["reviewer_performance"]:
            self.escalation_stats["reviewer_performance"][reviewer_id] = {
                "total_reviews": 0,
                "average_confidence": 0.0,
                "agreement_rate": 0.0
            }
        
        reviewer_stats = self.escalation_stats["reviewer_performance"][reviewer_id]
        reviewer_stats["total_reviews"] += 1
        
        # Check if consensus reached
        if len(escalation_item.reviews) >= self.config.min_reviewers_per_item:
            consensus = self._check_consensus(escalation_item)
            if consensus:
                await self._finalize_escalation(escalation_id, escalation_item)
        
        app_logger.info(f"Review submitted by {reviewer_id} for escalation {escalation_id}")
        return True
    
    def get_pending_escalations(
        self,
        priority_filter: Optional[EscalationPriority] = None,
        reviewer_id: Optional[str] = None
    ) -> List[EscalationItem]:
        """Get pending escalations for review"""
        
        escalations = []
        
        for item in self.escalation_queue.values():
            if item.status in ["pending", "in_review"]:
                # Apply priority filter
                if priority_filter and item.priority != priority_filter:
                    continue
                
                # Apply reviewer filter
                if reviewer_id:
                    if reviewer_id in item.assigned_reviewers:
                        escalations.append(item)
                else:
                    # Only include unassigned or partially assigned items
                    if len(item.assigned_reviewers) < self.config.max_reviewers_per_item:
                        escalations.append(item)
        
        # Sort by priority and creation time
        priority_order = {p: i for i, p in enumerate(EscalationPriority)}
        escalations.sort(key=lambda x: (priority_order[x.priority], x.created_at))
        
        return escalations
    
    def _evaluate_confidence_escalation(
        self,
        detection_results: Dict[str, DetectionResult]
    ) -> Tuple[List[EscalationReason], EscalationPriority]:
        """Evaluate escalation based on confidence levels"""
        
        reasons = []
        priority = EscalationPriority.LOW
        
        # Check for low confidence decisions
        low_confidence_count = 0
        min_confidence = 1.0
        
        for result in detection_results.values():
            if result.confidence < self.config.low_confidence_threshold:
                low_confidence_count += 1
                min_confidence = min(min_confidence, result.confidence)
        
        if low_confidence_count > 0:
            reasons.append(EscalationReason.LOW_CONFIDENCE)
            
            # Determine priority based on confidence level
            if min_confidence < 0.3:
                priority = EscalationPriority.HIGH
            elif min_confidence < 0.5:
                priority = EscalationPriority.MEDIUM
            else:
                priority = EscalationPriority.LOW
        
        return reasons, priority
    
    def _evaluate_disagreement_escalation(
        self,
        detection_results: Dict[str, DetectionResult]
    ) -> Tuple[List[EscalationReason], EscalationPriority]:
        """Evaluate escalation based on model disagreement"""
        
        reasons = []
        priority = EscalationPriority.LOW
        
        # Check for disagreement in each guardrail type
        disagreement_count = 0
        max_disagreement = 0.0
        
        for result in detection_results.values():
            if result.model_scores and len(result.model_scores) > 1:
                scores = list(result.model_scores.values())
                score_range = max(scores) - min(scores)
                
                if score_range > self.config.disagreement_threshold:
                    disagreement_count += 1
                    max_disagreement = max(max_disagreement, score_range)
        
        if disagreement_count > 0:
            reasons.append(EscalationReason.MODEL_DISAGREEMENT)
            
            # Determine priority based on disagreement severity
            if max_disagreement > 0.7:
                priority = EscalationPriority.HIGH
            elif max_disagreement > 0.5:
                priority = EscalationPriority.MEDIUM
            else:
                priority = EscalationPriority.LOW
        
        return reasons, priority
    
    def _evaluate_risk_escalation(
        self,
        context: PipelineContext,
        detection_results: Dict[str, DetectionResult]
    ) -> Tuple[List[EscalationReason], EscalationPriority]:
        """Evaluate escalation based on user risk"""
        
        reasons = []
        priority = EscalationPriority.LOW
        
        if context:
            # High-risk user escalation
            if context.user_risk_score > self.config.high_risk_user_threshold:
                reasons.append(EscalationReason.HIGH_RISK_USER)
                priority = EscalationPriority.HIGH
            
            # Sensitive domain escalation
            if context.domain_context in ["financial", "medical", "legal"]:
                reasons.append(EscalationReason.SENSITIVE_CONTENT)
                priority = max(priority, EscalationPriority.MEDIUM, key=lambda x: list(EscalationPriority).index(x))
        
        return reasons, priority
    
    def _evaluate_adversarial_escalation(
        self,
        detection_results: Dict[str, DetectionResult]
    ) -> Tuple[List[EscalationReason], EscalationPriority]:
        """Evaluate escalation based on adversarial detection"""
        
        reasons = []
        priority = EscalationPriority.LOW
        
        # Check for adversarial content detection
        adversarial_result = detection_results.get("adversarial")
        if adversarial_result and adversarial_result.blocked:
            reasons.append(EscalationReason.ADVERSARIAL_DETECTED)
            
            # High priority for adversarial attacks
            if adversarial_result.confidence > 0.8:
                priority = EscalationPriority.CRITICAL
            elif adversarial_result.confidence > 0.6:
                priority = EscalationPriority.HIGH
            else:
                priority = EscalationPriority.MEDIUM
        
        return reasons, priority
    
    def _evaluate_content_sensitivity(
        self,
        text: str,
        detection_results: Dict[str, DetectionResult]
    ) -> Tuple[List[EscalationReason], EscalationPriority]:
        """Evaluate escalation based on content sensitivity"""
        
        reasons = []
        priority = EscalationPriority.LOW
        
        # Check for sensitive content types
        for content_type in self.config.sensitive_content_types:
            if content_type in detection_results:
                result = detection_results[content_type]
                if result.blocked or result.confidence > 0.7:
                    reasons.append(EscalationReason.SENSITIVE_CONTENT)
                    priority = EscalationPriority.MEDIUM
                    break
        
        return reasons, priority
    
    def _check_consensus(self, escalation_item: EscalationItem) -> bool:
        """Check if reviewer consensus has been reached"""
        
        if len(escalation_item.reviews) < self.config.min_reviewers_per_item:
            return False
        
        # Calculate agreement
        decisions = [review["decision"] for review in escalation_item.reviews]
        block_votes = sum(decisions)
        allow_votes = len(decisions) - block_votes
        
        total_votes = len(decisions)
        agreement_ratio = max(block_votes, allow_votes) / total_votes
        
        return agreement_ratio >= self.config.reviewer_agreement_threshold
    
    async def _finalize_escalation(self, escalation_id: str, escalation_item: EscalationItem):
        """Finalize escalation with consensus decision"""
        
        # Calculate final decision
        decisions = [review["decision"] for review in escalation_item.reviews]
        confidences = [review["confidence"] for review in escalation_item.reviews]
        
        final_decision = sum(decisions) > len(decisions) / 2
        final_confidence = statistics.mean(confidences)
        
        # Update item status
        escalation_item.status = "completed"
        escalation_item.metadata["final_decision"] = final_decision
        escalation_item.metadata["final_confidence"] = final_confidence
        escalation_item.metadata["resolution_time_hours"] = (
            datetime.now() - escalation_item.created_at
        ).total_seconds() / 3600
        
        # Move to completed escalations
        self.completed_escalations.append(escalation_item)
        del self.escalation_queue[escalation_id]
        
        # Update performance stats
        resolution_time = escalation_item.metadata["resolution_time_hours"]
        current_avg = self.escalation_stats["average_resolution_time_hours"]
        completed_count = len(self.completed_escalations)
        
        self.escalation_stats["average_resolution_time_hours"] = (
            (current_avg * (completed_count - 1) + resolution_time) / completed_count
        )
        
        app_logger.info(f"Escalation {escalation_id} finalized: {final_decision} (confidence: {final_confidence:.3f})")
    
    async def _cleanup_expired_escalations(self):
        """Remove expired escalations from queue"""
        
        current_time = datetime.now()
        expired_ids = []
        
        for escalation_id, item in self.escalation_queue.items():
            if current_time > item.expires_at:
                expired_ids.append(escalation_id)
        
        for escalation_id in expired_ids:
            expired_item = self.escalation_queue[escalation_id]
            expired_item.status = "expired"
            self.completed_escalations.append(expired_item)
            del self.escalation_queue[escalation_id]
            app_logger.info(f"Escalation {escalation_id} expired and removed from queue")
    
    def _remove_low_priority_items(self):
        """Remove low priority items when queue is full"""
        
        low_priority_ids = [
            item_id for item_id, item in self.escalation_queue.items()
            if item.priority == EscalationPriority.LOW and item.status == "pending"
        ]
        
        # Remove oldest low priority items
        for item_id in low_priority_ids[:10]:  # Remove up to 10 items
            removed_item = self.escalation_queue[item_id]
            removed_item.status = "removed_capacity"
            self.completed_escalations.append(removed_item)
            del self.escalation_queue[item_id]
            app_logger.warning(f"Removed low priority escalation {item_id} due to capacity")
    
    def get_escalation_statistics(self) -> Dict[str, Any]:
        """Get escalation system performance statistics"""
        
        return {
            "queue_status": {
                "current_queue_size": len(self.escalation_queue),
                "max_queue_size": self.config.max_queue_size,
                "pending_items": len([i for i in self.escalation_queue.values() if i.status == "pending"]),
                "in_review_items": len([i for i in self.escalation_queue.values() if i.status == "in_review"])
            },
            "performance_metrics": {
                "total_escalations": self.escalation_stats["total_escalations"],
                "completed_escalations": len(self.completed_escalations),
                "average_resolution_time_hours": self.escalation_stats["average_resolution_time_hours"],
                "escalation_rate": self.escalation_stats["total_escalations"] / max(1, self.escalation_stats["total_escalations"])
            },
            "escalation_distribution": {
                "by_reason": self.escalation_stats["escalations_by_reason"],
                "by_priority": self.escalation_stats["escalations_by_priority"]
            },
            "reviewer_performance": self.escalation_stats["reviewer_performance"]
        }