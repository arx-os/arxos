from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from arx_svg_parser.services.transform import (
    apply_affine_transform, 
    convert_to_real_world_coordinates,
    validate_coordinate_system,
    calculate_scale_factors,
    transform_coordinates_batch
)
from arx_svg_parser.models.scale import (
    AnchorPoint, 
    ScaleRequest, 
    ScaleResponse,
    RealWorldCoordinateRequest,
    RealWorldCoordinateResponse,
    ScaleValidationRequest,
    ScaleValidationResponse,
    CoordinateTransformRequest,
    CoordinateTransformResponse,
    CoordinateValidationResult
)
from arx_svg_parser.services.coordinate_validator import validate_coordinates, CoordinateValidationError

router = APIRouter()

@router.post("/scale", response_model=ScaleResponse)
def scale_svg(request: ScaleRequest):
    """
    Scale SVG using anchor points with enhanced validation and real-world coordinate support
    """
    try:
        # Validate anchor points
        if len(request.anchor_points) < 2:
            raise HTTPException(status_code=400, detail="At least two anchor points required for scaling")
        
        # Validate coordinate system
        validation_result = validate_coordinate_system(request.anchor_points)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Apply transformation
        anchor_points = [ap.dict() for ap in request.anchor_points]
        result = apply_affine_transform(request.svg_xml, anchor_points)
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return {"modified_svg": result}
        
    except CoordinateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/convert-to-real-world", response_model=RealWorldCoordinateResponse)
def convert_to_real_world(request: RealWorldCoordinateRequest):
    """
    Convert SVG coordinates to real-world coordinates using scale factors
    """
    try:
        # Validate scale factors
        if request.scale_x <= 0 or request.scale_y <= 0:
            raise HTTPException(status_code=400, detail="Scale factors must be positive")
        
        # Convert coordinates
        real_world_coords = convert_to_real_world_coordinates(
            request.svg_coordinates,
            request.scale_x,
            request.scale_y,
            request.origin_x,
            request.origin_y,
            request.units
        )
        
        return {
            "real_world_coordinates": real_world_coords,
            "units": request.units,
            "scale_factors": {"x": request.scale_x, "y": request.scale_y},
            "origin": {"x": request.origin_x, "y": request.origin_y}
        }
        
    except CoordinateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/validate-coordinates", response_model=ScaleValidationResponse)
def validate_coordinate_system_endpoint(request: ScaleValidationRequest):
    """
    Validate coordinate system and scale factors
    """
    try:
        # Validate anchor points
        anchor_points = [ap.dict() for ap in request.anchor_points]
        validation_result = validate_coordinate_system(anchor_points)
        
        # Calculate scale factors if validation passes
        scale_factors = None
        if validation_result["valid"]:
            scale_factors = calculate_scale_factors(anchor_points)
        
        return {
            "valid": validation_result["valid"],
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "scale_factors": scale_factors,
            "coordinate_system_info": validation_result.get("coordinate_system_info", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/transform-coordinates", response_model=CoordinateTransformResponse)
def transform_coordinates(request: CoordinateTransformRequest):
    """
    Transform coordinates between different coordinate systems
    """
    try:
        # Validate input coordinates
        if not request.coordinates:
            raise HTTPException(status_code=400, detail="No coordinates provided")
        
        # Transform coordinates
        transformed_coords = transform_coordinates_batch(
            request.coordinates,
            request.source_system,
            request.target_system,
            request.transformation_matrix
        )
        
        return {
            "transformed_coordinates": transformed_coords,
            "source_system": request.source_system,
            "target_system": request.target_system,
            "transformation_matrix": request.transformation_matrix
        }
        
    except CoordinateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/coordinate-systems")
def get_supported_coordinate_systems():
    """
    Get list of supported coordinate systems and their properties
    """
    coordinate_systems = {
        "svg": {
            "name": "SVG Coordinate System",
            "description": "Standard SVG coordinate system with origin at top-left",
            "units": "pixels",
            "origin": "top-left",
            "axes": "x-right, y-down"
        },
        "real_world_meters": {
            "name": "Real World (Meters)",
            "description": "Real-world coordinate system using meters",
            "units": "meters",
            "origin": "configurable",
            "axes": "x-east, y-north"
        },
        "real_world_feet": {
            "name": "Real World (Feet)",
            "description": "Real-world coordinate system using feet",
            "units": "feet",
            "origin": "configurable",
            "axes": "x-east, y-north"
        },
        "bim": {
            "name": "BIM Coordinate System",
            "description": "Building Information Modeling coordinate system",
            "units": "configurable",
            "origin": "project-specific",
            "axes": "x-east, y-north, z-up"
        }
    }
    
    return {"coordinate_systems": coordinate_systems}

@router.post("/calculate-scale-factors")
def calculate_scale_factors_endpoint(request: ScaleValidationRequest):
    """
    Calculate scale factors from anchor points
    """
    try:
        anchor_points = [ap.dict() for ap in request.anchor_points]
        
        # Validate anchor points
        validation_result = validate_coordinate_system(anchor_points)
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Calculate scale factors
        scale_factors = calculate_scale_factors(anchor_points)
        
        return {
            "scale_factors": scale_factors,
            "anchor_points": anchor_points,
            "validation": validation_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/validate-scale-request")
def validate_scale_request(request: ScaleRequest):
    """
    Validate a scale request without applying the transformation
    """
    try:
        # Validate anchor points
        anchor_points = [ap.dict() for ap in request.anchor_points]
        validation_result = validate_coordinate_system(anchor_points)
        
        # Validate SVG content
        svg_validation = validate_svg_content(request.svg_xml)
        
        return {
            "anchor_points_valid": validation_result["valid"],
            "svg_valid": svg_validation["valid"],
            "anchor_point_errors": validation_result.get("errors", []),
            "svg_errors": svg_validation.get("errors", []),
            "warnings": validation_result.get("warnings", []) + svg_validation.get("warnings", []),
            "recommendations": validation_result.get("recommendations", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def validate_svg_content(svg_xml: str) -> Dict[str, Any]:
    """
    Validate SVG content for scaling operations
    """
    errors = []
    warnings = []
    
    try:
        # Basic SVG structure validation
        if not svg_xml.strip().startswith("<svg"):
            errors.append("Invalid SVG format: must start with <svg tag")
        
        # Check for required SVG attributes
        if 'viewBox' not in svg_xml and ('width' not in svg_xml or 'height' not in svg_xml):
            warnings.append("SVG should have viewBox or width/height attributes for better scaling")
        
        # Check for unsupported elements
        unsupported_elements = ['defs', 'style', 'script', 'foreignObject']
        for element in unsupported_elements:
            if f"<{element}" in svg_xml:
                warnings.append(f"Element '{element}' may not scale properly")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"SVG validation failed: {str(e)}"],
            "warnings": warnings
        } 