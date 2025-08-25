"""
Arxos AI Service - Field Worker Assistance
Main service for lightweight AI help during building mapping
"""

import logging
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import json

# Import our modules
from field_assistance import ComponentValidator, SuggestionEngine, QualityScorer
from ingestion import IngestionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Arxos AI Service",
    description="Lightweight AI assistance for field workers mapping buildings",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
component_validator = ComponentValidator()
suggestion_engine = SuggestionEngine()
quality_scorer = QualityScorer()
ingestion_manager = IngestionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Arxos AI Service...")
    logger.info(f"Available parsers: {ingestion_manager.get_available_parsers()}")
    logger.info(f"Supported formats: {ingestion_manager.get_supported_formats()}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Arxos AI Service",
        "version": "1.0.0",
        "parsers": ingestion_manager.get_available_parsers()
    }

# Field Assistance Endpoints

@app.post("/validate/component")
async def validate_component(component_data: Dict[str, Any]):
    """
    Validate field worker component input
    
    Args:
        component_data: Component data from field worker
        
    Returns:
        Validation result with status and suggestions
    """
    try:
        validation_result = await component_validator.validate_component(component_data)
        
        # Convert dataclass to dict for JSON serialization
        return {
            "is_valid": validation_result.is_valid,
            "confidence": validation_result.confidence,
            "suggestions": validation_result.suggestions,
            "warnings": validation_result.warnings,
            "errors": validation_result.errors
        }
        
    except Exception as e:
        logger.error(f"Component validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest/component")
async def suggest_component(
    input_data: Dict[str, Any],
    photo: Optional[UploadFile] = File(None)
):
    """
    Suggest component types based on field worker input
    
    Args:
        input_data: Field worker input (text, properties, etc.)
        photo: Optional photo for visual analysis
        
    Returns:
        List of component suggestions with confidence scores
    """
    try:
        # Convert photo to bytes if provided
        photo_data = None
        if photo:
            photo_data = await photo.read()
        
        suggestions = await suggestion_engine.suggest_component(input_data, photo_data)
        
        # Convert dataclasses to dicts for JSON serialization
        return [
            {
                "component_type": s.component_type,
                "confidence": s.confidence,
                "properties": s.properties,
                "reasoning": s.reasoning,
                "alternatives": s.alternatives
            }
            for s in suggestions
        ]
        
    except Exception as e:
        logger.error(f"Component suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score/quality")
async def score_quality(
    contribution_data: Dict[str, Any],
    validation_result: Optional[Dict[str, Any]] = None
):
    """
    Score field worker contribution for quality
    
    Args:
        contribution_data: The contribution data from field worker
        validation_result: Optional validation result from component validator
        
    Returns:
        Quality score with token reward and feedback
    """
    try:
        quality_score = await quality_scorer.score_contribution(
            contribution_data, validation_result
        )
        
        # Convert dataclass to dict for JSON serialization
        return {
            "overall_score": quality_score.overall_score,
            "token_reward": quality_score.token_reward,
            "breakdown": quality_score.breakdown,
            "feedback": quality_score.feedback,
            "timestamp": quality_score.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quality scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Ingestion Endpoints

@app.post("/ingest/building-plan")
async def ingest_building_plan(file: UploadFile = File(...)):
    """
    Ingest a building plan file (PDF, IFC, DWG, etc.)
    
    Args:
        file: Building plan file to process
        
    Returns:
        Parsed building plan data
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Check if file can be parsed
        if not await ingestion_manager.can_parse_file(temp_path):
            raise HTTPException(
                status_code=400, 
                detail=f"File format not supported. Supported formats: {ingestion_manager.get_supported_formats()}"
            )
        
        # Parse the building plan
        building_plan = await ingestion_manager.parse_building_plan(temp_path)
        
        # Convert to JSON-serializable format
        return {
            "building_name": building_plan.building_name,
            "floors": building_plan.floors,
            "rooms": building_plan.rooms,
            "elements_count": len(building_plan.elements),
            "dimensions": building_plan.dimensions,
            "scale_factor": building_plan.scale_factor,
            "source_format": building_plan.source_format,
            "metadata": building_plan.metadata
        }
        
    except Exception as e:
        logger.error(f"Building plan ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingest/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "supported_formats": ingestion_manager.get_supported_formats(),
        "available_parsers": ingestion_manager.get_available_parsers()
    }

@app.post("/ingest/validate-file")
async def validate_file(file: UploadFile = File(...)):
    """
    Validate a building plan file without parsing
    
    Args:
        file: Building plan file to validate
        
    Returns:
        Validation result
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate the file
        validation_result = await ingestion_manager.validate_file(temp_path)
        
        return validation_result
        
    except Exception as e:
        logger.error(f"File validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingest/parser-status")
async def get_parser_status():
    """Get status of all registered parsers"""
    return await ingestion_manager.get_parser_status()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )