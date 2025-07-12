"""
Comprehensive tests for Export Interoperability Service.

Tests cover:
- IFC-lite export functionality
- glTF export functionality
- ASCII-BIM export functionality
- Excel export functionality
- GeoJSON export functionality
- Export job management
- Error handling and edge cases
"""

import pytest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from ..services.export_interoperability import (
    ExportInteroperabilityService, ExportFormat, ExportStatus,
    ExportJob, IFCHeader, GLTFAsset
)

class TestExportInteroperabilityService:
    """Test cases for ExportInteroperabilityService."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def export_service(self, temp_db):
        """Create ExportInteroperabilityService instance with temporary database."""
        return ExportInteroperabilityService(db_path=temp_db)
    
    @pytest.fixture
    def sample_building_data(self):
        """Sample building data for testing."""
        return {
            "building_id": "TEST_BUILDING_001",
            "building_name": "Test Building",
            "floor_count": 3,
            "total_area_sqft": 50000.0,
            "elements": [
                {
                    "id": "ELEMENT_001",
                    "name": "Wall 1",
                    "type": "WALL",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "system": "STRUCTURAL",
                    "floor": 1
                },
                {
                    "id": "ELEMENT_002",
                    "name": "Door 1",
                    "type": "DOOR",
                    "x": 10.0,
                    "y": 0.0,
                    "z": 0.0,
                    "system": "ARCHITECTURAL",
                    "floor": 1
                },
                {
                    "id": "ELEMENT_003",
                    "name": "Window 1",
                    "type": "WINDOW",
                    "x": 20.0,
                    "y": 0.0,
                    "z": 0.0,
                    "system": "ARCHITECTURAL",
                    "floor": 1
                }
            ],
            "systems": [
                {
                    "id": "SYSTEM_001",
                    "name": "Structural System",
                    "type": "STRUCTURAL",
                    "elements": ["ELEMENT_001"]
                },
                {
                    "id": "SYSTEM_002",
                    "name": "Architectural System",
                    "type": "ARCHITECTURAL",
                    "elements": ["ELEMENT_002", "ELEMENT_003"]
                }
            ]
        }
    
    def test_init_database(self, temp_db):
        """Test database initialization."""
        service = ExportInteroperabilityService(db_path=temp_db)
        
        # Check if tables were created
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'export_jobs' in tables
        
        conn.close()
    
    def test_create_export_job(self, export_service):
        """Test export job creation."""
        job_id = export_service.create_export_job(
            building_id="TEST_BUILDING",
            format=ExportFormat.IFC_LITE,
            options={"output_path": "test.ifc"}
        )
        
        assert job_id is not None
        assert job_id in export_service.export_jobs
        
        job = export_service.export_jobs[job_id]
        assert job.building_id == "TEST_BUILDING"
        assert job.format == ExportFormat.IFC_LITE
        assert job.status == ExportStatus.PENDING
        assert job.options["output_path"] == "test.ifc"
    
    def test_export_to_ifc_lite(self, export_service, sample_building_data):
        """Test IFC-lite export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.ifc")
            
            result = export_service.export_to_ifc_lite(
                building_data=sample_building_data,
                options={"output_path": output_path}
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            
            # Check IFC content
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "ISO-10303-21;" in content
            assert "IFCBUILDING" in content
            assert "IFCWALL" in content
            assert "IFCDOOR" in content
            assert "IFCWINDOW" in content
    
    def test_export_to_gltf(self, export_service, sample_building_data):
        """Test glTF export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.gltf")
            
            result = export_service.export_to_gltf(
                building_data=sample_building_data,
                options={"output_path": output_path}
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            
            # Check glTF content
            with open(output_path, 'r') as f:
                content = json.load(f)
            
            assert "asset" in content
            assert "scene" in content
            assert "scenes" in content
            assert "nodes" in content
            assert "meshes" in content
            assert content["asset"]["version"] == "2.0"
            assert content["asset"]["generator"] == "Arxos SVG-BIM Exporter"
    
    def test_export_to_ascii_bim(self, export_service, sample_building_data):
        """Test ASCII-BIM export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.txt")
            
            result = export_service.export_to_ascii_bim(
                building_data=sample_building_data,
                options={"output_path": output_path}
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            
            # Check ASCII-BIM content
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "ASCII-BIM Export from Arxos Platform" in content
            assert "BUILDING {" in content
            assert "ELEMENTS {" in content
            assert "SYSTEMS {" in content
            assert "TEST_BUILDING_001" in content
            assert "Wall 1" in content
            assert "Door 1" in content
            assert "Window 1" in content
    
    @patch('services.export_interoperability.pd')
    def test_export_to_excel(self, mock_pd, export_service, sample_building_data):
        """Test Excel export functionality."""
        mock_excel_writer = MagicMock()
        mock_pd.ExcelWriter.return_value.__enter__.return_value = mock_excel_writer
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.xlsx")
            
            result = export_service.export_to_excel(
                building_data=sample_building_data,
                options={"output_path": output_path}
            )
            
            assert result == output_path
            mock_pd.ExcelWriter.assert_called_once_with(output_path, engine='openpyxl')
    
    def test_export_to_geojson(self, export_service, sample_building_data):
        """Test GeoJSON export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.geojson")
            
            result = export_service.export_to_geojson(
                building_data=sample_building_data,
                options={"output_path": output_path}
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            
            # Check GeoJSON content
            with open(output_path, 'r') as f:
                content = json.load(f)
            
            assert content["type"] == "FeatureCollection"
            assert "features" in content
            assert len(content["features"]) == 3  # 3 elements
            
            # Check feature properties
            feature = content["features"][0]
            assert "geometry" in feature
            assert "properties" in feature
            assert feature["geometry"]["type"] == "Point"
            assert "coordinates" in feature["geometry"]
            assert "id" in feature["properties"]
            assert "name" in feature["properties"]
            assert "type" in feature["properties"]
    
    def test_get_export_job_status(self, export_service):
        """Test export job status retrieval."""
        job_id = export_service.create_export_job(
            building_id="TEST_BUILDING",
            format=ExportFormat.IFC_LITE
        )
        
        job = export_service.get_export_job_status(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.status == ExportStatus.PENDING
        
        # Test non-existent job
        non_existent_job = export_service.get_export_job_status("NON_EXISTENT")
        assert non_existent_job is None
    
    def test_list_export_jobs(self, export_service):
        """Test export job listing."""
        # Create multiple jobs
        job1_id = export_service.create_export_job(
            building_id="BUILDING_1",
            format=ExportFormat.IFC_LITE
        )
        job2_id = export_service.create_export_job(
            building_id="BUILDING_2",
            format=ExportFormat.GLTF
        )
        job3_id = export_service.create_export_job(
            building_id="BUILDING_1",
            format=ExportFormat.ASCII_BIM
        )
        
        # List all jobs
        all_jobs = export_service.list_export_jobs()
        assert len(all_jobs) == 3
        
        # List jobs for specific building
        building_1_jobs = export_service.list_export_jobs(building_id="BUILDING_1")
        assert len(building_1_jobs) == 2
        assert all(job.building_id == "BUILDING_1" for job in building_1_jobs)
        
        # List jobs for non-existent building
        non_existent_jobs = export_service.list_export_jobs(building_id="NON_EXISTENT")
        assert len(non_existent_jobs) == 0
    
    def test_cancel_export_job(self, export_service):
        """Test export job cancellation."""
        job_id = export_service.create_export_job(
            building_id="TEST_BUILDING",
            format=ExportFormat.IFC_LITE
        )
        
        # Cancel job
        result = export_service.cancel_export_job(job_id)
        assert result is True
        
        # Check job status
        job = export_service.get_export_job_status(job_id)
        assert job.status == ExportStatus.CANCELLED
        assert job.completed_at is not None
        
        # Try to cancel non-existent job
        result = export_service.cancel_export_job("NON_EXISTENT")
        assert result is False
    
    def test_get_export_statistics(self, export_service):
        """Test export statistics retrieval."""
        # Create jobs with different formats and statuses
        job1_id = export_service.create_export_job(
            building_id="BUILDING_1",
            format=ExportFormat.IFC_LITE
        )
        job2_id = export_service.create_export_job(
            building_id="BUILDING_2",
            format=ExportFormat.GLTF
        )
        
        # Cancel one job
        export_service.cancel_export_job(job1_id)
        
        # Get statistics
        stats = export_service.get_export_statistics()
        
        assert "total_jobs" in stats
        assert "by_format" in stats
        assert "by_status" in stats
        assert stats["total_jobs"] == 2
        
        # Check format statistics
        assert "ifc_lite" in stats["by_format"]
        assert "gltf" in stats["by_format"]
        
        # Check status statistics
        assert "pending" in stats["by_status"]
        assert "cancelled" in stats["by_status"]
    
    def test_ifc_header_defaults(self):
        """Test IFC header default values."""
        header = IFCHeader()
        
        assert header.file_description == "Arxos SVG-BIM Export"
        assert header.implementation_level == "2;1"
        assert header.author == "Arxos System"
        assert header.organization == "Arxos"
        assert header.preprocessor_version == "Arxos SVG-BIM Parser"
        assert header.originating_system == "Arxos Platform"
        assert header.authorization == "Arxos User"
    
    def test_gltf_asset_defaults(self):
        """Test glTF asset default values."""
        asset = GLTFAsset()
        
        assert asset.version == "2.0"
        assert asset.generator == "Arxos SVG-BIM Exporter"
        assert asset.copyright == "Arxos Platform"
    
    def test_export_with_empty_building_data(self, export_service):
        """Test export with empty building data."""
        empty_data = {
            "building_id": "EMPTY_BUILDING",
            "building_name": "Empty Building",
            "elements": [],
            "systems": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "empty.ifc")
            
            # Should not raise an exception
            result = export_service.export_to_ifc_lite(
                building_data=empty_data,
                options={"output_path": output_path}
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
    
    def test_export_with_missing_optional_fields(self, export_service):
        """Test export with missing optional fields."""
        minimal_data = {
            "building_id": "MINIMAL_BUILDING",
            "elements": [
                {
                    "id": "ELEMENT_001",
                    "type": "WALL"
                    # Missing optional fields
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "minimal.ifc")
            
            # Should not raise an exception
            result = export_service.export_to_ifc_lite(
                building_data=minimal_data,
                options={"output_path": output_path}
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
    
    def test_export_error_handling(self, export_service):
        """Test export error handling."""
        invalid_data = None
        
        with pytest.raises(Exception):
            export_service.export_to_ifc_lite(
                building_data=invalid_data,
                options={"output_path": "test.ifc"}
            )
    
    def test_export_job_persistence(self, temp_db):
        """Test that export jobs persist across service instances."""
        # Create first service instance
        service1 = ExportInteroperabilityService(db_path=temp_db)
        job_id = service1.create_export_job(
            building_id="TEST_BUILDING",
            format=ExportFormat.IFC_LITE
        )
        
        # Create second service instance
        service2 = ExportInteroperabilityService(db_path=temp_db)
        
        # Job should be accessible from second instance
        job = service2.get_export_job_status(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.building_id == "TEST_BUILDING"
        assert job.format == ExportFormat.IFC_LITE 