import pytest
from fastapi.testclient import TestClient
from svgx_engine.services.api_interface import app
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def base_event():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": "test-session",
        "user_id": "test-user",
        "canvas_id": "test-canvas"
    }

def test_selection_event_success(base_event):
    event = {
        **base_event,
        "event_type": "selection",
        "payload": {
            "selection_mode": "single",
            "selected_ids": ["obj001"]
        }
    }
    resp = client.post("/runtime/ui-event/", json=event)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "updated_state" in data
    assert data["updated_state"]["selection_state"] == ["obj001"]

def test_editing_event_success(base_event):
    event = {
        **base_event,
        "event_type": "editing",
        "payload": {
            "target_id": "obj001",
            "edit_type": "move",
            "before": {"position": {"x": 0, "y": 0}},
            "after": {"position": {"x": 10, "y": 20}}
        }
    }
    resp = client.post("/runtime/ui-event/", json=event)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "updated_state" in data
    assert "edit_history" in data["updated_state"]
    assert data["updated_state"]["edit_history"][-1]["edit_type"] == "move"

def test_navigation_event_success(base_event):
    event = {
        **base_event,
        "event_type": "navigation",
        "payload": {
            "action": "zoom",
            "zoom_level": 2.0
        }
    }
    resp = client.post("/runtime/ui-event/", json=event)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

def test_annotation_event_success(base_event):
    event = {
        **base_event,
        "event_type": "annotation",
        "payload": {
            "target_id": "obj002",
            "annotation_type": "note",
            "content": "Test annotation.",
            "location": {"x": 1, "y": 2},
            "tag": ["test"]
        }
    }
    resp = client.post("/runtime/ui-event/", json=event)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"

def test_invalid_event_type(base_event):
    event = {
        **base_event,
        "event_type": "invalid_type",
        "payload": {}
    }
    resp = client.post("/runtime/ui-event/", json=event)
    assert resp.status_code == 422 or resp.json()["status"] == "error"
    data = resp.json()
    assert data["status"] == "error"
    assert "INVALID_PAYLOAD" in data.get("error_code", "")

def test_missing_payload(base_event):
    event = {
        **base_event,
        "event_type": "selection"
        # missing payload
    }
    resp = client.post("/runtime/ui-event/", json=event)
    assert resp.status_code == 422 or resp.json()["status"] == "error"
    data = resp.json()
    assert data["status"] == "error"
    assert "INVALID_PAYLOAD" in data.get("error_code", "") 