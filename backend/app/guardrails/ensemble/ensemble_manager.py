"""
Enterprise Guardrails Manager
Orchestrates the complete ensemble system as per implementation plan
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from .base_ensemble import EnsembleFramework, BaseDetector, EnsembleResult
from ..detectors.toxicity_ensemble import ToxicityEnsemble
from ..detectors.pii_ensemble import PIIEnsemble
from ..detectors.spam_ensemble import SpamEnsemble
from ..detectors.topic_ensemble import TopicEnsemble
from ..detectors.fact_check_ensemble import FactCheckEnsemble
from ..detectors.prompt_injection_ensemble import PromptInjectionEnsemble

logger = logging.getLogger(__name__)

class EnterpriseGuardrailsManager:
    """
    Enterprise-grade guardrails manager implementing the full
    multi-stage pipeline as specified in the implementation plan
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enterprise guardrails manager
        
        Args:
            config: Configuration dictionary for guardrails settings
        """
        self.config = config or {}
        self.ensemble_framework = EnsembleFramework(
            high_confidence_threshold=self.config.get('high_confidence_threshold', 0.92),
            medium_confidence_threshold=self.config.get('medium_confidence_threshold', 0.75),
            enable_parallel_processing=self.config.get('enable_parallel_processing', True)
        )
        
        # Guardrail ensembles
        self.guardrail_ensembles = {}
        self.enabled_guardrails = set()
        self.is_initialized = False
        
        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'allowed_requests': 0,
            'average_processing_time': 0.0,
            'guardrail_usage': {},
            'accuracy_metrics': {},
            'escalation_rate': 0.0
        }
        
        logger.info("EnterpriseGuardrailsManager initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize all guardrail ensembles according to the implementation plan
        
        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Initializing enterprise guardrails system...")
            
            # Initialize guardrail ensembles
            await self._initialize_guardrail_ensembles()
            
            # Load all models
            load_results = await self.ensemble_framework.load_all_models()
            
            # Check load success
            failed_loads = [name for name, success in load_results.items() if not success]
            if failed_loads:
                logger.warning(f"Failed to load some models: {failed_loads}")
            
            self.is_initialized = True
            logger.info("Enterprise guardrails system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize guardrails system: {e}")
            return False
    
    async def _initialize_guardrail_ensembles(self) -> None:
        """Initialize all guardrail ensemble detectors"""
        
        # Toxicity Detection Ensemble
        toxicity_ensemble = ToxicityEnsemble(self.config.get('toxicity', {}))
        await toxicity_ensemble.initialize()
        self.guardrail_ensembles['toxicity'] = toxicity_ensemble
        
        # Register toxicity detectors
        for detector in toxicity_ensemble.get_detectors():
            self.ensemble_framework.register_detector('toxicity', detector)
        
        # PII Detection Ensemble  
        pii_ensemble = PIIEnsemble(self.config.get('pii', {}))
        await pii_ensemble.initialize()
        self.guardrail_ensembles['pii'] = pii_ensemble
        
        for detector in pii_ensemble.get_detectors():
            self.ensemble_framework.register_detector('pii', detector)
        
        # Spam Detection Ensemble
        spam_ensemble = SpamEnsemble(self.config.get('spam', {}))
        await spam_ensemble.initialize()
        self.guardrail_ensembles['spam'] = spam_ensemble
        
        for detector in spam_ensemble.get_detectors():
            self.ensemble_framework.register_detector('spam', detector)
        
        # Topic Classification Ensemble
        topic_ensemble = TopicEnsemble(self.config.get('topic', {}))
        await topic_ensemble.initialize()
        self.guardrail_ensembles['topic'] = topic_ensemble
        
        for detector in topic_ensemble.get_detectors():
            self.ensemble_framework.register_detector('topic', detector)
        
        # Fact Check Ensemble
        fact_check_ensemble = FactCheckEnsemble(self.config.get('fact_check', {}))
        await fact_check_ensemble.initialize()
        self.guardrail_ensembles['fact_check'] = fact_check_ensemble
        
        for detector in fact_check_ensemble.get_detectors():
            self.ensemble_framework.register_detector('fact_check', detector)
        
        # Prompt Injection Ensemble
        injection_ensemble = PromptInjectionEnsemble(self.config.get('prompt_injection', {}))
        await injection_ensemble.initialize()
        self.guardrail_ensembles['prompt_injection'] = injection_ensemble
        
        for detector in injection_ensemble.get_detectors():
            self.ensemble_framework.register_detector('prompt_injection', detector)
        
        logger.info(f"Initialized {len(self.guardrail_ensembles)} guardrail ensembles")
    
    async def process_message(self, 
                            message: str,
                            enabled_guardrails: Optional[List[str]] = None,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process message through enterprise guardrails system
        
        Args:
            message: Input message to analyze
            enabled_guardrails: List of enabled guardrail types
            context: Optional context information
            
        Returns:
            Dict containing detection results and decision
        """
        if not self.is_initialized:
            raise RuntimeError("Guardrails system not initialized")
        
        start_time = datetime.now()
        
        try:
            # Determine which guardrails to apply
            if enabled_guardrails is None:
                enabled_guardrails = list(self.guardrail_ensembles.keys())
            
            # Filter to only enabled guardrails
            active_guardrails = [g for g in enabled_guardrails if g in self.guardrail_ensembles]
            
            if not active_guardrails:
                # No guardrails enabled - allow message
                return {
                    "blocked": False,
                    "blocking_reasons": [],
                    "confidence": 1.0,
                    "guardrails_used": [],
                    "processing_time_ms": 0.0,
                    "escalation_triggered": False,
                    "results": {}
                }
            
            # Process through ensemble framework
            ensemble_result = await self.ensemble_framework.process_text(
                message, active_guardrails, context
            )
            
            # Update performance metrics
            self._update_performance_metrics(ensemble_result, start_time)
            
            # Format response
            return {
                "blocked": ensemble_result.blocked,
                "blocking_reasons": ensemble_result.blocking_reasons,
                "confidence": ensemble_result.final_confidence,
                "guardrails_used": active_guardrails,
                "processing_time_ms": ensemble_result.total_processing_time_ms,
                "escalation_triggered": ensemble_result.escalation_triggered,
                "consensus_level": ensemble_result.consensus_level,
                "processing_stages": [stage.value for stage in ensemble_result.processing_stages],
                "results": {
                    "model_results": [result.to_dict() for result in ensemble_result.model_results],
                    "ensemble_analysis": ensemble_result.to_dict()
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Return safe default (block with error)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "blocked": True,
                "blocking_reasons": [f"Processing error: {str(e)}"],
                "confidence": 0.1,
                "guardrails_used": active_guardrails if 'active_guardrails' in locals() else [],
                "processing_time_ms": processing_time,
                "escalation_triggered": True,
                "error": True,
                "results": {"error": str(e)}
            }
    
    def _update_performance_metrics(self, result: EnsembleResult, start_time: datetime) -> None:
        """Update performance metrics with latest result"""
        self.performance_metrics['total_requests'] += 1
        
        if result.blocked:
            self.performance_metrics['blocked_requests'] += 1
        else:
            self.performance_metrics['allowed_requests'] += 1
        
        # Update average processing time
        total_requests = self.performance_metrics['total_requests']
        current_avg = self.performance_metrics['average_processing_time']
        new_time = result.total_processing_time_ms
        
        self.performance_metrics['average_processing_time'] = (
            (current_avg * (total_requests - 1) + new_time) / total_requests
        )
        
        # Track escalation rate
        if result.escalation_triggered:
            escalations = sum(1 for stage in result.processing_stages if stage.value == 'confidence_escalation')
            self.performance_metrics['escalation_rate'] = escalations / total_requests
    
    async def update_guardrail_config(self, guardrail_type: str, config: Dict[str, Any]) -> bool:
        """
        Update configuration for a specific guardrail type
        
        Args:
            guardrail_type: Type of guardrail to update
            config: New configuration
            
        Returns:
            bool: True if update successful
        """
        if guardrail_type not in self.guardrail_ensembles:
            logger.error(f"Unknown guardrail type: {guardrail_type}")
            return False
        
        try:
            ensemble = self.guardrail_ensembles[guardrail_type]
            await ensemble.update_config(config)
            logger.info(f"Updated config for {guardrail_type} guardrail")
            return True
        except Exception as e:
            logger.error(f"Failed to update {guardrail_type} config: {e}")
            return False
    
    def enable_guardrail(self, guardrail_type: str) -> bool:
        """Enable a specific guardrail type"""
        if guardrail_type not in self.guardrail_ensembles:
            logger.error(f"Unknown guardrail type: {guardrail_type}")
            return False
        
        self.enabled_guardrails.add(guardrail_type)
        logger.info(f"Enabled {guardrail_type} guardrail")
        return True
    
    def disable_guardrail(self, guardrail_type: str) -> bool:
        """Disable a specific guardrail type"""
        if guardrail_type not in self.guardrail_ensembles:
            logger.error(f"Unknown guardrail type: {guardrail_type}")
            return False
        
        self.enabled_guardrails.discard(guardrail_type)
        logger.info(f"Disabled {guardrail_type} guardrail")
        return True
    
    def get_enabled_guardrails(self) -> List[str]:
        """Get list of currently enabled guardrails"""
        return list(self.enabled_guardrails)
    
    def get_available_guardrails(self) -> List[str]:
        """Get list of all available guardrails"""
        return list(self.guardrail_ensembles.keys())
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        ensemble_stats = self.ensemble_framework.get_performance_stats()
        
        return {
            **self.performance_metrics,
            "ensemble_stats": ensemble_stats,
            "accuracy_rate": (
                self.performance_metrics['allowed_requests'] / 
                max(self.performance_metrics['total_requests'], 1)
            ),
            "block_rate": (
                self.performance_metrics['blocked_requests'] / 
                max(self.performance_metrics['total_requests'], 1)
            )
        }
    
    async def run_health_check(self) -> Dict[str, Any]:
        """
        Run comprehensive health check on the guardrails system
        
        Returns:
            Dict containing health status and details
        """
        health_status = {
            "overall_status": "healthy",
            "is_initialized": self.is_initialized,
            "guardrail_health": {},
            "performance_health": {},
            "issues": []
        }
        
        try:
            # Check each guardrail ensemble
            for name, ensemble in self.guardrail_ensembles.items():
                try:
                    ensemble_health = await ensemble.health_check()
                    health_status["guardrail_health"][name] = ensemble_health
                    
                    if not ensemble_health.get("healthy", False):
                        health_status["issues"].append(f"{name} guardrail unhealthy")
                        health_status["overall_status"] = "degraded"
                        
                except Exception as e:
                    health_status["guardrail_health"][name] = {"healthy": False, "error": str(e)}
                    health_status["issues"].append(f"{name} health check failed: {e}")
                    health_status["overall_status"] = "unhealthy"
            
            # Check performance metrics
            metrics = self.get_performance_metrics()
            
            if metrics["average_processing_time"] > 1000:  # >1 second
                health_status["issues"].append("High average processing time")
                health_status["overall_status"] = "degraded"
            
            if metrics["escalation_rate"] > 0.1:  # >10% escalation rate
                health_status["issues"].append("High escalation rate")
                health_status["overall_status"] = "degraded"
            
            health_status["performance_health"] = {
                "avg_processing_time": metrics["average_processing_time"],
                "escalation_rate": metrics["escalation_rate"],
                "total_requests": metrics["total_requests"]
            }
            
        except Exception as e:
            health_status["overall_status"] = "unhealthy"
            health_status["issues"].append(f"Health check error: {e}")
        
        return health_status
    
    async def cleanup(self) -> None:
        """Clean up resources and shutdown guardrails system"""
        try:
            logger.info("Shutting down enterprise guardrails system...")
            
            # Cleanup each ensemble
            for name, ensemble in self.guardrail_ensembles.items():
                try:
                    await ensemble.cleanup()
                    logger.info(f"Cleaned up {name} ensemble")
                except Exception as e:
                    logger.error(f"Error cleaning up {name} ensemble: {e}")
            
            # Reset state
            self.guardrail_ensembles.clear()
            self.enabled_guardrails.clear()
            self.is_initialized = False
            
            logger.info("Enterprise guardrails system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "is_initialized": self.is_initialized,
            "available_guardrails": self.get_available_guardrails(),
            "enabled_guardrails": self.get_enabled_guardrails(),
            "performance_metrics": self.get_performance_metrics(),
            "configuration": self.config,
            "version": "1.0.0",
            "framework_type": "enterprise_ensemble"
        }