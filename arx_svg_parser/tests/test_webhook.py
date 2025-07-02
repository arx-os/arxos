"""
Stub for unit tests for webhook.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.routers import webhook

def test_notify_webhooks():
    # TODO: Implement real test
    assert webhook.notify_webhooks('event', {}, []) == [] 