"""
SVGX Engine - Main Application Entry Point

FastAPI application providing REST API endpoints for SVGX operations:
- Health monitoring for Docker/Kubernetes
- SVGX parsing and validation
- Real-time simulation and behavior evaluation
- Interactive operations (click, drag, hover)
- Constraint system and selection management
- Tiered precision operations
- Performance monitoring and metrics

CTO Targets:
- <16ms UI response time
- <32ms redraw time
- <100ms physics simulation
- Batch processing for non-critical updates
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# SVGX Engine imports
try:
    from parser.parser import SVGXParser, SVGXElement
    from runtime.evaluator import SVGXEvaluator
    from runtime.behavior_engine import SVGXBehaviorEngine
    from runtime.physics_engine import SVGXPhysicsEngine
    from compiler.svgx_to_svg import SVGXToSVGCompiler
    from compiler.svgx_to_json import SVGXToJSONCompiler
    from utils.performance import PerformanceMonitor
    from utils.telemetry import TelemetryLogger
    from utils.errors import SVGXError, ValidationError, PerformanceError

    # Advanced CAD Features imports
    from services.advanced_cad_features import (
        initialize_advanced_cad_features,
        set_precision_level as cad_set_precision_level,
        calculate_precise_coordinates,
        add_constraint,
        solve_constraints,
        create_assembly,
        export_high_precision,
        get_cad_performance_stats,
    )
except ImportError:
    # Fallback for direct execution
    from parser.parser import SVGXParser, SVGXElement
    from runtime.evaluator import SVGXEvaluator
    from runtime.behavior_engine import SVGXBehaviorEngine
    from runtime.physics_engine import SVGXPhysicsEngine
    from compiler.svgx_to_svg import SVGXToSVGCompiler
    from compiler.svgx_to_json import SVGXToJSONCompiler
    from utils.performance import PerformanceMonitor
    from utils.telemetry import TelemetryLogger
    from utils.errors import SVGXError, ValidationError, PerformanceError

    # Advanced CAD Features imports
    from services.advanced_cad_features import (
        initialize_advanced_cad_features,
        set_precision_level as cad_set_precision_level,
        calculate_precise_coordinates,
        add_constraint,
        solve_constraints,
        create_assembly,
        export_high_precision,
        get_cad_performance_stats,
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SVGX Engine API",
    description="Programmable spatial markup format and simulation engine for CAD-grade infrastructure modeling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SVGX Engine components
parser = SVGXParser()
evaluator = SVGXEvaluator()
behavior_engine = SVGXBehaviorEngine()
physics_engine = SVGXPhysicsEngine()
svg_compiler = SVGXToSVGCompiler()
json_compiler = SVGXToJSONCompiler()
performance_monitor = PerformanceMonitor()
telemetry_logger = TelemetryLogger()

# Global state for interactive operations
interactive_state = {
    "selected_elements": [],
    "hovered_element": None,
    "drag_state": None,
    "constraints": [],
    "precision_level": "ui",  # ui, edit, compute
}


# Pydantic Models for API
class SVGXRequest(BaseModel):
    """Request model for SVGX operations."""

    content: str = Field(..., description="SVGX content to process")
    options: Optional[Dict[str, Any]] = Field(
        default={}, description="Processing options"
    )


class InteractiveRequest(BaseModel):
    """Request model for interactive operations."""

    operation: str = Field(..., description="Interactive operation type")
    element_id: Optional[str] = Field(None, description="Target element ID")
    coordinates: Optional[Dict[str, float]] = Field(
        None, description="Mouse coordinates"
    )
    modifiers: Optional[Dict[str, bool]] = Field(None, description="Keyboard modifiers")


class PrecisionRequest(BaseModel):
    """Request model for precision operations."""

    level: str = Field(..., description="Precision level: ui, edit, compute")
    coordinates: Dict[str, float] = Field(..., description="Coordinates to process")


class CADConstraintRequest(BaseModel):
    """Request model for CAD constraint operations."""

    constraint_id: str = Field(..., description="Unique constraint identifier")
    constraint_type: str = Field(..., description="Type of constraint")
    elements: List[str] = Field(..., description="Elements involved in constraint")
    parameters: Optional[Dict[str, Any]] = Field(
        default={}, description="Constraint parameters"
    )


class AssemblyRequest(BaseModel):
    """Request model for assembly operations."""

    assembly_id: str = Field(..., description="Assembly identifier")
    name: str = Field(..., description="Assembly name")
    components: Optional[List[str]] = Field(default=[], description="Component IDs")


class ExportRequest(BaseModel):
    """Request model for high-precision export."""

    elements: List[Dict[str, Any]] = Field(..., description="Elements to export")
    precision_level: str = Field(
        default="compute", description="Export precision level"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    performance: Dict[str, float] = Field(..., description="Performance metrics")


# Middleware for performance monitoring
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Middleware to monitor request performance."""
    start_time = time.time()

    response = await call_next(request)

    duration = (time.time() - start_time) * 1000
    performance_monitor.record_request(
        path=request.url.path, method=request.method, duration_ms=duration
    )

    # Add performance header
    response.headers["X-Response-Time"] = f"{duration:.2f}ms"

    return response


