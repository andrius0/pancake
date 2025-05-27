"""
Unit tests for the kitchen worker's execute_order activity.

These tests verify:
- Successful deduction of ingredients from inventory (real DB interaction)
- Proper error handling when inventory is insufficient
- Proper error handling when an invalid unit is provided

All database interactions are real. The test database must be available and kitchen_inventory table must exist.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
import asyncio
import logging
from sqlalchemy import create_engine, text
from shared.interface import IngredientItem, Ingredients
from src.execute_order import execute_order


# Configure logging for the test module
test_logger = logging.getLogger("test_execute_order")
test_logger.setLevel(logging.DEBUG)

DB_URL = "postgresql://postgres:postgres@localhost:5432/restaurant"
engine = create_engine(DB_URL)

def setup_inventory(ingredient_name, amount, unit):
    with engine.begin() as conn:
        # Remove if exists
        conn.execute(text("DELETE FROM kitchen_inventory WHERE ingredient = :name"), {"name": ingredient_name})
        # Insert new
        conn.execute(text("INSERT INTO kitchen_inventory (ingredient, available_amount, unit) VALUES (:name, :amount, :unit)"), {
            "name": ingredient_name,
            "amount": amount,  # just the float, e.g., 1000
            "unit": unit       # e.g., "g"
        })

def get_inventory_amount(ingredient_name):
    with engine.begin() as conn:
        result = conn.execute(text("SELECT available_amount FROM kitchen_inventory WHERE ingredient = :name"), {"name": ingredient_name}).fetchone()
        return result[0] if result else None

def cleanup_inventory(ingredient_name):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM kitchen_inventory WHERE ingredient = :name"), {"name": ingredient_name})

@pytest.mark.asyncio
async def test_execute_order_success():
    """
    Test that execute_order correctly deducts ingredient amounts when inventory is sufficient.
    The result should be an Ingredients object with updated amounts.
    """
    test_logger.info("Starting test_execute_order_success")
    # Arrange
    setup_inventory("flour", 1000, "g")
    setup_inventory("milk", 1000, "ml")
    test_ingredients = Ingredients(ingredients=[
        IngredientItem(ingredient_name="flour", amount=200, unit="g"),
        IngredientItem(ingredient_name="milk", amount=300, unit="ml")
    ])
    # Act
    result = await execute_order(test_ingredients)
    test_logger.info(f"Result: {result}")
    # Assert
    assert isinstance(result, Ingredients)
    assert result.ingredients[0].ingredient_name == "flour"
    assert result.ingredients[0].amount == 800  # 1000 - 200
    assert result.ingredients[1].ingredient_name == "milk"
    assert result.ingredients[1].amount == 700  # 1000 - 300
    # Check DB state
    flour_amount = get_inventory_amount("flour")
    milk_amount = get_inventory_amount("milk")
    assert flour_amount == 800.0
    assert milk_amount == 700.0
    # Cleanup
    cleanup_inventory("flour")
    cleanup_inventory("milk")
    test_logger.info("test_execute_order_success passed")

@pytest.mark.asyncio
async def test_execute_order_insufficient_inventory():
    """
    Test that execute_order returns the original ingredients if there is not enough inventory.
    The result should be the same as the input Ingredients object.
    """
    test_logger.info("Starting test_execute_order_insufficient_inventory")
    setup_inventory("flour", 100, "g")  # Not enough for the order
    test_ingredients = Ingredients(ingredients=[
        IngredientItem(ingredient_name="flour", amount=200, unit="g")
    ])
    result = await execute_order(test_ingredients)
    test_logger.info(f"Result: {result}")
    # Should return the original ingredients on error
    assert result == test_ingredients
    # Cleanup
    cleanup_inventory("flour")
    test_logger.info("test_execute_order_insufficient_inventory passed")

@pytest.mark.asyncio
async def test_execute_order_invalid_unit():
    """
    Test that execute_order returns the original ingredients if an invalid unit is provided.
    The result should be the same as the input Ingredients object.
    """
    test_logger.info("Starting test_execute_order_invalid_unit")
    setup_inventory("flour", 1000, "g")
    test_ingredients = Ingredients(ingredients=[
        IngredientItem(ingredient_name="flour", amount=200, unit="invalidunit")
    ])
    result = await execute_order(test_ingredients)
    test_logger.info(f"Result: {result}")
    assert result == test_ingredients
    # Cleanup
    cleanup_inventory("flour")
    test_logger.info("test_execute_order_invalid_unit passed") 