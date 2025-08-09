"""
Test suite for SVGX Engine BIM Export Service

Tests the BIM export and import functionality with SVGX-specific features.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from svgx_engine.services.bim_export import (
    SVGXBIMExportService,
    ExportFormat,
    ImportFormat,
    ExportOptions,
    ImportOptions,
    ExportResult,
    ImportResult
)
from svgx_engine.models.bim import (
    BIMModel, BIMElement, Room, Wall, Device, Geometry, GeometryType,
    SystemType, RoomType, DeviceCategory
)
from svgx_engine.utils.errors import ExportError, ImportError


class TestSVGXBIMExportService:
    """Test cases for SVGX BIM Export Service."""

    @pytest.fixture
def export_service(self):
        """Create a test instance of the BIM export service."""
        return SVGXBIMExportService()

    @pytest.fixture
def sample_bim_model(self):
        """Create a sample BIM model for testing."""
        model = BIMModel()

        # Add sample elements
        room = Room(
            id="room_1",
            name="Test Room",
            room_type=RoomType.OFFICE,
            geometry=Geometry(
                geometry_type=GeometryType.POLYGON,
                coordinates=[[0, 0], [10, 0], [10, 10], [0, 10]]
            )
        wall = Wall(
            id="wall_1",
            name="Test Wall",
            geometry=Geometry(
                geometry_type=GeometryType.LINESTRING,
                coordinates=[[0, 0], [10, 0]]
            )
        device = Device(
            id="device_1",
            name="Test Device",
            category=DeviceCategory.ELECTRICAL,
            geometry=Geometry(
                geometry_type=GeometryType.POINT,
                coordinates=[5, 5]
            )
        model.elements = [room, wall, device]
        model.systems = []
        model.relationships = []

        return model

    def test_service_initialization(self, export_service):
        """Test that the service initializes correctly."""
        assert export_service is not None
        assert hasattr(export_service, 'error_handler')
        assert hasattr(export_service, 'validator')
        assert hasattr(export_service, 'performance_monitor')
        assert hasattr(export_service, 'supported_formats')
        assert hasattr(export_service, 'import_formats')

    def test_supported_formats(self, export_service):
        """Test that all expected formats are supported."""
        formats = export_service.get_supported_formats()
        format_names = [f['format'] for f in formats]

        expected_formats = ['ifc', 'json', 'xml', 'gltf', 'obj', 'fbx', 'svgx', 'rvt', 'rfa']
        for expected in expected_formats:
            assert expected in format_names

    def test_export_options_validation(self, export_service):
        """Test export options validation."""
        # Valid options
        valid_options = {
            'include_metadata': True,
            'include_relationships': True,
            'svgx_namespace': True
        }
        assert export_service._validate_export_options(ExportFormat.JSON, valid_options)

        # Invalid options
        invalid_options = {
            'invalid_option': True
        }
        # Should handle gracefully
        result = export_service._validate_export_options(ExportFormat.JSON, invalid_options)
        assert isinstance(result, bool)

    def test_import_options_validation(self, export_service):
        """Test import options validation."""
        # Valid options
        valid_options = {
            'validate_on_import': True,
            'create_systems': True,
            'svgx_compatibility': True
        }
        assert export_service._validate_import_options(ImportFormat.JSON, valid_options)

        # Invalid options
        invalid_options = {
            'invalid_option': True
        }
        # Should handle gracefully
        result = export_service._validate_import_options(ImportFormat.JSON, invalid_options)
        assert isinstance(result, bool)

    def test_count_svgx_elements(self, export_service, sample_bim_model):
        """Test counting of SVGX elements."""
        # Add SVGX namespace to some elements
        sample_bim_model.elements[0].svgx_namespace = "arx"
        sample_bim_model.elements[1].svgx_namespace = "arx"

        count = export_service._count_svgx_elements(sample_bim_model)
        assert count == 2

    def test_export_statistics(self, export_service):
        """Test export service statistics."""
        stats = export_service.get_export_statistics()

        assert 'total_exports' in stats
        assert 'total_imports' in stats
        assert 'svgx_exports' in stats
        assert 'svgx_imports' in stats
        assert 'performance_metrics' in stats
        assert 'supported_formats' in stats
        assert 'svgx_enhanced_formats' in stats

    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._generate_json_content')
    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._save_to_file')
def test_export_to_json(self, mock_save, mock_generate, export_service, sample_bim_model):
        """Test JSON export functionality."""
        # Mock the content generation and file saving
        mock_generate.return_value = '{"test": "content"}'
        mock_save.return_value = "/tmp/test.json"

        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=True,
            svgx_namespace=True
        )

        result = export_service.export_bim_model(sample_bim_model, ExportFormat.JSON, options.__dict__)

        assert result.success is True
        assert result.format == ExportFormat.JSON
        assert result.elements_exported == 3
        assert result.systems_exported == 0
        assert result.relationships_exported == 0
        assert result.file_path == "/tmp/test.json"
        assert result.export_time > 0

    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._generate_xml_content')
    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._save_to_file')
def test_export_to_xml(self, mock_save, mock_generate, export_service, sample_bim_model):
        """Test XML export functionality."""
        # Mock the content generation and file saving
        mock_generate.return_value = '<test>content</test>'
        mock_save.return_value = "/tmp/test.xml"

        options = ExportOptions(
            format=ExportFormat.XML,
            include_metadata=True,
            svgx_namespace=True
        )

        result = export_service.export_bim_model(sample_bim_model, ExportFormat.XML, options.__dict__)

        assert result.success is True
        assert result.format == ExportFormat.XML
        assert result.elements_exported == 3
        assert result.file_path == "/tmp/test.xml"

    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._generate_gltf_content')
    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._save_to_file')
def test_export_visualization(self, mock_save, mock_generate, export_service, sample_bim_model):
        """Test visualization export functionality."""
        # Mock the content generation and file saving
        mock_generate.return_value = '{"gltf": "content"}'
        mock_save.return_value = "/tmp/test.gltf"

        options = ExportOptions(
            format=ExportFormat.GLTF,
            include_geometry=True,
            svgx_optimized=True
        )

        result = export_service.export_bim_model(sample_bim_model, ExportFormat.GLTF, options.__dict__)

        assert result.success is True
        assert result.format == ExportFormat.GLTF
        assert result.elements_exported == 3
        assert result.file_path == "/tmp/test.gltf"

    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._generate_rvt_content')
    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._save_to_file')
def test_export_to_revit(self, mock_save, mock_generate, export_service, sample_bim_model):
        """Test Revit export functionality."""
        # Mock the content generation and file saving
        mock_generate.return_value = '<Revit>content</Revit>'
        mock_save.return_value = "/tmp/test.rvt"

        options = ExportOptions(
            format=ExportFormat.REVIT_RVT,
            include_metadata=True,
            svgx_enhanced=True
        )

        result = export_service.export_bim_model(sample_bim_model, ExportFormat.REVIT_RVT, options.__dict__)

        assert result.success is True
        assert result.format == ExportFormat.REVIT_RVT
        assert result.elements_exported == 3
        assert result.file_path == "/tmp/test.rvt"

    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._generate_svgx_content')
    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._save_to_file')
def test_export_to_svgx(self, mock_save, mock_generate, export_service, sample_bim_model):
        """Test SVGX export functionality."""
        # Mock the content generation and file saving
        mock_generate.return_value = '<svgx>content</svgx>'
        mock_save.return_value = "/tmp/test.svgx"

        options = ExportOptions(
            format=ExportFormat.SVGX,
            include_metadata=True,
            svgx_namespace=True,
            optimize_for_svgx=True
        )

        result = export_service.export_bim_model(sample_bim_model, ExportFormat.SVGX, options.__dict__)

        assert result.success is True
        assert result.format == ExportFormat.SVGX
        assert result.elements_exported == 3
        assert result.svgx_elements_exported == 3  # All elements are SVGX
        assert result.file_path == "/tmp/test.svgx"

    def test_export_unsupported_format(self, export_service, sample_bim_model):
        """Test export with unsupported format raises error."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_service.export_bim_model(sample_bim_model, "UNSUPPORTED", {})

    @patch('svgx_engine.services.bim_export.SVGXBIMExportService._import_json')
