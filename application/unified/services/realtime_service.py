"""
Real-time Service - Unified Real-time Features for Building Management

This module provides comprehensive real-time services including WebSocket
integration, live updates, and real-time collaboration features.
"""

from typing import Dict, Any, List, Optional, Set, Callable
import asyncio
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from application.unified.dto.building_dto import BuildingDTO
from application.unified.dto.realtime_dto import (
    RealtimeEvent, RealtimeMessage, RealtimeUpdate, RealtimeConnection,
    CollaborationSession, UserPresence
)
from infrastructure.realtime.websocket_manager import WebSocketManager
from infrastructure.realtime.event_bus import EventBus
from infrastructure.realtime.collaboration_manager import CollaborationManager

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Real-time event types."""
    BUILDING_UPDATE = "building_update"
    BUILDING_CREATE = "building_create"
    BUILDING_DELETE = "building_delete"
    USER_PRESENCE = "user_presence"
    COLLABORATION_UPDATE = "collaboration_update"
    SYSTEM_NOTIFICATION = "system_notification"
    PERFORMANCE_ALERT = "performance_alert"
    MAINTENANCE_ALERT = "maintenance_alert"


@dataclass
class RealtimeConfig:
    """Configuration for real-time features."""
    max_connections: int = 1000
    heartbeat_interval: int = 30
    connection_timeout: int = 300
    max_message_size: int = 1024 * 1024  # 1MB
    enable_collaboration: bool = True
    enable_presence: bool = True
    enable_notifications: bool = True


class RealtimeService:
    """
    Unified real-time service providing WebSocket integration and live updates.

    This service implements:
    - WebSocket connection management
    - Real-time event broadcasting
    - User presence tracking
    - Real-time collaboration
    - Live notifications and alerts
    """

    def __init__(self,
                 websocket_manager: WebSocketManager,
                 event_bus: EventBus,
                 collaboration_manager: CollaborationManager,
                 config: RealtimeConfig = None):
        """Initialize real-time service with components."""
        self.websocket_manager = websocket_manager
        self.event_bus = event_bus
        self.collaboration_manager = collaboration_manager
        self.config = config or RealtimeConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Active connections and subscriptions
        self.active_connections: Dict[str, RealtimeConnection] = {}
        self.building_subscriptions: Dict[str, Set[str]] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Start background tasks
        asyncio.create_task(self._heartbeat_task())
        asyncio.create_task(self._cleanup_task())

    async def connect_user(self, websocket: WebSocket, user_id: str,
                          user_data: Dict[str, Any]) -> RealtimeConnection:
        """
        Connect a user to the real-time service.

        Args:
            websocket: WebSocket connection
            user_id: User identifier
            user_data: User metadata

        Returns:
            Real-time connection object
        """
        try:
            # Accept WebSocket connection
            await websocket.accept()

            # Create connection object
            connection = RealtimeConnection(
                id=f"conn_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                websocket=websocket,
                connected_at=datetime.utcnow(),
                user_data=user_data,
                subscriptions=set(),
                is_active=True
            )

            # Register connection
            self.active_connections[connection.id] = connection

            # Update user presence
            await self._update_user_presence(user_id, "online", user_data)

            # Send welcome message
            welcome_message = RealtimeMessage(
                type="connection_established",
                data={
                    "connection_id": connection.id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await self._send_message(connection, welcome_message)

            self.logger.info(f"User {user_id} connected with connection {connection.id}")
            return connection

        except Exception as e:
            self.logger.error(f"Error connecting user {user_id}: {e}")
            raise

    async def disconnect_user(self, connection_id: str) -> bool:
        """
        Disconnect a user from the real-time service.

        Args:
            connection_id: Connection identifier

        Returns:
            True if disconnection successful
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return False

            # Update user presence
            await self._update_user_presence(connection.user_id, "offline", {})

            # Remove from subscriptions import subscriptions
            await self._remove_user_subscriptions(connection)

            # Close WebSocket connection
            await connection.websocket.close()

            # Remove from active connections
            del self.active_connections[connection_id]

            self.logger.info(f"User {connection.user_id} disconnected")
            return True

        except Exception as e:
            self.logger.error(f"Error disconnecting user {connection_id}: {e}")
            return False

    async def subscribe_to_building(self, connection_id: str, building_id: str) -> bool:
        """
        Subscribe a connection to building updates.

        Args:
            connection_id: Connection identifier
            building_id: Building identifier

        Returns:
            True if subscription successful
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return False

            # Add to building subscriptions
            if building_id not in self.building_subscriptions:
                self.building_subscriptions[building_id] = set()
            self.building_subscriptions[building_id].add(connection_id)

            # Add to connection subscriptions
            connection.subscriptions.add(f"building:{building_id}")

            # Send subscription confirmation
            subscription_message = RealtimeMessage(
                type="subscription_confirmed",
                data={
                    "building_id": building_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            await self._send_message(connection, subscription_message)

            self.logger.info(f"Connection {connection_id} subscribed to building {building_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error subscribing to building {building_id}: {e}")
            return False

    async def unsubscribe_from_building(self, connection_id: str, building_id: str) -> bool:
        """
        Unsubscribe a connection from building updates.

        Args:
            connection_id: Connection identifier
            building_id: Building identifier

        Returns:
            True if unsubscription successful
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return False

            # Remove from building subscriptions
            if building_id in self.building_subscriptions:
                self.building_subscriptions[building_id].discard(connection_id)
                if not self.building_subscriptions[building_id]:
                    del self.building_subscriptions[building_id]

            # Remove from connection subscriptions
            connection.subscriptions.discard(f"building:{building_id}")

            self.logger.info(f"Connection {connection_id} unsubscribed from building {building_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error unsubscribing from building {building_id}: {e}")
            return False

    async def broadcast_building_update(self, building_id: str, update_data: Dict[str, Any]) -> int:
        """
        Broadcast building update to all subscribed connections.

        Args:
            building_id: Building identifier
            update_data: Update data to broadcast

        Returns:
            Number of connections that received the update
        """
        try:
            subscribed_connections = self.building_subscriptions.get(building_id, set())

            update_message = RealtimeMessage(
                type=EventType.BUILDING_UPDATE,
                data={
                    "building_id": building_id,
                    "update": update_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            sent_count = 0
            for connection_id in subscribed_connections:
                connection = self.active_connections.get(connection_id)
                if connection and connection.is_active:
                    try:
                        await self._send_message(connection, update_message)
                        sent_count += 1
                    except Exception as e:
                        self.logger.error(f"Error sending update to connection {connection_id}: {e}")
                        # Mark connection as inactive
                        connection.is_active = False

            self.logger.info(f"Broadcasted building update to {sent_count} connections")
            return sent_count

        except Exception as e:
            self.logger.error(f"Error broadcasting building update: {e}")
            return 0

    async def send_user_notification(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        Send notification to a specific user.

        Args:
            user_id: User identifier
            notification: Notification data

        Returns:
            True if notification sent successfully
        """
        try:
            # Find user's active connections'
            user_connections = [
                conn for conn in self.active_connections.values()
                if conn.user_id == user_id and conn.is_active
            ]

            notification_message = RealtimeMessage(
                type="user_notification",
                data={
                    "notification": notification,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            sent_count = 0
            for connection in user_connections:
                try:
                    await self._send_message(connection, notification_message)
                    sent_count += 1
                except Exception as e:
                    self.logger.error(f"Error sending notification to connection {connection.id}: {e}")
                    connection.is_active = False

            self.logger.info(f"Sent notification to user {user_id} via {sent_count} connections")
            return sent_count > 0

        except Exception as e:
            self.logger.error(f"Error sending user notification: {e}")
            return False

    async def start_collaboration_session(self, building_id: str,
                                        initiator_id: str) -> CollaborationSession:
        """
        Start a real-time collaboration session for a building.

        Args:
            building_id: Building identifier
            initiator_id: User who initiated the session

        Returns:
            Collaboration session object
        """
        try:
            session = await self.collaboration_manager.create_session(
                building_id=building_id,
                initiator_id=initiator_id
            )

            # Notify all building subscribers
            session_message = RealtimeMessage(
                type="collaboration_session_started",
                data={
                    "session_id": session.id,
                    "building_id": building_id,
                    "initiator_id": initiator_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            await self.broadcast_building_update(building_id, {
                "event": "collaboration_session_started",
                "session_id": session.id
            })

            self.logger.info(f"Started collaboration session {session.id} for building {building_id}")
            return session

        except Exception as e:
            self.logger.error(f"Error starting collaboration session: {e}")
            raise

    async def join_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """
        Join a collaboration session.

        Args:
            session_id: Session identifier
            user_id: User identifier

        Returns:
            True if join successful
        """
        try:
            success = await self.collaboration_manager.join_session(session_id, user_id)

            if success:
                # Notify session participants
                join_message = RealtimeMessage(
                    type="collaboration_user_joined",
                    data={
                        "session_id": session_id,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

                await self._broadcast_to_session(session_id, join_message)

                self.logger.info(f"User {user_id} joined collaboration session {session_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error joining collaboration session: {e}")
            return False

    async def leave_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """
        Leave a collaboration session.

        Args:
            session_id: Session identifier
            user_id: User identifier

        Returns:
            True if leave successful
        """
        try:
            success = await self.collaboration_manager.leave_session(session_id, user_id)

            if success:
                # Notify session participants
                leave_message = RealtimeMessage(
                    type="collaboration_user_left",
                    data={
                        "session_id": session_id,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

                await self._broadcast_to_session(session_id, leave_message)

                self.logger.info(f"User {user_id} left collaboration session {session_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error leaving collaboration session: {e}")
            return False

    async def handle_websocket_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Handle incoming WebSocket message.

        Args:
            connection_id: Connection identifier
            message: Message data

        Returns:
            True if message handled successfully
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return False

            message_type = message.get("type")
            data = message.get("data", {})

            if message_type == "subscribe_building":
                building_id = data.get("building_id")
                if building_id:
                    await self.subscribe_to_building(connection_id, building_id)

            elif message_type == "unsubscribe_building":
                building_id = data.get("building_id")
                if building_id:
                    await self.unsubscribe_from_building(connection_id, building_id)

            elif message_type == "join_collaboration":
                session_id = data.get("session_id")
                if session_id:
                    await self.join_collaboration_session(session_id, connection.user_id)

            elif message_type == "leave_collaboration":
                session_id = data.get("session_id")
                if session_id:
                    await self.leave_collaboration_session(session_id, connection.user_id)

            elif message_type == "collaboration_update":
                session_id = data.get("session_id")
                update_data = data.get("update")
                if session_id and update_data:
                    await self._handle_collaboration_update(session_id, connection.user_id, update_data)

            elif message_type == "ping":
                # Respond to ping with pong
                pong_message = RealtimeMessage(
                    type="pong",
                    data={"timestamp": datetime.utcnow().isoformat()}
                )
                await self._send_message(connection, pong_message)

            else:
                self.logger.warning(f"Unknown message type: {message_type}")

            return True

        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
            return False

    async def _send_message(self, connection: RealtimeConnection, message: RealtimeMessage) -> bool:
        """Send message to a specific connection."""
        try:
            message_data = {
                "type": message.type,
                "data": message.data,
                "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.utcnow().isoformat()
            }

            await connection.websocket.send_text(json.dumps(message_data))
            return True

        except Exception as e:
            self.logger.error(f"Error sending message to connection {connection.id}: {e}")
            connection.is_active = False
            return False

    async def _update_user_presence(self, user_id: str, status: str, user_data: Dict[str, Any]):
        """Update user presence status."""
        try:
            presence = UserPresence(
                user_id=user_id,
                status=status,
                last_seen=datetime.utcnow(),
                user_data=user_data
            )

            # Broadcast presence update
            presence_message = RealtimeMessage(
                type=EventType.USER_PRESENCE,
                data={
                    "user_id": user_id,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Send to all connections
            for connection in self.active_connections.values():
                if connection.is_active:
                    await self._send_message(connection, presence_message)

        except Exception as e:
            self.logger.error(f"Error updating user presence: {e}")

    async def _remove_user_subscriptions(self, connection: RealtimeConnection):
        """Remove user from all subscriptions."""
        try:
            for subscription in list(connection.subscriptions):
                if subscription.startswith("building:"):
                    building_id = subscription.split(":", 1)[1]
                    await self.unsubscribe_from_building(connection.id, building_id)

        except Exception as e:
            self.logger.error(f"Error removing user subscriptions: {e}")

    async def _broadcast_to_session(self, session_id: str, message: RealtimeMessage):
        """Broadcast message to all session participants."""
        try:
            session = await self.collaboration_manager.get_session(session_id)
            if not session:
                return

            for participant_id in session.participants:
                await self.send_user_notification(participant_id, {
                    "session_id": session_id,
                    "message": message.data
                })

        except Exception as e:
            self.logger.error(f"Error broadcasting to session: {e}")

    async def _handle_collaboration_update(self, session_id: str, user_id: str, update_data: Dict[str, Any]):
        """Handle collaboration update from a user."""
        try:
            # Store update in collaboration manager
            await self.collaboration_manager.add_update(session_id, user_id, update_data)

            # Broadcast to other session participants
            update_message = RealtimeMessage(
                type="collaboration_update",
                data={
                    "session_id": session_id,
                    "user_id": user_id,
                    "update": update_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            await self._broadcast_to_session(session_id, update_message)

        except Exception as e:
            self.logger.error(f"Error handling collaboration update: {e}")

    async def _heartbeat_task(self):
        """Background task to send heartbeat messages."""
        while True:
            try:
                heartbeat_message = RealtimeMessage(
                    type="heartbeat",
                    data={"timestamp": datetime.utcnow().isoformat()}
                )

                for connection in list(self.active_connections.values()):
                    if connection.is_active:
                        try:
                            await self._send_message(connection, heartbeat_message)
                        except Exception:
                            connection.is_active = False

                await asyncio.sleep(self.config.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Error in heartbeat task: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)

    async def _cleanup_task(self):
        """Background task to cleanup inactive connections."""
        while True:
            try:
                current_time = datetime.utcnow()
                inactive_connections = []

                for connection_id, connection in self.active_connections.items():
                    if not connection.is_active:
                        inactive_connections.append(connection_id)
                    elif (current_time - connection.connected_at).seconds > self.config.connection_timeout:
                        connection.is_active = False
                        inactive_connections.append(connection_id)

                for connection_id in inactive_connections:
                    await self.disconnect_user(connection_id)

                await asyncio.sleep(60)  # Cleanup every minute

            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