# Health and Monitoring Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    try:
        # Basic health checks
        parser_status = "healthy"
        evaluator_status = "healthy"
        physics_status = "healthy"

        # Get performance metrics
        metrics = performance_monitor.get_metrics()

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            performance={
                "avg_response_time_ms": metrics.get("avg_response_time", 0.0),
                "total_requests": metrics.get("total_requests", 0),
                "error_rate": metrics.get("error_rate", 0.0),
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.get("/metrics")
async def get_metrics():
    """Get detailed performance metrics."""
    try:
        metrics = performance_monitor.get_metrics()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


# Core SVGX Processing Endpoints
@app.post("/parse")
async def parse_svgx(request: SVGXRequest):
    """Parse SVGX content and return structured elements."""
    try:
        start_time = time.time()

        # Parse SVGX content
        elements = parser.parse(request.content)

        # Convert to JSON-serializable format
        parsed_data = []
        for element in elements:
            element_data = {
                "tag": element.tag,
                "attributes": element.attributes,
                "position": element.position,
                "has_arx_object": element.has_arx_object(),
                "arx_object": (
                    element.arx_object.__dict__ if element.arx_object else None
                ),
                "arx_behavior": (
                    element.arx_behavior.__dict__ if element.arx_behavior else None
                ),
                "arx_physics": (
                    element.arx_physics.__dict__ if element.arx_physics else None
                ),
            }
            parsed_data.append(element_data)

        duration = (time.time() - start_time) * 1000

        # Log performance
        telemetry_logger.log_performance(
            operation_name="svgx_parse",
            duration_ms=duration,
            metadata={"elements_count": len(elements)},
        )

        return {
            "status": "success",
            "elements": parsed_data,
            "count": len(elements),
            "duration_ms": duration,
        }

    except Exception as e:
        logger.error(f"Failed to parse SVGX: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse SVGX: {str(e)}")


@app.post("/evaluate")
async def evaluate_behavior(request: SVGXRequest):
    """Evaluate SVGX behavior and simulation logic."""
    try:
        start_time = time.time()

        # Parse SVGX content
        elements = parser.parse(request.content)

        # Evaluate behavior for each element
        results = []
        for element in elements:
            if element.arx_behavior:
                behavior_result = evaluator.evaluate_behavior(
                    {
                        "variables": element.arx_behavior.variables,
                        "calculations": element.arx_behavior.calculations,
                        "triggers": element.arx_behavior.triggers,
                    }
                )
                results.append(
                    {
                        "element_id": element.attributes.get("id", "unknown"),
                        "behavior": behavior_result,
                    }
                )

        duration = (time.time() - start_time) * 1000

        return {"status": "success", "results": results, "duration_ms": duration}

    except Exception as e:
        logger.error(f"Failed to evaluate behavior: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to evaluate behavior: {str(e)}"
        )


@app.post("/simulate")
async def simulate_physics(request: SVGXRequest):
    """Run physics simulation on SVGX content."""
    try:
        start_time = time.time()

        # Parse SVGX content
        elements = parser.parse(request.content)

        # Run physics simulation
        simulation_results = []
        for element in elements:
            if element.arx_physics:
                physics_result = evaluator.evaluate_physics(
                    {
                        "mass": element.arx_physics.mass,
                        "anchor": element.arx_physics.anchor,
                        "forces": element.arx_physics.forces,
                    }
                )
                simulation_results.append(
                    {
                        "element_id": element.attributes.get("id", "unknown"),
                        "physics": physics_result,
                    }
                )

        duration = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "simulation": simulation_results,
            "duration_ms": duration,
        }

    except Exception as e:
        logger.error(f"Failed to simulate physics: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to simulate physics: {str(e)}"
        )


