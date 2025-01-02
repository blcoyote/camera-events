import redis
from typing import Set

from lib.settings import get_settings

# 30 days in seconds
THIRTY_DAYS_SECONDS = 30 * 24 * 60 * 60

class RedisSetClient:
    """
    A Redis client wrapper for set operations with type safety.
    """
    def __init__(self, host: str = get_settings().redis_host, port: int = 6379, db: int = 0, password: str = get_settings().redis_password):
        """
        Initialize Redis connection.
        
        Args:
            host: Redis host address
            port: Redis port number
            db: Redis database number
            password: Redis password
        """
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True, password=password)
    
    def add_to_set(self, set_name: str, value: str) -> bool:
        """
        Add a string value to a Redis set with 30-day expiration.
        
        Args:
            set_name: Name of the Redis set
            value: String value to add
            
        Returns:
            bool: True if value was added, False if already existed
        """
        added = bool(self.client.sadd(set_name, value))
        # Reset expiration time to 30 days whenever a new element is added
        self.client.expire(set_name, THIRTY_DAYS_SECONDS)
        return added
    
    def get_set(self, set_name: str) -> Set[str]:
        """
        Retrieve all members of a set as a Python set.
        
        Args:
            set_name: Name of the Redis set
            
        Returns:
            Set[str]: Python set containing all members
        """
        return set(self.client.smembers(set_name))
