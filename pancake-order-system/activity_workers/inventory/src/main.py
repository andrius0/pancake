import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from temporalio.client import Client
from temporalio.worker import Worker
from shared.logging_config import setup_logging
from inventory_check import inventory_check
from temporalio.contrib.pydantic import pydantic_data_converter

async def main():
    # Load environment variables
    load_dotenv()
    
    # Required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    logger = setup_logging("inventory_worker", os.getenv("LOG_LEVEL", "INFO"))
    logger.info("Starting inventory worker")
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    try:
        temporal_server = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
        logger.info(f"Connecting to Temporal server at {temporal_server}")
        
        client = await Client.connect(
            temporal_server,
            data_converter=pydantic_data_converter
        )
        logger.info("Successfully connected to Temporal server")

        logger.info("Initializing worker with inventory_check activity")
        worker = Worker(
            client,
            task_queue="inventory-task-queue",
            activities=[inventory_check]
        )

        logger.info("Starting inventory worker - listening for inventory check requests")
        await worker.run()
        logger.info("Inventory worker stopped")

    except Exception as e:
        logger.error(f"Critical error in inventory worker: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    logger = setup_logging("inventory_worker", os.getenv("LOG_LEVEL", "INFO"))
    logger.info("Initializing inventory worker")
    asyncio.run(main())
