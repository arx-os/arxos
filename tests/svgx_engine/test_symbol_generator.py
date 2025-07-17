"""
Test suite for SVGX Symbol Generator Service

Tests automated symbol generation, templating, batch processing, and quality optimization.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from svgx_engine.models.svgx_symbol import SVGXSymbol, SVGXSymbolMetadata
from svgx_engine.services.symbol_generator import (
    SVGXSymbolGenerator,
    GenerationTemplate,
    GenerationRequest,
    GenerationResult,
    BatchGenerationResult,
    symbol_generator_service,
)
from svgx_engine.utils.errors import SymbolGenerationError, TemplateNotFoundError, ValidationError as SVGXValidationError


class TestGenerationTemplate:
    """Test GenerationTemplate model."""
    
    def test_valid_template(self):
        """Test creating a valid template."""
        template = GenerationTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="geometric",
            parameters={"size": 100, "color": "#000000"},
            constraints={"min_size": 10, "max_size": 500},
            svgx_metadata={"namespace": "test", "version": "1.0"}
        )
        
        assert template.template_id == "test_template"
        assert template.name == "Test Template"
        assert template.category == "geometric"
        assert template.parameters["size"] == 100
        assert template.constraints["min_size"] == 10
    
    def test_template_with_defaults(self):
        """Test template creation with default values."""
        template = GenerationTemplate(
            template_id="minimal_template",
            name="Minimal Template",
            description="Minimal template",
            category="technical"
        )
        
        assert template.parameters == {}
        assert template.constraints == {}
        assert template.svgx_metadata == {}


class TestGenerationRequest:
    """Test GenerationRequest model."""
    
    def test_valid_request(self):
        """Test creating a valid generation request."""
        request = GenerationRequest(
            template_id="test_template",
            category="geometric",
            parameters={"size": 100, "color": "#000000"},
            style_preferences={"fill_color": "red"},
            output_format="svgx",
            quality_level="high"
        )
        
        assert request.template_id == "test_template"
        assert request.category == "geometric"
        assert request.parameters["size"] == 100
        assert request.output_format == "svgx"
        assert request.quality_level == "high"
    
    def test_invalid_output_format(self):
        """Test validation of output format."""
        with pytest.raises(ValidationError):
            GenerationRequest(
                category="geometric",
                output_format="invalid_format"
            )
    
    def test_invalid_quality_level(self):
        """Test validation of quality level."""
        with pytest.raises(ValidationError):
            GenerationRequest(
                category="geometric",
                quality_level="invalid_level"
            )
    
    def test_batch_size_validation(self):
        """Test batch size validation."""
        # Valid batch size
        request = GenerationRequest(category="geometric", batch_size=50)
        assert request.batch_size == 50
        
        # Invalid batch size (too high)
        with pytest.raises(ValidationError):
            GenerationRequest(category="geometric", batch_size=150)
        
        # Invalid batch size (too low)
        with pytest.raises(ValidationError):
            GenerationRequest(category="geometric", batch_size=0)


class TestSVGXSymbolGenerator:
    """Test SVGX Symbol Generator service."""
    
    @pytest.fixture
    def generator(self):
        """Create a fresh generator instance for each test."""
        return SVGXSymbolGenerator()
    
    def test_initialization(self, generator):
        """Test generator initialization."""
        assert len(generator.templates) > 0
        assert "basic_geometric" in generator.templates
        assert "technical_symbol" in generator.templates
        assert "abstract_pattern" in generator.templates
    
    def test_register_template(self, generator):
        """Test template registration."""
        template = GenerationTemplate(
            template_id="custom_template",
            name="Custom Template",
            description="A custom template",
            category="custom",
            parameters={"custom_param": "value"},
            constraints={"min_size": 20},
            svgx_metadata={"namespace": "custom", "version": "1.0"}
        )
        
        generator.register_template(template)
        assert "custom_template" in generator.templates
        assert generator.templates["custom_template"] == template
    
    def test_get_template(self, generator):
        """Test getting a template by ID."""
        template = generator.get_template("basic_geometric")
        assert template.template_id == "basic_geometric"
        assert template.name == "Basic Geometric Shapes"
    
    def test_get_nonexistent_template(self, generator):
        """Test getting a non-existent template."""
        with pytest.raises(TemplateNotFoundError):
            generator.get_template("nonexistent_template")
    
    def test_list_templates(self, generator):
        """Test listing templates."""
        all_templates = generator.list_templates()
        assert len(all_templates) >= 3
        
        geometric_templates = generator.list_templates(category="geometric")
        assert len(geometric_templates) >= 1
        assert all(t.category == "geometric" for t in geometric_templates)
    
    def test_generate_symbol_basic(self, generator):
        """Test basic symbol generation."""
        request = GenerationRequest(
            category="geometric",
            parameters={"shape_type": "circle", "size": 100, "color": "#000000"}
        )
        
        result = generator.generate_symbol(request)
        
        assert isinstance(result, GenerationResult)
        assert result.symbol_id is not None
        assert isinstance(result.symbol, SVGXSymbol)
        assert result.generation_time > 0
        assert 0 <= result.quality_score <= 1
        assert result.template_used is None
        assert result.parameters == request.parameters
    
    def test_generate_symbol_with_template(self, generator):
        """Test symbol generation with template."""
        request = GenerationRequest(
            template_id="basic_geometric",
            category="geometric",
            parameters={"shape_type": "square", "size": 150}
        )
        
        result = generator.generate_symbol(request)
        
        assert result.template_used == "basic_geometric"
        assert result.symbol.metadata.namespace == "geometric"
        assert "geometric" in result.symbol.metadata.tags
    
    def test_generate_symbol_technical(self, generator):
        """Test technical symbol generation."""
        request = GenerationRequest(
            template_id="technical_symbol",
            category="technical",
            parameters={"symbol_type": "valve", "size": 80}
        )
        
        result = generator.generate_symbol(request)
        
        assert result.symbol.metadata.namespace == "technical"
        assert "technical" in result.symbol.metadata.tags
        assert "valve" in result.symbol.content.lower()
    
    def test_generate_symbol_abstract(self, generator):
        """Test abstract symbol generation."""
        request = GenerationRequest(
            template_id="abstract_pattern",
            category="abstract",
            parameters={"pattern_type": "geometric", "size": 120}
        )
        
        result = generator.generate_symbol(request)
        
        assert result.symbol.metadata.namespace == "abstract"
        assert "abstract" in result.symbol.metadata.tags
    
    def test_generate_symbol_with_style_preferences(self, generator):
        """Test symbol generation with style preferences."""
        request = GenerationRequest(
            category="geometric",
            parameters={"shape_type": "circle", "size": 100},
            style_preferences={"fill_color": "red", "stroke_color": "blue"}
        )
        
        result = generator.generate_symbol(request)
        
        # Check that style preferences are applied
        assert "fill=\"red\"" in result.symbol.content
        assert "stroke=\"blue\"" in result.symbol.content
    
    def test_generate_symbol_validation_error(self, generator):
        """Test symbol generation with invalid parameters."""
        request = GenerationRequest(
            template_id="basic_geometric",
            category="geometric",
            parameters={"size": 5}  # Below minimum constraint
        )
        
        with pytest.raises(SVGXValidationError):
            generator.generate_symbol(request)
    
    def test_generate_symbol_template_not_found(self, generator):
        """Test symbol generation with non-existent template."""
        request = GenerationRequest(
            template_id="nonexistent_template",
            category="geometric"
        )
        
        with pytest.raises(TemplateNotFoundError):
            generator.generate_symbol(request)
    
    def test_generate_batch(self, generator):
        """Test batch symbol generation."""
        requests = [
            GenerationRequest(category="geometric", parameters={"shape_type": "circle", "size": 100}),
            GenerationRequest(category="geometric", parameters={"shape_type": "square", "size": 120}),
            GenerationRequest(category="geometric", parameters={"shape_type": "triangle", "size": 80})
        ]
        
        batch_result = generator.generate_batch(requests)
        
        assert isinstance(batch_result, BatchGenerationResult)
        assert batch_result.batch_id is not None
        assert len(batch_result.results) == 3
        assert batch_result.success_count == 3
        assert batch_result.failure_count == 0
        assert batch_result.total_time > 0
        assert 0 <= batch_result.average_quality <= 1
    
    def test_generate_batch_with_failures(self, generator):
        """Test batch generation with some failures."""
        requests = [
            GenerationRequest(category="geometric", parameters={"shape_type": "circle", "size": 100}),
            GenerationRequest(template_id="nonexistent_template", category="geometric"),  # Will fail
            GenerationRequest(category="geometric", parameters={"shape_type": "square", "size": 120})
        ]
        
        batch_result = generator.generate_batch(requests)
        
        assert batch_result.success_count == 2
        assert batch_result.failure_count == 1
        assert len(batch_result.results) == 3
    
    def test_generate_geometric_svg(self, generator):
        """Test geometric SVG generation."""
        # Test circle
        svg_content = generator._generate_geometric_svg(
            {"shape_type": "circle", "size": 100, "color": "#000000"},
            {"fill_color": "red", "stroke_color": "blue"}
        )
        assert "circle" in svg_content
        assert "fill=\"red\"" in svg_content
        assert "stroke=\"blue\"" in svg_content
        
        # Test square
        svg_content = generator._generate_geometric_svg(
            {"shape_type": "square", "size": 100, "color": "#000000"},
            {}
        )
        assert "rect" in svg_content
        
        # Test triangle
        svg_content = generator._generate_geometric_svg(
            {"shape_type": "triangle", "size": 100, "color": "#000000"},
            {}
        )
        assert "polygon" in svg_content
    
    def test_generate_technical_svg(self, generator):
        """Test technical SVG generation."""
        # Test valve
        svg_content = generator._generate_technical_svg(
            {"symbol_type": "valve", "size": 80, "color": "#333333"},
            {}
        )
        assert "valve" in svg_content.lower() or "rect" in svg_content
        
        # Test pump
        svg_content = generator._generate_technical_svg(
            {"symbol_type": "pump", "size": 80, "color": "#333333"},
            {}
        )
        assert "circle" in svg_content
    
    def test_generate_abstract_svg(self, generator):
        """Test abstract SVG generation."""
        svg_content = generator._generate_abstract_svg(
            {"pattern_type": "geometric", "size": 120, "colors": ["#ff0000", "#00ff00"]},
            {}
        )
        assert "pattern" in svg_content or "circle" in svg_content
    
    def test_calculate_quality_score(self, generator):
        """Test quality score calculation."""
        symbol = SVGXSymbol(
            id="test",
            name="test_symbol",
            content="<svg></svg>",
            metadata=SVGXSymbolMetadata(namespace="test", version="1.0", tags=[])
        )
        
        request = GenerationRequest(
            category="geometric",
            quality_level="high",
            parameters={"size": 100},
            style_preferences={"fill_color": "red"}
        )
        
        score = generator._calculate_quality_score(symbol, request)
        assert 0 <= score <= 1
    
    def test_validate_parameters_against_constraints(self, generator):
        """Test parameter validation against constraints."""
        parameters = {"size": 50}
        constraints = {"min_size": 10, "max_size": 100}
        
        # Should not raise
        generator._validate_parameters_against_constraints(parameters, constraints)
        
        # Should raise for value below minimum
        with pytest.raises(SVGXValidationError):
            generator._validate_parameters_against_constraints({"size": 5}, constraints)
        
        # Should raise for value above maximum
        with pytest.raises(SVGXValidationError):
            generator._validate_parameters_against_constraints({"size": 150}, constraints)
    
    def test_get_performance_metrics(self, generator):
        """Test performance metrics retrieval."""
        metrics = generator.get_performance_metrics()
        
        assert "templates_count" in metrics
        assert "cache_size" in metrics
        assert "performance_metrics" in metrics
        assert metrics["templates_count"] >= 3
    
    def test_clear_cache(self, generator):
        """Test cache clearing."""
        # Add some data to cache
        generator.generation_cache["test_key"] = "test_value"
        assert len(generator.generation_cache) > 0
        
        generator.clear_cache()
        assert len(generator.generation_cache) == 0
    
    def test_export_import_templates(self, generator):
        """Test template export and import."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Export templates
            generator.export_templates(temp_file)
            
            # Create new generator and import templates
            new_generator = SVGXSymbolGenerator()
            new_generator.templates.clear()  # Clear default templates
            
            new_generator.import_templates(temp_file)
            
            # Check that templates were imported
            assert len(new_generator.templates) > 0
            assert "basic_geometric" in new_generator.templates
            
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def test_different_output_formats(self, generator):
        """Test generation with different output formats."""
        for output_format in ["svgx", "svg", "png", "pdf"]:
            request = GenerationRequest(
                category="geometric",
                parameters={"shape_type": "circle", "size": 100},
                output_format=output_format
            )
            
            result = generator.generate_symbol(request)
            assert result.metadata["output_format"] == output_format
    
    def test_different_quality_levels(self, generator):
        """Test generation with different quality levels."""
        for quality_level in ["low", "standard", "high", "ultra"]:
            request = GenerationRequest(
                category="geometric",
                parameters={"shape_type": "circle", "size": 100},
                quality_level=quality_level
            )
            
            result = generator.generate_symbol(request)
            assert result.metadata["quality_level"] == quality_level
    
    @patch('svgx_engine.services.symbol_generator.TelemetryLogger')
    def test_telemetry_logging(self, mock_telemetry, generator):
        """Test telemetry logging during generation."""
        mock_logger = Mock()
        mock_telemetry.return_value = mock_logger
        
        request = GenerationRequest(
            category="geometric",
            parameters={"shape_type": "circle", "size": 100}
        )
        
        result = generator.generate_symbol(request)
        
        # Check that telemetry was logged
        mock_logger.log_event.assert_called()
        call_args = mock_logger.log_event.call_args
        assert call_args[0][0] == "symbol_generated"
        assert "template_id" in call_args[0][1]
        assert "category" in call_args[0][1]
        assert "quality_score" in call_args[0][1]


