# Entry point for Kitchen Worker import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from shared.logging_config import setup_logging
from execute_order import execute_order
from temporalio.contrib.pydantic import pydantic_data_converter
import logging

logger = logging.getLogger("kitchen_main")

async def main():
    """
    Entry point for the kitchen worker service. Connects to the Temporal server, initializes the worker,
    and starts listening for execute_order activity tasks.

    Args:
        None
    Returns:
        None
    Raises:
        Logs and exits on any connection or worker errors.
    """
    logger.info("main() called for kitchen worker")
    logger.debug(f"Environment LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
    temporal_server = os.getenv("TEMPORAL_ADDRESS")
    logger.info(f"Connecting to Temporal server at {temporal_server}")
    try:
        client = await Client.connect(
            temporal_server,
            data_converter=pydantic_data_converter
        )
        logger.info("Successfully connected to Temporal server")
        logger.info("Initializing worker with execute_order activity")
        worker = Worker(
            client,
            task_queue="kitchen-task-queue",
            activities=[execute_order]
        )
        logger.info("Starting kitchen worker - listening for execute order requests")
        await worker.run()
        logger.info("Kitchen worker stopped")
    except Exception as e:
        logger.error(f"Error in kitchen worker main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger = setup_logging("kitchen_worker", os.getenv("LOG_LEVEL", "INFO"))
    logger.info("Initializing kitchen worker")
    import asyncio
    asyncio.run(main())
