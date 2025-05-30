# Status Service

This service listens to a Redis channel and logs any messages it receives.

## Folder Structure

```
status_service/
├── shared/
├── src/
│   ├── __init__.py
│   └── main.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Setup

1. Create a virtual environment and install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file and configure as needed:
   ```sh
   echo "REDIS_HOST=localhost" > .env
   echo "REDIS_PORT=6379" >> .env
   echo "REDIS_DB=0" >> .env
   echo "REDIS_CHANNEL=orders" >> .env
   ```

3. Run the service:
   ```sh
   python src/main.py
   ```

## Environment Variables
- `REDIS_HOST`: Redis server hostname (default: `localhost`)
- `REDIS_PORT`: Redis server port (default: `6379`)
- `REDIS_DB`: Redis database number (default: `0`)
- `REDIS_CHANNEL`: Redis channel to subscribe to (default: `orders`)

## Design/Architecture

- **order_service** publishes order status events to the Redis channel `orders` using an async publisher.
- **status_service** subscribes to the same `orders` channel and logs all received messages.
- Both services must use the same Redis instance and channel name for communication.
- The system is designed for loose coupling and can be extended to support more event types or consumers. 