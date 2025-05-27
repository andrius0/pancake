from dotenv import load_dotenv
load_dotenv()
# Analyze order using LangChain and OpenAI 
from temporalio import activity
from shared.interface import Ingredients
from langchain_openai import ChatOpenAI
import os
import logging
import json

@activity.defn
async def analyze_order(customer_order: str) -> Ingredients:
    """
    Analyze the customer's order to determine required ingredients.
    Args:
        customer_order: String containing the customer's order details
    Returns:
        Ingredients object containing the list of required ingredients
    """
    logger = logging.getLogger("analyze_order_activity")
    logger.info("Starting analysis of customer order.")
    logger.info(f"Order to be analyzed: {customer_order}")
    try:
        llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        structured_llm = llm.with_structured_output(Ingredients)
        prompt = (
            "You are a chef specializing in world-famous custom pancakes. "
            "You receive an order for: {order}. "
            "You need to estimate the amount of ingredients required. If no amount is provided, "
            "assume a normal meal size one would get at a generic restaurant.\n\n"
            "Provide a list of ingredients and their amounts.\n"
            "- Estimate the amount of each required ingredient.\n"
            "- Return a structured list of ingredients, their amounts, and units.\n"
            "- Use only standard units: grams (g), kilograms (kg), milliliters (ml), or liters (l).\n"
            "- Do not use 'pieces', 'units', or similar.\n"
            "- Each ingredient should have: ingredient_name (str), amount (float), unit (str).\n"
            "- Common ingredients include: flour, eggs, milk, butter, sugar, baking powder, salt."
        )
        result = await structured_llm.ainvoke(prompt.format(order=customer_order))
        logger.info("Order analysis completed.")
        logger.info(f"Analysis output: {result.model_dump()}")
        return result
    except Exception as e:
        logger.error(f"Error in analyze_order_activity: {e}", exc_info=True)
        raise 