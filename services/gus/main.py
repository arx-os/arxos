"""
GUS (General User Support) Agent Main Application

FastAPI application providing the GUS agent service with natural language
processing, knowledge management, and CAD assistance capabilities.
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

from core.agent import GUSAgent, GUSResponse
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


class QueryRequest(BaseModel):
    """Request model for GUS queries"""

    query: str
    user_id: str
    context: Dict[str, Any] = {}
    session_id: str = None


class TaskRequest(BaseModel):
    """Request model for GUS task execution"""

    task: str
    parameters: Dict[str, Any]
    user_id: str


class KnowledgeRequest(BaseModel):
    """Request model for knowledge queries"""

    topic: str
    context: Dict[str, Any] = {}


# Global GUS agent instance
gus_agent: GUSAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global gus_agent

    # Startup
    logger.info("Starting GUS Agent service...")

    try:
        # Initialize GUS agent
        settings = get_settings()
        gus_agent = GUSAgent(settings.dict())
        logger.info("GUS Agent initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to initialize GUS Agent: {e}")
        raise

    finally:
        # Shutdown
        logger.info("Shutting down GUS Agent service...")
        if gus_agent:
            await gus_agent.shutdown()


# Create FastAPI application
app = FastAPI(
    title="GUS (General User Support) Agent",
    description="AI agent for Arxos platform providing CAD assistance and knowledge management",
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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gus-agent", "version": "1.0.0"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "GUS (General User Support) Agent",
        "version": "1.0.0",
        "description": "AI agent for Arxos platform",
        "endpoints": {
            "/health": "Health check",
            "/docs": "API documentation",
            "/api/v1/query": "Process natural language queries",
            "/api/v1/task": "Execute specific tasks",
            "/api/v1/knowledge": "Query knowledge base",
        },
    }


# Query processing endpoint
@app.post("/api/v1/query")
async def process_query(request: QueryRequest):
    """Process a natural language query"""
    try:
        if not gus_agent:
            raise HTTPException(status_code=503, detail="GUS Agent not initialized")

        response = await gus_agent.process_query(
            query=request.query, user_id=request.user_id, context=request.context
        )

        return {
            "message": response.message,
            "confidence": response.confidence,
            "intent": response.intent,
            "entities": response.entities,
            "actions": response.actions,
            "timestamp": response.timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task execution endpoint
@app.post("/api/v1/task")
async def execute_task(request: TaskRequest):
    """Execute a specific task"""
    try:
        if not gus_agent:
            raise HTTPException(status_code=503, detail="GUS Agent not initialized")

        response = await gus_agent.execute_task(
            task=request.task, parameters=request.parameters, user_id=request.user_id
        )

        return {
            "message": response.message,
            "confidence": response.confidence,
            "intent": response.intent,
            "entities": response.entities,
            "actions": response.actions,
            "timestamp": response.timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge query endpoint
@app.post("/api/v1/knowledge")
async def query_knowledge(request: KnowledgeRequest):
    """Query the knowledge base"""
    try:
        if not gus_agent:
            raise HTTPException(status_code=503, detail="GUS Agent not initialized")

        response = await gus_agent.get_knowledge(
            topic=request.topic, context=request.context
        )

        return {
            "message": response.message,
            "confidence": response.confidence,
            "intent": response.intent,
            "entities": response.entities,
            "actions": response.actions,
            "timestamp": response.timestamp.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    # Get configuration
    settings = get_settings()

    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.gus_api_host,
        port=settings.gus_api_port,
        reload=settings.gus_dev_mode,
        log_level=settings.gus_log_level.lower(),
    )
