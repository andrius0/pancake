from typing import Dict, List, Tuple
import re
from sqlalchemy import create_engine, text, Connection
from langchain_core.tools import Tool
from shared.interface import InventoryItem, Ingredient
import logging
import inflect
import os

p = inflect.engine()

def parse_amount(amount_str: str) -> Tuple[float, str]:
    """Parse amount string into numeric value and unit."""
    match = re.match(r"([\d.]+)\s*(\w+)", amount_str.strip())
    if not match:
        raise ValueError(f"Invalid amount format: {amount_str}")
    value, unit = match.groups()
    return float(value), unit.lower()

def is_compatible_units(required_unit: str, available_unit: str) -> bool:
    """Check if units are compatible for comparison. Only mass and volume units are allowed."""
    mass_units = {'kg', 'g'}
    volume_units = {'l', 'ml', 'liters', 'liter'}
    
    required_unit = required_unit.lower()
    available_unit = available_unit.lower()
    
    if required_unit == available_unit:
        return True
    if required_unit in mass_units and available_unit in mass_units:
        return True
    if required_unit in volume_units and available_unit in volume_units:
        return True
    return False

def convert_to_base_unit(value: float, unit: str) -> Tuple[float, str]:
    """
    Convert value to base unit (kg for mass, L for volume).
    Returns tuple of (converted_value, base_unit)
    Only mass and volume units are allowed.
    """
    unit = unit.lower()
    
    # Mass conversions
    if unit in {'kg', 'kilograms', 'kilogram'}:
        return value, 'kg'
    elif unit in {'g', 'grams', 'gram'}:
        return value / 1000, 'kg'
    
    # Volume conversions
    elif unit in {'l', 'liter', 'liters'}:
        return value, 'l'
    elif unit in {'ml', 'milliliter', 'milliliters'}:
        return value / 1000, 'l'
    
    # Raise error for non-standard units
    raise ValueError(f"Unit '{unit}' is not a supported standard unit (g, kg, l, ml)")

def get_db_connection():
    db_url = os.environ.get(
        "INVENTORY_DB_URL",
        "postgresql://postgres:postgres@localhost:5432/restaurant"
    )
    logger = logging.getLogger("db_tools")
    logger.info(f"Connecting to DB with URL: {db_url}")
    try:
        engine = create_engine(db_url)
        # Try to connect to test if connection is successful
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    return engine

def normalize_ingredient_name(name: str) -> str:
    # Try singular form using inflect
    singular = p.singular_noun(name)
    if singular:
        return singular
    return name

def query_inventory_for_name(conn, name: str):
    query = text("""
        SELECT available_amount, unit
        FROM kitchen_inventory
        WHERE ingredient = :name
    """)
    return conn.execute(query, {"name": name}).fetchone()

def check_ingredient_availability(ingredient: dict) -> Dict[str, bool]:
    """
    Check if the requested ingredient is available in sufficient quantity.
    Accepts a raw dict (JSON object) with keys: ingredient_name, amount, unit.
    Only standard units (g, kg, l, ml) are allowed.
    Returns a dict {ingredient_name: True/False}
    """
    logger = logging.getLogger("check_ingredient_availability")
    logger.info(f"Checking availability for ingredient: {ingredient}")
    name = ingredient["ingredient_name"].lower()
    # Ensure required_qty is a float, even if passed as a string
    required_qty = float(ingredient["amount"])
    required_unit = ingredient["unit"].lower()
    if required_unit not in {'g', 'kg', 'l', 'ml'}:
        logger.warning(f"Unit '{required_unit}' is not allowed. Only standard units (g, kg, l, ml) are permitted.")
        raise ValueError(f"Unit '{required_unit}' is not allowed. Only standard units (g, kg, l, ml) are permitted.")
    engine = get_db_connection()
    conn = engine.connect()
    try:
        # Try original name first
        logger.info(f"Executing DB query for ingredient: {name}")
        result = query_inventory_for_name(conn, name)
        # If not found, try singular form
        if result is None:
            normalized_name = normalize_ingredient_name(name)
            if normalized_name != name:
                logger.info(f"Ingredient '{name}' not found, trying normalized name '{normalized_name}'")
                result = query_inventory_for_name(conn, normalized_name)
        if result is None:
            logger.info(f"Ingredient '{name}' (or its singular form) not found in inventory.")
            return {name: False}
        available_value = result[0]  # float
        available_unit = result[1]   # str
        logger.info(f"Found available amount in DB: {available_value} {available_unit}")
        if available_unit not in {'g', 'kg', 'l', 'ml'}:
            logger.warning(f"Unit '{available_unit}' in inventory is not allowed. Only standard units (g, kg, l, ml) are permitted.")
            raise ValueError(f"Unit '{available_unit}' in inventory is not allowed. Only standard units (g, kg, l, ml) are permitted.")
        if is_compatible_units(required_unit, available_unit):
            # Convert both to base units for comparison
            available_base_value, base_unit = convert_to_base_unit(available_value, available_unit)
            required_base_value, _ = convert_to_base_unit(float(required_qty), required_unit)
            logger.info(f"Converted available: {available_base_value} {base_unit}, required: {required_base_value} {base_unit}")
            result_bool = available_base_value >= required_base_value
            logger.info(f"Availability result for '{name}': {result_bool}")
            return {name: result_bool}
        else:
            logger.info(f"Units are not compatible: required '{required_unit}', available '{available_unit}'")
            return {name: False}
    except Exception as e:
        logger.error(f"Database or logic error: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_current_inventory(_=None) -> List[InventoryItem]:
    """
    Retrieve the current inventory status for all items in the kitchen.
    This function queries the database and returns a list of InventoryItem objects,
    each containing the ingredient name, its available amount (with units), and unit.
    Useful for getting a complete snapshot of what is currently in stock.
    Returns:
        List[InventoryItem]: A list of all inventory items with their available amounts and units.
    """
    engine = get_db_connection()
    conn = engine.connect()
    try:
        query = text("""
            SELECT ingredient, available_amount, unit
            FROM kitchen_inventory
        """)
        results = conn.execute(query).fetchall()
        inventory_items = [
            InventoryItem(
                ingredient=row[0],
                available_amount=row[1],
                unit=row[2]
            )
            for row in results
        ]
        return inventory_items
    except Exception as e:
        raise
    finally:
        conn.close()

# Define tools for the agent
check_ingredients_tool = Tool(
    name="check_ingredients",
    description="""Check if a specific ingredient is available in sufficient quantity. Each ingredient should be specified with ingredient_name, amount, and unit. Example: {\"ingredient_name\": \"flour\", \"amount\": 2.5, \"unit\": \"kg\"}""",
    func=check_ingredient_availability
)

get_inventory_tool = Tool(
    name="get_inventory",
    description="""Retrieve a complete list of all inventory items in the kitchen, including each ingredient's name and its available amount (with units). Use this tool to get a full snapshot of what is currently in stock.""",
    func=get_current_inventory
) 