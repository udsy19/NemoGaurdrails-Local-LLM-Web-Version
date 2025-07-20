import os
import tempfile
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.actions import ActionResult

from app.guardrails.config_loader import ConfigLoader
from app.guardrails.custom_actions import set_model_manager
from app.guardrails.pipeline.multi_stage_pipeline import get_multi_stage_pipeline
from app.guardrails.models import PipelineContext
from app.utils.logger import app_logger
from app.utils.exceptions import GuardrailsException

class GuardrailsManager:
    def __init__(self, model_manager, config_dir: str = "configs/guardrails", detection_service=None):
        self.model_manager = model_manager
        self.detection_service = detection_service
        self.config_loader = ConfigLoader(config_dir)
        self.rails = None
        self.active_detectors = []
        self.is_initialized = False
        
        # Phase 4: Multi-stage pipeline integration
        self.use_phase4_pipeline = True
        self.phase4_pipeline = None
        
        # Set model manager for custom actions
        set_model_manager(model_manager)
        
    async def initialize(self, active_detectors: Optional[List[str]] = None):
        """Initialize guardrails with specified detectors"""
        try:
            app_logger.info("Initializing Guardrails System...")
            
            # Default to all available detectors if none specified
            if active_detectors is None:
                active_detectors = list(self.model_manager.available_detectors.keys())
            
            # Initialize Phase 4 multi-stage pipeline
            if self.use_phase4_pipeline:
                app_logger.info("Initializing Phase 4 Multi-Stage Pipeline...")
                self.phase4_pipeline = get_multi_stage_pipeline()
                app_logger.info("Phase 4 pipeline initialized successfully")
            
            # Load traditional NeMo configuration as fallback
            await self.load_configuration(active_detectors)
            self.is_initialized = True
            
            app_logger.info("Guardrails system initialized successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize guardrails: {e}")
            raise GuardrailsException(f"Guardrails initialization failed: {e}")
    
    async def load_configuration(self, active_detectors: List[str]):
        """Load guardrails configuration for specified detectors"""
        try:
            app_logger.info(f"Loading configuration for detectors: {active_detectors}")
            
            # Generate dynamic configuration
            config_dict = self.config_loader.generate_dynamic_config(active_detectors)
            
            # Create temporary directory for configuration files
            temp_dir = tempfile.mkdtemp()
            temp_path = Path(temp_dir)
            
            # Write main config file
            config_path = temp_path / "config.yml"
            with open(config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            # Create flows directory and files
            flows_dir = temp_path / "flows"
            flows_dir.mkdir(exist_ok=True)
            
            # Write input flows
            await self.write_input_flows(flows_dir, active_detectors)
            
            # Write output flows
            await self.write_output_flows(flows_dir, active_detectors)
            
            # Create RailsConfig and LLMRails
            rails_config = RailsConfig.from_path(str(temp_path))
            
            # Configure LLM in the config YAML instead of directly setting models
            # The models will be handled by the YAML configuration
            
            self.rails = LLMRails(rails_config)
            self.active_detectors = active_detectors
            
            app_logger.info("Guardrails configuration loaded successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to load configuration: {e}")
            raise GuardrailsException(f"Failed to load configuration: {e}")
    
    async def write_input_flows(self, flows_dir: Path, active_detectors: List[str]):
        """Write input flow files for active detectors"""
        try:
            input_flows = []
            
            # Base input flow
            input_flows.append("""
define flow check input
  $result = execute check_all_detectors(text=$user_message)
  
  if $result.blocked
    bot inform "I cannot process this message due to safety concerns: {' and '.join($result.blocking_reasons)}"
    stop
  else
    continue
""")
            
            # Individual detector flows
            if 'toxicity' in active_detectors:
                input_flows.append("""
define flow check toxicity
  $toxicity_result = execute check_toxicity(text=$user_message)
  
  if $toxicity_result.is_toxic
    bot inform "I cannot process messages containing toxic content."
    stop
""")
            
            if 'pii' in active_detectors:
                input_flows.append("""
define flow check pii
  $pii_result = execute check_pii(text=$user_message)
  
  if $pii_result.has_pii
    bot inform "Please remove any personal information from your message before proceeding."
    stop
""")
            
            if 'prompt_injection' in active_detectors:
                input_flows.append("""
define flow check prompt injection
  $injection_result = execute check_prompt_injection(text=$user_message)
  
  if $injection_result.is_injection
    bot inform "I cannot process messages that appear to be attempting prompt injection."
    stop
""")
            
            if 'topic' in active_detectors:
                input_flows.append("""
define flow check topics
  $topic_result = execute check_topics(text=$user_message)
  
  if $topic_result.has_restricted_topic
    bot inform "I cannot discuss that topic as it may involve restricted content."
    stop
""")
            
            if 'spam' in active_detectors:
                input_flows.append("""
define flow check spam
  $spam_result = execute check_spam(text=$user_message)
  
  if $spam_result.is_spam
    bot inform "This message appears to be spam and cannot be processed."
    stop
""")
            
            # Write input flows file
            input_flows_path = flows_dir / "input_flows.co"
            with open(input_flows_path, 'w') as f:
                f.write('\n'.join(input_flows))
            
            app_logger.info("Input flows written successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to write input flows: {e}")
            raise GuardrailsException(f"Failed to write input flows: {e}")
    
    async def write_output_flows(self, flows_dir: Path, active_detectors: List[str]):
        """Write output flow files for active detectors"""
        try:
            output_flows = []
            
            # Base output flow
            output_flows.append("""
define flow check output
  $response = execute chat_with_ollama
  
  # Check output with active detectors
  if "toxicity" in $active_detectors
    $toxicity_result = execute check_toxicity(text=$response)
    if $toxicity_result.is_toxic
      bot inform "I apologize, but I cannot provide that response due to safety concerns."
      stop
  
  if "fact_check" in $active_detectors
    $fact_result = execute check_facts(text=$response)
    if $fact_result.needs_fact_check
      bot inform "Please note that this response may contain claims that should be fact-checked."
  
  bot $response
""")
            
            # Individual output flows
            if 'toxicity' in active_detectors:
                output_flows.append("""
define flow check output toxicity
  $toxicity_result = execute check_toxicity(text=$bot_message)
  
  if $toxicity_result.is_toxic
    bot inform "I apologize, but I cannot provide that response due to safety concerns."
    stop
""")
            
            if 'fact_check' in active_detectors:
                output_flows.append("""
define flow check facts
  $fact_result = execute check_facts(text=$bot_message)
  
  if $fact_result.needs_fact_check
    bot inform "Please note that this response may contain claims that should be fact-checked: $bot_message"
    stop
""")
            
            # Write output flows file
            output_flows_path = flows_dir / "output_flows.co"
            with open(output_flows_path, 'w') as f:
                f.write('\n'.join(output_flows))
            
            app_logger.info("Output flows written successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to write output flows: {e}")
            raise GuardrailsException(f"Failed to write output flows: {e}")
    
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a message through the guardrails"""
        try:
            if not self.is_initialized:
                raise GuardrailsException("Guardrails not initialized")
            
            app_logger.info(f"Processing message through guardrails: {message[:100]}...")
            
            # Phase 4: Use multi-stage pipeline if available
            if self.use_phase4_pipeline and self.phase4_pipeline:
                return await self._process_with_phase4_pipeline(message, context)
            
            # Fallback to traditional processing
            return await self._process_with_traditional_guardrails(message, context)
            
        except Exception as e:
            app_logger.error(f"Failed to process message: {e}")
            raise GuardrailsException(f"Message processing failed: {e}")
    
    async def _process_with_phase4_pipeline(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process message using Phase 4 multi-stage pipeline"""
        try:
            app_logger.info("Processing with Phase 4 Multi-Stage Pipeline")
            
            # Create pipeline context
            pipeline_context = PipelineContext(
                conversation_history=context.get("conversation_history", []) if context else [],
                user_risk_score=context.get("user_risk_score", 0.0) if context else 0.0,
                domain_context=context.get("domain_context", "general") if context else "general",
                metadata=context or {}
            )
            
            # Define guardrail types to check
            guardrail_types = ["toxicity", "pii", "prompt_injection", "spam", "topic"]
            
            # Process through multi-stage pipeline
            pipeline_results = await self.phase4_pipeline.process(
                message, 
                guardrail_types, 
                pipeline_context
            )
            
            # Analyze results
            blocked = any(result.blocked for result in pipeline_results.values())
            blocking_reasons = []
            guardrails_triggered = {}
            max_confidence = 0.0
            
            for guardrail_type, result in pipeline_results.items():
                guardrails_triggered[guardrail_type] = {
                    "blocked": result.blocked,
                    "confidence": result.confidence,
                    "stage": result.stage.value,
                    "reasons": result.reasons,
                    "processing_time_ms": result.processing_time_ms,
                    "escalation_required": result.escalation_required
                }
                
                if result.blocked:
                    blocking_reasons.extend(result.reasons)
                    max_confidence = max(max_confidence, result.confidence)
            
            # Generate response based on results
            if blocked:
                response_text = "I cannot process this message due to safety concerns detected by our advanced guardrails system."
                if blocking_reasons:
                    response_text += f" Issues detected: {', '.join(set(blocking_reasons[:3]))}"
            else:
                # Generate AI response if not blocked
                response_text = await self._generate_safe_response(message, pipeline_context)
            
            return {
                "response": response_text,
                "blocked": blocked,
                "blocking_reasons": list(set(blocking_reasons)),
                "guardrails_results": guardrails_triggered,
                "pipeline_stage": "phase4_multi_stage",
                "max_confidence": max_confidence,
                "context": context,
                "metadata": {
                    "pipeline_performance": self.phase4_pipeline.get_performance_metrics(),
                    "total_processing_time": sum(r.processing_time_ms for r in pipeline_results.values())
                }
            }
            
        except Exception as e:
            app_logger.error(f"Phase 4 pipeline processing failed: {e}")
            # Fallback to traditional processing
            return await self._process_with_traditional_guardrails(message, context)
    
    async def _process_with_traditional_guardrails(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process message using traditional NeMo guardrails (fallback)"""
        try:
            # Prepare context
            if context is None:
                context = {}
            
            context['user_message'] = message
            context['active_detectors'] = self.active_detectors
            
            # Run input detection through all detectors first
            input_analysis = None
            if self.detection_service:
                app_logger.info("Running input detection through safety detectors...")
                input_detection_result = await self.detection_service.run_detection(
                    message,
                    detector_names=self.active_detectors
                )
                
                input_analysis = {
                    "user_message": message,
                    "active_detectors": self.active_detectors,
                    "detection_results": input_detection_result.get("results", {}),
                    "blocked": input_detection_result.get("blocked", False),
                    "blocking_reasons": input_detection_result.get("blocking_reasons", [])
                }
                
                # If input is blocked, return immediately
                if input_detection_result.get("blocked", False):
                    app_logger.warning(f"Input blocked by detectors: {input_detection_result.get('blocking_reasons', [])}")
                    return {
                        "response": "I cannot proceed with that request. Is there anything else I can help you with?",
                        "blocked": True,
                        "blocking_reasons": input_detection_result.get("blocking_reasons", []),
                        "context": context,
                        "input_analysis": input_analysis
                    }
            
            # Generate response through guardrails
            response = await self.rails.generate_async(
                messages=[{"role": "user", "content": message}]
            )
            
            # Extract response content
            if isinstance(response, dict):
                bot_response = response.get('content', str(response))
            else:
                bot_response = str(response)
            
            result = {
                "response": bot_response,
                "blocked": False,
                "blocking_reasons": [],
                "context": context,
                "input_analysis": input_analysis
            }
            
            app_logger.info("Message processed successfully through guardrails")
            return result
            
        except Exception as e:
            app_logger.error(f"Failed to process message through guardrails: {e}")
            
            # Return error response
            return {
                "response": "I apologize, but I encountered an error processing your message.",
                "blocked": True,
                "blocking_reasons": [f"Processing error: {str(e)}"],
                "context": context or {},
                "error": str(e)
            }
    
    async def _generate_safe_response(self, message: str, pipeline_context: PipelineContext) -> str:
        """Generate a safe AI response using the model manager"""
        try:
            # Simple safe response generation for now
            # In production, this would integrate with the LLM with safety constraints
            return f"Thank you for your message. How can I assist you further?"
            
        except Exception as e:
            app_logger.error(f"Failed to generate safe response: {e}")
            return "I'm here to help. How can I assist you today?"
    
    async def update_active_detectors(self, detectors: List[str]):
        """Update active detectors and reload configuration"""
        try:
            app_logger.info(f"Updating active detectors to: {detectors}")
            
            # Validate detectors
            valid_detectors = [d for d in detectors if d in self.model_manager.available_detectors]
            if len(valid_detectors) != len(detectors):
                invalid = set(detectors) - set(valid_detectors)
                app_logger.warning(f"Invalid detectors ignored: {invalid}")
            
            # Reload configuration with new detectors
            await self.load_configuration(valid_detectors)
            
            app_logger.info("Active detectors updated successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to update active detectors: {e}")
            raise GuardrailsException(f"Failed to update active detectors: {e}")
    
    def get_active_detectors(self) -> List[str]:
        """Get currently active detectors"""
        return self.active_detectors.copy()
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            "active_detectors": self.active_detectors,
            "is_initialized": self.is_initialized,
            "config_loader": {
                "active_detectors": self.config_loader.get_active_detectors()
            }
        }
    
    async def test_detector(self, detector_name: str, test_text: str) -> Dict[str, Any]:
        """Test a specific detector with given text"""
        try:
            if detector_name not in self.model_manager.available_detectors:
                raise ValueError(f"Unknown detector: {detector_name}")
            
            result = await self.model_manager.detect(test_text, detector_name)
            
            app_logger.info(f"Detector {detector_name} test completed")
            return result
            
        except Exception as e:
            app_logger.error(f"Failed to test detector {detector_name}: {e}")
            raise GuardrailsException(f"Failed to test detector {detector_name}: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            app_logger.info("Cleaning up GuardrailsManager...")
            
            self.rails = None
            self.active_detectors.clear()
            self.is_initialized = False
            
            app_logger.info("GuardrailsManager cleanup completed")
            
        except Exception as e:
            app_logger.error(f"Error during guardrails cleanup: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of guardrails"""
        return {
            "initialized": self.is_initialized,
            "active_detectors": self.active_detectors,
            "rails_loaded": self.rails is not None,
            "config_loader_active": self.config_loader.get_active_detectors()
        }