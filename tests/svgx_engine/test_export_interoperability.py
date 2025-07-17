"""
Tests for SVGX Engine Export Interoperability Service

Comprehensive test suite covering:
- Export job management
- Format-specific exports (IFC, glTF, SVGX, etc.)
- Error handling and validation
- Performance monitoring
- SVGX-specific enhancements
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch

from svgx_engine.services.export_interoperability import (
    SVGXExportInteroperabilityService,
    ExportFormat,
    ExportStatus,
    ExportJob,
    create_svgx_export_service
)
from svgx_engine.utils.errors import ExportError


class TestSVGXExportInteroperabilityService:
    """Test suite for SVGX Export Interoperability Service."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_export.db"
        yield str(db_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def export_service(self, temp_db_path):
        """Create an export service instance for testing."""
        return SVGXExportInteroperabilityService(temp_db_path)
    
    @pytest.fixture
    def sample_building_data(self):
        """Sample building data for testing exports."""
        return {
            "building_id": "test_building_001",
            "name": "Test Building",
            "svgx_elements": [
                {
                    "id": "element_001",
                    "name": "Electrical Outlet",
                    "type": "electrical",
                    "category": "electrical",
                    "coordinates": [10, 20],
                    "properties": {
                        "voltage": "120V",
                        "amperage": "15A"
                    }
                },
                {
                    "id": "element_002", 
                    "name": "HVAC Duct",
                    "type": "mechanical",
                    "category": "mechanical",
                    "coordinates": [30, 40],
                    "properties": {
                        "diameter": "12in",
                        "flow_rate": "500cfm"
                    }
                }
            ]
        }
    
    def test_initialization(self, temp_db_path):
        """Test export service initialization."""
        service = SVGXExportInteroperabilityService(temp_db_path)
        assert service.db_path == temp_db_path
        assert isinstance(service.export_jobs, dict)
        assert service.ifc_header.file_description == "SVGX Engine Export"
        assert service.gltf_asset.generator == "SVGX Engine Exporter"
    
    def test_create_export_job(self, export_service):
        """Test export job creation."""
        job_id = export_service.create_export_job(
            building_id="test_building",
            format=ExportFormat.IFC_LITE,
            options={"output_path": "test.ifc"}
        )
        
        assert job_id is not None
        assert job_id in export_service.export_jobs
        
        job = export_service.export_jobs[job_id]
        assert job.building_id == "test_building"
        assert job.format == ExportFormat.IFC_LITE
        assert job.status == ExportStatus.PENDING
        assert job.options["output_path"] == "test.ifc"
    
    def test_export_to_ifc_lite(self, export_service, sample_building_data, temp_db_path):
        """Test IFC-lite export functionality."""
        temp_dir = Path(temp_db_path).parent
        output_path = temp_dir / "test_export.ifc"
        
        result = export_service.export_to_ifc_lite(
            sample_building_data,
            options={"output_path": str(output_path)}
        )
        
        assert result == str(output_path)
        assert output_path.exists()
        
        # Verify IFC content
        with open(output_path, 'r') as f:
            content = f.read()
            assert "ISO-10303-21" in content
            assert "SVGX Engine Export" in content
            assert "IFCBUILDING" in content
    
    def test_export_to_gltf(self, export_service, sample_building_data, temp_db_path):
        """Test glTF export functionality."""
        temp_dir = Path(temp_db_path).parent
        output_path = temp_dir / "test_export.gltf"
        
        result = export_service.export_to_gltf(
            sample_building_data,
            options={"output_path": str(output_path)}
        )
        
        assert result == str(output_path)
        assert output_path.exists()
        
        # Verify glTF content
        with open(output_path, 'r') as f:
            content = json.load(f)
            assert "asset" in content
            assert content["asset"]["generator"] == "SVGX Engine Exporter"
            assert "scenes" in content
            assert "nodes" in content
    
    def test_export_to_svgx(self, export_service, sample_building_data, temp_db_path):
        """Test SVGX format export functionality."""
        temp_dir = Path(temp_db_path).parent
        output_path = temp_dir / "test_export.svgx"
        
        result = export_service.export_to_svgx(
            sample_building_data,
            options={"output_path": str(output_path)}
        )
        
        assert result == str(output_path)
        assert output_path.exists()
        
        # Verify SVGX content
        with open(output_path, 'r') as f:
            content = json.load(f)
            assert content["version"] == "1.0"
            assert content["generator"] == "SVGX Engine"
            assert "building_data" in content
            assert "svgx_metadata" in content
    
    def test_export_to_excel(self, export_service, sample_building_data, temp_db_path):
        """Test Excel export functionality."""
        temp_dir = Path(temp_db_path).parent
        output_path = temp_dir / "test_export.xlsx"
        
        result = export_service.export_to_excel(
            sample_building_data,
            options={"output_path": str(output_path)}
        )
        
        assert result == str(output_path)
        assert output_path.exists()
        
        # Verify Excel content
        with open(output_path, 'r') as f:
            content = f.read()
            assert "Building Data Export" in content
            assert "SVGX Engine" in content
            assert "SVGX Elements" in content
    
    def test_export_to_geojson(self, export_service, sample_building_data, temp_db_path):
        """Test GeoJSON export functionality."""
        temp_dir = Path(temp_db_path).parent
        output_path = temp_dir / "test_export.geojson"
        
        result = export_service.export_to_geojson(
            sample_building_data,
            options={"output_path": str(output_path)}
        )
        
        assert result == str(output_path)
        assert output_path.exists()
        
        # Verify GeoJSON content
        with open(output_path, 'r') as f:
            content = json.load(f)
            assert content["type"] == "FeatureCollection"
            assert "features" in content
            assert len(content["features"]) == 2
    
    def test_get_export_job_status(self, export_service):
        """Test export job status retrieval."""
        job_id = export_service.create_export_job(
            building_id="test_building",
            format=ExportFormat.IFC_LITE
        )
        
        job = export_service.get_export_job_status(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.building_id == "test_building"
    
    def test_get_export_job_status_not_found(self, export_service):
        """Test export job status retrieval for non-existent job."""
        job = export_service.get_export_job_status("non_existent_id")
        assert job is None
    
    def test_list_export_jobs(self, export_service):
        """Test listing export jobs."""
        # Create multiple jobs
        job1 = export_service.create_export_job(
            building_id="building_1",
            format=ExportFormat.IFC_LITE
        )
        job2 = export_service.create_export_job(
            building_id="building_2", 
            format=ExportFormat.GLTF
        )
        
        # List all jobs
        all_jobs = export_service.list_export_jobs()
        assert len(all_jobs) == 2
        
        # List jobs for specific building
        building_1_jobs = export_service.list_export_jobs(building_id="building_1")
        assert len(building_1_jobs) == 1
        assert building_1_jobs[0].building_id == "building_1"
    
    def test_cancel_export_job(self, export_service):
        """Test export job cancellation."""
        job_id = export_service.create_export_job(
            building_id="test_building",
            format=ExportFormat.IFC_LITE
        )
        
        result = export_service.cancel_export_job(job_id)
        assert result is True
        
        job = export_service.get_export_job_status(job_id)
        assert job.status == ExportStatus.CANCELLED
    
    def test_cancel_export_job_not_found(self, export_service):
        """Test cancelling non-existent export job."""
        result = export_service.cancel_export_job("non_existent_id")
        assert result is False
    
    def test_get_export_statistics(self, export_service):
        """Test export statistics."""
        # Create jobs in different formats
        export_service.create_export_job(
            building_id="building_1",
            format=ExportFormat.IFC_LITE
        )
        export_service.create_export_job(
            building_id="building_2",
            format=ExportFormat.GLTF
        )
        
        stats = export_service.get_export_statistics()
        
        assert stats["total_jobs"] == 2
        assert "ifc_lite" in stats["format_breakdown"]
        assert "gltf" in stats["format_breakdown"]
        assert "pending" in stats["status_breakdown"]
        assert "performance_metrics" in stats
    
    def test_export_error_handling(self, export_service, sample_building_data):
        """Test export error handling."""
        # Test with invalid options
        with pytest.raises(ExportError):
            export_service.export_to_ifc_lite(
                sample_building_data,
                options={"invalid_option": "value"}
            )
    
    def test_database_persistence(self, export_service):
        """Test that export jobs persist in database."""
        job_id = export_service.create_export_job(
            building_id="test_building",
            format=ExportFormat.IFC_LITE
        )
        
        # Create new service instance (should load from database)
        new_service = SVGXExportInteroperabilityService(export_service.db_path)
        
        # Verify job exists in new instance
        job = new_service.get_export_job_status(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.building_id == "test_building"


class TestSVGXExportInteroperabilityServiceConvenienceFunction:
    """Test the convenience function for creating export services."""
    
    def test_create_svgx_export_service_default(self):
        """Test creating export service with default path."""
        service = create_svgx_export_service()
        assert isinstance(service, SVGXExportInteroperabilityService)
    
    def test_create_svgx_export_service_custom_path(self, temp_db_path):
        """Test creating export service with custom path."""
        service = create_svgx_export_service(temp_db_path)
        assert isinstance(service, SVGXExportInteroperabilityService)
        assert service.db_path == temp_db_path


if __name__ == "__main__":
    pytest.main([__file__]) 