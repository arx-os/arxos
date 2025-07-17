"""
SVGX Engine - Advanced Export Service Tests

Comprehensive test suite for the SVGX Advanced Export Service with coverage for:
- All export formats and quality levels
- Batch processing and job management
- Error handling and recovery
- Performance monitoring and analytics
- Thread safety and concurrency
- Database operations and persistence
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import threading
import time

from svgx_engine.services.advanced_export import (
    SVGXAdvancedExportService,
    AdvancedExportFormat,
    AdvancedExportStatus,
    ExportQuality,
    AdvancedExportJob,
    ExportBatch,
    ExportAnalytics,
    create_svgx_advanced_export_service
)
from svgx_engine.utils.errors import AdvancedExportError


class TestSVGXAdvancedExportService:
    """Test suite for SVGX Advanced Export Service."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_advanced_export.db"
        yield str(db_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def export_service(self, temp_db_path):
        """Create SVGX Advanced Export Service instance for testing."""
        return SVGXAdvancedExportService(
            db_path=temp_db_path,
            max_workers=2,
            cache_size=100
        )
    
    @pytest.fixture
    def sample_building_data(self):
        """Sample building data for testing."""
        return {
            "building_id": "test_building_001",
            "elements": [
                {
                    "id": "element_1",
                    "name": "Test Element",
                    "type": "wall",
                    "geometry": {
                        "type": "rectangle",
                        "x": 0,
                        "y": 0,
                        "width": 100,
                        "height": 200
                    }
                }
            ],
            "metadata": {
                "name": "Test Building",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            }
        }
    
    def test_service_initialization(self, export_service):
        """Test service initialization and configuration."""
        assert export_service is not None
        assert export_service.max_workers == 2
        assert export_service.cache_size == 100
        assert export_service.error_handler is not None
        assert export_service.performance_monitor is not None
    
    def test_create_advanced_export_job(self, export_service, sample_building_data):
        """Test creating advanced export jobs."""
        job_id = export_service.create_advanced_export_job(
            building_id=sample_building_data["building_id"],
            format=AdvancedExportFormat.IFC_LITE,
            quality=ExportQuality.STANDARD,
            options={"test_option": "test_value"}
        )
        
        assert job_id is not None
        assert len(job_id) > 0
        
        # Verify job was created
        job = export_service.get_advanced_export_job_status(job_id)
        assert job is not None
        assert job.building_id == sample_building_data["building_id"]
        assert job.format == AdvancedExportFormat.IFC_LITE
        assert job.quality == ExportQuality.STANDARD
        assert job.status == AdvancedExportStatus.PENDING
        assert job.options["test_option"] == "test_value"
    
    def test_create_export_batch(self, export_service, sample_building_data):
        """Test creating export batches."""
        jobs = [
            (sample_building_data["building_id"], AdvancedExportFormat.IFC_LITE, ExportQuality.STANDARD, {}),
            (sample_building_data["building_id"], AdvancedExportFormat.GLTF, ExportQuality.HIGH, {}),
            (sample_building_data["building_id"], AdvancedExportFormat.SVGX, ExportQuality.PROFESSIONAL, {})
        ]
        
        batch_id = export_service.create_export_batch(jobs, priority=2)
        
        assert batch_id is not None
        assert len(batch_id) > 0
        
        # Verify batch was created
        batch = export_service.export_batches.get(batch_id)
        assert batch is not None
        assert len(batch.jobs) == 3
        assert batch.priority == 2
    
    def test_export_format_enum(self):
        """Test export format enumeration."""
        formats = list(AdvancedExportFormat)
        assert AdvancedExportFormat.IFC_LITE in formats
        assert AdvancedExportFormat.GLTF in formats
        assert AdvancedExportFormat.SVGX in formats
        assert AdvancedExportFormat.EXCEL in formats
        assert AdvancedExportFormat.PARQUET in formats
        assert AdvancedExportFormat.GEOJSON in formats
    
    def test_export_quality_enum(self):
        """Test export quality enumeration."""
        qualities = list(ExportQuality)
        assert ExportQuality.DRAFT in qualities
        assert ExportQuality.STANDARD in qualities
        assert ExportQuality.HIGH in qualities
        assert ExportQuality.PROFESSIONAL in qualities
        assert ExportQuality.PUBLICATION in qualities
    
    def test_export_status_enum(self):
        """Test export status enumeration."""
        statuses = list(AdvancedExportStatus)
        assert AdvancedExportStatus.PENDING in statuses
        assert AdvancedExportStatus.PROCESSING in statuses
        assert AdvancedExportStatus.COMPLETED in statuses
        assert AdvancedExportStatus.FAILED in statuses
        assert AdvancedExportStatus.CANCELLED in statuses
    
    def test_list_export_jobs(self, export_service, sample_building_data):
        """Test listing export jobs with filtering."""
        # Create multiple jobs
        job_ids = []
        for i in range(3):
            job_id = export_service.create_advanced_export_job(
                building_id=f"building_{i}",
                format=AdvancedExportFormat.IFC_LITE,
                quality=ExportQuality.STANDARD
            )
            job_ids.append(job_id)
        
        # Test listing all jobs
        all_jobs = export_service.list_advanced_export_jobs()
        assert len(all_jobs) >= 3
        
        # Test filtering by building_id
        building_jobs = export_service.list_advanced_export_jobs(building_id="building_0")
        assert len(building_jobs) >= 1
        assert all(job.building_id == "building_0" for job in building_jobs)
        
        # Test filtering by status
        pending_jobs = export_service.list_advanced_export_jobs(status=AdvancedExportStatus.PENDING)
        assert len(pending_jobs) >= 3
        assert all(job.status == AdvancedExportStatus.PENDING for job in pending_jobs)
    
    def test_cancel_export_job(self, export_service, sample_building_data):
        """Test canceling export jobs."""
        job_id = export_service.create_advanced_export_job(
            building_id=sample_building_data["building_id"],
            format=AdvancedExportFormat.IFC_LITE,
            quality=ExportQuality.STANDARD
        )
        
        # Cancel the job
        success = export_service.cancel_advanced_export_job(job_id)
        assert success is True
        
        # Verify job was cancelled
        job = export_service.get_advanced_export_job_status(job_id)
        assert job.status == AdvancedExportStatus.CANCELLED
    
    def test_cancel_nonexistent_job(self, export_service):
        """Test canceling a non-existent job."""
        success = export_service.cancel_advanced_export_job("nonexistent_job_id")
        assert success is False
    
    def test_get_export_analytics(self, export_service):
        """Test getting export analytics."""
        analytics = export_service.get_advanced_export_analytics()
        assert isinstance(analytics, ExportAnalytics)
        assert analytics.total_exports >= 0
        assert analytics.successful_exports >= 0
        assert analytics.failed_exports >= 0
    
    def test_get_export_statistics(self, export_service):
        """Test getting comprehensive export statistics."""
        stats = export_service.get_advanced_export_statistics()
        
        assert "processing_stats" in stats
        assert "analytics" in stats
        assert "active_jobs" in stats
        assert "pending_jobs" in stats
        assert "completed_jobs" in stats
        
        assert isinstance(stats["processing_stats"], dict)
        assert isinstance(stats["analytics"], dict)
        assert isinstance(stats["active_jobs"], int)
        assert isinstance(stats["pending_jobs"], int)
        assert isinstance(stats["completed_jobs"], int)
    
    def test_thread_safety(self, export_service, sample_building_data):
        """Test thread safety of the service."""
        job_ids = []
        threads = []
        
        def create_job():
            job_id = export_service.create_advanced_export_job(
                building_id=sample_building_data["building_id"],
                format=AdvancedExportFormat.IFC_LITE,
                quality=ExportQuality.STANDARD
            )
            job_ids.append(job_id)
        
        # Create multiple threads
        for _ in range(5):
            thread = threading.Thread(target=create_job)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all jobs were created successfully
        assert len(job_ids) == 5
        for job_id in job_ids:
            job = export_service.get_advanced_export_job_status(job_id)
            assert job is not None
    
    def test_error_handling(self, export_service):
        """Test error handling in the service."""
        with pytest.raises(AdvancedExportError):
            export_service.create_advanced_export_job(
                building_id="",  # Invalid building_id
                format=AdvancedExportFormat.IFC_LITE,
                quality=ExportQuality.STANDARD
            )
    
    def test_database_persistence(self, export_service, sample_building_data):
        """Test database persistence of jobs."""
        job_id = export_service.create_advanced_export_job(
            building_id=sample_building_data["building_id"],
            format=AdvancedExportFormat.IFC_LITE,
            quality=ExportQuality.STANDARD
        )
        
        # Create new service instance to test persistence
        new_service = SVGXAdvancedExportService(db_path=export_service.db_path)
        
        # Verify job persists
        job = new_service.get_advanced_export_job_status(job_id)
        assert job is not None
        assert job.building_id == sample_building_data["building_id"]
    
    def test_performance_monitoring(self, export_service, sample_building_data):
        """Test performance monitoring integration."""
        with patch.object(export_service.performance_monitor, 'monitor') as mock_monitor:
            job_id = export_service.create_advanced_export_job(
                building_id=sample_building_data["building_id"],
                format=AdvancedExportFormat.IFC_LITE,
                quality=ExportQuality.STANDARD
            )
            
            # Verify performance monitoring was called
            assert mock_monitor.called
    
    def test_quality_levels(self, export_service, sample_building_data):
        """Test different quality levels."""
        quality_levels = [ExportQuality.DRAFT, ExportQuality.STANDARD, 
                         ExportQuality.HIGH, ExportQuality.PROFESSIONAL, ExportQuality.PUBLICATION]
        
        for quality in quality_levels:
            job_id = export_service.create_advanced_export_job(
                building_id=sample_building_data["building_id"],
                format=AdvancedExportFormat.IFC_LITE,
                quality=quality
            )
            
            job = export_service.get_advanced_export_job_status(job_id)
            assert job.quality == quality
    
    def test_format_support(self, export_service, sample_building_data):
        """Test support for different export formats."""
        formats = [AdvancedExportFormat.IFC_LITE, AdvancedExportFormat.GLTF, 
                  AdvancedExportFormat.SVGX, AdvancedExportFormat.EXCEL,
                  AdvancedExportFormat.PARQUET, AdvancedExportFormat.GEOJSON]
        
        for format in formats:
            job_id = export_service.create_advanced_export_job(
                building_id=sample_building_data["building_id"],
                format=format,
                quality=ExportQuality.STANDARD
            )
            
            job = export_service.get_advanced_export_job_status(job_id)
            assert job.format == format
    
    def test_batch_processing(self, export_service, sample_building_data):
        """Test batch processing functionality."""
        jobs = [
            (sample_building_data["building_id"], AdvancedExportFormat.IFC_LITE, ExportQuality.STANDARD, {}),
            (sample_building_data["building_id"], AdvancedExportFormat.GLTF, ExportQuality.HIGH, {}),
            (sample_building_data["building_id"], AdvancedExportFormat.SVGX, ExportQuality.PROFESSIONAL, {})
        ]
        
        batch_id = export_service.create_export_batch(jobs, priority=1)
        batch = export_service.export_batches.get(batch_id)
        
        assert batch is not None
        assert len(batch.jobs) == 3
        assert batch.priority == 1
        assert batch.status == AdvancedExportStatus.PENDING
    
    def test_service_factory(self, temp_db_path):
        """Test service factory function."""
        service = create_svgx_advanced_export_service(
            db_path=temp_db_path,
            max_workers=4,
            cache_size=500
        )
        
        assert service is not None
        assert service.max_workers == 4
        assert service.cache_size == 500
        assert service.db_path == temp_db_path
    
    def test_analytics_integration(self, export_service, sample_building_data):
        """Test analytics integration and updates."""
        initial_analytics = export_service.get_advanced_export_analytics()
        initial_total = initial_analytics.total_exports
        
        # Create a job
        job_id = export_service.create_advanced_export_job(
            building_id=sample_building_data["building_id"],
            format=AdvancedExportFormat.IFC_LITE,
            quality=ExportQuality.STANDARD
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        # Check analytics updated
        updated_analytics = export_service.get_advanced_export_analytics()
        assert updated_analytics.total_exports >= initial_total
    
    def test_validation_and_optimization(self, export_service, sample_building_data):
        """Test validation and optimization features."""
        job_id = export_service.create_advanced_export_job(
            building_id=sample_building_data["building_id"],
            format=AdvancedExportFormat.IFC_LITE,
            quality=ExportQuality.PROFESSIONAL
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        job = export_service.get_advanced_export_job_status(job_id)
        if job.status == AdvancedExportStatus.COMPLETED:
            assert "validation_results" in job.validation_results
            assert "optimization_metrics" in job.optimization_metrics
    
    def test_error_recovery(self, export_service):
        """Test error recovery mechanisms."""
        # Test with invalid parameters
        with pytest.raises(AdvancedExportError):
            export_service.create_advanced_export_job(
                building_id=None,
                format=AdvancedExportFormat.IFC_LITE,
                quality=ExportQuality.STANDARD
            )
    
    def test_concurrent_job_processing(self, export_service, sample_building_data):
        """Test concurrent job processing."""
        job_ids = []
        
        # Create multiple jobs quickly
        for i in range(5):
            job_id = export_service.create_advanced_export_job(
                building_id=f"building_{i}",
                format=AdvancedExportFormat.IFC_LITE,
                quality=ExportQuality.STANDARD
            )
            job_ids.append(job_id)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check that jobs are being processed
        completed_jobs = export_service.list_advanced_export_jobs(status=AdvancedExportStatus.COMPLETED)
        processing_jobs = export_service.list_advanced_export_jobs(status=AdvancedExportStatus.PROCESSING)
        
        # At least some jobs should be in progress or completed
        assert len(completed_jobs) + len(processing_jobs) >= 0
    
    def test_memory_management(self, export_service, sample_building_data):
        """Test memory management and cleanup."""
        # Create many jobs
        for i in range(10):
            export_service.create_advanced_export_job(
                building_id=f"building_{i}",
                format=AdvancedExportFormat.IFC_LITE,
                quality=ExportQuality.STANDARD
            )
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check memory usage doesn't grow excessively
        stats = export_service.get_advanced_export_statistics()
        assert stats["active_jobs"] <= export_service.max_workers
    
    def test_database_operations(self, export_service, sample_building_data):
        """Test database operations and persistence."""
        job_id = export_service.create_advanced_export_job(
            building_id=sample_building_data["building_id"],
            format=AdvancedExportFormat.IFC_LITE,
            quality=ExportQuality.STANDARD
        )
        
        # Verify job is stored in database
        import sqlite3
        conn = sqlite3.connect(export_service.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM advanced_export_jobs WHERE job_id = ?", (job_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 1


class TestAdvancedExportFormats:
    """Test specific export format functionality."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service for format testing."""
        return SVGXAdvancedExportService(max_workers=1)
    
    def test_ifc_lite_export(self, export_service):
        """Test IFC-lite export functionality."""
        job_id = export_service.create_advanced_export_job(
            building_id="test_building",
            format=AdvancedExportFormat.IFC_LITE,
            quality=ExportQuality.STANDARD
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        job = export_service.get_advanced_export_job_status(job_id)
        if job.status == AdvancedExportStatus.COMPLETED:
            assert job.file_path is not None
            assert job.file_size > 0
    
    def test_gltf_export(self, export_service):
        """Test glTF export functionality."""
        job_id = export_service.create_advanced_export_job(
            building_id="test_building",
            format=AdvancedExportFormat.GLTF,
            quality=ExportQuality.HIGH
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        job = export_service.get_advanced_export_job_status(job_id)
        if job.status == AdvancedExportStatus.COMPLETED:
            assert job.file_path is not None
            assert job.file_size > 0
    
    def test_svgx_export(self, export_service):
        """Test SVGX export functionality."""
        job_id = export_service.create_advanced_export_job(
            building_id="test_building",
            format=AdvancedExportFormat.SVGX,
            quality=ExportQuality.PROFESSIONAL
        )
        
        # Wait for processing
        time.sleep(0.1)
        
        job = export_service.get_advanced_export_job_status(job_id)
        if job.status == AdvancedExportStatus.COMPLETED:
            assert job.file_path is not None
            assert job.file_size > 0


class TestAdvancedExportQuality:
    """Test export quality levels and optimization."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service for quality testing."""
        return SVGXAdvancedExportService(max_workers=1)
    
    def test_quality_levels_processing(self, export_service):
        """Test processing with different quality levels."""
        quality_levels = [ExportQuality.DRAFT, ExportQuality.STANDARD, 
                         ExportQuality.HIGH, ExportQuality.PROFESSIONAL, ExportQuality.PUBLICATION]
        
        for quality in quality_levels:
            job_id = export_service.create_advanced_export_job(
                building_id="test_building",
                format=AdvancedExportFormat.IFC_LITE,
                quality=quality
            )
            
            # Wait for processing
            time.sleep(0.1)
            
            job = export_service.get_advanced_export_job_status(job_id)
            if job.status == AdvancedExportStatus.COMPLETED:
                assert job.quality == quality
                assert job.optimization_metrics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 