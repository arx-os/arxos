"""
Arx AI Services Main Application

FastAPI application providing AI/ML capabilities including GPT-based logic,
geometry validation, voice input, and AI agents for the Arxos platform.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

from core.ai_agent import AIAgent, AIResponse
from api.routes import router as api_router
from config.settings import get_settings


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
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


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


# Global AI agent instance
ai_agent: AIAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global ai_agent

    # Startup
    logger.info("Starting Arx AI Services...")

    try:
        # Initialize AI agent
        settings = get_settings()
        ai_agent = AIAgent(settings.model_dump())
        logger.info("AI Agent initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize AI Agent: {e}")
        raise

    finally:
        # Shutdown
        logger.info("Shutting down Arx AI Services...")
        if ai_agent:
            await ai_agent.shutdown()


# Create FastAPI application
app = FastAPI(
    title="Arx AI Services",
    description="AI/ML microservices for the Arxos platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "arx-ai-services",
        "version": "1.0.0",
        "ai_agent_ready": ai_agent is not None,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Arx AI Services",
        "version": "1.0.0",
        "endpoints": {"health": "/health", "api": "/api/v1", "docs": "/docs"},
    }


@app.post("/api/v1/query")
async def process_ai_query(request: AIQueryRequest):
    """Process AI queries using GPT-based logic"""
    try:
        if not ai_agent:
            raise HTTPException(status_code=503, detail="AI Agent not initialized")

        response = await ai_agent.process_query(
            query=request.query,
            user_id=request.user_id,
            context=request.context,
            session_id=request.session_id,
            model=request.model,
        )

        return response.model_dump()

    except Exception as e:
        logger.error(f"Error processing AI query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/geometry/validate")
async def validate_geometry(request: GeometryValidationRequest):
    """Validate geometry using AI-powered analysis"""
    try:
        if not ai_agent:
            raise HTTPException(status_code=503, detail="AI Agent not initialized")

        response = await ai_agent.validate_geometry(
            geometry_data=request.geometry_data,
            validation_type=request.validation_type,
            user_id=request.user_id,
        )

        return response.model_dump()

    except Exception as e:
        logger.error(f"Error validating geometry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/voice/process")
async def process_voice_input(request: VoiceInputRequest):
    """Process voice input and convert to text"""
    try:
        if not ai_agent:
            raise HTTPException(status_code=503, detail="AI Agent not initialized")

        response = await ai_agent.process_voice_input(
            audio_data=request.audio_data,
            user_id=request.user_id,
            language=request.language,
        )

        return response.model_dump()

    except Exception as e:
        logger.error(f"Error processing voice input: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agent/task")
async def execute_agent_task(request: AgentTaskRequest):
    """Execute AI agent tasks"""
    try:
        if not ai_agent:
            raise HTTPException(status_code=503, detail="AI Agent not initialized")

        response = await ai_agent.execute_task(
            task=request.task,
            parameters=request.parameters,
            user_id=request.user_id,
            agent_type=request.agent_type,
        )

        return response.model_dump()

    except Exception as e:
        logger.error(f"Error executing agent task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
