"""
Test suite for Export Integration Service

Tests for Phase 7.3: Export Integration
- Update SVG export to maintain proper scale
- Add scale metadata to exported files
- Test export consistency across zoom levels
- Validate exported file compatibility
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from services.export_integration import (
    ExportIntegration, ScaleMetadata, ExportMetadata, ExportOptions
)


class TestExportIntegration:
    """Test cases for Export Integration service."""
    
    @pytest.fixture
    def export_service(self):
        """Create export integration service instance."""
        return ExportIntegration()
    
    @pytest.fixture
    def sample_svg(self):
        """Sample SVG content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
    <g id="floor-plan">
        <rect x="100" y="100" width="200" height="150" fill="white" stroke="black"/>
        <circle cx="200" cy="175" r="20" fill="blue"/>
        <text x="200" y="200" text-anchor="middle" fill="black">Room 1</text>
    </g>
</svg>'''
    
    @pytest.fixture
    def scale_metadata(self):
        """Sample scale metadata for testing."""
        return ScaleMetadata(
            original_scale=1.0,
            current_scale=2.0,
            zoom_level=2.0,
            units="mm",
            scale_factor=2.0,
            viewport_width=800,
            viewport_height=600,
            created_at="2024-01-01T00:00:00Z",
            coordinate_system="cartesian"
        )
    
    @pytest.fixture
    def export_options(self):
        """Sample export options for testing."""
        return ExportOptions(
            include_metadata=True,
            include_scale_info=True,
            optimize_svg=True,
            export_format="svg",
            scale_factor=2.0,
            units="mm"
        )
    
    def test_create_scale_metadata(self, export_service):
        """Test creating scale metadata."""
        metadata = export_service.create_scale_metadata(
            original_scale=1.0,
            current_scale=2.0,
            zoom_level=2.0,
            viewport_size=(800, 600),
            units="mm"
        )
        
        assert metadata.original_scale == 1.0
        assert metadata.current_scale == 2.0
        assert metadata.zoom_level == 2.0
        assert metadata.units == "mm"
        assert metadata.scale_factor == 2.0
        assert metadata.viewport_width == 800
        assert metadata.viewport_height == 600
        assert metadata.coordinate_system == "cartesian"
        assert metadata.created_at is not None
    
    def test_export_svg_with_scale(self, export_service, sample_svg, scale_metadata, export_options):
        """Test exporting SVG with scale preservation."""
        exported_svg = export_service.export_svg_with_scale(
            sample_svg, scale_metadata, export_options
        )
        
        # Check that SVG is modified
        assert exported_svg != sample_svg
        
        # Check that scale metadata is embedded
        assert 'arxos.io/scale' in exported_svg
        assert 'scale_factor="2.0"' in exported_svg
        
        # Check that export metadata is embedded
        assert 'arxos.io/metadata' in exported_svg
        assert 'format="svg"' in exported_svg
        
        # Check that viewBox is updated
        assert 'viewBox="0 0 1600 1200"' in exported_svg
        
        # Check that width and height are updated
        assert 'width="1600"' in exported_svg
        assert 'height="1200"' in exported_svg
    
    def test_export_svg_without_scale_info(self, export_service, sample_svg, scale_metadata):
        """Test exporting SVG without scale information."""
        options = ExportOptions(
            include_metadata=True,
            include_scale_info=False,
            optimize_svg=True
        )
        
        exported_svg = export_service.export_svg_with_scale(
            sample_svg, scale_metadata, options
        )
        
        # Check that scale metadata is not embedded
        assert 'arxos.io/scale' not in exported_svg
        
        # Check that export metadata is still embedded
        assert 'arxos.io/metadata' in exported_svg
    
    def test_export_svg_without_metadata(self, export_service, sample_svg, scale_metadata):
        """Test exporting SVG without any metadata."""
        options = ExportOptions(
            include_metadata=False,
            include_scale_info=False,
            optimize_svg=True
        )
        
        exported_svg = export_service.export_svg_with_scale(
            sample_svg, scale_metadata, options
        )
        
        # Check that no metadata is embedded
        assert 'arxos.io/scale' not in exported_svg
        assert 'arxos.io/metadata' not in exported_svg
        
        # Check that transformations are still applied
        assert 'viewBox="0 0 1600 1200"' in exported_svg
    
    def test_export_with_metadata_sidecar(self, export_service, sample_svg, scale_metadata):
        """Test exporting SVG with metadata sidecar."""
        export_metadata = ExportMetadata(
            title="Test Floor Plan",
            description="Test description",
            building_id="test-building",
            floor_label="test-floor",
            version="1.0",
            created_at=scale_metadata.created_at,
            created_by="test-user",
            scale_metadata=scale_metadata,
            symbol_count=5,
            element_count=10,
            export_format="svg",
            export_version="1.0"
        )
        
        options = ExportOptions(
            include_metadata=True,
            include_scale_info=True,
            optimize_svg=True
        )
        
        result = export_service.export_with_metadata_sidecar(
            sample_svg, export_metadata, options
        )
        
        assert 'svg' in result
        assert 'metadata' in result
        assert result['format'] == 'svg_with_sidecar'
        
        # Check that metadata sidecar is valid JSON
        metadata_dict = json.loads(result['metadata'])
        assert metadata_dict['title'] == "Test Floor Plan"
        assert metadata_dict['building_id'] == "test-building"
        assert metadata_dict['scale_metadata']['scale_factor'] == 2.0
    
    def test_test_export_consistency(self, export_service, sample_svg):
        """Test export consistency across zoom levels."""
        zoom_levels = [0.25, 0.5, 1.0, 2.0, 4.0]
        options = ExportOptions(
            include_metadata=True,
            include_scale_info=True,
            optimize_svg=True
        )
        
        results = export_service.test_export_consistency(
            sample_svg, zoom_levels, options
        )
        
        assert 'consistency_score' in results
        assert 'tested_levels' in results
        assert 'scale_variations' in results
        assert 'issues' in results
        assert 'recommendations' in results
        
        # Check that all zoom levels were tested
        assert len(results['tested_levels']) == len(zoom_levels)
        
        # Check that consistency score is between 0 and 1
        assert 0.0 <= results['consistency_score'] <= 1.0
        
        # Check that scale variations are recorded
        assert len(results['scale_variations']) == len(zoom_levels)
    
    def test_validate_export_compatibility(self, export_service, sample_svg, scale_metadata, export_options):
        """Test export compatibility validation."""
        # First export the SVG
        exported_svg = export_service.export_svg_with_scale(
            sample_svg, scale_metadata, export_options
        )
        
        # Test compatibility with different formats
        target_formats = ['bim', 'cad', 'web', 'print']
        results = export_service.validate_export_compatibility(
            exported_svg, target_formats
        )
        
        assert 'overall_compatibility' in results
        assert 'svg_validation' in results
        assert 'format_compatibility' in results
        assert 'issues' in results
        assert 'warnings' in results
        
        # Check that SVG validation passed
        assert results['svg_validation']['is_valid'] is True
        
        # Check that all formats were tested
        assert len(results['format_compatibility']) == len(target_formats)
        
        # Check that overall compatibility score is between 0 and 1
        assert 0.0 <= results['overall_compatibility'] <= 1.0
    
    def test_validate_export_compatibility_invalid_svg(self, export_service):
        """Test compatibility validation with invalid SVG."""
        invalid_svg = "<invalid>svg</invalid>"
        target_formats = ['web']
        
        results = export_service.validate_export_compatibility(
            invalid_svg, target_formats
        )
        
        assert results['svg_validation']['is_valid'] is False
        assert 'error' in results['svg_validation']
    
    def test_generate_export_report(self, export_service):
        """Test generating export report."""
        test_results = {
            'consistency_score': 0.85,
            'tested_levels': [
                {
                    'zoom_level': 1.0,
                    'analysis': {'total_elements': 10}
                },
                {
                    'zoom_level': 2.0,
                    'analysis': {'total_elements': 10}
                }
            ],
            'issues': ['Minor scaling issue detected'],
            'recommendations': ['Consider standardizing element counts']
        }
        
        report = export_service.generate_export_report(test_results)
        
        assert '# Export Integration Report' in report
        assert 'Overall Consistency Score: 0.85' in report
        assert 'Minor scaling issue detected' in report
        assert 'Consider standardizing element counts' in report
    
    def test_scale_factor_calculation(self, export_service):
        """Test scale factor calculation edge cases."""
        # Test zero scale
        metadata = export_service.create_scale_metadata(
            original_scale=0.0,
            current_scale=1.0,
            zoom_level=1.0,
            viewport_size=(800, 600)
        )
        assert metadata.scale_factor == 1.0  # Should default to 1.0 when original_scale is 0
        
        # Test negative scale
        metadata = export_service.create_scale_metadata(
            original_scale=-1.0,
            current_scale=1.0,
            zoom_level=1.0,
            viewport_size=(800, 600)
        )
        assert metadata.scale_factor == 1.0  # Should handle negative scales gracefully
    
    def test_svg_optimization(self, export_service, scale_metadata):
        """Test SVG optimization during export."""
        svg_with_whitespace = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
    <g id="test">
        
        <rect x="100" y="100" width="200" height="150"/>
        
    </g>
</svg>'''
        
        options = ExportOptions(
            include_metadata=False,
            include_scale_info=False,
            optimize_svg=True
        )
        
        exported_svg = export_service.export_svg_with_scale(
            svg_with_whitespace, scale_metadata, options
        )
        
        # Check that excessive whitespace is removed
        assert '\n\n' not in exported_svg
        assert '    ' not in exported_svg  # No excessive indentation
    
    def test_empty_group_removal(self, export_service, scale_metadata):
        """Test removal of empty groups during optimization."""
        svg_with_empty_groups = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
    <g id="empty-group"></g>
    <g id="non-empty-group">
        <rect x="100" y="100" width="200" height="150"/>
    </g>
