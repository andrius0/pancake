import os
import logging
import redis
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Get Redis configuration from environment variables
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_CHANNEL = os.getenv('REDIS_CHANNEL', 'orders')


def main():
    logging.info(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT} (db={REDIS_DB}) with channel '{REDIS_CHANNEL}'...")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        # Test connection
        r.ping()
        logging.info("Successfully connected to Redis.")
    except Exception as e:
        logging.error(f"Failed to connect to Redis: {e}")
        return
    pubsub = r.pubsub()
    pubsub.subscribe(REDIS_CHANNEL)
    logging.info(f"Subscribed to Redis channel: {REDIS_CHANNEL}")
    for message in pubsub.listen():
        logging.debug(f"Raw message from pubsub: {message}")
        logging.info(f"Event type: {message.get('type')}, full message: {message}")
        if message.get('type') == 'message':
            try:
                decoded = message['data'].decode('utf-8')
                logging.info(f"Decoded message: {decoded}")
            except Exception as e:
                logging.error(f"Error decoding message: {e}")


if __name__ == "__main__":
    main() 