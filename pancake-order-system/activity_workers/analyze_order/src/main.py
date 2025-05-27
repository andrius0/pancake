# Entry point for Analyze Order Worker 
from temporalio.worker import Worker
from temporalio.client import Client
from shared.logging_config import setup_logging
import asyncio
import logging
from analyze_order import analyze_order
import os
from dotenv import load_dotenv

async def main():
    setup_logging("analyze_order_worker")
    logger = logging.getLogger("analyze_order_worker.main")
    load_dotenv()
    client = await Client.connect(os.getenv("TEMPORAL_ADDRESS"))
    logger.info("Connected to Temporal server")
    worker = Worker(
        client,
        task_queue="analyze-order-queue",
        activities=[analyze_order],
    )
    logger.info("Starting analyze_order worker...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main()) 