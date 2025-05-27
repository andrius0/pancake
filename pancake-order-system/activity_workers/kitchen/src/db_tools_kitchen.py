from typing import Dict, List, Tuple
import re
from sqlalchemy import create_engine, text, Connection
from langchain_core.tools import Tool
from shared.interface import InventoryItem, Ingredient, IngredientItem
import logging
import inflect
import os
logger = logging.getLogger(__name__)

p = inflect.engine()

def parse_amount(amount_str: str) -> Tuple[float, str]:
    """Parse amount string into numeric value and unit."""
    logger.info(f"Parsing amount string: {amount_str}")
    match = re.match(r"([\d.]+)\s*(\w+)", amount_str.strip())
    if not match:
        logger.error(f"Invalid amount format: {amount_str}")
        raise ValueError(f"Invalid amount format: {amount_str}")
    value, unit = match.groups()
    logger.info(f"Parsed value: {value}, unit: {unit}")
    return float(value), unit.lower()

def is_compatible_units(required_unit: str, available_unit: str) -> bool:
    """Check if units are compatible for comparison. Only mass and volume units are allowed."""
    logger.info(f"Checking unit compatibility: required={required_unit}, available={available_unit}")
    mass_units = {'kg', 'g'}
    volume_units = {'l', 'ml', 'liters', 'liter'}
    
    required_unit = required_unit.lower()
    available_unit = available_unit.lower()
    
    if required_unit == available_unit:
        logger.info("Units are exactly the same.")
        return True
    if required_unit in mass_units and available_unit in mass_units:
        logger.info("Both units are mass units and compatible.")
        return True
    if required_unit in volume_units and available_unit in volume_units:
        logger.info("Both units are volume units and compatible.")
        return True
    logger.info("Units are not compatible.")
    return False

def convert_to_base_unit(value: float, unit: str) -> Tuple[float, str]:
    """
    Convert value to base unit (kg for mass, L for volume).
    Returns tuple of (converted_value, base_unit)
    Only mass and volume units are allowed.
    """
    logger.info(f"Converting value {value} {unit} to base unit.")
    unit = unit.lower()
    
    # Mass conversions
    if unit in {'kg', 'kilograms', 'kilogram'}:
        logger.info(f"No conversion needed for {unit}.")
        return value, 'kg'
    elif unit in {'g', 'grams', 'gram'}:
        logger.info(f"Converting {value}g to kg.")
        return value / 1000, 'kg'
    
    # Volume conversions
    elif unit in {'l', 'liter', 'liters'}:
        logger.info(f"No conversion needed for {unit}.")
        return value, 'l'
    elif unit in {'ml', 'milliliter', 'milliliters'}:
        logger.info(f"Converting {value}ml to l.")
        return value / 1000, 'l'
    
    # Raise error for non-standard units
    logger.error(f"Unit '{unit}' is not a supported standard unit (g, kg, l, ml)")
    raise ValueError(f"Unit '{unit}' is not a supported standard unit (g, kg, l, ml)")


def get_db_connection():
    """Create database connection using hardcoded credentials."""
    db_url = os.environ.get(
        "INVENTORY_DB_URL",
        "postgresql://postgres:postgres@localhost:5432/restaurant"
    )
    logger.info(f"Connecting to DB with URL: {db_url}")
    try:
        engine = create_engine(db_url)
        logger.info("Database engine created successfully.")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}", exc_info=True)
        raise

def normalize_ingredient_name(name: str) -> str:
    logger.info(f"Normalizing ingredient name: {name}")
    # Try singular form using inflect
    singular = p.singular_noun(name)
    if singular:
        logger.info(f"Normalized '{name}' to singular '{singular}'")
        return singular
    logger.info(f"No normalization needed for '{name}'")
    return name

def query_inventory_for_name(conn, name: str):
    logger.info(f"Querying inventory for ingredient name: {name}")
    query = text("""
        SELECT available_amount, unit
        FROM kitchen_inventory
        WHERE ingredient = :name
    """)
    result = conn.execute(query, {"name": name}).fetchone()
    logger.info(f"Query result for '{name}': {result}")
    return result

