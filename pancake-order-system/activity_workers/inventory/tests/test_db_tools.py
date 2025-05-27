"""Integration tests for db_tools using the real database."""
import pytest
import os
from sqlalchemy import create_engine, text
from src.db_tools import get_current_inventory, check_ingredient_availability, parse_amount
from shared.interface import InventoryItem
import logging
import json

logger = logging.getLogger("test_db_tools")
logging.basicConfig(level=logging.INFO)

DB_URL = os.getenv("INVENTORY_DB_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/restaurant")

def db_available():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

@pytest.mark.skipif(not db_available(), reason="PostgreSQL test DB not available")
def test_get_inventory_real_db():
    inv = get_current_inventory()
    try:
        inv_list = [item.model_dump() if hasattr(item, 'model_dump') else item for item in inv]
        logger.info("test_get_inventory_real_db inventory:\n%s", json.dumps(inv_list, indent=2))
    except Exception:
        logger.info("test_get_inventory_real_db inventory: %s", inv)
    # Should contain at least one known ingredient from init.sql
    found_flour = any(item.ingredient == "all-purpose flour" for item in inv)
    assert found_flour, "All-purpose flour should be present in inventory"
    found_almond_milk = any(item.ingredient == "almond milk" for item in inv)
    assert found_almond_milk, "Almond milk should be present in inventory"
    # Check that available_amount is a float and unit is a string
    for item in inv:
        amt = getattr(item, 'available_amount', None)
        unit = getattr(item, 'unit', None)
        assert isinstance(amt, float)
        assert isinstance(unit, str)

@pytest.mark.skipif(not db_available(), reason="PostgreSQL test DB not available")
def test_check_ingredient_availability_sufficient():
    """
    Ingredient is present in inventory and available in sufficient quantity.
    Assumes 'all-purpose flour' exists in DB with at least 200 g available.
    """
    result = check_ingredient_availability({"ingredient_name": "all-purpose flour", "amount": 200.0, "unit": "g"})
    assert result["all-purpose flour"] is True

@pytest.mark.skipif(not db_available(), reason="PostgreSQL test DB not available")
def test_check_ingredient_availability_insufficient():
    """
    Ingredient is present in inventory but not enough is available.
    Assumes 'all-purpose flour' exists in DB with less than 26000 g available.
    """
    result = check_ingredient_availability({"ingredient_name": "all-purpose flour", "amount": 26000.0, "unit": "g"})
    assert result["all-purpose flour"] is False

@pytest.mark.skipif(not db_available(), reason="PostgreSQL test DB not available")
def test_check_ingredient_availability_not_found():
    """
    Ingredient is not present in inventory.
    """
    result = check_ingredient_availability({"ingredient_name": "unobtainium", "amount": 1.0, "unit": "kg"})
    assert result["unobtainium"] is False

@pytest.mark.skipif(not db_available(), reason="PostgreSQL test DB not available")
def test_check_ingredient_availability_invalid_unit():
    """
    Ingredient is present but unit is invalid.
    Should raise ValueError.
    """
    with pytest.raises(ValueError):
        check_ingredient_availability({"ingredient_name": "all-purpose flour", "amount": 100.0, "unit": "invalidunit"})

@pytest.mark.skipif(not db_available(), reason="PostgreSQL test DB not available")
def test_check_ingredient_availability_compatible_units():
    """
    Ingredient is present in inventory in kg, request is in g (or vice versa).
    Assumes 'all-purpose flour' exists in DB with at least 0.5 kg available.
    """
    result = check_ingredient_availability({"ingredient_name": "all-purpose flour", "amount": 500.0, "unit": "g"})
    assert result["all-purpose flour"] is True

@pytest.mark.skipif(not db_available(), reason="PostgreSQL test DB not available")
def test_check_ingredient_availability_real_db():
    """
    Uses the real database and checks the result of check_ingredient_availability
    for all-purpose flour, 200g. Logs the result and asserts correct structure.
    """
    input_data = {"ingredient_name": "all-purpose flour", "amount": 200.0, "unit": "g"}
    result = check_ingredient_availability(input_data)
    logger.info("test_check_ingredient_availability_real_db result: %s", result)
    assert isinstance(result, dict)
    assert "all-purpose flour" in result
    assert isinstance(result["all-purpose flour"], bool)

# Remove test_get_ingredient_real_db (not implemented) 