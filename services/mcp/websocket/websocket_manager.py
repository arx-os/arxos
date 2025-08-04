#!/usr/bin/env python3
"""
WebSocket Manager for MCP Real-time Validation

This module provides real-time validation updates for CAD/BIM integration
through WebSocket connections. It manages multiple client connections
and broadcasts validation results as they occur.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    VALIDATION_UPDATE = "validation_update"
    VIOLATION_HIGHLIGHT = "violation_highlight"
    COMPLIANCE_SCORE = "compliance_score"
    RULE_CHECK = "rule_check"
    CONNECTION_STATUS = "connection_status"
    ERROR = "error"


@dataclass
class ValidationMessage:
    """Validation message structure"""
    type: MessageType
    building_id: str
    data: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None


class WebSocketManager:
    """Manages WebSocket connections for real-time validation"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.building_sessions: Dict[str, Dict[str, Any]] = {}
        self.validation_queue = asyncio.Queue()
        self.connection_count = 0
        self.logger = logging.getLogger(__name__)
        
    async def connect(self, websocket: WebSocket, building_id: str, session_id: Optional[str] = None):
        """Connect client to building validation stream"""
        try:
            await websocket.accept()
            
            if building_id not in self.active_connections:
                self.active_connections[building_id] = []
            
            self.active_connections[building_id].append(websocket)
            self.connection_count += 1
            
            # Initialize building session if needed
            if building_id not in self.building_sessions:
                self.building_sessions[building_id] = {
                    "connected_clients": 0,
                    "last_validation": None,
                    "validation_count": 0,
                    "session_id": session_id
                }
            
            self.building_sessions[building_id]["connected_clients"] += 1
            
            # Send connection confirmation
            await self.send_message(websocket, ValidationMessage(
                type=MessageType.CONNECTION_STATUS,
                building_id=building_id,
                data={
                    "status": "connected",
                    "building_id": building_id,
                    "session_id": session_id,
                    "connection_id": id(websocket)
                },
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            ))
            
            self.logger.info(f"Client connected to building {building_id} (total connections: {self.connection_count})")
            
        except Exception as e:
            self.logger.error(f"Error connecting client: {e}")
            raise
    
    async def disconnect(self, websocket: WebSocket, building_id: str):
        """Disconnect client from validation stream"""
        try:
            if building_id in self.active_connections:
                if websocket in self.active_connections[building_id]:
                    self.active_connections[building_id].remove(websocket)
                    self.connection_count -= 1
                    
                    # Update building session
                    if building_id in self.building_sessions:
                        self.building_sessions[building_id]["connected_clients"] -= 1
                        
                        # Clean up if no more connections
                        if self.building_sessions[building_id]["connected_clients"] <= 0:
                            del self.building_sessions[building_id]
                            del self.active_connections[building_id]
                    
                    self.logger.info(f"Client disconnected from building {building_id} (remaining connections: {self.connection_count})")
                    
        except Exception as e:
            self.logger.error(f"Error disconnecting client: {e}")
    
    async def send_message(self, websocket: WebSocket, message: ValidationMessage):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(asdict(message)))
        except WebSocketDisconnect:
            # Connection was closed, remove it
            building_id = message.building_id
            await self.disconnect(websocket, building_id)
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
    
    async def broadcast_validation(self, building_id: str, validation_data: dict, session_id: Optional[str] = None):
        """Broadcast validation updates to all connected clients for a building"""
        if building_id not in self.active_connections:
            return
        
        message = ValidationMessage(
            type=MessageType.VALIDATION_UPDATE,
            building_id=building_id,
            data=validation_data,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        
        # Update building session
        if building_id in self.building_sessions:
            self.building_sessions[building_id]["last_validation"] = message.timestamp
            self.building_sessions[building_id]["validation_count"] += 1
        
        # Broadcast to all connected clients
        disconnected_clients = []
        for connection in self.active_connections[building_id]:
            try:
                await connection.send_text(json.dumps(asdict(message)))
            except WebSocketDisconnect:
                disconnected_clients.append(connection)
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.append(connection)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            await self.disconnect(client, building_id)
        
        self.logger.info(f"Broadcasted validation update to {len(self.active_connections[building_id])} clients for building {building_id}")
    
    async def broadcast_violation_highlight(self, building_id: str, violation_data: dict, session_id: Optional[str] = None):
        """Broadcast specific violation highlights for CAD integration"""
        if building_id not in self.active_connections:
            return
        
        message = ValidationMessage(
            type=MessageType.VIOLATION_HIGHLIGHT,
            building_id=building_id,
            data=violation_data,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        
        # Broadcast to all connected clients
        for connection in self.active_connections[building_id]:
            try:
                await connection.send_text(json.dumps(asdict(message)))
            except WebSocketDisconnect:
                await self.disconnect(connection, building_id)
            except Exception as e:
                self.logger.error(f"Error broadcasting violation highlight: {e}")
    
    async def broadcast_compliance_score(self, building_id: str, compliance_data: dict, session_id: Optional[str] = None):
        """Broadcast compliance score updates"""
        if building_id not in self.active_connections:
            return
        
        message = ValidationMessage(
            type=MessageType.COMPLIANCE_SCORE,
            building_id=building_id,
            data=compliance_data,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        
        # Broadcast to all connected clients
        for connection in self.active_connections[building_id]:
            try:
                await connection.send_text(json.dumps(asdict(message)))
            except WebSocketDisconnect:
                await self.disconnect(connection, building_id)
            except Exception as e:
                self.logger.error(f"Error broadcasting compliance score: {e}")
    
    async def broadcast_rule_check(self, building_id: str, rule_data: dict, session_id: Optional[str] = None):
        """Broadcast individual rule check results"""
        if building_id not in self.active_connections:
            return
        
        message = ValidationMessage(
            type=MessageType.RULE_CHECK,
            building_id=building_id,
            data=rule_data,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        
        # Broadcast to all connected clients
        for connection in self.active_connections[building_id]:
            try:
                await connection.send_text(json.dumps(asdict(message)))
            except WebSocketDisconnect:
                await self.disconnect(connection, building_id)
            except Exception as e:
                self.logger.error(f"Error broadcasting rule check: {e}")
    
    async def broadcast_error(self, building_id: str, error_data: dict, session_id: Optional[str] = None):
        """Broadcast error messages to clients"""
        if building_id not in self.active_connections:
            return
        
        message = ValidationMessage(
            type=MessageType.ERROR,
            building_id=building_id,
            data=error_data,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        
        # Broadcast to all connected clients
        for connection in self.active_connections[building_id]:
            try:
                await connection.send_text(json.dumps(asdict(message)))
            except WebSocketDisconnect:
                await self.disconnect(connection, building_id)
            except Exception as e:
                self.logger.error(f"Error broadcasting error message: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": self.connection_count,
            "active_buildings": len(self.active_connections),
            "building_sessions": self.building_sessions,
            "connection_details": {
                building_id: len(connections) 
                for building_id, connections in self.active_connections.items()
            }
        }
    
    def get_building_connections(self, building_id: str) -> int:
        """Get number of active connections for a building"""
        return len(self.active_connections.get(building_id, []))
    
    async def close_all_connections(self):
        """Close all active WebSocket connections"""
        for building_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.close()
                except Exception as e:
                    self.logger.error(f"Error closing connection: {e}")
        
        self.active_connections.clear()
        self.building_sessions.clear()
        self.connection_count = 0
        self.logger.info("All WebSocket connections closed")


# Global WebSocket manager instance
websocket_manager = WebSocketManager() 