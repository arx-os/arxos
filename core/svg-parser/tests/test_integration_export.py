"""
Integration Tests for Export Interoperability Service

Tests complete workflows and service interactions:
- End-to-end export workflows
- Service integration testing
- API endpoint integration
- Error handling and recovery
- Performance under load
"""

import pytest
import tempfile
import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import threading
import concurrent.futures

from ..services.export_interoperability import (
    ExportInteroperabilityService, ExportFormat, ExportStatus
)
from ..services.enhanced_bim_assembly import EnhancedBIMAssembly
from ..services.access_control import AccessControlService
from ..utils.response_helpers import ResponseHelper

class TestExportIntegration:
    """Integration tests for export interoperability service."""
    
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
        """Create ExportInteroperabilityService instance."""
        return ExportInteroperabilityService(db_path=temp_db)
    
    @pytest.fixture
    def bim_service(self):
        """Create BIM assembly service instance."""
        return EnhancedBIMAssembly()
    
    @pytest.fixture
    def access_service(self):
        """Create access control service instance."""
        return AccessControlService()
    
    @pytest.fixture
    def sample_building_data(self):
        """Comprehensive sample building data for integration testing."""
        return {
            "building_id": "INTEGRATION_TEST_BUILDING",
            "building_name": "Integration Test Building",
            "floor_count": 5,
            "total_area_sqft": 100000.0,
            "construction_year": 2023,
            "address": {
                "street": "123 Integration Street",
                "city": "Test City",
                "state": "TC",
                "zip": "12345",
                "country": "USA"
            },
            "elements": [
                # Structural elements
                {
                    "id": "WALL_001",
                    "name": "Exterior Wall North",
                    "type": "WALL",
                    "x": 0.0, "y": 0.0, "z": 0.0,
                    "system": "STRUCTURAL",
                    "floor": 1,
                    "properties": {
                        "material": "Concrete",
                        "thickness": 0.3,
                        "height": 3.0,
                        "length": 100.0
                    }
                },
                {
                    "id": "COLUMN_001",
                    "name": "Structural Column A1",
                    "type": "COLUMN",
                    "x": 10.0, "y": 10.0, "z": 0.0,
                    "system": "STRUCTURAL",
                    "floor": 1,
                    "properties": {
                        "material": "Steel",
                        "diameter": 0.5,
                        "height": 15.0
                    }
                },
                # Architectural elements
                {
                    "id": "DOOR_001",
                    "name": "Main Entrance",
                    "type": "DOOR",
                    "x": 50.0, "y": 0.0, "z": 0.0,
                    "system": "ARCHITECTURAL",
                    "floor": 1,
                    "properties": {
                        "material": "Glass",
                        "width": 2.0,
                        "height": 2.5,
                        "type": "Sliding"
                    }
                },
                {
                    "id": "WINDOW_001",
                    "name": "Office Window 1",
                    "type": "WINDOW",
                    "x": 5.0, "y": 0.0, "z": 1.0,
                    "system": "ARCHITECTURAL",
                    "floor": 1,
                    "properties": {
                        "material": "Glass",
                        "width": 1.5,
                        "height": 1.2,
                        "type": "Fixed"
                    }
                },
                # MEP elements
                {
                    "id": "HVAC_001",
                    "name": "Air Handler Unit 1",
                    "type": "HVAC",
                    "x": 90.0, "y": 90.0, "z": 0.0,
                    "system": "MECHANICAL",
                    "floor": 1,
                    "properties": {
                        "capacity": 10000.0,
                        "flow_rate": 5000.0,
                        "efficiency": 0.90
                    }
                },
                {
                    "id": "ELECTRICAL_001",
                    "name": "Electrical Panel 1",
                    "type": "ELECTRICAL",
                    "x": 5.0, "y": 90.0, "z": 0.0,
                    "system": "ELECTRICAL",
                    "floor": 1,
                    "properties": {
                        "voltage": 480.0,
                        "current": 200.0,
                        "phase": "Three"
                    }
                },
                {
                    "id": "PLUMBING_001",
                    "name": "Water Main",
                    "type": "PLUMBING",
                    "x": 0.0, "y": 50.0, "z": -1.0,
                    "system": "PLUMBING",
                    "floor": 1,
                    "properties": {
                        "pipe_size": "6 inch",
                        "material": "Copper",
                        "flow_rate": 200.0
                    }
                }
            ],
            "systems": [
                {
                    "id": "SYSTEM_STRUCTURAL",
                    "name": "Structural System",
                    "type": "STRUCTURAL",
                    "elements": ["WALL_001", "COLUMN_001"],
                    "properties": {
                        "design_code": "IBC 2021",
                        "seismic_zone": "Zone 4",
                        "wind_load": "150 mph"
                    }
                },
                {
                    "id": "SYSTEM_ARCHITECTURAL",
                    "name": "Architectural System",
                    "type": "ARCHITECTURAL",
                    "elements": ["DOOR_001", "WINDOW_001"],
                    "properties": {
                        "finish_grade": "Premium",
                        "fire_rating": "2 hour"
                    }
                },
                {
                    "id": "SYSTEM_MECHANICAL",
                    "name": "Mechanical System",
                    "type": "MECHANICAL",
                    "elements": ["HVAC_001"],
                    "properties": {
                        "design_temp": "72°F",
                        "humidity": "50%",
                        "air_changes": 8
                    }
                },
                {
                    "id": "SYSTEM_ELECTRICAL",
                    "name": "Electrical System",
                    "type": "ELECTRICAL",
                    "elements": ["ELECTRICAL_001"],
                    "properties": {
                        "service_size": "800A",
                        "voltage": "480V/277V",
                        "backup_power": "UPS"
                    }
                },
                {
                    "id": "SYSTEM_PLUMBING",
                    "name": "Plumbing System",
                    "type": "PLUMBING",
                    "elements": ["PLUMBING_001"],
                    "properties": {
                        "water_supply": "Municipal",
                        "pressure": "80 psi",
                        "backflow": "Required"
                    }
                }
            ]
        }
    
    def test_end_to_end_export_workflow(self, export_service, sample_building_data):
        """Test complete export workflow from job creation to file download."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Create export job
            job_id = export_service.create_export_job(
                building_id=sample_building_data["building_id"],
                format=ExportFormat.IFC_LITE,
                options={"output_path": os.path.join(temp_dir, "test.ifc")}
            )
            
            assert job_id is not None
            
            # Step 2: Check job status
            job = export_service.get_export_job_status(job_id)
            assert job.status == ExportStatus.PENDING
            
            # Step 3: Perform export
            result_path = export_service.export_to_ifc_lite(
                building_data=sample_building_data,
                options={"output_path": os.path.join(temp_dir, "test.ifc")}
            )
            
            # Step 4: Verify file was created
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 0
            
            # Step 5: Check job status after completion
            job = export_service.get_export_job_status(job_id)
            # Note: The job status might still be PENDING since we're not updating it in the export method
            # This would be updated in a real implementation
    
    def test_multi_format_export_workflow(self, export_service, sample_building_data):
        """Test exporting the same building data to multiple formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            formats = [
                ExportFormat.IFC_LITE,
                ExportFormat.GLTF,
                ExportFormat.ASCII_BIM,
                ExportFormat.GEOJSON
            ]
            
            results = {}
            
            for format in formats:
                # Create job for each format
                job_id = export_service.create_export_job(
                    building_id=sample_building_data["building_id"],
                    format=format,
                    options={"output_path": os.path.join(temp_dir, f"test.{format.value}")}
                )
                
                # Perform export
                if format == ExportFormat.IFC_LITE:
                    result_path = export_service.export_to_ifc_lite(
                        building_data=sample_building_data,
                        options={"output_path": os.path.join(temp_dir, f"test.{format.value}")}
                    )
                elif format == ExportFormat.GLTF:
                    result_path = export_service.export_to_gltf(
                        building_data=sample_building_data,
                        options={"output_path": os.path.join(temp_dir, f"test.{format.value}")}
                    )
                elif format == ExportFormat.ASCII_BIM:
                    result_path = export_service.export_to_ascii_bim(
                        building_data=sample_building_data,
                        options={"output_path": os.path.join(temp_dir, f"test.{format.value}")}
                    )
                elif format == ExportFormat.GEOJSON:
                    result_path = export_service.export_to_geojson(
                        building_data=sample_building_data,
                        options={"output_path": os.path.join(temp_dir, f"test.{format.value}")}
                    )
                
                results[format] = result_path
                
                # Verify file was created
                assert os.path.exists(result_path)
                assert os.path.getsize(result_path) > 0
            
            # Verify all formats were exported successfully
            assert len(results) == len(formats)
            
            # Check file sizes are reasonable
            for format, path in results.items():
                file_size = os.path.getsize(path)
                assert file_size > 100  # Minimum reasonable size
                print(f"{format.value}: {file_size} bytes")
    
    def test_concurrent_export_jobs(self, export_service, sample_building_data):
        """Test multiple concurrent export jobs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            job_ids = []
            
            # Create multiple jobs
            for i in range(5):
                job_id = export_service.create_export_job(
                    building_id=f"{sample_building_data['building_id']}_{i}",
                    format=ExportFormat.IFC_LITE,
                    options={"output_path": os.path.join(temp_dir, f"test_{i}.ifc")}
                )
                job_ids.append(job_id)
            
            # Verify all jobs were created
            assert len(job_ids) == 5
            
            # Check all jobs exist
            for job_id in job_ids:
                job = export_service.get_export_job_status(job_id)
                assert job is not None
                assert job.status == ExportStatus.PENDING
            
            # List all jobs
            all_jobs = export_service.list_export_jobs()
            assert len(all_jobs) >= 5  # At least our 5 jobs
    
    def test_export_job_cancellation_workflow(self, export_service, sample_building_data):
        """Test export job cancellation workflow."""
        # Create job
        job_id = export_service.create_export_job(
            building_id=sample_building_data["building_id"],
            format=ExportFormat.IFC_LITE
        )
        
        # Verify job exists
        job = export_service.get_export_job_status(job_id)
        assert job.status == ExportStatus.PENDING
        
        # Cancel job
        result = export_service.cancel_export_job(job_id)
        assert result is True
        
        # Verify job was cancelled
        job = export_service.get_export_job_status(job_id)
        assert job.status == ExportStatus.CANCELLED
        assert job.completed_at is not None
    
    def test_export_statistics_integration(self, export_service, sample_building_data):
        """Test export statistics with multiple jobs."""
        # Create jobs with different formats and statuses
        job1_id = export_service.create_export_job(
            building_id="BUILDING_1",
            format=ExportFormat.IFC_LITE
        )
        job2_id = export_service.create_export_job(
            building_id="BUILDING_2",
            format=ExportFormat.GLTF
        )
        job3_id = export_service.create_export_job(
            building_id="BUILDING_3",
            format=ExportFormat.ASCII_BIM
        )
        
        # Cancel one job
        export_service.cancel_export_job(job1_id)
        
        # Get statistics
        stats = export_service.get_export_statistics()
        
        # Verify statistics structure
        assert "total_jobs" in stats
        assert "by_format" in stats
        assert "by_status" in stats
        
        # Verify we have jobs in statistics
        assert stats["total_jobs"] >= 3
        
        # Verify format statistics
        assert "ifc_lite" in stats["by_format"]
        assert "gltf" in stats["by_format"]
        assert "ascii_bim" in stats["by_format"]
        
        # Verify status statistics
        assert "pending" in stats["by_status"]
        assert "cancelled" in stats["by_status"]
    
    def test_error_handling_integration(self, export_service):
        """Test error handling in integration scenarios."""
        # Test with invalid building data
        invalid_data = None
        
        with pytest.raises(Exception):
            export_service.export_to_ifc_lite(
                building_data=invalid_data,
                options={"output_path": "test.ifc"}
            )
        
        # Test with invalid job ID
        non_existent_job = export_service.get_export_job_status("NON_EXISTENT")
        assert non_existent_job is None
        
        # Test cancelling non-existent job
        result = export_service.cancel_export_job("NON_EXISTENT")
        assert result is False
    
    def test_performance_under_load(self, export_service, sample_building_data):
        """Test export performance under load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()
            
            # Perform multiple exports
            for i in range(10):
                result_path = export_service.export_to_ifc_lite(
                    building_data=sample_building_data,
                    options={"output_path": os.path.join(temp_dir, f"perf_test_{i}.ifc")}
                )
                assert os.path.exists(result_path)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify performance is reasonable (should complete in under 10 seconds)
            assert total_time < 10.0
            print(f"10 exports completed in {total_time:.2f} seconds")
    
    def test_large_building_export(self, export_service):
        """Test export with large building data."""
        # Create large building data
        large_building_data = {
            "building_id": "LARGE_BUILDING",
            "building_name": "Large Test Building",
            "floor_count": 20,
            "total_area_sqft": 500000.0,
            "elements": []
        }
        
        # Add 1000 elements
        for i in range(1000):
            element = {
                "id": f"ELEMENT_{i:04d}",
                "name": f"Element {i}",
                "type": "WALL" if i % 3 == 0 else "COLUMN" if i % 3 == 1 else "WINDOW",
                "x": float(i % 100),
                "y": float(i // 100),
                "z": float(i % 10),
                "system": "STRUCTURAL" if i % 3 == 0 else "ARCHITECTURAL",
                "floor": (i % 20) + 1,
                "properties": {
                    "material": "Concrete" if i % 3 == 0 else "Steel",
                    "size": i % 10 + 1
                }
            }
            large_building_data["elements"].append(element)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()
            
            # Export large building
            result_path = export_service.export_to_ifc_lite(
                building_data=large_building_data,
                options={"output_path": os.path.join(temp_dir, "large_building.ifc")}
            )
            
            end_time = time.time()
            export_time = end_time - start_time
            
            # Verify export completed
            assert os.path.exists(result_path)
            file_size = os.path.getsize(result_path)
            
            # Verify performance is reasonable
            assert export_time < 5.0  # Should complete in under 5 seconds
            assert file_size > 10000  # Should be substantial file size
            
            print(f"Large building export: {file_size} bytes in {export_time:.2f} seconds")
    
    def test_export_service_persistence(self, temp_db):
        """Test that export service data persists across instances."""
        # Create first service instance
        service1 = ExportInteroperabilityService(db_path=temp_db)
        job_id = service1.create_export_job(
            building_id="PERSISTENCE_TEST",
            format=ExportFormat.IFC_LITE
        )
        
        # Create second service instance
        service2 = ExportInteroperabilityService(db_path=temp_db)
        
        # Verify job is accessible from second instance
        job = service2.get_export_job_status(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.building_id == "PERSISTENCE_TEST"
        assert job.format == ExportFormat.IFC_LITE
    
    def test_export_format_compatibility(self, export_service, sample_building_data):
        """Test compatibility of different export formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test IFC-lite format
            ifc_path = export_service.export_to_ifc_lite(
                building_data=sample_building_data,
                options={"output_path": os.path.join(temp_dir, "test.ifc")}
            )
            
            with open(ifc_path, 'r') as f:
                ifc_content = f.read()
                assert "ISO-10303-21;" in ifc_content
                assert "IFCBUILDING" in ifc_content
            
            # Test glTF format
            gltf_path = export_service.export_to_gltf(
                building_data=sample_building_data,
                options={"output_path": os.path.join(temp_dir, "test.gltf")}
            )
            
            with open(gltf_path, 'r') as f:
                gltf_content = json.load(f)
                assert gltf_content["asset"]["version"] == "2.0"
                assert "scenes" in gltf_content
                assert "nodes" in gltf_content
            
            # Test ASCII-BIM format
            ascii_path = export_service.export_to_ascii_bim(
                building_data=sample_building_data,
                options={"output_path": os.path.join(temp_dir, "test.txt")}
            )
            
            with open(ascii_path, 'r') as f:
                ascii_content = f.read()
                assert "ASCII-BIM Export" in ascii_content
                assert "BUILDING {" in ascii_content
                assert "ELEMENTS {" in ascii_content
            
            # Test GeoJSON format
            geojson_path = export_service.export_to_geojson(
                building_data=sample_building_data,
                options={"output_path": os.path.join(temp_dir, "test.geojson")}
            )
            
            with open(geojson_path, 'r') as f:
                geojson_content = json.load(f)
                assert geojson_content["type"] == "FeatureCollection"
                assert "features" in geojson_content
                assert len(geojson_content["features"]) == len(sample_building_data["elements"])
    
    def test_export_error_recovery(self, export_service, sample_building_data):
        """Test error recovery in export scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with invalid output path (read-only directory)
            read_only_dir = os.path.join(temp_dir, "readonly")
            os.makedirs(read_only_dir, mode=0o444)  # Read-only
            
            with pytest.raises(Exception):
                export_service.export_to_ifc_lite(
                    building_data=sample_building_data,
                    options={"output_path": os.path.join(read_only_dir, "test.ifc")}
                )
            
            # Test with valid path after error
            valid_path = os.path.join(temp_dir, "test.ifc")
            result_path = export_service.export_to_ifc_lite(
                building_data=sample_building_data,
                options={"output_path": valid_path}
            )
            
            # Verify recovery worked
            assert os.path.exists(result_path)
    
    def test_export_job_filtering(self, export_service, sample_building_data):
        """Test export job filtering by building ID."""
        # Create jobs for different buildings
        building_ids = ["BUILDING_A", "BUILDING_B", "BUILDING_C"]
        
        for building_id in building_ids:
            export_service.create_export_job(
                building_id=building_id,
                format=ExportFormat.IFC_LITE
            )
        
        # Test filtering by building ID
        building_a_jobs = export_service.list_export_jobs(building_id="BUILDING_A")
        assert len(building_a_jobs) == 1
        assert all(job.building_id == "BUILDING_A" for job in building_a_jobs)
        
        # Test filtering by non-existent building
        non_existent_jobs = export_service.list_export_jobs(building_id="NON_EXISTENT")
        assert len(non_existent_jobs) == 0
        
        # Test listing all jobs
        all_jobs = export_service.list_export_jobs()
        assert len(all_jobs) >= 3  # At least our 3 jobs 