#!/usr/bin/env python3
"""
Test suite for SVGX Engine Symbol Renderer Service.

Tests advanced rendering capabilities including:
- Multi-format rendering (SVG, PNG, PDF, WebGL)
- Animation rendering and frame generation
- Interactive rendering with event handling
- Physics simulation rendering
- Performance optimization and caching
- SVGX-specific rendering enhancements
- Error handling and validation
"""

import pytest
import tempfile
import shutil
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add the parent directory to the path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgx_engine.services.symbol_renderer import (
    SVGXSymbolRendererService,
    RenderOptions,
    RenderResult,
    AnimationFrame,
    InteractiveElement,
    PhysicsSimulation,
    RenderCache,
    create_symbol_renderer_service
)
from svgx_engine.utils.errors import (
    RenderingError,
    ValidationError,
    SVGXError,
    PerformanceError
)


class TestSymbolRendererService:
    """Test suite for Symbol Renderer Service."""

    @pytest.fixture
def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
def service(self, temp_dir):
        """Create a Symbol Renderer Service instance."""
        options = {
            'enable_caching': True,
            'cache_ttl_seconds': 60,
            'max_cache_size': 100,
            'enable_performance_monitoring': True,
            'max_concurrent_renders': 5,
            'default_output_format': 'svg',
            'enable_animations': True,
            'enable_interactivity': True,
            'enable_physics': True,
            'enable_behaviors': True,
            'optimize_output': True,
        }

        # Override database paths to use temp directory
        with patch('services.symbol_renderer.SVGXSymbolRendererService._init_databases') as mock_init:
            service = SVGXSymbolRendererService(options)
            # Manually set database paths to temp directory
            service.render_db_path = os.path.join(temp_dir, 'render.db')
            service.cache_db_path = os.path.join(temp_dir, 'cache.db')
            service.animation_db_path = os.path.join(temp_dir, 'animation.db')
            service._init_databases()
            return service

    @pytest.fixture
