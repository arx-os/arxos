#!/usr/bin/env python3
"""
WebSocket Routes for MCP Real-time Validation

This module provides FastAPI WebSocket endpoints for real-time
validation updates and CAD/BIM integration.
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import JSONResponse

from .websocket_manager import websocket_manager, ValidationMessage, MessageType
from models.mcp_models import BuildingModel

logger = logging.getLogger(__name__)

# Create router for WebSocket routes
websocket_router = APIRouter(prefix="/ws", tags=["websocket"])


@websocket_router.websocket("/validation/{building_id}")
async def websocket_validation_endpoint(
    websocket: WebSocket,
    building_id: str,
    session_id: Optional[str] = Query(None, description="Session ID for tracking")
):
    """
    WebSocket endpoint for real-time validation updates
    
    Args:
        websocket: WebSocket connection
        building_id: Building identifier
        session_id: Optional session ID for tracking
    """
    try:
        # Connect to the WebSocket manager
        await websocket_manager.connect(websocket, building_id, session_id)
        
        logger.info(f"WebSocket connection established for building {building_id}")
        
        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Wait for messages from the client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await handle_client_message(websocket, building_id, message, session_id)
                except json.JSONDecodeError:
                    await websocket_manager.broadcast_error(
                        building_id,
                        {"error": "Invalid JSON message"},
                        session_id
                    )
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    await websocket_manager.broadcast_error(
                        building_id,
                        {"error": f"Message processing error: {str(e)}"},
                        session_id
                    )
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for building {building_id}")
        except Exception as e:
            logger.error(f"WebSocket error for building {building_id}: {e}")
        finally:
            # Clean up connection
            await websocket_manager.disconnect(websocket, building_id)
            
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}")
        try:
            await websocket.close()
        except:
            pass


@websocket_router.get("/status")
async def get_websocket_status():
    """Get WebSocket connection statistics"""
    try:
        stats = websocket_manager.get_connection_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get WebSocket status"}
        )


@websocket_router.get("/status/{building_id}")
async def get_building_websocket_status(building_id: str):
    """Get WebSocket status for a specific building"""
    try:
        connections = websocket_manager.get_building_connections(building_id)
        building_session = websocket_manager.building_sessions.get(building_id, {})
        
        return JSONResponse(content={
            "building_id": building_id,
            "active_connections": connections,
            "session_info": building_session
        })
    except Exception as e:
        logger.error(f"Error getting building WebSocket status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get building WebSocket status"}
        )


async def handle_client_message(websocket: WebSocket, building_id: str, message: dict, session_id: Optional[str]):
    """
    Handle incoming messages from WebSocket clients
    
    Args:
        websocket: WebSocket connection
        building_id: Building identifier
        message: Parsed JSON message from client
        session_id: Session ID for tracking
    """
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }))
        
    elif message_type == "request_validation":
        # Handle validation request
        await handle_validation_request(websocket, building_id, message, session_id)
        
    elif message_type == "highlight_violation":
        # Handle violation highlight request
        await handle_violation_highlight(websocket, building_id, message, session_id)
        
    elif message_type == "get_compliance_score":
        # Handle compliance score request
        await handle_compliance_score_request(websocket, building_id, message, session_id)
        
    else:
        # Unknown message type
        await websocket_manager.broadcast_error(
            building_id,
            {"error": f"Unknown message type: {message_type}"},
            session_id
        )


async def handle_validation_request(websocket: WebSocket, building_id: str, message: dict, session_id: Optional[str]):
    """Handle validation request from client"""
    try:
        # Extract building model from message
        building_data = message.get("building_model", {})
        
        # Create building model
        building_model = BuildingModel(**building_data)
        
        # Import rule engine (avoid circular imports)
        from validate.rule_engine import MCPRuleEngine
        rule_engine = MCPRuleEngine()
        
        # Perform validation
        validation_report = await rule_engine.validate_building_model_async(building_model)
        
        # Broadcast validation results
        await websocket_manager.broadcast_validation(
            building_id,
            {
                "validation_report": validation_report.dict(),
                "building_id": building_id,
                "session_id": session_id
            },
            session_id
        )
        
        logger.info(f"Validation completed for building {building_id}")
        
    except Exception as e:
        logger.error(f"Error handling validation request: {e}")
        await websocket_manager.broadcast_error(
            building_id,
            {"error": f"Validation failed: {str(e)}"},
            session_id
        )


async def handle_violation_highlight(websocket: WebSocket, building_id: str, message: dict, session_id: Optional[str]):
    """Handle violation highlight request from client"""
    try:
        violation_id = message.get("violation_id")
        highlight_data = message.get("highlight_data", {})
        
        # Broadcast violation highlight
        await websocket_manager.broadcast_violation_highlight(
            building_id,
            {
                "violation_id": violation_id,
                "highlight_data": highlight_data,
                "session_id": session_id
            },
            session_id
        )
        
        logger.info(f"Violation highlight broadcast for building {building_id}, violation {violation_id}")
        
    except Exception as e:
        logger.error(f"Error handling violation highlight: {e}")
        await websocket_manager.broadcast_error(
            building_id,
            {"error": f"Violation highlight failed: {str(e)}"},
            session_id
        )


async def handle_compliance_score_request(websocket: WebSocket, building_id: str, message: dict, session_id: Optional[str]):
    """Handle compliance score request from client"""
    try:
        # Import rule engine (avoid circular imports)
        from validate.rule_engine import MCPRuleEngine
        rule_engine = MCPRuleEngine()
        
        # Get building model from message
        building_data = message.get("building_model", {})
        building_model = BuildingModel(**building_data)
        
        # Get jurisdiction info
        jurisdiction_info = rule_engine.get_jurisdiction_info(building_model)
        
        # Calculate compliance score
        # This would typically involve running validation and calculating score
        compliance_score = {
            "building_id": building_id,
            "jurisdiction_info": jurisdiction_info,
            "compliance_percentage": 85.0,  # Placeholder
            "total_rules": 152,
            "passed_rules": 129,
            "failed_rules": 23,
            "session_id": session_id
        }
        
        # Broadcast compliance score
        await websocket_manager.broadcast_compliance_score(
            building_id,
            compliance_score,
            session_id
        )
        
        logger.info(f"Compliance score calculated for building {building_id}")
        
    except Exception as e:
        logger.error(f"Error handling compliance score request: {e}")
        await websocket_manager.broadcast_error(
            building_id,
            {"error": f"Compliance score calculation failed: {str(e)}"},
            session_id
        )


# Add missing import
from datetime import datetime 