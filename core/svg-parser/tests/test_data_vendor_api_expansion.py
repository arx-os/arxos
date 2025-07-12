"""
Comprehensive tests for Data Vendor API Expansion service.

Tests analytics, data masking, encryption, compliance checking,
audit logging, and data export functionality.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from services.data_vendor_api_expansion import (
    DataVendorAPIExpansion,
    DataMaskingLevel,
    ComplianceType,
    AnalyticsMetrics,
    DataMaskingRule,
    ComplianceConfig
)
from routers.data_vendor_api_expansion import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Test data
SAMPLE_VENDOR_DATA = {
    "vendor_id": "test_vendor_001",
    "name": "Test Vendor Inc.",
    "email": "contact@testvendor.com",
    "phone": "555-123-4567",
    "address": "123 Main Street, Anytown, USA",
    "ssn": "123-45-6789",
    "credit_card": "4111-1111-1111-1111",
    "ip_address": "192.168.1.100",
    "mac_address": "00:11:22:33:44:55",
    "financial_data": {
        "revenue": 1000000,
        "profit": 150000,
        "tax_id": "12-3456789"
    },
    "medical_record": {
        "patient_id": "P12345",
        "diagnosis": "Hypertension",
        "treatment": "Lisinopril 10mg daily"
    }
}

SAMPLE_ANALYTICS_DATA = {
    "total_records": 1500,
    "unique_vendors": 45,
    "data_quality_score": 0.92,
    "compliance_score": 0.88,
    "last_updated": datetime.now(),
    "trends": {
        "data_growth": [
            {"date": "2024-01-01", "count": 100},
            {"date": "2024-01-02", "count": 120}
        ],
        "quality_improvement": [],
        "compliance_trends": [],
        "vendor_activity": []
    },
    "predictions": {
        "data_growth_forecast": [
            {"day": 1, "predicted_count": 150},
            {"day": 2, "predicted_count": 175}
        ],
        "quality_prediction": 0.94,
        "compliance_risk": "low"
    }
}


class TestDataVendorAPIExpansion:
    """Test suite for DataVendorAPIExpansion service."""
    
    @pytest.fixture
    def service(self):
        """Create a test instance of the service."""
        return DataVendorAPIExpansion()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.total_records = 1500
        mock_result.unique_vendors = 45
        mock_result.avg_quality = 0.92
        mock_result.avg_compliance = 0.88
        mock_result.last_updated = datetime.now()
        mock_db.execute.return_value.fetchone.return_value = mock_result
        return mock_db
    
    def test_service_initialization(self, service):
        """Test service initialization and configuration."""
        assert service.analytics_cache is not None
        assert service.masking_rules is not None
        assert service.compliance_configs is not None
        assert service.encryption_key is not None
        assert service.cipher is not None
        
        # Check masking rules
        assert "email" in service.masking_rules
        assert "phone" in service.masking_rules
        assert "ssn" in service.masking_rules
        
        # Check compliance configs
        assert ComplianceType.GDPR in service.compliance_configs
        assert ComplianceType.HIPAA in service.compliance_configs
        assert ComplianceType.CCPA in service.compliance_configs
        assert ComplianceType.SOX in service.compliance_configs
    
    @patch('services.data_vendor_api_expansion.get_db')
    def test_get_analytics(self, mock_get_db, service, mock_db):
        """Test analytics generation functionality."""
        mock_get_db.return_value = iter([mock_db])
        
        analytics = service.get_analytics(
            vendor_id="test_vendor",
            time_range="30d",
            metrics=["total_records", "data_quality"]
        )
        
        assert isinstance(analytics, AnalyticsMetrics)
        assert analytics.total_records == 1500
        assert analytics.unique_vendors == 45
        assert analytics.data_quality_score == 0.92
        assert analytics.compliance_score == 0.88
        assert analytics.trends is not None
        assert analytics.predictions is not None
    
    def test_data_masking_partial(self, service):
        """Test partial data masking functionality."""
        masked_data = service.mask_sensitive_data(
            SAMPLE_VENDOR_DATA,
            masking_level=DataMaskingLevel.PARTIAL
        )
        
        # Check email masking
        assert masked_data["email"] == "c*****t@testvendor.com"
        
        # Check phone masking
        assert masked_data["phone"] == "***-***-4567"
        
        # Check SSN masking
        assert masked_data["ssn"] == "***-**-6789"
        
        # Check credit card masking
        assert masked_data["credit_card"] == "****-****-****-1111"
        
        # Check non-sensitive fields remain unchanged
        assert masked_data["vendor_id"] == SAMPLE_VENDOR_DATA["vendor_id"]
        assert masked_data["name"] == SAMPLE_VENDOR_DATA["name"]
    
    def test_data_masking_full(self, service):
        """Test full data masking functionality."""
        masked_data = service.mask_sensitive_data(
            SAMPLE_VENDOR_DATA,
            masking_level=DataMaskingLevel.FULL
        )
        
        # Check all sensitive fields are fully masked
        assert masked_data["email"] == "*" * len(SAMPLE_VENDOR_DATA["email"])
        assert masked_data["phone"] == "*" * len(SAMPLE_VENDOR_DATA["phone"])
        assert masked_data["ssn"] == "*" * len(SAMPLE_VENDOR_DATA["ssn"])
        assert masked_data["credit_card"] == "*" * len(SAMPLE_VENDOR_DATA["credit_card"])
    
    def test_data_masking_custom_rules(self, service):
        """Test custom masking rules functionality."""
        custom_rules = {
            "email": DataMaskingRule("email", DataMaskingLevel.FULL, replacement_char="#"),
            "phone": DataMaskingRule("phone", DataMaskingLevel.PARTIAL, replacement_char="X")
        }
        
        masked_data = service.mask_sensitive_data(
            SAMPLE_VENDOR_DATA,
            masking_level=DataMaskingLevel.CUSTOM,
            custom_rules=custom_rules
        )
        
        # Check custom masking applied
        assert masked_data["email"] == "#" * len(SAMPLE_VENDOR_DATA["email"])
        assert masked_data["phone"] == "XXX-XXX-4567"
    
    def test_encryption_and_decryption(self, service):
        """Test data encryption and decryption functionality."""
        # Encrypt sensitive data
        encrypted_data = service.encrypt_sensitive_data(SAMPLE_VENDOR_DATA)
        
        # Check that sensitive fields are encrypted
        assert encrypted_data["email"] != SAMPLE_VENDOR_DATA["email"]
        assert encrypted_data["phone"] != SAMPLE_VENDOR_DATA["phone"]
        assert encrypted_data["ssn"] != SAMPLE_VENDOR_DATA["ssn"]
        
        # Check that non-sensitive fields remain unchanged
        assert encrypted_data["vendor_id"] == SAMPLE_VENDOR_DATA["vendor_id"]
        assert encrypted_data["name"] == SAMPLE_VENDOR_DATA["name"]
        
        # Decrypt the data
        decrypted_data = service.decrypt_sensitive_data(encrypted_data)
        
        # Check that data is restored
        assert decrypted_data["email"] == SAMPLE_VENDOR_DATA["email"]
        assert decrypted_data["phone"] == SAMPLE_VENDOR_DATA["phone"]
        assert decrypted_data["ssn"] == SAMPLE_VENDOR_DATA["ssn"]
        assert decrypted_data["vendor_id"] == SAMPLE_VENDOR_DATA["vendor_id"]
    
    def test_gdpr_compliance_check(self, service):
        """Test GDPR compliance checking."""
        compliance_results = service.check_compliance(
            SAMPLE_VENDOR_DATA,
            ComplianceType.GDPR
        )
        
        assert "compliant" in compliance_results
        assert "warnings" in compliance_results
        assert "errors" in compliance_results
        assert "recommendations" in compliance_results
        
        # Should have warnings about personal data
        assert len(compliance_results["warnings"]) > 0 or len(compliance_results["errors"]) > 0
    
    def test_hipaa_compliance_check(self, service):
        """Test HIPAA compliance checking."""
        compliance_results = service.check_compliance(
            SAMPLE_VENDOR_DATA,
            ComplianceType.HIPAA
        )
        
        assert "compliant" in compliance_results
        assert "warnings" in compliance_results
        assert "errors" in compliance_results
        assert "recommendations" in compliance_results
        
        # Should have errors about PHI
        assert len(compliance_results["errors"]) > 0
    
    def test_audit_logging(self, service):
        """Test audit logging functionality."""
        # Log some events
        service._log_audit_event("test_event", {"test_data": "value"})
        service._log_audit_event("analytics_access", {"vendor_id": "test"})
        
        # Get audit log
        audit_entries = service.get_audit_log()
        
        assert len(audit_entries) >= 2
        
        # Check event types
        event_types = [entry["event_type"] for entry in audit_entries]
        assert "test_event" in event_types
        assert "analytics_access" in event_types
    
    def test_audit_log_filtering(self, service):
        """Test audit log filtering functionality."""
        # Log events with different types
        service._log_audit_event("event_type_1", {"data": "value1"})
        service._log_audit_event("event_type_2", {"data": "value2"})
        service._log_audit_event("event_type_1", {"data": "value3"})
        
        # Filter by event type
        filtered_entries = service.get_audit_log(event_type="event_type_1")
        
        assert len(filtered_entries) >= 2
        for entry in filtered_entries:
            assert entry["event_type"] == "event_type_1"
    
    def test_data_export_json(self, service):
        """Test data export in JSON format."""
        exported_data = service.export_data(
            SAMPLE_VENDOR_DATA,
            export_format="json",
            include_analytics=True,
            mask_sensitive=True
        )
        
        # Parse JSON to verify format
        parsed_data = json.loads(exported_data)
        assert isinstance(parsed_data, dict)
        assert "vendor_id" in parsed_data
        assert "analytics" in parsed_data
    
    def test_data_export_csv(self, service):
        """Test data export in CSV format."""
        exported_data = service.export_data(
            SAMPLE_VENDOR_DATA,
            export_format="csv",
            include_analytics=False,
            mask_sensitive=False
        )
        
        # Check CSV format
        assert exported_data.startswith("vendor_id,name,email")
        assert "test_vendor_001" in exported_data
    
    def test_data_export_xml(self, service):
        """Test data export in XML format."""
        exported_data = service.export_data(
            SAMPLE_VENDOR_DATA,
            export_format="xml",
            include_analytics=False,
            mask_sensitive=False
        )
        
        # Check XML format
        assert exported_data.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert "<data>" in exported_data
        assert "<vendor_id>test_vendor_001</vendor_id>" in exported_data
    
    def test_data_export_yaml(self, service):
        """Test data export in YAML format."""
        exported_data = service.export_data(
            SAMPLE_VENDOR_DATA,
            export_format="yaml",
            include_analytics=False,
            mask_sensitive=False
        )
        
        # Check YAML format
        assert "vendor_id: test_vendor_001" in exported_data
        assert "name: Test Vendor Inc." in exported_data
    
    def test_performance_metrics(self, service):
        """Test performance metrics generation."""
        metrics = service.get_performance_metrics()
        
        assert "analytics_cache_size" in metrics
        assert "masking_rules_count" in metrics
        assert "compliance_configs_count" in metrics
        assert "audit_log_entries" in metrics
        assert "encryption_enabled" in metrics
        assert "service_uptime" in metrics
        
        assert metrics["encryption_enabled"] is True
        assert metrics["masking_rules_count"] > 0
        assert metrics["compliance_configs_count"] > 0
    
    def test_sensitive_field_detection(self, service):
        """Test sensitive field detection functionality."""
        sensitive_fields = ["email", "phone", "ssn", "credit_card", "password"]
        non_sensitive_fields = ["vendor_id", "name", "description", "status"]
        
        for field in sensitive_fields:
            assert service._is_sensitive_field(field) is True
        
        for field in non_sensitive_fields:
            assert service._is_sensitive_field(field) is False
    
    def test_masking_rule_application(self, service):
        """Test specific masking rule applications."""
        # Test email masking
        masked_email = service._mask_email("test@example.com")
        assert masked_email == "t**t@example.com"
        
        # Test phone masking
        masked_phone = service._mask_phone("555-123-4567")
        assert masked_phone == "***-***-4567"
        
        # Test name masking
        masked_name = service._mask_name("John Doe")
        assert masked_name == "John D**"
        
        # Test address masking
        masked_address = service._mask_address("123 Main Street")
        assert masked_address == "123 **** Street"
    
    def test_concurrent_operations(self, service):
        """Test concurrent operations for thread safety."""
        import threading
        import time
        
        results = []
        errors = []
        
        def test_operation(operation_id):
            try:
                # Test analytics
                analytics = service.get_analytics(vendor_id=f"vendor_{operation_id}")
                results.append(f"analytics_{operation_id}")
                
                # Test masking
                masked_data = service.mask_sensitive_data(SAMPLE_VENDOR_DATA)
                results.append(f"masking_{operation_id}")
                
                # Test encryption
                encrypted_data = service.encrypt_sensitive_data(SAMPLE_VENDOR_DATA)
                results.append(f"encryption_{operation_id}")
                
            except Exception as e:
                errors.append(f"Error in operation {operation_id}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent operations: {errors}"
        assert len(results) == 15  # 3 operations * 5 threads
    
    def test_error_handling(self, service):
        """Test error handling for various scenarios."""
        # Test with invalid data
        with pytest.raises(Exception):
            service.get_analytics(vendor_id="invalid_vendor")
        
        # Test with empty data
        empty_data = {}
        masked_data = service.mask_sensitive_data(empty_data)
        assert masked_data == {}
        
        # Test with None values
        data_with_none = {"email": None, "phone": "555-123-4567"}
        masked_data = service.mask_sensitive_data(data_with_none)
        assert masked_data["email"] is None
        assert masked_data["phone"] == "***-***-4567"
    
    def test_cache_functionality(self, service):
        """Test analytics caching functionality."""
        # First call should populate cache
        analytics1 = service.get_analytics(vendor_id="test_vendor")
        
        # Second call should use cache
        analytics2 = service.get_analytics(vendor_id="test_vendor")
        
        # Results should be the same
        assert analytics1.total_records == analytics2.total_records
        assert analytics1.unique_vendors == analytics2.unique_vendors
    
    def test_compliance_config_validation(self, service):
        """Test compliance configuration validation."""
        # Test GDPR config
        gdpr_config = service.compliance_configs[ComplianceType.GDPR]
        assert gdpr_config.enabled is True
        assert gdpr_config.encryption_required is True
        assert gdpr_config.consent_required is True
        
        # Test HIPAA config
        hipaa_config = service.compliance_configs[ComplianceType.HIPAA]
        assert hipaa_config.enabled is True
        assert hipaa_config.audit_logging is True
        assert hipaa_config.encryption_required is True


class TestDataVendorAPIExpansionRouter:
    """Test suite for Data Vendor API Expansion router endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth(self):
        """Mock authentication."""
        with patch('routers.data_vendor_api_expansion.get_current_user') as mock:
            mock_user = Mock()
            mock_user.id = "test_user_id"
            mock.return_value = mock_user
            yield mock
    
    def test_get_analytics_endpoint(self, client, mock_auth):
        """Test analytics endpoint."""
        response = client.get("/api/v1/vendor/analytics?vendor_id=test&time_range=30d")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_records" in data
        assert "unique_vendors" in data
        assert "data_quality_score" in data
        assert "compliance_score" in data
        assert "trends" in data
        assert "predictions" in data
    
    def test_mask_data_endpoint(self, client, mock_auth):
        """Test data masking endpoint."""
        test_data = {
            "email": "test@example.com",
            "phone": "555-123-4567",
            "name": "John Doe"
        }
        
        response = client.post(
            "/api/v1/vendor/mask-data",
            json={
                "data": test_data,
                "masking_level": "partial"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "masked_data" in data
        assert "masking_applied" in data
        assert "metadata" in data
        
        masked_data = data["masked_data"]
        assert masked_data["email"] != test_data["email"]
        assert masked_data["phone"] != test_data["phone"]
    
    def test_encrypt_data_endpoint(self, client, mock_auth):
        """Test data encryption endpoint."""
        test_data = {
            "email": "test@example.com",
            "phone": "555-123-4567",
            "name": "John Doe"
        }
        
        response = client.post(
            "/api/v1/vendor/encrypt-data",
            json={"data": test_data}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "encrypted_data" in data
        assert "encryption_summary" in data
        assert "metadata" in data
        
        encrypted_data = data["encrypted_data"]
        assert encrypted_data["email"] != test_data["email"]
        assert encrypted_data["phone"] != test_data["phone"]
        assert encrypted_data["name"] == test_data["name"]  # Non-sensitive field
    
    def test_compliance_check_endpoint(self, client, mock_auth):
        """Test compliance check endpoint."""
        test_data = {
            "email": "test@example.com",
            "phone": "555-123-4567"
        }
        
        response = client.post(
            "/api/v1/vendor/compliance-check",
            json={
                "data": test_data,
                "compliance_type": "gdpr"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "compliance_results" in data
        assert "compliance_type" in data
        assert "metadata" in data
        
        results = data["compliance_results"]
        assert "compliant" in results
        assert "warnings" in results
        assert "errors" in results
    
    def test_audit_log_endpoint(self, client, mock_auth):
        """Test audit log endpoint."""
        response = client.get("/api/v1/vendor/audit-log?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "audit_entries" in data
        assert "summary" in data
        assert "metadata" in data
    
    def test_export_data_endpoint(self, client, mock_auth):
        """Test data export endpoint."""
        test_data = {
            "vendor_id": "test_vendor",
            "name": "Test Vendor",
            "email": "test@example.com"
        }
        
        response = client.post(
            "/api/v1/vendor/export-data",
            json={
                "data": test_data,
                "export_format": "json",
                "include_analytics": False,
                "mask_sensitive": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "exported_data" in data
        assert "export_summary" in data
        assert "metadata" in data
    
    def test_performance_metrics_endpoint(self, client, mock_auth):
        """Test performance metrics endpoint."""
        response = client.get("/api/v1/vendor/performance-metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "performance_metrics" in data
        assert "service_status" in data
        assert "capabilities" in data
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/vendor/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "checks" in data
    
    def test_supported_formats_endpoint(self, client):
        """Test supported formats endpoint."""
        response = client.get("/api/v1/vendor/supported-formats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "export_formats" in data
        assert "compliance_types" in data
        assert "masking_levels" in data
        
        # Check specific formats
        formats = data["export_formats"]
        assert "json" in formats
        assert "csv" in formats
        assert "xml" in formats
        assert "yaml" in formats
        
        # Check compliance types
        compliance_types = data["compliance_types"]
        assert "gdpr" in compliance_types
        assert "hipaa" in compliance_types
        assert "ccpa" in compliance_types
        assert "sox" in compliance_types


class TestDataVendorAPIExpansionIntegration:
    """Integration tests for Data Vendor API Expansion."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for integration tests."""
        return DataVendorAPIExpansion()
    
    def test_end_to_end_workflow(self, service):
        """Test complete end-to-end workflow."""
        # 1. Get analytics
        analytics = service.get_analytics(vendor_id="test_vendor")
        assert isinstance(analytics, AnalyticsMetrics)
        
        # 2. Mask sensitive data
        masked_data = service.mask_sensitive_data(SAMPLE_VENDOR_DATA)
        assert masked_data["email"] != SAMPLE_VENDOR_DATA["email"]
        
        # 3. Encrypt data
        encrypted_data = service.encrypt_sensitive_data(SAMPLE_VENDOR_DATA)
        assert encrypted_data["email"] != SAMPLE_VENDOR_DATA["email"]
        
        # 4. Check compliance
        compliance_results = service.check_compliance(SAMPLE_VENDOR_DATA, ComplianceType.GDPR)
        assert "compliant" in compliance_results
        
        # 5. Export data
        exported_data = service.export_data(SAMPLE_VENDOR_DATA, export_format="json")
        assert isinstance(exported_data, str)
        
        # 6. Get audit log
        audit_entries = service.get_audit_log()
        assert isinstance(audit_entries, list)
        
        # 7. Get performance metrics
        metrics = service.get_performance_metrics()
        assert isinstance(metrics, dict)
    
    def test_large_dataset_handling(self, service):
        """Test handling of large datasets."""
        # Create large dataset
        large_data = {}
        for i in range(1000):
            large_data[f"field_{i}"] = f"value_{i}"
        
        # Add some sensitive fields
        large_data["email"] = "test@example.com"
        large_data["phone"] = "555-123-4567"
        
        # Test masking
        masked_data = service.mask_sensitive_data(large_data)
        assert len(masked_data) == 1002  # 1000 + email + phone
        assert masked_data["email"] != large_data["email"]
        
        # Test encryption
        encrypted_data = service.encrypt_sensitive_data(large_data)
        assert len(encrypted_data) == 1002
        assert encrypted_data["email"] != large_data["email"]
        
        # Test export
        exported_data = service.export_data(large_data, export_format="json")
        assert len(exported_data) > 0
    
    def test_concurrent_user_scenario(self, service):
        """Test scenario with multiple concurrent users."""
        import threading
        import time
        
        results = []
        
        def user_workflow(user_id):
            """Simulate user workflow."""
            try:
                # User gets analytics
                analytics = service.get_analytics(vendor_id=f"vendor_{user_id}")
                
                # User masks their data
                user_data = {
                    "email": f"user{user_id}@example.com",
                    "phone": f"555-{user_id:03d}-4567",
                    "name": f"User {user_id}"
                }
                masked_data = service.mask_sensitive_data(user_data)
                
                # User checks compliance
                compliance = service.check_compliance(user_data, ComplianceType.GDPR)
                
                # User exports data
                exported = service.export_data(user_data, export_format="json")
                
                results.append({
                    "user_id": user_id,
                    "analytics": analytics.total_records,
                    "masked_email": masked_data["email"],
                    "compliant": compliance["compliant"],
                    "exported_size": len(exported)
                })
                
            except Exception as e:
                results.append({"user_id": user_id, "error": str(e)})
        
        # Create multiple user threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=user_workflow, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        successful_results = [r for r in results if "error" not in r]
        assert len(successful_results) == 10
        
        for result in successful_results:
            assert result["analytics"] >= 0
            assert result["masked_email"] != f"user{result['user_id']}@example.com"
            assert "compliant" in result
            assert result["exported_size"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 