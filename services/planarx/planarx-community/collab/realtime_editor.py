"""
Real-Time Collaboration Engine
Enables multiple users to edit Planarx drafts simultaneously with presence tracking
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from websockets.server import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class EditType(Enum):
    """Types of collaborative edits"""
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"
    STYLE = "style"
    ANNOTATION = "annotation"


class PresenceStatus(Enum):
    """User presence status"""
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"
    EDITING = "editing"


@dataclass
class EditOperation:
    """Represents a collaborative edit operation"""
    id: str
    draft_id: str
    user_id: str
    edit_type: EditType
    timestamp: datetime
    position: Dict[str, Any]
    content: Optional[str]
    metadata: Dict[str, Any]
    version: int

    def __post_init__(self):
        pass
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserPresence:
    """User presence information"""
    user_id: str
    display_name: str
    status: PresenceStatus
    last_seen: datetime
    current_section: Optional[str]
    cursor_position: Optional[Dict[str, Any]]
    is_typing: bool

    def __post_init__(self):
        if self.current_section is None:
            self.current_section = "main"
        if self.cursor_position is None:
            self.cursor_position = {"x": 0, "y": 0}


@dataclass
class CollaborationSession:
    """Active collaboration session for a draft"""
    draft_id: str
    session_id: str
    created_at: datetime
    last_activity: datetime
    active_users: Dict[str, UserPresence]
    edit_history: List[EditOperation]
    version: int
    is_active: bool
    permissions: Dict[str, List[str]]

    def __post_init__(self):
        if self.active_users is None:
            self.active_users = {}
        if self.edit_history is None:
            self.edit_history = []
        if self.permissions is None:
            self.permissions = {}


class RealtimeEditor:
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Real-time collaborative editing engine"""

    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.user_connections: Dict[str, Set[WebSocketServerProtocol]] = {}
        self.draft_sessions: Dict[str, str] = {}  # draft_id -> session_id
        self.heartbeat_interval = 30  # seconds
        self.presence_timeout = 120  # seconds
        self.logger = logging.getLogger(__name__)

    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket collaboration server"""
        async def handle_connection(websocket: WebSocketServerProtocol, path: str):
            try:
                await self.handle_client(websocket, path)
            except ConnectionClosed:
                self.logger.info("Client connection closed")
            except Exception as e:
                self.logger.error(f"Error handling client: {e}")

        server = await serve(handle_connection, host, port)
        self.logger.info(f"Collaboration server started on ws://{host}:{port}")

        # Start background tasks
        asyncio.create_task(self.cleanup_inactive_sessions()
        asyncio.create_task(self.heartbeat_presence()
        await server.wait_closed()

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle individual client connections"""
        user_id = None
        session_id = None

        try:
            async for message in websocket:
                data = json.loads(message)
                message_type = data.get("type")

                if message_type == "join_session":
                    user_id = data["user_id"]
                    draft_id = data["draft_id"]
                    display_name = data["display_name"]

                    session_id = await self.join_session(
                        websocket, user_id, draft_id, display_name
                    )

                    # Send session info to client
                    await websocket.send(json.dumps({
                        "type": "session_joined",
                        "session_id": session_id,
                        "draft_id": draft_id,
                        "active_users": self.get_session_users(session_id),
                        "current_version": self.sessions[session_id].version
                    }))

                elif message_type == "edit_operation":
                    if session_id and user_id:
                        await self.handle_edit_operation(
                            session_id, user_id, data["operation"]
                        )

                elif message_type == "presence_update":
                    if session_id and user_id:
                        await self.update_presence(
                            session_id, user_id, data["presence"]
                        )

                elif message_type == "cursor_update":
                    if session_id and user_id:
                        await self.update_cursor(
                            session_id, user_id, data["cursor"]
                        )

                elif message_type == "typing_indicator":
                    if session_id and user_id:
                        await self.update_typing_status(
                            session_id, user_id, data["is_typing"]
                        )

                elif message_type == "leave_session":
                    if session_id and user_id:
                        await self.leave_session(session_id, user_id)
                        break

                elif message_type == "ping":
                    await websocket.send(json.dumps({"type": "pong"})
        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")

        finally:
            if session_id and user_id:
                await self.leave_session(session_id, user_id)

    async def join_session(
        self,
        websocket: WebSocketServerProtocol,
        user_id: str,
        draft_id: str,
        display_name: str
    ) -> str:
        """Join a collaboration session"""

        # Get or create session
        if draft_id in self.draft_sessions:
            session_id = self.draft_sessions[draft_id]
        else:
            session_id = str(uuid.uuid4()
            session = CollaborationSession(
                draft_id=draft_id,
                session_id=session_id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                active_users={},
                edit_history=[],
                version=0,
                is_active=True,
                permissions={}
            )
            self.sessions[session_id] = session
            self.draft_sessions[draft_id] = session_id

        session = self.sessions[session_id]

        # Add user to session
        presence = UserPresence(
            user_id=user_id,
            display_name=display_name,
            status=PresenceStatus.ONLINE,
            last_seen=datetime.utcnow(),
            current_section="main",
            cursor_position={"x": 0, "y": 0},
            is_typing=False
        )
        session.active_users[user_id] = presence

        # Track connection
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        # Notify other users
        await self.broadcast_to_session(session_id, {
            "type": "user_joined",
            "user_id": user_id,
            "display_name": display_name,
            "presence": asdict(presence)
        }, exclude_user=user_id)

        self.logger.info(f"User {user_id} joined session {session_id}")
        return session_id

    async def leave_session(self, session_id: str, user_id: str):
        """Leave a collaboration session"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        # Remove user from session import session
        if user_id in session.active_users:
            del session.active_users[user_id]

        # Remove connection tracking
        if user_id in self.user_connections:
            self.user_connections[user_id].clear()

        # Notify other users
        await self.broadcast_to_session(session_id, {
            "type": "user_left",
            "user_id": user_id
        })

        # Clean up empty sessions
        if not session.active_users:
            await self.cleanup_session(session_id)

        self.logger.info(f"User {user_id} left session {session_id}")

    async def handle_edit_operation(self, session_id: str, user_id: str, operation_data: Dict):
        """Handle collaborative edit operations"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        # Create edit operation
        edit_op = EditOperation(
            id=str(uuid.uuid4()),
            draft_id=session.draft_id,
            user_id=user_id,
            edit_type=EditType(operation_data["type"]),
            timestamp=datetime.utcnow(),
            position=operation_data.get("position", {}),
            content=operation_data.get("content"),
            metadata=operation_data.get("metadata", {}),
            version=session.version + 1
        )

        # Add to history
        session.edit_history.append(edit_op)
        session.version = edit_op.version
        session.last_activity = datetime.utcnow()

        # Broadcast to other users
        await self.broadcast_to_session(session_id, {
            "type": "edit_operation",
            "operation": asdict(edit_op)
        }, exclude_user=user_id)

        self.logger.info(f"Edit operation applied: {edit_op.id} by {user_id}")

    async def update_presence(self, session_id: str, user_id: str, presence_data: Dict):
        """Update user presence information"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        if user_id not in session.active_users:
            return

        presence = session.active_users[user_id]
        presence.status = PresenceStatus(presence_data.get("status", "online")
        presence.last_seen = datetime.utcnow()
        presence.current_section = presence_data.get("section", "main")
        presence.is_typing = presence_data.get("is_typing", False)

        # Broadcast presence update
        await self.broadcast_to_session(session_id, {
            "type": "presence_update",
            "user_id": user_id,
            "presence": asdict(presence)
        }, exclude_user=user_id)

    async def update_cursor(self, session_id: str, user_id: str, cursor_data: Dict):
        """Update user cursor position"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        if user_id not in session.active_users:
            return

        presence = session.active_users[user_id]
        presence.cursor_position = cursor_data
        presence.last_seen = datetime.utcnow()

        # Broadcast cursor update
        await self.broadcast_to_session(session_id, {
            "type": "cursor_update",
            "user_id": user_id,
            "cursor": cursor_data
        }, exclude_user=user_id)

    async def update_typing_status(self, session_id: str, user_id: str, is_typing: bool):
        """Update user typing indicator"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        if user_id not in session.active_users:
            return

        presence = session.active_users[user_id]
        presence.is_typing = is_typing
        presence.last_seen = datetime.utcnow()

        # Broadcast typing status
        await self.broadcast_to_session(session_id, {
            "type": "typing_indicator",
            "user_id": user_id,
            "is_typing": is_typing
        }, exclude_user=user_id)

    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict,
        exclude_user: Optional[str] = None
    ):
        """Broadcast message to all users in a session"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        message_json = json.dumps(message)

        for user_id in session.active_users:
            if user_id == exclude_user:
                continue

            if user_id in self.user_connections:
                for websocket in self.user_connections[user_id]:
                    try:
                        await websocket.send(message_json)
                    except Exception as e:
                        self.logger.error(f"Error sending message to {user_id}: {e}")

    def get_session_users(self, session_id: str) -> List[Dict]:
        """Get list of active users in a session"""
        if session_id not in self.sessions:
            return []

        session = self.sessions[session_id]
        return [asdict(presence) for presence in session.active_users.values()]

    async def cleanup_session(self, session_id: str):
        """Clean up an inactive session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]

            # Remove from draft sessions mapping
            if session.draft_id in self.draft_sessions:
                del self.draft_sessions[session.draft_id]

            # Remove session
            del self.sessions[session_id]

            self.logger.info(f"Cleaned up session {session_id}")

    async def cleanup_inactive_sessions(self):
        """Background task to clean up inactive sessions"""
        while True:
            try:
                current_time = datetime.utcnow()
                sessions_to_cleanup = []

                for session_id, session in self.sessions.items():
                    # Check if session has been inactive for too long
                    if (current_time - session.last_activity).total_seconds() > 3600:  # 1 hour
                        sessions_to_cleanup.append(session_id)

                    # Check for inactive users
                    inactive_users = []
                    for user_id, presence in session.active_users.items():
                        if (current_time - presence.last_seen).total_seconds() > self.presence_timeout:
                            inactive_users.append(user_id)

                    # Remove inactive users
                    for user_id in inactive_users:
                        del session.active_users[user_id]
                        if user_id in self.user_connections:
                            self.user_connections[user_id].clear()

                # Clean up inactive sessions
                for session_id in sessions_to_cleanup:
                    await self.cleanup_session(session_id)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    async def heartbeat_presence(self):
        """Background task to send heartbeat and update presence"""
        while True:
            try:
                current_time = datetime.utcnow()

                for session_id, session in self.sessions.items():
                    # Update away status for inactive users
                    for user_id, presence in session.active_users.items():
                        time_since_activity = (current_time - presence.last_seen).total_seconds()

                        if time_since_activity > 300:  # 5 minutes
                            presence.status = PresenceStatus.AWAY
                        elif time_since_activity > 60:  # 1 minute
                            presence.status = PresenceStatus.EDITING
                        else:
                            presence.status = PresenceStatus.ONLINE

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a collaboration session"""
        if session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]

        return {
            "session_id": session_id,
            "draft_id": session.draft_id,
            "active_users": len(session.active_users),
            "total_edits": len(session.edit_history),
            "current_version": session.version,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_active": session.is_active
        }

    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all sessions a user is participating in"""
        sessions = []
        for session_id, session in self.sessions.items():
            if user_id in session.active_users:
                sessions.append(session_id)
        return sessions


# Global realtime editor instance
realtime_editor = RealtimeEditor()
