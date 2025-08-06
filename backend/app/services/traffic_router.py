"""
Traffic Router for managing requests across multiple LLM provider ports
"""
import asyncio
import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from app.services.provider_service import provider_service, Provider, ProviderStatus
from app.services.analytics_service import analytics_service, RequestStatus
from app.services.detection_service import DetectionService
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class TrafficRouter:
    """Routes traffic to appropriate providers with guardrail protection"""
    
    def __init__(self):
        self.running_servers: Dict[int, bool] = {}
        self.request_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.detection_service: Optional[DetectionService] = None
        self.config_service: Optional[ConfigService] = None
        
    def set_detection_service(self, detection_service: DetectionService):
        """Set the detection service for guardrail processing"""
        self.detection_service = detection_service
        
    def set_config_service(self, config_service: ConfigService):
        """Set the configuration service for getting user settings"""
        self.config_service = config_service
        
    async def create_provider_app(self, provider: Provider) -> FastAPI:
        """Create FastAPI app for a specific provider"""
        app = FastAPI(
            title=f"{provider.display_name} Proxy",
            description=f"Guardrail-protected proxy for {provider.display_name}",
            version="1.0.0"
        )
        
        # Add CORS middleware
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "provider": provider.display_name,
                "port": provider.port,
                "model": provider.selected_model,
                "timestamp": datetime.now().isoformat()
            }
        
        @app.post("/v1/chat/completions")
        async def chat_completions(request: Request):
            """Handle chat completion requests with guardrails"""
            return await self._handle_chat_request(provider, request)
        
        @app.post("/api/generate")  # Ollama format
        async def ollama_generate(request: Request):
            """Handle Ollama generate requests with guardrails"""
            return await self._handle_ollama_request(provider, request)
        
        @app.get("/api/tags")  # Ollama model listing
        async def ollama_tags():
            """List available Ollama models"""
            if provider.id != "ollama":
                raise HTTPException(status_code=404, detail="Endpoint only available for Ollama")
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:11434/api/tags")
                    return response.json()
            except Exception as e:
                logger.error(f"Error fetching Ollama models: {e}")
                raise HTTPException(status_code=503, detail="Ollama service unavailable")
        
        return app
    
    async def _handle_chat_request(self, provider: Provider, request: Request) -> JSONResponse:
        """Handle OpenAI-compatible chat completion requests"""
        start_time = datetime.now()
        
        # Get request details for analytics
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        try:
            # Parse request body
            body = await request.json()
            messages = body.get("messages", [])
            
            if not messages:
                raise HTTPException(status_code=400, detail="No messages provided")
            
            # Get the user message (last message or first user message)
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                raise HTTPException(status_code=400, detail="No user message found")
            
            # Apply guardrails to input
            input_safe, input_analysis, blocking_reasons = await self._apply_guardrails(user_message, "input")
            
            # Increment request count
            self.request_counts[provider.id] = self.request_counts.get(provider.id, 0) + 1
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if not input_safe:
                # Track blocked request in analytics
                analytics_service.track_request(
                    ip_address=client_ip,
                    user_agent=user_agent,
                    message=user_message,
                    status=RequestStatus.BLOCKED,
                    blocking_reasons=blocking_reasons,
                    detection_results=input_analysis,
                    response_time_ms=response_time,
                    provider=provider.display_name,
                    model=provider.selected_model
                )
                
                # Return blocked response
                return JSONResponse({
                    "blocked": True,
                    "blocking_reasons": blocking_reasons,
                    "input_analysis": input_analysis,
                    "provider": provider.display_name,
                    "timestamp": datetime.now().isoformat()
                }, status_code=200)
            
            # Forward request to actual provider
            response_content = await self._forward_to_provider(provider, body)
            
            # Extract AI response for output filtering
            ai_response = ""
            if isinstance(response_content, dict):
                choices = response_content.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    ai_response = message.get("content", "")
            
            # Apply guardrails to output
            output_safe, output_analysis, output_blocking_reasons = await self._apply_guardrails(ai_response, "output")
            
            # Calculate final response time
            final_response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if not output_safe:
                # Track blocked request in analytics
                analytics_service.track_request(
                    ip_address=client_ip,
                    user_agent=user_agent,
                    message=user_message,
                    status=RequestStatus.BLOCKED,
                    blocking_reasons=output_blocking_reasons,
                    detection_results=output_analysis,
                    response_time_ms=final_response_time,
                    provider=provider.display_name,
                    model=provider.selected_model
                )
                
                # Return blocked response
                return JSONResponse({
                    "blocked": True,
                    "blocking_reasons": output_blocking_reasons,
                    "output_analysis": output_analysis,
                    "provider": provider.display_name,
                    "timestamp": datetime.now().isoformat()
                }, status_code=200)
            
            # Track successful request in analytics
            analytics_service.track_request(
                ip_address=client_ip,
                user_agent=user_agent,
                message=user_message,
                status=RequestStatus.ALLOWED,
                blocking_reasons=[],
                detection_results={**input_analysis, **output_analysis},
                response_time_ms=final_response_time,
                provider=provider.display_name,
                model=provider.selected_model
            )
            
            # Return safe response with analysis
            if isinstance(response_content, dict):
                response_content["guardrails"] = {
                    "input_analysis": input_analysis,
                    "output_analysis": output_analysis,
                    "provider": provider.display_name,
                    "safe": True
                }
            
            return JSONResponse(response_content)
            
        except HTTPException:
            raise
        except Exception as e:
            self.error_counts[provider.id] = self.error_counts.get(provider.id, 0) + 1
            
            # Track error in analytics with graceful fallback
            error_response_time = (datetime.now() - start_time).total_seconds() * 1000
            try:
                analytics_service.track_request(
                    ip_address=client_ip,
                    user_agent=user_agent,
                    message=user_message if 'user_message' in locals() else "Unknown",
                    status=RequestStatus.ERROR,
                    blocking_reasons=[str(e)],
                    detection_results={},
                    response_time_ms=error_response_time,
                    provider=provider.display_name,
                    model=provider.selected_model
                )
            except Exception as analytics_error:
                logger.error(f"Failed to track error in analytics: {analytics_error}")
            
            logger.error(f"Error handling chat request for {provider.display_name}: {e}")
            
            # Provide graceful error response
            error_detail = {
                "error": "request_processing_failed",
                "message": f"Failed to process request: {str(e)}",
                "provider": provider.display_name,
                "timestamp": datetime.now().isoformat()
            }
            raise HTTPException(status_code=500, detail=error_detail)
    
    async def _handle_ollama_request(self, provider: Provider, request: Request) -> JSONResponse:
        """Handle Ollama-specific requests"""
        start_time = datetime.now()
        
        # Get request details for analytics
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        try:
            body = await request.json()
            prompt = body.get("prompt", "")
            
            if not prompt:
                raise HTTPException(status_code=400, detail="No prompt provided")
            
            # Apply guardrails to input
            input_safe, input_analysis, blocking_reasons = await self._apply_guardrails(prompt, "input")
            
            # Increment request count
            self.request_counts[provider.id] = self.request_counts.get(provider.id, 0) + 1
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if not input_safe:
                # Track blocked request in analytics
                analytics_service.track_request(
                    ip_address=client_ip,
                    user_agent=user_agent,
                    message=prompt,
                    status=RequestStatus.BLOCKED,
                    blocking_reasons=blocking_reasons,
                    detection_results=input_analysis,
                    response_time_ms=response_time,
                    provider=provider.display_name,
                    model=provider.selected_model
                )
                
                return JSONResponse({
                    "blocked": True,
                    "blocking_reasons": blocking_reasons,
                    "input_analysis": input_analysis,
                    "provider": provider.display_name,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Forward to Ollama
            response_content = await self._forward_ollama_request(provider, body)
            
            # Extract response for output filtering
            ai_response = response_content.get("response", "")
            
            # Apply guardrails to output
            output_safe, output_analysis, output_blocking_reasons = await self._apply_guardrails(ai_response, "output")
            
            # Calculate final response time
            final_response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if not output_safe:
                # Track blocked request in analytics
                analytics_service.track_request(
                    ip_address=client_ip,
                    user_agent=user_agent,
                    message=prompt,
                    status=RequestStatus.BLOCKED,
                    blocking_reasons=output_blocking_reasons,
                    detection_results=output_analysis,
                    response_time_ms=final_response_time,
                    provider=provider.display_name,
                    model=provider.selected_model
                )
                
                return JSONResponse({
                    "blocked": True,
                    "blocking_reasons": output_blocking_reasons,
                    "output_analysis": output_analysis,
                    "provider": provider.display_name,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Track successful request in analytics
            analytics_service.track_request(
                ip_address=client_ip,
                user_agent=user_agent,
                message=prompt,
                status=RequestStatus.ALLOWED,
                blocking_reasons=[],
                detection_results={**input_analysis, **output_analysis},
                response_time_ms=final_response_time,
                provider=provider.display_name,
                model=provider.selected_model
            )
            
            # Return safe response
            response_content["guardrails"] = {
                "input_analysis": input_analysis,
                "output_analysis": output_analysis,
                "provider": provider.display_name,
                "safe": True
            }
            
            return JSONResponse(response_content)
            
        except Exception as e:
            self.error_counts[provider.id] = self.error_counts.get(provider.id, 0) + 1
            
            # Track error in analytics
            error_response_time = (datetime.now() - start_time).total_seconds() * 1000
            analytics_service.track_request(
                ip_address=client_ip,
                user_agent=user_agent,
                message=prompt if 'prompt' in locals() else "Unknown",
                status=RequestStatus.ERROR,
                blocking_reasons=[str(e)],
                detection_results={},
                response_time_ms=error_response_time,
                provider=provider.display_name,
                model=provider.selected_model
            )
            
            logger.error(f"Error handling Ollama request: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _apply_guardrails(self, text: str, stage: str) -> Tuple[bool, Dict[str, Any], list]:
        """Apply guardrails to text using user configuration"""
        try:
            # SECURITY: If no detection service is available, BLOCK all traffic by default
            if not self.detection_service:
                logger.error("No detection service available, BLOCKING all traffic for security")
                return False, {"error": "No detection service available"}, ["Detection service unavailable - blocking for security"]
            
            # Get the current configuration
            enabled_detectors = []
            detector_configs = {}
            
            if self.config_service:
                # Get system configuration
                system_config = self.config_service.get_system_config()
                detector_system_config = system_config.get("detectors", {})
                
                # Get enabled detectors based on configuration
                for detector_name, config in detector_system_config.items():
                    if config.get("enabled", False):
                        enabled_detectors.append(detector_name)
                        detector_configs[detector_name] = config
                        
                # Also check guardrails configuration
                guardrails_config = system_config.get("guardrails", {})
                stage_enabled = guardrails_config.get(f"{stage}_enabled", True)
                
                # If stage is disabled, allow all traffic
                if not stage_enabled:
                    logger.info(f"Guardrails disabled for {stage} stage")
                    return True, {"stage_disabled": True}, []
            else:
                # Fallback: use default enabled detectors if no config service
                logger.warning("No config service available, using default detectors")
                enabled_detectors = ["toxicity", "pii", "prompt_injection"]
                detector_configs = {
                    detector: {"enabled": True, "threshold": 0.7} 
                    for detector in enabled_detectors
                }
            
            # SECURITY: If no detectors are enabled, BLOCK all traffic by default
            if not enabled_detectors:
                logger.warning("No detectors enabled, BLOCKING all traffic for security")
                return False, {"error": "No detectors enabled"}, ["No detectors enabled - blocking for security"]
            
            # Use the detection service to analyze the text with enabled detectors
            detection_result = await self.detection_service.run_detection(
                text=text,
                detector_names=enabled_detectors,
                detector_config=detector_configs
            )
            
            # Handle case where detection_result is None
            if detection_result is None:
                logger.error("Detection service returned None - blocking for safety")
                return False, {"error": "detection_service_returned_none"}, ["Detection service error"]
            
            # Extract results
            results = detection_result.get("results", {})
            is_safe = True  # Start with safe, then check each detector
            blocking_reasons = []
            
            # First check if the detection service already determined it's blocked
            detection_blocked = detection_result.get("blocked", False)
            if detection_blocked:
                is_safe = False
                # Get blocking reasons from detection service
                service_reasons = detection_result.get("blocking_reasons", [])
                blocking_reasons.extend(service_reasons)
            
            # Check each detector result for blocking
            for detector_name, result in results.items():
                if isinstance(result, dict):
                    # Handle the nested result structure: result['result'] contains the actual detection
                    actual_result = result.get('result', {})
                    
                    # Check various blocking indicators in the actual result
                    blocked = (
                        actual_result.get('blocked', False) or
                        actual_result.get('is_toxic', False) or
                        actual_result.get('has_pii', False) or
                        actual_result.get('is_injection', False) or
                        actual_result.get('has_restricted_topic', False) or
                        actual_result.get('is_spam', False) or
                        actual_result.get('needs_fact_check', False)
                    )
                    
                    if blocked:
                        is_safe = False
                        # Create informative blocking reason
                        confidence = actual_result.get('confidence', 0)
                        if confidence > 0:
                            reason = f"{detector_name} detection triggered (confidence: {confidence:.2f})"
                        else:
                            reason = f"{detector_name} detection triggered"
                        blocking_reasons.append(reason)
                        
                elif isinstance(result, bool) and result:
                    # Boolean true means blocked
                    is_safe = False
                    blocking_reasons.append(f"{detector_name} detection triggered")
            
            return is_safe, results, blocking_reasons
            
        except Exception as e:
            logger.error(f"Error applying guardrails: {e}")
            # Graceful error handling - provide detailed error info but default to safe behavior
            error_details = {
                "error": "guardrail_system_error",
                "message": str(e),
                "fallback_applied": True
            }
            return False, error_details, [f"Guardrail system error: {str(e)}"]
    
    async def _forward_to_provider(self, provider: Provider, body: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to the actual provider API"""
        try:
            if provider.id == "openai":
                return await self._forward_openai_request(provider, body)
            elif provider.id == "azure_openai":
                return await self._forward_azure_openai_request(provider, body)
            elif provider.id == "anthropic":
                return await self._forward_anthropic_request(provider, body)
            elif provider.id == "gemini":
                return await self._forward_gemini_request(provider, body)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown provider: {provider.id}")
                
        except Exception as e:
            logger.error(f"Error forwarding to {provider.display_name}: {e}")
            raise HTTPException(status_code=503, detail=f"Provider {provider.display_name} unavailable")
    
    async def _forward_openai_request(self, provider: Provider, body: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to OpenAI API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json"
                },
                json={**body, "model": provider.selected_model}
            )
            response.raise_for_status()
            return response.json()
    
    async def _forward_azure_openai_request(self, provider: Provider, body: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to Azure OpenAI API"""
        if not provider.azure_endpoint:
            raise HTTPException(status_code=400, detail="Azure endpoint not configured")
        if not provider.azure_deployment_name:
            raise HTTPException(status_code=400, detail="Azure deployment name not configured")
        
        # Clean endpoint URL - remove trailing slash if present
        endpoint = provider.azure_endpoint.rstrip('/')
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Azure OpenAI uses deployment-specific URLs
            url = f"{endpoint}/openai/deployments/{provider.azure_deployment_name}/chat/completions"
            
            response = await client.post(
                url,
                headers={
                    "api-key": provider.api_key,
                    "Content-Type": "application/json"
                },
                params={"api-version": provider.azure_api_version or "2024-10-21"},
                json={**body, "model": provider.selected_model}
            )
            response.raise_for_status()
            return response.json()
    
    async def _forward_anthropic_request(self, provider: Provider, body: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to Anthropic API"""
        # Convert OpenAI format to Anthropic format
        messages = body.get("messages", [])
        anthropic_messages = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            # Map roles (Anthropic uses 'user' and 'assistant')
            if role == "system":
                # Anthropic handles system messages differently
                if anthropic_messages and anthropic_messages[0]["role"] == "user":
                    anthropic_messages[0]["content"] = f"{content}\n\n{anthropic_messages[0]['content']}"
                else:
                    anthropic_messages.insert(0, {"role": "user", "content": content})
            elif role in ["user", "assistant"]:
                anthropic_messages.append({"role": role, "content": content})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": provider.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": provider.selected_model,
                    "max_tokens": body.get("max_tokens", 1000),
                    "messages": anthropic_messages
                }
            )
            response.raise_for_status()
            anthropic_response = response.json()
            
            # Convert back to OpenAI format
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": anthropic_response.get("content", [{}])[0].get("text", "")
                    },
                    "finish_reason": "stop"
                }],
                "usage": anthropic_response.get("usage", {}),
                "model": provider.selected_model
            }
    
    async def _forward_gemini_request(self, provider: Provider, body: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to Google Gemini API"""
        # Convert OpenAI format to Gemini format
        messages = body.get("messages", [])
        gemini_parts = []
        
        for msg in messages:
            content = msg.get("content", "")
            if content:
                gemini_parts.append({"text": content})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1/models/{provider.selected_model}:generateContent?key={provider.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": gemini_parts}],
                    "generationConfig": {
                        "maxOutputTokens": body.get("max_tokens", 1000),
                        "temperature": body.get("temperature", 0.7)
                    }
                }
            )
            response.raise_for_status()
            gemini_response = response.json()
            
            # Convert back to OpenAI format
            content = ""
            candidates = gemini_response.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    content = parts[0].get("text", "")
            
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "model": provider.selected_model
            }
    
    async def _forward_ollama_request(self, provider: Provider, body: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to Ollama"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={**body, "model": provider.selected_model}
            )
            response.raise_for_status()
            return response.json()
    
    async def start_provider_server(self, provider: Provider):
        """Start server for a specific provider"""
        if self.running_servers.get(provider.port, False):
            logger.info(f"Server for {provider.display_name} already running on port {provider.port}")
            return
        
        try:
            app = await self.create_provider_app(provider)
            
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=provider.port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            # Mark as running
            self.running_servers[provider.port] = True
            logger.info(f"Starting {provider.display_name} server on port {provider.port}")
            
            # Start server in background
            await server.serve()
            
        except Exception as e:
            logger.error(f"Error starting server for {provider.display_name}: {e}")
            self.running_servers[provider.port] = False
            raise
    
    async def stop_provider_server(self, provider: Provider):
        """Stop server for a specific provider"""
        if not self.running_servers.get(provider.port, False):
            return
        
        self.running_servers[provider.port] = False
        logger.info(f"Stopped {provider.display_name} server on port {provider.port}")
    
    def get_traffic_stats(self) -> Dict[str, Any]:
        """Get traffic statistics"""
        return {
            "request_counts": dict(self.request_counts),
            "error_counts": dict(self.error_counts),
            "running_servers": dict(self.running_servers),
            "total_requests": sum(self.request_counts.values()),
            "total_errors": sum(self.error_counts.values())
        }

# Global traffic router instance
traffic_router = TrafficRouter()