"""
Test suite for SVGX Engine Persistence Export Service.

Tests cover:
- Export operations for all formats
- Job management and monitoring
- Database operations
- Error handling and recovery
- Performance monitoring
- SVGX-specific optimizations
"""

import pytest
import tempfile
import os
import json
import sqlite3
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from svgx_engine.services.persistence_export import (
    PersistenceExportService,
    ExportFormat,
    DatabaseType,
    JobStatus,
    ExportOptions,
    DatabaseConfig,
    ExportJob,
    SVGXSerializer,
    SVGXExporter,
    create_persistence_export_service
)
from svgx_engine.models.svgx import SVGXDocument, SVGXElement
from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace
from svgx_engine.utils.errors import (
    PersistenceExportError, ExportError, ValidationError,
    DatabaseError, JobError
)


class TestSVGXSerializer:
    """Test SVGX Serializer functionality."""

    def test_to_dict_with_svgx_document(self):
        """Test serialization of SVGX document."""
        # Create test SVGX document
        element = SVGXElement(
            id="test-element",
            tag="rect",
            properties={"width": 100, "height": 50},
            metadata={"floor": "1", "room": "A101"}
        )

        document = SVGXDocument(
            id="test-document",
            elements=[element],
            metadata={"project": "test", "version": "1.0"}
        )

        # Serialize
        result = SVGXSerializer.to_dict(document)

        # Verify structure
        assert result['id'] == "test-document"
        assert result['metadata']['project'] == "test"
        assert len(result['elements']) == 1
        assert result['elements'][0]['id'] == "test-element"
        assert result['elements'][0]['properties']['width'] == 100

    def test_to_json_pretty_print(self):
        """Test JSON serialization with pretty print."""
        element = SVGXElement(
            id="test-element",
            tag="circle",
            properties={"radius": 25}
        )

        document = SVGXDocument(
            id="test-document",
            elements=[element]
        )

        result = SVGXSerializer.to_json(document, pretty=True)

        # Verify it's valid JSON'
        parsed = json.loads(result)
        assert parsed['id'] == "test-document"
        assert len(parsed['elements']) == 1

    def test_to_json_compact(self):
        """Test JSON serialization without pretty print."""
        element = SVGXElement(
            id="test-element",
            tag="line",
            properties={"x1": 0, "y1": 0, "x2": 100, "y2": 100}
        )

        document = SVGXDocument(
            id="test-document",
            elements=[element]
        )

        result = SVGXSerializer.to_json(document, pretty=False)

        # Verify it's compact JSON'
        assert '\n' not in result
        parsed = json.loads(result)
        assert parsed['id'] == "test-document"

    def test_from_dict_reconstruction(self):
        """Test deserialization from dictionary."""
        original_element = SVGXElement(
            id="test-element",
            tag="rect",
            properties={"width": 100, "height": 50},
            metadata={"floor": "1"}
        )

        original_document = SVGXDocument(
            id="test-document",
            elements=[original_element],
            metadata={"project": "test"}
        )

        # Serialize and deserialize
        data = SVGXSerializer.to_dict(original_document)
        reconstructed = SVGXSerializer.from_dict(data, SVGXDocument)

        # Verify reconstruction
        assert reconstructed.id == original_document.id
        assert reconstructed.metadata['project'] == original_document.metadata['project']
        assert len(reconstructed.elements) == 1
        assert reconstructed.elements[0].id == original_element.id
        assert reconstructed.elements[0].properties['width'] == original_element.properties['width']


