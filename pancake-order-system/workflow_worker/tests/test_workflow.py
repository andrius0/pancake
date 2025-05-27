# Placeholder for workflow_worker unit tests 

import pytest
from temporalio.testing import WorkflowEnvironment
from shared.interface import Ingredients, IngredientItem, InventoryResponse
from temporalio import workflow
from unittest.mock import AsyncMock
from pancake_workflow import PancakeOrderWorkflow

@pytest.mark.asyncio
async def test_workflow_inventory_make(monkeypatch):
    # Mock analyze_order_activity to return Ingredients
    mock_ingredients = Ingredients(ingredients=[
        IngredientItem(ingredient_name="flour", amount=200, unit="g"),
        IngredientItem(ingredient_name="milk", amount=300, unit="ml")
    ])
    # Mock inventory_check to return InventoryResponse
    mock_inventory_response = InventoryResponse(
        decision="make",
        available_ingredients=["flour", "milk"],
        missing_ingredients=[]
    )
    async def mock_execute_activity(activity, *args, **kwargs):
        if activity == "analyze_order_activity":
            return mock_ingredients
        elif activity == "inventory_check":
            return mock_inventory_response
        else:
            raise Exception("Unknown activity")
    monkeypatch.setattr(workflow, "execute_activity", mock_execute_activity)
    wf = PancakeOrderWorkflow()
    result = await wf.run("order1", {"customer_order": "pancakes with milk and flour"})
    assert result == mock_inventory_response.dict()

@pytest.mark.asyncio
async def test_workflow_inventory_error(monkeypatch):
    # Mock analyze_order_activity to return Ingredients
    mock_ingredients = Ingredients(ingredients=[
        IngredientItem(ingredient_name="flour", amount=200, unit="g"),
        IngredientItem(ingredient_name="milk", amount=300, unit="ml")
    ])
    # Mock inventory_check to return error string
    mock_error = "Inventory check error"
    async def mock_execute_activity(activity, *args, **kwargs):
        if activity == "analyze_order_activity":
            return mock_ingredients
        elif activity == "inventory_check":
            return mock_error
        else:
            raise Exception("Unknown activity")
    monkeypatch.setattr(workflow, "execute_activity", mock_execute_activity)
    wf = PancakeOrderWorkflow()
    result = await wf.run("order1", {"customer_order": "pancakes with milk and flour"})
    assert result == {"status": "error", "reason": mock_error} 