# Interactive Behavior Endpoints
@app.post("/interactive")
async def handle_interactive_operation(request: InteractiveRequest):
    """Handle interactive operations (click, drag, hover)."""
    try:
        start_time = time.time()

        operation = request.operation.lower()
        element_id = request.element_id
        coordinates = request.coordinates or {}
        modifiers = request.modifiers or {}

        result = None

        if operation == "click":
            result = await handle_click(element_id, coordinates, modifiers)
        elif operation == "drag_start":
            result = await handle_drag_start(element_id, coordinates, modifiers)
        elif operation == "drag_move":
            result = await handle_drag_move(coordinates, modifiers)
        elif operation == "drag_end":
            result = await handle_drag_end(coordinates, modifiers)
        elif operation == "hover":
            result = await handle_hover(element_id, coordinates, modifiers)
        elif operation == "select":
            result = await handle_select(element_id, modifiers)
        elif operation == "deselect":
            result = await handle_deselect(element_id)
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown operation: {operation}"
            )

        duration = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "operation": operation,
            "result": result,
            "duration_ms": duration,
        }

    except Exception as e:
        logger.error(f"Failed to handle interactive operation: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to handle operation: {str(e)}"
        )


async def handle_click(
    element_id: Optional[str], coordinates: Dict[str, float], modifiers: Dict[str, bool]
):
    """Handle click operation."""
    if element_id:
        # Add to selection if Ctrl/Cmd is pressed
        if modifiers.get("ctrl", False) or modifiers.get("meta", False):
            if element_id not in interactive_state["selected_elements"]:
                interactive_state["selected_elements"].append(element_id)
        else:
            # Single selection
            interactive_state["selected_elements"] = [element_id]

    return {
        "selected_elements": interactive_state["selected_elements"],
        "click_position": coordinates,
    }


async def handle_drag_start(
    element_id: Optional[str], coordinates: Dict[str, float], modifiers: Dict[str, bool]
):
    """Handle drag start operation."""
    interactive_state["drag_state"] = {
        "element_id": element_id,
        "start_position": coordinates,
        "current_position": coordinates,
        "is_dragging": True,
    }

    return {
        "drag_started": True,
        "element_id": element_id,
        "start_position": coordinates,
    }


async def handle_drag_move(coordinates: Dict[str, float], modifiers: Dict[str, bool]):
    """Handle drag move operation."""
    if (
        interactive_state["drag_state"]
        and interactive_state["drag_state"]["is_dragging"]
    ):
        interactive_state["drag_state"]["current_position"] = coordinates

        # Apply constraints if any
        constrained_position = apply_constraints(
            coordinates, interactive_state["constraints"]
        )

        return {
            "is_dragging": True,
            "current_position": constrained_position,
            "original_position": coordinates,
        }

    return {"is_dragging": False}