class TestSVGXExporter:
    """Test SVGX Exporter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = SVGXExporter()

        # Create test SVGX document
        elements = [
            SVGXElement(
                id="rect-1",
                tag="rect",
                properties={"width": 100, "height": 50, "x": 0, "y": 0},
                metadata={"floor": "1", "room": "A101"}
            ),
            SVGXElement(
                id="circle-1",
                tag="circle",
                properties={"radius": 25, "cx": 50, "cy": 25},
                metadata={"floor": "1", "room": "A102"}
            )
        ]

        self.test_document = SVGXDocument(
            id="test-document",
            elements=elements,
            metadata={"project": "test", "version": "1.0"}
        )

    def test_export_to_json(self):
        """Test JSON export."""
        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True,
            pretty_print=True,
            svgx_optimization_enabled=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)

        # Verify JSON structure
        parsed = json.loads(result)
        assert parsed['id'] == "test-document"
        assert parsed['metadata']['project'] == "test"
        assert len(parsed['elements']) == 2
        assert parsed['elements'][0]['id'] == "rect-1"
        assert parsed['elements'][1]['id'] == "circle-1"

    def test_export_to_json_without_metadata(self):
        """Test JSON export without metadata."""
        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=False,
            include_geometry=True,
            include_properties=True,
            include_relationships=True,
            pretty_print=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)
        parsed = json.loads(result)

        # Verify metadata is excluded
        assert 'metadata' not in parsed

    def test_export_to_csv(self):
        """Test CSV export."""
        options = ExportOptions(
            format=ExportFormat.CSV,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)

        # Verify CSV structure
        lines = result.strip().split('\n')
        assert len(lines) == 3  # Header + 2 data rows

        # Check header
        header = lines[0]
        assert 'id' in header
        assert 'type' in header
        assert 'properties' in header
        assert 'metadata' in header

    def test_export_to_svgx(self):
        """Test SVGX format export."""
        options = ExportOptions(
            format=ExportFormat.SVGX,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)

        # Verify SVGX structure
        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert '<svgx:document' in result
        assert 'id="test-document"' in result
        assert '<svgx:element id="rect-1"' in result
        assert '<svgx:element id="circle-1"' in result

    def test_export_to_ifc(self):
        """Test IFC format export."""
        options = ExportOptions(
            format=ExportFormat.IFC,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)

        # Verify IFC structure
        assert 'ISO-10303-21;' in result
        assert 'IFCPROJECT' in result
        assert 'SVGX Project' in result

    def test_export_to_gbxml(self):
        """Test gbXML format export."""
        options = ExportOptions(
            format=ExportFormat.GBXML,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)

        # Verify gbXML structure
        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert '<gbXML' in result
        assert 'SVGX_Campus' in result
        assert 'SVGX_Building' in result

    def test_export_to_pickle(self):
        """Test pickle format export."""
        options = ExportOptions(
            format=ExportFormat.PICKLE,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)

        # Verify pickle result
        assert isinstance(result, bytes)

        # Test deserialization
        reconstructed = SVGXSerializer.from_pickle(result)
        assert reconstructed.id == self.test_document.id
        assert len(reconstructed.elements) == 2

    def test_export_unsupported_format(self):
        """Test export with unsupported format."""
        options = ExportOptions(
            format=ExportFormat.SQLITE,  # Not implemented
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True
        )

        with pytest.raises(ExportError, match="Unsupported export format"):
            self.exporter.export_svgx_document(self.test_document, options)

    def test_export_with_svgx_optimizations(self):
        """Test export with SVGX optimizations enabled."""
        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True,
            svgx_optimization_enabled=True
        )

        result = self.exporter.export_svgx_document(self.test_document, options)
        parsed = json.loads(result)

        # Verify optimizations applied
        assert 'id' in parsed
        assert 'elements' in parsed
        # Should not have empty fields due to optimization


class TestPersistenceExportService:
    """Test Persistence Export Service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PersistenceExportService({
            'enable_persistence': True,
            'enable_job_monitoring': True,
            'enable_svgx_optimization': True,
            'max_job_timeout': 60,
            'max_concurrent_jobs': 2,
            'job_queue_size': 10,
            'database_type': DatabaseType.SQLITE,
            'database_connection': ':memory:'
        })

        # Create test SVGX document
        elements = [
            SVGXElement(
                id="rect-1",
                tag="rect",
                properties={"width": 100, "height": 50, "x": 0, "y": 0},
                metadata={"floor": "1", "room": "A101"}
            ),
            SVGXElement(
                id="circle-1",
                tag="circle",
                properties={"radius": 25, "cx": 50, "cy": 25},
                metadata={"floor": "1", "room": "A102"}
            )
        ]

        self.test_document = SVGXDocument(
            id="test-document",
            elements=elements,
            metadata={"project": "test", "version": "1.0"}
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        self.service.cleanup()

    def test_export_svgx_document_to_file(self):
        """Test exporting SVGX document to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name

        try:
            options = ExportOptions(
                format=ExportFormat.JSON,
                include_metadata=True,
                include_geometry=True,
                include_properties=True,
                include_relationships=True,
                pretty_print=True
            )

            self.service.export_svgx_document(self.test_document, file_path, options)

            # Verify file was created and contains expected content
            assert os.path.exists(file_path)

            with open(file_path, 'r') as f:
                content = f.read()
                parsed = json.loads(content)
                assert parsed['id'] == "test-document"
                assert len(parsed['elements']) == 2

        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_create_export_job(self):
        """Test creating export job."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name

        try:
            options = ExportOptions(
                format=ExportFormat.JSON,
                include_metadata=True,
                include_geometry=True,
                include_properties=True,
                include_relationships=True,
                pretty_print=True
            )

            job_id = self.service.create_export_job(self.test_document, file_path, options)

            # Verify job was created
            assert job_id is not None
            assert len(job_id) > 0

            # Check job status
            job = self.service.get_job_status(job_id)
            assert job is not None
            assert job.job_id == job_id
            assert job.status in [JobStatus.PENDING, JobStatus.IN_PROGRESS]
            assert job.total_items == 2

        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_job_monitoring(self):
        """Test job monitoring functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name

        try:
            options = ExportOptions(
                format=ExportFormat.JSON,
                include_metadata=True,
                include_geometry=True,
                include_properties=True,
                include_relationships=True,
                pretty_print=True
            )

            job_id = self.service.create_export_job(self.test_document, file_path, options)

            # Wait for job to complete
            import time
            max_wait = 10  # 10 seconds max
            wait_time = 0

            while wait_time < max_wait:
                job = self.service.get_job_status(job_id)
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    break
                time.sleep(0.1)
                wait_time += 0.1

            # Verify job completed
            job = self.service.get_job_status(job_id)
            assert job.status == JobStatus.COMPLETED
            assert job.progress == 100.0
            assert job.processed_items == job.total_items
            assert job.result_path == file_path

        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_cancel_job(self):
        """Test job cancellation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name

        try:
            options = ExportOptions(
                format=ExportFormat.JSON,
                include_metadata=True,
                include_geometry=True,
                include_properties=True,
                include_relationships=True,
                pretty_print=True
            )

            job_id = self.service.create_export_job(self.test_document, file_path, options)

            # Cancel job immediately
            cancelled = self.service.cancel_job(job_id)
            assert cancelled is True

            # Verify job was cancelled
            job = self.service.get_job_status(job_id)
            assert job.status == JobStatus.CANCELLED

        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_database_operations(self):
        """Test database operations."""
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=':memory:',
            table_name='test_svgx_models',
            create_tables=True
        )

        # Save document to database
        self.service.save_svgx_document_to_database(
            self.test_document, "test-doc-1", db_config
        )

        # Load document from database import database
        loaded_document = self.service.load_svgx_document_from_database(
            "test-doc-1", db_config
        )

        # Verify document was loaded correctly
        assert loaded_document.id == self.test_document.id
        assert loaded_document.metadata['project'] == self.test_document.metadata['project']
        assert len(loaded_document.elements) == 2

        # List documents
        documents = self.service.list_database_documents(db_config)
        assert "test-doc-1" in documents

        # Delete document
        self.service.delete_database_document("test-doc-1", db_config)

        # Verify document was deleted
        documents = self.service.list_database_documents(db_config)
        assert "test-doc-1" not in documents

    def test_database_error_handling(self):
        """Test database error handling."""
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string='invalid_path.db',
            table_name='test_svgx_models',
            create_tables=True
        )

        # Test save with invalid connection
        with pytest.raises(PersistenceExportError):
            self.service.save_svgx_document_to_database(
                self.test_document, "test-doc-1", db_config
            )

    def test_get_statistics(self):
        """Test service statistics."""
        stats = self.service.get_statistics()

        # Verify statistics structure
        assert 'total_jobs' in stats
        assert 'pending_jobs' in stats
        assert 'in_progress_jobs' in stats
        assert 'completed_jobs' in stats
        assert 'failed_jobs' in stats
        assert 'cancelled_jobs' in stats
        assert 'performance_metrics' in stats

        # Verify initial values
        assert stats['total_jobs'] == 0
        assert stats['pending_jobs'] == 0
        assert stats['in_progress_jobs'] == 0

    def test_export_error_handling(self):
        """Test export error handling."""
        # Test with invalid file path
        invalid_path = "/invalid/path/test.json"

        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=True,
            include_geometry=True,
            include_properties=True,
            include_relationships=True,
            pretty_print=True
        )

        with pytest.raises(PersistenceExportError):
            self.service.export_svgx_document(self.test_document, invalid_path, options)

    def test_service_cleanup(self):
        """Test service cleanup."""
        # Create a job to test cleanup
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name

        try:
            options = ExportOptions(
                format=ExportFormat.JSON,
                include_metadata=True,
                include_geometry=True,
                include_properties=True,
                include_relationships=True,
                pretty_print=True
            )

            job_id = self.service.create_export_job(self.test_document, file_path, options)

            # Verify job exists
            job = self.service.get_job_status(job_id)
            assert job is not None

            # Cleanup service
            self.service.cleanup()

            # Verify job queue is cleared
            job = self.service.get_job_status(job_id)
            assert job is None

        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)