</svg>'''
        
        options = ExportOptions(
            include_metadata=False,
            include_scale_info=False,
            optimize_svg=True
        )
        
        exported_svg = export_service.export_svg_with_scale(
            svg_with_empty_groups, scale_metadata, options
        )
        
        # Check that empty group is removed
        assert 'id="empty-group"' not in exported_svg
        # Check that non-empty group is preserved
        assert 'id="non-empty-group"' in exported_svg
    
    def test_viewbox_transformation(self, export_service, scale_metadata):
        """Test viewBox transformation during scaling."""
        svg_with_viewbox = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
    <rect x="100" y="100" width="200" height="150"/>
</svg>'''
        
        options = ExportOptions(
            include_metadata=False,
            include_scale_info=False,
            optimize_svg=False
        )
        
        exported_svg = export_service.export_svg_with_scale(
            svg_with_viewbox, scale_metadata, options
        )
        
        # Check that viewBox is scaled correctly
        assert 'viewBox="0 0 1600 1200"' in exported_svg
    
    def test_invalid_viewbox_handling(self, export_service, scale_metadata):
        """Test handling of invalid viewBox values."""
        svg_with_invalid_viewbox = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="invalid">
    <rect x="100" y="100" width="200" height="150"/>
</svg>'''
        
        options = ExportOptions(
            include_metadata=False,
            include_scale_info=False,
            optimize_svg=False
        )
        
        # Should not raise an exception
        exported_svg = export_service.export_svg_with_scale(
            svg_with_invalid_viewbox, scale_metadata, options
        )
        
        # Should preserve original viewBox
        assert 'viewBox="invalid"' in exported_svg
    
    def test_dimension_transformation(self, export_service, scale_metadata):
        """Test width and height transformation during scaling."""
        svg_with_dimensions = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
    <rect x="100" y="100" width="200" height="150"/>
</svg>'''
        
        options = ExportOptions(
            include_metadata=False,
            include_scale_info=False,
            optimize_svg=False
        )
        
        exported_svg = export_service.export_svg_with_scale(
            svg_with_dimensions, scale_metadata, options
        )
        
        # Check that dimensions are scaled correctly
        assert 'width="1600"' in exported_svg
        assert 'height="1200"' in exported_svg
    
    def test_invalid_dimension_handling(self, export_service, scale_metadata):
        """Test handling of invalid width/height values."""
        svg_with_invalid_dimensions = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="invalid" height="600">
    <rect x="100" y="100" width="200" height="150"/>