def test_import_from_json(self, mock_import, export_service):
        """Test JSON import functionality."""
        # Mock the import
        mock_model = Mock(spec=BIMModel)
        mock_model.elements = [Mock(), Mock(), Mock()]
        mock_model.systems = [Mock()]
        mock_model.relationships = [Mock(), Mock()]
        mock_import.return_value = mock_model

        options = ImportOptions(
            format=ImportFormat.JSON,
            validate_on_import=True,
            svgx_compatibility=True
        )

        result = export_service.import_bim_model("/tmp/test.json", ImportFormat.JSON, options.__dict__)

        assert result.success is True
        assert result.format == ImportFormat.JSON
        assert result.elements_imported == 3
        assert result.systems_imported == 1
        assert result.relationships_imported == 2
        assert result.import_time > 0

    def test_import_unsupported_format(self, export_service):
        """Test import with unsupported format raises error."""
        with pytest.raises(ValueError, match="Unsupported import format"):
            export_service.import_bim_model("/tmp/test.unsupported", "UNSUPPORTED", {})

    def test_export_options_dataclass(self):
        """Test ExportOptions dataclass functionality."""
        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=True,
            svgx_namespace=True,
            optimize_for_svgx=True
        )

        assert options.format == ExportFormat.JSON
        assert options.include_metadata is True
        assert options.svgx_namespace is True
        assert options.optimize_for_svgx is True

    def test_import_options_dataclass(self):
        """Test ImportOptions dataclass functionality."""
        options = ImportOptions(
            format=ImportFormat.JSON,
            validate_on_import=True,
            svgx_compatibility=True
        )

        assert options.format == ImportFormat.JSON
        assert options.validate_on_import is True
        assert options.svgx_compatibility is True

    def test_export_result_dataclass(self):
        """Test ExportResult dataclass functionality."""
        result = ExportResult(
            success=True,
            file_path="/tmp/test.json",
            file_size=1024,
            export_time=1.5,
            format=ExportFormat.JSON,
            elements_exported=10,
            systems_exported=2,
            relationships_exported=5,
            svgx_elements_exported=8
        )

        assert result.success is True
        assert result.file_path == "/tmp/test.json"
        assert result.file_size == 1024
        assert result.export_time == 1.5
        assert result.format == ExportFormat.JSON
        assert result.elements_exported == 10
        assert result.svgx_elements_exported == 8

    def test_import_result_dataclass(self):
        """Test ImportResult dataclass functionality."""
        result = ImportResult(
            success=True,
            elements_imported=10,
            systems_imported=2,
            relationships_imported=5,
            svgx_elements_imported=8,
            import_time=1.5,
            format=ImportFormat.JSON
        )

        assert result.success is True
        assert result.elements_imported == 10
        assert result.systems_imported == 2
        assert result.relationships_imported == 5
        assert result.svgx_elements_imported == 8
        assert result.import_time == 1.5
        assert result.format == ImportFormat.JSON

    def test_error_handling_export(self, export_service, sample_bim_model):
        """Test error handling during export."""
        with patch.object(export_service, '_generate_json_content', side_effect=Exception("Test error")):
            with pytest.raises(ExportError):
                export_service.export_bim_model(sample_bim_model, ExportFormat.JSON, {})

    def test_error_handling_import(self, export_service):
        """Test error handling during import."""
        with patch.object(export_service, '_import_json', side_effect=Exception("Test error")):
            with pytest.raises(ImportError):
                export_service.import_bim_model("/tmp/test.json", ImportFormat.JSON, {})

    def test_performance_monitoring(self, export_service, sample_bim_model):
        """Test that performance monitoring is active."""
        with patch.object(export_service, '_generate_json_content', return_value='{"test": "content"}'):
            with patch.object(export_service, '_save_to_file', return_value="/tmp/test.json"):
                result = export_service.export_bim_model(sample_bim_model, ExportFormat.JSON, {})

                assert result.performance_metrics is not None
                assert isinstance(result.performance_metrics, dict)


