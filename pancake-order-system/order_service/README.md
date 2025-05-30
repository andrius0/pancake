# Order Service

This service manages pancake orders and publishes order status events to Redis.

## Folder Structure

```
order_service/
├── shared/
│   ├── event_publisher.py
│   ├── interface.py
│   └── logging_config.py
├── src/
│   ├── __init__.py
│   ├── api.py
│   └── main.py
├── tests/
├── requirements.txt
├── Dockerfile
└── venv/
```

## Redis Event Publishing
- Publishes order status events to the Redis channel `orders`.
- Uses environment variable `REDIS_ADDRESS` for Redis connection (default: `redis://localhost:6379`).
- Events are published asynchronously and include fields: `status`, `message`, `order_id`.

## Design/Architecture
- **order_service** publishes events to the `orders` channel in Redis.
- **status_service** (in a separate repo/folder) subscribes to the same channel and logs messages.
- Both services must use the same Redis instance and channel name for communication.
- The system is designed for loose coupling and can be extended to support more event types or consumers. 