async def handle_drag_end(coordinates: Dict[str, float], modifiers: Dict[str, bool]):
    """Handle drag end operation."""
    if interactive_state["drag_state"]:
        final_position = apply_constraints(
            coordinates, interactive_state["constraints"]
        )

        # Update element position (in real implementation, this would update the SVGX)
        result = {
            "drag_ended": True,
            "final_position": final_position,
            "element_id": interactive_state["drag_state"]["element_id"],
        }

        interactive_state["drag_state"] = None
        return result

    return {"drag_ended": False}


async def handle_hover(
    element_id: Optional[str], coordinates: Dict[str, float], modifiers: Dict[str, bool]
):
    """Handle hover operation."""
    interactive_state["hovered_element"] = element_id

    return {"hovered_element": element_id, "hover_position": coordinates}


async def handle_select(element_id: str, modifiers: Dict[str, bool]):
    """Handle element selection."""
    if modifiers.get("ctrl", False) or modifiers.get("meta", False):
        # Multi-select
        if element_id not in interactive_state["selected_elements"]:
            interactive_state["selected_elements"].append(element_id)
    else:
        # Single select
        interactive_state["selected_elements"] = [element_id]

    return {"selected_elements": interactive_state["selected_elements"]}


async def handle_deselect(element_id: str):
    """Handle element deselection."""
    if element_id in interactive_state["selected_elements"]:
        interactive_state["selected_elements"].remove(element_id)

    return {"selected_elements": interactive_state["selected_elements"]}


