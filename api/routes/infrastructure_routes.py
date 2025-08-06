"""
Arxos API - Infrastructure as Code Routes

Provides user-first endpoints for creating, retrieving, updating, deleting, and exporting
digital elements with micron precision. Includes GUS-specific endpoints for natural language
instructions and optimized export.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

from svgx_engine.services.infrastructure_as_code import (
    infrastructure_service,
    DigitalElement,
    ElementType,
    PrecisionLevel,
)
from svgx_engine.core.precision import precision_manager, PrecisionDisplayMode
from svgx_engine.core.primitives import Line, Arc, Circle, Rectangle, Polyline
from svgx_engine.core.constraints import (
    Constraint,
    ParallelConstraint,
    PerpendicularConstraint,
    EqualConstraint,
    FixedConstraint,
    ConstraintType,
)

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure as Code"])


# Pydantic models for API requests/responses
class CreateElementRequest(BaseModel):
    element_type: str
    position_x: float
    position_y: float
    position_z: float
    width: float
    height: float
    depth: float
    properties: Dict[str, Any] = Field(default_factory=dict)


class CreateCADElementRequest(BaseModel):
    element_type: str
    position_x: float
    position_y: float
    position_z: float
    width: float
    height: float
    depth: float
    properties: Dict[str, Any] = Field(default_factory=dict)
    primitives: List[Dict[str, Any]] = Field(default_factory=list)


class CreateConstraintRequest(BaseModel):
    constraint_type: str
    target_ids: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ElementResponse(BaseModel):
    id: str
    element_type: str
    position_x: str
    position_y: str
    position_z: str
    width: str
    height: str
    depth: str
    properties: Dict[str, Any]
    connections: List[str]
    constraints_count: int
    cad_primitives_count: int
    created_at: str
    updated_at: str


class UpdateElementRequest(BaseModel):
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None


class ExportRequest(BaseModel):
    format_type: str = "svgx"  # svgx, instructions, json


class ExportResponse(BaseModel):
    content: str
    format_type: str
    element_count: int


class StatisticsResponse(BaseModel):
    total_elements: int
    element_types: Dict[str, int]
    total_cad_primitives: int
    total_constraints: int
    precision_level: str
    measurement_unit: str


class GUSElementRequest(BaseModel):
    instruction: str


class GUSElementResponse(BaseModel):
    element_id: str
    instruction: str
    success: bool
    message: str


@router.post("/elements", response_model=ElementResponse)
async def create_element(request: CreateElementRequest):
    """Create a new digital element with micron precision."""
    try:
        element_type = ElementType(request.element_type)
        element = infrastructure_service.create_element(
            element_type=element_type,
            position_x=request.position_x,
            position_y=request.position_y,
            position_z=request.position_z,
            width=request.width,
            height=request.height,
            depth=request.depth,
            properties=request.properties,
        )
        return _format_element_response(element)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid element type: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating element: {e}")


@router.post("/elements/cad", response_model=ElementResponse)
async def create_cad_element(request: CreateCADElementRequest):
    """Create a digital element with CAD primitives."""
    try:
        element_type = ElementType(request.element_type)

        # Convert primitive data to actual primitive objects
        primitives = []
        for prim_data in request.primitives:
            prim_type = prim_data.get("type")
            if prim_type == "line":
                primitive = Line(
                    start_x=Decimal(str(prim_data["start_x"])),
                    start_y=Decimal(str(prim_data["start_y"])),
                    end_x=Decimal(str(prim_data["end_x"])),
                    end_y=Decimal(str(prim_data["end_y"])),
                )
            elif prim_type == "circle":
                primitive = Circle(
                    center_x=Decimal(str(prim_data["center_x"])),
                    center_y=Decimal(str(prim_data["center_y"])),
                    radius=Decimal(str(prim_data["radius"])),
                )
            elif prim_type == "rectangle":
                primitive = Rectangle(
                    x=Decimal(str(prim_data["x"])),
                    y=Decimal(str(prim_data["y"])),
                    width=Decimal(str(prim_data["width"])),
                    height=Decimal(str(prim_data["height"])),
                )
            elif prim_type == "arc":
                primitive = Arc(
                    center_x=Decimal(str(prim_data["center_x"])),
                    center_y=Decimal(str(prim_data["center_y"])),
                    radius=Decimal(str(prim_data["radius"])),
                    start_angle=Decimal(str(prim_data["start_angle"])),
                    end_angle=Decimal(str(prim_data["end_angle"])),
                )
            elif prim_type == "polyline":
                points = [
                    {"x": Decimal(str(p["x"])), "y": Decimal(str(p["y"]))}
                    for p in prim_data["points"]
                ]
                primitive = Polyline(
                    points=points, closed=prim_data.get("closed", False)
                )
            else:
                raise ValueError(f"Unsupported primitive type: {prim_type}")

            primitives.append(primitive)

        element = infrastructure_service.create_cad_element(
            element_type=element_type,
            primitives=primitives,
            position_x=request.position_x,
            position_y=request.position_y,
            position_z=request.position_z,
            width=request.width,
            height=request.height,
            depth=request.depth,
            properties=request.properties,
        )
        return _format_element_response(element)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating CAD element: {e}")


@router.post("/elements/{element_id}/constraints")
async def add_constraint_to_element(element_id: str, request: CreateConstraintRequest):
    """Add a constraint to an existing element."""
    try:
        constraint_type = ConstraintType(request.constraint_type)

        if constraint_type == ConstraintType.PARALLEL:
            constraint = ParallelConstraint(request.target_ids, request.parameters)
        elif constraint_type == ConstraintType.PERPENDICULAR:
            constraint = PerpendicularConstraint(request.target_ids, request.parameters)
        elif constraint_type == ConstraintType.EQUAL:
            constraint = EqualConstraint(request.target_ids, request.parameters)
        elif constraint_type == ConstraintType.FIXED:
            constraint = FixedConstraint(request.target_ids, request.parameters)
        else:
            constraint = Constraint(
                constraint_type, request.target_ids, request.parameters, request.enabled
            )

        success = infrastructure_service.add_constraint_to_element(
            element_id, constraint
        )
        if not success:
            raise HTTPException(status_code=404, detail="Element not found")

        return {
            "message": f"Constraint {constraint_type.value} added to element {element_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid constraint type: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding constraint: {e}")


@router.get("/elements/{element_id}", response_model=ElementResponse)
async def get_element(element_id: str):
    """Get a specific element by ID."""
    element = infrastructure_service.get_element(element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")
    return _format_element_response(element)


@router.put("/elements/{element_id}", response_model=ElementResponse)
async def update_element(element_id: str, request: UpdateElementRequest):
    """Update an element's properties."""
    try:
        update_data = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        success = infrastructure_service.update_element(element_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Element not found")

        element = infrastructure_service.get_element(element_id)
        return _format_element_response(element)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating element: {e}")


@router.delete("/elements/{element_id}")
async def delete_element(element_id: str):
    """Delete an element."""
    success = infrastructure_service.delete_element(element_id)
    if not success:
        raise HTTPException(status_code=404, detail="Element not found")
    return {"message": f"Element {element_id} deleted"}


@router.get("/elements", response_model=List[ElementResponse])
async def list_elements(element_type: Optional[str] = None):
    """List all elements, optionally filtered by type."""
    try:
        if element_type:
            filter_type = ElementType(element_type)
            elements = infrastructure_service.list_elements(filter_type)
        else:
            elements = infrastructure_service.list_elements()

        return [_format_element_response(element) for element in elements]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid element type: {e}")


@router.post("/export", response_model=ExportResponse)
async def export_infrastructure(request: ExportRequest):
    """Export infrastructure data in specified format."""
    try:
        content = infrastructure_service.export_for_gus(request.format_type)
        element_count = len(infrastructure_service.elements)
        return ExportResponse(
            content=content,
            format_type=request.format_type,
            element_count=element_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting infrastructure: {e}"
        )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get infrastructure statistics."""
    stats = infrastructure_service.get_statistics()
    return StatisticsResponse(**stats)


@router.post("/import/svgx")
async def import_svgx(content: str):
    """Import elements from SVGX content."""
    try:
        infrastructure_service.import_from_svgx(content)
        return {
            "message": f"Imported {len(infrastructure_service.elements)} elements from SVGX"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing SVGX: {e}")


# GUS-compatible endpoints
@router.post("/gus/elements", response_model=GUSElementResponse)
async def gus_create_element(request: GUSElementRequest):
    """Create element from natural language instruction (GUS-compatible)."""
    try:
        # Simple parsing for now - can be enhanced with NLP
        parsed = _parse_gus_instruction(request.instruction)

        element = infrastructure_service.create_element(
            element_type=parsed["element_type"],
            position_x=parsed["position_x"],
            position_y=parsed["position_y"],
            position_z=parsed["position_z"],
            width=parsed["width"],
            height=parsed["height"],
            depth=parsed["depth"],
            properties=parsed.get("properties", {}),
        )

        return GUSElementResponse(
            element_id=element.id,
            instruction=request.instruction,
            success=True,
            message=f"Created {parsed['element_type'].value} element",
        )
    except Exception as e:
        return GUSElementResponse(
            element_id="",
            instruction=request.instruction,
            success=False,
            message=f"Error: {e}",
        )


@router.get("/gus/instructions")
async def gus_get_instructions():
    """Get natural language instructions for GUS."""
    instructions = infrastructure_service.to_gus_instructions()
    return {"instructions": instructions}


@router.post("/gus/export")
async def gus_export_infrastructure():
    """Export SVGX and instructions for GUS."""
    svgx_content = infrastructure_service.export_for_gus("svgx")
    instructions = infrastructure_service.to_gus_instructions()

    return {
        "svgx_content": svgx_content,
        "instructions": instructions,
        "element_count": len(infrastructure_service.elements),
    }


def _format_element_response(element: DigitalElement) -> ElementResponse:
    """Helper to format Decimal values for API response."""
    return ElementResponse(
        id=element.id,
        element_type=element.element_type.value,
        position_x=str(element.position_x),
        position_y=str(element.position_y),
        position_z=str(element.position_z),
        width=str(element.width),
        height=str(element.height),
        depth=str(element.depth),
        properties=element.properties,
        connections=element.connections,
        constraints_count=len(element.constraints),
        cad_primitives_count=len(element.cad_primitives),
        created_at=element.created_at.isoformat(),
        updated_at=element.updated_at.isoformat(),
    )


def _parse_gus_instruction(instruction: str) -> Dict[str, Any]:
    """Simple parsing for now - can be enhanced with NLP."""
    # Basic parsing - extract element type and basic properties
    words = instruction.lower().split()

    # Find element type
    element_types = [et.value for et in ElementType]
    element_type = None
    for word in words:
        if word in element_types:
            element_type = ElementType(word)
            break

    if not element_type:
        element_type = ElementType.WALL  # Default

    # Extract basic properties (simplified)
    return {
        "element_type": element_type,
        "position_x": 0.0,
        "position_y": 0.0,
        "position_z": 0.0,
        "width": 100.0,
        "height": 100.0,
        "depth": 100.0,
        "properties": {},
    }