class TestSymbolGeneratorService:
    """Test the global symbol generator service instance."""
    
    def test_service_instance(self):
        """Test that the service instance is available."""
        assert symbol_generator_service is not None
        assert isinstance(symbol_generator_service, SVGXSymbolGenerator)
    
    def test_service_functionality(self):
        """Test basic functionality of the service instance."""
        request = GenerationRequest(
            category="geometric",
            parameters={"shape_type": "circle", "size": 100}
        )
        
        result = symbol_generator_service.generate_symbol(request)
        assert isinstance(result, GenerationResult)
        assert result.symbol_id is not None


class TestIntegration:
    """Integration tests for symbol generation workflow."""
    
    def test_complete_generation_workflow(self):
        """Test complete symbol generation workflow."""
        generator = SVGXSymbolGenerator()
        
        # 1. Register custom template
        template = GenerationTemplate(
            template_id="custom_workflow",
            name="Custom Workflow Template",
            description="Template for workflow testing",
            category="custom",
            parameters={"custom_param": "value"},
            constraints={"min_size": 20},
            svgx_metadata={"namespace": "custom", "version": "1.0"}
        )
        generator.register_template(template)
        
        # 2. Generate symbol with template
        request = GenerationRequest(
            template_id="custom_workflow",
            category="custom",
            parameters={"size": 100},
            style_preferences={"fill_color": "green"}
        )
        
        result = generator.generate_symbol(request)
        
        # 3. Verify result
        assert result.template_used == "custom_workflow"
        assert result.symbol.metadata.namespace == "custom"
        assert result.generation_time > 0
        assert 0 <= result.quality_score <= 1
        
        # 4. Check performance metrics
        metrics = generator.get_performance_metrics()
        assert metrics["templates_count"] >= 4  # 3 default + 1 custom
    
    def test_batch_generation_workflow(self):
        """Test batch generation workflow."""
        generator = SVGXSymbolGenerator()
        
        # Create multiple requests
        requests = [
            GenerationRequest(category="geometric", parameters={"shape_type": "circle", "size": 100}),
            GenerationRequest(category="geometric", parameters={"shape_type": "square", "size": 120}),
            GenerationRequest(category="geometric", parameters={"shape_type": "triangle", "size": 80}),
            GenerationRequest(template_id="technical_symbol", category="technical", parameters={"symbol_type": "valve"}),
            GenerationRequest(template_id="abstract_pattern", category="abstract", parameters={"pattern_type": "geometric"})
        ]
        
        # Generate batch
        batch_result = generator.generate_batch(requests)
        
        # Verify batch result
        assert batch_result.success_count >= 4  # At least 4 should succeed
        assert batch_result.failure_count <= 1  # At most 1 might fail
        assert len(batch_result.results) == 5
        assert batch_result.total_time > 0
        assert 0 <= batch_result.average_quality <= 1
        
        # Check individual results
        for result in batch_result.results:
            assert result.symbol_id is not None
            assert isinstance(result.symbol, SVGXSymbol)
            assert result.generation_time >= 0
            assert 0 <= result.quality_score <= 1


if __name__ == "__main__":
    pytest.main([__file__]) 