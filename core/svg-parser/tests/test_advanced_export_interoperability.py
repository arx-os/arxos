"""
Advanced Export & Interoperability Tests

Comprehensive test suite for BIM data export in various industry-standard formats:
- IFC-lite for BIM interoperability
- glTF for 3D visualization
- ASCII-BIM for roundtrip conversion
- Excel, Parquet, GeoJSON for analytics and GIS
"""

import pytest
import json
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from core.services.advanced_export_interoperability
    AdvancedExportInteroperabilityService,
    ExportFormat
)
from core.routers.advanced_export_interoperability
from core.api.main

# Test BIM data
SAMPLE_BIM_DATA = {
    "elements": [
        {
            "id": "elem_001",
            "type": "wall",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [10, 0], [10, 3], [0, 3], [0, 0]]]
            },
            "properties": {
                "material": "concrete",
                "height": 3.0,
                "thickness": 0.2
            }
        },
        {
            "id": "elem_002",
            "type": "door",
            "geometry": {
                "type": "Point",
                "coordinates": [5, 0]
            },
            "properties": {
                "width": 1.0,
                "height": 2.1,
                "material": "wood"
            }
        }
    ],
    "metadata": {
        "project_name": "Test Building",
        "version": "1.0",
        "created_at": "2024-01-01T00:00:00Z"
    }
}


