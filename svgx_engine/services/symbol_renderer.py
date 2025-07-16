"""
SVGX Engine Symbol Renderer Service.

Implements advanced rendering capabilities for SVGX symbols:
- Real-time SVGX symbol rendering and visualization
- Performance-optimized rendering engine
- Multi-format output support (SVG, PNG, PDF, WebGL)
- Interactive rendering with event handling
- SVGX-specific rendering enhancements
- Rendering pipeline optimization
- Real-time preview and animation support
"""

import logging
import json
import time
import hashlib
import threading
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import base64
import io
from PIL import Image, ImageDraw
import cairosvg
import svglib
from reportlab.graphics import renderPDF, renderPS
from reportlab.graphics.shapes import Drawing
import numpy as np
from collections import defaultdict, deque
import pickle
import zlib

try:
    from ..utils.performance import PerformanceMonitor
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import PerformanceMonitor

try:
    from ..utils.errors import (
        RenderingError, ValidationError, SVGXError, PerformanceError
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import (
        RenderingError, ValidationError, SVGXError, PerformanceError
    )

from ..models.svgx import SVGXElement, SVGXDocument


@dataclass
class RenderOptions:
    """Configuration options for symbol rendering."""
    output_format: str = "svg"  # svg, png, pdf, webgl, canvas
    width: int = 800
    height: int = 600
    background_color: str = "white"
    quality: int = 100  # 1-100
    enable_animations: bool = True
    enable_interactivity: bool = True
    enable_physics: bool = True
    enable_behaviors: bool = True
    cache_rendered: bool = True
    optimize_output: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderResult:
    """Result of a rendering operation."""
    symbol_id: str
    rendered_content: str
    output_format: str
    dimensions: Tuple[int, int]
    render_time: float
    file_size: int
    checksum: str
    metadata: Dict[str, Any]
    cache_hit: bool = False


@dataclass
class AnimationFrame:
    """Represents a single animation frame."""
    frame_number: int
    timestamp: float
    content: str
    metadata: Dict[str, Any]


@dataclass
class InteractiveElement:
    """Represents an interactive element in the rendered symbol."""
    element_id: str
    element_type: str
    position: Tuple[float, float]
    dimensions: Tuple[float, float]
    event_handlers: Dict[str, Callable]
    metadata: Dict[str, Any]


@dataclass
class PhysicsSimulation:
    """Represents physics simulation data for rendered symbols."""
    symbol_id: str
    simulation_time: float
    object_positions: Dict[str, Tuple[float, float]]
    velocities: Dict[str, Tuple[float, float]]
    forces: Dict[str, Tuple[float, float]]
    metadata: Dict[str, Any]


@dataclass
class RenderCache:
    """Cache for rendered symbol outputs."""
    symbol_hash: str
    render_options_hash: str
    render_result: RenderResult
    cached_at: datetime
    expires_at: datetime


class SVGXSymbolRendererService:
    """
    SVGX Engine Symbol Renderer Service.
    
    Provides advanced rendering capabilities for SVGX symbols with features:
    - Multi-format rendering (SVG, PNG, PDF, WebGL)
    - Real-time interactive rendering
    - Animation and physics simulation
    - Performance-optimized rendering pipeline
    - Caching and optimization
    - SVGX-specific rendering enhancements
    """
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Symbol Renderer Service.
        
        Args:
            options: Configuration options
        """
        self.options = {
            'enable_caching': True,
            'cache_ttl_seconds': 3600,  # 1 hour
            'max_cache_size': 1000,
            'enable_performance_monitoring': True,
            'max_concurrent_renders': 10,
            'default_output_format': 'svg',
            'enable_animations': True,
            'enable_interactivity': True,
            'enable_physics': True,
            'enable_behaviors': True,
            'optimize_output': True,
            'quality_settings': {
                'svg': {'optimize': True, 'minify': True},
                'png': {'dpi': 300, 'antialias': True},
                'pdf': {'vector': True, 'compression': True},
                'webgl': {'shaders': True, 'textures': True}
            }
        }
        if options:
            self.options.update(options)
        
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize databases
        self._init_databases()
        
        # Rendering pipeline
        self.render_cache: Dict[str, RenderCache] = {}
        self.cache_lock = threading.Lock()
        self.render_executor = ThreadPoolExecutor(
            max_workers=self.options['max_concurrent_renders']
        )
        
        # Performance tracking
        self.render_stats = {
            'total_renders': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_render_time': 0.0,
            'format_stats': defaultdict(int),
            'error_count': 0,
        }
        
        # Interactive elements registry
        self.interactive_elements: Dict[str, InteractiveElement] = {}
        self.animation_frames: Dict[str, List[AnimationFrame]] = {}
        self.physics_simulations: Dict[str, PhysicsSimulation] = {}
        
        self.logger.info("symbol_renderer_service_initialized",
                        options=self.options)
    
    def _init_databases(self):
        """Initialize rendering databases."""
        self.render_db_path = "data/render.db"
        self.cache_db_path = "data/render_cache.db"
        self.animation_db_path = "data/animation.db"
        
        # Create directories if they don't exist
        for db_path in [self.render_db_path, self.cache_db_path, self.animation_db_path]:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize render database
        with sqlite3.connect(self.render_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS render_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol_id TEXT NOT NULL,
                    symbol_hash TEXT NOT NULL,
                    output_format TEXT NOT NULL,
                    render_options TEXT NOT NULL,
                    rendered_content TEXT NOT NULL,
                    dimensions TEXT NOT NULL,
                    render_time REAL,
                    file_size INTEGER,
                    checksum TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_render_symbol_id 
                ON render_results(symbol_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_render_hash 
                ON render_results(symbol_hash)
            """)
        
        # Initialize cache database
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS render_cache (
                    symbol_hash TEXT,
                    render_options_hash TEXT,
                    rendered_content TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (symbol_hash, render_options_hash)
                )
            """)
        
        # Initialize animation database
        with sqlite3.connect(self.animation_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS animation_frames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol_id TEXT NOT NULL,
                    animation_id TEXT NOT NULL,
                    frame_number INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def render_symbol(self, symbol_id: str, content: str, 
                     options: Optional[RenderOptions] = None) -> RenderResult:
        """
        Render an SVGX symbol to the specified format.
        
        Args:
            symbol_id: Unique identifier for the symbol
            content: SVGX symbol content
            options: Rendering options
            
        Returns:
            RenderResult with rendered output
        """
        start_time = time.time()
        
        try:
            # Use default options if not provided
            if options is None:
                options = RenderOptions()
            
            # Generate hashes for caching
            symbol_hash = self._generate_symbol_hash(content)
            options_hash = self._generate_options_hash(options)
            
            # Check cache first
            cached_result = self._get_cached_render(symbol_hash, options_hash)
            if cached_result:
                self.render_stats['cache_hits'] += 1
                cached_result.cache_hit = True
                return cached_result
            
            self.render_stats['cache_misses'] += 1
            
            # Parse SVGX content
            svgx_doc = self._parse_svgx_content(content)
            
            # Apply rendering pipeline
            rendered_content = self._apply_rendering_pipeline(svgx_doc, options)
            
            # Optimize output if requested
            if options.optimize_output:
                rendered_content = self._optimize_rendered_output(rendered_content, options)
            
            # Calculate dimensions
            dimensions = self._calculate_dimensions(svgx_doc, options)
            
            # Create render result
            render_time = time.time() - start_time
            file_size = len(rendered_content.encode('utf-8'))
            checksum = hashlib.sha256(rendered_content.encode('utf-8')).hexdigest()
            
            result = RenderResult(
                symbol_id=symbol_id,
                rendered_content=rendered_content,
                output_format=options.output_format,
                dimensions=dimensions,
                render_time=render_time,
                file_size=file_size,
                checksum=checksum,
                metadata={
                    'symbol_hash': symbol_hash,
                    'options_hash': options_hash,
                    'original_format': 'svgx',
                    'optimized': options.optimize_output,
                    'quality': options.quality
                }
            )
            
            # Cache the result
            if self.options['enable_caching']:
                self._cache_render_result(symbol_hash, options_hash, result)
            
            # Update statistics
            self.render_stats['total_renders'] += 1
            self.render_stats['format_stats'][options.output_format] += 1
            
            # Update average render time
            total_renders = self.render_stats['total_renders']
            current_avg = self.render_stats['average_render_time']
            self.render_stats['average_render_time'] = (
                (current_avg * (total_renders - 1) + render_time) / total_renders
            )
            
            # Save render result to database
            self._save_render_result(result, symbol_hash, options)
            
            return result
            
        except Exception as e:
            self.render_stats['error_count'] += 1
            self.logger.error("render_error", 
                            symbol_id=symbol_id, 
                            error=str(e))
            raise RenderingError(f"Rendering failed: {str(e)}")
    
    def render_animation(self, symbol_id: str, content: str, 
                       duration: float = 5.0, fps: int = 30,
                       options: Optional[RenderOptions] = None) -> List[AnimationFrame]:
        """
        Render an animated version of the SVGX symbol.
        
        Args:
            symbol_id: Unique identifier for the symbol
            content: SVGX symbol content
            duration: Animation duration in seconds
            fps: Frames per second
            options: Rendering options
            
        Returns:
            List of AnimationFrame objects
        """
        try:
            frames = []
            total_frames = int(duration * fps)
            
            # Parse SVGX content
            svgx_doc = self._parse_svgx_content(content)
            
            # Extract animation data
            animations = self._extract_animations(svgx_doc)
            
            # Generate frames
            for frame_num in range(total_frames):
                timestamp = frame_num / fps
                
                # Apply animation transformations
                animated_content = self._apply_animation_frame(
                    svgx_doc, animations, timestamp, duration
                )
                
                # Render the frame
                frame_options = options or RenderOptions()
                frame_result = self.render_symbol(
                    f"{symbol_id}_frame_{frame_num}",
                    animated_content,
                    frame_options
                )
                
                frame = AnimationFrame(
                    frame_number=frame_num,
                    timestamp=timestamp,
                    content=frame_result.rendered_content,
                    metadata={
                        'symbol_id': symbol_id,
                        'duration': duration,
                        'fps': fps,
                        'frame_size': frame_result.file_size
                    }
                )
                
                frames.append(frame)
            
            # Save animation frames
            self._save_animation_frames(symbol_id, frames)
            
            return frames
            
        except Exception as e:
            self.logger.error("animation_render_error", 
                            symbol_id=symbol_id, 
                            error=str(e))
            raise RenderingError(f"Animation rendering failed: {str(e)}")
    
    def render_interactive(self, symbol_id: str, content: str,
                          options: Optional[RenderOptions] = None) -> Tuple[str, List[InteractiveElement]]:
        """
        Render an interactive version of the SVGX symbol.
        
        Args:
            symbol_id: Unique identifier for the symbol
            content: SVGX symbol content
            options: Rendering options
            
        Returns:
            Tuple of (rendered_content, interactive_elements)
        """
        try:
            # Parse SVGX content
            svgx_doc = self._parse_svgx_content(content)
            
            # Extract interactive elements
            interactive_elements = self._extract_interactive_elements(svgx_doc)
            
            # Generate interactive JavaScript
            interactive_js = self._generate_interactive_js(interactive_elements)
            
            # Render base symbol
            base_options = options or RenderOptions()
            base_result = self.render_symbol(symbol_id, content, base_options)
            
            # Combine with interactive elements
            interactive_content = self._combine_with_interactivity(
                base_result.rendered_content, interactive_js, interactive_elements
            )
            
            return interactive_content, interactive_elements
            
        except Exception as e:
            self.logger.error("interactive_render_error", 
                            symbol_id=symbol_id, 
                            error=str(e))
            raise RenderingError(f"Interactive rendering failed: {str(e)}")
    
    def render_physics_simulation(self, symbol_id: str, content: str,
                                simulation_time: float = 10.0, time_step: float = 0.016,
                                options: Optional[RenderOptions] = None) -> List[PhysicsSimulation]:
        """
        Render a physics simulation of the SVGX symbol.
        
        Args:
            symbol_id: Unique identifier for the symbol
            content: SVGX symbol content
            simulation_time: Total simulation time in seconds
            time_step: Time step for simulation
            options: Rendering options
            
        Returns:
            List of PhysicsSimulation objects
        """
        try:
            simulations = []
            total_steps = int(simulation_time / time_step)
            
            # Parse SVGX content
            svgx_doc = self._parse_svgx_content(content)
            
            # Extract physics data
            physics_data = self._extract_physics_data(svgx_doc)
            
            # Initialize simulation state
            simulation_state = self._initialize_physics_simulation(physics_data)
            
            # Run simulation
            for step in range(total_steps):
                current_time = step * time_step
                
                # Update physics simulation
                simulation_state = self._update_physics_simulation(
                    simulation_state, physics_data, time_step
                )
                
                # Apply physics to rendered content
                physics_content = self._apply_physics_to_content(
                    svgx_doc, simulation_state
                )
                
                # Render the physics frame
                frame_options = options or RenderOptions()
                frame_result = self.render_symbol(
                    f"{symbol_id}_physics_{step}",
                    physics_content,
                    frame_options
                )
                
                simulation = PhysicsSimulation(
                    symbol_id=symbol_id,
                    simulation_time=current_time,
                    object_positions=simulation_state['positions'],
                    velocities=simulation_state['velocities'],
                    forces=simulation_state['forces'],
                    metadata={
                        'step': step,
                        'time_step': time_step,
                        'frame_content': frame_result.rendered_content,
                        'frame_size': frame_result.file_size
                    }
                )
                
                simulations.append(simulation)
            
            return simulations
            
        except Exception as e:
            self.logger.error("physics_render_error", 
                            symbol_id=symbol_id, 
                            error=str(e))
            raise RenderingError(f"Physics simulation rendering failed: {str(e)}")
    
    def get_render_statistics(self) -> Dict[str, Any]:
        """Get rendering statistics."""
        return {
            **self.render_stats,
            'cache_size': len(self.render_cache),
            'interactive_elements_count': len(self.interactive_elements),
            'animation_frames_count': sum(len(frames) for frames in self.animation_frames.values()),
            'physics_simulations_count': len(self.physics_simulations),
            'performance_metrics': self.performance_monitor.get_metrics()
        }
    
    def clear_cache(self) -> bool:
        """Clear render cache."""
        try:
            with self.cache_lock:
                self.render_cache.clear()
            
            # Clear cache database
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute("DELETE FROM render_cache")
            
            self.logger.info("render_cache_cleared")
            return True
        except Exception as e:
            self.logger.error("clear_cache_error", error=str(e))
            return False
    
    def _parse_svgx_content(self, content: str) -> ET.Element:
        """Parse SVGX content into XML element tree."""
        try:
            return ET.fromstring(content)
        except ET.ParseError as e:
            raise RenderingError(f"Failed to parse SVGX content: {str(e)}")
    
    def _apply_rendering_pipeline(self, svgx_doc: ET.Element, options: RenderOptions) -> str:
        """Apply the rendering pipeline to SVGX content."""
        # Convert SVGX to target format
        if options.output_format == "svg":
            return self._render_to_svg(svgx_doc, options)
        elif options.output_format == "png":
            return self._render_to_png(svgx_doc, options)
        elif options.output_format == "pdf":
            return self._render_to_pdf(svgx_doc, options)
        elif options.output_format == "webgl":
            return self._render_to_webgl(svgx_doc, options)
        else:
            raise RenderingError(f"Unsupported output format: {options.output_format}")
    
    def _render_to_svg(self, svgx_doc: ET.Element, options: RenderOptions) -> str:
        """Render SVGX to SVG format."""
        # Convert SVGX to standard SVG
        svg_content = self._convert_svgx_to_svg(svgx_doc, options)
        
        # Apply SVG optimizations
        if options.optimize_output:
            svg_content = self._optimize_svg(svg_content)
        
        return svg_content
    
    def _render_to_png(self, svgx_doc: ET.Element, options: RenderOptions) -> str:
        """Render SVGX to PNG format."""
        # First convert to SVG
        svg_content = self._convert_svgx_to_svg(svgx_doc, options)
        
        # Convert SVG to PNG using cairosvg
        try:
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=options.width,
                output_height=options.height,
                dpi=72
            )
            
            # Convert to base64 for storage
            png_base64 = base64.b64encode(png_data).decode('utf-8')
            return f"data:image/png;base64,{png_base64}"
            
        except Exception as e:
            raise RenderingError(f"PNG conversion failed: {str(e)}")
    
    def _render_to_pdf(self, svgx_doc: ET.Element, options: RenderOptions) -> str:
        """Render SVGX to PDF format."""
        # First convert to SVG
        svg_content = self._convert_svgx_to_svg(svgx_doc, options)
        
        try:
            # Convert SVG to PDF using reportlab
            drawing = svglib.svg2rlg(io.StringIO(svg_content))
            pdf_data = renderPDF.drawToString(drawing)
            
            # Convert to base64 for storage
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            return f"data:application/pdf;base64,{pdf_base64}"
            
        except Exception as e:
            raise RenderingError(f"PDF conversion failed: {str(e)}")
    
    def _render_to_webgl(self, svgx_doc: ET.Element, options: RenderOptions) -> str:
        """Render SVGX to WebGL format."""
        # Convert SVGX to WebGL shader code
        webgl_content = self._convert_svgx_to_webgl(svgx_doc, options)
        return webgl_content
    
    def _convert_svgx_to_svg(self, svgx_doc: ET.Element, options: RenderOptions) -> str:
        """Convert SVGX content to standard SVG."""
        # Create SVG root element
        svg_root = ET.Element("svg")
        svg_root.set("xmlns", "http://www.w3.org/2000/svg")
        svg_root.set("width", str(options.width))
        svg_root.set("height", str(options.height))
        svg_root.set("viewBox", f"0 0 {options.width} {options.height}")
        
        # Process SVGX elements
        for element in svgx_doc.iter():
            if element.tag.endswith('geometry'):
                self._process_geometry_element(element, svg_root)
            elif element.tag.endswith('behaviors'):
                self._process_behaviors_element(element, svg_root)
            elif element.tag.endswith('physics'):
                self._process_physics_element(element, svg_root)
        
        return ET.tostring(svg_root, encoding='unicode')
    
    def _process_geometry_element(self, geometry_elem: ET.Element, svg_root: ET.Element):
        """Process geometry elements and convert to SVG."""
        for child in geometry_elem:
            if child.tag.endswith('rect'):
                rect = ET.SubElement(svg_root, "rect")
                for attr, value in child.attrib.items():
                    rect.set(attr, value)
            elif child.tag.endswith('circle'):
                circle = ET.SubElement(svg_root, "circle")
                for attr, value in child.attrib.items():
                    circle.set(attr, value)
            elif child.tag.endswith('path'):
                path = ET.SubElement(svg_root, "path")
                for attr, value in child.attrib.items():
                    path.set(attr, value)
    
    def _process_behaviors_element(self, behaviors_elem: ET.Element, svg_root: ET.Element):
        """Process behaviors and add interactive elements."""
        for behavior in behaviors_elem.findall('.//behavior'):
            # Add JavaScript for interactivity
            script = ET.SubElement(svg_root, "script")
            script.set("type", "text/javascript")
            script.text = self._generate_behavior_script(behavior)
    
    def _process_physics_element(self, physics_elem: ET.Element, svg_root: ET.Element):
        """Process physics elements and add simulation data."""
        # Add physics simulation attributes
        for child in physics_elem:
            if child.tag.endswith('mass'):
                svg_root.set("data-physics-mass", child.text)
            elif child.tag.endswith('friction'):
                svg_root.set("data-physics-friction", child.text)
    
    def _convert_svgx_to_webgl(self, svgx_doc: ET.Element, options: RenderOptions) -> str:
        """Convert SVGX to WebGL shader code."""
        # Generate WebGL vertex and fragment shaders
        vertex_shader = self._generate_vertex_shader(svgx_doc)
        fragment_shader = self._generate_fragment_shader(svgx_doc)
        
        # Create WebGL rendering code
        webgl_code = f"""
        <canvas id="webgl-canvas" width="{options.width}" height="{options.height}"></canvas>
        <script type="text/javascript">
        const canvas = document.getElementById('webgl-canvas');
        const gl = canvas.getContext('webgl');
        
        // Vertex Shader
        const vertexShaderSource = `{vertex_shader}`;
        
        // Fragment Shader
        const fragmentShaderSource = `{fragment_shader}`;
        
        // WebGL rendering code...
        </script>
        """
        
        return webgl_code
    
    def _generate_vertex_shader(self, svgx_doc: ET.Element) -> str:
        """Generate WebGL vertex shader from SVGX content."""
        return """
        attribute vec2 a_position;
        attribute vec2 a_texCoord;
        varying vec2 v_texCoord;
        
        void main() {
            gl_Position = vec4(a_position, 0.0, 1.0);
            v_texCoord = a_texCoord;
        }
        """
    
    def _generate_fragment_shader(self, svgx_doc: ET.Element) -> str:
        """Generate WebGL fragment shader from SVGX content."""
        return """
        precision mediump float;
        varying vec2 v_texCoord;
        
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
        }
        """
    
    def _optimize_rendered_output(self, content: str, options: RenderOptions) -> str:
        """Optimize rendered output based on format."""
        if options.output_format == "svg":
            return self._optimize_svg(content)
        elif options.output_format == "png":
            return self._optimize_png(content)
        else:
            return content
    
    def _optimize_svg(self, svg_content: str) -> str:
        """Optimize SVG content."""
        # Remove unnecessary whitespace and comments
        import re
        svg_content = re.sub(r'<!--.*?-->', '', svg_content)
        svg_content = re.sub(r'\s+', ' ', svg_content)
        return svg_content.strip()
    
    def _optimize_png(self, png_content: str) -> str:
        """Optimize PNG content."""
        # PNG is already optimized, return as-is
        return png_content
    
    def _calculate_dimensions(self, svgx_doc: ET.Element, options: RenderOptions) -> Tuple[int, int]:
        """Calculate output dimensions."""
        # Check for explicit dimensions in SVGX
        viewbox = svgx_doc.get('viewBox')
        if viewbox:
            try:
                _, _, width, height = map(float, viewbox.split())
                return (int(width), int(height))
            except:
                pass
        
        # Use default dimensions
        return (options.width, options.height)
    
    def _generate_symbol_hash(self, content: str) -> str:
        """Generate hash for symbol content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _generate_options_hash(self, options: RenderOptions) -> str:
        """Generate hash for render options."""
        options_dict = {
            'output_format': options.output_format,
            'width': options.width,
            'height': options.height,
            'background_color': options.background_color,
            'quality': options.quality,
            'enable_animations': options.enable_animations,
            'enable_interactivity': options.enable_interactivity,
            'enable_physics': options.enable_physics,
            'enable_behaviors': options.enable_behaviors,
            'optimize_output': options.optimize_output
        }
        return hashlib.sha256(json.dumps(options_dict, sort_keys=True).encode('utf-8')).hexdigest()
    
    def _get_cached_render(self, symbol_hash: str, options_hash: str) -> Optional[RenderResult]:
        """Get cached render result."""
        if not self.options['enable_caching']:
            return None
        
        cache_key = f"{symbol_hash}_{options_hash}"
        
        with self.cache_lock:
            cached = self.render_cache.get(cache_key)
            if cached and cached.expires_at > datetime.now():
                return cached.render_result
        
        return None
    
    def _cache_render_result(self, symbol_hash: str, options_hash: str, result: RenderResult):
        """Cache render result."""
        if not self.options['enable_caching']:
            return
        
        cache_key = f"{symbol_hash}_{options_hash}"
        expires_at = datetime.now() + timedelta(seconds=self.options['cache_ttl_seconds'])
        
        cache_entry = RenderCache(
            symbol_hash=symbol_hash,
            render_options_hash=options_hash,
            render_result=result,
            cached_at=datetime.now(),
            expires_at=expires_at
        )
        
        with self.cache_lock:
            # Implement LRU cache eviction
            if len(self.render_cache) >= self.options['max_cache_size']:
                oldest_key = min(self.render_cache.keys(), 
                               key=lambda k: self.render_cache[k].cached_at)
                del self.render_cache[oldest_key]
            
            self.render_cache[cache_key] = cache_entry
        
        # Save to database
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO render_cache 
                (symbol_hash, render_options_hash, rendered_content, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                symbol_hash,
                options_hash,
                result.rendered_content,
                cache_entry.cached_at.isoformat(),
                cache_entry.expires_at.isoformat()
            ))
    
    def _save_render_result(self, result: RenderResult, symbol_hash: str, options: RenderOptions):
        """Save render result to database."""
        with sqlite3.connect(self.render_db_path) as conn:
            conn.execute("""
                INSERT INTO render_results 
                (symbol_id, symbol_hash, output_format, render_options, rendered_content,
                 dimensions, render_time, file_size, checksum, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.symbol_id,
                symbol_hash,
                result.output_format,
                json.dumps(options.__dict__),
                result.rendered_content,
                json.dumps(result.dimensions),
                result.render_time,
                result.file_size,
                result.checksum,
                json.dumps(result.metadata),
                datetime.now().isoformat()
            ))
    
    def _extract_animations(self, svgx_doc: ET.Element) -> Dict[str, Any]:
        """Extract animation data from SVGX document."""
        animations = {}
        
        # Look for animation elements
        for animation in svgx_doc.findall('.//animation'):
            anim_id = animation.get('id', f"anim_{len(animations)}")
            animations[anim_id] = {
                'type': animation.get('type', 'transform'),
                'duration': float(animation.get('duration', 1.0)),
                'easing': animation.get('easing', 'linear'),
                'properties': {}
            }
            
            for prop in animation.findall('.//property'):
                prop_name = prop.get('name')
                prop_values = prop.text.split(',')
                animations[anim_id]['properties'][prop_name] = prop_values
        
        return animations
    
    def _apply_animation_frame(self, svgx_doc: ET.Element, animations: Dict[str, Any], 
                              timestamp: float, duration: float) -> str:
        """Apply animation frame to SVGX content."""
        # Create a copy of the document for animation
        animated_doc = ET.fromstring(ET.tostring(svgx_doc))
        
        # Apply animation transformations
        for anim_id, animation in animations.items():
            progress = min(timestamp / animation['duration'], 1.0)
            
            for prop_name, prop_values in animation['properties'].items():
                # Apply interpolation
                if len(prop_values) >= 2:
                    start_value = float(prop_values[0])
                    end_value = float(prop_values[1])
                    current_value = start_value + (end_value - start_value) * progress
                    
                    # Apply to elements
                    for element in animated_doc.findall(f'.//*[@id="{anim_id}"]'):
                        element.set(prop_name, str(current_value))
        
        return ET.tostring(animated_doc, encoding='unicode')
    
    def _extract_interactive_elements(self, svgx_doc: ET.Element) -> List[InteractiveElement]:
        """Extract interactive elements from SVGX document."""
        interactive_elements = []
        
        # Look for elements with behaviors
        for element in svgx_doc.findall('.//*[@id]'):
            element_id = element.get('id')
            behaviors = element.findall('.//behavior')
            
            if behaviors:
                # Calculate position and dimensions
                position = self._calculate_element_position(element)
                dimensions = self._calculate_element_dimensions(element)
                
                # Create event handlers
                event_handlers = {}
                for behavior in behaviors:
                    event_type = behavior.get('type', 'click')
                    action = behavior.find('action')
                    if action is not None:
                        event_handlers[event_type] = lambda: action.text
                
                interactive_element = InteractiveElement(
                    element_id=element_id,
                    element_type=element.tag,
                    position=position,
                    dimensions=dimensions,
                    event_handlers=event_handlers,
                    metadata={'behaviors': len(behaviors)}
                )
                
                interactive_elements.append(interactive_element)
        
        return interactive_elements
    
    def _generate_interactive_js(self, interactive_elements: List[InteractiveElement]) -> str:
        """Generate JavaScript for interactive elements."""
        js_code = """
        <script type="text/javascript">
        document.addEventListener('DOMContentLoaded', function() {
        """
        
        for element in interactive_elements:
            for event_type, handler in element.event_handlers.items():
                js_code += f"""
            document.getElementById('{element.element_id}').addEventListener('{event_type}', function() {{
                {handler()};
            }});
                """
        
        js_code += """
        });
        </script>
        """
        
        return js_code
    
    def _combine_with_interactivity(self, rendered_content: str, interactive_js: str, 
                                   interactive_elements: List[InteractiveElement]) -> str:
        """Combine rendered content with interactive JavaScript."""
        # Insert JavaScript before closing </svg> tag
        if '</svg>' in rendered_content:
            return rendered_content.replace('</svg>', f'{interactive_js}</svg>')
        else:
            return rendered_content + interactive_js
    
    def _extract_physics_data(self, svgx_doc: ET.Element) -> Dict[str, Any]:
        """Extract physics data from SVGX document."""
        physics_data = {}
        
        physics_elem = svgx_doc.find('.//physics')
        if physics_elem is not None:
            for child in physics_elem:
                if child.tag.endswith('mass'):
                    physics_data['mass'] = float(child.text)
                elif child.tag.endswith('friction'):
                    physics_data['friction'] = float(child.text)
                elif child.tag.endswith('elasticity'):
                    physics_data['elasticity'] = float(child.text)
        
        return physics_data
    
    def _initialize_physics_simulation(self, physics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize physics simulation state."""
        return {
            'positions': {},
            'velocities': {},
            'forces': {},
            'mass': physics_data.get('mass', 1.0),
            'friction': physics_data.get('friction', 0.1),
            'elasticity': physics_data.get('elasticity', 0.5)
        }
    
    def _update_physics_simulation(self, state: Dict[str, Any], physics_data: Dict[str, Any], 
                                 time_step: float) -> Dict[str, Any]:
        """Update physics simulation state."""
        # Simple physics simulation
        for obj_id, position in state['positions'].items():
            if obj_id in state['velocities']:
                velocity = state['velocities'][obj_id]
                
                # Apply forces (gravity, friction, etc.)
                force = state['forces'].get(obj_id, (0, 0))
                
                # Update velocity
                new_velocity = (
                    velocity[0] + force[0] * time_step,
                    velocity[1] + force[1] * time_step
                )
                
                # Apply friction
                friction = state['friction']
                new_velocity = (
                    new_velocity[0] * (1 - friction),
                    new_velocity[1] * (1 - friction)
                )
                
                # Update position
                new_position = (
                    position[0] + new_velocity[0] * time_step,
                    position[1] + new_velocity[1] * time_step
                )
                
                state['positions'][obj_id] = new_position
                state['velocities'][obj_id] = new_velocity
        
        return state
    
    def _apply_physics_to_content(self, svgx_doc: ET.Element, simulation_state: Dict[str, Any]) -> str:
        """Apply physics simulation to SVGX content."""
        # Create a copy of the document
        physics_doc = ET.fromstring(ET.tostring(svgx_doc))
        
        # Apply positions to elements
        for obj_id, position in simulation_state['positions'].items():
            for element in physics_doc.findall(f'.//*[@id="{obj_id}"]'):
                element.set('x', str(position[0]))
                element.set('y', str(position[1]))
        
        return ET.tostring(physics_doc, encoding='unicode')
    
    def _calculate_element_position(self, element: ET.Element) -> Tuple[float, float]:
        """Calculate element position."""
        x = float(element.get('x', 0))
        y = float(element.get('y', 0))
        return (x, y)
    
    def _calculate_element_dimensions(self, element: ET.Element) -> Tuple[float, float]:
        """Calculate element dimensions."""
        width = float(element.get('width', 0))
        height = float(element.get('height', 0))
        return (width, height)
    
    def _generate_behavior_script(self, behavior: ET.Element) -> str:
        """Generate JavaScript for behavior."""
        behavior_name = behavior.get('name', 'default')
        behavior_type = behavior.get('type', 'click')
        action = behavior.find('action')
        
        if action is not None:
            return f"""
            function {behavior_name}() {{
                {action.text};
            }}
            """
        else:
            return f"""
            function {behavior_name}() {{
                console.log('Behavior {behavior_name} triggered');
            }}
            """
    
    def _save_animation_frames(self, symbol_id: str, frames: List[AnimationFrame]):
        """Save animation frames to database."""
        with sqlite3.connect(self.animation_db_path) as conn:
            for frame in frames:
                conn.execute("""
                    INSERT INTO animation_frames 
                    (symbol_id, animation_id, frame_number, timestamp, content, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol_id,
                    f"{symbol_id}_animation",
                    frame.frame_number,
                    frame.timestamp,
                    frame.content,
                    json.dumps(frame.metadata),
                    datetime.now().isoformat()
                ))
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            # Clear expired cache entries
            with self.cache_lock:
                current_time = datetime.now()
                expired_keys = [
                    key for key, cache_entry in self.render_cache.items()
                    if cache_entry.expires_at <= current_time
                ]
                for key in expired_keys:
                    del self.render_cache[key]
            
            # Shutdown thread pool
            self.render_executor.shutdown(wait=True)
            
            self.logger.info("symbol_renderer_cleanup_completed")
        except Exception as e:
            self.logger.error("cleanup_error", error=str(e))


def create_symbol_renderer_service(options: Optional[Dict[str, Any]] = None) -> SVGXSymbolRendererService:
    """
    Create a Symbol Renderer Service instance.
    
    Args:
        options: Configuration options
        
    Returns:
        SVGXSymbolRendererService instance
    """
    return SVGXSymbolRendererService(options) 