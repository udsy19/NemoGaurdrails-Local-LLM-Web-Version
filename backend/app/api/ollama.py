"""
Ollama API endpoints for model management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import json
import asyncio
import httpx
from datetime import datetime

from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ollama", tags=["ollama"])

class ModelPullRequest(BaseModel):
    model: str
    stream: bool = True

class ModelDeleteRequest(BaseModel):
    model: str

class ModelInfo(BaseModel):
    name: str
    modified_at: str
    size: int
    digest: str
    details: Optional[Dict[str, Any]] = None

ollama_service = OllamaService()

@router.get("/models", response_model=Dict[str, Any])
async def list_models():
    """List locally installed Ollama models"""
    try:
        models = await ollama_service.get_local_models()
        return {
            "models": models,
            "count": len(models),
            "success": True
        }
    except Exception as e:
        logger.error(f"Error listing Ollama models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/available", response_model=Dict[str, Any])
async def list_available_models():
    """List available models that can be downloaded"""
    try:
        # This would normally fetch from Ollama registry
        # For now, return popular models
        popular_models = [
            {
                "name": "llama3.2",
                "description": "Meta's latest Llama model",
                "tags": ["3b", "1b", "11b", "90b"],
                "size": "2GB",
                "popular": True
            },
            {
                "name": "llama3.1",
                "description": "Previous generation Llama model",
                "tags": ["8b", "70b", "405b"],
                "size": "4.7GB",
                "popular": True
            },
            {
                "name": "qwen2.5",
                "description": "Alibaba's multilingual model",
                "tags": ["0.5b", "1.5b", "3b", "7b", "14b", "32b", "72b"],
                "size": "900MB",
                "popular": True
            },
            {
                "name": "mistral",
                "description": "High-quality 7B parameter model",
                "tags": ["7b", "8x7b", "8x22b"],
                "size": "4.1GB",
                "popular": True
            },
            {
                "name": "codellama",
                "description": "Specialized for code generation",
                "tags": ["7b", "13b", "34b"],
                "size": "3.8GB",
                "popular": False
            },
            {
                "name": "phi3",
                "description": "Microsoft's efficient small model",
                "tags": ["mini", "small", "medium"],
                "size": "2.3GB",
                "popular": True
            },
            {
                "name": "gemma2",
                "description": "Google's latest Gemma model",
                "tags": ["2b", "9b", "27b"],
                "size": "1.6GB",
                "popular": True
            },
            {
                "name": "deepseek-coder",
                "description": "Specialized for coding tasks",
                "tags": ["1.3b", "6.7b", "33b"],
                "size": "1.3GB",
                "popular": False
            }
        ]
        
        return {
            "models": popular_models,
            "count": len(popular_models),
            "success": True
        }
    except Exception as e:
        logger.error(f"Error listing available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pull/{model_name}")
async def pull_model(model_name: str, background_tasks: BackgroundTasks):
    """Pull/download a model from Ollama registry with streaming progress"""
    try:
        # Check if Ollama is running
        if not await ollama_service.is_ollama_running():
            raise HTTPException(
                status_code=503, 
                detail="Ollama service is not running. Please start Ollama first."
            )
        
        async def generate_progress():
            """Generator function for streaming progress updates"""
            try:
                async with httpx.AsyncClient(timeout=600.0) as client:
                    async with client.stream(
                        "POST",
                        "http://localhost:11434/api/pull",
                        json={"name": model_name}
                    ) as response:
                        
                        if response.status_code != 200:
                            error_text = await response.aread()
                            yield f"data: {json.dumps({'error': f'HTTP {response.status_code}: {error_text.decode()}'})}\n\n"
                            return
                        
                        async for chunk in response.aiter_bytes():
                            if chunk:
                                # Parse the chunk for progress information
                                try:
                                    lines = chunk.decode().strip().split('\n')
                                    for line in lines:
                                        if line.strip():
                                            data = json.loads(line)
                                            yield f"data: {json.dumps(data)}\n\n"
                                except json.JSONDecodeError:
                                    # If not JSON, send as plain text
                                    yield f"data: {json.dumps({'status': 'downloading', 'message': chunk.decode()})}\n\n"
                                except Exception as e:
                                    logger.error(f"Error processing chunk: {e}")
                                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                        
                        # Send completion signal
                        yield f"data: {json.dumps({'status': 'success', 'message': f'Model {model_name} downloaded successfully'})}\n\n"
                        
            except Exception as e:
                logger.error(f"Error pulling model {model_name}: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_progress(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting model pull for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a locally installed model"""
    try:
        # Check if Ollama is running
        if not await ollama_service.is_ollama_running():
            raise HTTPException(
                status_code=503, 
                detail="Ollama service is not running. Please start Ollama first."
            )
        
        await ollama_service.delete_model(model_name)
        
        return {
            "message": f"Model {model_name} deleted successfully",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error deleting model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get detailed information about a model"""
    try:
        # Check if Ollama is running
        if not await ollama_service.is_ollama_running():
            raise HTTPException(
                status_code=503, 
                detail="Ollama service is not running. Please start Ollama first."
            )
        
        info = await ollama_service.get_model_info(model_name)
        
        return {
            "model_info": info,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting info for model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_ollama_status():
    """Check if Ollama service is running"""
    try:
        is_running = await ollama_service.is_ollama_running()
        
        status = {
            "running": is_running,
            "timestamp": datetime.now().isoformat()
        }
        
        if is_running:
            try:
                models = await ollama_service.get_local_models()
                status["models_count"] = len(models)
            except:
                status["models_count"] = 0
        
        return {
            "status": status,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_name}/test")
async def test_model(model_name: str):
    """Test a model with a simple generation"""
    try:
        # Check if Ollama is running
        if not await ollama_service.is_ollama_running():
            raise HTTPException(
                status_code=503, 
                detail="Ollama service is not running. Please start Ollama first."
            )
        
        # Test the model with a simple prompt
        test_prompt = "Hello! Please respond with 'Model test successful' to confirm you're working."
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": test_prompt,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Model test failed: {response.text}"
                )
            
            result = response.json()
            
            return {
                "test_result": {
                    "prompt": test_prompt,
                    "response": result.get("response", "No response"),
                    "success": True,
                    "model": model_name
                },
                "success": True
            }
            
    except Exception as e:
        logger.error(f"Error testing model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))