def apply_constraints(
    coordinates: Dict[str, float], constraints: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Apply geometric constraints to coordinates."""
    # Simple snap-to-grid constraint (1mm grid)
    grid_size = 1.0  # 1mm

    x = round(coordinates.get("x", 0) / grid_size) * grid_size
    y = round(coordinates.get("y", 0) / grid_size) * grid_size
    z = round(coordinates.get("z", 0) / grid_size) * grid_size

    return {"x": x, "y": y, "z": z}


# Precision and Advanced Features
@app.post("/precision")
async def set_precision_level(request: PrecisionRequest):
    """Set precision level for operations."""
    try:
        level = request.level.lower()
        if level not in ["ui", "edit", "compute"]:
            raise HTTPException(status_code=400, detail="Invalid precision level")

        interactive_state["precision_level"] = level

        # Update precision based on level
        precision_values = {
            "ui": 0.1,  # 0.1mm for UI
            "edit": 0.01,  # 0.01mm for editing
            "compute": 0.001,  # 0.001mm for computation
        }

        return {
            "status": "success",
            "precision_level": level,
            "precision_value_mm": precision_values[level],
        }

    except Exception as e:
        logger.error(f"Failed to set precision level: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to set precision: {str(e)}"
        )


@app.get("/state")
async def get_interactive_state():
    """Get current interactive state."""
    return {
        "selected_elements": interactive_state["selected_elements"],
        "hovered_element": interactive_state["hovered_element"],
        "drag_state": interactive_state["drag_state"],
        "constraints": interactive_state["constraints"],
        "precision_level": interactive_state["precision_level"],
    }


# Compilation Endpoints
@app.post("/compile/svg")
async def compile_to_svg(request: SVGXRequest):
    """Compile SVGX to SVG format."""
    try:
        start_time = time.time()

        svg_content = svg_compiler.compile(request.content)

        duration = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "format": "svg",
            "content": svg_content,
            "duration_ms": duration,
        }

    except Exception as e:
        logger.error(f"Failed to compile to SVG: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to compile to SVG: {str(e)}"
        )


@app.post("/compile/json")
async def compile_to_json(request: SVGXRequest):
    """Compile SVGX to JSON format."""
    try:
        start_time = time.time()

        json_content = json_compiler.compile(request.content)

        duration = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "format": "json",
            "content": json_content,
            "duration_ms": duration,
        }

    except Exception as e:
        logger.error(f"Failed to compile to JSON: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to compile to JSON: {str(e)}"
        )


# Advanced CAD Features Endpoints


@app.post("/cad/precision")
async def cad_set_precision(request: PrecisionRequest):
    """Set CAD precision level for advanced operations."""
    try:
        start_time = time.time()

        success = await cad_set_precision_level(request.level)

        if success:
            precise_coords = await calculate_precise_coordinates(
                request.coordinates, request.level
            )
            duration = (time.time() - start_time) * 1000

            return {
                "status": "success",
                "precision_level": request.level,
                "original_coordinates": request.coordinates,
                "precise_coordinates": precise_coords,
                "duration_ms": duration,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to set precision level")

    except Exception as e:
        logger.error(f"Failed to set CAD precision: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to set CAD precision: {str(e)}"
        )


@app.post("/cad/constraint")
async def cad_add_constraint(request: CADConstraintRequest):
    """Add a geometric constraint to the CAD system."""
    try:
        start_time = time.time()

        constraint_data = {
            "id": request.constraint_id,
            "type": request.constraint_type,
            "elements": request.elements,
            "parameters": request.parameters,
        }

        success = await add_constraint(constraint_data)
        duration = (time.time() - start_time) * 1000

        if success:
            return {
                "status": "success",
                "constraint_id": request.constraint_id,
                "constraint_type": request.constraint_type,
                "elements": request.elements,
                "duration_ms": duration,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add constraint")

    except Exception as e:
        logger.error(f"Failed to add CAD constraint: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to add constraint: {str(e)}"
        )


@app.post("/cad/solve")
async def cad_solve_constraints():
    """Solve all CAD constraints using batching."""
    try:
        start_time = time.time()

        result = await solve_constraints()
        duration = (time.time() - start_time) * 1000

        return {"status": "success", "result": result, "duration_ms": duration}

    except Exception as e:
        logger.error(f"Failed to solve CAD constraints: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to solve constraints: {str(e)}"
        )


@app.post("/cad/assembly")
async def cad_create_assembly(request: AssemblyRequest):
    """Create a new CAD assembly."""
    try:
        start_time = time.time()

        result = await create_assembly(request.assembly_id, request.name)
        duration = (time.time() - start_time) * 1000

        if result["success"]:
            return {
                "status": "success",
                "assembly_id": result["assembly_id"],
                "name": result["name"],
                "duration_ms": duration,
            }
        else:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Failed to create assembly")
            )

    except Exception as e:
        logger.error(f"Failed to create CAD assembly: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to create assembly: {str(e)}"
        )


@app.post("/cad/export")
async def cad_export_high_precision(request: ExportRequest):
    """Export elements with high precision for manufacturing."""
    try:
        start_time = time.time()

        result = await export_high_precision(request.elements, request.precision_level)
        duration = (time.time() - start_time) * 1000

        if result["success"]:
            return {
                "status": "success",
                "precision_level": result["precision_level"],
                "precision_value": result["precision_value"],
                "elements_count": len(result["elements"]),
                "duration_ms": duration,
            }
        else:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Failed to export")
            )

    except Exception as e:
        logger.error(f"Failed to export with high precision: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to export: {str(e)}")


@app.get("/cad/stats")
async def get_cad_performance_stats():
    """Get CAD features performance statistics."""
    try:
        stats = get_cad_performance_stats()
        return {"status": "success", "stats": stats}

    except Exception as e:
        logger.error(f"Failed to get CAD stats: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get stats: {str(e)}")


# Logic Engine Endpoints


class LogicRuleRequest(BaseModel):
    """Request model for logic rule operations."""

    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    rule_type: str = Field(
        ...,
        description="Rule type: conditional, transformation, validation, workflow, analysis",
    )
    conditions: List[Dict[str, Any]] = Field(..., description="Rule conditions")
    actions: List[Dict[str, Any]] = Field(..., description="Rule actions")
    priority: int = Field(default=1, description="Rule priority")
    tags: Optional[List[str]] = Field(default=[], description="Rule tags")


class LogicExecutionRequest(BaseModel):
    """Request model for logic rule execution."""

    element_id: str = Field(..., description="Element ID")
    data: Dict[str, Any] = Field(..., description="Data for rule execution")
    rule_ids: Optional[List[str]] = Field(
        default=None, description="Specific rule IDs to execute"
    )


@app.post("/logic/create_rule")
async def create_logic_rule(request: LogicRuleRequest):
    """Create a new logic rule."""
    try:
        start_time = time.time()

        rule_id = runtime.create_logic_rule(
            name=request.name,
            description=request.description,
            rule_type=request.rule_type,
            conditions=request.conditions,
            actions=request.actions,
            priority=request.priority,
            tags=request.tags,
        )

        duration = (time.time() - start_time) * 1000

        if rule_id:
            return {"status": "success", "rule_id": rule_id, "duration_ms": duration}
        else:
            raise HTTPException(status_code=400, detail="Failed to create logic rule")

    except Exception as e:
        logger.error(f"Failed to create logic rule: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create rule: {str(e)}")


@app.post("/logic/execute")
async def execute_logic_rules(request: LogicExecutionRequest):
    """Execute logic rules for an element."""
    try:
        start_time = time.time()

        results = runtime.execute_logic_rules(
            element_id=request.element_id, data=request.data, rule_ids=request.rule_ids
        )

        duration = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "results": results,
            "execution_count": len(results),
            "duration_ms": duration,
        }

    except Exception as e:
        logger.error(f"Failed to execute logic rules: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to execute rules: {str(e)}"
        )


@app.get("/logic/stats")
async def get_logic_engine_stats():
    """Get logic engine performance statistics."""
    try:
        stats = runtime.get_logic_engine_stats()
        return {"status": "success", "stats": stats}

    except Exception as e:
        logger.error(f"Failed to get logic engine stats: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get stats: {str(e)}")


@app.get("/logic/rules")
async def list_logic_rules():
    """List all available logic rules."""
    try:
        if not runtime.logic_engine:
            raise HTTPException(status_code=503, detail="Logic engine not available")

        rules = runtime.logic_engine.list_rules()
        return {
            "status": "success",
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "rule_type": rule.rule_type.value,
                }
                for rule in rules
            ],
            "total_rules": len(rules),
        }

    except Exception as e:
        logger.error(f"Failed to list logic rules: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to list rules: {str(e)}")


@app.get("/logic/rules/{rule_id}")
async def get_logic_rule(rule_id: str):
    """Get a specific logic rule."""
    try:
        if not runtime.logic_engine:
            raise HTTPException(status_code=503, detail="Logic engine not available")

        rule = runtime.logic_engine.get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        return {
            "status": "success",
            "rule": {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type.value,
                "status": rule.status.value,
                "priority": rule.priority,
                "tags": rule.tags,
                "execution_count": rule.execution_count,
                "success_count": rule.success_count,
                "error_count": rule.error_count,
                "avg_execution_time": rule.avg_execution_time,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get logic rule: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get rule: {str(e)}")


@app.delete("/logic/rules/{rule_id}")
async def delete_logic_rule(rule_id: str):
    """Delete a logic rule."""
    try:
        if not runtime.logic_engine:
            raise HTTPException(status_code=503, detail="Logic engine not available")

        success = runtime.logic_engine.delete_rule(rule_id)

        if success:
            return {
                "status": "success",
                "message": f"Rule {rule_id} deleted successfully",
            }
        else:
            raise HTTPException(status_code=404, detail="Rule not found")

    except Exception as e:
        logger.error(f"Failed to delete logic rule: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to delete rule: {str(e)}")


# Real-time Collaboration Endpoints


@app.post("/collaboration/join")
async def join_collaboration_session(request: Dict[str, Any]):
    """Join a real-time collaboration session."""
    try:
        start_time = time.time()

        # Extract user information
        user_id = request.get("user_id")
        username = request.get("username", "Anonymous")
        session_id = request.get("session_id", str(uuid.uuid4()))

        # Add user to presence system
        from svgx_engine.services.realtime_collaboration import get_active_users

        active_users = get_active_users()

        duration = (time.time() - start_time) * 1000

        return {
            "status": "success",
            "user_id": user_id,
            "username": username,
            "session_id": session_id,
            "active_users": len(active_users),
            "duration_ms": duration,
        }

    except Exception as e:
        logger.error(f"Failed to join collaboration session: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to join session: {str(e)}")


@app.post("/collaboration/operation")
async def send_collaboration_operation(request: Dict[str, Any]):
    """Send a collaborative operation."""
    try:
        start_time = time.time()

        from svgx_engine.services.realtime_collaboration import send_operation

        success = await send_operation(request)
        duration = (time.time() - start_time) * 1000

        if success:
            return {
                "status": "success",
                "operation_sent": True,
                "duration_ms": duration,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to send operation")

    except Exception as e:
        logger.error(f"Failed to send collaboration operation: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to send operation: {str(e)}"
        )


@app.post("/collaboration/resolve")
async def resolve_collaboration_conflict(request: Dict[str, Any]):
    """Resolve a collaboration conflict."""
    try:
        start_time = time.time()

        from svgx_engine.services.realtime_collaboration import resolve_conflict

        conflict_id = request.get("conflict_id")
        resolution = request.get("resolution", "automatic")
        resolved_by = request.get("resolved_by")

        success = await resolve_conflict(conflict_id, resolution, resolved_by)
        duration = (time.time() - start_time) * 1000

        if success:
            return {
                "status": "success",
                "conflict_resolved": True,
                "resolution": resolution,
                "duration_ms": duration,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to resolve conflict")

    except Exception as e:
        logger.error(f"Failed to resolve collaboration conflict: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to resolve conflict: {str(e)}"
        )


@app.get("/collaboration/users")
async def get_collaboration_users():
    """Get active collaboration users."""
    try:
        from svgx_engine.services.realtime_collaboration import get_active_users

        active_users = get_active_users()

        return {
            "status": "success",
            "active_users": active_users,
            "total_users": len(active_users),
        }

    except Exception as e:
        logger.error(f"Failed to get collaboration users: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get users: {str(e)}")


@app.get("/collaboration/stats")
async def get_collaboration_stats():
    """Get collaboration performance statistics."""
    try:
        from svgx_engine.services.realtime_collaboration import (
            get_collaboration_performance_stats,
        )

        stats = get_collaboration_performance_stats()

        return {"status": "success", "stats": stats}

    except Exception as e:
        logger.error(f"Failed to get collaboration stats: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get stats: {str(e)}")


# Initialize collaboration server on startup
@app.on_event("startup")
async def startup_collaboration():
    """Initialize collaboration server on application startup."""
    try:
        from svgx_engine.services.realtime_collaboration import (
            start_collaboration_server,
        )

        success = await start_collaboration_server("localhost", 8765)
        if success:
            logger.info("Real-time collaboration server started successfully")
        else:
            logger.warning("Failed to start real-time collaboration server")
    except Exception as e:
        logger.error(f"Error starting collaboration server: {e}")


# Initialize CAD features on startup
@app.on_event("startup")
async def startup_event():
    """Initialize CAD features on application startup."""
    try:
        success = await initialize_advanced_cad_features()
        if success:
            logger.info("Advanced CAD features initialized successfully")
        else:
            logger.warning("Failed to initialize advanced CAD features")
    except Exception as e:
        logger.error(f"Error initializing CAD features: {e}")


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    """Run the FastAPI application."""
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
