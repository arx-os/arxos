"""
Real-time WebSocket Router
Handles WebSocket connections, real-time updates, and collaborative editing
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime

from arx_svg_parser.services.realtime_service import realtime_service, LockType
from arx_svg_parser.services.cache_service import cache_service
from arx_svg_parser.utils.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/realtime", tags=["realtime"])

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    try:
        # Get user information (you might want to validate the user_id)
        username = f"User_{user_id}"  # In production, get from database
        
        # Connect to real-time service
        await realtime_service.websocket_manager.connect(websocket, user_id, username)
        active_connections[user_id] = websocket
        
        logger.info(f"WebSocket connected: {user_id}")
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Main message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle the message
                await realtime_service.handle_websocket_message(user_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        if user_id in active_connections:
            del active_connections[user_id]
        
        await realtime_service.websocket_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected: {user_id}")

@router.post("/join-room")
async def join_room(user_id: str, room_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Join a room (floor, building, etc.)"""
    try:
        if user_id in active_connections:
            await realtime_service.websocket_manager.join_room(user_id, room_id)
            
            # Preload floor data when joining
            await cache_service.preload_floor(room_id)
            
            return JSONResponse({
                "success": True,
                "message": f"Joined room: {room_id}",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            raise HTTPException(status_code=400, detail="User not connected via WebSocket")
    
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        raise HTTPException(status_code=500, detail="Failed to join room")

@router.post("/leave-room")
async def leave_room(user_id: str, room_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Leave a room"""
    try:
        if user_id in active_connections:
            await realtime_service.websocket_manager.leave_room(user_id, room_id)
            
            return JSONResponse({
                "success": True,
                "message": f"Left room: {room_id}",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            raise HTTPException(status_code=400, detail="User not connected via WebSocket")
    
    except Exception as e:
        logger.error(f"Error leaving room: {e}")
        raise HTTPException(status_code=500, detail="Failed to leave room")

@router.post("/acquire-lock")
async def acquire_lock(
    user_id: str,
    lock_type: str,
    resource_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Acquire a collaborative editing lock"""
    try:
        if user_id not in active_connections:
            raise HTTPException(status_code=400, detail="User not connected via WebSocket")
        
        # Validate lock type
        try:
            lock_type_enum = LockType(lock_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid lock type: {lock_type}")
        
        username = realtime_service.websocket_manager.user_presence.get(
            user_id, 
            type('UserPresence', (), {'username': f'User_{user_id}'})()
        ).username
        
        success, result = await realtime_service.collaborative_editing.acquire_lock(
            user_id, username, lock_type_enum, resource_id, metadata or {}
        )
        
        return JSONResponse({
            "success": success,
            "lock_id": result if success else None,
            "message": result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acquiring lock: {e}")
        raise HTTPException(status_code=500, detail="Failed to acquire lock")

@router.post("/release-lock")
async def release_lock(
    user_id: str,
    lock_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Release a collaborative editing lock"""
    try:
        if user_id not in active_connections:
            raise HTTPException(status_code=400, detail="User not connected via WebSocket")
        
        success = await realtime_service.collaborative_editing.release_lock(lock_id, user_id)
        
        return JSONResponse({
            "success": success,
            "message": "Lock released" if success else "Failed to release lock",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error releasing lock: {e}")
        raise HTTPException(status_code=500, detail="Failed to release lock")

@router.get("/room-users/{room_id}")
async def get_room_users(room_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get all users currently in a room"""
    try:
        room_users = []
        
        if room_id in realtime_service.websocket_manager.room_connections:
            for user_id in realtime_service.websocket_manager.room_connections[room_id]:
                if user_id in realtime_service.websocket_manager.user_presence:
                    presence = realtime_service.websocket_manager.user_presence[user_id]
                    room_users.append({
                        "user_id": presence.user_id,
                        "username": presence.username,
                        "current_action": presence.current_action,
                        "cursor_position": presence.cursor_position,
                        "last_seen": presence.last_seen.isoformat(),
                        "is_active": presence.is_active
                    })
        
        return JSONResponse({
            "room_id": room_id,
            "users": room_users,
            "count": len(room_users),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting room users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room users")

@router.get("/active-locks/{resource_id}")
async def get_active_locks(resource_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get all active locks for a resource"""
    try:
        active_locks = []
        
        for lock in realtime_service.websocket_manager.editing_locks.values():
            if lock.resource_id == resource_id and datetime.utcnow() < lock.expires_at:
                active_locks.append({
                    "lock_id": lock.lock_id,
                    "lock_type": lock.lock_type.value,
                    "user_id": lock.user_id,
                    "username": lock.username,
                    "acquired_at": lock.acquired_at.isoformat(),
                    "expires_at": lock.expires_at.isoformat(),
                    "metadata": lock.metadata
                })
        
        return JSONResponse({
            "resource_id": resource_id,
            "locks": active_locks,
            "count": len(active_locks),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting active locks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active locks")

@router.get("/user-presence/{user_id}")
async def get_user_presence(user_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get user presence information"""
    try:
        if user_id in realtime_service.websocket_manager.user_presence:
            presence = realtime_service.websocket_manager.user_presence[user_id]
            return JSONResponse({
                "user_id": presence.user_id,
                "username": presence.username,
                "floor_id": presence.floor_id,
                "building_id": presence.building_id,
                "current_action": presence.current_action,
                "cursor_position": presence.cursor_position,
                "last_seen": presence.last_seen.isoformat(),
                "is_active": presence.is_active,
                "metadata": presence.metadata,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            raise HTTPException(status_code=404, detail="User not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user presence: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user presence")

@router.post("/update-presence")
async def update_presence(
    user_id: str,
    floor_id: Optional[str] = None,
    current_action: Optional[str] = None,
    cursor_position: Optional[List[float]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Update user presence information"""
    try:
        if user_id not in active_connections:
            raise HTTPException(status_code=400, detail="User not connected via WebSocket")
        
        message = {
            "type": "update_presence",
            "floor_id": floor_id,
            "current_action": current_action,
            "cursor_position": cursor_position,
            "metadata": metadata or {}
        }
        
        await realtime_service.handle_websocket_message(user_id, message)
        
        return JSONResponse({
            "success": True,
            "message": "Presence updated",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating presence: {e}")
        raise HTTPException(status_code=500, detail="Failed to update presence")

@router.get("/cache-stats")
async def get_cache_stats(current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get cache statistics"""
    try:
        stats = await cache_service.get_stats()
        return JSONResponse({
            "cache_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")

@router.post("/preload-floor")
async def preload_floor_data(
    floor_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Manually trigger floor data preloading"""
    try:
        await cache_service.preload_floor(floor_id)
        
        return JSONResponse({
            "success": True,
            "message": f"Floor data preloading initiated for: {floor_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error preloading floor data: {e}")
        raise HTTPException(status_code=500, detail="Failed to preload floor data")

@router.post("/invalidate-floor-cache")
async def invalidate_floor_cache(
    floor_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Invalidate all cache entries for a floor"""
    try:
        count = await cache_service.invalidate_floor(floor_id)
        
        return JSONResponse({
            "success": True,
            "message": f"Invalidated {count} cache entries for floor: {floor_id}",
            "count": count,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error invalidating floor cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate floor cache")

@router.get("/connection-status")
async def get_connection_status(current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get real-time service connection status"""
    try:
        return JSONResponse({
            "websocket_connections": len(active_connections),
            "total_users": len(realtime_service.websocket_manager.user_presence),
            "active_rooms": len(realtime_service.websocket_manager.room_connections),
            "active_locks": len(realtime_service.websocket_manager.editing_locks),
            "active_conflicts": len(realtime_service.websocket_manager.conflicts),
            "cache_connected": cache_service.cache_manager.redis_client is not None,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connection status")

@router.post("/broadcast")
async def broadcast_message(
    room_id: str,
    message: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Broadcast a message to all users in a room"""
    try:
        await realtime_service.websocket_manager.broadcast_to_room(room_id, {
            "type": "broadcast",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return JSONResponse({
            "success": True,
            "message": f"Message broadcasted to room: {room_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")

@router.post("/resolve-conflict")
async def resolve_conflict(
    conflict_id: str,
    resolution: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Resolve a conflict"""
    try:
        user_id = current_user.get("user_id") if current_user else "system"
        success = await realtime_service.conflict_resolution.resolve_conflict(conflict_id, resolution, user_id)
        
        return JSONResponse({
            "success": success,
            "message": "Conflict resolved" if success else "Failed to resolve conflict",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve conflict") 