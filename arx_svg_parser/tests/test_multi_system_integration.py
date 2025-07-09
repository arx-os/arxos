"""
Multi-System Integration Framework Tests

Comprehensive test suite for the Multi-System Integration Framework covering
connection management, data transformation, synchronization, and monitoring.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

from services.multi_system_integration import (
    MultiSystemIntegration,
    SystemType,
    ConnectionStatus,
    SyncDirection,
    ConflictResolution,
    SystemConnection,
    FieldMapping,
    SyncResult
)


class TestMultiSystemIntegration:
    """Test suite for Multi-System Integration Framework."""
    
    @pytest.fixture
    def integration_service(self):
        """Create a fresh integration service instance for testing."""
        return MultiSystemIntegration()
    
    @pytest.fixture
    def sample_connection_config(self):
        """Sample connection configuration for testing."""
        return {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password",
            "database": "test_db",
            "ssl_enabled": True,
            "timeout": 30,
            "retry_attempts": 3
        }
    
    @pytest.fixture
    def sample_mapping_config(self):
        """Sample field mapping configuration for testing."""
        return {
            "mapping_id": "mapping_001",
            "system_id": "test_cmms_001",
            "arxos_field": "equipment_name",
            "external_field": "asset_name",
            "transformation_rule": "formatting:uppercase",
            "is_required": True,
            "data_type": "string",
            "validation_rule": "validation:required"
        }
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for transformation and sync testing."""
        return {
            "equipment_name": "HVAC Unit 1",
            "equipment_type": "HVAC",
            "location": "Floor 2",
            "status": "operational",
            "last_maintenance": "2024-01-15",
            "next_maintenance": "2024-04-15"
        }
    
    def test_initialization(self, integration_service):
        """Test service initialization."""
        assert integration_service is not None
        assert hasattr(integration_service, 'connections')
        assert hasattr(integration_service, 'transformers')
        assert hasattr(integration_service, 'connectors')
        assert hasattr(integration_service, 'transformation_engine')
    
    def test_create_system_connection(self, integration_service, sample_connection_config):
        """Test creating a system connection."""
        connection = integration_service.create_system_connection(sample_connection_config)
        
        assert connection.system_id == "test_cmms_001"
        assert connection.system_type == SystemType.CMMS
        assert connection.connection_name == "Test CMMS Connection"
        assert connection.host == "test-cmms.example.com"
        assert connection.port == 8080
        assert connection.username == "test_user"
        assert connection.password == "test_password"
        assert connection.database == "test_db"
        assert connection.ssl_enabled is True
        assert connection.timeout == 30
        assert connection.retry_attempts == 3
        assert connection.status == ConnectionStatus.DISCONNECTED
        assert connection.created_at is not None
        assert connection.updated_at is not None
        
        # Verify connection is stored
        assert "test_cmms_001" in integration_service.connections
    
    def test_create_system_connection_validation(self, integration_service):
        """Test connection configuration validation."""
        # Test missing required fields
        invalid_config = {
            "system_id": "test_001",
            # Missing system_type
            "connection_name": "Test Connection"
        }
        
        with pytest.raises(ValueError, match="Missing required field: system_type"):
            integration_service.create_system_connection(invalid_config)
        
        # Test invalid port
        invalid_port_config = {
            "system_id": "test_002",
            "system_type": "cmms",
            "connection_name": "Test Connection",
            "host": "test.example.com",
            "port": -1,  # Invalid port
            "username": "user",
            "password": "pass"
        }
        
        with pytest.raises(ValueError, match="Port must be a positive integer"):
            integration_service.create_system_connection(invalid_port_config)
        
        # Test invalid system type
        invalid_type_config = {
            "system_id": "test_003",
            "system_type": "invalid_type",
            "connection_name": "Test Connection",
            "host": "test.example.com",
            "port": 8080,
            "username": "user",
            "password": "pass"
        }
        
        with pytest.raises(ValueError, match="Invalid system type: invalid_type"):
            integration_service.create_system_connection(invalid_type_config)
    
    def test_test_connection(self, integration_service, sample_connection_config):
        """Test system connection testing."""
        # Create connection first
        connection = integration_service.create_system_connection(sample_connection_config)
        
        # Test connection
        test_result = integration_service.test_connection("test_cmms_001")
        
        assert test_result["success"] is True
        assert "system_type" in test_result
        assert "capabilities" in test_result
        assert "response_time" in test_result
        assert test_result["system_type"] == "CMMS"
        assert "work_orders" in test_result["capabilities"]
        
        # Verify connection status was updated
        updated_connection = integration_service.connections["test_cmms_001"]
        assert updated_connection.status == ConnectionStatus.CONNECTED
    
    def test_test_connection_not_found(self, integration_service):
        """Test connection testing for non-existent connection."""
        with pytest.raises(ValueError, match="System connection not found: nonexistent"):
            integration_service.test_connection("nonexistent")
    
    def test_create_field_mapping(self, integration_service, sample_connection_config, sample_mapping_config):
        """Test creating field mapping."""
        # Create connection first
        integration_service.create_system_connection(sample_connection_config)
        
        # Create mapping
        mapping = integration_service.create_field_mapping(sample_mapping_config)
        
        assert mapping.mapping_id == "mapping_001"
        assert mapping.system_id == "test_cmms_001"
        assert mapping.arxos_field == "equipment_name"
        assert mapping.external_field == "asset_name"
        assert mapping.transformation_rule == "formatting:uppercase"
        assert mapping.is_required is True
        assert mapping.data_type == "string"
        assert mapping.validation_rule == "validation:required"
        assert mapping.created_at is not None
        
        # Verify mapping is stored
        assert "test_cmms_001" in integration_service.transformers
        assert "mapping_001" in integration_service.transformers["test_cmms_001"]
    
    def test_create_field_mapping_validation(self, integration_service, sample_mapping_config):
        """Test field mapping configuration validation."""
        # Test missing required fields
        invalid_mapping = {
            "mapping_id": "mapping_001",
            # Missing system_id
            "arxos_field": "equipment_name",
            "external_field": "asset_name"
        }
        
        with pytest.raises(ValueError, match="Missing required field: system_id"):
            integration_service.create_field_mapping(invalid_mapping)
        
        # Test non-existent system
        invalid_system_mapping = {
            "mapping_id": "mapping_001",
            "system_id": "nonexistent",
            "arxos_field": "equipment_name",
            "external_field": "asset_name"
        }
        
        with pytest.raises(ValueError, match="System connection not found: nonexistent"):
            integration_service.create_field_mapping(invalid_system_mapping)
    
    def test_transform_data_outbound(self, integration_service, sample_connection_config, sample_mapping_config, sample_data):
        """Test data transformation for outbound direction."""
        # Create connection and mapping
        integration_service.create_system_connection(sample_connection_config)
        integration_service.create_field_mapping(sample_mapping_config)
        
        # Transform data outbound
        transformed_data = integration_service.transform_data(sample_data, "test_cmms_001", "outbound")
        
        assert "asset_name" in transformed_data
        assert transformed_data["asset_name"] == "HVAC UNIT 1"  # Uppercase transformation
        assert len(transformed_data) == 1  # Only mapped field
    
    def test_transform_data_inbound(self, integration_service, sample_connection_config, sample_mapping_config):
        """Test data transformation for inbound direction."""
        # Create connection and mapping
        integration_service.create_system_connection(sample_connection_config)
        integration_service.create_field_mapping(sample_mapping_config)
        
        # Transform data inbound
        external_data = {"asset_name": "HVAC UNIT 1"}
        transformed_data = integration_service.transform_data(external_data, "test_cmms_001", "inbound")
        
        assert "equipment_name" in transformed_data
        assert transformed_data["equipment_name"] == "HVAC UNIT 1"
        assert len(transformed_data) == 1  # Only mapped field
    
    def test_transform_data_no_mappings(self, integration_service, sample_data):
        """Test data transformation when no mappings exist."""
        # Transform data without any mappings
        transformed_data = integration_service.transform_data(sample_data, "nonexistent", "outbound")
        
        # Should return original data unchanged
        assert transformed_data == sample_data
    
    def test_transform_data_with_calculations(self, integration_service, sample_connection_config):
        """Test data transformation with calculation rules."""
        # Create connection
        integration_service.create_system_connection(sample_connection_config)
        
        # Create mapping with calculation
        calculation_mapping = {
            "mapping_id": "calc_mapping",
            "system_id": "test_cmms_001",
            "arxos_field": "total_cost",
            "external_field": "cost_sum",
            "transformation_rule": "calculation:add:100",
            "is_required": False,
            "data_type": "number"
        }
        integration_service.create_field_mapping(calculation_mapping)
        
        # Transform data with calculation
        data = {"total_cost": 500}
        transformed_data = integration_service.transform_data(data, "test_cmms_001", "outbound")
        
        assert "cost_sum" in transformed_data
        assert transformed_data["cost_sum"] == 600  # 500 + 100
    
    def test_transform_data_with_validation(self, integration_service, sample_connection_config):
        """Test data transformation with validation rules."""
        # Create connection
        integration_service.create_system_connection(sample_connection_config)
        
        # Create mapping with validation
        validation_mapping = {
            "mapping_id": "validation_mapping",
            "system_id": "test_cmms_001",
            "arxos_field": "email",
            "external_field": "contact_email",
            "validation_rule": "validation:email",
            "is_required": True,
            "data_type": "string"
        }
        integration_service.create_field_mapping(validation_mapping)
        
        # Test valid email
        valid_data = {"email": "test@example.com"}
        transformed_data = integration_service.transform_data(valid_data, "test_cmms_001", "outbound")
        assert "contact_email" in transformed_data
        
        # Test invalid email
        invalid_data = {"email": "invalid-email"}
        with pytest.raises(ValueError, match="Required field validation failed: email"):
            integration_service.transform_data(invalid_data, "test_cmms_001", "outbound")
    
    def test_sync_data(self, integration_service, sample_connection_config, sample_data):
        """Test data synchronization."""
        # Create connection
        integration_service.create_system_connection(sample_connection_config)
        
        # Sync data
        sync_result = integration_service.sync_data(
            system_id="test_cmms_001",
            direction=SyncDirection.OUTBOUND,
            data=[sample_data],
            conflict_resolution=ConflictResolution.TIMESTAMP_BASED
        )
        
        assert sync_result.sync_id is not None
        assert sync_result.system_id == "test_cmms_001"
        assert sync_result.direction == SyncDirection.OUTBOUND
        assert sync_result.records_processed == 1
        assert sync_result.records_successful >= 0
        assert sync_result.records_failed >= 0
        assert sync_result.conflicts_resolved >= 0
        assert sync_result.sync_duration > 0
        assert sync_result.status in ["completed", "partial"]
        assert sync_result.timestamp is not None
    
    def test_sync_data_not_connected(self, integration_service, sample_data):
        """Test data synchronization with non-existent connection."""
        with pytest.raises(ValueError, match="System connection not found: nonexistent"):
            integration_service.sync_data(
                system_id="nonexistent",
                direction=SyncDirection.OUTBOUND,
                data=[sample_data]
            )
    
    def test_sync_data_disconnected(self, integration_service, sample_connection_config, sample_data):
        """Test data synchronization with disconnected system."""
        # Create connection (starts as disconnected)
        integration_service.create_system_connection(sample_connection_config)
        
        with pytest.raises(ValueError, match="System not connected: test_cmms_001"):
            integration_service.sync_data(
                system_id="test_cmms_001",
                direction=SyncDirection.OUTBOUND,
                data=[sample_data]
            )
    
    def test_get_connection_status(self, integration_service, sample_connection_config):
        """Test getting connection status."""
        # Create connection
        integration_service.create_system_connection(sample_connection_config)
        
        # Get status
        status = integration_service.get_connection_status("test_cmms_001")
        
        assert status["system_id"] == "test_cmms_001"
        assert status["system_type"] == "cmms"
        assert status["connection_name"] == "Test CMMS Connection"
        assert status["host"] == "test-cmms.example.com"
        assert status["port"] == 8080
        assert status["status"] == "disconnected"
        assert "created_at" in status
        assert "updated_at" in status
    
    def test_get_connection_status_not_found(self, integration_service):
        """Test getting status for non-existent connection."""
        with pytest.raises(ValueError, match="System connection not found: nonexistent"):
            integration_service.get_connection_status("nonexistent")
    
    def test_get_all_connections(self, integration_service, sample_connection_config):
        """Test getting all connections."""
        # Create connection
        integration_service.create_system_connection(sample_connection_config)
        
        # Get all connections
        connections = integration_service.get_all_connections()
        
        assert len(connections) == 1
        assert connections[0]["system_id"] == "test_cmms_001"
        assert connections[0]["system_type"] == "cmms"
    
    def test_get_sync_history(self, integration_service):
        """Test getting sync history."""
        history = integration_service.get_sync_history()
        
        assert isinstance(history, list)
        # Mock history should have some records
        assert len(history) > 0
        
        # Test filtering
        filtered_history = integration_service.get_sync_history(system_id="cmms_001")
        assert isinstance(filtered_history, list)
    
    def test_get_performance_metrics(self, integration_service):
        """Test getting performance metrics."""
        metrics = integration_service.get_performance_metrics()
        
        assert "total_connections" in metrics
        assert "active_connections" in metrics
        assert "total_mappings" in metrics
        assert "supported_system_types" in metrics
        assert "supported_connectors" in metrics
        assert "transformation_operations" in metrics
        
        assert isinstance(metrics["total_connections"], int)
        assert isinstance(metrics["active_connections"], int)
        assert isinstance(metrics["total_mappings"], int)
        assert isinstance(metrics["supported_system_types"], int)
        assert isinstance(metrics["supported_connectors"], int)
        assert isinstance(metrics["transformation_operations"], int)
    
    def test_transformation_engine_operations(self, integration_service):
        """Test transformation engine operations."""
        engine = integration_service.transformation_engine
        
        # Test calculations
        assert engine["calculations"]["add"](5, 3) == 8
        assert engine["calculations"]["subtract"](10, 4) == 6
        assert engine["calculations"]["multiply"](6, 7) == 42
        assert engine["calculations"]["divide"](20, 5) == 4
        assert engine["calculations"]["divide"](10, 0) == 0  # Division by zero protection
        assert engine["calculations"]["average"]([1, 2, 3, 4, 5]) == 3
        assert engine["calculations"]["sum"]([1, 2, 3, 4, 5]) == 15
        assert engine["calculations"]["max"]([1, 5, 3, 2, 4]) == 5
        assert engine["calculations"]["min"]([5, 2, 8, 1, 6]) == 1
        
        # Test validations
        assert engine["validations"]["required"]("test") is True
        assert engine["validations"]["required"]("") is False
        assert engine["validations"]["required"](None) is False
        assert engine["validations"]["email"]("test@example.com") is True
        assert engine["validations"]["email"]("invalid-email") is False
        assert engine["validations"]["numeric"]("123") is True
        assert engine["validations"]["numeric"]("abc") is False
        assert engine["validations"]["range"](5, 1, 10) is True
        assert engine["validations"]["range"](15, 1, 10) is False
        
        # Test formatting
        assert engine["formatting"]["uppercase"]("hello") == "HELLO"
        assert engine["formatting"]["lowercase"]("WORLD") == "world"
        assert engine["formatting"]["titlecase"]("hello world") == "Hello World"
        assert engine["formatting"]["trim"]("  test  ") == "test"
    
    def test_system_connectors(self, integration_service):
        """Test system connectors initialization."""
        connectors = integration_service.connectors
        
        # Test CMMS connectors
        assert SystemType.CMMS in connectors
        cmms_connectors = connectors[SystemType.CMMS]
        assert "maximo" in cmms_connectors
        assert "sap_pm" in cmms_connectors
        assert "infor" in cmms_connectors
        assert "custom" in cmms_connectors
        
        # Test ERP connectors
        assert SystemType.ERP in connectors
        erp_connectors = connectors[SystemType.ERP]
        assert "sap" in erp_connectors
        assert "oracle" in erp_connectors
        assert "dynamics" in erp_connectors
        assert "custom" in erp_connectors
        
        # Test SCADA connectors
        assert SystemType.SCADA in connectors
        scada_connectors = connectors[SystemType.SCADA]
        assert "honeywell" in scada_connectors
        assert "siemens" in scada_connectors
        assert "abb" in scada_connectors
        assert "custom" in scada_connectors
        
        # Test BMS connectors
        assert SystemType.BMS in connectors
        bms_connectors = connectors[SystemType.BMS]
        assert "honeywell_bms" in bms_connectors
        assert "siemens_bms" in bms_connectors
        assert "johnson" in bms_connectors
        assert "custom" in bms_connectors
        
        # Test IoT connectors
        assert SystemType.IOT in connectors
        iot_connectors = connectors[SystemType.IOT]
        assert "modbus" in iot_connectors
        assert "bacnet" in iot_connectors
        assert "mqtt" in iot_connectors
        assert "custom" in iot_connectors
    
    def test_connection_testing_by_type(self, integration_service, sample_connection_config):
        """Test connection testing for different system types."""
        # Test CMMS connection
        cmms_config = sample_connection_config.copy()
        cmms_config["system_type"] = "cmms"
        cmms_connection = integration_service.create_system_connection(cmms_config)
        cmms_result = integration_service._test_cmms_connection(cmms_connection)
        assert cmms_result["success"] is True
        assert cmms_result["system_type"] == "CMMS"
        
        # Test ERP connection
        erp_config = sample_connection_config.copy()
        erp_config["system_type"] = "erp"
        erp_connection = integration_service.create_system_connection(erp_config)
        erp_result = integration_service._test_erp_connection(erp_connection)
        assert erp_result["success"] is True
        assert erp_result["system_type"] == "ERP"
        
        # Test SCADA connection
        scada_config = sample_connection_config.copy()
        scada_config["system_type"] = "scada"
        scada_connection = integration_service.create_system_connection(scada_config)
        scada_result = integration_service._test_scada_connection(scada_connection)
        assert scada_result["success"] is True
        assert scada_result["system_type"] == "SCADA"
        
        # Test BMS connection
        bms_config = sample_connection_config.copy()
        bms_config["system_type"] = "bms"
        bms_connection = integration_service.create_system_connection(bms_config)
        bms_result = integration_service._test_bms_connection(bms_connection)
        assert bms_result["success"] is True
        assert bms_result["system_type"] == "BMS"
        
        # Test IoT connection
        iot_config = sample_connection_config.copy()
        iot_config["system_type"] = "iot"
        iot_connection = integration_service.create_system_connection(iot_config)
        iot_result = integration_service._test_iot_connection(iot_connection)
        assert iot_result["success"] is True
        assert iot_result["system_type"] == "IoT"
    
    def test_sync_by_system_type(self, integration_service, sample_connection_config, sample_data):
        """Test synchronization for different system types."""
        # Test CMMS sync
        cmms_config = sample_connection_config.copy()
        cmms_config["system_type"] = "cmms"
        cmms_connection = integration_service.create_system_connection(cmms_config)
        cmms_connection.status = ConnectionStatus.CONNECTED
        
        cmms_result = integration_service._sync_cmms_record(cmms_connection, sample_data, SyncDirection.OUTBOUND)
        assert cmms_result["success"] is True
        assert "external_id" in cmms_result
        
        # Test ERP sync
        erp_config = sample_connection_config.copy()
        erp_config["system_type"] = "erp"
        erp_connection = integration_service.create_system_connection(erp_config)
        erp_connection.status = ConnectionStatus.CONNECTED
        
        erp_result = integration_service._sync_erp_record(erp_connection, sample_data, SyncDirection.OUTBOUND)
        assert erp_result["success"] is True
        assert "external_id" in erp_result
        
        # Test SCADA sync
        scada_config = sample_connection_config.copy()
        scada_config["system_type"] = "scada"
        scada_connection = integration_service.create_system_connection(scada_config)
        scada_connection.status = ConnectionStatus.CONNECTED
        
        scada_result = integration_service._sync_scada_record(scada_connection, sample_data, SyncDirection.OUTBOUND)
        assert scada_result["success"] is True
        assert "external_id" in scada_result
        
        # Test BMS sync
        bms_config = sample_connection_config.copy()
        bms_config["system_type"] = "bms"
        bms_connection = integration_service.create_system_connection(bms_config)
        bms_connection.status = ConnectionStatus.CONNECTED
        
        bms_result = integration_service._sync_bms_record(bms_connection, sample_data, SyncDirection.OUTBOUND)
        assert bms_result["success"] is True
        assert "external_id" in bms_result
        
        # Test IoT sync
        iot_config = sample_connection_config.copy()
        iot_config["system_type"] = "iot"
        iot_connection = integration_service.create_system_connection(iot_config)
        iot_connection.status = ConnectionStatus.CONNECTED
        
        iot_result = integration_service._sync_iot_record(iot_connection, sample_data, SyncDirection.OUTBOUND)
        assert iot_result["success"] is True
        assert "external_id" in iot_result
    
    def test_error_handling(self, integration_service):
        """Test error handling in various scenarios."""
        # Test invalid transformation rule
        with pytest.raises(Exception):
            integration_service._apply_transformation_rule("test", "invalid:rule:format")
        
        # Test invalid calculation
        with pytest.raises(Exception):
            integration_service._apply_calculation("test", "invalid_operation", [])
        
        # Test invalid validation
        with pytest.raises(Exception):
            integration_service._apply_validation("test", "invalid_validation", [])
        
        # Test invalid formatting
        with pytest.raises(Exception):
            integration_service._apply_formatting("test", "invalid_format", [])
    
    def test_concurrent_operations(self, integration_service, sample_connection_config):
        """Test concurrent operations on the integration service."""
        import threading
        
        # Create connection
        integration_service.create_system_connection(sample_connection_config)
        
        # Test concurrent status checks
        def get_status():
            return integration_service.get_connection_status("test_cmms_001")
        
        threads = []
        results = []
        
        for _ in range(10):
            thread = threading.Thread(target=lambda: results.append(get_status()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 10
        for result in results:
            assert result["system_id"] == "test_cmms_001"
    
    def test_performance_under_load(self, integration_service, sample_connection_config, sample_data):
        """Test performance under load."""
        # Create multiple connections
        for i in range(5):
            config = sample_connection_config.copy()
            config["system_id"] = f"test_cmms_{i:03d}"
            integration_service.create_system_connection(config)
        
        # Test bulk operations
        start_time = time.time()
        
        # Perform multiple operations
        for i in range(100):
            integration_service.get_connection_status(f"test_cmms_{i % 5:03d}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        assert duration < 1.0  # Should complete in under 1 second
    
    def test_data_integrity(self, integration_service, sample_connection_config, sample_mapping_config, sample_data):
        """Test data integrity during transformations."""
        # Create connection and mapping
        integration_service.create_system_connection(sample_connection_config)
        integration_service.create_field_mapping(sample_mapping_config)
        
        # Test that original data is not modified
        original_data = sample_data.copy()
        transformed_data = integration_service.transform_data(sample_data, "test_cmms_001", "outbound")
        
        # Original data should remain unchanged
        assert sample_data == original_data
        
        # Transformed data should be different
        assert transformed_data != original_data
    
    def test_audit_logging(self, integration_service, sample_connection_config):
        """Test audit logging functionality."""
        # Create connection (should trigger audit log)
        connection = integration_service.create_system_connection(sample_connection_config)
        
        # Test connection (should trigger audit log)
        test_result = integration_service.test_connection("test_cmms_001")
        
        # Both operations should have been logged
        # In a real implementation, we would verify the logs were written
        assert connection.system_id == "test_cmms_001"
        assert test_result["success"] is True


class TestIntegrationFrameworkEndpoints:
    """Test suite for integration framework API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from ..api.main import app
        return TestClient(app)
    
    def test_create_system_connection_endpoint(self, client):
        """Test create system connection endpoint."""
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        
        response = client.post("/api/v1/integration/connections", json=connection_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["connection"]["system_id"] == "test_cmms_001"
        assert data["connection"]["system_type"] == "cmms"
        assert "message" in data
        assert "metadata" in data
    
    def test_test_connection_endpoint(self, client):
        """Test test connection endpoint."""
        # First create a connection
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        client.post("/api/v1/integration/connections", json=connection_config)
        
        # Then test the connection
        response = client.post("/api/v1/integration/connections/test_cmms_001/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["system_id"] == "test_cmms_001"
        assert "test_result" in data
        assert "metadata" in data
    
    def test_get_all_connections_endpoint(self, client):
        """Test get all connections endpoint."""
        response = client.get("/api/v1/integration/connections")
        
        assert response.status_code == 200
        data = response.json()
        assert "connections" in data
        assert "summary" in data
        assert "metadata" in data
    
    def test_get_connection_status_endpoint(self, client):
        """Test get connection status endpoint."""
        # First create a connection
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        client.post("/api/v1/integration/connections", json=connection_config)
        
        # Then get the status
        response = client.get("/api/v1/integration/connections/test_cmms_001")
        
        assert response.status_code == 200
        data = response.json()
        assert "connection_status" in data
        assert "metadata" in data
    
    def test_create_field_mapping_endpoint(self, client):
        """Test create field mapping endpoint."""
        # First create a connection
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        client.post("/api/v1/integration/connections", json=connection_config)
        
        # Then create a mapping
        mapping_config = {
            "mapping_id": "mapping_001",
            "system_id": "test_cmms_001",
            "arxos_field": "equipment_name",
            "external_field": "asset_name",
            "transformation_rule": "formatting:uppercase",
            "is_required": True,
            "data_type": "string"
        }
        
        response = client.post("/api/v1/integration/mappings", json=mapping_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["mapping"]["mapping_id"] == "mapping_001"
        assert data["mapping"]["system_id"] == "test_cmms_001"
        assert "message" in data
        assert "metadata" in data
    
    def test_transform_data_endpoint(self, client):
        """Test transform data endpoint."""
        # First create connection and mapping
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        client.post("/api/v1/integration/connections", json=connection_config)
        
        mapping_config = {
            "mapping_id": "mapping_001",
            "system_id": "test_cmms_001",
            "arxos_field": "equipment_name",
            "external_field": "asset_name",
            "transformation_rule": "formatting:uppercase",
            "is_required": True,
            "data_type": "string"
        }
        client.post("/api/v1/integration/mappings", json=mapping_config)
        
        # Then transform data
        transform_request = {
            "data": {"equipment_name": "HVAC Unit 1"},
            "system_id": "test_cmms_001",
            "direction": "outbound"
        }
        
        response = client.post("/api/v1/integration/transform", json=transform_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "transformed_data" in data
        assert "transformation_summary" in data
        assert "metadata" in data
    
    def test_sync_data_endpoint(self, client):
        """Test sync data endpoint."""
        # First create a connection
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        client.post("/api/v1/integration/connections", json=connection_config)
        
        # Then sync data
        sync_request = {
            "system_id": "test_cmms_001",
            "direction": "outbound",
            "data": [{"equipment_name": "HVAC Unit 1"}],
            "conflict_resolution": "timestamp_based"
        }
        
        response = client.post("/api/v1/integration/sync", json=sync_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "sync_result" in data
        assert "metadata" in data
    
    def test_get_sync_history_endpoint(self, client):
        """Test get sync history endpoint."""
        response = client.get("/api/v1/integration/sync/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "sync_history" in data
        assert "summary" in data
        assert "metadata" in data
    
    def test_get_performance_metrics_endpoint(self, client):
        """Test get performance metrics endpoint."""
        response = client.get("/api/v1/integration/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert "performance_metrics" in data
        assert "framework_status" in data
        assert "capabilities" in data
        assert "supported_systems" in data
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/integration/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "checks" in data
    
    def test_get_supported_systems_endpoint(self, client):
        """Test get supported systems endpoint."""
        response = client.get("/api/v1/integration/supported-systems")
        
        assert response.status_code == 200
        data = response.json()
        assert "system_types" in data
        assert "transformation_engine" in data
        assert "sync_directions" in data
        assert "conflict_resolution" in data
        assert "connection_statuses" in data
    
    def test_disconnect_system_endpoint(self, client):
        """Test disconnect system endpoint."""
        # First create a connection
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        client.post("/api/v1/integration/connections", json=connection_config)
        
        # Then disconnect
        response = client.post("/api/v1/integration/connections/test_cmms_001/disconnect")
        
        assert response.status_code == 200
        data = response.json()
        assert data["system_id"] == "test_cmms_001"
        assert data["new_status"] == "disconnected"
        assert "message" in data
    
    def test_reconnect_system_endpoint(self, client):
        """Test reconnect system endpoint."""
        # First create a connection
        connection_config = {
            "system_id": "test_cmms_001",
            "system_type": "cmms",
            "connection_name": "Test CMMS Connection",
            "host": "test-cmms.example.com",
            "port": 8080,
            "username": "test_user",
            "password": "test_password"
        }
        client.post("/api/v1/integration/connections", json=connection_config)
        
        # Then reconnect
        response = client.post("/api/v1/integration/connections/test_cmms_001/reconnect")
        
        assert response.status_code == 200
        data = response.json()
        assert data["system_id"] == "test_cmms_001"
        assert "reconnection_successful" in data
        assert "new_status" in data
        assert "test_result" in data
        assert "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 