</svg>'''
        
        options = ExportOptions(
            include_metadata=False,
            include_scale_info=False,
            optimize_svg=False
        )
        
        # Should not raise an exception
        exported_svg = export_service.export_svg_with_scale(
            svg_with_invalid_dimensions, scale_metadata, options
        )
        
        # Should preserve original dimensions
        assert 'width="invalid"' in exported_svg
        assert 'height="1200"' in exported_svg  # This one should be transformed
    
    def test_consistency_score_calculation(self, export_service):
        """Test consistency score calculation with various scenarios."""
        # Test perfect consistency
        perfect_levels = [
            {'analysis': {'total_elements': 10}},
            {'analysis': {'total_elements': 10}},
            {'analysis': {'total_elements': 10}}
        ]
        score = export_service._calculate_consistency_score(perfect_levels)
        assert score == 1.0
        
        # Test poor consistency
        poor_levels = [
            {'analysis': {'total_elements': 5}},
            {'analysis': {'total_elements': 10}},
            {'analysis': {'total_elements': 20}}
        ]
        score = export_service._calculate_consistency_score(poor_levels)
        assert score < 0.5
        
        # Test empty levels
        score = export_service._calculate_consistency_score([])
        assert score == 0.0
    
    def test_format_compatibility_checks(self, export_service):
        """Test format compatibility checks."""
        # Test BIM compatibility
        bim_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
    <metadata>
        <arxos:export xmlns:arxos="http://arxos.io/metadata" format="svg"/>
        <arxos:scale xmlns:arxos="http://arxos.io/scale" scale_factor="1.0"/>
    </metadata>
    <rect data-x="100" data-y="100" width="200" height="150"/>
</svg>'''
        
        bim_result = export_service._check_bim_compatibility(bim_svg)
        assert bim_result['compatible'] is True
        assert bim_result['has_metadata'] is True
        assert bim_result['has_scale_info'] is True
        assert bim_result['has_coordinates'] is True
        
        # Test CAD compatibility
        cad_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
    <path d="M100,100 L300,100 L300,250 L100,250 Z"/>
    <line x1="100" y1="100" x2="300" y2="250"/>
    <rect x="100" y="100" width="200" height="150"/>
