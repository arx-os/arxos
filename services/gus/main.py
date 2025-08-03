"""
GUS Service Main Application

This module contains the FastAPI application for the GUS service, following
Clean Architecture principles by keeping the presentation layer separate
from domain logic.

Presentation Layer:
- FastAPI application setup
- HTTP endpoint definitions
- Request/response models
- Error handling
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

# Import domain and application layers (framework independent)
from domain.entities.gus_agent import GUSAgentConfig, QueryType
from application.use_cases.process_gus_query_use_case import (
    ProcessGUSQueryUseCase, ProcessGUSQueryRequest, ProcessGUSQueryResponse
)
from application.use_cases.execute_gus_task_use_case import (
    ExecuteGUSTaskUseCase, ExecuteGUSTaskRequest, ExecuteGUSTaskResponse
)
from infrastructure.gus_agent_impl import ConcreteGUSAgent
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


class PDFAnalysisRequest(BaseModel):
    """Request model for PDF analysis"""
    pdf_file_path: str
    requirements: Dict[str, Any] = {}
    user_id: str


# Global use case instances (dependency injection)
gus_query_use_case: ProcessGUSQueryUseCase = None
gus_task_use_case: ExecuteGUSTaskUseCase = None


@asynccontextmanager
    async def lifespan(app: FastAPI, user: User = Depends(get_current_user)):
    """Application lifespan manager"""
    global gus_query_use_case, gus_task_use_case
    
    # Startup
    logger.info("Starting GUS Agent service...")
    
    try:
        # Initialize domain and application layers
        settings = get_settings()
        
        # Create domain configuration
        config = GUSAgentConfig(
            model_type="gpt-4",
            api_key=settings.openai_api_key,
            knowledge_base_path=settings.knowledge_base_path,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            timeout=settings.timeout
        )
        
        # Create infrastructure implementation
        gus_agent = ConcreteGUSAgent(config)
        
        # Create use cases with dependency injection
        gus_query_use_case = ProcessGUSQueryUseCase(gus_agent)
        gus_task_use_case = ExecuteGUSTaskUseCase(gus_agent)
        
        logger.info("GUS Service initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize GUS Service: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down GUS Agent service...")
        if gus_query_use_case and gus_query_use_case.gus_agent:
            gus_query_use_case.gus_agent.shutdown()


# Create FastAPI application
app = FastAPI(
    title="GUS Agent Service",
    description="General User Support agent service for building information modeling",
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
        "service": "gus",
        "version": "1.0.0"
    }


@app.get("/")
    async def root(user: User = Depends(get_current_user)):
    """Root endpoint"""
    return {
        "message": "GUS Agent Service",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/v1/query",
            "/api/v1/task",
            "/api/v1/knowledge",
            "/api/v1/pdf_analysis",
            "/api/v1/pdf_upload"
        ]
    }


@app.post("/api/v1/query")
    async def process_query(request: QueryRequest, user: User = Depends(get_current_user)):
    """
    Process GUS query endpoint.
    
    This endpoint uses the use case to process GUS queries while keeping
    the presentation layer separate from business logic.
    """
    try:
        # Convert API request to use case request
        use_case_request = ProcessGUSQueryRequest(
            query=request.query,
            user_id=request.user_id,
            context=request.context,
            session_id=request.session_id
        )
        
        # Execute use case
        response = gus_query_use_case.execute(use_case_request)
        
        # Convert use case response to API response
        if response.success:
            return {
                "success": True,
                "response_id": response.response_id,
                "content": response.content,
                "confidence": response.confidence,
                "query_type": response.query_type,
                "processing_time": response.processing_time,
                "metadata": response.metadata
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=response.error_message
            )
            
    except Exception as e:
        logger.error(f"Error processing GUS query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/task")
    async def execute_task(request: TaskRequest, user: User = Depends(get_current_user)):
    """
    Execute GUS task endpoint.
    
    This endpoint uses the use case to execute GUS tasks while keeping
    the presentation layer separate from business logic.
    """
    try:
        # Convert API request to use case request
        use_case_request = ExecuteGUSTaskRequest(
            task=request.task,
            parameters=request.parameters,
            user_id=request.user_id
        )
        
        # Execute use case
        response = gus_task_use_case.execute(use_case_request)
        
        # Convert use case response to API response
        if response.success:
            return {
                "success": True,
                "task_id": response.task_id,
                "status": response.status,
                "result": response.result
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=response.error_message
            )
            
    except Exception as e:
        logger.error(f"Error executing GUS task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/knowledge")
    async def query_knowledge(request: KnowledgeRequest, user: User = Depends(get_current_user)):
    """Query knowledge endpoint"""
    try:
        # TODO: Implement knowledge query use case
        return {
            "success": True,
            "topic": request.topic,
            "content": "Knowledge query not yet implemented",
            "confidence": 0.0
        }
    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/pdf_analysis")
    async def analyze_pdf_for_schedule(request: PDFAnalysisRequest, user: User = Depends(get_current_user)):
    """Analyze PDF for schedule endpoint"""
    try:
        # TODO: Implement PDF analysis use case
        return {
            "success": True,
            "pdf_file_path": request.pdf_file_path,
            "analysis": "PDF analysis not yet implemented",
            "requirements_met": True
        }
    except Exception as e:
        logger.error(f"Error analyzing PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/v1/pdf_upload")
async def upload_and_analyze_pdf(
    file: UploadFile = File(...),
    user_id: str = None,
    requirements: Dict[str, Any] = {}
):
    """Upload and analyze PDF endpoint"""
    try:
        # TODO: Implement PDF upload and analysis use case
        return {
            "success": True,
            "filename": file.filename,
            "analysis": "PDF upload and analysis not yet implemented",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error uploading and analyzing PDF: {e}")
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