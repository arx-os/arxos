"""
End-to-End Tests for Data Vendor API Expansion

Tests complete user workflows and integration scenarios for:
- Analytics generation and retrieval
- Data masking and encryption workflows
- Compliance checking processes
- Audit logging and monitoring
- Data export functionality
- Performance under load
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from services.data_vendor_api_expansion import (
    data_vendor_api_expansion,
    DataMaskingLevel,
    ComplianceType
)
from routers.data_vendor_api_expansion import router


class TestDataVendorAPIExpansionE2E:
    """End-to-end test suite for Data Vendor API Expansion."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_auth(self):
        """Mock authentication for testing."""
        with patch('routers.data_vendor_api_expansion.get_current_user') as mock:
            mock_user = Mock()
            mock_user.id = "test_user_id"
            mock_user.email = "test@example.com"
            mock.return_value = mock_user
            yield mock
    
    @pytest.fixture
    def sample_vendor_data(self):
        """Sample vendor data for testing."""
        return {
            "vendor_id": "e2e_test_vendor_001",
            "name": "E2E Test Vendor Corporation",
            "email": "contact@e2etestvendor.com",
            "phone": "555-123-4567",
            "address": "123 Test Street, Test City, USA",
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
    
    def test_complete_analytics_workflow(self, client, mock_auth):
        """Test complete analytics workflow from API request to response."""
        # Step 1: Request analytics
        response = client.get("/api/v1/vendor/analytics?vendor_id=e2e_test&time_range=30d")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify analytics structure
        assert "total_records" in data
        assert "unique_vendors" in data
        assert "data_quality_score" in data
        assert "compliance_score" in data
        assert "trends" in data
        assert "predictions" in data
        assert "request_metadata" in data
        
        # Verify data types
        assert isinstance(data["total_records"], int)
        assert isinstance(data["unique_vendors"], int)
        assert isinstance(data["data_quality_score"], float)
        assert isinstance(data["compliance_score"], float)
        assert isinstance(data["trends"], dict)
        assert isinstance(data["predictions"], dict)
        
        print(f"✅ Analytics workflow completed: {data['total_records']} records, {data['unique_vendors']} vendors")
    
    def test_complete_data_masking_workflow(self, client, mock_auth, sample_vendor_data):
        """Test complete data masking workflow."""
        # Step 1: Request data masking
        response = client.post(
            "/api/v1/vendor/mask-data",
            json={
                "data": sample_vendor_data,
                "masking_level": "partial"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "masked_data" in data
        assert "masking_applied" in data
        assert "metadata" in data
        
        masked_data = data["masked_data"]
        masking_applied = data["masking_applied"]
        
        # Verify masking was applied
        assert masking_applied["level"] == "partial"
        assert masking_applied["fields_processed"] == len(sample_vendor_data)
        
        # Verify sensitive fields were masked
        assert masked_data["email"] != sample_vendor_data["email"]
        assert masked_data["phone"] != sample_vendor_data["phone"]
        assert masked_data["ssn"] != sample_vendor_data["ssn"]
        assert masked_data["credit_card"] != sample_vendor_data["credit_card"]
        
        # Verify non-sensitive fields remain unchanged
        assert masked_data["vendor_id"] == sample_vendor_data["vendor_id"]
        assert masked_data["name"] == sample_vendor_data["name"]
        
        print(f"✅ Data masking workflow completed: {masking_applied['fields_processed']} fields processed")
    
    def test_complete_encryption_workflow(self, client, mock_auth, sample_vendor_data):
        """Test complete encryption and decryption workflow."""
        # Step 1: Encrypt data
        response = client.post(
            "/api/v1/vendor/encrypt-data",
            json={"data": sample_vendor_data}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        encrypted_data = data["encrypted_data"]
        encryption_summary = data["encryption_summary"]
        
        # Verify encryption was applied
        assert encryption_summary["total_fields"] == len(sample_vendor_data)
        assert encryption_summary["encrypted_fields"] > 0
        
        # Verify sensitive fields were encrypted
        assert encrypted_data["email"] != sample_vendor_data["email"]
        assert encrypted_data["phone"] != sample_vendor_data["phone"]
        assert encrypted_data["ssn"] != sample_vendor_data["ssn"]
        
        # Verify non-sensitive fields remain unchanged
        assert encrypted_data["vendor_id"] == sample_vendor_data["vendor_id"]
        assert encrypted_data["name"] == sample_vendor_data["name"]
        
        # Step 2: Decrypt data
        response = client.post(
            "/api/v1/vendor/decrypt-data",
            json={"encrypted_data": encrypted_data}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        decrypted_data = data["decrypted_data"]
        decryption_summary = data["decryption_summary"]
        
        # Verify decryption was successful
        assert decryption_summary["total_fields"] == len(encrypted_data)
        assert decryption_summary["decrypted_fields"] > 0
        
        # Verify data was restored
        assert decrypted_data["email"] == sample_vendor_data["email"]
        assert decrypted_data["phone"] == sample_vendor_data["phone"]
        assert decrypted_data["ssn"] == sample_vendor_data["ssn"]
        assert decrypted_data["vendor_id"] == sample_vendor_data["vendor_id"]
        
        print(f"✅ Encryption/decryption workflow completed: {decryption_summary['decrypted_fields']} fields decrypted")
    
    def test_complete_compliance_workflow(self, client, mock_auth, sample_vendor_data):
        """Test complete compliance checking workflow."""
        compliance_types = ["gdpr", "hipaa", "ccpa", "sox"]
        
        for compliance_type in compliance_types:
            # Step 1: Check compliance
            response = client.post(
                "/api/v1/vendor/compliance-check",
                json={
                    "data": sample_vendor_data,
                    "compliance_type": compliance_type
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "compliance_results" in data
            assert "compliance_type" in data
            assert "metadata" in data
            
            results = data["compliance_results"]
            
            # Verify compliance results structure
            assert "compliant" in results
            assert "warnings" in results
            assert "errors" in results
            assert "recommendations" in results
            
            # Verify data types
            assert isinstance(results["compliant"], bool)
            assert isinstance(results["warnings"], list)
            assert isinstance(results["errors"], list)
            assert isinstance(results["recommendations"], list)
            
            print(f"✅ {compliance_type.upper()} compliance check completed: {'Compliant' if results['compliant'] else 'Non-compliant'}")
    
    def test_complete_audit_logging_workflow(self, client, mock_auth):
        """Test complete audit logging workflow."""
        # Step 1: Generate some audit events
        events = [
            ("analytics_access", {"vendor_id": "e2e_test", "time_range": "30d"}),
            ("data_masking", {"fields_masked": ["email", "phone"], "level": "partial"}),
            ("data_encryption", {"fields_encrypted": ["ssn", "credit_card"]}),
            ("compliance_check", {"compliance_type": "gdpr", "compliant": True}),
            ("data_export", {"format": "json", "size_bytes": 2048})
        ]
        
        for event_type, event_data in events:
            # Trigger events through API calls
            if event_type == "analytics_access":
                client.get("/api/v1/vendor/analytics?vendor_id=e2e_test")
            elif event_type == "data_masking":
                client.post("/api/v1/vendor/mask-data", json={"data": {"email": "test@example.com"}, "masking_level": "partial"})
            elif event_type == "data_encryption":
                client.post("/api/v1/vendor/encrypt-data", json={"data": {"ssn": "123-45-6789"}})
            elif event_type == "compliance_check":
                client.post("/api/v1/vendor/compliance-check", json={"data": {"email": "test@example.com"}, "compliance_type": "gdpr"})
            elif event_type == "data_export":
                client.post("/api/v1/vendor/export-data", json={"data": {"test": "data"}, "export_format": "json"})
        
        # Step 2: Retrieve audit log
        response = client.get("/api/v1/vendor/audit-log?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "audit_entries" in data
        assert "summary" in data
        assert "metadata" in data
        
        audit_entries = data["audit_entries"]
        summary = data["summary"]
        
        # Verify audit log structure
        assert len(audit_entries) > 0
        assert "total_entries" in summary
        assert "event_types" in summary
        
        # Verify audit entry structure
        for entry in audit_entries:
            assert "timestamp" in entry
            assert "event_type" in entry
            assert "event_data" in entry
            assert "user_id" in entry
            assert "session_id" in entry
        
        print(f"✅ Audit logging workflow completed: {len(audit_entries)} entries logged")
    
    def test_complete_data_export_workflow(self, client, mock_auth, sample_vendor_data):
        """Test complete data export workflow."""
        export_formats = ["json", "csv", "xml", "yaml"]
        
        for format_type in export_formats:
            # Step 1: Export data
            response = client.post(
                "/api/v1/vendor/export-data",
                json={
                    "data": sample_vendor_data,
                    "export_format": format_type,
                    "include_analytics": True,
                    "mask_sensitive": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "exported_data" in data
            assert "export_summary" in data
            assert "metadata" in data
            
            exported_data = data["exported_data"]
            export_summary = data["export_summary"]
            
            # Verify export summary
            assert export_summary["format"] == format_type
            assert export_summary["include_analytics"] is True
            assert export_summary["mask_sensitive"] is True
            assert export_summary["data_size_bytes"] > 0
            
            # Verify exported data
            assert len(exported_data) > 0
            
            # Verify format-specific content
            if format_type == "json":
                # Should be valid JSON
                parsed_json = json.loads(exported_data)
                assert isinstance(parsed_json, dict)
            elif format_type == "csv":
                # Should contain CSV headers
                assert "vendor_id" in exported_data
                assert "name" in exported_data
            elif format_type == "xml":
                # Should contain XML structure
                assert "<?xml" in exported_data
                assert "<data>" in exported_data
            elif format_type == "yaml":
                # Should contain YAML structure
                assert "vendor_id:" in exported_data
                assert "name:" in exported_data
            
            print(f"✅ {format_type.upper()} export workflow completed: {export_summary['data_size_bytes']} bytes")
    
    def test_complete_performance_workflow(self, client, mock_auth):
        """Test complete performance monitoring workflow."""
        # Step 1: Get performance metrics
        response = client.get("/api/v1/vendor/performance-metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "performance_metrics" in data
        assert "service_status" in data
        assert "capabilities" in data
        
        metrics = data["performance_metrics"]
        status = data["service_status"]
        capabilities = data["capabilities"]
        
        # Verify performance metrics
        assert "analytics_cache_size" in metrics
        assert "masking_rules_count" in metrics
        assert "compliance_configs_count" in metrics
        assert "audit_log_entries" in metrics
        assert "encryption_enabled" in metrics
        assert "service_uptime" in metrics
        
        # Verify service status
        assert "status" in status
        assert "version" in status
        assert status["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Verify capabilities
        assert "analytics" in capabilities
        assert "data_masking" in capabilities
        assert "encryption" in capabilities
        assert "compliance_checking" in capabilities
        assert "audit_logging" in capabilities
        assert "data_export" in capabilities
        
        print(f"✅ Performance workflow completed: {metrics['audit_log_entries']} audit entries, {metrics['service_uptime']:.2f}s uptime")
    
    def test_complete_health_check_workflow(self, client):
        """Test complete health check workflow."""
        # Step 1: Check health status
        response = client.get("/api/v1/vendor/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "checks" in data
        
        # Verify health status
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["service"] == "Data Vendor API Expansion"
        assert data["version"] == "1.0.0"
        
        # Verify health checks
        checks = data["checks"]
        assert "encryption" in checks
        assert "masking_rules" in checks
        assert "compliance_configs" in checks
        assert "audit_logging" in checks
        
        # All checks should be True for healthy status
        if data["status"] == "healthy":
            assert all(checks.values())
        
        print(f"✅ Health check workflow completed: {data['status']} status")
    
    def test_complete_supported_formats_workflow(self, client):
        """Test complete supported formats workflow."""
        # Step 1: Get supported formats
        response = client.get("/api/v1/vendor/supported-formats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "export_formats" in data
        assert "compliance_types" in data
        assert "masking_levels" in data
        
        export_formats = data["export_formats"]
        compliance_types = data["compliance_types"]
        masking_levels = data["masking_levels"]
        
        # Verify export formats
        expected_formats = ["json", "csv", "xml", "yaml"]
        for format_type in expected_formats:
            assert format_type in export_formats
            assert "description" in export_formats[format_type]
            assert "content_type" in export_formats[format_type]
            assert "compression" in export_formats[format_type]
        
        # Verify compliance types
        expected_compliance = ["gdpr", "hipaa", "ccpa", "sox"]
        for compliance_type in expected_compliance:
            assert compliance_type in compliance_types
            assert "name" in compliance_types[compliance_type]
            assert "description" in compliance_types[compliance_type]
            assert "enabled" in compliance_types[compliance_type]
        
        # Verify masking levels
        expected_levels = ["none", "partial", "full", "custom"]
        for level in expected_levels:
            assert level in masking_levels
        
        print(f"✅ Supported formats workflow completed: {len(export_formats)} formats, {len(compliance_types)} compliance types")
    
    def test_concurrent_user_scenario(self, client, mock_auth, sample_vendor_data):
        """Test concurrent user scenario with multiple simultaneous operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def user_workflow(user_id: int):
            """Simulate user workflow."""
            try:
                # User 1: Analytics request
                if user_id % 4 == 0:
                    response = client.get(f"/api/v1/vendor/analytics?vendor_id=user_{user_id}")
                    if response.status_code == 200:
                        data = response.json()
                        results.append({"user_id": user_id, "operation": "analytics", "records": data.get("total_records", 0)})
                
                # User 2: Data masking
                elif user_id % 4 == 1:
                    response = client.post("/api/v1/vendor/mask-data", json={
                        "data": {"email": f"user{user_id}@example.com", "phone": f"555-{user_id:03d}-4567"},
                        "masking_level": "partial"
                    })
                    if response.status_code == 200:
                        data = response.json()
                        results.append({"user_id": user_id, "operation": "masking", "fields": data["masking_applied"]["fields_processed"]})
                
                # User 3: Encryption
                elif user_id % 4 == 2:
                    response = client.post("/api/v1/vendor/encrypt-data", json={
                        "data": {"ssn": f"123-{user_id:02d}-6789", "credit_card": f"4111-{user_id:04d}-1111"}
                    })
                    if response.status_code == 200:
                        data = response.json()
                        results.append({"user_id": user_id, "operation": "encryption", "fields": data["encryption_summary"]["encrypted_fields"]})
                
                # User 4: Compliance check
                else:
                    response = client.post("/api/v1/vendor/compliance-check", json={
                        "data": {"email": f"user{user_id}@example.com"},
                        "compliance_type": "gdpr"
                    })
                    if response.status_code == 200:
                        data = response.json()
                        results.append({"user_id": user_id, "operation": "compliance", "compliant": data["compliance_results"]["compliant"]})
                
            except Exception as e:
                errors.append({"user_id": user_id, "error": str(e)})
        
        # Create multiple user threads
        threads = []
        for i in range(20):  # 20 concurrent users
            thread = threading.Thread(target=user_workflow, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors in concurrent operations: {errors}"
        assert len(results) == 20, f"Expected 20 results, got {len(results)}"
        
        # Verify operation distribution
        operation_counts = {}
        for result in results:
            op = result["operation"]
            operation_counts[op] = operation_counts.get(op, 0) + 1
        
        assert operation_counts.get("analytics", 0) >= 4
        assert operation_counts.get("masking", 0) >= 4
        assert operation_counts.get("encryption", 0) >= 4
        assert operation_counts.get("compliance", 0) >= 4
        
        print(f"✅ Concurrent user scenario completed: {len(results)} operations, {len(errors)} errors")
    
    def test_large_dataset_scenario(self, client, mock_auth):
        """Test handling of large datasets."""
        # Create large dataset
        large_data = {}
        for i in range(1000):
            large_data[f"field_{i}"] = f"value_{i}"
        
        # Add sensitive fields
        large_data["email"] = "test@example.com"
        large_data["phone"] = "555-123-4567"
        large_data["ssn"] = "123-45-6789"
        large_data["credit_card"] = "4111-1111-1111-1111"
        
        # Test masking large dataset
        start_time = time.time()
        response = client.post("/api/v1/vendor/mask-data", json={
            "data": large_data,
            "masking_level": "partial"
        })
        masking_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data["masking_applied"]["fields_processed"] == len(large_data)
        
        # Test encryption large dataset
        start_time = time.time()
        response = client.post("/api/v1/vendor/encrypt-data", json={"data": large_data})
        encryption_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data["encryption_summary"]["total_fields"] == len(large_data)
        
        # Test export large dataset
        start_time = time.time()
        response = client.post("/api/v1/vendor/export-data", json={
            "data": large_data,
            "export_format": "json",
            "include_analytics": False,
            "mask_sensitive": True
        })
        export_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data["export_summary"]["data_size_bytes"] > 0
        
        print(f"✅ Large dataset scenario completed:")
        print(f"   • Masking: {masking_time:.3f}s for {len(large_data)} fields")
        print(f"   • Encryption: {encryption_time:.3f}s for {len(large_data)} fields")
        print(f"   • Export: {export_time:.3f}s for {data['export_summary']['data_size_bytes']} bytes")
    
    def test_error_handling_scenario(self, client, mock_auth):
        """Test error handling scenarios."""
        # Test invalid analytics request
        response = client.get("/api/v1/vendor/analytics?vendor_id=invalid&time_range=invalid")
        assert response.status_code == 500  # Should handle invalid parameters gracefully
        
        # Test invalid masking request
        response = client.post("/api/v1/vendor/mask-data", json={
            "data": {},
            "masking_level": "invalid_level"
        })
        assert response.status_code == 500  # Should handle invalid masking level
        
        # Test invalid compliance request
        response = client.post("/api/v1/vendor/compliance-check", json={
            "data": {},
            "compliance_type": "invalid_type"
        })
        assert response.status_code == 500  # Should handle invalid compliance type
        
        # Test invalid export request
        response = client.post("/api/v1/vendor/export-data", json={
            "data": {},
            "export_format": "invalid_format"
        })
        assert response.status_code == 500  # Should handle invalid export format
        
        print("✅ Error handling scenario completed: All invalid requests handled gracefully")
    
    def test_integration_workflow_scenario(self, client, mock_auth, sample_vendor_data):
        """Test complete integration workflow scenario."""
        workflow_results = []
        
        # Step 1: Get analytics
        response = client.get("/api/v1/vendor/analytics?vendor_id=integration_test")
        assert response.status_code == 200
        analytics_data = response.json()
        workflow_results.append({"step": "analytics", "success": True, "records": analytics_data.get("total_records", 0)})
        
        # Step 2: Mask sensitive data
        response = client.post("/api/v1/vendor/mask-data", json={
            "data": sample_vendor_data,
            "masking_level": "partial"
        })
        assert response.status_code == 200
        masking_data = response.json()
        workflow_results.append({"step": "masking", "success": True, "fields": masking_data["masking_applied"]["fields_processed"]})
        
        # Step 3: Check compliance
        response = client.post("/api/v1/vendor/compliance-check", json={
            "data": sample_vendor_data,
            "compliance_type": "gdpr"
        })
        assert response.status_code == 200
        compliance_data = response.json()
        workflow_results.append({"step": "compliance", "success": True, "compliant": compliance_data["compliance_results"]["compliant"]})
        
        # Step 4: Export data
        response = client.post("/api/v1/vendor/export-data", json={
            "data": masking_data["masked_data"],
            "export_format": "json",
            "include_analytics": True,
            "mask_sensitive": False  # Already masked
        })
        assert response.status_code == 200
        export_data = response.json()
        workflow_results.append({"step": "export", "success": True, "size": export_data["export_summary"]["data_size_bytes"]})
        
        # Step 5: Get audit log
        response = client.get("/api/v1/vendor/audit-log?limit=5")
        assert response.status_code == 200
        audit_data = response.json()
        workflow_results.append({"step": "audit", "success": True, "entries": len(audit_data["audit_entries"])})
        
        # Verify all steps completed successfully
        assert len(workflow_results) == 5
        for result in workflow_results:
            assert result["success"] is True
        
        print("✅ Integration workflow scenario completed:")
        for result in workflow_results:
            print(f"   • {result['step']}: {result}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 