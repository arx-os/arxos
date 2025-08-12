"""
Enhanced SVGX Compiler with ArxObject Integration

This compiler generates optimized output formats using real ArxObject data
from the Go engine, ensuring accuracy and performance.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

from svgx_engine.integration.arxobject_bridge import get_arxobject_bridge
from svgx_engine.models.svgx import SVGXDocument, SVGXElement
from svgx_engine.compiler.svgx_to_svg import SVGXToSVGCompiler
from services.arxobject.client.python_client import ArxObjectClient

logger = logging.getLogger(__name__)


class EnhancedSVGXCompiler:
    """
    Enhanced compiler that integrates with Go ArxObject engine.
    
    Features:
    - Direct ArxObject to SVG compilation
    - Optimized rendering using Go engine queries
    - Real-time constraint validation
    - Performance optimization through caching
    """
    
    def __init__(self):
        """Initialize enhanced compiler."""
        self.bridge = get_arxobject_bridge()
        self.arxobject_client = None
        self.render_cache = {}
        self.style_registry = self._init_styles()
        self.symbol_registry = self._init_symbols()
        
    async def initialize(self):
        """Initialize connection to ArxObject engine."""
        await self.bridge.connect()
        self.arxobject_client = self.bridge.client
        logger.info("Enhanced compiler connected to ArxObject engine")
    
    async def compile_region(
        self,
        min_x: float, min_y: float,
        max_x: float, max_y: float,
        output_format: str = 'svg',
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compile a region directly from ArxObject engine to output format.
        
        This is the most efficient way to render building sections.
        """
        options = options or {}
        
        # Query ArxObjects in region
        arxobjects = await self.arxobject_client.query_region(
            min_x, min_y, 0,
            max_x, max_y, 100,
            object_types=options.get('object_types'),
            limit=options.get('limit', 10000)
        )
        
        logger.info(f"Compiling {len(arxobjects)} ArxObjects to {output_format}")
        
        # Compile based on format
        if output_format == 'svg':
            return await self._compile_to_svg(arxobjects, options)
        elif output_format == 'json':
            return await self._compile_to_json(arxobjects, options)
        elif output_format == 'ifc':
            return await self._compile_to_ifc(arxobjects, options)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    async def _compile_to_svg(
        self,
        arxobjects: List,
        options: Dict[str, Any]
    ) -> str:
        """Compile ArxObjects to optimized SVG."""
        # Calculate viewport
        viewport = self._calculate_viewport(arxobjects)
        
        # Start SVG document
        svg = self._generate_svg_header(viewport, options)
        
        # Add styles
        svg += self._generate_styles(arxobjects)
        
        # Group by system for organized layers
        grouped = self._group_by_system(arxobjects)
        
        for system, objects in grouped.items():
            svg += f'  <g id="{system}-layer" class="{system}-system">\n'
            
            # Render objects efficiently
            for obj in objects:
                svg += await self._render_arxobject_svg(obj, options)
            
            svg += '  </g>\n'
        
        # Add dimensions if requested
        if options.get('show_dimensions'):
            svg += await self._generate_dimensions(arxobjects)
        
        # Add labels if requested
        if options.get('show_labels'):
            svg += await self._generate_labels(arxobjects)
        
        svg += '</svg>'
        
        # Optimize if requested
        if options.get('optimize', True):
            svg = self._optimize_svg(svg)
        
        return svg
    
    async def _render_arxobject_svg(
        self,
        obj,
        options: Dict[str, Any]
    ) -> str:
        """Render single ArxObject as SVG element."""
        # Check cache
        cache_key = f"{obj.id}_{obj.version}"
        if cache_key in self.render_cache and not options.get('force_render'):
            return self.render_cache[cache_key]
        
        svg = ''
        
        # Determine element type and render
        if obj.type == 'ELECTRICAL_OUTLET':
            svg = self._render_outlet(obj)
        elif obj.type == 'ELECTRICAL_PANEL':
            svg = self._render_panel(obj)
        elif obj.type.startswith('STRUCTURAL_'):
            svg = self._render_structural(obj)
        elif obj.type.startswith('PLUMBING_'):
            svg = self._render_plumbing(obj)
        else:
            svg = self._render_generic(obj)
        
        # Cache result
        self.render_cache[cache_key] = svg
        
        return svg
    
    def _render_outlet(self, obj) -> str:
        """Render electrical outlet."""
        x, y = obj.geometry.x, obj.geometry.y
        
        # Use symbol if available
        if 'outlet' in self.symbol_registry:
            return f'    <use href="#outlet-symbol" x="{x}" y="{y}" ' \
                   f'id="arx-{obj.id}" class="electrical-outlet" ' \
                   f'arx:id="{obj.id}" arx:voltage="{obj.properties.get("voltage", 120)}"/>\n'
        
        # Fallback to basic shape
        return f'    <circle cx="{x}" cy="{y}" r="8" ' \
               f'id="arx-{obj.id}" class="electrical-outlet" ' \
               f'arx:id="{obj.id}"/>\n'
    
    def _render_panel(self, obj) -> str:
        """Render electrical panel."""
        x, y = obj.geometry.x, obj.geometry.y
        w, h = obj.geometry.width, obj.geometry.height
        
        svg = f'    <g id="arx-{obj.id}" class="electrical-panel">\n'
        svg += f'      <rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}"/>\n'
        
        # Add breaker lines
        breaker_count = obj.properties.get('breaker_count', 20)
        for i in range(min(breaker_count, 10)):  # Limit visual breakers
            y_offset = y - h/2 + (i+1) * h/11
            svg += f'      <line x1="{x-w/2+2}" y1="{y_offset}" ' \
                   f'x2="{x+w/2-2}" y2="{y_offset}" class="breaker-line"/>\n'
        
        svg += '    </g>\n'
        return svg
    
    def _render_structural(self, obj) -> str:
        """Render structural element."""
        x, y = obj.geometry.x, obj.geometry.y
        w, h = obj.geometry.width, obj.geometry.height
        
        element_class = obj.type.lower().replace('_', '-')
        
        if obj.type == 'STRUCTURAL_COLUMN':
            # Column with cross-hatch
            svg = f'    <g id="arx-{obj.id}" class="{element_class}">\n'
            svg += f'      <rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}"/>\n'
            svg += f'      <line x1="{x-w/2}" y1="{y-h/2}" x2="{x+w/2}" y2="{y+h/2}"/>\n'
            svg += f'      <line x1="{x-w/2}" y1="{y+h/2}" x2="{x+w/2}" y2="{y-h/2}"/>\n'
            svg += '    </g>\n'
            return svg
        else:
            # Generic structural rectangle
            return f'    <rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" ' \
                   f'id="arx-{obj.id}" class="{element_class}"/>\n'
    
    def _render_plumbing(self, obj) -> str:
        """Render plumbing element."""
        if obj.type == 'PLUMBING_PIPE':
            # Render as line
            x1, y1 = obj.geometry.x, obj.geometry.y
            x2 = x1 + obj.geometry.length
            y2 = y1
            
            return f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" ' \
                   f'id="arx-{obj.id}" class="plumbing-pipe" ' \
                   f'stroke-width="{obj.properties.get("diameter", 20)}"/>\n'
        
        return self._render_generic(obj)
    
    def _render_generic(self, obj) -> str:
        """Render generic ArxObject."""
        x, y = obj.geometry.x, obj.geometry.y
        w, h = obj.geometry.width, obj.geometry.height
        
        return f'    <rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" ' \
               f'id="arx-{obj.id}" class="arxobject"/>\n'
    
    async def _compile_to_json(
        self,
        arxobjects: List,
        options: Dict[str, Any]
    ) -> str:
        """Compile ArxObjects to JSON format."""
        data = {
            'version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'object_count': len(arxobjects),
            'objects': []
        }
        
        for obj in arxobjects:
            obj_data = {
                'id': obj.id,
                'type': obj.type,
                'geometry': {
                    'x': obj.geometry.x,
                    'y': obj.geometry.y,
                    'z': obj.geometry.z,
                    'width': obj.geometry.width,
                    'height': obj.geometry.height,
                    'length': obj.geometry.length,
                },
                'properties': obj.properties or {},
                'precision': obj.precision,
                'active': obj.active
            }
            
            # Add relationships if requested
            if options.get('include_relationships'):
                # Fetch relationships
                pass
            
            data['objects'].append(obj_data)
        
        return json.dumps(data, indent=2 if options.get('pretty') else None)
    
    async def _compile_to_ifc(
        self,
        arxobjects: List,
        options: Dict[str, Any]
    ) -> str:
        """Compile ArxObjects to IFC format."""
        # IFC header
        ifc = "ISO-10303-21;\n"
        ifc += "HEADER;\n"
        ifc += f"FILE_DESCRIPTION(('ArxOS IFC Export'),'{datetime.utcnow().isoformat()}');\n"
        ifc += "FILE_NAME('arxos_export.ifc');\n"
        ifc += "FILE_SCHEMA(('IFC4'));\n"
        ifc += "ENDSEC;\n\n"
        
        ifc += "DATA;\n"
        
        # Convert each ArxObject to IFC entity
        entity_id = 1
        for obj in arxobjects:
            ifc += self._arxobject_to_ifc(obj, entity_id)
            entity_id += 1
        
        ifc += "ENDSEC;\n"
        ifc += "END-ISO-10303-21;\n"
        
        return ifc
    
    def _arxobject_to_ifc(self, obj, entity_id: int) -> str:
        """Convert ArxObject to IFC entity."""
        # Map ArxObject types to IFC classes
        type_map = {
            'ELECTRICAL_OUTLET': 'IfcOutlet',
            'ELECTRICAL_PANEL': 'IfcElectricDistributionBoard',
            'STRUCTURAL_COLUMN': 'IfcColumn',
            'STRUCTURAL_BEAM': 'IfcBeam',
            'STRUCTURAL_WALL': 'IfcWall',
        }
        
        ifc_class = type_map.get(obj.type, 'IfcBuildingElement')
        
        # Create IFC entity
        ifc = f"#{entity_id}={ifc_class}("
        ifc += f"'{obj.id}',#2,$,'{obj.type}',$,#10,#20,$);\n"
        
        return ifc
    
    def _calculate_viewport(self, arxobjects: List) -> Dict[str, float]:
        """Calculate viewport bounds from ArxObjects."""
        if not arxobjects:
            return {'min_x': 0, 'min_y': 0, 'width': 1000, 'height': 1000}
        
        min_x = min(obj.geometry.x for obj in arxobjects)
        max_x = max(obj.geometry.x for obj in arxobjects)
        min_y = min(obj.geometry.y for obj in arxobjects)
        max_y = max(obj.geometry.y for obj in arxobjects)
        
        # Add padding
        padding = 50
        return {
            'min_x': min_x - padding,
            'min_y': min_y - padding,
            'width': max_x - min_x + 2 * padding,
            'height': max_y - min_y + 2 * padding
        }
    
    def _generate_svg_header(
        self,
        viewport: Dict[str, float],
        options: Dict[str, Any]
    ) -> str:
        """Generate SVG header with viewport."""
        width = options.get('width', 1000)
        height = options.get('height', 800)
        
        svg = '<?xml version="1.0" encoding="UTF-8"?>\n'
        svg += f'<svg xmlns="http://www.w3.org/2000/svg" '
        svg += f'xmlns:arx="http://arxos.io/svgx" '
        svg += f'width="{width}" height="{height}" '
        svg += f'viewBox="{viewport["min_x"]} {viewport["min_y"]} '
        svg += f'{viewport["width"]} {viewport["height"]}">\n'
        
        # Add title and description
        svg += '  <title>ArxOS Building Diagram</title>\n'
        svg += '  <desc>Generated from ArxObject engine</desc>\n'
        
        return svg
    
    def _generate_styles(self, arxobjects: List) -> str:
        """Generate CSS styles for ArxObjects."""
        styles = '  <style>\n'
        
        # Base styles
        for selector, style in self.style_registry.items():
            styles += f'    {selector} {{ {style} }}\n'
        
        # Dynamic styles based on objects
        systems = set(self._get_system(obj.type) for obj in arxobjects)
        for system in systems:
            color = self._get_system_color(system)
            styles += f'    .{system}-system {{ stroke: {color}; }}\n'
        
        styles += '  </style>\n'
        return styles
    
    def _group_by_system(self, arxobjects: List) -> Dict[str, List]:
        """Group ArxObjects by system type."""
        grouped = {}
        for obj in arxobjects:
            system = self._get_system(obj.type)
            if system not in grouped:
                grouped[system] = []
            grouped[system].append(obj)
        return grouped
    
    def _get_system(self, object_type: str) -> str:
        """Get system from object type."""
        if 'ELECTRICAL' in object_type:
            return 'electrical'
        elif 'STRUCTURAL' in object_type:
            return 'structural'
        elif 'PLUMBING' in object_type:
            return 'plumbing'
        elif 'HVAC' in object_type:
            return 'hvac'
        return 'general'
    
    def _get_system_color(self, system: str) -> str:
        """Get color for system type."""
        colors = {
            'electrical': '#ff0000',
            'structural': '#000000',
            'plumbing': '#0000ff',
            'hvac': '#00ff00',
            'general': '#666666'
        }
        return colors.get(system, '#999999')
    
    async def _generate_dimensions(self, arxobjects: List) -> str:
        """Generate dimension lines for ArxObjects."""
        svg = '  <g id="dimensions" class="dimension-layer">\n'
        
        # Add dimension lines between objects
        # This would calculate and render dimension lines
        
        svg += '  </g>\n'
        return svg
    
    async def _generate_labels(self, arxobjects: List) -> str:
        """Generate labels for ArxObjects."""
        svg = '  <g id="labels" class="label-layer">\n'
        
        for obj in arxobjects:
            x, y = obj.geometry.x, obj.geometry.y
            label = f"{obj.type.split('_')[-1]} {obj.id}"
            
            svg += f'    <text x="{x}" y="{y-10}" class="object-label">{label}</text>\n'
        
        svg += '  </g>\n'
        return svg
    
    def _optimize_svg(self, svg: str) -> str:
        """Optimize SVG output."""
        import re
        
        # Remove unnecessary whitespace
        svg = re.sub(r'\s+', ' ', svg)
        svg = re.sub(r'> <', '><', svg)
        
        # Remove empty attributes
        svg = re.sub(r'\s+[a-z-]+=""', '', svg)
        
        # Consolidate transforms
        # More optimization could be added
        
        return svg
    
    def _init_styles(self) -> Dict[str, str]:
        """Initialize style registry."""
        return {
            '.electrical-outlet': 'fill: none; stroke: #ff0000; stroke-width: 2;',
            '.electrical-panel': 'fill: #ffeeee; stroke: #ff0000; stroke-width: 2;',
            '.structural-column': 'fill: #cccccc; stroke: #000000; stroke-width: 3;',
            '.structural-wall': 'fill: #eeeeee; stroke: #000000; stroke-width: 2;',
            '.plumbing-pipe': 'stroke: #0000ff; stroke-width: 2; fill: none;',
            '.object-label': 'font-size: 10px; font-family: Arial;',
            '.dimension-layer': 'stroke: #999999; stroke-width: 0.5;',
        }
    
    def _init_symbols(self) -> Dict[str, str]:
        """Initialize symbol registry."""
        # Define reusable symbols
        return {
            'outlet': '<symbol id="outlet-symbol"><circle r="8"/><line x1="-4" x2="4"/></symbol>',
            'switch': '<symbol id="switch-symbol"><rect width="16" height="16"/></symbol>',
        }
    
    async def compile_with_validation(
        self,
        min_x: float, min_y: float,
        max_x: float, max_y: float,
        output_format: str = 'svg'
    ) -> Dict[str, Any]:
        """
        Compile with constraint validation.
        
        Returns both the compiled output and validation results.
        """
        # Query objects
        arxobjects = await self.arxobject_client.query_region(
            min_x, min_y, 0, max_x, max_y, 100
        )
        
        # Validate each object
        violations = []
        for obj in arxobjects:
            collisions = await self.arxobject_client.check_collisions(obj.id)
            if collisions:
                violations.append({
                    'object_id': obj.id,
                    'type': 'collision',
                    'details': collisions
                })
        
        # Compile output
        output = await self.compile_region(
            min_x, min_y, max_x, max_y, output_format
        )
        
        return {
            'output': output,
            'validation': {
                'valid': len(violations) == 0,
                'violations': violations
            },
            'statistics': {
                'object_count': len(arxobjects),
                'systems': list(set(self._get_system(obj.type) for obj in arxobjects))
            }
        }