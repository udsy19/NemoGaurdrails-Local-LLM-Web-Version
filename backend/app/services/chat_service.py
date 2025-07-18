import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.guardrails.guardrails_manager import GuardrailsManager
from app.utils.logger import app_logger
from app.utils.exceptions import GuardrailsException
from app.services.analytics_service import analytics_service, RequestStatus

class ChatService:
    def __init__(self, model_manager, detection_service):
        self.model_manager = model_manager
        self.detection_service = detection_service
        self.guardrails_manager = GuardrailsManager(model_manager, detection_service=detection_service)
        self.chat_history = {}
        self.session_configs = {}
        
    async def initialize(self):
        """Initialize chat service"""
        try:
            await self.guardrails_manager.initialize()
            app_logger.info("Chat service initialized successfully")
        except Exception as e:
            app_logger.error(f"Failed to initialize chat service: {e}")
            raise GuardrailsException(f"Chat service initialization failed: {e}")
    
    async def process_message(
        self,
        message: str,
        detector_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        provider_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a chat message through the safety pipeline"""
        start_time = datetime.now()
        request_status = RequestStatus.ERROR
        blocking_reasons = []
        detection_results = {}
        
        try:
            # Generate session ID if not provided
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Initialize session if new
            if session_id not in self.chat_history:
                self.chat_history[session_id] = []
                self.session_configs[session_id] = detector_config or {}
            
            # Update detector config for session
            if detector_config:
                self.session_configs[session_id].update(detector_config)
            
            app_logger.info(f"Processing message for session {session_id}: {message[:100]}...")
            
            # Validate input
            validation_result = await self.detection_service.validate_input(message)
            if not validation_result["valid"]:
                request_status = RequestStatus.BLOCKED
                blocking_reasons = validation_result["errors"]
                
                # Track analytics for blocked input
                if ip_address:
                    analytics_service.track_request(
                        ip_address=ip_address,
                        user_agent=user_agent or "unknown",
                        message=message,
                        status=request_status,
                        blocking_reasons=blocking_reasons,
                        detection_results=validation_result,
                        response_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        session_id=session_id
                    )
                
                return {
                    "response": "I cannot process this message due to input validation errors.",
                    "blocked": True,
                    "blocking_reasons": validation_result["errors"],
                    "session_id": session_id,
                    "message_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Create message record
            message_record = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            # Process through detectors only (simplified mode)
            try:
                # Use guardrails if initialized, otherwise fall back to simple detection
                if hasattr(self.guardrails_manager, 'is_initialized') and self.guardrails_manager.is_initialized:
                    # Add provider_id to context if specified
                    if provider_id:
                        context = context or {}
                        context["provider_id"] = provider_id
                    
                    guardrails_result = await self.guardrails_manager.process_message(
                        message, 
                        context=context
                    )
                else:
                    # Simplified detection using just the detection service
                    app_logger.info("Using simplified detection mode (guardrails not initialized)")
                    
                    # Get detector names from session config or use enabled detectors from detector_config
                    session_config = self.session_configs.get(session_id, {})
                    if session_config:
                        # Use only enabled detectors from config
                        enabled_detectors = [name for name, config in session_config.items() 
                                           if config.get("enabled", False)]
                    else:
                        # If no config, don't run any detectors
                        enabled_detectors = []
                    
                    # Log detector status for debugging
                    app_logger.info(f"Session {session_id} detector config: {session_config}")
                    app_logger.info(f"Enabled detectors: {enabled_detectors}")
                    
                    # If no detectors are enabled, skip detection entirely
                    if not enabled_detectors:
                        app_logger.info("No detectors enabled - allowing message without detection")
                        # Generate AI response directly
                        ai_response = await self._generate_ai_response(message, session_id)
                        request_status = RequestStatus.ALLOWED
                        
                        guardrails_result = {
                            "response": ai_response,
                            "blocked": False,
                            "blocking_reasons": [],
                            "input_analysis": {},
                            "output_analysis": {}
                        }
                    else:
                        detection_results = await self.detection_service.run_detection(
                            message, 
                            detector_names=enabled_detectors,
                            detector_config=session_config
                        )
                        
                        # Check if input was blocked
                        if detection_results.get("blocked", False):
                            request_status = RequestStatus.BLOCKED
                            blocking_reasons = detection_results.get("blocking_reasons", [])
                            detection_results_data = detection_results.get("results", {})
                            
                            guardrails_result = {
                                "response": "I cannot provide a response to this message as it was flagged by our safety systems.",
                                "blocked": True,
                                "blocking_reasons": blocking_reasons,
                                "input_analysis": detection_results_data,
                                "output_analysis": None
                            }
                        else:
                            # Generate AI response using Ollama
                            ai_response = await self._generate_ai_response(message, session_id)
                            
                            # Analyze AI response using same detector configuration
                            output_detection = await self.detection_service.run_detection(
                                ai_response,
                                detector_names=enabled_detectors,
                                detector_config=session_config
                            )
                            
                            if output_detection.get("blocked", False):
                                request_status = RequestStatus.BLOCKED
                                blocking_reasons = output_detection.get("blocking_reasons", [])
                                detection_results_data = {
                                    "input": detection_results.get("results", {}),
                                    "output": output_detection.get("results", {})
                                }
                                
                                guardrails_result = {
                                    "response": "I apologize, but I cannot provide a response as my output was flagged by safety systems.",
                                    "blocked": True,
                                    "blocking_reasons": blocking_reasons,
                                    "input_analysis": detection_results.get("results", {}),
                                    "output_analysis": output_detection.get("results", {})
                                }
                            else:
                                request_status = RequestStatus.ALLOWED
                                blocking_reasons = []
                                detection_results_data = {
                                    "input": detection_results.get("results", {}),
                                    "output": output_detection.get("results", {})
                                }
                                
                                guardrails_result = {
                                    "response": ai_response,
                                    "blocked": False,
                                    "blocking_reasons": [],
                                    "input_analysis": detection_results.get("results", {}),
                                    "output_analysis": output_detection.get("results", {})
                                }
            except Exception as e:
                app_logger.error(f"Error in detection process: {e}")
                guardrails_result = {
                    "response": "I apologize, but I encountered an error processing your message.",
                    "blocked": True,
                    "blocking_reasons": [f"Processing error: {str(e)}"],
                    "input_analysis": None,
                    "output_analysis": None
                }
            
            # Handle blocked messages
            if guardrails_result["blocked"]:
                # Update request status to blocked
                request_status = RequestStatus.BLOCKED
                blocking_reasons = guardrails_result["blocking_reasons"]
                
                response_record = {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": guardrails_result["response"],
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "blocked": True,
                    "blocking_reasons": guardrails_result["blocking_reasons"]
                }
                
                # Track analytics for blocked response
                if ip_address:
                    # Ensure detection_results_data is defined from the guardrails_result
                    if 'detection_results_data' not in locals():
                        detection_results_data = guardrails_result.get("input_analysis", {})
                    
                    app_logger.info(f"Tracking blocked request: status={request_status}, reasons={blocking_reasons}, detection_results={detection_results_data}")
                    analytics_service.track_request(
                        ip_address=ip_address,
                        user_agent=user_agent or "unknown",
                        message=message,
                        status=request_status,
                        blocking_reasons=blocking_reasons,
                        detection_results=detection_results_data,
                        response_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                        session_id=session_id
                    )
                
                # Add to history
                self.chat_history[session_id].extend([message_record, response_record])
                
                return {
                    "response": guardrails_result["response"],
                    "blocked": True,
                    "blocking_reasons": guardrails_result["blocking_reasons"],
                    "session_id": session_id,
                    "message_id": response_record["id"],
                    "timestamp": response_record["timestamp"]
                }
            
            # Generate response using Ollama
            try:
                # Prepare conversation context
                conversation_messages = []
                
                # Add recent chat history for context
                recent_history = self.chat_history[session_id][-10:]  # Last 10 messages
                for msg in recent_history:
                    if not msg.get("blocked", False):
                        conversation_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                
                # Add current message
                conversation_messages.append({
                    "role": "user",
                    "content": message
                })
                
                # Generate response
                ollama_response = await self.model_manager.ollama_client.chat(
                    conversation_messages
                )
                
                assistant_response = ollama_response.get("message", {}).get("content", "I apologize, but I couldn't generate a response.")
                
            except Exception as e:
                app_logger.error(f"Ollama response generation failed: {e}")
                assistant_response = "I apologize, but I encountered an error while generating a response."
            
            # Process assistant response through output guardrails using same configuration
            # Use the same enabled detectors for output analysis as input
            session_config = self.session_configs.get(session_id, {})
            if session_config:
                enabled_detectors = [name for name, config in session_config.items() 
                                   if config.get("enabled", False)]
            else:
                enabled_detectors = []
            
            # Only run output detection if detectors are enabled
            if enabled_detectors:
                output_result = await self.detection_service.run_detection(
                    assistant_response,
                    detector_names=enabled_detectors,
                    detector_config=session_config
                )
            else:
                # No detectors enabled - skip output detection
                output_result = {
                    "blocked": False,
                    "blocking_reasons": [],
                    "results": {}
                }
            
            # Handle output blocking
            if output_result["blocked"]:
                assistant_response = "I apologize, but I cannot provide that response due to safety concerns."
                output_blocked = True
                output_blocking_reasons = output_result["blocking_reasons"]
            else:
                output_blocked = False
                output_blocking_reasons = []
            
            # Create response record
            response_record = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "blocked": output_blocked,
                "blocking_reasons": output_blocking_reasons,
                "output_analysis": output_result
            }
            
            # Add to history
            self.chat_history[session_id].extend([message_record, response_record])
            
            # Track analytics for response (successful or output blocked)
            final_status = RequestStatus.BLOCKED if output_blocked else RequestStatus.ALLOWED
            final_blocking_reasons = output_blocking_reasons if output_blocked else []
            
            if ip_address:
                analytics_service.track_request(
                    ip_address=ip_address,
                    user_agent=user_agent or "unknown",
                    message=message,
                    status=final_status,
                    blocking_reasons=final_blocking_reasons,
                    detection_results=output_result,
                    response_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    session_id=session_id
                )
            
            # Prepare response
            response = {
                "response": assistant_response,
                "blocked": output_blocked,
                "blocking_reasons": output_blocking_reasons,
                "session_id": session_id,
                "message_id": response_record["id"],
                "timestamp": response_record["timestamp"],
                "input_analysis": guardrails_result.get("context", {}),
                "output_analysis": output_result
            }
            
            # Add warnings if any
            if output_result.get("warnings"):
                response["warnings"] = output_result["warnings"]
            
            app_logger.info(f"Message processed successfully for session {session_id}")
            return response
            
        except Exception as e:
            app_logger.error(f"Failed to process message: {e}")
            
            # Track analytics for error case
            if ip_address:
                analytics_service.track_request(
                    ip_address=ip_address,
                    user_agent=user_agent or "unknown",
                    message=message,
                    status=RequestStatus.ERROR,
                    blocking_reasons=[f"Processing error: {str(e)}"],
                    detection_results={"error": str(e)},
                    response_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    session_id=session_id or "error"
                )
            
            return {
                "response": "I apologize, but I encountered an error processing your message.",
                "blocked": True,
                "blocking_reasons": [f"Processing error: {str(e)}"],
                "session_id": session_id or "error",
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        try:
            if session_id not in self.chat_history:
                return []
            
            history = self.chat_history[session_id]
            
            # Return most recent messages up to limit
            return history[-limit:] if len(history) > limit else history
            
        except Exception as e:
            app_logger.error(f"Failed to get chat history: {e}")
            return []
    
    async def clear_chat_history(self, session_id: str) -> bool:
        """Clear chat history for a session"""
        try:
            if session_id in self.chat_history:
                del self.chat_history[session_id]
            
            if session_id in self.session_configs:
                del self.session_configs[session_id]
            
            app_logger.info(f"Chat history cleared for session {session_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to clear chat history: {e}")
            return False
    
    async def update_detector_config(self, session_id: str, detector_config: Dict[str, Any]) -> bool:
        """Update detector configuration for a session"""
        try:
            if session_id not in self.session_configs:
                self.session_configs[session_id] = {}
            
            self.session_configs[session_id].update(detector_config)
            
            # Update guardrails manager with new configuration
            active_detectors = list(detector_config.keys())
            await self.guardrails_manager.update_active_detectors(active_detectors)
            
            app_logger.info(f"Detector config updated for session {session_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to update detector config: {e}")
            return False
    
    def get_session_config(self, session_id: str) -> Dict[str, Any]:
        """Get detector configuration for a session"""
        return self.session_configs.get(session_id, {})
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.chat_history.keys())
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        try:
            if session_id not in self.chat_history:
                return {"error": "Session not found"}
            
            history = self.chat_history[session_id]
            
            stats = {
                "session_id": session_id,
                "total_messages": len(history),
                "user_messages": len([msg for msg in history if msg["role"] == "user"]),
                "assistant_messages": len([msg for msg in history if msg["role"] == "assistant"]),
                "blocked_messages": len([msg for msg in history if msg.get("blocked", False)]),
                "config": self.session_configs.get(session_id, {})
            }
            
            if history:
                stats["first_message"] = history[0]["timestamp"]
                stats["last_message"] = history[-1]["timestamp"]
            
            return stats
            
        except Exception as e:
            app_logger.error(f"Failed to get session stats: {e}")
            return {"error": str(e)}
    
    async def export_chat_history(self, session_id: str, format: str = "json") -> Dict[str, Any]:
        """Export chat history in specified format"""
        try:
            if session_id not in self.chat_history:
                return {"error": "Session not found"}
            
            history = self.chat_history[session_id]
            
            if format == "json":
                return {
                    "session_id": session_id,
                    "export_timestamp": datetime.now().isoformat(),
                    "message_count": len(history),
                    "messages": history
                }
            
            elif format == "text":
                text_export = []
                for msg in history:
                    role = msg["role"].title()
                    content = msg["content"]
                    timestamp = msg["timestamp"]
                    
                    text_export.append(f"[{timestamp}] {role}: {content}")
                    
                    if msg.get("blocked", False):
                        text_export.append(f"    [BLOCKED: {', '.join(msg['blocking_reasons'])}]")
                
                return {
                    "session_id": session_id,
                    "export_timestamp": datetime.now().isoformat(),
                    "format": "text",
                    "content": "\n".join(text_export)
                }
            
            else:
                return {"error": f"Unsupported format: {format}"}
            
        except Exception as e:
            app_logger.error(f"Failed to export chat history: {e}")
            return {"error": str(e)}
    
    async def _generate_ai_response(self, message: str, session_id: str) -> str:
        """Generate AI response using Ollama"""
        try:
            # Get chat history for context
            history = self.chat_history.get(session_id, [])
            
            # Build conversation context
            conversation = []
            for msg in history[-10:]:  # Last 10 messages for context
                conversation.append(f"{msg['role']}: {msg['content']}")
            
            # Add current user message
            conversation.append(f"user: {message}")
            
            # Create prompt
            prompt = f"""You are a helpful AI assistant. Please respond to the user's message appropriately.

Conversation:
{chr(10).join(conversation)}

assistant:"""

            # Generate response using Ollama
            response = await self.model_manager.ollama_client.generate(
                model="llama3.1:latest",
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "top_p": 0.9
                }
            )
            
            if response and "response" in response:
                return response["response"].strip()
            else:
                return "I apologize, but I couldn't generate a response at this time."
                
        except Exception as e:
            app_logger.error(f"Failed to generate AI response: {e}")
            return "I apologize, but I encountered an error while generating a response."

    async def cleanup(self):
        """Clean up resources"""
        try:
            app_logger.info("Cleaning up ChatService...")
            
            await self.guardrails_manager.cleanup()
            
            self.chat_history.clear()
            self.session_configs.clear()
            
            app_logger.info("ChatService cleanup completed")
            
        except Exception as e:
            app_logger.error(f"Error during chat service cleanup: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of chat service"""
        return {
            "initialized": self.guardrails_manager.is_initialized,
            "active_sessions": len(self.chat_history),
            "guardrails_health": self.guardrails_manager.get_health_status(),
            "total_messages": sum(len(history) for history in self.chat_history.values())
        }