import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.pydantic import pydantic_data_converter
from shared.logging_config import setup_logging
from pancake_workflow import PancakeOrderWorkflow
from dotenv import load_dotenv

load_dotenv()

async def main():
    logger = setup_logging("workflow_worker", os.getenv("LOG_LEVEL", "INFO"))

    try:
        temporal_server = os.getenv("TEMPORAL_ADDRESS")
        logger.info(f"Connecting to Temporal server at {temporal_server}")
        
        client = await Client.connect(
            temporal_server,
            data_converter=pydantic_data_converter
        )
        logger.info("Successfully connected to Temporal server")

        logger.info("Initializing workflow worker with PancakeOrderWorkflow")
        worker = Worker(
            client,
            task_queue="pancake-task-queue",
            workflows=[PancakeOrderWorkflow]
        )

        logger.info("Starting workflow worker - listening for pancake orders")
        await worker.run()
        logger.info("Workflow worker stopped")

    except Exception as e:
        logger.error(f"Critical error in workflow worker: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    logger = setup_logging("workflow_worker", os.getenv("LOG_LEVEL", "INFO"))
    logger.info("Starting pancake order workflow worker")
    asyncio.run(main())
