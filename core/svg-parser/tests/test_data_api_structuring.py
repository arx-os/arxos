"""
Tests for Data API Structuring Service

Comprehensive test suite for system object querying, filtering, pagination,
contributor attribution, and data anonymization.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from services.data_api_structuring import (
    DataAPIStructuringService, QueryFilter, ObjectType, ObjectStatus,
    ObjectCondition, ContributorRole, SystemObject, PaginationInfo, QueryResult
)
from routers.data_api_structuring import router
from cli_commands.data_api_structuring_cli import DataAPIStructuringCLI
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestDataAPIStructuringService:
    """Test cases for Data API Structuring Service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance with temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        service = DataAPIStructuringService(db_path=db_path)
        yield service
        
        # Cleanup
        os.unlink(db_path)
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.db_path is not None
        assert isinstance(service, DataAPIStructuringService)
    
    def test_query_system_objects_basic(self, service):
        """Test basic system object querying."""
        result = service.query_system_objects(
            page=1,
            page_size=10,
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert isinstance(result, QueryResult)
        assert len(result.objects) > 0
        assert result.pagination.total_count > 0
        assert result.pagination.page == 1
        assert result.pagination.page_size == 10
        assert result.query_time >= 0
        assert result.anonymized_count >= 0
    
    def test_query_system_objects_with_filters(self, service):
        """Test system object querying with filters."""
        filters = QueryFilter(
            object_type=ObjectType.MECHANICAL,
            status=ObjectStatus.ACTIVE,
            condition=ObjectCondition.GOOD
        )
        
        result = service.query_system_objects(
            filters=filters,
            page=1,
            page_size=50,
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert isinstance(result, QueryResult)
        assert len(result.objects) >= 0  # May be 0 if no matching objects
        
        # Verify filters were applied
        for obj in result.objects:
            assert obj.object_type == ObjectType.MECHANICAL
            assert obj.status == ObjectStatus.ACTIVE
            assert obj.condition == ObjectCondition.GOOD
    
    def test_query_system_objects_pagination(self, service):
        """Test pagination functionality."""
        # First page
        result1 = service.query_system_objects(
            page=1,
            page_size=5,
            user_id="test_user",
            user_license_level="basic"
        )
        
        # Second page
        result2 = service.query_system_objects(
            page=2,
            page_size=5,
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert len(result1.objects) <= 5
        assert len(result2.objects) <= 5
        
        # Objects should be different between pages
        obj_ids_1 = {obj.object_id for obj in result1.objects}
        obj_ids_2 = {obj.object_id for obj in result2.objects}
        assert obj_ids_1.isdisjoint(obj_ids_2)
    
    def test_get_system_object(self, service):
        """Test getting specific system object."""
        # First get a list to find an existing object
        result = service.query_system_objects(
            page=1,
            page_size=1,
            user_id="test_user",
            user_license_level="basic"
        )
        
        if result.objects:
            obj_id = result.objects[0].object_id
            obj = service.get_system_object(
                object_id=obj_id,
                user_id="test_user",
                user_license_level="basic"
            )
            
            assert obj is not None
            assert obj.object_id == obj_id
            assert isinstance(obj, SystemObject)
    
    def test_get_system_object_not_found(self, service):
        """Test getting non-existent system object."""
        obj = service.get_system_object(
            object_id="non_existent_id",
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert obj is None
    
    def test_get_objects_by_contributor(self, service):
        """Test getting objects by contributor."""
        result = service.get_objects_by_contributor(
            contributor_id="contrib_001",
            page=1,
            page_size=10,
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert isinstance(result, QueryResult)
        assert len(result.objects) >= 0
        
        # Verify all objects belong to the specified contributor
        for obj in result.objects:
            assert obj.contributor_id == "contrib_001"
    
    def test_get_system_summary(self, service):
        """Test getting system summary."""
        summary = service.get_system_summary(
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert isinstance(summary, dict)
        assert "total_objects" in summary
        assert "objects_by_type" in summary
        assert "objects_by_status" in summary
        assert "objects_by_condition" in summary
        assert "objects_by_contributor" in summary
        assert "recent_installations" in summary
        assert "generated_at" in summary
    
    def test_export_objects_json(self, service):
        """Test exporting objects in JSON format."""
        exported_data = service.export_objects(
            format="json",
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert isinstance(exported_data, str)
        
        # Verify it's valid JSON
        data = json.loads(exported_data)
        assert "objects" in data
        assert "export_info" in data
    
    def test_export_objects_csv(self, service):
        """Test exporting objects in CSV format."""
        exported_data = service.export_objects(
            format="csv",
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert isinstance(exported_data, str)
        assert len(exported_data) > 0
        
        # Verify CSV format
        lines = exported_data.strip().split('\n')
        assert len(lines) > 1  # Header + at least one data row
    
    def test_export_objects_invalid_format(self, service):
        """Test exporting with invalid format."""
        with pytest.raises(ValueError):
            service.export_objects(
                format="invalid_format",
                user_id="test_user",
                user_license_level="basic"
            )
    
    def test_get_access_analytics(self, service):
        """Test getting access analytics."""
        analytics = service.get_access_analytics(days=30)
        
        assert isinstance(analytics, dict)
        assert "period_days" in analytics
        assert "total_access" in analytics
        assert "access_by_endpoint" in analytics
        assert "avg_response_time" in analytics
        assert "total_objects_returned" in analytics
        assert "total_objects_anonymized" in analytics
        assert "anonymization_rate" in analytics
    
    def test_anonymization_basic_license(self, service):
        """Test anonymization for basic license level."""
        result = service.query_system_objects(
            page=1,
            page_size=10,
            user_id="test_user",
            user_license_level="basic"
        )
        
        for obj in result.objects:
            assert obj.contributor_name == "Anonymous"
            assert obj.metadata["manufacturer"] == "Unknown"
            assert obj.metadata["serial_number"] == "***"
    
    def test_anonymization_limited_license(self, service):
        """Test anonymization for limited license level."""
        result = service.query_system_objects(
            page=1,
            page_size=10,
            user_id="test_user",
            user_license_level="limited"
        )
        
        for obj in result.objects:
            assert obj.contributor_name.endswith("***")
            assert obj.metadata["serial_number"] == "***"
            assert "critical_thresholds" not in obj.behavior_profile
    
    def test_anonymization_full_license(self, service):
        """Test no anonymization for full license level."""
        result = service.query_system_objects(
            page=1,
            page_size=10,
            user_id="test_user",
            user_license_level="full"
        )
        
        for obj in result.objects:
            assert obj.contributor_name != "Anonymous"
            assert obj.metadata["manufacturer"] != "Unknown"
            assert obj.metadata["serial_number"] != "***"
    
    def test_performance_metrics(self, service):
        """Test getting performance metrics."""
        metrics = service.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert "total_objects" in metrics
        assert "objects_by_type" in metrics
        assert "recent_access" in metrics
        assert "avg_response_time" in metrics
        assert "database_size" in metrics
    
    def test_query_with_date_filters(self, service):
        """Test querying with date filters."""
        from datetime import datetime, timedelta
        
        # Create date filters
        date_from = datetime.now() - timedelta(days=365)
        date_to = datetime.now()
        
        filters = QueryFilter(
            date_from=date_from,
            date_to=date_to
        )
        
        result = service.query_system_objects(
            filters=filters,
            page=1,
            page_size=50,
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert isinstance(result, QueryResult)
        
        # Verify date filters were applied
        for obj in result.objects:
            assert obj.installation_date >= date_from
            assert obj.installation_date <= date_to


class TestDataAPIStructuringRouter:
    """Test cases for Data API Structuring Router."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_get_systems_endpoint(self, client):
        """Test GET /data/systems endpoint."""
        response = client.get("/data/systems?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "objects" in data["data"]
        assert "pagination" in data["data"]
    
    def test_get_systems_with_filters(self, client):
        """Test GET /data/systems with filters."""
        response = client.get(
            "/data/systems",
            params={
                "object_type": "mechanical",
                "status": "active",
                "page": 1,
                "page_size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_get_systems_invalid_filter(self, client):
        """Test GET /data/systems with invalid filter."""
        response = client.get(
            "/data/systems",
            params={"object_type": "invalid_type"}
        )
        
        assert response.status_code == 400
        assert "Invalid object type" in response.json()["detail"]
    
    def test_get_system_object_endpoint(self, client):
        """Test GET /data/systems/{object_id} endpoint."""
        # First get a list to find an existing object
        list_response = client.get("/data/systems?page=1&page_size=1")
        list_data = list_response.json()
        
        if list_data["data"]["objects"]:
            object_id = list_data["data"]["objects"][0]["object_id"]
            
            response = client.get(f"/data/systems/{object_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["object_id"] == object_id
    
    def test_get_system_object_not_found(self, client):
        """Test GET /data/systems/{object_id} with non-existent object."""
        response = client.get("/data/systems/non_existent_id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_objects_endpoint(self, client):
        """Test GET /data/objects endpoint."""
        response = client.get("/data/objects?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "objects" in data["data"]
        assert "pagination" in data["data"]
    
    def test_get_objects_by_contributor_endpoint(self, client):
        """Test GET /data/contributors/{contributor_id}/objects endpoint."""
        response = client.get("/data/contributors/contrib_001/objects?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["contributor_id"] == "contrib_001"
    
    def test_get_system_summary_endpoint(self, client):
        """Test GET /data/summary endpoint."""
        response = client.get("/data/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_objects" in data["data"]
        assert "objects_by_type" in data["data"]
    
    def test_get_analytics_endpoint(self, client):
        """Test GET /data/analytics endpoint."""
        response = client.get("/data/analytics?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "period_days" in data["data"]
        assert "total_access" in data["data"]
    
    def test_export_endpoint(self, client):
        """Test GET /data/export endpoint."""
        response = client.get("/data/export?format=json")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["format"] == "json"
    
    def test_export_invalid_format(self, client):
        """Test GET /data/export with invalid format."""
        response = client.get("/data/export?format=invalid")
        
        assert response.status_code == 400
        assert "Unsupported format" in response.json()["detail"]
    
    def test_status_endpoint(self, client):
        """Test GET /data/status endpoint."""
        response = client.get("/data/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "service_status" in data["data"]
    
    def test_health_endpoint(self, client):
        """Test GET /data/health endpoint."""
        response = client.get("/data/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data["data"]
    
    def test_filters_endpoints(self, client):
        """Test filter endpoints."""
        # Test object types
        response = client.get("/data/filters/object-types")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "object_types" in data["data"]
        
        # Test statuses
        response = client.get("/data/filters/statuses")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "statuses" in data["data"]
        
        # Test conditions
        response = client.get("/data/filters/conditions")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "conditions" in data["data"]
        
        # Test contributors
        response = client.get("/data/filters/contributors")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "contributors" in data["data"]
    
    def test_advanced_query_endpoint(self, client):
        """Test POST /data/query endpoint."""
        query_data = {
            "filters": {
                "object_type": "mechanical",
                "status": "active"
            },
            "page": 1,
            "page_size": 10,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        
        response = client.post("/data/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "objects" in data["data"]


class TestDataAPIStructuringCLI:
    """Test cases for Data API Structuring CLI."""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance."""
        return DataAPIStructuringCLI()
    
    def test_cli_initialization(self, cli):
        """Test CLI initialization."""
        assert isinstance(cli, DataAPIStructuringCLI)
        assert cli.service is not None
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'query', '--page', '1', '--page-size', '5'])
    def test_cli_query_command(self, cli):
        """Test CLI query command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'get', '--object-id', 'test_id'])
    def test_cli_get_command(self, cli):
        """Test CLI get command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'summary'])
    def test_cli_summary_command(self, cli):
        """Test CLI summary command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'analytics', '--days', '30'])
    def test_cli_analytics_command(self, cli):
        """Test CLI analytics command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'export', '--format', 'json'])
    def test_cli_export_command(self, cli):
        """Test CLI export command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'filters', '--type', 'object-types'])
    def test_cli_filters_command(self, cli):
        """Test CLI filters command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'status'])
    def test_cli_status_command(self, cli):
        """Test CLI status command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    @patch('sys.argv', ['data_api_structuring_cli.py', 'health'])
    def test_cli_health_command(self, cli):
        """Test CLI health command."""
        with patch('builtins.print') as mock_print:
            cli.run()
            mock_print.assert_called()
    
    def test_cli_parser_creation(self, cli):
        """Test CLI parser creation."""
        parser = cli.create_parser()
        assert parser is not None
        
        # Test that all expected commands exist
        subparsers = [action for action in parser._actions if hasattr(action, 'choices')]
        if subparsers:
            commands = subparsers[0].choices.keys()
            expected_commands = ['query', 'get', 'contributor', 'summary', 'analytics', 
                               'export', 'filters', 'status', 'health']
            for cmd in expected_commands:
                assert cmd in commands


class TestDataAPIStructuringIntegration:
    """Integration tests for Data API Structuring."""
    
    @pytest.fixture
    def service(self):
        """Create service instance with temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        service = DataAPIStructuringService(db_path=db_path)
        yield service
        
        # Cleanup
        os.unlink(db_path)
    
    def test_end_to_end_query_workflow(self, service):
        """Test end-to-end query workflow."""
        # 1. Query objects
        result = service.query_system_objects(
            page=1,
            page_size=10,
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert len(result.objects) > 0
        
        # 2. Get specific object
        obj_id = result.objects[0].object_id
        obj = service.get_system_object(
            object_id=obj_id,
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert obj is not None
        assert obj.object_id == obj_id
        
        # 3. Get system summary
        summary = service.get_system_summary(
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert summary["total_objects"] > 0
        
        # 4. Export objects
        exported_data = service.export_objects(
            format="json",
            user_id="test_user",
            user_license_level="basic"
        )
        
        assert len(exported_data) > 0
        
        # 5. Get analytics
        analytics = service.get_access_analytics(days=1)
        
        assert analytics["period_days"] == 1
    
    def test_performance_under_load(self, service):
        """Test performance under load."""
        import time
        
        start_time = time.time()
        
        # Perform multiple queries
        for i in range(10):
            result = service.query_system_objects(
                page=1,
                page_size=50,
                user_id=f"user_{i}",
                user_license_level="basic"
            )
            assert len(result.objects) >= 0
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 10.0  # 10 seconds max
    
    def test_data_consistency(self, service):
        """Test data consistency across operations."""
        # Get summary
        summary = service.get_system_summary(
            user_id="test_user",
            user_license_level="basic"
        )
        total_objects = summary["total_objects"]
        
        # Query all objects
        result = service.query_system_objects(
            page=1,
            page_size=total_objects + 100,  # Large page size to get all
            user_id="test_user",
            user_license_level="basic"
        )
        
        # Verify consistency
        assert result.pagination.total_count == total_objects
    
    def test_error_handling(self, service):
        """Test error handling."""
        # Test invalid object ID
        obj = service.get_system_object(
            object_id="invalid_id",
            user_id="test_user",
            user_license_level="basic"
        )
        assert obj is None
        
        # Test invalid export format
        with pytest.raises(ValueError):
            service.export_objects(
                format="invalid_format",
                user_id="test_user",
                user_license_level="basic"
            )


if __name__ == "__main__":
    pytest.main([__file__]) 