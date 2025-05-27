# Notification logic for Notify Worker 
from shared.interface import NotifyRequest, NotifyResponse
import logging
from temporalio import activity
from shared.logging_config import setup_logging

setup_logging("NotifyWorker")
logger = logging.getLogger("notify")

@activity.defn
async def notify(order_id: str, message: str) -> str:
    if message == "Order completed":
        logger.info(f"Order completed for order_id={order_id}")
        return "Order completed"
    else:
        logger.info(f"Order not completed for order_id={order_id}")
        return "Order not completed"