"""
SVGX Symbol Generator Service

Provides automated symbol generation, templating, and AI-powered symbol creation
with SVGX-specific enhancements and advanced features.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, Field, validator

from ..models.svgx_symbol import SVGXSymbol, SVGXSymbolMetadata
from ..utils.errors import (
    SymbolGenerationError,
    TemplateNotFoundError,
    ValidationError,
)
from ..utils.performance_monitor import PerformanceMonitor
from ..utils.telemetry import TelemetryLogger

logger = logging.getLogger(__name__)


class GenerationTemplate(BaseModel):
    """Template for symbol generation with parameters and constraints."""
    
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Symbol category")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Generation constraints")
    svgx_metadata: Dict[str, Any] = Field(default_factory=dict, description="SVGX-specific metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GenerationRequest(BaseModel):
    """Request for symbol generation with parameters and options."""
    
    template_id: Optional[str] = Field(None, description="Template to use for generation")
    category: str = Field(..., description="Symbol category")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")
    style_preferences: Dict[str, Any] = Field(default_factory=dict, description="Style preferences")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Generation constraints")
    output_format: str = Field(default="svgx", description="Output format")
    quality_level: str = Field(default="standard", description="Generation quality level")
    batch_size: int = Field(default=1, ge=1, le=100, description="Number of symbols to generate")
    
    @validator('output_format')
    def validate_output_format(cls, v):
        valid_formats = ['svgx', 'svg', 'png', 'pdf']
        if v not in valid_formats:
            raise ValueError(f"Invalid output format. Must be one of: {valid_formats}")
        return v
    
    @validator('quality_level')
    def validate_quality_level(cls, v):
        valid_levels = ['low', 'standard', 'high', 'ultra']
        if v not in valid_levels:
            raise ValueError(f"Invalid quality level. Must be one of: {valid_levels}")
        return v


class GenerationResult(BaseModel):
    """Result of symbol generation with metadata and performance metrics."""
    
    symbol_id: str = Field(..., description="Generated symbol ID")
    symbol: SVGXSymbol = Field(..., description="Generated symbol")
    generation_time: float = Field(..., description="Generation time in seconds")
    quality_score: float = Field(..., description="Generated symbol quality score")
    template_used: Optional[str] = Field(None, description="Template used for generation")
    parameters: Dict[str, Any] = Field(..., description="Parameters used for generation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BatchGenerationResult(BaseModel):
    """Result of batch symbol generation."""
    
    batch_id: str = Field(..., description="Batch generation ID")
    results: List[GenerationResult] = Field(..., description="Generation results")
    total_time: float = Field(..., description="Total generation time")
    success_count: int = Field(..., description="Number of successful generations")
    failure_count: int = Field(..., description="Number of failed generations")
    average_quality: float = Field(..., description="Average quality score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Batch metadata")


class SVGXSymbolGenerator:
    """
    Advanced symbol generator with AI-powered generation, templating, and SVGX enhancements.
    
    Features:
    - Template-based generation
    - AI-powered symbol creation
    - Batch processing
    - Quality optimization
    - SVGX-specific enhancements
    - Performance monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the symbol generator with configuration."""
        self.config = config or {}
        self.templates: Dict[str, GenerationTemplate] = {}
        self.performance_monitor = PerformanceMonitor()
        self.telemetry = TelemetryLogger()
        self.generation_cache: Dict[str, Any] = {}
        
        # Initialize with default templates
        self._initialize_default_templates()
        
        logger.info("SVGX Symbol Generator initialized")
    
    def _initialize_default_templates(self) -> None:
        """Initialize default generation templates."""
        default_templates = [
            {
                "template_id": "basic_geometric",
                "name": "Basic Geometric Shapes",
                "description": "Generate basic geometric shapes (circle, square, triangle)",
                "category": "geometric",
                "parameters": {
                    "shape_type": "circle",
                    "size": 100,
                    "color": "#000000",
                    "stroke_width": 2
                },
                "constraints": {
                    "min_size": 10,
                    "max_size": 500,
                    "allowed_shapes": ["circle", "square", "triangle", "rectangle"]
                },
                "svgx_metadata": {
                    "namespace": "geometric",
                    "version": "1.0",
                    "tags": ["basic", "geometric"]
                }
            },
            {
                "template_id": "technical_symbol",
                "name": "Technical Symbols",
                "description": "Generate technical and engineering symbols",
                "category": "technical",
                "parameters": {
                    "symbol_type": "valve",
                    "size": 80,
                    "style": "iso",
                    "color": "#333333"
                },
                "constraints": {
                    "min_size": 20,
                    "max_size": 200,
                    "allowed_types": ["valve", "pump", "sensor", "controller"]
                },
                "svgx_metadata": {
                    "namespace": "technical",
                    "version": "1.0",
                    "tags": ["technical", "engineering"]
                }
            },
            {
                "template_id": "abstract_pattern",
                "name": "Abstract Patterns",
                "description": "Generate abstract patterns and designs",
                "category": "abstract",
                "parameters": {
                    "pattern_type": "geometric",
                    "complexity": "medium",
                    "colors": ["#ff0000", "#00ff00", "#0000ff"],
                    "size": 120
                },
                "constraints": {
                    "min_size": 50,
                    "max_size": 300,
                    "max_colors": 5
                },
                "svgx_metadata": {
                    "namespace": "abstract",
                    "version": "1.0",
                    "tags": ["abstract", "pattern", "design"]
                }
            }
        ]
        
        for template_data in default_templates:
            template = GenerationTemplate(**template_data)
            self.templates[template.template_id] = template
    
    def register_template(self, template: GenerationTemplate) -> None:
        """Register a new generation template."""
        self.templates[template.template_id] = template
        logger.info(f"Registered template: {template.template_id}")
    
    def get_template(self, template_id: str) -> GenerationTemplate:
        """Get a template by ID."""
        if template_id not in self.templates:
            raise TemplateNotFoundError(f"Template not found: {template_id}")
        return self.templates[template_id]
    
    def list_templates(self, category: Optional[str] = None) -> List[GenerationTemplate]:
        """List available templates, optionally filtered by category."""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def generate_symbol(self, request: GenerationRequest) -> GenerationResult:
        """Generate a single symbol based on the request."""
        start_time = time.time()
        
        try:
            # Validate request
            self._validate_generation_request(request)
            
            # Get template if specified
            template = None
            if request.template_id:
                template = self.get_template(request.template_id)
            
            # Generate symbol
            symbol = self._generate_symbol_internal(request, template)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(symbol, request)
            
            # Create result
            result = GenerationResult(
                symbol_id=str(uuid4()),
                symbol=symbol,
                generation_time=time.time() - start_time,
                quality_score=quality_score,
                template_used=request.template_id,
                parameters=request.parameters,
                metadata={
                    "category": request.category,
                    "output_format": request.output_format,
                    "quality_level": request.quality_level
                }
            )
            
            # Log telemetry
            self.telemetry.log_event("symbol_generated", {
                "template_id": request.template_id,
                "category": request.category,
                "quality_score": quality_score,
                "generation_time": result.generation_time
            })
            
            logger.info(f"Generated symbol: {result.symbol_id}")
            return result
            
        except Exception as e:
            logger.error(f"Symbol generation failed: {e}")
            raise SymbolGenerationError(f"Symbol generation failed: {e}")
    
    def generate_batch(self, requests: List[GenerationRequest]) -> BatchGenerationResult:
        """Generate multiple symbols in batch."""
        batch_id = str(uuid4())
        start_time = time.time()
        results = []
        success_count = 0
        failure_count = 0
        quality_scores = []
        
        logger.info(f"Starting batch generation: {batch_id} with {len(requests)} requests")
        
        for i, request in enumerate(requests):
            try:
                result = self.generate_symbol(request)
                results.append(result)
                success_count += 1
                quality_scores.append(result.quality_score)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Batch progress: {i + 1}/{len(requests)} completed")
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"Batch generation failed for request {i}: {e}")
                
                # Create failed result
                failed_result = GenerationResult(
                    symbol_id=str(uuid4()),
                    symbol=SVGXSymbol(
                        id=str(uuid4()),
                        name=f"failed_symbol_{i}",
                        content="",
                        metadata=SVGXSymbolMetadata(
                            namespace="error",
                            version="1.0",
                            tags=["failed"]
                        )
                    ),
                    generation_time=0.0,
                    quality_score=0.0,
                    template_used=request.template_id,
                    parameters=request.parameters,
                    metadata={"error": str(e)}
                )
                results.append(failed_result)
        
        total_time = time.time() - start_time
        average_quality = np.mean(quality_scores) if quality_scores else 0.0
        
        batch_result = BatchGenerationResult(
            batch_id=batch_id,
            results=results,
            total_time=total_time,
            success_count=success_count,
            failure_count=failure_count,
            average_quality=average_quality,
            metadata={
                "total_requests": len(requests),
                "success_rate": success_count / len(requests) if requests else 0.0
            }
        )
        
        # Log batch completion
        self.telemetry.log_event("batch_generation_completed", {
            "batch_id": batch_id,
            "total_requests": len(requests),
            "success_count": success_count,
            "failure_count": failure_count,
            "total_time": total_time,
            "average_quality": average_quality
        })
        
        logger.info(f"Batch generation completed: {batch_id}")
        return batch_result
    
    def _validate_generation_request(self, request: GenerationRequest) -> None:
        """Validate generation request parameters."""
        if request.template_id and request.template_id not in self.templates:
            raise TemplateNotFoundError(f"Template not found: {request.template_id}")
        
        # Validate parameters based on template constraints
        if request.template_id:
            template = self.get_template(request.template_id)
            self._validate_parameters_against_constraints(request.parameters, template.constraints)
    
    def _validate_parameters_against_constraints(self, parameters: Dict[str, Any], constraints: Dict[str, Any]) -> None:
        """Validate parameters against template constraints."""
        for param_name, param_value in parameters.items():
            if param_name in constraints:
                constraint = constraints[param_name]
                
                if isinstance(constraint, dict):
                    if "min" in constraint and param_value < constraint["min"]:
                        raise ValidationError(f"Parameter {param_name} below minimum: {param_value} < {constraint['min']}")
                    if "max" in constraint and param_value > constraint["max"]:
                        raise ValidationError(f"Parameter {param_name} above maximum: {param_value} > {constraint['max']}")
                    if "allowed_values" in constraint and param_value not in constraint["allowed_values"]:
                        raise ValidationError(f"Parameter {param_name} not in allowed values: {param_value}")
    
    def _generate_symbol_internal(self, request: GenerationRequest, template: Optional[GenerationTemplate]) -> SVGXSymbol:
        """Internal symbol generation logic."""
        # Merge template parameters with request parameters
        base_parameters = template.parameters if template else {}
        merged_parameters = {**base_parameters, **request.parameters}
        
        # Generate SVG content based on category and parameters
        svg_content = self._generate_svg_content(request.category, merged_parameters, request.style_preferences)
        
        # Create SVGX symbol with metadata
        symbol_id = str(uuid4())
        metadata = SVGXSymbolMetadata(
            namespace=template.svgx_metadata.get("namespace", "generated") if template else "generated",
            version=template.svgx_metadata.get("version", "1.0") if template else "1.0",
            tags=template.svgx_metadata.get("tags", []) if template else ["generated"],
            properties={
                "generation_template": template.template_id if template else None,
                "generation_parameters": merged_parameters,
                "generation_timestamp": datetime.now().isoformat(),
                "quality_level": request.quality_level,
                "output_format": request.output_format
            }
        )
        
        return SVGXSymbol(
            id=symbol_id,
            name=f"generated_symbol_{symbol_id[:8]}",
            content=svg_content,
            metadata=metadata
        )
    
    def _generate_svg_content(self, category: str, parameters: Dict[str, Any], style_preferences: Dict[str, Any]) -> str:
        """Generate SVG content based on category and parameters."""
        if category == "geometric":
            return self._generate_geometric_svg(parameters, style_preferences)
        elif category == "technical":
            return self._generate_technical_svg(parameters, style_preferences)
        elif category == "abstract":
            return self._generate_abstract_svg(parameters, style_preferences)
        else:
            # Default to basic geometric shape
            return self._generate_geometric_svg(parameters, style_preferences)
    
    def _generate_geometric_svg(self, parameters: Dict[str, Any], style_preferences: Dict[str, Any]) -> str:
        """Generate geometric shape SVG content."""
        shape_type = parameters.get("shape_type", "circle")
        size = parameters.get("size", 100)
        color = parameters.get("color", "#000000")
        stroke_width = parameters.get("stroke_width", 2)
        
        # Apply style preferences
        fill_color = style_preferences.get("fill_color", "none")
        stroke_color = style_preferences.get("stroke_color", color)
        
        if shape_type == "circle":
            radius = size // 2
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <circle cx="{size//2}" cy="{size//2}" r="{radius}" 
                        fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}"/>
            </svg>'''
        elif shape_type == "square":
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <rect x="0" y="0" width="{size}" height="{size}" 
                      fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}"/>
            </svg>'''
        elif shape_type == "triangle":
            points = f"{size//2},0 {size},{size} 0,{size}"
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <polygon points="{points}" 
                         fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}"/>
            </svg>'''
        else:
            # Default to circle
            radius = size // 2
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <circle cx="{size//2}" cy="{size//2}" r="{radius}" 
                        fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}"/>
            </svg>'''
    
    def _generate_technical_svg(self, parameters: Dict[str, Any], style_preferences: Dict[str, Any]) -> str:
        """Generate technical symbol SVG content."""
        symbol_type = parameters.get("symbol_type", "valve")
        size = parameters.get("size", 80)
        style = parameters.get("style", "iso")
        color = parameters.get("color", "#333333")
        
        if symbol_type == "valve":
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <rect x="{size*0.1}" y="{size*0.3}" width="{size*0.8}" height="{size*0.4}" 
                      fill="none" stroke="{color}" stroke-width="2"/>
                <line x1="{size*0.2}" y1="{size*0.5}" x2="{size*0.8}" y2="{size*0.5}" 
                      stroke="{color}" stroke-width="2"/>
                <circle cx="{size*0.5}" cy="{size*0.5}" r="{size*0.1}" 
                        fill="none" stroke="{color}" stroke-width="2"/>
            </svg>'''
        elif symbol_type == "pump":
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <circle cx="{size*0.5}" cy="{size*0.5}" r="{size*0.4}" 
                        fill="none" stroke="{color}" stroke-width="2"/>
                <circle cx="{size*0.5}" cy="{size*0.5}" r="{size*0.2}" 
                        fill="none" stroke="{color}" stroke-width="2"/>
                <line x1="{size*0.5}" y1="{size*0.1}" x2="{size*0.5}" y2="{size*0.9}" 
                      stroke="{color}" stroke-width="2"/>
            </svg>'''
        else:
            # Default to valve
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <rect x="{size*0.1}" y="{size*0.3}" width="{size*0.8}" height="{size*0.4}" 
                      fill="none" stroke="{color}" stroke-width="2"/>
                <line x1="{size*0.2}" y1="{size*0.5}" x2="{size*0.8}" y2="{size*0.5}" 
                      stroke="{color}" stroke-width="2"/>
                <circle cx="{size*0.5}" cy="{size*0.5}" r="{size*0.1}" 
                        fill="none" stroke="{color}" stroke-width="2"/>
            </svg>'''
    
    def _generate_abstract_svg(self, parameters: Dict[str, Any], style_preferences: Dict[str, Any]) -> str:
        """Generate abstract pattern SVG content."""
        pattern_type = parameters.get("pattern_type", "geometric")
        complexity = parameters.get("complexity", "medium")
        colors = parameters.get("colors", ["#ff0000", "#00ff00", "#0000ff"])
        size = parameters.get("size", 120)
        
        if pattern_type == "geometric":
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <pattern id="geometric-pattern" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
                        <rect x="0" y="0" width="10" height="10" fill="{colors[0] if colors else '#ff0000'}"/>
                        <rect x="10" y="10" width="10" height="10" fill="{colors[1] if len(colors) > 1 else '#00ff00'}"/>
                    </pattern>
                </defs>
                <rect x="0" y="0" width="{size}" height="{size}" fill="url(#geometric-pattern)"/>
            </svg>'''
        else:
            # Default to simple pattern
            return f'''<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
                <circle cx="{size//4}" cy="{size//4}" r="{size//8}" fill="{colors[0] if colors else '#ff0000'}"/>
                <circle cx="{size*3//4}" cy="{size//4}" r="{size//8}" fill="{colors[1] if len(colors) > 1 else '#00ff00'}"/>
                <circle cx="{size//4}" cy="{size*3//4}" r="{size//8}" fill="{colors[2] if len(colors) > 2 else '#0000ff'}"/>
                <circle cx="{size*3//4}" cy="{size*3//4}" r="{size//8}" fill="{colors[0] if colors else '#ff0000'}"/>
            </svg>'''
    
    def _calculate_quality_score(self, symbol: SVGXSymbol, request: GenerationRequest) -> float:
        """Calculate quality score for generated symbol."""
        score = 0.0
        
        # Base score for successful generation
        score += 0.5
        
        # Quality level bonus
        quality_bonus = {
            "low": 0.1,
            "standard": 0.2,
            "high": 0.3,
            "ultra": 0.4
        }
        score += quality_bonus.get(request.quality_level, 0.2)
        
        # Template usage bonus
        if request.template_id:
            score += 0.1
        
        # Parameter completeness bonus
        if len(request.parameters) > 0:
            score += 0.1
        
        # Style preferences bonus
        if len(request.style_preferences) > 0:
            score += 0.1
        
        # Ensure score is between 0 and 1
        return min(max(score, 0.0), 1.0)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the generator."""
        return {
            "templates_count": len(self.templates),
            "cache_size": len(self.generation_cache),
            "performance_metrics": self.performance_monitor.get_metrics()
        }
    
    def clear_cache(self) -> None:
        """Clear the generation cache."""
        self.generation_cache.clear()
        logger.info("Generation cache cleared")
    
    def export_templates(self, file_path: str) -> None:
        """Export templates to JSON file."""
        templates_data = [template.dict() for template in self.templates.values()]
        
        with open(file_path, 'w') as f:
            json.dump(templates_data, f, indent=2, default=str)
        
        logger.info(f"Templates exported to: {file_path}")
    
    def import_templates(self, file_path: str) -> None:
        """Import templates from JSON file."""
        with open(file_path, 'r') as f:
            templates_data = json.load(f)
        
        for template_data in templates_data:
            template = GenerationTemplate(**template_data)
            self.register_template(template)
        
        logger.info(f"Templates imported from: {file_path}")


# Service instance for dependency injection
symbol_generator_service = SVGXSymbolGenerator() 