"""
MCP-Engineering API Routes

Provides REST API endpoints for MCP-Engineering integration with the Arxos platform.
This module handles engineering validation, compliance checking, and AI-powered recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json
import logging
import asyncio
from uuid import uuid4

from api.dependencies import (
    get_current_user,
    require_read_permission,
    require_write_permission,
)
from application.logging_config import get_logger
from application.services.mcp_engineering_service import MCPEngineeringService
from domain.mcp_engineering_entities import (
    BuildingData,
    ValidationType,
    ValidationStatus,
    IssueSeverity,
    SuggestionType,
    ReportType,
    ReportFormat,
)

logger = get_logger("api.mcp_engineering_routes")

# Initialize router
router = APIRouter(prefix="/mcp", tags=["MCP Engineering"])

# Initialize MCP-Engineering service
try:
    mcp_service = MCPEngineeringService()
except RuntimeError as e:
    if "Repository factory not initialized" in str(e):
        # For testing purposes, create a mock service
        mcp_service = None
        logger.warning(
            "Repository factory not initialized - using mock service for testing"
        )
    else:
        raise


# WebSocket connection manager for real-time validation updates
class MCPConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.validation_sessions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"MCP Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            # Remove from all validation sessions
            for session_id, clients in self.validation_sessions.items():
                if client_id in clients:
                    clients.remove(client_id)
            logger.info(f"MCP Client {client_id} disconnected")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast_to_session(self, message: str, session_id: str):
        if session_id in self.validation_sessions:
            for client_id in self.validation_sessions[session_id]:
                await self.send_personal_message(message, client_id)

    def join_validation_session(self, client_id: str, session_id: str):
        if session_id not in self.validation_sessions:
            self.validation_sessions[session_id] = []
        if client_id not in self.validation_sessions[session_id]:
            self.validation_sessions[session_id].append(client_id)
        logger.info(f"Client {client_id} joined validation session {session_id}")


mcp_manager = MCPConnectionManager()

# Pydantic models for MCP-Engineering API


class BuildingData(BaseModel):
    """Building data for validation"""

    area: float = Field(..., description="Building area in square feet")
    height: float = Field(..., description="Building height in feet")
    type: str = Field(
        ..., description="Building type (residential, commercial, industrial)"
    )
    occupancy: Optional[str] = Field(None, description="Occupancy classification")
    floors: Optional[int] = Field(None, description="Number of floors")
    jurisdiction: Optional[str] = Field(None, description="Building jurisdiction")


class ValidationRequest(BaseModel):
    """Request model for building validation"""

    building_data: BuildingData = Field(..., description="Building data for validation")
    validation_type: str = Field(
        ...,
        description="Type of validation (structural, electrical, mechanical, plumbing, fire, accessibility)",
    )
    include_suggestions: bool = Field(
        True, description="Include AI-powered suggestions"
    )
    confidence_threshold: float = Field(
        0.7, description="Minimum confidence threshold for AI suggestions"
    )


class ValidationResponse(BaseModel):
    """Response model for building validation"""

    validation_result: str = Field(
        ..., description="Validation result (pass, fail, warning)"
    )
    issues: List[Dict[str, Any]] = Field(
        default=[], description="Compliance issues found"
    )
    suggestions: List[Dict[str, Any]] = Field(
        default=[], description="AI-powered suggestions"
    )
    confidence_score: float = Field(..., description="Overall confidence score")
    timestamp: datetime = Field(..., description="Validation timestamp")


class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge base search"""

    query: str = Field(..., description="Search query")
    code_standard: Optional[str] = Field(
        None, description="Building code standard (IBC, NEC, ASHRAE, etc.)"
    )
    max_results: int = Field(5, description="Maximum number of results")


class KnowledgeSearchResponse(BaseModel):
    """Response model for knowledge base search"""

    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")


class MLValidationRequest(BaseModel):
    """Request model for ML-powered validation"""

    building_data: BuildingData = Field(
        ..., description="Building data for ML validation"
    )
    validation_type: str = Field(..., description="Type of ML validation")
    include_confidence: bool = Field(True, description="Include confidence scores")
    model_version: Optional[str] = Field(None, description="ML model version to use")


class MLValidationResponse(BaseModel):
    """Response model for ML-powered validation"""

    prediction: str = Field(..., description="ML prediction result")
    confidence: float = Field(..., description="Prediction confidence score")
    features: List[Dict[str, Any]] = Field(default=[], description="Feature importance")
    model_version: str = Field(..., description="ML model version used")


class ReportGenerationRequest(BaseModel):
    """Request model for report generation"""

    building_data: BuildingData = Field(..., description="Building data for report")
    validation_results: List[ValidationResponse] = Field(
        ..., description="Validation results to include"
    )
    report_type: str = Field(
        "comprehensive", description="Report type (comprehensive, summary, technical)"
    )
    format: str = Field("pdf", description="Report format (pdf, html, json)")


