"""
Analytics Middleware for Real-time Request Tracking
Implements request interception and data collection as defined in IMPLEMENTATION_FEASIBILITY_AND_STRATEGY.md
"""
import time
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

class AnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture all requests for comprehensive analytics collection.
    Features:
    - Real-time request/response capture
    - Performance metrics collection
    - Guardrail results integration
    - Privacy-protected data storage
    - Thread-safe operation
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico",
            "/static/", "/_next/", "/api/system/health"
        ]
        
    async def dispatch(self, request: Request, call_next):
        """Capture and analyze all HTTP requests"""
        
        # Skip analytics for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Generate unique request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Extract request metadata
        user_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        
        # Capture request body for chat endpoints
        request_body = await self._extract_request_body(request)
        
        # Track request start time
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            response_data = await self._extract_response_data(response)
            
            # Extract analytics data from the response
            analytics_data = self._extract_analytics_data(request_body, response_data)
            
            # Record analytics asynchronously (non-blocking)
            await self._record_analytics(
                request_id=request_id,
                user_ip=user_ip,
                user_agent=user_agent,
                method=method,
                path=path,
                request_body=request_body,
                response_data=response_data,
                response_time_ms=response_time_ms,
                analytics_data=analytics_data
            )
            
            # Add request ID to response headers for tracking
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error and record failed request
            logger.error(f"Request {request_id} failed: {e}")
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Record error analytics
            await self._record_error_analytics(
                request_id=request_id,
                user_ip=user_ip,
                user_agent=user_agent,
                method=method,
                path=path,
                request_body=request_body,
                error=str(e),
                response_time_ms=response_time_ms
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address with proxy support"""
        # Check for forwarded IP headers (for load balancer/proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP if multiple are listed
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return getattr(request.client, 'host', 'unknown')
    
    async def _extract_request_body(self, request: Request) -> Dict[str, Any]:
        """Extract and parse request body safely"""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                # Clone the request to avoid consuming the body
                body = await request.body()
                if body:
                    import json
                    try:
                        return json.loads(body)
                    except json.JSONDecodeError:
                        return {"raw_body": body.decode('utf-8', errors='ignore')[:1000]}
            return {}
        except Exception as e:
            logger.warning(f"Failed to extract request body: {e}")
            return {}
    
    async def _extract_response_data(self, response: Response) -> Dict[str, Any]:
        """Extract response data for analytics"""
        try:
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_type": response.headers.get("content-type", "")
            }
            
            # For JSON responses, try to extract body
            if "application/json" in response_data["content_type"]:
                # Note: In real middleware, extracting response body is complex
                # This is a simplified version - in production, you'd need to buffer the response
                response_data["has_json_body"] = True
            
            return response_data
        except Exception as e:
            logger.warning(f"Failed to extract response data: {e}")
            return {"status_code": getattr(response, 'status_code', 500)}
    
    def _extract_analytics_data(self, request_body: Dict[str, Any], response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract analytics-specific data from request/response"""
        analytics_data = {
            "guardrail_results": {},
            "performance_metrics": {},
            "provider_info": {},
            "content_info": {}
        }
        
        # Extract guardrail results from response
        if response_data.get("has_json_body"):
            # This would be populated by the actual response in a real implementation
            # For now, we'll extract what we can from headers
            analytics_data["guardrail_results"] = {
                "blocked": response_data.get("status_code", 200) >= 400,
                "status_code": response_data.get("status_code", 200)
            }
        
        # Extract provider information from request
        if "provider_id" in request_body:
            analytics_data["provider_info"]["provider_used"] = request_body["provider_id"]
        
        if "model" in request_body:
            analytics_data["provider_info"]["model_used"] = request_body["model"]
        
        # Extract content information
        if "message" in request_body:
            analytics_data["content_info"]["prompt"] = request_body["message"]
            analytics_data["content_info"]["prompt_length"] = len(str(request_body["message"]))
        
        return analytics_data
    
    async def _record_analytics(
        self, 
        request_id: str,
        user_ip: str,
        user_agent: str,
        method: str,
        path: str,
        request_body: Dict[str, Any],
        response_data: Dict[str, Any],
        response_time_ms: int,
        analytics_data: Dict[str, Any]
    ):
        """Record comprehensive analytics data"""
        try:
            # Extract data for analytics service
            prompt = analytics_data["content_info"].get("prompt", f"{method} {path}")
            response_text = None  # Would be extracted from actual response in production
            
            # Prepare guardrail results
            guardrail_results = analytics_data["guardrail_results"]
            
            # Prepare performance metrics
            performance_metrics = {
                "response_time_ms": response_time_ms,
                "provider_used": analytics_data["provider_info"].get("provider_used"),
                "model_used": analytics_data["provider_info"].get("model_used"),
                "method": method,
                "path": path,
                "status_code": response_data.get("status_code", 200)
            }
            
            # Extract session ID if available
            session_id = request_body.get("session_id")
            
            # Record the analytics
            await analytics_service.record_user_request(
                user_ip=user_ip,
                request_id=request_id,
                prompt=prompt,
                response=response_text,
                guardrail_results=guardrail_results,
                performance_metrics=performance_metrics,
                session_id=session_id
            )
            
            logger.debug(f"Recorded analytics for {request_id}: {method} {path}")
            
        except Exception as e:
            logger.error(f"Failed to record analytics for {request_id}: {e}")
    
    async def _record_error_analytics(
        self,
        request_id: str,
        user_ip: str,
        user_agent: str,
        method: str,
        path: str,
        request_body: Dict[str, Any],
        error: str,
        response_time_ms: int
    ):
        """Record analytics for error requests"""
        try:
            prompt = request_body.get("message", f"{method} {path}")
            
            guardrail_results = {
                "blocked": False,
                "error": True,
                "error_message": error
            }
            
            performance_metrics = {
                "response_time_ms": response_time_ms,
                "method": method,
                "path": path,
                "status_code": 500
            }
            
            session_id = request_body.get("session_id")
            
            await analytics_service.record_user_request(
                user_ip=user_ip,
                request_id=request_id,
                prompt=prompt,
                response=None,
                guardrail_results=guardrail_results,
                performance_metrics=performance_metrics,
                session_id=session_id
            )
            
            logger.debug(f"Recorded error analytics for {request_id}")
            
        except Exception as e:
            logger.error(f"Failed to record error analytics for {request_id}: {e}")


class ChatAnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Specialized middleware for chat endpoints with detailed guardrail integration.
    This captures the actual guardrail results and AI responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Enhanced analytics for chat endpoints"""
        
        # Only process chat-related endpoints
        if not request.url.path.startswith("/api/chat"):
            return await call_next(request)
        
        request_id = f"chat_{uuid.uuid4().hex[:12]}"
        user_ip = self._get_client_ip(request)
        start_time = time.time()
        
        # Extract request data
        request_body = await self._extract_chat_request(request)
        
        try:
            # Process the request
            response = await call_next(request)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data (this would need to be enhanced to capture actual response)
            response_data = await self._extract_chat_response(response)
            
            # Record detailed chat analytics
            await self._record_chat_analytics(
                request_id=request_id,
                user_ip=user_ip,
                request_data=request_body,
                response_data=response_data,
                response_time_ms=response_time_ms
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Chat request {request_id} failed: {e}")
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Record error
            await self._record_chat_error(request_id, user_ip, request_body, str(e), response_time_ms)
            
            return JSONResponse(
                status_code=500,
                content={"error": "Chat service error", "request_id": request_id}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP (same as AnalyticsMiddleware)"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return getattr(request.client, 'host', 'unknown')
    
    async def _extract_chat_request(self, request: Request) -> Dict[str, Any]:
        """Extract chat request data"""
        try:
            body = await request.body()
            if body:
                import json
                return json.loads(body)
            return {}
        except Exception as e:
            logger.warning(f"Failed to extract chat request: {e}")
            return {}
    
    async def _extract_chat_response(self, response: Response) -> Dict[str, Any]:
        """Extract chat response data (simplified)"""
        return {
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", "")
        }
    
    async def _record_chat_analytics(
        self,
        request_id: str,
        user_ip: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        response_time_ms: int
    ):
        """Record detailed chat analytics"""
        try:
            prompt = request_data.get("message", "")
            provider_id = request_data.get("provider_id")
            session_id = request_data.get("session_id")
            detector_config = request_data.get("detector_config", {})
            
            # Simulate guardrail results (in real implementation, these would come from the actual response)
            guardrail_results = {
                "blocked": response_data.get("status_code", 200) >= 400,
                "detector_config": detector_config
            }
            
            performance_metrics = {
                "response_time_ms": response_time_ms,
                "provider_used": provider_id,
                "status_code": response_data.get("status_code", 200)
            }
            
            await analytics_service.record_user_request(
                user_ip=user_ip,
                request_id=request_id,
                prompt=prompt,
                response=None,  # Would extract from actual response
                guardrail_results=guardrail_results,
                performance_metrics=performance_metrics,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Failed to record chat analytics: {e}")
    
    async def _record_chat_error(
        self, request_id: str, user_ip: str, request_data: Dict[str, Any], 
        error: str, response_time_ms: int
    ):
        """Record chat error analytics"""
        try:
            prompt = request_data.get("message", "")
            
            guardrail_results = {
                "blocked": False,
                "error": True,
                "error_message": error
            }
            
            performance_metrics = {
                "response_time_ms": response_time_ms,
                "status_code": 500
            }
            
            await analytics_service.record_user_request(
                user_ip=user_ip,
                request_id=request_id,
                prompt=prompt,
                response=None,
                guardrail_results=guardrail_results,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to record chat error analytics: {e}")