"""
Provider Management API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import time

from app.services.provider_service import provider_service, ProviderStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/providers", tags=["providers"])

class ProviderConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    api_key: Optional[str] = None
    selected_model: Optional[str] = None

class TestConnectionRequest(BaseModel):
    provider_id: str

class ProviderResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    port: int
    requires_api_key: bool
    models: List[Dict[str, Any]]
    enabled: bool
    api_key: str
    selected_model: str
    status: str
    last_tested: Optional[str] = None
    error_message: Optional[str] = None

@router.get("/", response_model=Dict[str, Any])
async def list_providers():
    """Get all providers with their configurations"""
    try:
        providers_data = provider_service.to_dict()
        stats = provider_service.get_provider_stats()
        
        return {
            "providers": providers_data,
            "stats": stats,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider_id}", response_model=Dict[str, Any])
async def get_provider(provider_id: str):
    """Get specific provider details"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        provider_dict = provider_service.to_dict()[provider_id]
        return {
            "provider": provider_dict,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{provider_id}/config")
async def update_provider_config(provider_id: str, config: ProviderConfigUpdate):
    """Update provider configuration"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Update fields that were provided
        updates = {}
        if config.enabled is not None:
            updates['enabled'] = config.enabled
        if config.api_key is not None:
            updates['api_key'] = config.api_key
        if config.selected_model is not None:
            updates['selected_model'] = config.selected_model
        
        # Apply updates
        success = provider_service.update_provider_config(provider_id, **updates)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update provider configuration")
        
        # Return updated provider
        updated_provider = provider_service.to_dict()[provider_id]
        return {
            "provider": updated_provider,
            "message": f"Updated {provider.display_name} configuration",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_id}/enable")
async def enable_provider(provider_id: str, force_port: bool = False):
    """Enable a provider with port conflict detection"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        result = await provider_service.enable_provider(provider_id, True, force_port)
        if not result["success"]:
            if result.get("error") == "Port conflict detected":
                # Return port conflict information for frontend to handle
                return {
                    "success": False,
                    "conflict": True,
                    "port_status": result["port_status"],
                    "suggested_actions": result["suggested_actions"],
                    "message": f"Port {provider.port} is already in use by {result['port_status']['in_use_by']}"
                }
            else:
                raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": result["message"],
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_id}/disable")
async def disable_provider(provider_id: str):
    """Disable a provider"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        result = await provider_service.enable_provider(provider_id, False)
        success = result["success"]
        if not success:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to disable provider"))
        
        return {
            "message": f"Disabled {provider.display_name}",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_id}/test-connection")
async def test_provider_connection(provider_id: str, background_tasks: BackgroundTasks):
    """Test connection to a provider with LLM generation test"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Start connection test in background
        success, error_message = await provider_service.test_provider_connection(provider_id)
        
        # Skip LLM generation test for basic connection test - just return connection result
        llm_test_result = {
            "skipped": True,
            "message": "LLM test skipped for fast connection test. Use /test-llm endpoint for full test."
        }
        
        # Get updated provider status
        updated_provider = provider_service.to_dict()[provider_id]
        
        return {
            "provider": updated_provider,
            "connection_success": success,
            "error_message": error_message,
            "message": f"Connection test completed for {provider.display_name}",
            "llm_test": llm_test_result,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing connection for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_id}/api-key")
async def set_provider_api_key(provider_id: str, api_key: str):
    """Set API key for a provider"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        if not provider.requires_api_key:
            raise HTTPException(status_code=400, detail="Provider does not require API key")
        
        success = provider_service.set_api_key(provider_id, api_key)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to set API key")
        
        return {
            "message": f"Updated API key for {provider.display_name}",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting API key for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_id}/select-model")
async def select_provider_model(provider_id: str, model_id: str):
    """Select model for a provider"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        success = provider_service.select_model(provider_id, model_id)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid model ID or failed to select model")
        
        return {
            "message": f"Selected model {model_id} for {provider.display_name}",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting model for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_id}/test-llm")
