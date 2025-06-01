from shared.logging_config import get_logger, log_with_temporal_context  # Remove log_with_temporal_context
import os
import logging
from typing import List, Dict
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel
from temporalio import activity

from db_tools import check_ingredients_tool, get_inventory_tool
from shared.interface import Ingredients, InventoryResponse

from shared.event_publisher import EventPublisher
import asyncio

load_dotenv()

REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "orders")

SYSTEM_PROMPT = """You are a kitchen inventory management assistant. Your task is to check if we have enough ingredients for an order.

You have access to two tools:
1. get_inventory - Get the current status of all inventory items.
2. check_ingredients - Check if specific ingredients are available in sufficient quantities. 
Tool can only handle one ingridient per call. If you need to check multiple ingredients, call the tool multiple times.
function can be called with the following input:
{
    "ingredient_name": str,
    "amount": str,
    "unit": str
}


When checking ingredients, follow these guidelines for units:
- Dry ingredients (flour, sugar, etc.): kg or g
- Liquids (milk, oil, etc.): L or ml
- do not use count items such as pieces, use weight instead
- Spices and small quantities: kg or g


Your final response must be in json format:
{
    "decision": "no make" or "make",
    "available_ingredients": ["ingredient1", "ingredient2"],
    "missing_ingredients": ["ingredient3", "ingredient4"]
}
"""

def format_ingredients(ingredients: Ingredients):
    return [
        {
            "name": ingredient.ingredient_name,
            "quantity": ingredient.amount,
            "unit": ingredient.unit
        }
        for ingredient in ingredients.ingredients
    ]

@activity.defn
async def inventory_check(order_id: str, ingredients: Ingredients) -> str:
    """
    Check if all required ingredients are available in inventory using LangGraph agent.
    Args:
        order_id: Unique identifier for the order
        ingredients: Ingredients object containing a list of Ingredient objects
    Returns:
        String indicating inventory status or error message
    """
    logger = logging.getLogger("inventory_check")
    logger.info(f"Checking inventory for order_id: {order_id} with ingredients: {ingredients}")
    try:
        model = ChatOpenAI(
            model="gpt-4.1",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        agent = create_react_agent(
            model=model,
            tools=[check_ingredients_tool, get_inventory_tool],
            prompt=SYSTEM_PROMPT,
            response_format=InventoryResponse
        )
        

        formatted_ingredients = format_ingredients(ingredients)
        initial_message = {
            "messages": [{
                "role": "user",
                "content": f"Check ingredients for order {order_id}: {formatted_ingredients}"
            }]
        }

        logger.info(f"Invoking agent with message: {initial_message}")

        response = agent.invoke(initial_message)
        
        structured = response["structured_response"]
        result = InventoryResponse(
            available_ingredients=structured.available_ingredients,
            missing_ingredients=structured.missing_ingredients,
            decision=structured.decision
        )
        logger.info("Inventory check response:\n%s", json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        
        # Publish event to Redis
        publisher = EventPublisher()
        event_message = {
            "status": "inventory_check",
            "message": f"Inventory check for order {order_id}: Decision - {result.decision}. Available: {', '.join(result.available_ingredients)}. Missing: {', '.join(result.missing_ingredients)}",
            "order_id": str(order_id),
        }
        asyncio.create_task(publisher.publish_event(REDIS_CHANNEL, event_message))
        return result


    except Exception as e:
        logger.error(f"Error in inventory_check: {e}", exc_info=True)
        if "AuthenticationError" in str(e):
            return "API auth failed"
        elif "RateLimitError" in str(e):
            return "API rate limit hit"
        elif "InvalidRequestError" in str(e):
            return "Invalid API request"
        elif "APIConnectionError" in str(e):
            return "API connection failed"
        return "Inventory check error"