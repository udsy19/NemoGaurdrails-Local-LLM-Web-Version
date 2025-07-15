"""
Ollama Service for managing local models
"""
import asyncio
import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def is_ollama_running(self) -> bool:
        """Check if Ollama service is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not running: {e}")
            return False
    
    async def get_local_models(self) -> List[Dict[str, Any]]:
        """Get list of locally installed models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
                data = response.json()
                return data.get("models", [])
                
        except Exception as e:
            logger.error(f"Error getting local models: {e}")
            raise e
    
    async def delete_model(self, model_name: str) -> None:
        """Delete a locally installed model"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/api/delete",
                    json={"name": model_name}
                )
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {e}")
            raise e
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name}
                )
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            raise e
    
    async def pull_model(self, model_name: str) -> None:
        """Pull/download a model"""
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                )
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            raise e
    
    async def generate_text(self, model_name: str, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Generate text using a model"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": stream
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error generating text with {model_name}: {e}")
            raise e
    
    def format_model_size(self, size_bytes: int) -> str:
        """Format model size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {units[i]}"
    
    def format_model_info(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format model information for display"""
        return {
            "name": model_data.get("name", "Unknown"),
            "size": self.format_model_size(model_data.get("size", 0)),
            "size_bytes": model_data.get("size", 0),
            "modified_at": model_data.get("modified_at", "Unknown"),
            "digest": model_data.get("digest", "Unknown"),
            "details": model_data.get("details", {}),
            "family": model_data.get("details", {}).get("family", "Unknown"),
            "parameter_size": model_data.get("details", {}).get("parameter_size", "Unknown"),
            "quantization": model_data.get("details", {}).get("quantization_level", "Unknown")
        }