def sample_svgx_content(self):
        """Sample SVGX content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>'
<svgx xmlns="http://www.svgx.org/schema/1.0">
    <metadata>
        <name>Test Symbol</name>
        <description>A test symbol for rendering</description>
        <version>1.0.0</version>
        <author>Test Author</author>
        <tags>test, rendering, symbol</tags>
    </metadata>
    <geometry>
        <rect id="rect1" x="0" y="0" width="100" height="50" fill="blue"/>
        <circle id="circle1" cx="50" cy="25" r="20" fill="red"/>
    </geometry>
    <behaviors>
        <behavior name="click" type="interaction">
            <action>console.log('clicked');</action>
        </behavior>
    </behaviors>
    <physics>
        <mass>1.0</mass>
        <friction>0.1</friction>
        <elasticity>0.5</elasticity>
    </physics>
</svgx>'''

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.options['enable_caching'] is True
        assert service.options['enable_performance_monitoring'] is True
        assert service.options['enable_animations'] is True
        assert service.options['enable_interactivity'] is True
        assert service.options['enable_physics'] is True
        assert service.options['enable_behaviors'] is True
        assert service.options['optimize_output'] is True

    def test_render_symbol_svg(self, service, sample_svgx_content):
        """Test rendering SVGX symbol to SVG format."""
        symbol_id = "test_symbol_001"
        options = RenderOptions(output_format="svg", width=800, height=600)

        result = service.render_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        assert result is not None
        assert result.symbol_id == symbol_id
        assert result.output_format == "svg"
        assert result.dimensions == (800, 600)
        assert result.render_time > 0
        assert result.file_size > 0
        assert result.checksum is not None
        assert result.cache_hit is False
        assert "<svg" in result.rendered_content
        assert "xmlns=\"http://www.w3.org/2000/svg\"" in result.rendered_content

    def test_render_symbol_png(self, service, sample_svgx_content):
        """Test rendering SVGX symbol to PNG format."""
        symbol_id = "test_symbol_002"
        options = RenderOptions(output_format="png", width=400, height=300)

        result = service.render_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        assert result is not None
        assert result.symbol_id == symbol_id
        assert result.output_format == "png"
        assert result.dimensions == (400, 300)
        assert result.render_time > 0
        assert result.file_size > 0
        assert result.checksum is not None
        assert "data:image/png;base64," in result.rendered_content

    def test_render_symbol_pdf(self, service, sample_svgx_content):
        """Test rendering SVGX symbol to PDF format."""
        symbol_id = "test_symbol_003"
        options = RenderOptions(output_format="pdf", width=600, height=400)

        result = service.render_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        assert result is not None
        assert result.symbol_id == symbol_id
        assert result.output_format == "pdf"
        assert result.dimensions == (600, 400)
        assert result.render_time > 0
        assert result.file_size > 0
        assert result.checksum is not None
        assert "data:application/pdf;base64," in result.rendered_content

    def test_render_symbol_webgl(self, service, sample_svgx_content):
        """Test rendering SVGX symbol to WebGL format."""
        symbol_id = "test_symbol_004"
        options = RenderOptions(output_format="webgl", width=800, height=600)

        result = service.render_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        assert result is not None
        assert result.symbol_id == symbol_id
        assert result.output_format == "webgl"
        assert result.dimensions == (800, 600)
        assert result.render_time > 0
        assert result.file_size > 0
        assert result.checksum is not None
        assert "<canvas" in result.rendered_content
        assert "webgl" in result.rendered_content.lower()

    def test_render_caching(self, service, sample_svgx_content):
        """Test render result caching."""
        symbol_id = "test_symbol_005"
        options = RenderOptions(output_format="svg")

        # First render
        result1 = service.render_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        # Second render (should use cache)
        result2 = service.render_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        assert result1.symbol_id == result2.symbol_id
        assert result1.output_format == result2.output_format
        assert result1.checksum == result2.checksum

        # Check cache statistics
        stats = service.get_render_statistics()
        assert stats['cache_hits'] > 0
        assert stats['cache_misses'] > 0

    def test_render_animation(self, service, sample_svgx_content):
        """Test rendering animation frames."""
        symbol_id = "test_symbol_006"
        duration = 2.0
        fps = 10

        frames = service.render_animation(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            duration=duration,
            fps=fps
        )

        assert len(frames) == int(duration * fps)
        assert all(isinstance(frame, AnimationFrame) for frame in frames)

        for i, frame in enumerate(frames):
            assert frame.frame_number == i
            assert frame.timestamp == i / fps
            assert frame.content is not None
            assert frame.metadata['symbol_id'] == symbol_id

    def test_render_interactive(self, service, sample_svgx_content):
        """Test rendering interactive elements."""
        symbol_id = "test_symbol_007"
        options = RenderOptions(enable_interactivity=True)

        interactive_content, interactive_elements = service.render_interactive(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        assert interactive_content is not None
        assert len(interactive_elements) > 0
        assert all(isinstance(elem, InteractiveElement) for elem in interactive_elements)
        assert "<script" in interactive_content
        assert "addEventListener" in interactive_content

    def test_render_physics_simulation(self, service, sample_svgx_content):
        """Test rendering physics simulation."""
        symbol_id = "test_symbol_008"
        simulation_time = 1.0
        time_step = 0.1

        simulations = service.render_physics_simulation(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            simulation_time=simulation_time,
            time_step=time_step
        )

        assert len(simulations) == int(simulation_time / time_step)
        assert all(isinstance(sim, PhysicsSimulation) for sim in simulations)

        for i, simulation in enumerate(simulations):
            assert simulation.symbol_id == symbol_id
            assert simulation.simulation_time == i * time_step
            assert simulation.object_positions is not None
            assert simulation.velocities is not None
            assert simulation.forces is not None

    def test_render_options(self, service, sample_svgx_content):
        """Test different render options."""
        symbol_id = "test_symbol_009"

        # Test with custom options
        options = RenderOptions(
            output_format="svg",
            width=1200,
            height=800,
            background_color="black",
            quality=90,
            enable_animations=False,
            enable_interactivity=False,
            enable_physics=False,
            enable_behaviors=False,
            cache_rendered=True,
            optimize_output=True
        )

        result = service.render_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_content,
            options=options
        )

        assert result is not None
        assert result.dimensions == (1200, 800)
        assert result.metadata['quality'] == 90
        assert result.metadata['optimized'] is True

    def test_render_statistics(self, service, sample_svgx_content):
        """Test getting render statistics."""
        # Perform some renders
        for i in range(3):
            service.render_symbol(
                symbol_id=f"test_symbol_{i}",
                content=sample_svgx_content,
                options=RenderOptions(output_format="svg")
        stats = service.get_render_statistics()

        assert stats['total_renders'] >= 3
        assert stats['average_render_time'] > 0
        assert 'cache_size' in stats
        assert 'format_stats' in stats
        assert 'error_count' in stats
        assert 'performance_metrics' in stats

    def test_clear_cache(self, service, sample_svgx_content):
        """Test clearing render cache."""
        # Perform render to populate cache
        service.render_symbol(
            symbol_id="test_symbol_cache",
            content=sample_svgx_content,
            options=RenderOptions(output_format="svg")
        # Clear cache
        success = service.clear_cache()
        assert success is True

        # Check cache is empty
        stats = service.get_render_statistics()
        assert stats['cache_size'] == 0

    def test_error_handling_invalid_content(self, service):
        """Test error handling for invalid content."""
        with pytest.raises(RenderingError):
            service.render_symbol(
                symbol_id="test_invalid",
                content="invalid content",
                options=RenderOptions()
    def test_error_handling_invalid_format(self, service, sample_svgx_content):
        """Test error handling for invalid output format."""
        with pytest.raises(RenderingError):
            service.render_symbol(
                symbol_id="test_invalid_format",
                content=sample_svgx_content,
                options=RenderOptions(output_format="invalid_format")
    def test_performance_monitoring(self, service, sample_svgx_content):
        """Test performance monitoring integration."""
        start_time = time.time()

        result = service.render_symbol(
            symbol_id="test_performance",
            content=sample_svgx_content,
            options=RenderOptions()
        end_time = time.time()

        # Verify performance monitoring works
        assert result.render_time > 0
        assert result.render_time < (end_time - start_time + 0.1)  # Allow some tolerance

        # Check performance metrics
        stats = service.get_render_statistics()
        assert stats['average_render_time'] > 0

    def test_concurrent_rendering(self, service, sample_svgx_content):
        """Test concurrent rendering operations."""
        import threading

        results = []
        errors = []

        def render_symbol(symbol_id):
            try:
                result = service.render_symbol(
                    symbol_id=symbol_id,
                    content=sample_svgx_content,
                    options=RenderOptions()
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Start multiple render threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=render_symbol,
                args=(f"concurrent_symbol_{i}",)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all renders completed
        assert len(results) == 5
        assert len(errors) == 0

        for result in results:
            assert result.is_valid is True

    def test_cleanup(self, service):
        """Test service cleanup."""
        # Add some test data
        service.render_symbol(
            symbol_id="test_cleanup",
            content="<svgx></svgx>",
            options=RenderOptions()
        # Perform cleanup
        service.cleanup()

        # Verify cleanup completed without errors
        assert True  # If we get here, cleanup succeeded

    def test_optimization_settings(self, service, sample_svgx_content):
        """Test different optimization settings."""
        symbol_id = "test_optimization"

        # Test with optimization enabled
        options_optimized = RenderOptions(optimize_output=True)
        result_optimized = service.render_symbol(
            symbol_id=f"{symbol_id}_optimized",
            content=sample_svgx_content,
            options=options_optimized
        )

        # Test with optimization disabled
        options_unoptimized = RenderOptions(optimize_output=False)
        result_unoptimized = service.render_symbol(
            symbol_id=f"{symbol_id}_unoptimized",
            content=sample_svgx_content,
            options=options_unoptimized
        )

        # Both should work, but optimized might be smaller
        assert result_optimized.file_size > 0
        assert result_unoptimized.file_size > 0


class TestRenderOptions:
    """Test suite for RenderOptions dataclass."""

    def test_render_options_creation(self):
        """Test creating a RenderOptions instance."""
        options = RenderOptions(
            output_format="png",
            width=1024,
            height=768,
            background_color="white",
            quality=95,
            enable_animations=True,
            enable_interactivity=True,
            enable_physics=True,
            enable_behaviors=True,
            cache_rendered=True,
            optimize_output=True,
            metadata={"test": "data"}
        )

        assert options.output_format == "png"
        assert options.width == 1024
        assert options.height == 768
        assert options.background_color == "white"
        assert options.quality == 95
        assert options.enable_animations is True
        assert options.enable_interactivity is True
        assert options.enable_physics is True
        assert options.enable_behaviors is True
        assert options.cache_rendered is True
        assert options.optimize_output is True
        assert options.metadata == {"test": "data"}

    def test_render_options_defaults(self):
        """Test RenderOptions default values."""
        options = RenderOptions()

        assert options.output_format == "svg"
        assert options.width == 800
        assert options.height == 600
        assert options.background_color == "white"
        assert options.quality == 100
        assert options.enable_animations is True
        assert options.enable_interactivity is True
        assert options.enable_physics is True
        assert options.enable_behaviors is True
        assert options.cache_rendered is True
        assert options.optimize_output is True


class TestRenderResult:
    """Test suite for RenderResult dataclass."""

    def test_render_result_creation(self):
        """Test creating a RenderResult instance."""
        result = RenderResult(
            symbol_id="test_symbol",
            rendered_content="<svg>test</svg>",
            output_format="svg",
            dimensions=(800, 600),
            render_time=0.1,
            file_size=100,
            checksum="abc123",
            metadata={"test": "data"},
            cache_hit=False
        )

        assert result.symbol_id == "test_symbol"
        assert result.rendered_content == "<svg>test</svg>"
        assert result.output_format == "svg"
        assert result.dimensions == (800, 600)
        assert result.render_time == 0.1
        assert result.file_size == 100
        assert result.checksum == "abc123"
        assert result.metadata == {"test": "data"}
        assert result.cache_hit is False


class TestAnimationFrame:
    """Test suite for AnimationFrame dataclass."""

    def test_animation_frame_creation(self):
        """Test creating an AnimationFrame instance."""
        frame = AnimationFrame(
            frame_number=5,
            timestamp=0.5,
            content="<svg>frame5</svg>",
            metadata={"duration": 2.0, "fps": 10}
        )

        assert frame.frame_number == 5
        assert frame.timestamp == 0.5
        assert frame.content == "<svg>frame5</svg>"
        assert frame.metadata == {"duration": 2.0, "fps": 10}


class TestInteractiveElement:
    """Test suite for InteractiveElement dataclass."""

    def test_interactive_element_creation(self):
        """Test creating an InteractiveElement instance."""
def click_handler():
            return "clicked"

        element = InteractiveElement(
            element_id="button1",
            element_type="rect",
            position=(10, 20),
            dimensions=(100, 50),
            event_handlers={"click": click_handler},
            metadata={"behaviors": 2}
        )

        assert element.element_id == "button1"
        assert element.element_type == "rect"
        assert element.position == (10, 20)
        assert element.dimensions == (100, 50)
        assert "click" in element.event_handlers
        assert element.metadata == {"behaviors": 2}


class TestPhysicsSimulation:
    """Test suite for PhysicsSimulation dataclass."""

    def test_physics_simulation_creation(self):
        """Test creating a PhysicsSimulation instance."""
        simulation = PhysicsSimulation(
            symbol_id="test_symbol",
            simulation_time=1.5,
            object_positions={"obj1": (10, 20), "obj2": (30, 40)},
            velocities={"obj1": (5, 0), "obj2": (0, 5)},
            forces={"obj1": (0, -9.8), "obj2": (0, -9.8)},
            metadata={"step": 15, "time_step": 0.1}
        )

        assert simulation.symbol_id == "test_symbol"
        assert simulation.simulation_time == 1.5
        assert simulation.object_positions == {"obj1": (10, 20), "obj2": (30, 40)}
        assert simulation.velocities == {"obj1": (5, 0), "obj2": (0, 5)}
        assert simulation.forces == {"obj1": (0, -9.8), "obj2": (0, -9.8)}
        assert simulation.metadata == {"step": 15, "time_step": 0.1}


class TestRenderCache:
    """Test suite for RenderCache dataclass."""

    def test_render_cache_creation(self):
        """Test creating a RenderCache instance."""
        result = RenderResult(
            symbol_id="test",
            rendered_content="<svg>test</svg>",
            output_format="svg",
            dimensions=(800, 600),
            render_time=0.1,
            file_size=100,
            checksum="abc123",
            metadata={}
        )

        cache = RenderCache(
            symbol_hash="hash123",
            render_options_hash="options456",
            render_result=result,
            cached_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        assert cache.symbol_hash == "hash123"
        assert cache.render_options_hash == "options456"
        assert cache.render_result == result
        assert cache.cached_at is not None
        assert cache.expires_at is not None


def test_create_symbol_renderer_service():
    """Test creating a service instance using the factory function."""
    service = create_symbol_renderer_service()

    assert service is not None
    assert isinstance(service, SVGXSymbolRendererService)
    assert service.options['enable_caching'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
