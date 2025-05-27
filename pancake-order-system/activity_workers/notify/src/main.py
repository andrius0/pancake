# Entry point for Notify Worker 
import asyncio
from temporalio.worker import Worker
from temporalio.client import Client
from shared.logging_config import setup_logging
import logging
from notify import notify
import os

async def main():
    setup_logging("notify_worker")
    logger = logging.getLogger("notify_worker.main")
    client = await Client.connect(os.getenv("TEMPORAL_ADDRESS"))
    logger.info("Connected to Temporal server")
    worker = Worker(
        client,
        task_queue="notification-task-queue",
        activities=[notify],
    )
    logger.info("Starting notify worker...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main()) 