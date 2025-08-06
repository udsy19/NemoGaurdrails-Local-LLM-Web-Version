"""
Provider Service for managing multiple LLM providers with port-based routing
"""
import asyncio
import logging
import socket
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import httpx
import json
import os
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ProviderStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    TESTING = "testing"
    ERROR = "error"

@dataclass
class LLMModel:
    id: str
    name: str
    description: str
    context_length: int
    pricing: Optional[Dict[str, float]] = None

@dataclass
class Provider:
    id: str
    name: str
    display_name: str
    description: str
    port: int
    requires_api_key: bool
    models: List[LLMModel]
    enabled: bool = False
    api_key: str = ""
    selected_model: str = ""
    status: ProviderStatus = ProviderStatus.DISCONNECTED
    last_tested: Optional[datetime] = None
    error_message: Optional[str] = None
    # Azure OpenAI specific fields
    azure_endpoint: str = ""
    azure_api_version: str = "2024-10-21"
    azure_deployment_name: str = ""

class ProviderService:
    """Manages multiple LLM providers with port-based routing"""
    
    def __init__(self):
        self.providers: Dict[str, Provider] = {}
        self.port_mapping: Dict[int, str] = {}  # port -> provider_id
        self.running_services: Dict[str, bool] = {}  # provider_id -> is_running
        self.server_tasks: Dict[str, asyncio.Task] = {}  # provider_id -> server_task
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Add locks to prevent race conditions
        self._provider_locks: Dict[str, asyncio.Lock] = {}  # provider_id -> lock
        self._global_lock = asyncio.Lock()
        
        self._initialize_default_providers()
    
    def _initialize_default_providers(self):
        """Initialize default provider configurations"""
        
        # OpenAI - Updated 2025 model strings
        openai_models = [
            LLMModel("gpt-4o", "GPT-4o (Omni)", "Latest flagship model with text, vision, and advanced reasoning", 128000, {"input": 0.0025, "output": 0.01}),
            LLMModel("gpt-4o-mini", "GPT-4o Mini", "Lightweight, cheaper GPT-4o with strong reasoning", 128000, {"input": 0.00015, "output": 0.0006}),
            LLMModel("gpt-4-turbo", "GPT-4 Turbo", "Prior generation turbo-optimized GPT-4", 128000, {"input": 0.01, "output": 0.03}),
            LLMModel("gpt-4", "GPT-4", "Original GPT-4 model", 8192, {"input": 0.03, "output": 0.06}),
            LLMModel("gpt-3.5-turbo", "GPT-3.5 Turbo", "Fast and efficient for most tasks", 16385, {"input": 0.001, "output": 0.002}),
            LLMModel("gpt-3.5-turbo-instruct", "GPT-3.5 Turbo Instruct", "Instruct variant for prompt-based completions", 4096, {"input": 0.0015, "output": 0.002})
        ]
        openai = Provider(
            id="openai",
            name="openai",
            display_name="OpenAI",
            description="GPT models including GPT-4, GPT-3.5-turbo with advanced reasoning capabilities",
            port=8891,
            requires_api_key=True,
            models=openai_models,
            selected_model="gpt-4o"
        )
        
        # Anthropic - Updated 2025 model strings
        anthropic_models = [
            LLMModel("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet", "Latest and most capable Claude model", 200000, {"input": 0.003, "output": 0.015}),
            LLMModel("claude-3-opus-20240229", "Claude 3 Opus", "Most powerful model for complex reasoning", 200000, {"input": 0.015, "output": 0.075}),
            LLMModel("claude-3-sonnet-20240229", "Claude 3 Sonnet", "Balanced performance and speed", 200000, {"input": 0.003, "output": 0.015}),
            LLMModel("claude-3-haiku-20240307", "Claude 3 Haiku", "Fastest model for quick tasks", 200000, {"input": 0.00025, "output": 0.00125})
        ]
        anthropic = Provider(
            id="anthropic",
            name="anthropic",
            display_name="Anthropic Claude",
            description="Claude models with constitutional AI training for helpful, harmless responses",
            port=8892,
            requires_api_key=True,
            models=anthropic_models,
            selected_model="claude-3-5-sonnet-20241022"
        )
        
        # Google Gemini - Updated 2025 model strings
        gemini_models = [
            LLMModel("gemini-2.0-flash-exp", "Gemini 2.0 Flash", "Latest multimodal model with advanced capabilities", 1000000, {"input": 0.000075, "output": 0.0003}),
            LLMModel("gemini-1.5-pro", "Gemini 1.5 Pro", "Most capable Gemini model for complex tasks", 2000000, {"input": 0.00125, "output": 0.005}),
            LLMModel("gemini-1.5-flash", "Gemini 1.5 Flash", "Fast and efficient for most tasks", 1000000, {"input": 0.000075, "output": 0.0003}),
            LLMModel("gemini-1.0-pro", "Gemini 1.0 Pro", "Original Gemini Pro model", 32760, {"input": 0.0005, "output": 0.0015})
        ]
        gemini = Provider(
            id="gemini",
            name="gemini",
            display_name="Google Gemini",
            description="Google's multimodal AI with excellent reasoning and coding capabilities",
            port=8893,
            requires_api_key=True,
            models=gemini_models,
            selected_model="gemini-2.0-flash-exp"
        )
        
        # Ollama - Updated 2025 popular models
        ollama_models = [
            LLMModel("llama3.2", "Llama 3.2", "Meta's latest open-source model (1B/3B/11B/90B)", 131072),
            LLMModel("llama3.1", "Llama 3.1", "Previous generation Llama model (8B/70B/405B)", 131072),
            LLMModel("qwen2.5", "Qwen 2.5", "Alibaba's multilingual model (0.5B-72B)", 32768),
            LLMModel("mistral", "Mistral", "High-quality 7B parameter model", 32768),
            LLMModel("codellama", "Code Llama", "Specialized for code generation", 16384),
            LLMModel("phi3", "Phi 3", "Microsoft's efficient small language model", 128000),
            LLMModel("gemma2", "Gemma 2", "Google's latest Gemma model (2B/9B/27B)", 8192),
            LLMModel("deepseek-coder", "DeepSeek Coder", "Specialized for coding tasks", 16384)
        ]
        ollama = Provider(
            id="ollama",
            name="ollama",
            display_name="Ollama (Local)",
            description="Local models running on your machine - private and free",
            port=8895,
            requires_api_key=False,
            models=ollama_models,
            selected_model="llama3.2"
        )
        
        # Azure OpenAI - Same models as regular OpenAI but via Azure endpoints
        azure_openai_models = [
            LLMModel("gpt-4o", "GPT-4o (Azure)", "Latest flagship model via Azure OpenAI Service", 128000, {"input": 0.0025, "output": 0.01}),
            LLMModel("gpt-4o-mini", "GPT-4o Mini (Azure)", "Lightweight, cheaper GPT-4o via Azure", 128000, {"input": 0.00015, "output": 0.0006}),
            LLMModel("gpt-4-turbo", "GPT-4 Turbo (Azure)", "Turbo-optimized GPT-4 via Azure", 128000, {"input": 0.01, "output": 0.03}),
            LLMModel("gpt-4", "GPT-4 (Azure)", "Original GPT-4 model via Azure", 8192, {"input": 0.03, "output": 0.06}),
            LLMModel("gpt-35-turbo", "GPT-3.5 Turbo (Azure)", "Fast and efficient via Azure", 16385, {"input": 0.001, "output": 0.002}),
        ]
        azure_openai = Provider(
            id="azure_openai",
            name="azure_openai",
            display_name="Azure OpenAI",
            description="OpenAI models via Microsoft Azure with enterprise features and compliance",
            port=8894,
            requires_api_key=True,
            models=azure_openai_models,
            selected_model="gpt-4o-mini",
            azure_endpoint="https://ai-admin8236ai262666201853.openai.azure.com/",
            azure_api_version="2024-10-21",
            azure_deployment_name="gpt-4o-mini"
        )
        
        # Register providers
        for provider in [openai, anthropic, gemini, azure_openai, ollama]:
            self.register_provider(provider)
    
    def register_provider(self, provider: Provider):
        """Register a new provider"""
        self.providers[provider.id] = provider
        self.port_mapping[provider.port] = provider.id
        self.running_services[provider.id] = False
        logger.info(f"Registered provider: {provider.display_name} on port {provider.port}")
    
    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Get provider by ID"""
        return self.providers.get(provider_id)
    
    def get_provider_by_port(self, port: int) -> Optional[Provider]:
        """Get provider by port number"""
        provider_id = self.port_mapping.get(port)
        if provider_id:
            return self.providers.get(provider_id)
        return None
    
    def list_providers(self) -> List[Provider]:
        """List all providers"""
        return list(self.providers.values())
    
    def list_enabled_providers(self) -> List[Provider]:
        """List only enabled providers"""
        return [p for p in self.providers.values() if p.enabled]
    
    async def test_provider_connection(self, provider_id: str) -> Tuple[bool, Optional[str]]:
        """Test connection to a provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False, "Provider not found"
        
        provider.status = ProviderStatus.TESTING
        provider.last_tested = datetime.now()
        
        try:
            if provider.id == "openai":
                success, error = await self._test_openai_connection(provider)
            elif provider.id == "anthropic":
                success, error = await self._test_anthropic_connection(provider)
            elif provider.id == "gemini":
                success, error = await self._test_gemini_connection(provider)
            elif provider.id == "ollama":
                success, error = await self._test_ollama_connection(provider)
            elif provider.id == "azure_openai":
                success, error = await self._test_azure_openai_connection(provider)
            else:
                return False, "Unknown provider type"
            
            if success:
                provider.status = ProviderStatus.CONNECTED
                provider.error_message = None
                logger.info(f"Successfully connected to {provider.display_name}")
            else:
                provider.status = ProviderStatus.ERROR
                provider.error_message = error
                logger.error(f"Failed to connect to {provider.display_name}: {error}")
            
            return success, error
            
        except Exception as e:
            provider.status = ProviderStatus.ERROR
            provider.error_message = str(e)
            logger.error(f"Exception testing {provider.display_name}: {e}")
            return False, str(e)
    
    async def _test_openai_connection(self, provider: Provider) -> Tuple[bool, Optional[str]]:
        """Test OpenAI API connection"""
        if not provider.api_key:
            return False, "API key required"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {provider.api_key}"}
                )
                if response.status_code == 200:
                    return True, None
                else:
                    return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    async def _test_anthropic_connection(self, provider: Provider) -> Tuple[bool, Optional[str]]:
        """Test Anthropic API connection"""
        if not provider.api_key:
            return False, "API key required"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": provider.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "test"}]
                    }
                )
                if response.status_code in [200, 400]:  # 400 might be expected for test message
                    return True, None
                else:
                    return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    async def _test_gemini_connection(self, provider: Provider) -> Tuple[bool, Optional[str]]:
        """Test Google Gemini API connection"""
        if not provider.api_key:
            return False, "API key required"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={provider.api_key}"
                )
                if response.status_code == 200:
                    return True, None
                else:
                    return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    async def _test_ollama_connection(self, provider: Provider) -> Tuple[bool, Optional[str]]:
        """Test Ollama connection"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    return True, None
                else:
                    return False, f"HTTP {response.status_code}: Ollama not running on port 11434"
        except Exception as e:
            return False, f"Ollama not accessible: {str(e)}"
    
    async def _test_azure_openai_connection(self, provider: Provider) -> Tuple[bool, Optional[str]]:
        """Test Azure OpenAI API connection"""
        if not provider.api_key:
            return False, "API key required"
        
        if not provider.azure_endpoint:
            return False, "Azure endpoint required"
            
        try:
            # Clean endpoint URL - remove trailing slash if present
            endpoint = provider.azure_endpoint.rstrip('/')
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test deployments endpoint
                url = f"{endpoint}/openai/deployments?api-version={provider.azure_api_version}"
                response = await client.get(
                    url,
                    headers={"api-key": provider.api_key}
                )
                if response.status_code == 200:
                    return True, None
                else:
                    return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def update_provider_config(self, provider_id: str, **kwargs) -> bool:
        """Update provider configuration"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False
        
        for key, value in kwargs.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
        
        logger.info(f"Updated provider {provider.display_name} configuration")
        return True
    
    def check_port_availability(self, port: int) -> Dict[str, Any]:
        """Check if a port is available and what might be using it"""
        result = {
            "available": False,
            "port": port,
            "in_use_by": None,
            "process_info": None,
            "can_override": False
        }
        
        try:
            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result_code = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result_code == 0:
                # Port is in use
                result["available"] = False
                
                # Check if it's used by one of our providers
                for provider_id, provider in self.providers.items():
                    if provider.port == port and provider.enabled:
                        result["in_use_by"] = provider.display_name
                        result["can_override"] = True
                        break
                
                # If not our provider, try to get system info
                if not result["in_use_by"]:
                    try:
                        import psutil
                        for proc in psutil.process_iter(['pid', 'name', 'connections']):
                            try:
                                for conn in proc.info['connections']:
                                    if conn.laddr.port == port:
                                        result["process_info"] = {
                                            "pid": proc.info['pid'],
                                            "name": proc.info['name']
                                        }
                                        result["in_use_by"] = f"{proc.info['name']} (PID: {proc.info['pid']})"
                                        break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except ImportError:
                        # psutil not available
                        result["in_use_by"] = "Unknown process"
            else:
                result["available"] = True
                
        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
            result["available"] = False
            result["in_use_by"] = f"Error checking port: {str(e)}"
        
        return result
    
    def find_next_available_port(self, start_port: int = 8900, max_attempts: int = 100) -> Optional[int]:
        """Find the next available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            port_status = self.check_port_availability(port)
            if port_status["available"]:
                return port
        return None

    async def enable_provider(self, provider_id: str, enabled: bool = True, force_port: bool = False) -> Dict[str, Any]:
        """Enable or disable a provider with port conflict detection - optimized for speed"""
        provider = self.get_provider(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not found"}
        
        try:
            if not enabled:
                # Stop the proxy server if running
                await self._stop_provider_server(provider_id)
                provider.enabled = False
                provider.status = ProviderStatus.DISCONNECTED
                logger.info(f"Provider {provider.display_name} disabled")
                return {"success": True, "message": f"Provider {provider.display_name} disabled"}
            
            # For enabling, do a quick port check without deep system inspection
            port_status = self.check_port_availability(provider.port)
            
            if not port_status["available"] and not force_port:
                return {
                    "success": False,
                    "error": "Port conflict detected",
                    "port_status": port_status,
                    "suggested_actions": [
                        "Force enable (will terminate conflicting service)",
                        "Use next available port",
                        "Cancel operation"
                    ]
                }
            
            # If port is not available but force is requested
            if not port_status["available"] and force_port:
                if port_status["can_override"]:
                    # Disable the conflicting provider quickly
                    for other_provider_id, other_provider in self.providers.items():
                        if other_provider.port == provider.port and other_provider.enabled:
                            await self._stop_provider_server(other_provider_id)
                            other_provider.enabled = False
                            other_provider.status = ProviderStatus.DISCONNECTED
                            logger.info(f"Disabled conflicting provider {other_provider.display_name}")
                            break
                else:
                    logger.warning(f"Forcing enable of {provider.display_name} on port {provider.port} (may conflict with {port_status['in_use_by']})")
            
            # Enable provider immediately for responsive UI
            provider.enabled = enabled
            
            # Start the proxy server
            await self._start_provider_server(provider_id)
            logger.info(f"Provider {provider.display_name} enabled and proxy server started on port {provider.port}")
            return {"success": True, "message": f"Provider {provider.display_name} enabled and proxy server started on port {provider.port}"}
            
        except Exception as e:
            # Graceful error handling
            provider.enabled = False
            provider.status = ProviderStatus.ERROR
            provider.error_message = f"Failed to start proxy server: {str(e)}"
            logger.error(f"Failed to start proxy server for {provider.display_name}: {e}")
            return {"success": False, "error": f"Failed to start proxy server: {str(e)}"}
    
    async def enable_provider_with_port_selection(self, provider_id: str, use_next_available: bool = False) -> Dict[str, Any]:
        """Enable provider with automatic port selection if current port is unavailable"""
        provider = self.get_provider(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not found"}
        
        port_status = self.check_port_availability(provider.port)
        
        if not port_status["available"] and use_next_available:
            new_port = self.find_next_available_port(provider.port + 1)
            if new_port:
                old_port = provider.port
                provider.port = new_port
                self.port_mapping[new_port] = provider_id
                if old_port in self.port_mapping:
                    del self.port_mapping[old_port]
                
                provider.enabled = True
                
                # Start the proxy server on the new port
                try:
                    await self._start_provider_server(provider_id)
                    logger.info(f"Provider {provider.display_name} enabled on new port {new_port} (was {old_port})")
                    return {
                        "success": True, 
                        "message": f"Provider {provider.display_name} enabled on port {new_port}",
                        "port_changed": True,
                        "old_port": old_port,
                        "new_port": new_port
                    }
                except Exception as e:
                    provider.enabled = False
                    provider.status = ProviderStatus.ERROR
                    provider.error_message = f"Failed to start proxy server: {str(e)}"
                    return {"success": False, "error": f"Failed to start proxy server: {str(e)}"}
            else:
                return {"success": False, "error": "No available ports found"}
        
        return await self.enable_provider(provider_id, True)
    
    def set_api_key(self, provider_id: str, api_key: str) -> bool:
        """Set API key for a provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False
        
        provider.api_key = api_key
        # Reset status when API key changes
        provider.status = ProviderStatus.DISCONNECTED
        provider.error_message = None
        
        logger.info(f"Updated API key for {provider.display_name} (key: ***REDACTED***)")
        return True
    
    def select_model(self, provider_id: str, model_id: str) -> bool:
        """Select model for a provider"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False
        
        # Verify model exists
        if not any(model.id == model_id for model in provider.models):
            return False
        
        provider.selected_model = model_id
        logger.info(f"Selected model {model_id} for {provider.display_name}")
        return True
    
    def update_azure_config(self, provider_id: str, endpoint: str = None, api_version: str = None, deployment_name: str = None) -> bool:
        """Update Azure OpenAI specific configuration"""
        provider = self.get_provider(provider_id)
        if not provider or provider.id != "azure_openai":
            return False
        
        if endpoint is not None:
            provider.azure_endpoint = endpoint
        if api_version is not None:
            provider.azure_api_version = api_version
        if deployment_name is not None:
            provider.azure_deployment_name = deployment_name
            
        # Reset status when config changes
        provider.status = ProviderStatus.DISCONNECTED
        provider.error_message = None
        
        logger.info(f"Updated Azure configuration for {provider.display_name} (endpoint: {provider.azure_endpoint[:50]}...)")
        return True
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get provider statistics"""
        total_providers = len(self.providers)
        enabled_providers = len(self.list_enabled_providers())
        connected_providers = len([p for p in self.providers.values() if p.status == ProviderStatus.CONNECTED])
        running_servers = len([p for p in self.providers.values() if self.running_services.get(p.id, False)])
        
        return {
            "total_providers": total_providers,
            "enabled_providers": enabled_providers,
            "connected_providers": connected_providers,
            "running_servers": running_servers,
            "port_mappings": dict(self.port_mapping),
            "provider_summary": [
                {
                    "id": p.id,
                    "name": p.display_name,
                    "port": p.port,
                    "enabled": p.enabled,
                    "status": p.status.value,
                    "model": p.selected_model,
                    "server_running": self.running_services.get(p.id, False)
                }
                for p in self.providers.values()
            ]
        }
    
    async def _start_provider_server(self, provider_id: str):
        """Start proxy server for a provider - optimized for quick startup"""
        from app.services.traffic_router import traffic_router
        
        # Get or create provider-specific lock
        if provider_id not in self._provider_locks:
            async with self._global_lock:
                if provider_id not in self._provider_locks:
                    self._provider_locks[provider_id] = asyncio.Lock()
        
        # Use provider-specific lock to prevent race conditions
        async with self._provider_locks[provider_id]:
            provider = self.get_provider(provider_id)
            if not provider:
                raise ValueError(f"Provider {provider_id} not found")
            
            # Check if server is already running
            if self.running_services.get(provider_id, False):
                logger.info(f"Proxy server for {provider.display_name} already running on port {provider.port}")
                return
            
            try:
                # Create server task directly in the current event loop
                app = await traffic_router.create_provider_app(provider)
                
                # Use uvicorn programmatically with the current event loop
                import uvicorn
                config = uvicorn.Config(
                    app,
                    host="0.0.0.0",
                    port=provider.port,
                    log_level="error",  # Reduce logging for faster startup
                    access_log=False    # Disable access log for better performance
                )
                
                server = uvicorn.Server(config)
                
                # Create server task and store it
                server_task = asyncio.create_task(server.serve())
                self.server_tasks[provider_id] = server_task
                
                # Mark as running immediately
                self.running_services[provider_id] = True
                provider.status = ProviderStatus.CONNECTED
                provider.error_message = None
                
                logger.info(f"✅ {provider.display_name} proxy server started on port {provider.port}")
                
                # Quick health check to ensure server is responding
                await asyncio.sleep(0.1)  # Minimal delay
                
                # Verify server is actually running by checking if task is still running
                if server_task.done():
                    # Server task completed immediately, likely due to error
                    try:
                        await server_task  # This will raise any exception
                    except Exception as e:
                        raise e
                
            except Exception as e:
                logger.error(f"❌ Error starting server for {provider.display_name}: {e}")
                self.running_services[provider_id] = False
                provider.status = ProviderStatus.ERROR
                provider.error_message = f"Server start failed: {str(e)}"
                
                # Clean up server task if it was created
                if provider_id in self.server_tasks:
                    task = self.server_tasks[provider_id]
                    if not task.done():
                        task.cancel()
                    del self.server_tasks[provider_id]
                
                raise e
    
    async def _stop_provider_server(self, provider_id: str):
        """Stop proxy server for a provider - optimized for quick shutdown"""
        # Get or create provider-specific lock
        if provider_id not in self._provider_locks:
            async with self._global_lock:
                if provider_id not in self._provider_locks:
                    self._provider_locks[provider_id] = asyncio.Lock()
        
        # Use provider-specific lock to prevent race conditions
        async with self._provider_locks[provider_id]:
            try:
                provider = self.get_provider(provider_id)
                
                if not self.running_services.get(provider_id, False):
                    if provider:
                        logger.info(f"Proxy server for {provider.display_name} already stopped")
                    return
                
                # Mark as stopped immediately
                self.running_services[provider_id] = False
                
                # If we have a server task, cancel it gracefully
                if provider_id in self.server_tasks:
                    task = self.server_tasks[provider_id]
                    if not task.done():
                        task.cancel()
                        try:
                            await asyncio.wait_for(task, timeout=1.0)  # Wait up to 1 second
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            pass  # Expected when cancelling
                    del self.server_tasks[provider_id]
                
                if provider:
                    provider.status = ProviderStatus.DISCONNECTED
                    provider.error_message = None
                    logger.info(f"🔴 {provider.display_name} proxy server stopped on port {provider.port}")
                    
            except Exception as e:
                logger.error(f"Error stopping server for provider {provider_id}: {e}")
                # Ensure we mark as stopped even if there was an error
                self.running_services[provider_id] = False
                if provider_id in self.server_tasks:
                    del self.server_tasks[provider_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all providers to dictionary format"""
        return {
            provider_id: {
                **asdict(provider),
                "status": provider.status.value,
                "last_tested": provider.last_tested.isoformat() if provider.last_tested else None,
                "models": [asdict(model) for model in provider.models],
                "server_running": self.running_services.get(provider_id, False)
            }
            for provider_id, provider in self.providers.items()
        }

# Global provider service instance
provider_service = ProviderService()

# Cleanup function for graceful shutdown
async def cleanup_provider_service():
    """Cleanup function to stop all running servers"""
    for provider_id in list(provider_service.running_services.keys()):
        if provider_service.running_services[provider_id]:
            await provider_service._stop_provider_server(provider_id)
    
    # Shutdown the executor
    provider_service.executor.shutdown(wait=True)