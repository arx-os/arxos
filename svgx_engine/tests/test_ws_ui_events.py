import pytest
import asyncio
import json
import websockets
from datetime import datetime

WS_URL = "ws://localhost:8000/runtime/events"


@pytest.mark.asyncio
async def test_ws_handshake_and_selection():
    async with websockets.connect(WS_URL) as ws:
        # Handshake
        await ws.send(
            json.dumps({"session_id": "ws-test-session", "canvas_id": "ws-canvas-1"})
        )
        handshake_ack = json.loads(await ws.recv())
        assert handshake_ack["status"] == "handshake_ack"
        # Send selection event
        await ws.send(
            json.dumps(
                {
                    "event_type": "selection",
                    "payload": {"selection_mode": "single", "selected_ids": ["obj001"]},
                }
            )
        )
        feedback = json.loads(await ws.recv())
        assert feedback["status"] == "success"
        assert feedback["event_type"] == "selection"
        assert feedback["feedback"]["selected_ids"] == ["obj001"]


@pytest.mark.asyncio
async def test_ws_invalid_event_type():
    async with websockets.connect(WS_URL) as ws:
        await ws.send(
            json.dumps({"session_id": "ws-test-session", "canvas_id": "ws-canvas-1"})
        )
        await ws.recv()  # handshake ack
        await ws.send(json.dumps({"event_type": "invalid_type", "payload": {}}))
        feedback = json.loads(await ws.recv())
        assert feedback["status"] == "error"


@pytest.mark.asyncio
async def test_ws_disconnect_and_reconnect():
    # Connect, handshake, disconnect, reconnect
    async with websockets.connect(WS_URL) as ws:
        await ws.send(
            json.dumps({"session_id": "ws-test-session", "canvas_id": "ws-canvas-1"})
        )
        handshake_ack = json.loads(await ws.recv())
        assert handshake_ack["status"] == "handshake_ack"
    # Reconnect
    async with websockets.connect(WS_URL) as ws2:
        await ws2.send(
            json.dumps({"session_id": "ws-test-session", "canvas_id": "ws-canvas-1"})
        )
        handshake_ack2 = json.loads(await ws2.recv())
        assert handshake_ack2["status"] == "handshake_ack"
