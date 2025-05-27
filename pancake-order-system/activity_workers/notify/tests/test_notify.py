# Placeholder for notify activity unit tests 
import pytest
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared')))
from notify import notify_activity
from interface import NotifyRequest, NotifyResponse

@pytest.mark.asyncio
async def test_notify_activity_logs_and_returns_response(caplog):
    req = NotifyRequest(order_id="123", message="Order ready!")
    with caplog.at_level("INFO"):
        resp = await notify_activity(req)
    assert resp.status == "delivered"
    assert "Sending notification for order_id=123: Order ready!" in caplog.text 