class ReportGenerationResponse(BaseModel):
    """Response model for report generation"""

    report_id: str = Field(..., description="Generated report ID")
    download_url: str = Field(..., description="Report download URL")
    report_type: str = Field(..., description="Report type")
    format: str = Field(..., description="Report format")
    generated_at: datetime = Field(..., description="Report generation timestamp")


# API Endpoints


@router.post("/validate", response_model=ValidationResponse)
async def validate_building(
    request: ValidationRequest, current_user=Depends(get_current_user)
):
    """Validate building against building codes"""
    try:
        # Convert request to domain entities
        building_data = BuildingData(
            area=request.building_data.area,
            height=request.building_data.height,
            building_type=request.building_data.type,
            occupancy=request.building_data.occupancy,
            floors=request.building_data.floors,
            jurisdiction=request.building_data.jurisdiction,
        )

        # Perform validation using application service
        validation_result = await mcp_service.validate_building(
            building_data=building_data.__dict__,
            validation_type=request.validation_type,
            user=current_user,
            include_suggestions=request.include_suggestions,
            confidence_threshold=request.confidence_threshold,
        )

        return ValidationResponse(**validation_result)

    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail="Validation failed")


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_base(
    request: KnowledgeSearchRequest, current_user=Depends(get_current_user)
):
    """Search building codes knowledge base"""
    try:
        # Perform knowledge base search using application service
        search_results = await mcp_service.search_knowledge_base(
            query=request.query,
            code_standard=request.code_standard,
            max_results=request.max_results,
            user=current_user,
        )

        return KnowledgeSearchResponse(**search_results)

    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        raise HTTPException(status_code=500, detail="Knowledge search failed")


@router.post("/ml/validate", response_model=MLValidationResponse)
async def ml_validate_building(
    request: MLValidationRequest, current_user=Depends(get_current_user)
):
    """Perform ML-powered building validation"""
    try:
        # Convert request to domain entities
        building_data = BuildingData(
            area=request.building_data.area,
            height=request.building_data.height,
            building_type=request.building_data.type,
            occupancy=request.building_data.occupancy,
            floors=request.building_data.floors,
            jurisdiction=request.building_data.jurisdiction,
        )

        # Perform ML validation using application service
        ml_result = await mcp_service.ml_validate_building(
            building_data=building_data.__dict__,
            validation_type=request.validation_type,
            include_confidence=request.include_confidence,
            model_version=request.model_version,
            user=current_user,
        )

        return MLValidationResponse(**ml_result)

    except Exception as e:
        logger.error(f"ML validation error: {e}")
        raise HTTPException(status_code=500, detail="ML validation failed")


@router.post("/reports/generate", response_model=ReportGenerationResponse)
async def generate_report(
    request: ReportGenerationRequest, current_user=Depends(get_current_user)
):
    """Generate professional compliance report"""
    try:
        # Convert request to domain entities
        building_data = BuildingData(
            area=request.building_data.area,
            height=request.building_data.height,
            building_type=request.building_data.type,
            occupancy=request.building_data.occupancy,
            floors=request.building_data.floors,
            jurisdiction=request.building_data.jurisdiction,
        )

        # Generate report using application service
        report_result = await mcp_service.generate_report(
            building_data=building_data.__dict__,
            validation_results=request.validation_results,
            report_type=request.report_type,
            format=request.format,
            user=current_user,
        )

        return ReportGenerationResponse(**report_result)

    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail="Report generation failed")


@router.get("/reports/{report_id}/download")
async def download_report(report_id: str, current_user=Depends(get_current_user)):
    """Download generated report"""
    try:
        # TODO: Integrate with MCP-Engineering report service
        # For now, return mock response
        return {"message": f"Report {report_id} download endpoint"}
    except Exception as e:
        logger.error(f"Report download error: {e}")
        raise HTTPException(status_code=500, detail="Report download failed")


@router.get("/health")
async def health_check():
    """MCP-Engineering service health check"""
    return {
        "status": "healthy",
        "service": "mcp-engineering",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@router.get("/metrics")
async def get_metrics():
    """Get MCP-Engineering service metrics"""
    try:
        # Get metrics from application service
        metrics = await mcp_service.get_service_statistics()
        metrics["active_sessions"] = len(mcp_manager.active_connections)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.websocket("/ws/validation/{session_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, client_id: str):
    """WebSocket endpoint for real-time validation updates"""
    await mcp_manager.connect(websocket, client_id)
    mcp_manager.join_validation_session(client_id, session_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Process validation update
            if message.get("type") == "validation_request":
                # TODO: Process validation request
                response = {
                    "type": "validation_update",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "validation_result": "pass",
                    "issues": [],
                    "suggestions": [],
                }

                # Broadcast to all clients in session
                await mcp_manager.broadcast_to_session(json.dumps(response), session_id)

    except WebSocketDisconnect:
        mcp_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        mcp_manager.disconnect(client_id)