class TestAdvancedExportInteroperabilityService:
    """Test the core export service."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service instance."""
        return AdvancedExportInteroperabilityService()
    
    def test_export_ifc_lite(self, export_service):
        """Test IFC-lite export."""
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_ifc_lite(SAMPLE_BIM_DATA, output_path)
            
            assert result.exists()
            assert result.suffix == '.ifc'
            
            # Check file content
            with open(result, 'r') as f:
                content = f.read()
                assert "IFC-LITE EXPORT" in content
                assert "elem_001" in content
                assert "elem_002" in content
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_gltf(self, export_service):
        """Test glTF export."""
        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_gltf(SAMPLE_BIM_DATA, output_path)
            
            assert result.exists()
            assert result.suffix == '.gltf'
            
            # Check file content
            with open(result, 'r') as f:
                content = f.read()
                assert "GLTF EXPORT" in content
                assert "elem_001" in content
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_ascii_bim(self, export_service):
        """Test ASCII-BIM export."""
        with tempfile.NamedTemporaryFile(suffix='.bim', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_ascii_bim(SAMPLE_BIM_DATA, output_path)
            
            assert result.exists()
            assert result.suffix == '.bim'
            
            # Check file content
            with open(result, 'r') as f:
                content = f.read()
                assert "ASCII-BIM EXPORT" in content
                assert "elem_001" in content
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_excel(self, export_service):
        """Test Excel export."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_excel(SAMPLE_BIM_DATA, output_path)
            
            assert result.exists()
            assert result.suffix == '.xlsx'
            
            # Check Excel file can be read
            df = pd.read_excel(result)
            assert len(df) == 2  # Two elements
            assert 'id' in df.columns
            assert 'type' in df.columns
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_parquet(self, export_service):
        """Test Parquet export."""
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_parquet(SAMPLE_BIM_DATA, output_path)
            
            assert result.exists()
            assert result.suffix == '.parquet'
            
            # Check Parquet file can be read
            df = pd.read_parquet(result)
            assert len(df) == 2  # Two elements
            assert 'id' in df.columns
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_geojson(self, export_service):
        """Test GeoJSON export."""
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_geojson(SAMPLE_BIM_DATA, output_path)
            
            assert result.exists()
            assert result.suffix == '.geojson'
            
            # Check GeoJSON file can be read
            with open(result, 'r') as f:
                geojson = json.load(f)
                assert geojson["type"] == "FeatureCollection"
                assert len(geojson["features"]) == 2
                assert geojson["features"][0]["properties"]["id"] == "elem_001"
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_with_options(self, export_service):
        """Test export with options."""
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            options = {"include_metadata": True, "compression": "none"}
            result = export_service.export_ifc_lite(SAMPLE_BIM_DATA, output_path, options)
            
            assert result.exists()
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_invalid_format(self, export_service):
        """Test export with invalid format."""
        with tempfile.NamedTemporaryFile(suffix='.invalid', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(ValueError, match="Unsupported export format"):
                export_service.export(SAMPLE_BIM_DATA, "invalid_format", output_path)
                
        finally:
            if output_path.exists():
                output_path.unlink()


class TestAdvancedExportInteroperabilityAPI:
    """Test the API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_export_endpoint(self, client):
        """Test export API endpoint."""
        request_data = {
            "data": SAMPLE_BIM_DATA,
            "format": "ifc-lite",
            "options": {"include_metadata": True}
        }
        
        response = client.post("/api/v1/export/export", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["format"] == "ifc-lite"
        assert "file_path" in data
        assert "file_size" in data
        assert "export_time" in data
    
    def test_export_invalid_format(self, client):
        """Test export with invalid format."""
        request_data = {
            "data": SAMPLE_BIM_DATA,
            "format": "invalid-format"
        }
        
        response = client.post("/api/v1/export/export", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported export format" in data["detail"]
    
    def test_get_supported_formats(self, client):
        """Test supported formats endpoint."""
        response = client.get("/api/v1/export/formats")
        
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "total_formats" in data
        assert data["total_formats"] == 6
        
        formats = data["formats"]
        format_names = [f["format"] for f in formats]
        assert "ifc-lite" in format_names
        assert "gltf" in format_names
        assert "ascii-bim" in format_names
        assert "excel" in format_names
        assert "parquet" in format_names
        assert "geojson" in format_names
    
    def test_validate_data(self, client):
        """Test data validation endpoint."""
        # Valid data
        response = client.post("/api/v1/export/validate", json=SAMPLE_BIM_DATA)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0
    
    def test_validate_invalid_data(self, client):
        """Test validation with invalid data."""
        invalid_data = {"invalid": "data"}
        
        response = client.post("/api/v1/export/validate", json=invalid_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/export/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Advanced Export & Interoperability" in data["service"]
        assert "supported_formats" in data


class TestAdvancedExportInteroperabilityCLI:
    """Test the CLI commands."""
    
    def test_export_data_command(self, tmp_path):
        """Test export data CLI command."""
        from ..cmd.advanced_export_cli import export_data
        
        # Create test data file
        data_file = tmp_path / "test_data.json"
        with open(data_file, 'w') as f:
            json.dump(SAMPLE_BIM_DATA, f)
        
        # Create output file path
        output_file = tmp_path / "test_output.ifc"
        
        # Mock click context
        with patch('click.echo') as mock_echo:
            with patch('sys.exit') as mock_exit:
                # Test successful export
                export_data.callback(
                    str(data_file),
                    str(output_file),
                    'ifc-lite',
                    None,
                    False,
                    False
                )
                
                # Verify file was created
                assert output_file.exists()
                
                # Check file content
                with open(output_file, 'r') as f:
                    content = f.read()
                    assert "IFC-LITE EXPORT" in content
    
    def test_validate_command(self, tmp_path):
        """Test validate CLI command."""
        from ..cmd.advanced_export_cli import validate
        
        # Create test data file
        data_file = tmp_path / "test_data.json"
        with open(data_file, 'w') as f:
            json.dump(SAMPLE_BIM_DATA, f)
        
        # Mock click context
        with patch('click.echo') as mock_echo:
            with patch('sys.exit') as mock_exit:
                # Test successful validation
                validate.callback(str(data_file), False)
                
                # Verify validation passed
                mock_echo.assert_called_with("✅ Data validation passed!")
    
    def test_formats_command(self):
        """Test formats CLI command."""
        from ..cmd.advanced_export_cli import formats
        
        # Mock click context
        with patch('click.echo') as mock_echo:
            formats.callback()
            
            # Verify formats were displayed
            mock_echo.assert_called()
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("Supported Export Formats" in call for call in calls)
    
    def test_batch_export_command(self, tmp_path):
        """Test batch export CLI command."""
        from ..cmd.advanced_export_cli import batch_export
        
        # Create test data file
        data_file = tmp_path / "test_data.json"
        with open(data_file, 'w') as f:
            json.dump(SAMPLE_BIM_DATA, f)
        
        # Create output directory
        output_dir = tmp_path / "exports"
        output_dir.mkdir()
        
        # Mock click context
        with patch('click.echo') as mock_echo:
            with patch('sys.exit') as mock_exit:
                # Test successful batch export
                batch_export.callback(
                    str(data_file),
                    str(output_dir),
                    "ifc-lite,gltf",
                    False
                )
                
                # Verify files were created
                export_files = list(output_dir.glob("*.ifc")) + list(output_dir.glob("*.gltf"))
                assert len(export_files) == 2


class TestExportFormats:
    """Test specific export format implementations."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service instance."""
        return AdvancedExportInteroperabilityService()
    
    def test_ifc_lite_structure(self, export_service):
        """Test IFC-lite export structure."""
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_ifc_lite(SAMPLE_BIM_DATA, output_path)
            
            with open(result, 'r') as f:
                content = f.read()
                
                # Check for IFC structure indicators
                assert "IFC-LITE EXPORT" in content
                assert "elem_001" in content
                assert "wall" in content
                assert "door" in content
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_gltf_structure(self, export_service):
        """Test glTF export structure."""
        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_gltf(SAMPLE_BIM_DATA, output_path)
            
            with open(result, 'r') as f:
                content = f.read()
                
                # Check for glTF structure indicators
                assert "GLTF EXPORT" in content
                assert "elem_001" in content
                
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_geojson_structure(self, export_service):
        """Test GeoJSON export structure."""
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            result = export_service.export_geojson(SAMPLE_BIM_DATA, output_path)
            
            with open(result, 'r') as f:
                geojson = json.load(f)
                
                # Check GeoJSON structure
                assert geojson["type"] == "FeatureCollection"
                assert len(geojson["features"]) == 2
                
                # Check feature properties
                feature = geojson["features"][0]
                assert "properties" in feature
                assert "geometry" in feature
                assert feature["properties"]["id"] == "elem_001"
                
        finally:
            if output_path.exists():
                output_path.unlink()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service instance."""
        return AdvancedExportInteroperabilityService()
    
    def test_export_to_readonly_location(self, export_service):
        """Test export to read-only location."""
        # Try to export to a location that doesn't exist
        output_path = Path("/nonexistent/path/test.ifc")
        
        with pytest.raises(Exception):
            export_service.export_ifc_lite(SAMPLE_BIM_DATA, output_path)
    
    def test_export_with_empty_data(self, export_service):
        """Test export with empty data."""
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            empty_data = {"elements": [], "metadata": {}}
            result = export_service.export_ifc_lite(empty_data, output_path)
            
            assert result.exists()
            
        finally:
            if output_path.exists():
                output_path.unlink()
    
    def test_export_with_malformed_data(self, export_service):
        """Test export with malformed data."""
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            malformed_data = {"invalid": "data"}
            result = export_service.export_ifc_lite(malformed_data, output_path)
            
            assert result.exists()
            
        finally:
            if output_path.exists():
                output_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 