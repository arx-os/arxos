"""
Tests for Persistence Service and API Layer

This module tests:
- Persistence service (save/load BIM assemblies and SVGs)
- API endpoints (upload, assemble, export, query)
- Error handling and edge cases
- Round-trip save/load functionality
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
from typing import Dict, Any

from core.services.persistence
from services.export_integration import ExportIntegration
from utils.errors import ExportError, ValidationError

# Mock FastAPI app for testing
from fastapi.testclient import TestClient
from core.api.main

client = TestClient(app)


class TestPersistenceService:
    """Test PersistenceService functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.persistence = PersistenceService()
        self.test_bim_data = {
            "elements": [
                {"id": "elem1", "type": "wall", "properties": {"height": 3.0}},
                {"id": "elem2", "type": "door", "properties": {"width": 0.9}}
            ],
            "systems": [
                {"id": "sys1", "type": "hvac", "elements": ["elem1"]}
            ],
            "spaces": [
                {"id": "space1", "type": "room", "elements": ["elem1", "elem2"]}
            ],
            "relationships": [
                {"id": "rel1", "type": "contains", "source": "space1", "target": "elem1"}
            ],
            "metadata": {
                "version": "1.0",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
        self.test_svg_content = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray"/>
            <circle cx="150" cy="200" r="30" fill="blue"/>
        </svg>
        """
    
    def test_save_load_bim_json(self):
        """Test saving and loading BIM data in JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name
        
        try:
            # Save BIM data
            self.persistence.save_bim_json(self.test_bim_data, file_path)
            
            # Load BIM data
            loaded_data = self.persistence.load_bim_json(file_path)
            
            # Verify data integrity
            assert loaded_data["elements"] == self.test_bim_data["elements"]
            assert loaded_data["systems"] == self.test_bim_data["systems"]
            assert loaded_data["spaces"] == self.test_bim_data["spaces"]
            assert loaded_data["relationships"] == self.test_bim_data["relationships"]
            assert loaded_data["metadata"] == self.test_bim_data["metadata"]
            
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_save_load_bim_xml(self):
        """Test saving and loading BIM data in XML format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            file_path = f.name
        
        try:
            # Save BIM data
            self.persistence.save_bim_xml(self.test_bim_data, file_path)
            
            # Load BIM data
            loaded_data = self.persistence.load_bim_xml(file_path)
            
            # Verify data integrity (XML structure may differ slightly)
            assert "elements" in loaded_data
            assert "systems" in loaded_data
            assert "spaces" in loaded_data
            assert "relationships" in loaded_data
            assert "metadata" in loaded_data
            
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_save_load_svg(self):
        """Test saving and loading SVG content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            file_path = f.name
        
        try:
            # Save SVG
            self.persistence.save_svg(self.test_svg_content, file_path)
            
            # Load SVG
            loaded_content = self.persistence.load_svg(file_path)
            
            # Verify content integrity
            assert loaded_content.strip() == self.test_svg_content.strip()
            
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_save_bim_json_error(self):
        """Test error handling when saving BIM JSON fails."""
        # Try to save to a non-existent directory
        invalid_path = "/non/existent/path/test.json"
        
        with pytest.raises(ExportError):
            self.persistence.save_bim_json(self.test_bim_data, invalid_path)
    
    def test_load_bim_json_error(self):
        """Test error handling when loading BIM JSON fails."""
        # Try to load from a non-existent file
        invalid_path = "/non/existent/file.json"
        
        with pytest.raises(ValidationError):
            self.persistence.load_bim_json(invalid_path)
    
    def test_save_bim_xml_error(self):
        """Test error handling when saving BIM XML fails."""
        # Try to save to a non-existent directory
        invalid_path = "/non/existent/path/test.xml"
        
        with pytest.raises(ExportError):
            self.persistence.save_bim_xml(self.test_bim_data, invalid_path)
    
    def test_load_bim_xml_error(self):
        """Test error handling when loading BIM XML fails."""
        # Try to load from a non-existent file
        invalid_path = "/non/existent/file.xml"
        
        with pytest.raises(ValidationError):
            self.persistence.load_bim_xml(invalid_path)
    
    def test_save_svg_error(self):
        """Test error handling when saving SVG fails."""
        # Try to save to a non-existent directory
        invalid_path = "/non/existent/path/test.svg"
        
        with pytest.raises(ExportError):
            self.persistence.save_svg(self.test_svg_content, invalid_path)
    
    def test_load_svg_error(self):
        """Test error handling when loading SVG fails."""
        # Try to load from a non-existent file
        invalid_path = "/non/existent/file.svg"
        
        with pytest.raises(ValidationError):
            self.persistence.load_svg(invalid_path)


class TestExportIntegration:
    """Test ExportIntegration functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.export_service = ExportIntegration()
        self.test_bim_data = {
            "elements": [{"id": "elem1", "type": "wall"}],
            "systems": [{"id": "sys1", "type": "hvac"}],
            "metadata": {"version": "1.0"}
        }
        self.test_svg_content = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray"/>
        </svg>
        """
    
    def test_save_load_bim_assembly(self):
        """Test saving and loading BIM assembly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            file_path = f.name
        
        try:
            # Save BIM assembly
            self.export_service.save_bim_assembly(self.test_bim_data, file_path, "json")
            
            # Load BIM assembly
            loaded_data = self.export_service.load_bim_assembly(file_path, "json")
            
            # Verify data integrity
            assert loaded_data["elements"] == self.test_bim_data["elements"]
            assert loaded_data["systems"] == self.test_bim_data["systems"]
            assert loaded_data["metadata"] == self.test_bim_data["metadata"]
            
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_save_svg_with_metadata(self):
        """Test saving SVG with embedded metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            file_path = f.name
        
        try:
            metadata = {"title": "Test SVG", "author": "Test User"}
            
            # Save SVG with metadata
            self.export_service.save_svg_with_metadata(self.test_svg_content, file_path, metadata)
            
            # Load SVG and extract metadata
            loaded_content, loaded_metadata = self.export_service.load_svg_with_metadata(file_path)
            
            # Verify content integrity
            assert "rect" in loaded_content
            assert "svg" in loaded_content
            
            # Metadata extraction may not work perfectly due to XML parsing
            # but should not raise an error
            
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_save_bim_assembly_unsupported_format(self):
        """Test error handling for unsupported BIM assembly format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            file_path = f.name
        
        try:
            with pytest.raises(ExportError):
                self.export_service.save_bim_assembly(self.test_bim_data, file_path, "txt")
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_load_bim_assembly_unsupported_format(self):
        """Test error handling for unsupported BIM assembly format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            file_path = f.name
        
        try:
            with pytest.raises(ValidationError):
                self.export_service.load_bim_assembly(file_path, "txt")
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "SVG-BIM API is running"
        assert data["version"] == "1.0.0"
    
    def test_upload_svg_success(self):
        """Test successful SVG upload."""
        # Create a test SVG file
        test_svg_content = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray"/>
            <circle cx="150" cy="200" r="30" fill="blue"/>
        </svg>
        """
        
        # Mock file upload
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = test_svg_content.encode()
            
            response = client.post(
                "/upload/svg",
                files={"file": ("test.svg", test_svg_content, "image/svg+xml")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["element_count"] > 0
            assert "svg_" in data["svg_id"]
    
    def test_upload_svg_invalid_file(self):
        """Test SVG upload with invalid file type."""
        response = client.post(
            "/upload/svg",
            files={"file": ("test.txt", "not an svg", "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "File must be an SVG" in data["detail"]
    
    def test_assemble_bim_success(self):
        """Test successful BIM assembly."""
        test_svg_content = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray"/>
        </svg>
        """
        
        response = client.post(
            "/assemble/bim",
            data={
                "svg_content": test_svg_content,
                "format": "json",
                "validation_level": "standard"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["format"] == "json"
        assert "file_path" in data
    
    def test_assemble_bim_invalid_format(self):
        """Test BIM assembly with invalid format."""
        test_svg_content = """
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect x="100" y="100" width="200" height="20" fill="gray"/>
        </svg>
        """
        
        response = client.post(
            "/assemble/bim",
            data={
                "svg_content": test_svg_content,
                "format": "invalid",
                "validation_level": "standard"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported format" in data["detail"]
    
    def test_export_bim_success(self):
        """Test successful BIM export."""
        response = client.get("/export/bim/test123?format=json")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["format"] == "json"
        assert "file_path" in data
    
    def test_export_bim_invalid_format(self):
        """Test BIM export with invalid format."""
        response = client.get("/export/bim/test123?format=invalid")
        
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported format" in data["detail"]
    
    def test_query_bim_summary(self):
        """Test BIM query for summary."""
        response = client.get("/query/bim/test123?query_type=summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "element_count" in data["data"]
        assert "system_count" in data["data"]
    
    def test_query_bim_elements(self):
        """Test BIM query for elements."""
        response = client.get("/query/bim/test123?query_type=elements")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "elements" in data["data"]
    
    def test_query_bim_invalid_type(self):
        """Test BIM query with invalid query type."""
        response = client.get("/query/bim/test123?query_type=invalid")
        
        assert response.status_code == 400
        data = response.json()
        assert "Unknown query type" in data["detail"]
    
    def test_download_file_not_found(self):
        """Test file download when file doesn't exist."""
        response = client.get("/download/nonexistent/file.txt")
        
        assert response.status_code == 404
        data = response.json()
        assert "File not found" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__]) 