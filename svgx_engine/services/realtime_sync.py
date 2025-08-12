"""
Real-time Synchronization Service

This service maintains real-time synchronization between the Go ArxObject
engine and SVGX rendering, enabling live updates and collaborative editing.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime
import logging
from enum import Enum
import websockets
from dataclasses import dataclass, field

from svgx_engine.integration.arxobject_bridge import get_arxobject_bridge
from services.arxobject.client.python_client import ArxObjectClient

logger = logging.getLogger(__name__)


class SyncEventType(Enum):
    """Types of synchronization events."""
    OBJECT_CREATED = "object_created"
    OBJECT_UPDATED = "object_updated"
    OBJECT_DELETED = "object_deleted"
    RELATIONSHIP_CREATED = "relationship_created"
    RELATIONSHIP_DELETED = "relationship_deleted"
    CONSTRAINT_VIOLATED = "constraint_violated"
    COLLISION_DETECTED = "collision_detected"


@dataclass
class SyncEvent:
    """Synchronization event data."""
    event_type: SyncEventType
    object_id: int
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class RealtimeSyncService:
    """
    Service for real-time synchronization between ArxObject engine and SVGX.
    
    Features:
    - WebSocket-based real-time updates
    - Efficient delta synchronization
    - Conflict resolution
    - Optimistic updates with rollback
    - Multi-user collaboration support
    """
    
    def __init__(self, websocket_port: int = 8765):
        """Initialize real-time sync service."""
        self.bridge = get_arxobject_bridge()
        self.arxobject_client = None
        self.websocket_port = websocket_port
        
        # Connected clients
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.client_sessions: Dict[str, str] = {}  # client -> session_id
        
        # Sync state
        self.object_versions: Dict[int, int] = {}  # object_id -> version
        self.pending_updates: Dict[int, List[SyncEvent]] = {}
        self.conflict_queue: List[SyncEvent] = []
        
        # Event handlers
        self.event_handlers: Dict[SyncEventType, List[Callable]] = {
            event_type: [] for event_type in SyncEventType
        }
        
        # Performance tracking
        self.metrics = {
            'events_processed': 0,
            'conflicts_resolved': 0,
            'updates_sent': 0,
            'updates_received': 0
        }
    
    async def start(self):
        """Start the synchronization service."""
        # Connect to ArxObject engine
        await self.bridge.connect()
        self.arxobject_client = self.bridge.client
        
        # Start WebSocket server
        asyncio.create_task(self._start_websocket_server())
        
        # Start ArxObject change stream
        asyncio.create_task(self._monitor_arxobject_changes())
        
        # Start sync processor
        asyncio.create_task(self._process_sync_queue())
        
        logger.info(f"Real-time sync service started on port {self.websocket_port}")
    
    async def _start_websocket_server(self):
        """Start WebSocket server for client connections."""
        async def handle_client(websocket, path):
            """Handle individual client connection."""
            # Register client
            self.clients.add(websocket)
            session_id = self._generate_session_id()
            self.client_sessions[websocket] = session_id
            
            logger.info(f"Client connected: {session_id}")
            
            try:
                # Send initial sync state
                await self._send_initial_state(websocket)
                
                # Handle client messages
                async for message in websocket:
                    await self._handle_client_message(websocket, message)
                    
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                # Unregister client
                self.clients.discard(websocket)
                if websocket in self.client_sessions:
                    del self.client_sessions[websocket]
                logger.info(f"Client disconnected: {session_id}")
        
        # Start server
        await websockets.serve(handle_client, "localhost", self.websocket_port)
    
    async def _monitor_arxobject_changes(self):
        """Monitor ArxObject engine for changes."""
        
        async def handle_change(event_type: str, obj, timestamp):
            """Handle ArxObject change event."""
            # Create sync event
            sync_event = SyncEvent(
                event_type=SyncEventType(event_type),
                object_id=obj.id,
                timestamp=timestamp,
                data={
                    'type': obj.type,
                    'geometry': {
                        'x': obj.geometry.x,
                        'y': obj.geometry.y,
                        'z': obj.geometry.z,
                        'width': obj.geometry.width,
                        'height': obj.geometry.height,
                    },
                    'properties': obj.properties or {}
                }
            )
            
            # Queue for processing
            await self._queue_sync_event(sync_event)
        
        # Stream changes from ArxObject engine
        try:
            await self.arxobject_client.stream_changes(handle_change)
        except Exception as e:
            logger.error(f"Error monitoring ArxObject changes: {e}")
    
    async def _handle_client_message(self, websocket, message: str):
        """Handle message from client."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'update':
                await self._handle_client_update(websocket, data)
            elif msg_type == 'subscribe':
                await self._handle_subscription(websocket, data)
            elif msg_type == 'query':
                await self._handle_query(websocket, data)
            elif msg_type == 'validate':
                await self._handle_validation(websocket, data)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from client: {e}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def _handle_client_update(self, websocket, data: Dict):
        """Handle update from client."""
        object_id = data.get('object_id')
        changes = data.get('changes', {})
        version = data.get('version')
        
        # Check version for conflict
        current_version = self.object_versions.get(object_id, 0)
        
        if version and version < current_version:
            # Conflict detected
            await self._handle_conflict(websocket, object_id, changes, version)
            return
        
        # Apply update optimistically
        try:
            # Update in ArxObject engine
            updated_obj = await self.arxobject_client.update_object(
                object_id,
                properties=changes.get('properties'),
                validate=True
            )
            
            # Update version
            self.object_versions[object_id] = updated_obj.version
            
            # Broadcast to other clients
            await self._broadcast_update(
                object_id,
                updated_obj,
                exclude_client=websocket
            )
            
            # Send confirmation to originating client
            await self._send_message(websocket, {
                'type': 'update_confirmed',
                'object_id': object_id,
                'version': updated_obj.version
            })
            
            self.metrics['updates_received'] += 1
            
        except Exception as e:
            # Rollback on error
            await self._send_message(websocket, {
                'type': 'update_failed',
                'object_id': object_id,
                'error': str(e)
            })
    
    async def _handle_conflict(
        self,
        websocket,
        object_id: int,
        changes: Dict,
        client_version: int
    ):
        """Handle update conflict."""
        # Get current object state
        current_obj = await self.arxobject_client.get_object(object_id)
        
        # Send conflict notification
        await self._send_message(websocket, {
            'type': 'conflict',
            'object_id': object_id,
            'client_version': client_version,
            'server_version': current_obj.version,
            'current_state': {
                'geometry': {
                    'x': current_obj.geometry.x,
                    'y': current_obj.geometry.y,
                    'width': current_obj.geometry.width,
                    'height': current_obj.geometry.height,
                },
                'properties': current_obj.properties
            },
            'resolution_strategy': 'manual'  # or 'auto_merge', 'server_wins', etc.
        })
        
        self.metrics['conflicts_resolved'] += 1
    
    async def _handle_subscription(self, websocket, data: Dict):
        """Handle subscription request from client."""
        region = data.get('region')  # {min_x, min_y, max_x, max_y}
        object_types = data.get('object_types', [])
        
        # Query objects in region
        objects = await self.arxobject_client.query_region(
            region['min_x'], region['min_y'], 0,
            region['max_x'], region['max_y'], 100,
            object_types=object_types
        )
        
        # Send objects to client
        await self._send_message(websocket, {
            'type': 'subscription_data',
            'region': region,
            'objects': [
                {
                    'id': obj.id,
                    'type': obj.type,
                    'geometry': {
                        'x': obj.geometry.x,
                        'y': obj.geometry.y,
                        'width': obj.geometry.width,
                        'height': obj.geometry.height,
                    },
                    'properties': obj.properties,
                    'version': obj.version
                }
                for obj in objects
            ]
        })
        
        # Track subscription for future updates
        # (Store subscription info for targeted updates)
    
    async def _handle_query(self, websocket, data: Dict):
        """Handle query request from client."""
        query_type = data.get('query_type')
        
        if query_type == 'collisions':
            object_id = data.get('object_id')
            collisions = await self.arxobject_client.check_collisions(object_id)
            
            await self._send_message(websocket, {
                'type': 'query_result',
                'query_type': 'collisions',
                'object_id': object_id,
                'collisions': collisions
            })
            
        elif query_type == 'relationships':
            # Query relationships
            pass
    
    async def _handle_validation(self, websocket, data: Dict):
        """Handle validation request from client."""
        object_id = data.get('object_id')
        
        # Validate object
        collisions = await self.arxobject_client.check_collisions(object_id)
        
        await self._send_message(websocket, {
            'type': 'validation_result',
            'object_id': object_id,
            'valid': len(collisions) == 0,
            'violations': collisions
        })
    
    async def _broadcast_update(
        self,
        object_id: int,
        obj,
        exclude_client=None
    ):
        """Broadcast update to all connected clients."""
        message = {
            'type': 'object_updated',
            'object_id': object_id,
            'data': {
                'type': obj.type,
                'geometry': {
                    'x': obj.geometry.x,
                    'y': obj.geometry.y,
                    'width': obj.geometry.width,
                    'height': obj.geometry.height,
                },
                'properties': obj.properties,
                'version': obj.version
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to all clients except the originator
        for client in self.clients:
            if client != exclude_client:
                try:
                    await self._send_message(client, message)
                    self.metrics['updates_sent'] += 1
                except Exception as e:
                    logger.error(f"Failed to send update to client: {e}")
    
    async def _send_initial_state(self, websocket):
        """Send initial synchronization state to new client."""
        # Send current viewport objects
        # This would be based on client's initial request
        await self._send_message(websocket, {
            'type': 'initial_state',
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.client_sessions[websocket]
        })
    
    async def _send_message(self, websocket, message: Dict):
        """Send message to client."""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def _queue_sync_event(self, event: SyncEvent):
        """Queue sync event for processing."""
        if event.object_id not in self.pending_updates:
            self.pending_updates[event.object_id] = []
        self.pending_updates[event.object_id].append(event)
    
    async def _process_sync_queue(self):
        """Process queued sync events."""
        while True:
            try:
                # Process pending updates
                for object_id, events in list(self.pending_updates.items()):
                    if events:
                        # Process events in order
                        for event in events:
                            await self._process_sync_event(event)
                        
                        # Clear processed events
                        self.pending_updates[object_id] = []
                
                # Short delay to batch updates
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing sync queue: {e}")
                await asyncio.sleep(1)
    
    async def _process_sync_event(self, event: SyncEvent):
        """Process individual sync event."""
        # Trigger event handlers
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
        
        # Broadcast to clients
        if event.event_type in [
            SyncEventType.OBJECT_CREATED,
            SyncEventType.OBJECT_UPDATED,
            SyncEventType.OBJECT_DELETED
        ]:
            # Get updated object
            if event.event_type != SyncEventType.OBJECT_DELETED:
                obj = await self.arxobject_client.get_object(event.object_id)
                await self._broadcast_update(event.object_id, obj)
        
        self.metrics['events_processed'] += 1
    
    def register_event_handler(
        self,
        event_type: SyncEventType,
        handler: Callable
    ):
        """Register event handler for sync events."""
        self.event_handlers[event_type].append(handler)
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get synchronization metrics."""
        return {
            **self.metrics,
            'connected_clients': len(self.clients),
            'pending_updates': sum(len(events) for events in self.pending_updates.values()),
            'conflict_queue_size': len(self.conflict_queue)
        }


class SyncClient:
    """Client for connecting to sync service."""
    
    def __init__(self, url: str = "ws://localhost:8765"):
        """Initialize sync client."""
        self.url = url
        self.websocket = None
        self.handlers = {}
    
    async def connect(self):
        """Connect to sync service."""
        self.websocket = await websockets.connect(self.url)
        
        # Start message handler
        asyncio.create_task(self._handle_messages())
    
    async def _handle_messages(self):
        """Handle incoming messages."""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type in self.handlers:
                    await self.handlers[msg_type](data)
                    
            except Exception as e:
                logger.error(f"Error handling message: {e}")
    
    async def update_object(
        self,
        object_id: int,
        changes: Dict,
        version: Optional[int] = None
    ):
        """Send object update."""
        await self.websocket.send(json.dumps({
            'type': 'update',
            'object_id': object_id,
            'changes': changes,
            'version': version
        }))
    
    async def subscribe_region(
        self,
        min_x: float, min_y: float,
        max_x: float, max_y: float,
        object_types: Optional[List[str]] = None
    ):
        """Subscribe to region updates."""
        await self.websocket.send(json.dumps({
            'type': 'subscribe',
            'region': {
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y
            },
            'object_types': object_types or []
        }))
    
    def on_update(self, handler: Callable):
        """Register update handler."""
        self.handlers['object_updated'] = handler
    
    def on_conflict(self, handler: Callable):
        """Register conflict handler."""
        self.handlers['conflict'] = handler