class TestPersistenceExportServiceIntegration:
    """Integration tests for Persistence Export Service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = create_persistence_export_service({
            'enable_persistence': True,
            'enable_job_monitoring': True,
            'enable_svgx_optimization': True,
            'max_job_timeout': 60,
            'max_concurrent_jobs': 3,
            'job_queue_size': 10,
            'database_type': DatabaseType.SQLITE,
            'database_connection': ':memory:'
        })

        # Create complex test document
        elements = []
        for i in range(10):
            element = SVGXElement(
                id=f"element-{i}",
                tag="rect" if i % 2 == 0 else "circle",
                properties={
                    "width": 100 + i,
                    "height": 50 + i,
                    "x": i * 10,
                    "y": i * 5
                },
                metadata={
                    "floor": str(i // 3 + 1),
                    "room": f"A{i:03d}",
                    "system": "electrical" if i % 3 == 0 else "hvac" if i % 3 == 1 else "plumbing"
                }
            )
            elements.append(element)

        self.test_document = SVGXDocument(
            id="integration-test-document",
            elements=elements,
            metadata={
                "project": "integration-test",
                "version": "1.0",
                "created_by": "test-user",
                "description": "Integration test document"
            }
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        self.service.cleanup()

    def test_full_export_workflow(self):
        """Test complete export workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name

        try:
            # Test multiple export formats
            formats = [ExportFormat.JSON, ExportFormat.XML, ExportFormat.CSV, ExportFormat.SVGX]

            for format_type in formats:
                options = ExportOptions(
                    format=format_type,
                    include_metadata=True,
                    include_geometry=True,
                    include_properties=True,
                    include_relationships=True,
                    pretty_print=True,
                    svgx_optimization_enabled=True
                )

                # Export document
                self.service.export_svgx_document(self.test_document, file_path, options)

                # Verify file was created
                assert os.path.exists(file_path)
                assert os.path.getsize(file_path) > 0

                # Verify content based on format
                with open(file_path, 'r') as f:
                    content = f.read()

                    if format_type == ExportFormat.JSON:
                        parsed = json.loads(content)
                        assert parsed['id'] == "integration-test-document"
                        assert len(parsed['elements']) == 10
                    elif format_type == ExportFormat.XML:
                        assert '<?xml version="1.0"' in content
                        assert '<SVGXDocument' in content
                    elif format_type == ExportFormat.CSV:
                        lines = content.strip().split('\n')
                        assert len(lines) == 11  # Header + 10 data rows
                    elif format_type == ExportFormat.SVGX:
                        assert '<?xml version="1.0"' in content
                        assert '<svgx:document' in content
                        assert 'id="integration-test-document"' in content

        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_concurrent_job_processing(self):
        """Test concurrent job processing."""
        job_ids = []
        file_paths = []

        try:
            # Create multiple export jobs
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.json', delete=False) as f:
                    file_path = f.name
                    file_paths.append(file_path)

                options = ExportOptions(
                    format=ExportFormat.JSON,
                    include_metadata=True,
                    include_geometry=True,
                    include_properties=True,
                    include_relationships=True,
                    pretty_print=True
                )

                job_id = self.service.create_export_job(self.test_document, file_path, options)
                job_ids.append(job_id)

            # Wait for all jobs to complete
            import time
            max_wait = 30  # 30 seconds max
            wait_time = 0

            while wait_time < max_wait:
                completed_jobs = 0
                for job_id in job_ids:
                    job = self.service.get_job_status(job_id)
                    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                        completed_jobs += 1

                if completed_jobs == len(job_ids):
                    break

                time.sleep(0.1)
                wait_time += 0.1

            # Verify all jobs completed successfully
            for job_id in job_ids:
                job = self.service.get_job_status(job_id)
                assert job.status == JobStatus.COMPLETED
                assert job.progress == 100.0

            # Verify all files were created
            for file_path in file_paths:
                assert os.path.exists(file_path)
                assert os.path.getsize(file_path) > 0

        finally:
            # Clean up files
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    def test_database_persistence_workflow(self):
        """Test complete database persistence workflow."""
        db_config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            connection_string=':memory:',
            table_name='integration_test_models',
            create_tables=True
        )

        # Save multiple documents
        for i in range(3):
            document_id = f"test-doc-{i}"
            self.service.save_svgx_document_to_database(
                self.test_document, document_id, db_config
            )

        # List documents
        documents = self.service.list_database_documents(db_config)
        assert len(documents) == 3
        assert "test-doc-0" in documents
        assert "test-doc-1" in documents
        assert "test-doc-2" in documents

        # Load and verify documents
        for i in range(3):
            document_id = f"test-doc-{i}"
            loaded_document = self.service.load_svgx_document_from_database(
                document_id, db_config
            )

            assert loaded_document.id == self.test_document.id
            assert loaded_document.metadata['project'] == self.test_document.metadata['project']
            assert len(loaded_document.elements) == 10

        # Delete documents
        for i in range(3):
            document_id = f"test-doc-{i}"
            self.service.delete_database_document(document_id, db_config)

        # Verify documents were deleted
        documents = self.service.list_database_documents(db_config)
        assert len(documents) == 0


if __name__ == "__main__":
    pytest.main([__file__])
