"""
ArxLink Sync Protocol

Mesh topology formation and synchronization protocol for RF nodes.
Handles node discovery, route establishment, and data synchronization.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac
import base64
from collections import defaultdict, deque
import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncState(Enum):
    """Node synchronization states."""
    DISCOVERING = "discovering"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"


class MessageType(Enum):
    """Message types for sync protocol."""
    DISCOVERY = "discovery"
    HEARTBEAT = "heartbeat"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    ROUTE_UPDATE = "route_update"
    TOPOLOGY_UPDATE = "topology_update"
    DATA_FORWARD = "data_forward"
    ERROR = "error"


@dataclass
class NodeInfo:
    """Node information for mesh topology."""
    id: str
    address: str
    parent_id: Optional[str] = None
    children: List[str] = None
    hop_count: int = 0
    last_seen: Optional[datetime] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[int] = None
    is_gateway: bool = False
    capabilities: List[str] = None
    metadata: Dict[str, Any] = None

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
        if self.children is None:
            self.children = []
        if self.capabilities is None:
            self.capabilities = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SyncMessage:
    """Synchronization message structure."""
    id: str
    type: MessageType
    source_id: str
    dest_id: Optional[str] = None
    sequence: int = 0
    payload: Dict[str, Any] = None
    timestamp: datetime = None
    ttl: int = 10
    signature: Optional[str] = None

    def __post_init__(self):
        if self.payload is None:
            self.payload = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class RouteInfo:
    """Routing information."""
    destination: str
    next_hop: str
    hop_count: int
    cost: float
    last_updated: datetime
    is_active: bool = True


class MeshTopology:
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
    """Mesh network topology management."""

    def __init__(self):
        self.nodes: Dict[str, NodeInfo] = {}
        self.routes: Dict[str, RouteInfo] = {}
        self.graph = nx.Graph()
        self.gateway_nodes: Set[str] = set()
        self.max_hops = 15
        self.route_timeout = 300  # 5 minutes

    def add_node(self, node: NodeInfo) -> bool:
        """Add node to topology."""
        try:
            self.nodes[node.id] = node
            self.graph.add_node(node.id, **asdict(node)
            # Add edges for parent-child relationships
            if node.parent_id:
                self.graph.add_edge(node.parent_id, node.id)

            # Update gateway nodes
            if node.is_gateway:
                self.gateway_nodes.add(node.id)

            logger.info(f"Added node {node.id} to topology")
            return True

        except Exception as e:
            logger.error(f"Failed to add node {node.id}: {e}")
            return False

    def remove_node(self, node_id: str) -> bool:
        """Remove node from topology."""
        try:
            if node_id in self.nodes:
                # Remove children first
                children = self.nodes[node_id].children.copy()
                for child_id in children:
                    self.remove_node(child_id)

                # Remove from graph import graph
                self.graph.remove_node(node_id)

                # Remove from nodes dict
                del self.nodes[node_id]

                # Remove from gateway nodes
                self.gateway_nodes.discard(node_id)

                # Remove routes
                routes_to_remove = []
                for dest, route in self.routes.items():
                    if route.destination == node_id or route.next_hop == node_id:
                        routes_to_remove.append(dest)

                for dest in routes_to_remove:
                    del self.routes[dest]

                logger.info(f"Removed node {node_id} from topology")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to remove node {node_id}: {e}")
            return False

    def update_node(self, node_id: str, updates: Dict[str, Any]) -> bool:
        """Update node information."""
        try:
            if node_id not in self.nodes:
                return False

            node = self.nodes[node_id]

            # Apply updates
            for key, value in updates.items():
                if hasattr(node, key):
                    setattr(node, key, value)

            # Update graph
            self.graph.nodes[node_id].update(updates)

            # Update gateway nodes
            if "is_gateway" in updates:
                if updates["is_gateway"]:
                    self.gateway_nodes.add(node_id)
                else:
                    self.gateway_nodes.discard(node_id)

            logger.info(f"Updated node {node_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update node {node_id}: {e}")
            return False

    def find_route(self, source: str, destination: str) -> Optional[List[str]]:
        """Find route between nodes."""
        try:
            if source not in self.nodes or destination not in self.nodes:
                return None

            # Use NetworkX to find shortest path
            try:
                path = nx.shortest_path(self.graph, source, destination)
                return path
            except nx.NetworkXNoPath:
                return None

        except Exception as e:
            logger.error(f"Failed to find route from {source} to {destination}: {e}")
            return None

    def calculate_routes(self) -> Dict[str, RouteInfo]:
        """Calculate optimal routes for all nodes."""
        try:
            new_routes = {}

            # Calculate routes to all nodes from each gateway
            for gateway_id in self.gateway_nodes:
                try:
                    paths = nx.single_source_shortest_path(self.graph, gateway_id)

                    for dest_id, path in paths.items():
                        if dest_id != gateway_id:
                            route = RouteInfo(
                                destination=dest_id,
                                next_hop=path[1] if len(path) > 1 else dest_id,
                                hop_count=len(path) - 1,
                                cost=len(path) - 1,  # Simple cost based on hops
                                last_updated=datetime.utcnow()
                            new_routes[f"{gateway_id}:{dest_id}"] = route

                except Exception as e:
                    logger.error(f"Failed to calculate routes from gateway {gateway_id}: {e}")

            # Update routes
            self.routes.update(new_routes)

            # Clean up old routes
            self._cleanup_routes()

            logger.info(f"Calculated {len(new_routes)} routes")
            return new_routes

        except Exception as e:
            logger.error(f"Failed to calculate routes: {e}")
            return {}

    def _cleanup_routes(self):
        """Clean up old routes."""
        current_time = datetime.utcnow()
        routes_to_remove = []

        for route_id, route in self.routes.items():
            if (current_time - route.last_updated).total_seconds() > self.route_timeout:
                routes_to_remove.append(route_id)

        for route_id in routes_to_remove:
            del self.routes[route_id]

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighbor nodes."""
        try:
            if node_id in self.graph:
                return list(self.graph.neighbors(node_id)
            return []
        except Exception as e:
            logger.error(f"Failed to get neighbors for {node_id}: {e}")
            return []

    def get_topology_summary(self) -> Dict[str, Any]:
        """Get topology summary."""
        try:
            return {
                "total_nodes": len(self.nodes),
                "gateway_nodes": len(self.gateway_nodes),
                "total_routes": len(self.routes),
                "average_hops": self._calculate_average_hops(),
                "connectivity": self._calculate_connectivity(),
                "gateways": list(self.gateway_nodes),
                "isolated_nodes": self._find_isolated_nodes()
            }
        except Exception as e:
            logger.error(f"Failed to get topology summary: {e}")
            return {}

    def _calculate_average_hops(self) -> float:
        """Calculate average hop count."""
        if not self.routes:
            return 0.0

        total_hops = sum(route.hop_count for route in self.routes.values()
        return total_hops / len(self.routes)

    def _calculate_connectivity(self) -> float:
        """Calculate network connectivity."""
        if len(self.nodes) < 2:
            return 1.0

        try:
            # Calculate connectivity as ratio of connected components
            connected_components = list(nx.connected_components(self.graph)
            return len(connected_components) / len(self.nodes)
        except Exception:
            return 0.0

    def _find_isolated_nodes(self) -> List[str]:
        """Find isolated nodes."""
        try:
            isolated = []
            for node_id in self.nodes:
                if self.graph.degree(node_id) == 0:
                    isolated.append(node_id)
            return isolated
        except Exception:
            return []


class ArxLinkSyncProtocol:
    """ArxLink synchronization protocol implementation."""

    def __init__(self, node_id: str, address: str):
        self.node_id = node_id
        self.address = address
        self.topology = MeshTopology()
        self.state = SyncState.DISCOVERING
        self.sequence_number = 0
        self.message_queue = deque(maxlen=1000)
        self.pending_responses = {}
        self.last_sync_time = None
        self.sync_interval = 30  # seconds
        self.heartbeat_interval = 10  # seconds
        self.discovery_timeout = 60  # seconds
        self.max_retries = 3

        # Security
        self.session_key = None
        self.authenticated = False

        # Initialize node info
        self.node_info = NodeInfo(
            id=node_id,
            address=address,
            last_seen=datetime.utcnow(),
            capabilities=["sync", "route", "forward"],
            metadata={"version": "1.0", "protocol": "arxlink"}
        )

        # Add self to topology
        self.topology.add_node(self.node_info)

        # Start background tasks
        asyncio.create_task(self._heartbeat_loop()
        asyncio.create_task(self._sync_loop()
        asyncio.create_task(self._cleanup_loop()
    async def start(self):
        """Start the sync protocol."""
        logger.info(f"Starting ArxLink sync protocol for node {self.node_id}")

        # Start discovery
        await self._start_discovery()

        # Main event loop
        while True:
            try:
                await self._process_messages()
                await asyncio.sleep(0.1)  # Small delay
            except Exception as e:
                logger.error(f"Sync protocol error: {e}")
                await asyncio.sleep(1)

    async def _start_discovery(self):
        """Start node discovery process."""
        logger.info("Starting node discovery")
        self.state = SyncState.DISCOVERING

        # Send discovery broadcast
        discovery_msg = SyncMessage(
            id=str(uuid.uuid4()),
            type=MessageType.DISCOVERY,
            source_id=self.node_id,
            payload={
                "node_id": self.node_id,
                "address": self.address,
                "capabilities": self.node_info.capabilities,
                "battery_level": self.node_info.battery_level,
                "signal_strength": self.node_info.signal_strength
            }
        )

        await self._send_message(discovery_msg)

        # Wait for responses
        await asyncio.sleep(self.discovery_timeout)

        # Transition to connecting state
        self.state = SyncState.CONNECTING
        await self._establish_connections()

    async def _establish_connections(self):
        """Establish connections with discovered nodes."""
        logger.info("Establishing connections")

        # Find potential parent nodes
        potential_parents = self._find_potential_parents()

        for parent_id in potential_parents:
            if await self._connect_to_parent(parent_id):
                break

        # If no parent found, become gateway
        if not self.node_info.parent_id:
            self.node_info.is_gateway = True
            self.topology.update_node(self.node_id, {"is_gateway": True})
            logger.info(f"Node {self.node_id} became gateway")

        self.state = SyncState.CONNECTED
        logger.info("Connections established")

    def _find_potential_parents(self) -> List[str]:
        """Find potential parent nodes."""
        potential_parents = []

        for node_id, node in self.topology.nodes.items():
            if node_id != self.node_id:
                # Prefer gateway nodes as parents
                if node.is_gateway:
                    potential_parents.insert(0, node_id)
                else:
                    potential_parents.append(node_id)

        return potential_parents

    async def _connect_to_parent(self, parent_id: str) -> bool:
        """Connect to a parent node."""
        try:
            # Send connection request
            connect_msg = SyncMessage(
                id=str(uuid.uuid4()),
                type=MessageType.SYNC_REQUEST,
                source_id=self.node_id,
                dest_id=parent_id,
                payload={
                    "action": "connect",
                    "node_id": self.node_id,
                    "capabilities": self.node_info.capabilities
                }
            )

            response = await self._send_message_with_response(connect_msg)

            if response and response.type == MessageType.SYNC_RESPONSE:
                if response.payload.get("status") == "accepted":
                    # Update parent
                    self.node_info.parent_id = parent_id
                    self.topology.update_node(self.node_id, {"parent_id": parent_id})

                    # Update hop count
                    parent_hop_count = self.topology.nodes[parent_id].hop_count
                    self.node_info.hop_count = parent_hop_count + 1
                    self.topology.update_node(self.node_id, {"hop_count": self.node_info.hop_count})

                    # Update topology graph
                    self.topology.graph.add_edge(parent_id, self.node_id)

                    logger.info(f"Connected to parent {parent_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to connect to parent {parent_id}: {e}")
            return False

    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages."""
        while True:
            try:
                if self.state == SyncState.CONNECTED:
                    await self._send_heartbeat()

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def _sync_loop(self):
        """Perform periodic synchronization."""
        while True:
            try:
                if self.state == SyncState.CONNECTED:
                    await self._perform_sync()

                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Sync error: {e}")
                await asyncio.sleep(self.sync_interval)

    async def _cleanup_loop(self):
        """Clean up stale nodes and routes."""
        while True:
            try:
                await self._cleanup_stale_nodes()
                await asyncio.sleep(60)  # Cleanup every minute

            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(60)

    async def _send_heartbeat(self):
        """Send heartbeat message."""
        heartbeat_msg = SyncMessage(
            id=str(uuid.uuid4()),
            type=MessageType.HEARTBEAT,
            source_id=self.node_id,
            payload={
                "node_id": self.node_id,
                "battery_level": self.node_info.battery_level,
                "signal_strength": self.node_info.signal_strength,
                "hop_count": self.node_info.hop_count,
                "children_count": len(self.node_info.children)
            }
        )

        await self._send_message(heartbeat_msg)

    async def _perform_sync(self):
        """Perform network synchronization."""
        logger.info("Performing network sync")

        # Update topology
        self.topology.calculate_routes()

        # Send topology update
        topology_msg = SyncMessage(
            id=str(uuid.uuid4()),
            type=MessageType.TOPOLOGY_UPDATE,
            source_id=self.node_id,
            payload={
                "node_id": self.node_id,
                "parent_id": self.node_info.parent_id,
                "hop_count": self.node_info.hop_count,
                "children": self.node_info.children,
                "is_gateway": self.node_info.is_gateway,
                "topology_summary": self.topology.get_topology_summary()
            }
        )

        await self._send_message(topology_msg)

        # Update last sync time
        self.last_sync_time = datetime.utcnow()

    async def _send_message(self, message: SyncMessage) -> bool:
        """Send a message."""
        try:
            # Add to queue
            self.message_queue.append(message)

            # Update sequence number
            message.sequence = self.sequence_number
            self.sequence_number += 1

            # Add signature if authenticated
            if self.authenticated and self.session_key:
                message.signature = self._sign_message(message)

            # Convert to JSON
            message_json = json.dumps(asdict(message), default=str)

            # Send via RF (this would be implemented by the RF driver)
            await self._send_rf_message(message_json)

            logger.debug(f"Sent message {message.id} to {message.dest_id or 'broadcast'}")
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def _send_message_with_response(self, message: SyncMessage,
                                        timeout: float = 5.0) -> Optional[SyncMessage]:
        """Send message and wait for response."""
        try:
            # Add to pending responses
            self.pending_responses[message.id] = asyncio.Future()

            # Send message
            await self._send_message(message)

            # Wait for response
            response = await asyncio.wait_for(
                self.pending_responses[message.id],
                timeout=timeout
            )

            # Remove from pending import pending
            del self.pending_responses[message.id]

            return response

        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for response to message {message.id}")
            if message.id in self.pending_responses:
                del self.pending_responses[message.id]
            return None
        except Exception as e:
            logger.error(f"Error sending message with response: {e}")
            return None

    async def _send_rf_message(self, message_json: str):
        """Send message via RF (placeholder implementation)."""
        # This would interface with the RF hardware
        # For now, just log the message
        logger.debug(f"RF SEND: {message_json}")

        # Simulate RF transmission delay
        await asyncio.sleep(0.01)

    async def _receive_rf_message(self) -> Optional[str]:
        """Receive message via RF (placeholder implementation)."""
        # This would interface with the RF hardware
        # For now, return None (no messages)
        return None

    async def _process_messages(self):
        """Process incoming messages."""
        # Check for RF messages
        message_json = await self._receive_rf_message()

        if message_json:
            try:
                # Parse message
                message_dict = json.loads(message_json)
                message = SyncMessage(**message_dict)

                # Verify signature if present
                if message.signature and not self._verify_message_signature(message):
                    logger.warning(f"Invalid signature for message {message.id}")
                    return

                # Process message
                await self._handle_message(message)

            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    async def _handle_message(self, message: SyncMessage):
        """Handle incoming message."""
        try:
            # Update node info if it's from a neighbor'
            if message.source_id in self.topology.nodes:
                node = self.topology.nodes[message.source_id]
                node.last_seen = datetime.utcnow()

                if "battery_level" in message.payload:
                    node.battery_level = message.payload["battery_level"]
                if "signal_strength" in message.payload:
                    node.signal_strength = message.payload["signal_strength"]

            # Handle different message types
            if message.type == MessageType.DISCOVERY:
                await self._handle_discovery(message)
            elif message.type == MessageType.HEARTBEAT:
                await self._handle_heartbeat(message)
            elif message.type == MessageType.SYNC_REQUEST:
                await self._handle_sync_request(message)
            elif message.type == MessageType.SYNC_RESPONSE:
                await self._handle_sync_response(message)
            elif message.type == MessageType.ROUTE_UPDATE:
                await self._handle_route_update(message)
            elif message.type == MessageType.TOPOLOGY_UPDATE:
                await self._handle_topology_update(message)
            elif message.type == MessageType.DATA_FORWARD:
                await self._handle_data_forward(message)
            elif message.type == MessageType.ERROR:
                await self._handle_error(message)

        except Exception as e:
            logger.error(f"Failed to handle message {message.id}: {e}")

    async def _handle_discovery(self, message: SyncMessage):
        """Handle discovery message."""
        try:
            payload = message.payload
            node_id = payload["node_id"]
            address = payload["address"]

            # Add or update node in topology
            if node_id not in self.topology.nodes:
                node_info = NodeInfo(
                    id=node_id,
                    address=address,
                    last_seen=datetime.utcnow(),
                    capabilities=payload.get("capabilities", []),
                    battery_level=payload.get("battery_level"),
                    signal_strength=payload.get("signal_strength")
                self.topology.add_node(node_info)
                logger.info(f"Discovered node {node_id}")

            # Send discovery response
            response = SyncMessage(
                id=str(uuid.uuid4()),
                type=MessageType.DISCOVERY,
                source_id=self.node_id,
                dest_id=node_id,
                payload={
                    "node_id": self.node_id,
                    "address": self.address,
                    "capabilities": self.node_info.capabilities,
                    "battery_level": self.node_info.battery_level,
                    "signal_strength": self.node_info.signal_strength
                }
            )

            await self._send_message(response)

        except Exception as e:
            logger.error(f"Failed to handle discovery: {e}")

    async def _handle_heartbeat(self, message: SyncMessage):
        """Handle heartbeat message."""
        try:
            payload = message.payload
            node_id = payload["node_id"]

            # Update node information
            if node_id in self.topology.nodes:
                updates = {}
                if "battery_level" in payload:
                    updates["battery_level"] = payload["battery_level"]
                if "signal_strength" in payload:
                    updates["signal_strength"] = payload["signal_strength"]
                if "hop_count" in payload:
                    updates["hop_count"] = payload["hop_count"]

                self.topology.update_node(node_id, updates)

        except Exception as e:
            logger.error(f"Failed to handle heartbeat: {e}")

    async def _handle_sync_request(self, message: SyncMessage):
        """Handle sync request."""
        try:
            payload = message.payload
            action = payload.get("action")

            if action == "connect":
                # Handle connection request
                requesting_node_id = payload["node_id"]

                # Check if we can accept this connection
                can_accept = self._can_accept_connection(requesting_node_id)

                response = SyncMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.SYNC_RESPONSE,
                    source_id=self.node_id,
                    dest_id=requesting_node_id,
                    payload={
                        "status": "accepted" if can_accept else "rejected",
                        "reason": "capacity" if not can_accept else None
                    }
                )

                if can_accept:
                    # Add as child
                    self.node_info.children.append(requesting_node_id)
                    self.topology.update_node(self.node_id, {"children": self.node_info.children})

                    # Update topology graph
                    self.topology.graph.add_edge(self.node_id, requesting_node_id)

                await self._send_message(response)

        except Exception as e:
            logger.error(f"Failed to handle sync request: {e}")

    async def _handle_sync_response(self, message: SyncMessage):
        """Handle sync response."""
        try:
            # Check if this is a response to a pending request
            for request_id, future in self.pending_responses.items():
                if future.done():
                    continue

                # This is a simplified check - in practice you'd match request/response'
                future.set_result(message)
                break

        except Exception as e:
            logger.error(f"Failed to handle sync response: {e}")

    async def _handle_route_update(self, message: SyncMessage):
        """Handle route update."""
        try:
            payload = message.payload
            routes = payload.get("routes", [])

            for route_data in routes:
                route = RouteInfo(**route_data)
                route_id = f"{route.destination}:{route.next_hop}"
                self.topology.routes[route_id] = route

            logger.info(f"Updated {len(routes)} routes")

        except Exception as e:
            logger.error(f"Failed to handle route update: {e}")

    async def _handle_topology_update(self, message: SyncMessage):
        """Handle topology update."""
        try:
            payload = message.payload
            node_id = payload["node_id"]
            parent_id = payload.get("parent_id")
            hop_count = payload.get("hop_count", 0)
            children = payload.get("children", [])
            is_gateway = payload.get("is_gateway", False)

            # Update node information
            updates = {
                "parent_id": parent_id,
                "hop_count": hop_count,
                "children": children,
                "is_gateway": is_gateway
            }

            self.topology.update_node(node_id, updates)

            # Update topology graph
            if parent_id:
                self.topology.graph.add_edge(parent_id, node_id)

            logger.info(f"Updated topology for node {node_id}")

        except Exception as e:
            logger.error(f"Failed to handle topology update: {e}")

    async def _handle_data_forward(self, message: SyncMessage):
        """Handle data forwarding."""
        try:
            payload = message.payload
            destination = payload.get("destination")
            data = payload.get("data")

            # Check if we're the destination'
            if destination == self.node_id:
                # Process data locally
                await self._process_local_data(data)
            else:
                # Forward to next hop
                await self._forward_data(destination, data)

        except Exception as e:
            logger.error(f"Failed to handle data forward: {e}")

    async def _handle_error(self, message: SyncMessage):
        """Handle error message."""
        try:
            payload = message.payload
            error_code = payload.get("error_code")
            error_message = payload.get("error_message")

            logger.error(f"Received error from {message.source_id}: {error_code} - {error_message}")

        except Exception as e:
            logger.error(f"Failed to handle error: {e}")

    def _can_accept_connection(self, node_id: str) -> bool:
        """Check if we can accept a connection from a node."""
        # Simple capacity check - max 8 children
        return len(self.node_info.children) < 8

    async def _cleanup_stale_nodes(self):
        """Clean up stale nodes."""
        try:
            current_time = datetime.utcnow()
            stale_timeout = 300  # 5 minutes

            nodes_to_remove = []

            for node_id, node in self.topology.nodes.items():
                if node_id == self.node_id:
                    continue

                if node.last_seen and (current_time - node.last_seen).total_seconds() > stale_timeout:
                    nodes_to_remove.append(node_id)

            for node_id in nodes_to_remove:
                self.topology.remove_node(node_id)
                logger.info(f"Removed stale node {node_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup stale nodes: {e}")

    async def _process_local_data(self, data: Dict[str, Any]):
        """Process data locally."""
        logger.info(f"Processing local data: {data}")

        # Handle different data types
        data_type = data.get("type")

        if data_type == "sensor":
            await self._handle_sensor_data(data)
        elif data_type == "command":
            await self._handle_command_data(data)
        elif data_type == "status":
            await self._handle_status_data(data)

    async def _forward_data(self, destination: str, data: Dict[str, Any]):
        """Forward data to destination."""
        try:
            # Find route to destination
            route = self.topology.find_route(self.node_id, destination)

            if route and len(route) > 1:
                next_hop = route[1]

                # Create forward message
                forward_msg = SyncMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.DATA_FORWARD,
                    source_id=self.node_id,
                    dest_id=next_hop,
                    payload={
                        "destination": destination,
                        "data": data,
                        "original_source": self.node_id
                    }
                )

                await self._send_message(forward_msg)
                logger.info(f"Forwarded data to {destination} via {next_hop}")
            else:
                logger.warning(f"No route to {destination}")

        except Exception as e:
            logger.error(f"Failed to forward data: {e}")

    async def _handle_sensor_data(self, data: Dict[str, Any]):
        """Handle sensor data."""
        sensor_id = data.get("sensor_id")
        value = data.get("value")
        timestamp = data.get("timestamp")

        logger.info(f"Received sensor data from {sensor_id}: {value}")

        # Process sensor data (e.g., store, analyze, forward)
        # This would be implemented based on specific requirements

    async def _handle_command_data(self, data: Dict[str, Any]):
        """Handle command data."""
        command = data.get("command")
        parameters = data.get("parameters", {})

        logger.info(f"Received command: {command} with parameters: {parameters}")

        # Execute command
        # This would be implemented based on specific requirements

    async def _handle_status_data(self, data: Dict[str, Any]):
        """Handle status data."""
        status = data.get("status")
        details = data.get("details", {})

        logger.info(f"Received status update: {status}")

        # Process status update
        # This would be implemented based on specific requirements

    def _sign_message(self, message: SyncMessage) -> str:
        """Sign a message."""
        if not self.session_key:
            return ""

        # Create signature data
        signature_data = f"{message.id}:{message.type.value}:{message.source_id}:{message.sequence}"

        # Create HMAC signature
        signature = hmac.new(
            str(self.session_key).encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _verify_message_signature(self, message: SyncMessage) -> bool:
        """Verify message signature."""
        if not message.signature or not self.session_key:
            return True  # Allow unsigned messages if no session key

        expected_signature = self._sign_message(message)
        return message.signature == expected_signature

    def get_status(self) -> Dict[str, Any]:
        """Get protocol status."""
        return {
            "node_id": self.node_id,
            "state": self.state.value,
            "connected_nodes": len(self.topology.nodes) - 1,
            "routes": len(self.topology.routes),
            "is_gateway": self.node_info.is_gateway,
            "parent_id": self.node_info.parent_id,
            "hop_count": self.node_info.hop_count,
            "children_count": len(self.node_info.children),
            "battery_level": self.node_info.battery_level,
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "topology_summary": self.topology.get_topology_summary()
        }


# Example usage
async def main():
    """Example usage of ArxLink sync protocol."""
    # Create sync protocol instance
    sync_protocol = ArxLinkSyncProtocol("node_001", "192.168.1.100")

    # Start the protocol
    await sync_protocol.start()


if __name__ == "__main__":
    asyncio.run(main()
