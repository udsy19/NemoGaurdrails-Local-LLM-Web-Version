"""
Ollama Models API endpoints
"""
import re
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from app.utils.logger import app_logger
import asyncio
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/models", tags=["models"])

class ModelInfo(BaseModel):
    name: str
    library_path: str
    description: str
    capabilities: List[str]
    sizes: List[str]
    pull_count: str
    tag_count: int
    updated: str

class ModelsResponse(BaseModel):
    models: List[ModelInfo]
    total_count: int
    fetched_at: str

class OllamaModelsParser:
    """Parser for Ollama search page HTML"""
    
    def __init__(self):
        self.base_url = "https://ollama.com"
        self._cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=10)
    
    async def fetch_models_page(self, page: int = 1, sort: str = "popular") -> str:
        """Fetch the Ollama models search page with caching"""
        cache_key = f"page_{page}_{sort}"
        
        # Check cache first
        if cache_key in self._cache and datetime.now() < self._cache_expiry.get(cache_key, datetime.min):
            app_logger.info(f"Using cached models data for {cache_key}")
            return self._cache[cache_key]
        
        try:
            params = {
                "o": sort,  # popular, newest
            }
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                    }
                )
                response.raise_for_status()
                
                # Cache the result
                self._cache[cache_key] = response.text
                self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
                
                return response.text
                
        except httpx.RequestError as e:
            app_logger.error(f"Failed to fetch Ollama models page: {e}")
            raise HTTPException(status_code=503, detail="Failed to fetch models from Ollama")
        except httpx.HTTPStatusError as e:
            app_logger.error(f"HTTP error fetching Ollama models: {e}")
            raise HTTPException(status_code=503, detail="Ollama service unavailable")
    
    def parse_models_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse the HTML content and extract model information"""
        try:
            # Use lxml parser for better performance if available, fallback to html.parser
            try:
                soup = BeautifulSoup(html_content, 'lxml')
            except:
                soup = BeautifulSoup(html_content, 'html.parser')
            
            models = []
            
            # Find all model list items
            model_items = soup.find_all('li', {'x-test-model': True})
            app_logger.info(f"Found {len(model_items)} model items to parse")
            
            # Process models in batches for better performance
            for item in model_items:
                try:
                    model_data = self._parse_model_item(item)
                    if model_data:
                        models.append(model_data)
                except Exception as e:
                    app_logger.debug(f"Failed to parse model item: {e}")
                    continue
            
            app_logger.info(f"Successfully parsed {len(models)} models from Ollama")
            return models
            
        except Exception as e:
            app_logger.error(f"Failed to parse Ollama HTML: {e}")
            return []
    
    def _parse_model_item(self, item) -> Optional[Dict[str, Any]]:
        """Parse a single model item from the HTML"""
        try:
            # Get model name and library path from the link
            link = item.find('a', {'href': True})
            if not link:
                return None
            
            library_path = link['href']
            
            # Extract model name
            title_elem = item.find('span', {'x-test-search-response-title': True})
            if not title_elem:
                return None
            name = title_elem.get_text(strip=True)
            
            # Extract description
            description_elem = item.find('p', class_='max-w-lg break-words text-neutral-800 text-md')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Extract capabilities
            capabilities = []
            capability_spans = item.find_all('span', {'x-test-capability': True})
            for cap_span in capability_spans:
                cap_text = cap_span.get_text(strip=True)
                if cap_text:
                    capabilities.append(cap_text)
            
            # Extract model sizes
            sizes = []
            size_spans = item.find_all('span', {'x-test-size': True})
            for size_span in size_spans:
                size_text = size_span.get_text(strip=True)
                if size_text:
                    sizes.append(size_text)
            
            # Extract pull count
            pull_count = "0"
            pull_elem = item.find('span', {'x-test-pull-count': True})
            if pull_elem:
                pull_count = pull_elem.get_text(strip=True)
            
            # Extract tag count
            tag_count = 0
            tag_elem = item.find('span', {'x-test-tag-count': True})
            if tag_elem:
                try:
                    tag_count = int(tag_elem.get_text(strip=True))
                except (ValueError, TypeError):
                    tag_count = 0
            
            # Extract updated time
            updated = "Unknown"
            updated_elem = item.find('span', {'x-test-updated': True})
            if updated_elem:
                updated = updated_elem.get_text(strip=True)
            
            return {
                'name': name,
                'library_path': library_path,
                'description': description,
                'capabilities': capabilities,
                'sizes': sizes,
                'pull_count': pull_count,
                'tag_count': tag_count,
                'updated': updated,
            }
            
        except Exception as e:
            app_logger.error(f"Error parsing model item: {e}")
            return None

# Global parser instance
models_parser = OllamaModelsParser()

@router.get("/search", response_model=ModelsResponse)
async def search_models(
    response: Response,
    sort: str = "popular",
    page: int = 1,
) -> ModelsResponse:
    """
    Fetch and parse models from Ollama search page
    
    Args:
        sort: Sort order - 'popular' or 'newest'
        page: Page number (currently only page 1 is supported)
        
    Returns:
        ModelsResponse with parsed model information
    """
    try:
        app_logger.info(f"Fetching Ollama models (sort={sort}, page={page})")
        
        # Fetch the HTML content
        html_content = await models_parser.fetch_models_page(page=page, sort=sort)
        
        # Parse the HTML to extract model info
        raw_models = models_parser.parse_models_html(html_content)
        
        # Convert to Pydantic models
        models = []
        for raw_model in raw_models:
            try:
                model = ModelInfo(**raw_model)
                models.append(model)
            except Exception as e:
                app_logger.warning(f"Failed to create ModelInfo for {raw_model.get('name', 'unknown')}: {e}")
                continue
        
        from datetime import datetime
        models_response = ModelsResponse(
            models=models,
            total_count=len(models),
            fetched_at=datetime.now().isoformat()
        )
        
        # Add caching headers
        response.headers["Cache-Control"] = "public, max-age=600"  # 10 minutes
        response.headers["ETag"] = f'"{len(models)}-{sort}-{page}"'
        
        app_logger.info(f"Successfully fetched {len(models)} models from Ollama")
        return models_response
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Unexpected error fetching Ollama models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching models")

@router.get("/popular")
async def get_popular_models(limit: int = 10) -> ModelsResponse:
    """Get popular models"""
    response = await search_models(sort="popular")
    if limit < len(response.models):
        response.models = response.models[:limit]
        response.total_count = limit
    return response

@router.get("/newest")
async def get_newest_models(limit: int = 10) -> ModelsResponse:
    """Get newest models"""
    response = await search_models(sort="newest")
    if limit < len(response.models):
        response.models = response.models[:limit]
        response.total_count = limit
    return response

@router.get("/capabilities")
async def get_available_capabilities() -> Dict[str, Any]:
    """Get all available model capabilities"""
    try:
        response = await search_models()
        capabilities = set()
        
        for model in response.models:
            capabilities.update(model.capabilities)
        
        return {
            "capabilities": sorted(list(capabilities)),
            "total_capabilities": len(capabilities),
        }
        
    except Exception as e:
        app_logger.error(f"Error fetching capabilities: {e}")
        return {
            "capabilities": ["tools", "vision", "thinking", "embedding"],
            "total_capabilities": 4,
        }