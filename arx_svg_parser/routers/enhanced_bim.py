"""
Enhanced BIM Router.

This router provides endpoints for enhanced BIM operations including:
- Advanced symbol recognition with machine learning
- Multi-system BIM model creation
- Custom element type support
- Enhanced geometry and relationship mapping
"""

from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from services.enhanced_bim_assembly import enhanced_bim_assembly
from services.enhanced_symbol_recognition import enhanced_symbol_recognition
from models.enhanced_bim_elements import (
    EnhancedBIMModel, System, SystemType, ElementCategory,
    HVACElement, ElectricalElement, PlumbingElement, FireSafetyElement,
    SecurityElement, NetworkElement, StructuralElement, LightingElement
)

router = APIRouter(prefix="/enhanced-bim", tags=["Enhanced BIM"])

# Request/Response Models
class EnhancedBIMParseRequest(BaseModel):
    svg_xml: str = Field(..., min_length=10, description="SVG content to parse")
    building_type: str = Field(default="office", description="Building type (office, residential, industrial)")
    name: Optional[str] = Field(default=None, description="Model name")
    description: Optional[str] = Field(default=None, description="Model description")
    user_id: str = Field(..., description="User performing the operation")
    project_id: str = Field(..., description="Project identifier")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Processing options")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "svg_xml": "<svg width='800' height='600'>...</svg>",
                "building_type": "office",
                "name": "Enhanced Office Building Model",
                "description": "Complete BIM model with all building systems",
                "user_id": "user_456",
                "project_id": "project_789",
                "options": {"enable_ml": True, "min_confidence": 0.7},
                "metadata": {"scale": "1:100", "units": "mm"}
            }
        }


class SymbolTrainingRequest(BaseModel):
    symbol_id: str = Field(..., description="Symbol identifier")
    training_data: List[Dict[str, Any]] = Field(..., description="Training examples")
    model_type: str = Field(default="svm", description="ML model type")
    user_id: str = Field(..., description="User training the model")
    project_id: str = Field(..., description="Project identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol_id": "custom_hvac_unit",
                "training_data": [
                    {"svg_path": "M 10 10 L 50 10 L 50 50 Z", "features": {"complexity": 0.3}},
                    {"svg_path": "M 20 20 L 60 20 L 60 60 Z", "features": {"complexity": 0.4}}
                ],
                "model_type": "svm",
                "user_id": "user_456",
                "project_id": "project_789"
            }
        }


class EnhancedBIMResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    model_id: str = Field(..., description="BIM model identifier")
    name: str = Field(..., description="Model name")
    description: Optional[str] = Field(default=None, description="Model description")
    building_type: str = Field(..., description="Building type")
    statistics: Dict[str, Any] = Field(..., description="Model statistics")
    systems_count: int = Field(..., description="Number of systems")
    elements_count: int = Field(..., description="Number of elements")
    connections_count: int = Field(..., description="Number of connections")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Model metadata")


class SymbolTrainingResponse(BaseModel):
    success: bool = Field(..., description="Training success status")
    symbol_id: str = Field(..., description="Symbol identifier")
    model_type: str = Field(..., description="ML model type")
    training_samples: int = Field(..., description="Number of training samples")
    model_accuracy: Optional[float] = Field(default=None, description="Model accuracy")
    created_at: datetime = Field(..., description="Training timestamp")


class RecognitionStatisticsResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    statistics: Dict[str, Any] = Field(..., description="Recognition statistics")
    assembly_statistics: Dict[str, Any] = Field(..., description="Assembly statistics")


# Enhanced BIM Operations
@router.post("/parse", response_model=EnhancedBIMResponse, status_code=status.HTTP_201_CREATED)
async def parse_svg_to_enhanced_bim(request: EnhancedBIMParseRequest):
    """
    Parse SVG content and create enhanced BIM model with multiple systems.
    
    Creates a comprehensive BIM model with HVAC, electrical, plumbing,
    fire safety, security, network, and lighting systems.
    """
    try:
        # Prepare options
        options = request.options or {}
        options.update({
            "building_type": request.building_type,
            "name": request.name or f"Enhanced {request.building_type.title()} Model",
            "description": request.description,
            "user_id": request.user_id,
            "project_id": request.project_id,
            "metadata": request.model_metadata
        })
        
        # Assemble enhanced BIM
        model = enhanced_bim_assembly.assemble_enhanced_bim(request.svg_xml, options)
        
        # Get statistics
        stats = model.get_statistics()
        
        return EnhancedBIMResponse(
            success=True,
            model_id=model.id,
            name=model.name,
            description=model.description,
            building_type=request.building_type,
            statistics=stats,
            systems_count=stats["total_systems"],
            elements_count=stats["total_elements"],
            connections_count=stats["total_connections"],
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.model_metadata
        )
        
    except Exception as e:
        logging.error(f"Enhanced BIM parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced BIM parsing failed: {str(e)}"
        )


@router.post("/train-symbol", response_model=SymbolTrainingResponse, status_code=status.HTTP_201_CREATED)
async def train_custom_symbol(request: SymbolTrainingRequest):
    """
    Train a custom symbol recognition model.
    
    Allows users to train machine learning models for custom symbol recognition
    to improve accuracy for specific building types or symbols.
    """
    try:
        # Train the custom symbol model
        success = enhanced_symbol_recognition.train_custom_symbol(
            symbol_id=request.symbol_id,
            training_data=request.training_data,
            model_type=request.model_type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to train custom symbol model"
            )
        
        return SymbolTrainingResponse(
            success=True,
            symbol_id=request.symbol_id,
            model_type=request.model_type,
            training_samples=len(request.training_data),
            model_accuracy=0.85,  # Placeholder accuracy
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Symbol training failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Symbol training failed: {str(e)}"
        )


