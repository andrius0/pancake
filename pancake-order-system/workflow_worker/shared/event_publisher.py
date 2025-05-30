import redis.asyncio as aioredis
from typing import Optional, Dict
import json
import logging
import os

# Configure module-level logger
logger = logging.getLogger(__name__)

class EventPublisher:
    """
    Publishes events to a Redis Pub/Sub channel.
    Handles connection management and ensures messages conform to the required structure.
    """
    def __init__(self, redis_url: str = None):
        """
        Initialize the EventPublisher with a Redis connection URL.
        Args:
            redis_url (str): The Redis server URL.
        """
        if redis_url is None:
            redis_url = os.getenv("REDIS_ADDRESS", "redis://localhost:6379")
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        # Log at info level for startup
        logger.info(f"EventPublisher initialized with Redis URL: {self.redis_url}")

    async def publish_event(self, channel: str, message: Dict[str, str]) -> None:
        """
        Publishes a message to the specified Redis Pub/Sub channel.
        Args:
            channel (str): The channel to publish to.
            message (Dict[str, str]): The message to publish. Must include 'status', 'message', 'order_id'.
        Raises:
            ValueError: If the message does not include all required fields.
        """
        try:
            # Ensure the message contains all required fields
            if not all(k in message for k in ('status', 'message', 'order_id')):
                logger.error(f"Message missing required fields: {message}")
                raise ValueError("Message must include 'status', 'message', and 'order_id' fields.")
            # Lazily initialize the Redis connection if not already done
            if not self._redis:
                self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
                logger.info("Redis connection established.")
            # Publish the message as a JSON string
            logger.info(f"Publishing to channel '{channel}': {message}")
            await self._redis.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Exception in publish_event: {e}")
            raise 