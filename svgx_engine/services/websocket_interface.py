from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from svgx_engine.runtime.advanced_behavior_engine import AdvancedBehaviorEngine
from svgx_engine.services.auth_middleware import authenticate_websocket, User
from svgx_engine.services.rate_limiter import websocket_rate_limit_middleware
import logging
from collections import defaultdict, Dict

router = APIRouter()
engine = AdvancedBehaviorEngine()
logger = logging.getLogger(__name__)

# Registry of connected clients per canvas for push updates
ws_clients: Dict[str, set] = defaultdict(set)  # canvas_id -> set of WebSocket

@router.websocket("/runtime/events")
async def websocket_event_handler(ws: WebSocket):
    """
    WebSocket endpoint for real-time UI events and collaboration.
    
    Handshake:
    { "session_id": "...", "canvas_id": "...", "auth_token": "..." }
    
    Supported events:
    { "event_type": "selection", "payload": { ... } }
    { "event_type": "editing", "payload": { ... } }
    { "event_type": "navigation", "payload": { ... } }
    { "event_type": "annotation", "payload": { ... } }
    { "event_type": "undo", "canvas_id": "..." }
    { "event_type": "redo", "canvas_id": "..." }
    { "event_type": "annotation_update", "canvas_id": "...", "target_id": "...", "annotation_index": 0, "new_data": { ... } }
    { "event_type": "annotation_delete", "canvas_id": "...", "target_id": "...", "annotation_index": 0 }
    { "event_type": "lock", "canvas_id": "...", "object_id": "...", "session_id": "...", "user_id": "..." }
    { "event_type": "unlock", "canvas_id": "...", "object_id": "...", "session_id": "..." }
    { "event_type": "lock_status", "canvas_id": "...", "object_id": "..." }
    { "event_type": "release_session_locks", "session_id": "..." }
    """
    await ws.accept()
    session_ctx = {}
    canvas_id = None
    session_id = None
    current_user = None
    
    try:
        # Handshake
        handshake_data = await ws.receive_json()
        session_ctx = {
            "session_id": handshake_data.get("session_id"),
            "canvas_id": handshake_data.get("canvas_id"),
            "auth_token": handshake_data.get("auth_token")
        }
        session_id = session_ctx["session_id"]
        canvas_id = session_ctx["canvas_id"]
        
        if not session_ctx["session_id"] or not session_ctx["canvas_id"]:
            await ws.send_json({"status": "error", "message": "Missing session_id or canvas_id"})
            return
        
        # Authenticate user if token provided
        if session_ctx.get("auth_token"):
            current_user = await authenticate_websocket(ws)
            if current_user:
                # Store user context in websocket object
                ws.user_id = current_user.user_id
                ws.session_id = session_id
                logger.info(f"WebSocket authenticated: {current_user.username} ({current_user.role})")
            else:
                logger.warning(f"WebSocket authentication failed for session {session_id}")
                await ws.send_json({"status": "error", "message": "Authentication failed"})
                return
        else:
            # Anonymous connection (limited functionality)
            ws.user_id = "anonymous"
            ws.session_id = session_id
            logger.info(f"WebSocket anonymous connection: {session_id}")
        
        logger.info(f"WebSocket handshake: {session_ctx}")
        await ws.send_json({"status": "handshake_ack", "session": session_ctx})
        
        # Add client to canvas registry
        if canvas_id:
            ws_clients[canvas_id].add(ws)
        
        while True:
            data = await ws.receive_json()
            if "event_type" not in data:
                await ws.send_json({"status": "error", "message": "Missing event_type"})
                continue
            
            # Apply rate limiting to WebSocket messages
            rate_limit_allowed = await websocket_rate_limit_middleware(ws, message_count=1)
            if not rate_limit_allowed:
                continue  # Rate limit exceeded, message already sent
            
            try:
                # Attach session/canvas context if not present
                data.setdefault("session_id", session_ctx.get("session_id"))
                data.setdefault("canvas_id", session_ctx.get("canvas_id"))
                data.setdefault("user_id", current_user.user_id if current_user else "anonymous")
                
                canvas_id = data["canvas_id"]
                ws_clients[canvas_id].add(ws)
                
                # Handle specific event types
                if data["event_type"] == "undo":
                    feedback = engine.perform_undo(data["canvas_id"])
                    await ws.send_json({"status": "success", "event_type": "undo", "feedback": feedback})
                    continue
                if data["event_type"] == "redo":
                    feedback = engine.perform_redo(data["canvas_id"])
                    await ws.send_json({"status": "success", "event_type": "redo", "feedback": feedback})
                    continue
                if data["event_type"] == "annotation_update":
                    feedback = engine.update_annotation(
                        data["canvas_id"], 
                        data["target_id"], 
                        data["annotation_index"], 
                        data["new_data"]
                    )
                    await ws.send_json({"status": "success", "event_type": "annotation_update", "feedback": feedback})
                    continue
                if data["event_type"] == "annotation_delete":
                    feedback = engine.delete_annotation(
                        data["canvas_id"], 
                        data["target_id"], 
                        data["annotation_index"]
                    )
                    await ws.send_json({"status": "success", "event_type": "annotation_delete", "feedback": feedback})
                    continue
                if data["event_type"] == "lock":
                    feedback = engine.lock_object(canvas_id, data["object_id"], data["session_id"], data["user_id"])
                    # Broadcast lock status to all clients on this canvas
                    for client in ws_clients[canvas_id]:
                        await client.send_json({"status": "success", "event_type": "lock_status", "feedback": feedback})
                    continue
                if data["event_type"] == "unlock":
                    feedback = engine.unlock_object(canvas_id, data["object_id"], data["session_id"])
                    for client in ws_clients[canvas_id]:
                        await client.send_json({"status": "success", "event_type": "lock_status", "feedback": feedback})
                    continue
                if data["event_type"] == "lock_status":
                    feedback = engine.get_lock_status(canvas_id, data["object_id"])
                    await ws.send_json({"status": "success", "event_type": "lock_status", "feedback": feedback})
                    continue
                if data["event_type"] == "release_session_locks":
                    feedback = engine.release_session_locks(data["session_id"])
                    await ws.send_json({"status": "success", "event_type": "release_session_locks", "feedback": feedback})
                    continue
                
                # Handle general UI events
                response = engine.handle_ui_event(data)
                await ws.send_json({
                    "status": "success",
                    "event_type": data["event_type"],
                    "feedback": response
                })
            except Exception as e:
                logger.error(f"WebSocket event error: {e}")
                await ws.send_json({
                    "status": "error",
                    "message": str(e)
                })
    except WebSocketDisconnect:
        # Auto-release all locks for this session on disconnect
        if session_id:
            try:
                release_result = engine.release_session_locks(session_id)
                logger.info(f"Auto-released locks for disconnected session {session_id}: {release_result}")
            except Exception as e:
                logger.error(f"Error releasing locks for session {session_id}: {e}")
        
        # Remove client from canvas registry
        if canvas_id and ws in ws_clients[canvas_id]:
            ws_clients[canvas_id].remove(ws)
        
        logger.info(f"WebSocket disconnected: {session_ctx}")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
        await ws.send_json({
            "status": "error",
            "message": str(e)
        }) 