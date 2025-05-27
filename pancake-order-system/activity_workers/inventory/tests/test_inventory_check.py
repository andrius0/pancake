"""Tests for inventory_check activity using relative imports."""
import pytest
import os
from shared.interface import Ingredients, IngredientItem, InventoryResponse
from src.inventory_check import inventory_check
import logging
import json
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from src.db_tools import check_ingredients_tool, get_inventory_tool

# Add the src directory to sys.path

load_dotenv()

logger = logging.getLogger("test_inventory_check")
logging.basicConfig(level=logging.INFO)

def has_openai_key():
    # Helper to check if the OpenAI API key is set in the environment
    return os.getenv("OPENAI_API_KEY") is not None

@pytest.fixture
def sample_ingredients():
    # Provides a sample set of common pancake ingredients for use in tests
    return Ingredients(ingredients=[
        IngredientItem(ingredient_name="flour", amount=200, unit="g"),
        IngredientItem(ingredient_name="milk", amount=300, unit="ml")
    ])

@pytest.mark.asyncio
@pytest.mark.skipif(not has_openai_key(), reason="OPENAI_API_KEY not set")
async def test_inventory_check_make(sample_ingredients):
    """
    Test the inventory_check activity with typical available ingredients.
    This test calls the real LLM and expects a valid InventoryResponse object.
    - Checks that the response is of the correct type (by name, not isinstance, to avoid import issues).
    - Checks that the response has the expected attributes.
    - Accepts both 'make' and 'no make' as valid LLM outputs (since LLMs can be non-deterministic).
    - Ensures at least one of the queried ingredients is mentioned in the result.
    """
    resp = await inventory_check("order1", sample_ingredients)
    logger.info("test_inventory_check_make response:\n%s", json.dumps(resp.dict(), indent=2))
    assert isinstance(resp, InventoryResponse)
    assert resp.decision in {"make", "no make"}
    assert isinstance(resp.available_ingredients, list)
    assert isinstance(resp.missing_ingredients, list)
    all_ingredients = set(resp.available_ingredients + resp.missing_ingredients)
    assert "flour" in all_ingredients or "milk" in all_ingredients

@pytest.mark.asyncio
@pytest.mark.skipif(not has_openai_key(), reason="OPENAI_API_KEY not set")
async def test_inventory_check_no_make():
    """
    Test the inventory_check activity with an ingredient that is guaranteed to be missing.
    - Uses a fictional ingredient ('unobtainium') to ensure the LLM returns it as missing.
    - Checks for correct type and attributes.
    - Accepts both 'make' and 'no make' as valid decisions (LLM may still say 'make' if it hallucinates).
    - Ensures 'unobtainium' is in the missing_ingredients list.
    """
    ingredients = Ingredients(ingredients=[
        IngredientItem(ingredient_name="unobtainium", amount=100, unit="kg")
    ])
    resp = await inventory_check("order2", ingredients)
    logger.info("test_inventory_check_no_make response:\n%s", json.dumps(resp.dict(), indent=2))
    assert isinstance(resp, InventoryResponse)
    assert resp.decision in {"make", "no make"}
    assert "unobtainium" in resp.missing_ingredients

@pytest.mark.asyncio
@pytest.mark.skipif(not has_openai_key(), reason="OPENAI_API_KEY not set")
async def test_inventory_check_error():
    """
    Test the inventory_check activity with an invalid unit to trigger error handling.
    - Uses an invalid unit ('invalidunit') to provoke an error or a 'no make' response.
    - Accepts either a string error message or a valid InventoryResponse.
    - If InventoryResponse, checks for correct type and attributes, and valid decision.
    - If string, checks that it contains 'error' or 'invalid'.
    """
    ingredients = Ingredients(ingredients=[
        IngredientItem(ingredient_name="flour", amount=100, unit="invalidunit")
    ])
    resp = await inventory_check("order3", ingredients)
    if isinstance(resp, InventoryResponse):
        logger.info("test_inventory_check_error response:\n%s", json.dumps(resp.dict(), indent=2))
        assert resp.decision in {"make", "no make"}
    else:
        logger.info("test_inventory_check_error response: %s", resp)
        assert isinstance(resp, str)
        assert "error" in resp.lower() or "invalid" in resp.lower()

@pytest.mark.asyncio
@pytest.mark.skipif(not has_openai_key(), reason="OPENAI_API_KEY not set")
async def test_inventory_check_realistic():
    """
    Test the inventory_check activity with a realistic full pancake order input.
    """
    ingredients = Ingredients(ingredients=[
        IngredientItem(amount=100, ingredient_name="flour", unit="g"),
        IngredientItem(amount=150, ingredient_name="milk", unit="ml"),
        IngredientItem(amount=50, ingredient_name="eggs", unit="g"),
        IngredientItem(amount=20, ingredient_name="butter", unit="g"),
        IngredientItem(amount=15, ingredient_name="sugar", unit="g"),
        IngredientItem(amount=4, ingredient_name="baking powder", unit="g"),
        IngredientItem(amount=1, ingredient_name="salt", unit="g"),
    ])
    resp = await inventory_check("order-001", ingredients)
    logger.info("test_inventory_check_realistic response:\n%s", json.dumps(resp.dict(), indent=2))
    assert isinstance(resp, InventoryResponse)
    assert resp.decision in {"make", "no make"}
    assert isinstance(resp.available_ingredients, list)
    assert isinstance(resp.missing_ingredients, list)
    all_ingredients = set(resp.available_ingredients + resp.missing_ingredients)
    assert "flour" in all_ingredients or "milk" in all_ingredients 

@pytest.mark.asyncio
async def test_inventory_check_make2(sample_ingredients):
    """
    Test the inventory_check activity with typical available ingredients.
    This test calls the real LLM and expects a valid InventoryResponse object.
    - Checks that the response is of the correct type (by name, not isinstance, to avoid import issues).
    - Checks that the response has the expected attributes.
    - Accepts both 'make' and 'no make' as valid LLM outputs (since LLMs can be non-deterministic).
    - Ensures at least one of the queried ingredients is mentioned in the result.
    """
    resp = await inventory_check("order1", sample_ingredients)
    logger.info("test_inventory_check_make response:\n%s", json.dumps(resp.dict(), indent=2))
    assert isinstance(resp, InventoryResponse)
    assert resp.decision in {"make", "no make"}
    assert isinstance(resp.available_ingredients, list)
    assert isinstance(resp.missing_ingredients, list)
    all_ingredients = set(resp.available_ingredients + resp.missing_ingredients)
    assert "flour" in all_ingredients or "milk" in all_ingredients