@router.post("/add-symbol")
async def add_symbol_to_library(
    symbol_id: str = Query(..., description="Symbol identifier"),
    symbol_data: Dict[str, Any] = Query(..., description="Symbol data"),
    user_id: str = Query(..., description="User adding the symbol"),
    project_id: str = Query(..., description="Project identifier")
):
    """
    Add a new symbol to the symbol library.
    
    Allows users to add custom symbols to the recognition library
    for improved symbol detection.
    """
    try:
        success = enhanced_symbol_recognition.add_symbol_to_library(symbol_id, symbol_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add symbol to library"
            )
        
        return {
            "success": True,
            "symbol_id": symbol_id,
            "message": "Symbol added to library successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Symbol addition failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Symbol addition failed: {str(e)}"
        )


@router.get("/statistics", response_model=RecognitionStatisticsResponse)
async def get_enhanced_statistics():
    """
    Get enhanced BIM recognition and assembly statistics.
    
    Returns comprehensive statistics about the enhanced symbol recognition
    and BIM assembly systems.
    """
    try:
        recognition_stats = enhanced_symbol_recognition.get_recognition_statistics()
        assembly_stats = enhanced_bim_assembly.get_assembly_statistics()
        
        return RecognitionStatisticsResponse(
            success=True,
            statistics=recognition_stats,
            assembly_statistics=assembly_stats
        )
        
    except Exception as e:
        logging.error(f"Statistics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistics retrieval failed: {str(e)}"
        )


@router.get("/supported-systems")
async def get_supported_systems():
    """
    Get list of supported building systems and element categories.
    
    Returns information about all supported building systems and
    their element categories for enhanced BIM modeling.
    """
    try:
        return {
            "success": True,
            "systems": {
                "hvac": {
                    "name": "HVAC System",
                    "description": "Heating, Ventilation, and Air Conditioning",
                    "categories": [cat.value for cat in ElementCategory if "HVAC" in cat.name or cat.name in ["AIR_HANDLER", "VAV_BOX", "DUCT", "DIFFUSER", "THERMOSTAT", "CHILLER", "BOILER", "COOLING_TOWER", "HEAT_EXCHANGER"]]
                },
                "electrical": {
                    "name": "Electrical System",
                    "description": "Electrical power and distribution",
                    "categories": [cat.value for cat in ElementCategory if cat.name in ["PANEL", "CIRCUIT", "OUTLET", "SWITCH", "LIGHTING_FIXTURE", "TRANSFORMER", "GENERATOR", "UPS"]]
                },
                "plumbing": {
                    "name": "Plumbing System",
                    "description": "Water supply and drainage",
                    "categories": [cat.value for cat in ElementCategory if cat.name in ["PIPE", "VALVE", "PUMP", "TANK", "FIXTURE", "DRAIN", "VENT"]]
                },
                "fire_safety": {
                    "name": "Fire Safety System",
                    "description": "Fire detection and suppression",
                    "categories": [cat.value for cat in ElementCategory if cat.name in ["SPRINKLER", "SMOKE_DETECTOR", "HEAT_DETECTOR", "PULL_STATION", "HORN_STROBE", "FIRE_DAMPER"]]
                },
                "security": {
                    "name": "Security System",
                    "description": "Building security and access control",
                    "categories": [cat.value for cat in ElementCategory if cat.name in ["CAMERA", "ACCESS_CONTROL", "MOTION_DETECTOR", "DOOR_CONTACT", "GLASS_BREAK", "CARD_READER"]]
                },
                "network": {
                    "name": "Network System",
                    "description": "IT and communication network",
                    "categories": [cat.value for cat in ElementCategory if cat.name in ["ROUTER", "SWITCH", "SERVER", "ACCESS_POINT", "CABLE", "PATCH_PANEL"]]
                },
                "structural": {
                    "name": "Structural System",
                    "description": "Building structure and load-bearing elements",
                    "categories": [cat.value for cat in ElementCategory if cat.name in ["WALL", "COLUMN", "BEAM", "SLAB", "FOUNDATION", "ROOF"]]
                },
                "lighting": {
                    "name": "Lighting System",
                    "description": "Building lighting and emergency lighting",
                    "categories": [cat.value for cat in ElementCategory if cat.name in ["LIGHT", "EMERGENCY_LIGHT", "EXIT_SIGN", "DIMMER", "SENSOR"]]
                }
            },
            "building_types": ["office", "residential", "industrial"],
            "ml_models": ["svm", "random_forest", "neural_network", "knn"]
        }
        
    except Exception as e:
        logging.error(f"Supported systems retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supported systems retrieval failed: {str(e)}"
        )


@router.get("/health")
async def enhanced_bim_health_check():
    """
    Health check for enhanced BIM service.
    
    Returns service status and basic statistics.
    """
    try:
        recognition_stats = enhanced_symbol_recognition.get_recognition_statistics()
        assembly_stats = enhanced_bim_assembly.get_assembly_statistics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "enhanced_symbol_recognition": "available",
                "enhanced_bim_assembly": "available"
            },
            "statistics": {
                "total_symbols": recognition_stats.get("total_symbols", 0),
                "ml_models": recognition_stats.get("ml_models", 0),
                "system_templates": assembly_stats.get("system_templates", 0)
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        } 