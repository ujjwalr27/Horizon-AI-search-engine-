import os
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
import urllib.parse
import logging
import json
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()

class RenderRedisCache:
    def __init__(self):
        """Initialize Redis cache."""
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load Redis URL
        self.redis_url = os.getenv('REDIS_URL')
        
        # Convert CACHE_EXPIRY to int with error handling
        try:
            self.default_expiry = int(os.getenv('CACHE_EXPIRY', '600'))
        except ValueError:
            self.logger.warning("Invalid CACHE_EXPIRY value, using default of 600 seconds")
            self.default_expiry = 600
        
        if not self.redis_url:
            raise ValueError("Missing required Redis configuration (REDIS_URL)")

        # Initialize connections as None
        self.redis_client = None
        self.async_client = None
        
        self._initialize_connection()
        self._initialize_async_connection()

    def _initialize_connection(self):
        """Initialize synchronous Redis connection."""
        try:
            self.redis_client = Redis.from_url(
                url=self.redis_url,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30  # Added health check
            )
            # Verify connection is working
            if not self.redis_client.ping():
                raise ConnectionError("Redis ping failed")
            self.logger.info("Successfully connected to Redis (sync)!")
        except Exception as e:
            self.logger.error(f"Error initializing sync Redis connection: {str(e)}")
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    def _initialize_async_connection(self):
        """Initialize async Redis connection."""
        try:
            self.async_client = AsyncRedis.from_url(
                url=self.redis_url,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30  # Added health check
            )
            self.logger.info("Successfully initialized async Redis connection!")
        except Exception as e:
            self.logger.error(f"Error initializing async Redis connection: {str(e)}")
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    def put(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """Store data in Redis synchronously."""
        if not self.redis_client:
            raise ConnectionError("Redis client not initialized")
            
        if key is None or value is None:
            self.logger.error("Key or value cannot be None")
            return False
            
        try:
            serialized_data = json.dumps(value)
            return bool(self.redis_client.set(
                key, 
                serialized_data,
                ex=expiry or self.default_expiry
            ))
        except json.JSONEncodeError as e:
            self.logger.error(f"JSON serialization error in PUT: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error in sync PUT: {str(e)}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis synchronously."""
        if not self.redis_client:
            raise ConnectionError("Redis client not initialized")
            
        if key is None:
            self.logger.error("Key cannot be None")
            return None
            
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON deserialization error in GET: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error in sync GET: {str(e)}")
            return None

    async def async_put(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """Store data in Redis asynchronously."""
        if not self.async_client:
            raise ConnectionError("Async Redis client not initialized")
            
        if key is None or value is None:
            self.logger.error("Key or value cannot be None")
            return False
            
        try:
            serialized_data = json.dumps(value)
            return bool(await self.async_client.set(
                key, 
                serialized_data,
                ex=expiry or self.default_expiry
            ))
        except json.JSONEncodeError as e:
            self.logger.error(f"JSON serialization error in async PUT: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error in async PUT: {str(e)}")
            return False

    async def async_get(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis asynchronously."""
        if not self.async_client:
            raise ConnectionError("Async Redis client not initialized")
            
        if key is None:
            self.logger.error("Key cannot be None")
            return None
            
        try:
            data = await self.async_client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON deserialization error in async GET: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error in async GET: {str(e)}")
            return None

    async def async_delete(self, key: str) -> bool:
        """Delete a key from Redis asynchronously."""
        if not self.async_client:
            raise ConnectionError("Async Redis client not initialized")
            
        if key is None:
            self.logger.error("Key cannot be None")
            return False
            
        try:
            return bool(await self.async_client.delete(key))
        except Exception as e:
            self.logger.error(f"Error in async DELETE: {str(e)}")
            return False

    async def async_clear(self) -> bool:
        """Clear all data from Redis asynchronously."""
        if not self.async_client:
            raise ConnectionError("Async Redis client not initialized")
            
        try:
            return bool(await self.async_client.flushdb())
        except Exception as e:
            self.logger.error(f"Error in async CLEAR: {str(e)}")
            return False

    async def close(self):
        """Close both sync and async Redis connections."""
        try:
            if self.async_client:
                await self.async_client.close()
            if self.redis_client:
                self.redis_client.close()
            self.logger.info("Redis connections closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing Redis connections: {str(e)}")
            raise