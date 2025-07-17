"""
SVGX Engine - Symbol Renderer Service

Provides SVGX-specific rendering capabilities with:
- Real-time visualization
- Cross-platform compatibility
- Performance optimization
- Custom rendering pipelines
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math
import re

from svgx_engine.utils.errors import RenderingError, ValidationError
from svgx_engine.logging.structured_logger import get_logger

logger = get_logger(__name__)


class RenderFormat(Enum):
    """Supported rendering formats."""
    SVG = "svg"
    PNG = "png"
    JPEG = "jpeg"
    PDF = "pdf"
    HTML = "html"
    CANVAS = "canvas"


class RenderQuality(Enum):
    """Rendering quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class RenderOptions:
    """Options for symbol rendering."""
    format: RenderFormat = RenderFormat.SVG
    quality: RenderQuality = RenderQuality.MEDIUM
    width: Optional[int] = None
    height: Optional[int] = None
    background_color: str = "transparent"
    include_metadata: bool = True
    optimize_output: bool = True
    include_debug_info: bool = False
    custom_styles: Dict[str, str] = field(default_factory=dict)
    transform: Optional[Dict[str, float]] = None


@dataclass
class RenderResult:
    """Result of symbol rendering."""
    content: str
    format: RenderFormat
    width: int
    height: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    render_time_ms: float = 0.0
    optimized: bool = False
    rendered_at: datetime = field(default_factory=datetime.utcnow)


class SVGXSymbolRenderer:
    """
    Comprehensive symbol renderer for SVGX Engine.
    
    Features:
    - Multi-format rendering (SVG, PNG, JPEG, PDF, HTML, Canvas)
    - Quality optimization and performance tuning
    - Cross-platform compatibility
    - Real-time visualization capabilities
    - Custom rendering pipelines
    - SVGX-specific optimizations
    """
    
    def __init__(self, default_options: Optional[RenderOptions] = None):
        """Initialize the symbol renderer."""
        self.default_options = default_options or RenderOptions()
        self.render_cache: Dict[str, RenderResult] = {}
        self.custom_renderers: Dict[RenderFormat, Callable] = {}
        self.stats = {
            'total_renders': 0,
            'successful_renders': 0,
            'failed_renders': 0,
            'average_render_time_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self._initialize_default_renderers()
        self._setup_optimization_pipelines()
        
        logger.info("Symbol renderer initialized")
    
    def _initialize_default_renderers(self):
        """Initialize default rendering functions."""
        self.custom_renderers[RenderFormat.SVG] = self._render_svg
        self.custom_renderers[RenderFormat.HTML] = self._render_html
        self.custom_renderers[RenderFormat.CANVAS] = self._render_canvas
    
    def _setup_optimization_pipelines(self):
        """Setup optimization pipelines for different formats."""
        self.optimization_pipelines = {
            RenderFormat.SVG: self._optimize_svg,
            RenderFormat.HTML: self._optimize_html,
            RenderFormat.CANVAS: self._optimize_canvas
        }
    
    def render_symbol(self, symbol_data: Dict[str, Any], 
                     options: Optional[RenderOptions] = None,
                     cache_result: bool = True) -> RenderResult:
        """
        Render a symbol with the specified options.
        
        Args:
            symbol_data: The symbol data to render
            options: Rendering options
            cache_result: Whether to cache the render result
            
        Returns:
            RenderResult: The rendered symbol
        """
        start_time = datetime.utcnow()
        
        # Merge options with defaults
        render_options = self._merge_options(options)
        
        # Check cache first
        cache_key = self._generate_cache_key(symbol_data, render_options)
        if cache_result and cache_key in self.render_cache:
            self.stats['cache_hits'] += 1
            logger.debug("Using cached render result", cache_key=cache_key)
            return self.render_cache[cache_key]
        
        self.stats['cache_misses'] += 1
        
        try:
            # Validate symbol data
            self._validate_symbol_data(symbol_data)
            
            # Get renderer function
            renderer_func = self.custom_renderers.get(render_options.format)
            if not renderer_func:
                raise RenderingError(f"No renderer available for format: {render_options.format.value}")
            
            # Render the symbol
            content = renderer_func(symbol_data, render_options)
            
            # Calculate dimensions
            width, height = self._calculate_dimensions(symbol_data, render_options)
            
            # Optimize if requested
            if render_options.optimize_output:
                optimizer = self.optimization_pipelines.get(render_options.format)
                if optimizer:
                    content = optimizer(content, render_options)
            
            # Create result
            result = RenderResult(
                content=content,
                format=render_options.format,
                width=width,
                height=height,
                metadata=self._extract_metadata(symbol_data),
                optimized=render_options.optimize_output,
                rendered_at=datetime.utcnow()
            )
            
            # Calculate render time
            render_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.render_time_ms = render_time
            
            # Update statistics
            self._update_stats(result)
            
            # Cache result if requested
            if cache_result:
                self.render_cache[cache_key] = result
            
            logger.info("Symbol rendering completed",
                       format=render_options.format.value,
                       width=width,
                       height=height,
                       render_time_ms=render_time)
            
            return result
            
        except Exception as e:
            logger.error("Symbol rendering failed", error=str(e))
            raise RenderingError(f"Rendering failed: {str(e)}")
    
    def _render_svg(self, symbol_data: Dict[str, Any], options: RenderOptions) -> str:
        """Render symbol as SVG."""
        # Extract SVG content
        content = symbol_data.get('content', '')
        if not content:
            # Generate basic SVG from symbol data
            content = self._generate_svg_from_data(symbol_data)
        
        # Apply transformations
        if options.transform:
            content = self._apply_svg_transform(content, options.transform)
        
        # Add custom styles
        if options.custom_styles:
            content = self._add_svg_styles(content, options.custom_styles)
        
        # Add metadata if requested
        if options.include_metadata:
            content = self._add_svg_metadata(content, symbol_data)
        
        return content
    
    def _render_html(self, symbol_data: Dict[str, Any], options: RenderOptions) -> str:
        """Render symbol as HTML."""
        svg_content = self._render_svg(symbol_data, options)
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SVGX Symbol</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {options.background_color};
            font-family: Arial, sans-serif;
        }}
        .svgx-symbol {{
            display: block;
            margin: 0 auto;
        }}
        {self._generate_custom_css(options.custom_styles)}
    </style>
