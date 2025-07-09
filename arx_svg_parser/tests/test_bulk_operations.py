"""
Test bulk operations for symbol management.

Features tested:
- Bulk import from files (JSON, CSV)
- Bulk export to files (JSON, CSV)
- Progress tracking for long-running operations
- Background task processing
- Error handling and validation
- File format validation
- Authentication and authorization
"""

import pytest
import json
import csv
import io
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from ..routers.symbol_management import router, job_tracker, process_bulk_import, process_bulk_export, ExportFormat
from ..services.symbol_manager import SymbolManager
from ..utils.auth import User, UserRole

# Test client
client = TestClient(router)

class TestBulkImport:
    """Test bulk import functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear job tracker
        job_tracker.jobs.clear()
        
        # Mock symbol manager
        self.mock_symbol_manager = Mock(spec=SymbolManager)
        self.mock_symbol_manager.create_symbol.return_value = {
            "id": "test_symbol",
            "name": "Test Symbol",
            "system": "test"
        }
    
    def test_bulk_import_json_valid(self):
        """Test bulk import with valid JSON file."""
        # Create test JSON data
        symbols_data = [
            {
                "id": "symbol1",
                "name": "Symbol 1",
                "system": "electrical",
                "svg": {"content": "<svg>...</svg>"}
            },
            {
                "id": "symbol2", 
                "name": "Symbol 2",
                "system": "mechanical",
                "svg": {"content": "<svg>...</svg>"}
            }
        ]
        
        json_content = json.dumps(symbols_data)
        file_content = json_content.encode('utf-8')
        
        # Mock file upload
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "symbols.json"
        mock_file.read = AsyncMock(return_value=file_content)
        
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            with patch('routers.symbol_management.symbol_manager', self.mock_symbol_manager):
                response = client.post(
                    "/api/v1/symbols/bulk-import",
                    files={"file": ("symbols.json", file_content, "application/json")},
                    headers={"Authorization": "Bearer test-token"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 2
        assert data["job_id"] is not None
        
        # Verify job was created
        job = job_tracker.get_job(data["job_id"])
        assert job is not None
        assert job["status"] == "pending"
        assert job["total_items"] == 2
    
    def test_bulk_import_csv_valid(self):
        """Test bulk import with valid CSV file."""
        # Create test CSV data
        symbols_data = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"}
        ]
        
        # Convert to CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "name", "system"])
        writer.writeheader()
        writer.writerows(symbols_data)
        csv_content = output.getvalue()
        file_content = csv_content.encode('utf-8')
        
        # Mock file upload
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "symbols.csv"
        mock_file.read = AsyncMock(return_value=file_content)
        
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            with patch('routers.symbol_management.symbol_manager', self.mock_symbol_manager):
                response = client.post(
                    "/api/v1/symbols/bulk-import",
                    files={"file": ("symbols.csv", file_content, "text/csv")},
                    headers={"Authorization": "Bearer test-token"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 2
        assert data["job_id"] is not None
    
    def test_bulk_import_invalid_format(self):
        """Test bulk import with invalid file format."""
        file_content = b"invalid content"
        
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.post(
                "/api/v1/symbols/bulk-import",
                files={"file": ("symbols.txt", file_content, "text/plain")},
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]
    
    def test_bulk_import_invalid_json(self):
        """Test bulk import with invalid JSON content."""
        file_content = b"{ invalid json }"
        
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.post(
                "/api/v1/symbols/bulk-import",
                files={"file": ("symbols.json", file_content, "application/json")},
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 400
        assert "Failed to parse file" in response.json()["detail"]
    
    def test_bulk_import_empty_file(self):
        """Test bulk import with empty file."""
        file_content = b"[]"
        
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.post(
                "/api/v1/symbols/bulk-import",
                files={"file": ("symbols.json", file_content, "application/json")},
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 400
        assert "No symbols found in file" in response.json()["detail"]

class TestBulkExport:
    """Test bulk export functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear job tracker
        job_tracker.jobs.clear()
        
        # Mock symbol manager
        self.mock_symbol_manager = Mock(spec=SymbolManager)
        self.mock_symbol_manager.list_symbols.return_value = [
            {
                "id": "symbol1",
                "name": "Symbol 1",
                "system": "electrical",
                "svg": {"content": "<svg>...</svg>"}
            },
            {
                "id": "symbol2",
                "name": "Symbol 2", 
                "system": "mechanical",
                "svg": {"content": "<svg>...</svg>"}
            }
        ]
    
    def test_export_json_format(self):
        """Test export in JSON format."""
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            with patch('routers.symbol_management.symbol_manager', self.mock_symbol_manager):
                response = client.get(
                    "/api/v1/symbols/export?format=json",
                    headers={"Authorization": "Bearer test-token"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        assert data["total_symbols"] == 2
        assert data["job_id"] is not None
    
    def test_export_csv_format(self):
        """Test export in CSV format."""
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            with patch('routers.symbol_management.symbol_manager', self.mock_symbol_manager):
                response = client.get(
                    "/api/v1/symbols/export?format=csv",
                    headers={"Authorization": "Bearer test-token"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"
        assert data["total_symbols"] == 2
    
    def test_export_with_system_filter(self):
        """Test export with system filter."""
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            with patch('routers.symbol_management.symbol_manager', self.mock_symbol_manager):
                response = client.get(
                    "/api/v1/symbols/export?format=json&system=electrical",
                    headers={"Authorization": "Bearer test-token"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "json"
        # Verify system filter was applied
        self.mock_symbol_manager.list_symbols.assert_called_with(system="electrical")
    
    def test_export_no_symbols(self):
        """Test export when no symbols exist."""
        # Mock empty symbol list
        self.mock_symbol_manager.list_symbols.return_value = []
        
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            with patch('routers.symbol_management.symbol_manager', self.mock_symbol_manager):
                response = client.get(
                    "/api/v1/symbols/export?format=json",
                    headers={"Authorization": "Bearer test-token"}
                )
        
        assert response.status_code == 404
        assert "No symbols found to export" in response.json()["detail"]

class TestProgressTracking:
    """Test progress tracking functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear job tracker
        job_tracker.jobs.clear()
        
        # Create a test job
        self.job_id = job_tracker.create_job("test_job")
        job_tracker.update_job(
            self.job_id,
            status="processing",
            progress=50,
            total_items=10,
            processed_items=5
        )
    
    def test_get_job_progress(self):
        """Test getting job progress."""
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.get(
                f"/api/v1/symbols/progress/{self.job_id}",
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == self.job_id
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["total_items"] == 10
        assert data["processed_items"] == 5
    
    def test_get_nonexistent_job(self):
        """Test getting progress for nonexistent job."""
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.get(
                "/api/v1/symbols/progress/nonexistent_job",
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

class TestDownloadExport:
    """Test download export functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear job tracker
        job_tracker.jobs.clear()
        
        # Create a completed export job
        self.job_id = job_tracker.create_job("bulk_export")
        job_tracker.update_job(
            self.job_id,
            status="completed",
            result={
                "content": '{"symbols": []}',
                "filename": "symbols_export.json",
                "content_type": "application/json"
            }
        )
    
    def test_download_completed_export(self):
        """Test downloading completed export."""
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.get(
                f"/api/v1/symbols/export/download?job_id={self.job_id}",
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]
        assert "symbols_export.json" in response.headers["content-disposition"]
    
    def test_download_incomplete_export(self):
        """Test downloading incomplete export."""
        # Update job to incomplete status
        job_tracker.update_job(self.job_id, status="processing")
        
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.get(
                f"/api/v1/symbols/export/download?job_id={self.job_id}",
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 400
        assert "Export job not completed" in response.json()["detail"]
    
    def test_download_nonexistent_export(self):
        """Test downloading nonexistent export."""
        # Mock authentication
        mock_user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        with patch('routers.symbol_management.get_current_user', return_value=mock_user):
            response = client.get(
                "/api/v1/symbols/export/download?job_id=nonexistent_job",
                headers={"Authorization": "Bearer test-token"}
            )
        
        assert response.status_code == 404
        assert "Export job not found" in response.json()["detail"]

class TestBackgroundTasks:
    """Test background task processing."""
    
    @pytest.mark.asyncio
    async def test_process_bulk_import_success(self):
        """Test successful bulk import processing."""
        # Mock symbol manager
        mock_symbol_manager = Mock(spec=SymbolManager)
        mock_symbol_manager.create_symbol.return_value = {"id": "test"}
        
        # Test data
        symbols_data = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"}
        ]
        
        job_id = job_tracker.create_job("bulk_import")
        
        with patch('routers.symbol_management.symbol_manager', mock_symbol_manager):
            await process_bulk_import(job_id, symbols_data, "testuser")
        
        # Verify job completion
        job = job_tracker.get_job(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 100
        assert job["processed_items"] == 2
        assert job["result"]["successful"] == 2
        assert job["result"]["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_process_bulk_import_with_errors(self):
        """Test bulk import processing with errors."""
        # Mock symbol manager that raises exception
        mock_symbol_manager = Mock(spec=SymbolManager)
        mock_symbol_manager.create_symbol.side_effect = [
            {"id": "symbol1"},  # Success
            ValueError("Invalid symbol"),  # Error
            {"id": "symbol3"}   # Success
        ]
        
        # Test data
        symbols_data = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"},
            {"id": "symbol3", "name": "Symbol 3", "system": "plumbing"}
        ]
        
        job_id = job_tracker.create_job("bulk_import")
        
        with patch('routers.symbol_management.symbol_manager', mock_symbol_manager):
            await process_bulk_import(job_id, symbols_data, "testuser")
        
        # Verify job completion with errors
        job = job_tracker.get_job(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 100
        assert job["result"]["successful"] == 2
        assert job["result"]["failed"] == 1
        assert len(job["errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_process_bulk_export_json(self):
        """Test bulk export processing in JSON format."""
        # Test data
        symbols = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"}
        ]
        
        job_id = job_tracker.create_job("bulk_export")
        
        await process_bulk_export(job_id, symbols, ExportFormat.JSON, "testuser")
        
        # Verify job completion
        job = job_tracker.get_job(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 100
        assert job["result"]["content_type"] == "application/json"
        assert "symbols_export_" in job["result"]["filename"]
        assert job["result"]["filename"].endswith(".json")
        
        # Verify JSON content
        content = job["result"]["content"]
        parsed = json.loads(content)
        assert len(parsed) == 2
        assert parsed[0]["id"] == "symbol1"
        assert parsed[1]["id"] == "symbol2"
    
    @pytest.mark.asyncio
    async def test_process_bulk_export_csv(self):
        """Test bulk export processing in CSV format."""
        # Test data
        symbols = [
            {"id": "symbol1", "name": "Symbol 1", "system": "electrical"},
            {"id": "symbol2", "name": "Symbol 2", "system": "mechanical"}
        ]
        
        job_id = job_tracker.create_job("bulk_export")
        
        await process_bulk_export(job_id, symbols, ExportFormat.CSV, "testuser")
        
        # Verify job completion
        job = job_tracker.get_job(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 100
        assert job["result"]["content_type"] == "text/csv"
        assert job["result"]["filename"].endswith(".csv")
        
        # Verify CSV content
        content = job["result"]["content"]
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["id"] == "symbol1"
        assert rows[1]["id"] == "symbol2"

if __name__ == "__main__":
    pytest.main([__file__]) 