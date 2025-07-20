"""
Intelligent Caching System for Phase 2 Optimization
Implements response caching, model caching, and cache invalidation strategies
Target: 60-80% cache hit rate for repeated content
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import OrderedDict
import pickle

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    timestamp: float
    access_count: int
    last_accessed: float
    expiry_time: Optional[float] = None
    size_bytes: int = 0
    cache_type: str = "response"
    metadata: Dict[str, Any] = None

class IntelligentCacheManager:
    """
    Intelligent caching system with multiple cache types and strategies:
    - Response caching (text -> detection results)
    - Model caching (preloaded models)
    - Configuration caching (settings, weights)
    - Pattern caching (regex, NLP patterns)
    """
    
    def __init__(self, 
                 cache_dir: str = "cache",
                 max_memory_mb: int = 1024,
                 max_disk_mb: int = 5120,
                 default_ttl_seconds: int = 3600):
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache configuration
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_disk_bytes = max_disk_mb * 1024 * 1024
        self.default_ttl = default_ttl_seconds
        
        # In-memory caches (LRU-based)
        self.response_cache = OrderedDict()  # Fast access for repeated content
        self.model_cache = OrderedDict()     # Loaded models
        self.config_cache = OrderedDict()    # Configuration data
        self.pattern_cache = OrderedDict()   # Compiled patterns
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0,
            "cache_size_bytes": 0,
            "hit_rate": 0.0,
            "cache_types": {
                "response": {"hits": 0, "misses": 0},
                "model": {"hits": 0, "misses": 0},
                "config": {"hits": 0, "misses": 0},
                "pattern": {"hits": 0, "misses": 0}
            }
        }
        
        # Cache maintenance
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        logger.info(f"CacheManager initialized: {max_memory_mb}MB memory, {max_disk_mb}MB disk")
    
    def _generate_cache_key(self, content: str, cache_type: str, **kwargs) -> str:
        """Generate consistent cache key"""
        # Include relevant parameters in key generation
        key_data = {
            "content": content,
            "type": cache_type,
            **kwargs
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _get_cache_by_type(self, cache_type: str) -> OrderedDict:
        """Get appropriate cache based on type"""
        cache_map = {
            "response": self.response_cache,
            "model": self.model_cache,
            "config": self.config_cache,
            "pattern": self.pattern_cache
        }
        return cache_map.get(cache_type, self.response_cache)
    
    async def get(self, 
                  key: str, 
                  cache_type: str = "response",
                  default: Any = None) -> Any:
        """
        Get item from cache
        
        Args:
            key: Cache key
            cache_type: Type of cache (response, model, config, pattern)
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        try:
            self.stats["total_requests"] += 1
            cache = self._get_cache_by_type(cache_type)
            
            if key not in cache:
                self.stats["misses"] += 1
                self.stats["cache_types"][cache_type]["misses"] += 1
                
                # Try loading from disk for persistent cache types
                if cache_type in ["model", "config"]:
                    disk_value = await self._load_from_disk(key, cache_type)
                    if disk_value is not None:
                        await self.set(key, disk_value, cache_type)
                        return disk_value
                
                return default
            
            # Update access statistics
            entry = cache[key]
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # Check expiry
            if entry.expiry_time and time.time() > entry.expiry_time:
                await self.delete(key, cache_type)
                self.stats["misses"] += 1
                self.stats["cache_types"][cache_type]["misses"] += 1
                return default
            
            # Move to end (LRU)
            cache.move_to_end(key)
            
            # Update statistics
            self.stats["hits"] += 1
            self.stats["cache_types"][cache_type]["hits"] += 1
            self._update_hit_rate()
            
            return entry.value
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(self, 
                  key: str, 
                  value: Any, 
                  cache_type: str = "response",
                  ttl_seconds: Optional[int] = None) -> bool:
        """
        Set item in cache
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache
            ttl_seconds: Time to live (None for default)
            
        Returns:
            True if successful
        """
        try:
            cache = self._get_cache_by_type(cache_type)
            
            # Calculate size
            size_bytes = len(str(value).encode('utf-8'))
            
            # Set expiry
            expiry_time = None
            if ttl_seconds or self.default_ttl:
                ttl = ttl_seconds or self.default_ttl
                expiry_time = time.time() + ttl
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                access_count=1,
                last_accessed=time.time(),
                expiry_time=expiry_time,
                size_bytes=size_bytes,
                cache_type=cache_type,
                metadata={}
            )
            
            # Check if we need to evict
            await self._ensure_cache_space(cache, size_bytes)
            
            # Add to cache
            cache[key] = entry
            cache.move_to_end(key)
            
            # Update statistics
            self.stats["cache_size_bytes"] += size_bytes
            
            # Persist to disk for certain cache types
            if cache_type in ["model", "config"]:
                await self._save_to_disk(key, value, cache_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str, cache_type: str = "response") -> bool:
        """Delete item from cache"""
        try:
            cache = self._get_cache_by_type(cache_type)
            
            if key in cache:
                entry = cache[key]
                self.stats["cache_size_bytes"] -= entry.size_bytes
                del cache[key]
                
                # Remove from disk if applicable
                if cache_type in ["model", "config"]:
                    await self._remove_from_disk(key, cache_type)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def cache_response(self, 
                           text: str, 
                           detection_result: Dict[str, Any],
                           model_name: str = "ensemble",
                           ttl_seconds: int = 1800) -> bool:
        """
        Cache detection response for text
        
        Args:
            text: Input text
            detection_result: Detection result to cache
            model_name: Name of the model/ensemble
            ttl_seconds: Cache TTL (30 minutes default)
            
        Returns:
            True if cached successfully
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                text, 
                "response", 
                model=model_name,
                text_hash=hashlib.sha256(text.encode()).hexdigest()[:8]
            )
            
            # Prepare cache value
            cache_value = {
                "text": text,
                "result": detection_result,
                "model_name": model_name,
                "cached_at": time.time()
            }
            
            return await self.set(cache_key, cache_value, "response", ttl_seconds)
            
        except Exception as e:
            logger.error(f"Response caching error: {e}")
            return False
    
    async def get_cached_response(self, 
                                text: str, 
                                model_name: str = "ensemble") -> Optional[Dict[str, Any]]:
        """
        Get cached detection response for text
        
        Args:
            text: Input text
            model_name: Name of the model/ensemble
            
        Returns:
            Cached detection result or None
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                text, 
                "response", 
                model=model_name,
                text_hash=hashlib.sha256(text.encode()).hexdigest()[:8]
            )
            
            cached_value = await self.get(cache_key, "response")
            
            if cached_value and cached_value.get("text") == text:
                return cached_value.get("result")
            
            return None
            
        except Exception as e:
            logger.error(f"Response cache retrieval error: {e}")
            return None
    
    async def cache_model(self, 
                         model_name: str, 
                         model_object: Any,
                         metadata: Dict[str, Any] = None) -> bool:
        """
        Cache loaded model object
        
        Args:
            model_name: Name of the model
            model_object: The loaded model
            metadata: Additional metadata
            
        Returns:
            True if cached successfully
        """
        try:
            cache_value = {
                "model": model_object,
                "metadata": metadata or {},
                "loaded_at": time.time()
            }
            
            return await self.set(model_name, cache_value, "model")
            
        except Exception as e:
            logger.error(f"Model caching error for {model_name}: {e}")
            return False
    
    async def get_cached_model(self, model_name: str) -> Optional[Any]:
        """
        Get cached model object
        
        Args:
            model_name: Name of the model
            
        Returns:
            Cached model object or None
        """
        try:
            cached_value = await self.get(model_name, "model")
            
            if cached_value:
                return cached_value.get("model")
            
            return None
            
        except Exception as e:
            logger.error(f"Model cache retrieval error for {model_name}: {e}")
            return None
    
    async def _ensure_cache_space(self, cache: OrderedDict, required_bytes: int) -> None:
        """Ensure cache has space for new entry"""
        try:
            # Calculate current cache size
            current_size = sum(entry.size_bytes for entry in cache.values())
            
            # Evict LRU entries if needed
            while current_size + required_bytes > self.max_memory_bytes and cache:
                # Get LRU entry (first in OrderedDict)
                lru_key = next(iter(cache))
                lru_entry = cache[lru_key]
                
                current_size -= lru_entry.size_bytes
                self.stats["cache_size_bytes"] -= lru_entry.size_bytes
                self.stats["evictions"] += 1
                
                del cache[lru_key]
                
        except Exception as e:
            logger.error(f"Cache space management error: {e}")
    
    async def _load_from_disk(self, key: str, cache_type: str) -> Optional[Any]:
        """Load cache entry from disk"""
        try:
            disk_path = self.cache_dir / cache_type / f"{key}.pkl"
            
            if disk_path.exists():
                with open(disk_path, 'rb') as f:
                    return pickle.load(f)
            
            return None
            
        except Exception as e:
            logger.warning(f"Disk cache load error for {key}: {e}")
            return None
    
    async def _save_to_disk(self, key: str, value: Any, cache_type: str) -> bool:
        """Save cache entry to disk"""
        try:
            disk_dir = self.cache_dir / cache_type
            disk_dir.mkdir(exist_ok=True)
            
            disk_path = disk_dir / f"{key}.pkl"
            
            with open(disk_path, 'wb') as f:
                pickle.dump(value, f)
            
            return True
            
        except Exception as e:
            logger.warning(f"Disk cache save error for {key}: {e}")
            return False
    
    async def _remove_from_disk(self, key: str, cache_type: str) -> bool:
        """Remove cache entry from disk"""
        try:
            disk_path = self.cache_dir / cache_type / f"{key}.pkl"
            
            if disk_path.exists():
                disk_path.unlink()
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Disk cache removal error for {key}: {e}")
            return False
    
    def _update_hit_rate(self) -> None:
        """Update cache hit rate statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        if total_requests > 0:
            self.stats["hit_rate"] = (self.stats["hits"] / total_requests) * 100
    
    async def cleanup_expired(self) -> Dict[str, Any]:
        """Clean up expired cache entries"""
        try:
            current_time = time.time()
            
            if current_time - self.last_cleanup < self.cleanup_interval:
                return {"skipped": "too_recent"}
            
            cleanup_stats = {
                "expired_entries": 0,
                "freed_bytes": 0,
                "cache_types": {}
            }
            
            cache_types = ["response", "model", "config", "pattern"]
            
            for cache_type in cache_types:
                cache = self._get_cache_by_type(cache_type)
                expired_keys = []
                freed_bytes = 0
                
                for key, entry in cache.items():
                    if entry.expiry_time and current_time > entry.expiry_time:
                        expired_keys.append(key)
                        freed_bytes += entry.size_bytes
                
                # Remove expired entries
                for key in expired_keys:
                    del cache[key]
                    await self._remove_from_disk(key, cache_type)
                
                cleanup_stats["cache_types"][cache_type] = {
                    "expired": len(expired_keys),
                    "freed_bytes": freed_bytes
                }
                
                cleanup_stats["expired_entries"] += len(expired_keys)
                cleanup_stats["freed_bytes"] += freed_bytes
            
            self.stats["cache_size_bytes"] -= cleanup_stats["freed_bytes"]
            self.last_cleanup = current_time
            
            logger.info(f"Cache cleanup: {cleanup_stats['expired_entries']} expired entries, {cleanup_stats['freed_bytes']} bytes freed")
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return {"error": str(e)}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            await self.cleanup_expired()
            
            stats = self.stats.copy()
            
            # Add cache size information
            stats["cache_sizes"] = {}
            cache_types = ["response", "model", "config", "pattern"]
            
            for cache_type in cache_types:
                cache = self._get_cache_by_type(cache_type)
                stats["cache_sizes"][cache_type] = {
                    "entries": len(cache),
                    "size_bytes": sum(entry.size_bytes for entry in cache.values())
                }
            
            # Add memory usage
            stats["memory_usage"] = {
                "current_bytes": self.stats["cache_size_bytes"],
                "max_bytes": self.max_memory_bytes,
                "usage_percent": (self.stats["cache_size_bytes"] / self.max_memory_bytes) * 100
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}
    
    async def clear_cache(self, cache_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear cache entries
        
        Args:
            cache_type: Specific cache type to clear (None for all)
            
        Returns:
            Cleanup statistics
        """
        try:
            cleared_stats = {
                "cleared_entries": 0,
                "freed_bytes": 0,
                "cache_types": {}
            }
            
            if cache_type:
                cache_types = [cache_type]
            else:
                cache_types = ["response", "model", "config", "pattern"]
            
            for ct in cache_types:
                cache = self._get_cache_by_type(ct)
                entries_count = len(cache)
                freed_bytes = sum(entry.size_bytes for entry in cache.values())
                
                cache.clear()
                
                # Clear disk cache
                disk_dir = self.cache_dir / ct
                if disk_dir.exists():
                    import shutil
                    shutil.rmtree(disk_dir)
                
                cleared_stats["cache_types"][ct] = {
                    "cleared": entries_count,
                    "freed_bytes": freed_bytes
                }
                
                cleared_stats["cleared_entries"] += entries_count
                cleared_stats["freed_bytes"] += freed_bytes
            
            self.stats["cache_size_bytes"] -= cleared_stats["freed_bytes"]
            
            logger.info(f"Cache cleared: {cleared_stats['cleared_entries']} entries, {cleared_stats['freed_bytes']} bytes")
            
            return cleared_stats
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return {"error": str(e)}
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """
        Optimize cache by removing least used entries
        
        Returns:
            Optimization statistics
        """
        try:
            optimization_stats = {
                "optimized_entries": 0,
                "freed_bytes": 0,
                "cache_types": {}
            }
            
            cache_types = ["response", "model", "config", "pattern"]
            
            for cache_type in cache_types:
                cache = self._get_cache_by_type(cache_type)
                
                if not cache:
                    continue
                
                # Sort by access frequency (least used first)
                sorted_entries = sorted(
                    cache.items(),
                    key=lambda x: (x[1].access_count, x[1].last_accessed)
                )
                
                # Remove bottom 25% of entries
                removal_count = max(1, len(sorted_entries) // 4)
                freed_bytes = 0
                
                for key, entry in sorted_entries[:removal_count]:
                    freed_bytes += entry.size_bytes
                    del cache[key]
                    await self._remove_from_disk(key, cache_type)
                
                optimization_stats["cache_types"][cache_type] = {
                    "optimized": removal_count,
                    "freed_bytes": freed_bytes
                }
                
                optimization_stats["optimized_entries"] += removal_count
                optimization_stats["freed_bytes"] += freed_bytes
            
            self.stats["cache_size_bytes"] -= optimization_stats["freed_bytes"]
            
            logger.info(f"Cache optimized: {optimization_stats['optimized_entries']} entries removed, {optimization_stats['freed_bytes']} bytes freed")
            
            return optimization_stats
            
        except Exception as e:
            logger.error(f"Cache optimization error: {e}")
            return {"error": str(e)}