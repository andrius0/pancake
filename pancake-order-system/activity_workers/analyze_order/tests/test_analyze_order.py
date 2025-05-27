# Placeholder for analyze_order activity unit tests 

import pytest
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from analyze_order import analyze_order

@pytest.mark.asyncio
async def test_analyze_order_basic():
    customer_order = "Two servings of classic pancakes with extra syrup."
    result = await analyze_order(customer_order)
    print("\nResult for basic order:", result)

@pytest.mark.asyncio
async def test_analyze_order_custom():
    customer_order = "Gluten-free banana pancakes with almond milk, no sugar."
    result = await analyze_order(customer_order)
    print("\nResult for custom order:", result)

@pytest.mark.asyncio
async def test_analyze_order_edge_case():
    customer_order = "Pancakes for 10 people, vegan, with blueberries and maple syrup."
    result = await analyze_order(customer_order)
    print("\nResult for edge case order:", result) 