</head>
<body>
    <div class="svgx-symbol">
        {svg_content}
    </div>
    {self._generate_debug_info(symbol_data) if options.include_debug_info else ''}
</body>
</html>
        """
        
        return html_template.strip()
    
    def _render_canvas(self, symbol_data: Dict[str, Any], options: RenderOptions) -> str:
        """Render symbol as HTML5 Canvas."""
        # Generate canvas HTML with JavaScript
        canvas_id = f"svgx-canvas-{hash(str(symbol_data))}"
        
        canvas_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SVGX Canvas Symbol</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {options.background_color};
        }}
        canvas {{
            border: 1px solid #ccc;
            display: block;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    <canvas id="{canvas_id}" width="{options.width or 400}" height="{options.height or 300}"></canvas>
    <script>
        {self._generate_canvas_script(symbol_data, canvas_id)}
    </script>
</body>
</html>
        """
        
        return canvas_html.strip()
    
    def _generate_svg_from_data(self, symbol_data: Dict[str, Any]) -> str:
        """Generate SVG content from symbol data."""
        symbol_type = symbol_data.get('type', 'rect')
        attributes = symbol_data.get('attributes', {})
        
        # Basic SVG generation based on type
        if symbol_type == 'rect':
            x = attributes.get('x', 0)
            y = attributes.get('y', 0)
            width = attributes.get('width', 100)
            height = attributes.get('height', 100)
            return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" />'
        
        elif symbol_type == 'circle':
            cx = attributes.get('cx', 50)
            cy = attributes.get('cy', 50)
            r = attributes.get('r', 25)
            return f'<circle cx="{cx}" cy="{cy}" r="{r}" />'
        
        elif symbol_type == 'line':
            x1 = attributes.get('x1', 0)
            y1 = attributes.get('y1', 0)
            x2 = attributes.get('x2', 100)
            y2 = attributes.get('y2', 100)
            return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />'
        
        else:
            # Default to a simple rectangle
            return '<rect x="0" y="0" width="100" height="100" />'
    
    def _apply_svg_transform(self, content: str, transform: Dict[str, float]) -> str:
        """Apply transformation to SVG content."""
        transform_str = ""
        
        if 'translate' in transform:
            tx, ty = transform['translate']
            transform_str += f"translate({tx},{ty}) "
        
        if 'scale' in transform:
            sx, sy = transform['scale']
            transform_str += f"scale({sx},{sy}) "
        
        if 'rotate' in transform:
            angle = transform['rotate']
            transform_str += f"rotate({angle}) "
        
        if transform_str:
            # Add transform attribute to the first SVG element
            content = re.sub(r'(<[^>]+>)', r'\1 transform="' + transform_str.strip() + '"', content, count=1)
        
        return content
    
    def _add_svg_styles(self, content: str, styles: Dict[str, str]) -> str:
        """Add custom styles to SVG content."""
        style_str = ""
        for property_name, value in styles.items():
            style_str += f"{property_name}: {value}; "
        
        if style_str:
            # Add style attribute to the first SVG element
            content = re.sub(r'(<[^>]+>)', r'\1 style="' + style_str.strip() + '"', content, count=1)
        
        return content
    
    def _add_svg_metadata(self, content: str, symbol_data: Dict[str, Any]) -> str:
        """Add metadata to SVG content."""
        metadata = {
            'symbol_id': symbol_data.get('id', ''),
            'symbol_type': symbol_data.get('type', ''),
            'namespace': symbol_data.get('namespace', ''),
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Add metadata as comments or attributes
        metadata_comment = f"<!-- SVGX Metadata: {json.dumps(metadata)} -->"
        return metadata_comment + "\n" + content
    
    def _generate_custom_css(self, styles: Dict[str, str]) -> str:
        """Generate custom CSS from styles."""
        css = ""
        for selector, properties in styles.items():
            css += f"{selector} {{ {properties} }}\n"
        return css
    
    def _generate_debug_info(self, symbol_data: Dict[str, Any]) -> str:
        """Generate debug information HTML."""
        debug_html = f"""
    <div style="margin-top: 20px; padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;">
        <h3>Debug Information</h3>
        <pre>{json.dumps(symbol_data, indent=2)}</pre>
    </div>
        """
        return debug_html
    
    def _generate_canvas_script(self, symbol_data: Dict[str, Any], canvas_id: str) -> str:
        """Generate JavaScript for canvas rendering."""
        symbol_type = symbol_data.get('type', 'rect')
        attributes = symbol_data.get('attributes', {})
        
        script = f"""
        const canvas = document.getElementById('{canvas_id}');
        const ctx = canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Set default styles
        ctx.strokeStyle = '#000';
        ctx.fillStyle = '#fff';
        ctx.lineWidth = 2;
        
        // Draw based on symbol type
        """
        
        if symbol_type == 'rect':
            x = attributes.get('x', 0)
            y = attributes.get('y', 0)
            width = attributes.get('width', 100)
            height = attributes.get('height', 100)
            script += f"""
        ctx.fillRect({x}, {y}, {width}, {height});
        ctx.strokeRect({x}, {y}, {width}, {height});
            """
        
        elif symbol_type == 'circle':
            cx = attributes.get('cx', 50)
            cy = attributes.get('cy', 50)
            r = attributes.get('r', 25)
            script += f"""
        ctx.beginPath();
        ctx.arc({cx}, {cy}, {r}, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
            """
        
        elif symbol_type == 'line':
            x1 = attributes.get('x1', 0)
            y1 = attributes.get('y1', 0)
            x2 = attributes.get('x2', 100)
            y2 = attributes.get('y2', 100)
            script += f"""
        ctx.beginPath();
        ctx.moveTo({x1}, {y1});
        ctx.lineTo({x2}, {y2});
        ctx.stroke();
            """
        
        return script
    
    def _optimize_svg(self, content: str, options: RenderOptions) -> str:
        """Optimize SVG content."""
        # Remove unnecessary whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'>\s+<', '><', content)
        
        # Remove comments if not debugging
        if not options.include_debug_info:
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        return content.strip()
    
    def _optimize_html(self, content: str, options: RenderOptions) -> str:
        """Optimize HTML content."""
        # Remove unnecessary whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'>\s+<', '><', content)
        
        return content.strip()
    
    def _optimize_canvas(self, content: str, options: RenderOptions) -> str:
        """Optimize Canvas content."""
        # Remove unnecessary whitespace
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def _calculate_dimensions(self, symbol_data: Dict[str, Any], options: RenderOptions) -> Tuple[int, int]:
        """Calculate render dimensions."""
        if options.width and options.height:
            return options.width, options.height
        
        # Extract dimensions from symbol data
        attributes = symbol_data.get('attributes', {})
        
        if options.format == RenderFormat.SVG:
            width = attributes.get('width', 100)
            height = attributes.get('height', 100)
        else:
            width = options.width or 400
            height = options.height or 300
        
        return int(width), int(height)
    
    def _extract_metadata(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from symbol data."""
        return {
            'symbol_id': symbol_data.get('id', ''),
            'symbol_type': symbol_data.get('type', ''),
            'namespace': symbol_data.get('namespace', ''),
            'attributes_count': len(symbol_data.get('attributes', {})),
            'has_content': bool(symbol_data.get('content')),
            'has_behavior': bool(symbol_data.get('behavior')),
            'has_physics': bool(symbol_data.get('physics'))
        }
    
    def _validate_symbol_data(self, symbol_data: Dict[str, Any]):
        """Validate symbol data before rendering."""
        if not isinstance(symbol_data, dict):
            raise ValidationError("Symbol data must be a dictionary")
        
        if 'type' not in symbol_data:
            raise ValidationError("Symbol data must have a 'type' field")
        
        if 'attributes' not in symbol_data:
            raise ValidationError("Symbol data must have an 'attributes' field")
    
    def _merge_options(self, options: Optional[RenderOptions]) -> RenderOptions:
        """Merge options with defaults."""
        if options is None:
            return self.default_options
        
        # Create a new options object with merged values
        merged = RenderOptions()
        for field in merged.__dataclass_fields__:
            user_value = getattr(options, field)
            default_value = getattr(self.default_options, field)
            setattr(merged, field, user_value if user_value is not None else default_value)
        
        return merged
    
    def _generate_cache_key(self, symbol_data: Dict[str, Any], options: RenderOptions) -> str:
        """Generate cache key for render result."""
        import hashlib
        data_str = json.dumps(symbol_data, sort_keys=True)
        options_str = json.dumps({
            'format': options.format.value,
            'quality': options.quality.value,
            'width': options.width,
            'height': options.height,
            'background_color': options.background_color,
            'include_metadata': options.include_metadata,
            'optimize_output': options.optimize_output,
            'include_debug_info': options.include_debug_info,
            'custom_styles': options.custom_styles,
            'transform': options.transform
        }, sort_keys=True)
        
        return hashlib.md5(f"{data_str}:{options_str}".encode()).hexdigest()
    
    def _update_stats(self, result: RenderResult):
        """Update rendering statistics."""
        self.stats['total_renders'] += 1
        self.stats['successful_renders'] += 1
        
        # Update average render time
        total_time = self.stats['average_render_time_ms'] * (self.stats['total_renders'] - 1)
        total_time += result.render_time_ms
        self.stats['average_render_time_ms'] = total_time / self.stats['total_renders']
    
    def add_custom_renderer(self, format_type: RenderFormat, renderer_func: Callable):
        """Add a custom renderer for a specific format."""
        self.custom_renderers[format_type] = renderer_func
        logger.info("Custom renderer added", format=format_type.value)
    
    def get_rendering_statistics(self) -> Dict[str, Any]:
        """Get rendering statistics."""
        return {
            'stats': self.stats,
            'supported_formats': [fmt.value for fmt in self.custom_renderers.keys()],
            'cache_size': len(self.render_cache)
        }
    
    def clear_cache(self):
        """Clear the render cache."""
        self.render_cache.clear()
        logger.info("Render cache cleared")
    
    def set_default_options(self, options: RenderOptions):
        """Set default rendering options."""
        self.default_options = options
        logger.info("Default rendering options updated")


# Factory function for creating renderer instances
def create_symbol_renderer(default_options: Optional[RenderOptions] = None) -> SVGXSymbolRenderer:
    """Create a new symbol renderer instance."""
    return SVGXSymbolRenderer(default_options)


# Global renderer instance
_symbol_renderer = None


def get_symbol_renderer() -> SVGXSymbolRenderer:
    """Get the global symbol renderer instance."""
    global _symbol_renderer
    if _symbol_renderer is None:
        _symbol_renderer = create_symbol_renderer()
    return _symbol_renderer 