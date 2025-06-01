from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from shared.interface import OrderRequest, OrderResponse
from shared.logging_config import setup_logging, log_with_temporal_context
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
import os
import json
from dotenv import load_dotenv
from shared.event_publisher import EventPublisher
import asyncio

load_dotenv()

REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "orders")

logger = setup_logging("order_service")

app = FastAPI(
    title="Pancake Order Service",
    description="API for managing pancake orders with AI-powered ingredient analysis",
    version="1.0.0"
)

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:5002", # Allow requests from your front-end
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderRequest):
    try:
        # Publish event to Redis
        publisher = EventPublisher()
        event_message = {
            "status": "received",
            "message": "Order has been received and is being processed.",
            "order_id": str(order.order_id),
        }
        asyncio.create_task(publisher.publish_event(REDIS_CHANNEL, event_message))
        
        log_with_temporal_context(
            logger,
            "info",
            f"Received new order request: {order.model_dump_json(indent=2)}"
        )
        # Connect to Temporal
        temporal_server = os.getenv("TEMPORAL_ADDRESS")
        log_with_temporal_context(
            logger,
            "info",
            f"Connecting to Temporal server at {temporal_server}"
        )
        client = await Client.connect(
            temporal_server,
            data_converter=pydantic_data_converter
        )
        log_with_temporal_context(
            logger,
            "info",
            "Successfully connected to Temporal server"
        )
        # Generate workflow ID
        workflow_id = f"pancake-workflow-{order.order_id}"
        log_with_temporal_context(
            logger,
            "info",
            f"Generated workflow ID: {workflow_id}"
        )
        # Start the workflow
        log_with_temporal_context(
            logger,
            "info",
            f"Starting workflow with ID: {workflow_id}"
        )
        handle = await client.start_workflow(
            "PancakeOrderWorkflow",
            args=[
                order.order_id,
                order
            ],
            id=workflow_id,
            task_queue="pancake-task-queue"
        )
        log_with_temporal_context(
            logger,
            "info",
            f"Successfully started workflow with ID: {workflow_id}"
        )
        response = OrderResponse(
            order_id=order.order_id,
            workflow_id=workflow_id,
            status="accepted",
            message="Order accepted and workflow started"
        )
        log_with_temporal_context(
            logger,
            "info",
            f"Returning response for order {order.order_id}: {response.model_dump_json(indent=2)}"
        )
        return response
    except Exception as e:
        log_with_temporal_context(
            logger,
            "error",
            f"Error processing order: {str(e)}",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process order: {str(e)}"
        )

@app.get("/health", tags=["Health"])
async def health_check():
    log_with_temporal_context(
        logger,
        "info",
        "Health check requested"
    )
    return {"status": "healthy"} 