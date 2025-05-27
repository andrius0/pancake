# Shared data models and interfaces (Pydantic models, etc.) 
from pydantic import BaseModel, Field
from typing import Optional
from temporalio import activity

class OrderRequest(BaseModel):
    order_id: str
    customer_order: str
    customer_name: str
    special_instructions: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: str
    workflow_id: str
    status: str
    message: str

class IngredientItem(BaseModel):
    ingredient_name: str
    amount: float
    unit: str

class Ingredients(BaseModel):
    ingredients: list[IngredientItem]

class InventoryResponse(BaseModel):
    decision: str  # 'make' or 'no make'
    available_ingredients: list[str]
    missing_ingredients: list[str]

class NotifyRequest(BaseModel):
    order_id: str
    message: str

class NotifyResponse(BaseModel):
    status: str
    detail: str 

class InventoryItem(BaseModel):
    """Model for inventory items."""
    ingredient: str
    available_amount: float
    unit: str

class Ingredient(BaseModel):
    """Model for storing ingredient details with standard units."""
    ingredient_name: str = Field(description="The name of the ingredient")
    amount: float = Field(description="The amount of the ingredient required, in standard units")
    unit: str = Field(description="The unit of the ingredient amount, e.g., 'g', 'ml', 'kg', 'l', etc.")    

@activity.defn(name="analyze_order")
async def analyze_order(order: str) -> Ingredients:
    raise NotImplementedError

@activity.defn(name="inventory_check")
async def inventory_check(order_id: str, ingredients: Ingredients) -> str:
    raise NotImplementedError

@activity.defn(name="notify")
async def notify(order_id: str, message: str) -> None:
    raise NotImplementedError

@activity.defn(name="execute_order")
async def execute_order(ingredients: Ingredients) -> Ingredients:
    raise NotImplementedError    
