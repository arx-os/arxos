"""
AI Service Main Application

This module contains the FastAPI application for the AI service, following
Clean Architecture principles by keeping the presentation layer separate
from domain import domain

Presentation Layer:
- FastAPI application setup
- HTTP endpoint definitions
- Request/response models
- Error handling
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

# Import domain and application layers (framework independent)
from domain.entities.ai_agent import AIAgentConfig, ModelType
from application.use_cases.process_ai_query_use_case import (
    ProcessAIQueryUseCase, ProcessAIQueryRequest, ProcessAIQueryResponse
)
from infrastructure.ai_agent_impl import ConcreteAIAgent
from config.settings import get_settings
from core.security.auth_middleware import get_current_user, User


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Pydantic models for API requests/responses (Presentation Layer)
class AIQueryRequest(BaseModel):
    """Request model for AI queries"""
    query: str
    user_id: str
    context: Dict[str, Any] = {}
    session_id: str = None
    model: str = "gpt-4"


class GeometryValidationRequest(BaseModel):
    """Request model for geometry validation"""
    geometry_data: Dict[str, Any]
    validation_type: str = "comprehensive"
    user_id: str


class VoiceInputRequest(BaseModel):
    """Request model for voice input processing"""
    audio_data: str  # Base64 encoded audio
    user_id: str
    language: str = "en"


class AgentTaskRequest(BaseModel):
    """Request model for AI agent task execution"""
    task: str
    parameters: Dict[str, Any]
    user_id: str
    agent_type: str = "general"


# Global use case instance (dependency injection)
ai_query_use_case: ProcessAIQueryUseCase = None


@asynccontextmanager
    async def lifespan(app: FastAPI, user: User = Depends(get_current_user)):
    """Application lifespan manager"""
    global ai_query_use_case

    # Startup
    logger.info("Starting Arx AI Services...")

    try:
        # Initialize domain and application layers
        settings = get_settings()

        # Create domain configuration
        config = AIAgentConfig(
            model_type=ModelType.GPT_4,
            api_key=settings.openai_api_key,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            timeout=settings.timeout
        )

        # Create infrastructure implementation
        ai_agent = ConcreteAIAgent(config)

        # Create use case with dependency injection
        ai_query_use_case = ProcessAIQueryUseCase(ai_agent)

        logger.info("AI Service initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize AI Service: {e}")
        raise

    finally:
        # Shutdown
        logger.info("Shutting down Arx AI Services...")
        if ai_query_use_case and ai_query_use_case.ai_agent:
            ai_query_use_case.ai_agent.shutdown()


# Create FastAPI application
app = FastAPI(
    title="Arx AI Service",
    description="AI service for building information modeling",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
    async def health_check(user: User = Depends(get_current_user)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai",
        "version": "1.0.0"
    }


@app.get("/")
    async def root(user: User = Depends(get_current_user)):
    """Root endpoint"""
    return {
        "message": "Arx AI Service",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/v1/query",
            "/api/v1/geometry/validate",
            "/api/v1/voice/process",
            "/api/v1/agent/task"
        ]
    }


@app.post("/api/v1/query")
    async def process_ai_query(request: AIQueryRequest, user: User = Depends(get_current_user)):
    """
    Process AI query endpoint.

    This endpoint uses the use case to process AI queries while keeping
    the presentation layer separate from business logic.
    """
    try:
        # Convert API request to use case request
        use_case_request = ProcessAIQueryRequest(
            query=request.query,
            user_id=request.user_id,
            context=request.context,
            session_id=request.session_id,
            model=request.model
        )

        # Execute use case
        response = ai_query_use_case.execute(use_case_request)

        # Convert use case response to API response
        if response.success:
            return {
                "success": True,
                "response_id": response.response_id,
                "content": response.content,
                "confidence": response.confidence,
                "model_used": response.model_used,
                "processing_time": response.processing_time,
                "metadata": response.metadata
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=response.error_message
            )

    except Exception as e:
        logger.error(f"Error processing AI query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/geometry/validate")
    async def validate_geometry(request: GeometryValidationRequest, user: User = Depends(get_current_user)):
    """Validate geometry endpoint"""
    try:
        # TODO: Implement geometry validation use case
        return {
            "success": True,
            "valid": True,
            "issues": [],
            "message": "Geometry validation not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error validating geometry: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/voice/process")
    async def process_voice_input(request: VoiceInputRequest, user: User = Depends(get_current_user)):
    """Process voice input endpoint"""
    try:
        # TODO: Implement voice processing use case
        return {
            "success": True,
            "transcription": "Voice processing not yet implemented",
            "confidence": 0.0
        }
    except Exception as e:
        logger.error(f"Error processing voice input: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/agent/task")
    async def execute_agent_task(request: AgentTaskRequest, user: User = Depends(get_current_user)):
    """Execute agent task endpoint"""
    try:
        # TODO: Implement agent task use case
        return {
            "success": True,
            "task_id": "task-001",
            "result": "Agent task execution not yet implemented"
        }
    except Exception as e:
        logger.error(f"Error executing agent task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(Exception)
    async def global_exception_handler(request, exc, user: User = Depends(get_current_user)):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