</svg>'''
        
        cad_result = export_service._check_cad_compatibility(cad_svg)
        assert cad_result['compatible'] is True
        assert cad_result['has_paths'] is True
        assert cad_result['has_lines'] is True
        assert cad_result['has_rectangles'] is True
        
        # Test web compatibility
        web_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
    <g style="fill: blue;">
        <rect x="100" y="100" width="200" height="150"/>
    </g>
</svg>'''
        
        web_result = export_service._check_web_compatibility(web_svg)
        assert web_result['compatible'] is True
        assert web_result['has_web_elements'] is True
        assert web_result['has_styling'] is True
        assert web_result['has_svg_namespace'] is True
        
        # Test print compatibility
        print_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
    <metadata>
        <arxos:scale xmlns:arxos="http://arxos.io/scale" scale_factor="1.0"/>
    </metadata>
    <rect x="100" y="100" width="200" height="150"/>
</svg>'''
        
        print_result = export_service._check_print_compatibility(print_svg)
        assert print_result['compatible'] is True
        assert print_result['has_dimensions'] is True
        assert print_result['has_viewbox'] is True
        assert print_result['has_scale_info'] is True
    
    def test_unknown_format_handling(self, export_service):
        """Test handling of unknown format types."""
        result = export_service._check_format_compatibility("", "unknown_format")
        assert result['compatible'] is False
        assert 'Unknown format' in result['reason']
    
    def test_compatibility_score_calculation(self, export_service):
        """Test overall compatibility score calculation."""
        results = {
            'format_compatibility': {
                'bim': {'score': 0.8},
                'cad': {'score': 0.7},
                'web': {'score': 0.9},
                'print': {'score': 0.6}
            }
        }
        
        score = export_service._calculate_compatibility_score(results)
        expected_score = (0.8 + 0.7 + 0.9 + 0.6) / 4
        assert score == expected_score
        
        # Test with no formats
        results = {'format_compatibility': {}}
        score = export_service._calculate_compatibility_score(results)
        assert score == 0.0


if __name__ == "__main__":
    pytest.main([__file__]) 