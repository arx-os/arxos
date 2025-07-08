"""
Real-time Service for Multi-user Synchronization
Handles WebSocket connections, user presence, conflict resolution, and collaborative editing
"""

import asyncio
import json
import time
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LockType(Enum):
    """Types of collaborative editing locks"""
    FLOOR_EDIT = "floor_edit"
    OBJECT_EDIT = "object_edit"
    ROUTE_EDIT = "route_edit"
    GRID_CALIBRATION = "grid_calibration"
    ANALYTICS_VIEW = "analytics_view"

class ConflictSeverity(Enum):
    """Conflict severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class UserPresence:
    """User presence information"""
    user_id: str
    username: str
    floor_id: Optional[str] = None
    building_id: Optional[str] = None
    last_seen: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    current_action: Optional[str] = None
    cursor_position: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EditingLock:
    """Collaborative editing lock"""
    lock_id: str
    lock_type: LockType
    resource_id: str  # floor_id, object_id, etc.
    user_id: str
    username: str
    acquired_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conflict:
    """Conflict information"""
    conflict_id: str
    resource_id: str
    conflict_type: str
    severity: ConflictSeverity
    user_id_1: str
    user_id_2: str
    description: str
    created_at: datetime
    resolved: bool = False
    resolution: Optional[str] = None

class WebSocketManager:
    """Manages WebSocket connections and real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, Any] = {}  # user_id -> websocket
        self.room_connections: Dict[str, Set[str]] = {}  # room_id -> set of user_ids
        self.user_presence: Dict[str, UserPresence] = {}
        self.editing_locks: Dict[str, EditingLock] = {}
        self.conflicts: Dict[str, Conflict] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the WebSocket manager"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("WebSocket manager started")
    
    async def stop(self):
        """Stop the WebSocket manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        logger.info("WebSocket manager stopped")
    
    async def connect(self, websocket: Any, user_id: str, username: str):
        """Handle new WebSocket connection"""
        self.active_connections[user_id] = websocket
        self.user_presence[user_id] = UserPresence(
            user_id=user_id,
            username=username
        )
        
        # Notify other users about new connection
        await self.broadcast_user_joined(user_id, username)
        logger.info(f"User {username} ({user_id}) connected")
    
    async def disconnect(self, user_id: str):
        """Handle WebSocket disconnection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Release all locks held by this user
        await self.release_user_locks(user_id)
        
        # Remove from all rooms
        for room_id, users in self.room_connections.items():
            users.discard(user_id)
        
        # Update presence
        if user_id in self.user_presence:
            self.user_presence[user_id].is_active = False
            self.user_presence[user_id].last_seen = datetime.utcnow()
        
        # Notify other users about disconnection
        await self.broadcast_user_left(user_id)
        logger.info(f"User {user_id} disconnected")
    
    async def join_room(self, user_id: str, room_id: str):
        """Join a room (floor, building, etc.)"""
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        
        self.room_connections[room_id].add(user_id)
        
        if user_id in self.user_presence:
            self.user_presence[user_id].floor_id = room_id
        
        # Notify room about new user
        await self.broadcast_to_room(room_id, {
            "type": "user_joined_room",
            "user_id": user_id,
            "username": self.user_presence.get(user_id, UserPresence(user_id, "Unknown")).username,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send current room state to new user
        await self.send_room_state(user_id, room_id)
    
    async def leave_room(self, user_id: str, room_id: str):
        """Leave a room"""
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(user_id)
        
        if user_id in self.user_presence:
            self.user_presence[user_id].floor_id = None
        
        # Notify room about user leaving
        await self.broadcast_to_room(room_id, {
            "type": "user_left_room",
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any]):
        """Broadcast message to all users in a room"""
        if room_id not in self.room_connections:
            return
        
        message_json = json.dumps(message)
        disconnected_users = []
        
        for user_id in self.room_connections[room_id]:
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_text(message_json)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    disconnected_users.append(user_id)
            else:
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id not in self.active_connections:
            return
        
        try:
            message_json = json.dumps(message)
            await self.active_connections[user_id].send_text(message_json)
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            await self.disconnect(user_id)
    
    async def broadcast_user_joined(self, user_id: str, username: str):
        """Broadcast user joined event"""
        message = {
            "type": "user_joined",
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for room_id in self.room_connections.values():
            for room_user_id in room_id:
                if room_user_id != user_id:
                    await self.send_to_user(room_user_id, message)
    
    async def broadcast_user_left(self, user_id: str):
        """Broadcast user left event"""
        message = {
            "type": "user_left",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for room_id in self.room_connections.values():
            for room_user_id in room_id:
                if room_user_id != user_id:
                    await self.send_to_user(room_user_id, message)
    
    async def send_room_state(self, user_id: str, room_id: str):
        """Send current room state to user"""
        # Get all users in the room
        room_users = []
        if room_id in self.room_connections:
            for uid in self.room_connections[room_id]:
                if uid in self.user_presence:
                    presence = self.user_presence[uid]
                    room_users.append({
                        "user_id": presence.user_id,
                        "username": presence.username,
                        "current_action": presence.current_action,
                        "cursor_position": presence.cursor_position
                    })
        
        # Get active locks in the room
        room_locks = []
        for lock in self.editing_locks.values():
            if lock.resource_id == room_id:
                room_locks.append({
                    "lock_id": lock.lock_id,
                    "lock_type": lock.lock_type.value,
                    "user_id": lock.user_id,
                    "username": lock.username,
                    "acquired_at": lock.acquired_at.isoformat(),
                    "expires_at": lock.expires_at.isoformat()
                })
        
        message = {
            "type": "room_state",
            "room_id": room_id,
            "users": room_users,
            "locks": room_locks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_to_user(user_id, message)

class CollaborativeEditingManager:
    """Manages collaborative editing locks and conflict resolution"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.lock_timeout = 300  # 5 minutes
        self.conflict_resolution_timeout = 60  # 1 minute
    
    async def acquire_lock(self, user_id: str, username: str, lock_type: LockType, 
                          resource_id: str, metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Acquire a collaborative editing lock"""
        # Check if resource is already locked
        existing_lock = self._get_lock_for_resource(resource_id, lock_type)
        
        if existing_lock:
            if existing_lock.user_id == user_id:
                # User already has the lock, extend it
                existing_lock.expires_at = datetime.utcnow() + timedelta(seconds=self.lock_timeout)
                return True, existing_lock.lock_id
            else:
                # Resource is locked by another user
                return False, f"Resource locked by {existing_lock.username}"
        
        # Create new lock
        lock_id = str(uuid4())
        lock = EditingLock(
            lock_id=lock_id,
            lock_type=lock_type,
            resource_id=resource_id,
            user_id=user_id,
            username=username,
            acquired_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.lock_timeout),
            metadata=metadata or {}
        )
        
        self.websocket_manager.editing_locks[lock_id] = lock
        
        # Notify other users about the lock
        await self._notify_lock_acquired(lock)
        
        logger.info(f"Lock acquired: {lock_type.value} on {resource_id} by {username}")
        return True, lock_id
    
    async def release_lock(self, lock_id: str, user_id: str) -> bool:
        """Release a collaborative editing lock"""
        if lock_id not in self.websocket_manager.editing_locks:
            return False
        
        lock = self.websocket_manager.editing_locks[lock_id]
        
        if lock.user_id != user_id:
            return False
        
        # Notify other users about lock release
        await self._notify_lock_released(lock)
        
        del self.websocket_manager.editing_locks[lock_id]
        
        logger.info(f"Lock released: {lock.lock_type.value} on {lock.resource_id} by {lock.username}")
        return True
    
    async def release_user_locks(self, user_id: str):
        """Release all locks held by a user"""
        locks_to_release = []
        
        for lock_id, lock in self.websocket_manager.editing_locks.items():
            if lock.user_id == user_id:
                locks_to_release.append(lock_id)
        
        for lock_id in locks_to_release:
            await self.release_lock(lock_id, user_id)
    
    def _get_lock_for_resource(self, resource_id: str, lock_type: LockType) -> Optional[EditingLock]:
        """Get existing lock for a resource"""
        for lock in self.websocket_manager.editing_locks.values():
            if lock.resource_id == resource_id and lock.lock_type == lock_type:
                # Check if lock is expired
                if datetime.utcnow() > lock.expires_at:
                    del self.websocket_manager.editing_locks[lock.lock_id]
                    continue
                return lock
        return None
    
    async def _notify_lock_acquired(self, lock: EditingLock):
        """Notify users about lock acquisition"""
        message = {
            "type": "lock_acquired",
            "lock_id": lock.lock_id,
            "lock_type": lock.lock_type.value,
            "resource_id": lock.resource_id,
            "user_id": lock.user_id,
            "username": lock.username,
            "acquired_at": lock.acquired_at.isoformat(),
            "expires_at": lock.expires_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_room(lock.resource_id, message)
    
    async def _notify_lock_released(self, lock: EditingLock):
        """Notify users about lock release"""
        message = {
            "type": "lock_released",
            "lock_id": lock.lock_id,
            "lock_type": lock.lock_type.value,
            "resource_id": lock.resource_id,
            "user_id": lock.user_id,
            "username": lock.username,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast_to_room(lock.resource_id, message)

class ConflictResolutionManager:
    """Manages conflict detection and resolution"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
    
    async def detect_conflict(self, resource_id: str, user_id_1: str, user_id_2: str, 
                            conflict_type: str, description: str, severity: ConflictSeverity = ConflictSeverity.MEDIUM):
        """Detect and create a conflict"""
        conflict_id = str(uuid4())
        
        conflict = Conflict(
            conflict_id=conflict_id,
            resource_id=resource_id,
            conflict_type=conflict_type,
            severity=severity,
            user_id_1=user_id_1,
            user_id_2=user_id_2,
            description=description,
            created_at=datetime.utcnow()
        )
        
        self.websocket_manager.conflicts[conflict_id] = conflict
        
        # Notify users about the conflict
        await self._notify_conflict_detected(conflict)
        
        logger.warning(f"Conflict detected: {conflict_type} on {resource_id} between {user_id_1} and {user_id_2}")
        return conflict_id
    
    async def resolve_conflict(self, conflict_id: str, resolution: str, resolved_by: str):
        """Resolve a conflict"""
        if conflict_id not in self.websocket_manager.conflicts:
            return False
        
        conflict = self.websocket_manager.conflicts[conflict_id]
        conflict.resolved = True
        conflict.resolution = resolution
        
        # Notify users about conflict resolution
        await self._notify_conflict_resolved(conflict, resolved_by)
        
        logger.info(f"Conflict resolved: {conflict_id} by {resolved_by}")
        return True
    
    async def _notify_conflict_detected(self, conflict: Conflict):
        """Notify users about conflict detection"""
        message = {
            "type": "conflict_detected",
            "conflict_id": conflict.conflict_id,
            "resource_id": conflict.resource_id,
            "conflict_type": conflict.conflict_type,
            "severity": conflict.severity.value,
            "user_id_1": conflict.user_id_1,
            "user_id_2": conflict.user_id_2,
            "description": conflict.description,
            "created_at": conflict.created_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to both users involved in the conflict
        await self.websocket_manager.send_to_user(conflict.user_id_1, message)
        await self.websocket_manager.send_to_user(conflict.user_id_2, message)
    
    async def _notify_conflict_resolved(self, conflict: Conflict, resolved_by: str):
        """Notify users about conflict resolution"""
        message = {
            "type": "conflict_resolved",
            "conflict_id": conflict.conflict_id,
            "resource_id": conflict.resource_id,
            "resolution": conflict.resolution,
            "resolved_by": resolved_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to both users involved in the conflict
        await self.websocket_manager.send_to_user(conflict.user_id_1, message)
        await self.websocket_manager.send_to_user(conflict.user_id_2, message)

class RealTimeService:
    """Main real-time service that coordinates all real-time features"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.collaborative_editing = CollaborativeEditingManager(self.websocket_manager)
        self.conflict_resolution = ConflictResolutionManager(self.websocket_manager)
    
    async def start(self):
        """Start the real-time service"""
        await self.websocket_manager.start()
        logger.info("Real-time service started")
    
    async def stop(self):
        """Stop the real-time service"""
        await self.websocket_manager.stop()
        logger.info("Real-time service stopped")
    
    async def handle_websocket_message(self, user_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = message.get("type")
        
        try:
            if message_type == "join_room":
                await self.websocket_manager.join_room(user_id, message["room_id"])
            
            elif message_type == "leave_room":
                await self.websocket_manager.leave_room(user_id, message["room_id"])
            
            elif message_type == "update_presence":
                await self._update_user_presence(user_id, message)
            
            elif message_type == "acquire_lock":
                await self._handle_acquire_lock(user_id, message)
            
            elif message_type == "release_lock":
                await self._handle_release_lock(user_id, message)
            
            elif message_type == "resolve_conflict":
                await self._handle_resolve_conflict(user_id, message)
            
            elif message_type == "broadcast":
                await self._handle_broadcast(user_id, message)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
            await self.websocket_manager.send_to_user(user_id, {
                "type": "error",
                "message": "Failed to process message",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _update_user_presence(self, user_id: str, message: Dict[str, Any]):
        """Update user presence information"""
        if user_id not in self.websocket_manager.user_presence:
            return
        
        presence = self.websocket_manager.user_presence[user_id]
        presence.last_seen = datetime.utcnow()
        
        if "floor_id" in message:
            presence.floor_id = message["floor_id"]
        
        if "current_action" in message:
            presence.current_action = message["current_action"]
        
        if "cursor_position" in message:
            presence.cursor_position = message["cursor_position"]
        
        if "metadata" in message:
            presence.symbol_metadata.update(message["metadata"])
        
        # Broadcast presence update to room
        if presence.floor_id:
            await self.websocket_manager.broadcast_to_room(presence.floor_id, {
                "type": "presence_updated",
                "user_id": user_id,
                "username": presence.username,
                "current_action": presence.current_action,
                "cursor_position": presence.cursor_position,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_acquire_lock(self, user_id: str, message: Dict[str, Any]):
        """Handle lock acquisition request"""
        username = self.websocket_manager.user_presence.get(user_id, UserPresence(user_id, "Unknown")).username
        lock_type = LockType(message["lock_type"])
        resource_id = message["resource_id"]
        metadata = message.get("metadata", {})
        
        success, result = await self.collaborative_editing.acquire_lock(
            user_id, username, lock_type, resource_id, metadata
        )
        
        await self.websocket_manager.send_to_user(user_id, {
            "type": "lock_response",
            "success": success,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_release_lock(self, user_id: str, message: Dict[str, Any]):
        """Handle lock release request"""
        lock_id = message["lock_id"]
        
        success = await self.collaborative_editing.release_lock(lock_id, user_id)
        
        await self.websocket_manager.send_to_user(user_id, {
            "type": "lock_release_response",
            "success": success,
            "lock_id": lock_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_resolve_conflict(self, user_id: str, message: Dict[str, Any]):
        """Handle conflict resolution request"""
        conflict_id = message["conflict_id"]
        resolution = message["resolution"]
        
        success = await self.conflict_resolution.resolve_conflict(conflict_id, resolution, user_id)
        
        await self.websocket_manager.send_to_user(user_id, {
            "type": "conflict_resolution_response",
            "success": success,
            "conflict_id": conflict_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_broadcast(self, user_id: str, message: Dict[str, Any]):
        """Handle broadcast message"""
        room_id = message.get("room_id")
        broadcast_message = message.get("message", {})
        
        if room_id:
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "broadcast",
                "user_id": user_id,
                "username": self.websocket_manager.user_presence.get(user_id, UserPresence(user_id, "Unknown")).username,
                "message": broadcast_message,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _cleanup_loop(self):
        """Cleanup loop for expired locks and inactive users"""
        while True:
            try:
                # Clean up expired locks
                current_time = datetime.utcnow()
                expired_locks = []
                
                for lock_id, lock in self.websocket_manager.editing_locks.items():
                    if current_time > lock.expires_at:
                        expired_locks.append(lock_id)
                
                for lock_id in expired_locks:
                    await self.collaborative_editing.release_lock(lock_id, lock.user_id)
                
                # Clean up inactive users (not seen for more than 5 minutes)
                inactive_users = []
                for user_id, presence in self.websocket_manager.user_presence.items():
                    if current_time - presence.last_seen > timedelta(minutes=5):
                        inactive_users.append(user_id)
                
                for user_id in inactive_users:
                    await self.websocket_manager.disconnect(user_id)
                
                await asyncio.sleep(30)  # Run cleanup every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(30)

# Global service instance - lazy singleton
_realtime_service = None

def get_realtime_service() -> RealTimeService:
    """Get the global realtime service instance (lazy singleton)"""
    global _realtime_service
    if _realtime_service is None:
        _realtime_service = RealTimeService()
    return _realtime_service

# For backward compatibility
realtime_service = get_realtime_service() 