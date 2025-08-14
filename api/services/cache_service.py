import hashlib
from typing import List, Optional
from loguru import logger
from database.redis_client import RedisSetClient
from models.event_model import CameraEvent, CameraEventQueryParams

class EventCacheService:
    """
    Service for caching camera events with Redis.
    """
    
    def __init__(self):
        """Initialize the cache service with Redis client."""
        self.redis_client = RedisSetClient()
        self.cache_prefix = "events"
        self.ttl_seconds = 10 * 60  # 10 minutes
    
    def _generate_cache_key(self, params: CameraEventQueryParams) -> str:
        """
        Generate a unique cache key based on query parameters.
        
        Args:
            params: Query parameters for events
            
        Returns:
            str: Unique cache key
        """
        # Create a string representation of the parameters
        param_dict = params.model_dump() if hasattr(params, 'model_dump') else params.dict()
        # Sort the dictionary to ensure consistent ordering
        sorted_params = sorted(param_dict.items())
        param_string = str(sorted_params)
        
        # Generate a hash for the parameters to create a shorter, unique key
        param_hash = hashlib.md5(param_string.encode()).hexdigest()
        
        return f"{self.cache_prefix}:{param_hash}"
    
    def get_cached_events(self, params: CameraEventQueryParams) -> Optional[List[CameraEvent]]:
        """
        Retrieve cached events for the given parameters.
        
        Args:
            params: Query parameters for events
            
        Returns:
            List of cached events or None if not found
        """
        cache_key = self._generate_cache_key(params)
        cached_data = self.redis_client.get_cache(cache_key)
        
        if cached_data:
            logger.info(f"Cache HIT for key: {cache_key}")
            # Convert the cached data back to CameraEvent objects
            return [CameraEvent(**event_data) for event_data in cached_data]
        else:
            logger.info(f"Cache MISS for key: {cache_key}")
        
        return None
    
    def cache_events(self, params: CameraEventQueryParams, events: List[CameraEvent]) -> bool:
        """
        Cache the events for the given parameters.
        
        Args:
            params: Query parameters for events
            events: List of events to cache
            
        Returns:
            bool: True if cached successfully
        """
        cache_key = self._generate_cache_key(params)
        
        # Convert events to serializable format
        events_data = [event.model_dump() if hasattr(event, 'model_dump') else event.dict() for event in events]
        
        success = self.redis_client.set_cache(cache_key, events_data, self.ttl_seconds)
        
        if success:
            logger.info(f"Cache SET for key: {cache_key} with {len(events)} events")
        else:
            logger.error(f"Cache SET FAILED for key: {cache_key}")
        
        return success
    
    def bust_cache(self, params: Optional[CameraEventQueryParams] = None) -> int:
        """
        Bust the cache for specific parameters or all event caches.
        
        Args:
            params: Specific parameters to bust cache for, or None to bust all
            
        Returns:
            int: Number of cache entries deleted
        """
        if params:
            # Bust specific cache entry
            cache_key = self._generate_cache_key(params)
            deleted = 1 if self.redis_client.delete_cache(cache_key) else 0
            logger.info(f"Cache BUST for specific key: {cache_key}")
            return deleted
        else:
            # Bust all event caches
            deleted = self.redis_client.delete_cache_pattern(f"{self.cache_prefix}:*")
            logger.info(f"Cache BUST ALL: {deleted} entries deleted")
            return deleted

# Create a singleton instance
event_cache_service = EventCacheService()