def check_ingredient_availability(ingredient: dict) -> Dict[str, bool]:
    """
    Check if the requested ingredient is available in sufficient quantity.
    Accepts a raw dict (JSON object) with keys: ingredient_name, amount, unit.
    Only standard units (g, kg, l, ml) are allowed.
    Returns a dict {ingredient_name: True/False}
    """
    logger.info(f"Checking availability for ingredient: {ingredient}")
    name = ingredient["ingredient_name"].lower()
    required_qty = ingredient["amount"]
    required_unit = ingredient["unit"].lower()
    if required_unit not in {'g', 'kg', 'l', 'ml'}:
        logger.warning(f"Unit '{required_unit}' is not allowed. Only standard units (g, kg, l, ml) are permitted.")
        raise ValueError(f"Unit '{required_unit}' is not allowed. Only standard units (g, kg, l, ml) are permitted.")
    engine = get_db_connection()
    logger.info("Acquired DB engine, connecting...")
    conn = engine.connect()
    logger.info("Database connection established.")
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
        logger.info("Closing database connection.")
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
    logger.info("Retrieving current inventory from database.")
    engine = get_db_connection()
    logger.info("Acquired DB engine, connecting...")
    conn = engine.connect()
    logger.info("Database connection established.")
    try:
        query = text("""
            SELECT ingredient, available_amount, unit
            FROM kitchen_inventory
        """)
        logger.info("Executing inventory query.")
        results = conn.execute(query).fetchall()
        logger.info(f"Inventory query returned {len(results)} rows.")
        inventory_items = [
            InventoryItem(
                ingredient=row[0],
                available_amount=row[1],
                unit=row[2]
            )
            for row in results
        ]
        logger.info(f"Returning {len(inventory_items)} inventory items.")
        return inventory_items
    except Exception as e:
        logger.error(f"Error retrieving inventory: {e}", exc_info=True)
        raise
    finally:
        logger.info("Closing database connection.")
        conn.close()

def subtract_ingredient_amount(ingredient_name: str, amount: float, unit: str) -> IngredientItem:
    """
    Subtract the given amount (in the given unit) from the available amount for the specified ingredient in the database.
    Raises ValueError if not enough is available or if units are incompatible.
    Updates the database with the new amount.
    Returns the updated IngredientItem object with the new amount.
    """
    logger.info(f"Subtracting {amount} {unit} from ingredient '{ingredient_name}' in inventory.")
    allowed_units = {'g', 'kg', 'l', 'ml'}
    unit = unit.lower()
    if unit not in allowed_units:
        logger.error(f"Unit '{unit}' is not allowed. Only standard units (g, kg, l, ml) are permitted.")
        raise ValueError(f"Unit '{unit}' is not allowed. Only standard units (g, kg, l, ml) are permitted.")
    engine = get_db_connection()
    logger.info("Acquired DB engine, connecting...")
    conn = engine.connect()
    logger.info("Database connection established.")
    try:
        query = text("""
            SELECT available_amount, unit
            FROM kitchen_inventory 
            WHERE ingredient = :name
        """)
        logger.info(f"Executing select query for '{ingredient_name}'.")
        result = conn.execute(query, {"name": ingredient_name}).fetchone()
        logger.info(f"Select query result: {result}")
        if result is None:
            logger.error(f"Ingredient '{ingredient_name}' not found in inventory.")
            raise ValueError(f"Ingredient '{ingredient_name}' not found in inventory.")
        available_value = result[0]  # float
        available_unit = result[1]   # str
        available_unit = available_unit.lower()
        if available_unit not in allowed_units:
            logger.error(f"Unit '{available_unit}' in inventory is not allowed. Only standard units (g, kg, l, ml) are permitted.")
            raise ValueError(f"Unit '{available_unit}' in inventory is not allowed. Only standard units (g, kg, l, ml) are permitted.")
        if not is_compatible_units(unit, available_unit):
            logger.error(f"Incompatible units: requested '{unit}', available '{available_unit}'")
            raise ValueError(f"Incompatible units: requested '{unit}', available '{available_unit}'")
        # Convert both to base units for comparison and subtraction
        available_base_value, base_unit = convert_to_base_unit(available_value, available_unit)
        subtract_base_value, _ = convert_to_base_unit(float(amount), unit)
        if subtract_base_value > available_base_value:
            logger.error(f"Not enough '{ingredient_name}' in inventory to subtract {amount} {unit}.")
            raise ValueError(f"Not enough '{ingredient_name}' in inventory to subtract {amount} {unit}.")
        new_base_value = available_base_value - subtract_base_value
        # Convert back to the original unit for storage
        if base_unit == 'kg' and available_unit == 'g':
            new_value = new_base_value * 1000
            new_unit = 'g'
        elif base_unit == 'kg':
            new_value = new_base_value
            new_unit = 'kg'
        elif base_unit == 'l' and available_unit == 'ml':
            new_value = new_base_value * 1000
            new_unit = 'ml'
        elif base_unit == 'l':
            new_value = new_base_value
            new_unit = 'l'
        else:
            logger.error(f"Unexpected base unit '{base_unit}' or available unit '{available_unit}'")
            raise ValueError(f"Unexpected base unit '{base_unit}' or available unit '{available_unit}'")
        update_query = text("""
            UPDATE kitchen_inventory
            SET available_amount = :new_amount
            WHERE ingredient = :name
        """)
        logger.info(f"Executing update query for '{ingredient_name}' with new amount {new_value} {new_unit}.")
        conn.execute(update_query, {"new_amount": new_value, "name": ingredient_name})
        conn.commit()
        logger.info(f"Updated '{ingredient_name}' in inventory to {new_value} {new_unit}.")
        return IngredientItem(ingredient_name=ingredient_name, amount=new_value, unit=new_unit)
    except Exception as e:
        logger.error(f"Error subtracting ingredient amount: {e}", exc_info=True)
        raise
    finally:
        logger.info("Closing database connection.")
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