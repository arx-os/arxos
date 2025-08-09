# SVGX Engine UI Event API Examples

## Overview
This guide provides example code and usage patterns for integrating the SVGX Engine UI event system with Web IDEs, CLI tools, and other clients. It covers both REST and WebSocket endpoints, event formats, and feedback handling.

---

## 1. WebSocket Integration (Web IDE, Real-Time)

### a. Handshake
Send immediately after connecting:
```json
{
  "auth_token": "optional",
  "session_id": "web-ide-123",
  "canvas_id": "building789"
}
```

### b. Sending Events
Example (selection):
```json
{
  "event_type": "selection",
  "payload": {
    "selection_mode": "single",
    "selected_ids": ["obj001"]
  }
}
```

### c. Receiving Feedback
Example:
```json
{
  "status": "success",
  "event_type": "selection",
  "feedback": {
    "status": "updated",
    "canvas_id": "building789",
    "selected_ids": ["obj001"]
  }
}
```

### d. JavaScript Example (Web IDE)
```js
const ws = new WebSocket("ws://localhost:8000/runtime/events");
ws.onopen = () => {
  ws.send(JSON.stringify({
    session_id: "web-ide-123",
    canvas_id: "building789"
  }));
};
ws.onmessage = (msg) => {
  const data = JSON.parse(msg.data);
  console.log("Feedback:", data);
};
// Send a selection event
ws.send(JSON.stringify({
  event_type: "selection",
  payload: {
    selection_mode: "single",
    selected_ids: ["obj001"]
  }
}));
```

---

## 2. REST API Integration (CLI, Batch)

### a. Endpoint
`POST /runtime/ui-event/`

### b. Request Example
```json
{
  "event_type": "editing",
  "timestamp": "2025-07-21T14:25:00Z",
  "session_id": "cli-789",
  "user_id": "user456",
  "canvas_id": "building789",
  "payload": {
    "target_id": "obj123",
    "edit_type": "move",
    "before": { "position": {"x": 100, "y": 200} },
    "after": { "position": {"x": 120, "y": 250} }
  }
}
```

### c. Response Example
```json
{
  "status": "success",
  "updated_state": {
    "canvas_id": "building789",
    "selection_state": ["obj001"],
    "edit_history": [ ... ]
  },
  "message": "Edit applied successfully."
}
```

### d. Python CLI Example
```python
import requests
import json

event = {
    "event_type": "selection",
    "timestamp": "2025-07-21T14:25:00Z",
    "session_id": "cli-789",
    "user_id": "user456",
    "canvas_id": "building789",
    "payload": {
        "selection_mode": "single",
        "selected_ids": ["obj001"]
    }
}
resp = requests.post("http://localhost:8000/runtime/ui-event/", json=event)
print(resp.json())
```

---

## 3. Event and Feedback Formats

### a. Event (Generic)
```json
{
  "event_type": "...",
  "timestamp": "...",
  "session_id": "...",
  "user_id": "...",
  "canvas_id": "...",
  "payload": { ... }
}
```

### b. Feedback (Generic)
```json
{
  "status": "success" | "error",
  "event_type": "...",
  "feedback": { ... },
  "message": "..."
}
```

---

## 4. Integration Tips
- Always send handshake first on WebSocket.
- Attach session_id and canvas_id to all events.
- Handle error feedback and display user-friendly messages.
- Use REST for batch/CLI, WebSocket for real-time/interactive.
- See OpenAPI docs at `/docs` for full schema and endpoint details.

---

## 5. Further Reading
- [SVGX Engine API Reference](../svgx_engine/services/api_interface.py)
- [UI Event Schemas](../svgx_engine/runtime/behavior/ui_event_schemas.py)
- [WebSocket Interface](../svgx_engine/services/websocket_interface.py)

---

## 6. Navigation and Annotation Event Examples

### a. Navigation Event (WebSocket/REST)
**Send:**
```json
{
  "event_type": "navigation",
  "session_id": "web-ide-123",
  "canvas_id": "building789",
  "payload": {
    "action": "zoom",
    "zoom_level": 2.0
  }
}
```
**Feedback:**
```json
{
  "status": "success",
  "event_type": "navigation",
  "feedback": {
    "status": "navigation_updated",
    "canvas_id": "building789",
    "navigation_state": {
      "zoom_level": 2.0
    }
  }
}
```

### b. Annotation Event (WebSocket/REST)
**Send:**
```json
{
  "event_type": "annotation",
  "session_id": "web-ide-123",
  "canvas_id": "building789",
  "payload": {
    "target_id": "obj456",
    "annotation_type": "note",
    "content": "Check this fixture.",
    "location": {"x": 120, "y": 340},
    "tag": ["QA", "voltage"]
  }
}
```
**Feedback:**
```json
{
  "status": "success",
  "event_type": "annotation",
  "feedback": {
    "status": "annotation_added",
    "canvas_id": "building789",
    "target_id": "obj456",
    "annotations": [
      {
        "type": "note",
        "content": "Check this fixture.",
        "location": {"x": 120, "y": 340},
        "media": null,
        "tag": ["QA", "voltage"],
        "timestamp": "2025-07-21T14:30:00Z",
        "user_id": "user456"
      }
    ]
  }
}
```

---
