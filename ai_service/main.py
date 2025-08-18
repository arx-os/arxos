"""
Arxos AI Service - Confidence-Aware Building Intelligence
Following best practices: async, type hints, error handling, monitoring
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from models.arxobject import ArxObject, ConversionResult, ValidationData
from processors.pdf_processor import PDFProcessor
from processors.confidence_calculator import ConfidenceCalculator
from processors.validation_engine import ValidationEngine
from utils.config import settings
from utils.monitoring import setup_monitoring, track_conversion

# Configure structured logging
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with proper startup/shutdown"""
    # Startup
    logger.info("Starting Arxos AI Service", version=settings.VERSION)
    setup_monitoring()
    
    # Initialize processors
    app.state.pdf_processor = PDFProcessor()
    app.state.confidence_calculator = ConfidenceCalculator()
    app.state.validation_engine = ValidationEngine()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Arxos AI Service")
    # Cleanup resources if needed


# Create FastAPI app with best practices
app = FastAPI(
    title="Arxos AI Service",
    description="AI-powered building plan conversion with confidence scoring",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "arxos-ai",
        "version": settings.VERSION,
    }


@app.post("/api/v1/convert", response_model=ConversionResult)
async def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    building_type: Optional[str] = None,
    building_name: Optional[str] = None,
) -> ConversionResult:
    """
    Convert PDF floor plan to ArxObjects with confidence scoring
    
    Args:
        file: PDF file to convert
        building_type: Type of building (office, residential, hospital, etc.)
        building_name: Name of the building
        
    Returns:
        ConversionResult with ArxObjects and confidence scores
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Check file size (max 100MB)
    if file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 100MB")
    
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Process PDF with confidence scoring
        logger.info("Processing PDF", filename=file.filename, building_type=building_type)
        
        result = await app.state.pdf_processor.process(
            pdf_path=temp_path,
            building_type=building_type,
            building_name=building_name
        )
        
        # Track metrics
        background_tasks.add_task(
            track_conversion,
            building_type=building_type,
            object_count=len(result.arxobjects),
            confidence=result.overall_confidence,
            processing_time=result.processing_time
        )
        
        # Clean up temp file
        background_tasks.add_task(os.remove, temp_path)
        
        logger.info(
            "PDF conversion completed",
            objects_created=len(result.arxobjects),
            confidence=result.overall_confidence,
            duration=result.processing_time
        )
        
        return result
        
    except Exception as e:
        logger.error("PDF conversion failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@app.post("/api/v1/validate")
async def submit_validation(validation: ValidationData):
    """
    Submit field validation and propagate confidence improvements
    
    Args:
        validation: Field validation data
        
    Returns:
        Validation impact including cascaded updates
    """
    try:
        impact = await app.state.validation_engine.process_validation(validation)
        
        logger.info(
            "Validation processed",
            object_id=validation.object_id,
            confidence_improvement=impact.confidence_improvement,
            cascaded_objects=impact.cascaded_count
        )
        
        return impact
        
    except Exception as e:
        logger.error("Validation processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.post("/api/v1/analyze/quality")
async def analyze_pdf_quality(file: UploadFile = File(...)):
    """
    Analyze PDF quality and extractability before processing
    
    Args:
        file: PDF file to analyze
        
    Returns:
        Quality assessment with recommendations
    """
    try:
        # Save file temporarily
        temp_path = f"/tmp/quality_{file.filename}"
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Analyze quality
        quality = await app.state.pdf_processor.assess_quality(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return quality
        
    except Exception as e:
        logger.error("Quality analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/v1/patterns/{building_type}")
async def get_building_patterns(building_type: str):
    """
    Get learned patterns for a specific building type
    
    Args:
        building_type: Type of building
        
    Returns:
        Pattern library for the building type
    """
    patterns = app.state.validation_engine.get_patterns(building_type)
    if not patterns:
        raise HTTPException(status_code=404, detail=f"No patterns found for {building_type}")
    
    return patterns


if __name__ == "__main__":
    # Run with production-ready settings
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )