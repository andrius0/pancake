from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from typing import Dict, List
from shared.interface import OrderRequest, Ingredients
from dotenv import load_dotenv
import os

# workflow is kicked off by the order_service, by call to /order endpoint
# order_service will pass in the 
# order_id
# order_details
# ingredient_requirements   

from shared.event_publisher import EventPublisher
import asyncio

load_dotenv()

REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "orders")

@workflow.defn
class PancakeOrderWorkflow:
    @workflow.run
    async def run(
        self,
        order_id: str,
        order_details: OrderRequest
    ) -> Dict[str, str]:
        """
        Run the pancake order workflow.
        
        Args:
            order_id: Unique identifier for the order
            order_details: Order details including customer information
            ingredient_requirements: List of required ingredients
            
        Returns:
            Dictionary containing workflow execution results
        """
        # Add logging for workflow start
        workflow.logger.info(f"Workflow started for order_id={order_id}, customer={order_details.customer_name}")
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
            non_retryable_error_types=["ValueError"]  # Don't retry on invalid input
        )
        #######################
        # Analyze the order
        #######################
        workflow.logger.info(f"Analyzing order: {order_details.customer_order}")
        required_ingredients = await workflow.execute_activity(
            "analyze_order",
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
            task_queue="analyze-order-queue",
            args=[
                order_details.customer_order
            ]
        )
        workflow.logger.info(f"Required ingredients: {required_ingredients}")
        #######################
        # Inventory check
        #######################
        workflow.logger.info(f"Checking inventory for order_id={order_id}")
        inventory_check_result = await workflow.execute_activity(
            "inventory_check",
            args=[order_id, required_ingredients],
            task_queue="inventory-task-queue",
            schedule_to_close_timeout=timedelta(seconds=30)
        )
        workflow.logger.info(f"Inventory check result: {inventory_check_result}")

        #######################
        # if we have enough ingredients, we can make the order and notify the customer
        ####################### 
        if inventory_check_result["decision"] == "make":
            workflow.logger.info(f"Decision: MAKE. Sending to kitchen.")
            kitchen_result = await workflow.execute_activity(
                "execute_order",
                args=[order_id, required_ingredients],
                task_queue="kitchen-task-queue",
                schedule_to_close_timeout=timedelta(seconds=30)
            )
            workflow.logger.info(f"Kitchen result: {kitchen_result}")
            # call the notify activity
            workflow.logger.info(f"Notifying customer: Order completed for order_id={order_id}")
            await workflow.execute_activity(
                "notify",
                args=[order_id, "Order completed"],
                task_queue="notification-task-queue",
                schedule_to_close_timeout=timedelta(seconds=10)
            )

            return kitchen_result
        else:
            #######################
            # notify the customer about missing ingredients
            #######################  
            workflow.logger.info(f"Decision: NO MAKE. Notifying customer about missing ingredients.")
            await workflow.execute_activity(
                "notify",
                args=[order_id, "Not enough ingredients to make the order"],
                task_queue="notification-task-queue",
                schedule_to_close_timeout=timedelta(seconds=30)
            )
            return inventory_check_result

