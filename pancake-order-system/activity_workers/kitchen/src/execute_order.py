from temporalio import activity
from shared.interface import Ingredients
from db_tools_kitchen import subtract_ingredient_amount
import logging
import json

logger = logging.getLogger(__name__)

@activity.defn
async def execute_order(ingredients: Ingredients) -> Ingredients:
    """
    Executes the kitchen order by consuming the specified ingredients from the database.

    Args:
        ingredients (Ingredients): An Ingredients object containing a list of IngredientItem objects to be consumed.

    Returns:
        Ingredients: An Ingredients object with updated IngredientItem objects after consumption.

    Raises:
        Returns the original Ingredients object if any error occurs during processing.
    """
    logger.info(f"execute_order called with ingredients: {ingredients}")
    updated_ingredients = []
    try:
        for ingredient in ingredients.ingredients:
            logger.info(f"Consuming ingredient: {ingredient.ingredient_name}, amount: {ingredient.amount} {ingredient.unit}")
            # Subtract the ingredient amount in the database and get the updated IngredientItem
            updated_ingredient = subtract_ingredient_amount(
                ingredient.ingredient_name,
                ingredient.amount,
                ingredient.unit
            )
            logger.info(f"Updated ingredient: {updated_ingredient}")
            updated_ingredients.append(updated_ingredient)
        result_ingredients = Ingredients(ingredients=updated_ingredients)
        logger.info("All ingredients consumed successfully: %s", json.dumps(result_ingredients.model_dump()))
        return result_ingredients
    except Exception as e:
        logger.error(f"Error consuming ingredients: {e}", exc_info=True)
        # Return the original ingredients with their original amounts if error
        logger.info("Returning original ingredients due to error: %s", json.dumps(ingredients.model_dump()))
        return ingredients