async def test_provider_llm_generation(provider_id: str):
    """Test full LLM generation for a provider"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # First test basic connection
        success, error_message = await provider_service.test_provider_connection(provider_id)
        if not success:
            return {
                "provider_id": provider_id,
                "connection_success": False,
                "error_message": error_message,
                "llm_test": {"success": False, "error": "Connection failed"},
                "success": False
            }
        
        # Test LLM generation
        try:
            test_prompt = "Hello! Please respond with 'Connection test successful' to confirm the LLM is working."
            
            # Import chat service to test generation
            from app.main import chat_service
            if chat_service:
                start_time = time.time()
                chat_response = await chat_service.process_message(
                    message=test_prompt,
                    detector_config={},  # Minimal config for test
                    context={"test_mode": True, "provider": provider_id}
                )
                response_time = round((time.time() - start_time) * 1000, 2)
                
                llm_test_result = {
                    "prompt": test_prompt,
                    "response": chat_response.get("response", "No response"),
                    "blocked": chat_response.get("blocked", False),
                    "response_time_ms": response_time,
                    "success": not chat_response.get("blocked", False) and chat_response.get("response")
                }
            else:
                llm_test_result = {
                    "error": "Chat service not available",
                    "success": False
                }
        except Exception as e:
            llm_test_result = {
                "error": f"LLM generation test failed: {str(e)}",
                "success": False
            }
        
        return {
            "provider_id": provider_id,
            "connection_success": success,
            "error_message": error_message,
            "llm_test": llm_test_result,
            "success": success and llm_test_result.get("success", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing LLM for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/port/{port}")
async def get_provider_by_port(port: int):
    """Get provider configuration by port number"""
    try:
        provider = provider_service.get_provider_by_port(port)
        if not provider:
            raise HTTPException(status_code=404, detail=f"No provider found on port {port}")
        
        provider_dict = provider_service.to_dict()[provider.id]
        return {
            "provider": provider_dict,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider by port {port}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_provider_stats():
    """Get provider statistics summary"""
    try:
        stats = provider_service.get_provider_stats()
        return {
            "stats": stats,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting provider stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{provider_id}/enable-with-port-selection")
async def enable_provider_with_port_selection(provider_id: str, use_next_available: bool = False):
    """Enable provider with automatic port selection if needed"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        result = await provider_service.enable_provider_with_port_selection(provider_id, use_next_available)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling provider with port selection {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{provider_id}/port-status")
async def get_port_status(provider_id: str):
    """Get port availability status for a provider"""
    try:
        provider = provider_service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        port_status = provider_service.check_port_availability(provider.port)
        
        return {
            "provider_id": provider_id,
            "port_status": port_status,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting port status for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-all-connections")
async def test_all_connections(background_tasks: BackgroundTasks):
    """Test connections to all enabled providers"""
    try:
        enabled_providers = provider_service.list_enabled_providers()
        if not enabled_providers:
            return {
                "message": "No enabled providers to test",
                "results": [],
                "success": True,
                "stats": provider_service.get_provider_stats()
            }
        
        # Test all connections
        results = []
        success_count = 0
        
        for provider in enabled_providers:
            success, error_message = await provider_service.test_provider_connection(provider.id)
            if success:
                success_count += 1
                
            results.append({
                "provider_id": provider.id,
                "provider_name": provider.display_name,
                "success": success,
                "error_message": error_message,
                "port": provider.port,
                "status": provider.status.value
            })
        
        # Get updated provider data and stats
        providers_data = provider_service.to_dict()
        updated_stats = provider_service.get_provider_stats()
        
        return {
            "message": f"Tested connections for {len(enabled_providers)} providers - {success_count}/{len(enabled_providers)} successful",
            "results": results,
            "providers": providers_data,
            "stats": updated_stats,
            "test_summary": {
                "total_tested": len(enabled_providers),
                "successful": success_count,
                "failed": len(enabled_providers) - success_count,
                "success_rate": round((success_count / len(enabled_providers)) * 100, 1) if enabled_providers else 0
            },
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error testing all connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))