class TestExportFormat:
    """Test cases for ExportFormat enum."""

    def test_export_format_values(self):
        """Test that all expected export formats are available."""
        formats = [f.value for f in ExportFormat]
        expected = ['ifc', 'rvt', 'rfa', 'json', 'xml', 'gltf', 'obj', 'fbx', 'dae', 'threejs', 'svgx', 'custom']

        for expected_format in expected:
            assert expected_format in formats

    def test_svgx_format(self):
        """Test that SVGX format is specifically available."""
        assert ExportFormat.SVGX.value == 'svgx'


class TestImportFormat:
    """Test cases for ImportFormat enum."""

    def test_import_format_values(self):
        """Test that all expected import formats are available."""
        formats = [f.value for f in ImportFormat]
        expected = ['ifc', 'json', 'xml', 'gltf', 'obj', 'fbx', 'svgx', 'custom']

        for expected_format in expected:
            assert expected_format in formats

    def test_svgx_format(self):
        """Test that SVGX format is specifically available."""
        assert ImportFormat.SVGX.value == 'svgx'


def test_create_bim_export_service():
    """Test the convenience function for creating BIM export service."""
    from svgx_engine.services.bim_export import create_bim_export_service

    service = create_bim_export_service()
    assert isinstance(service, SVGXBIMExportService)
    assert service is not None


if __name__ == "__main__":
    pytest.main([__file__])
