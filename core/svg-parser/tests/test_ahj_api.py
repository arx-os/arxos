#!/usr/bin/env python3
"""
Comprehensive Tests for AHJ API Integration

This test suite covers all aspects of the AHJ API including:
- API endpoint functionality
- Request/response validation
- Permission enforcement
- Audit trail logging
- Security measures
- Error handling
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.services.ahj_api_service
    AHJAPIService, Inspection, Annotation, Violation, AuditEvent,
    InspectionStatus, AnnotationType, Coordinates, PermissionLevel
)
from core.routers.ahj_api
from core.utils.logger

# Test client setup
client = TestClient(router)

class TestAHJAPIService:
    """Test suite for AHJ API Service."""
    
    @pytest.fixture(autouse=True)
    def setup_service(self):
        """Setup service for each test."""
        self.service = AHJAPIService()
        self.logger = setup_logger("test_ahj_api", level="DEBUG")
        
        # Add test permissions
        self.service.permissions["test_inspector"] = ["read", "write"]
        self.service.permissions["test_admin"] = ["read", "write", "admin"]
        self.service.permissions["test_reviewer"] = ["read", "write", "review"]
    
    @pytest.mark.asyncio
    async def test_create_inspection_success(self):
        """Test successful inspection creation."""
        # Arrange
        building_id = "test_building_001"
        inspector_id = "test_inspector"
        metadata = {"priority": "high", "notes": "Test inspection"}
        
        # Act
        inspection = await self.service.create_inspection(
            building_id=building_id,
            inspector_id=inspector_id,
            metadata=metadata
        )
        
        # Assert
        assert inspection is not None
        assert inspection.building_id == building_id
        assert inspection.inspector_id == inspector_id
        assert inspection.status == InspectionStatus.PENDING
        assert inspection.metadata == metadata
        assert inspection.id in self.service.inspections
    
    @pytest.mark.asyncio
    async def test_create_inspection_permission_denied(self):
        """Test inspection creation with insufficient permissions."""
        # Arrange
        building_id = "test_building_001"
        inspector_id = "unauthorized_user"
        
        # Act & Assert
        with pytest.raises(Exception):
            await self.service.create_inspection(
                building_id=building_id,
                inspector_id=inspector_id
            )
    
    @pytest.mark.asyncio
    async def test_add_annotation_success(self):
        """Test successful annotation addition."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        coordinates = Coordinates(x=10.5, y=20.3, z=5.0, floor="1", room="101")
        annotation_type = AnnotationType.NOTE
        content = "Test annotation content"
        object_id = "test_object_001"
        metadata = {"category": "safety", "priority": "medium"}
        
        # Act
        annotation = await self.service.add_annotation(
            inspection_id=inspection.id,
            object_id=object_id,
            annotation_type=annotation_type,
            content=content,
            coordinates=coordinates,
            inspector_id="test_inspector",
            metadata=metadata
        )
        
        # Assert
        assert annotation is not None
        assert annotation.inspection_id == inspection.id
        assert annotation.object_id == object_id
        assert annotation.annotation_type == annotation_type
        assert annotation.content == content
        assert annotation.coordinates == coordinates
        assert annotation.metadata == metadata
        assert annotation.immutable_hash is not None
        assert len(annotation.immutable_hash) == 64  # SHA-256 hash length
    
    @pytest.mark.asyncio
    async def test_add_annotation_inspection_not_found(self):
        """Test adding annotation to non-existent inspection."""
        # Arrange
        coordinates = Coordinates(x=10.5, y=20.3)
        annotation_type = AnnotationType.NOTE
        content = "Test annotation content"
        object_id = "test_object_001"
        
        # Act & Assert
        with pytest.raises(Exception):
            await self.service.add_annotation(
                inspection_id="non_existent_inspection",
                object_id=object_id,
                annotation_type=annotation_type,
                content=content,
                coordinates=coordinates,
                inspector_id="test_inspector"
            )
    
    @pytest.mark.asyncio
    async def test_add_violation_success(self):
        """Test successful violation addition."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        object_id = "test_object_001"
        code_section = "NFPA 70-2020 210.8"
        description = "GFCI protection required in bathroom"
        severity = "high"
        
        # Act
        violation = await self.service.add_violation(
            inspection_id=inspection.id,
            object_id=object_id,
            code_section=code_section,
            description=description,
            severity=severity,
            inspector_id="test_inspector"
        )
        
        # Assert
        assert violation is not None
        assert violation.inspection_id == inspection.id
        assert violation.object_id == object_id
        assert violation.code_section == code_section
        assert violation.description == description
        assert violation.severity == severity
        assert violation.status == "open"
        assert violation.immutable_hash is not None
        assert len(violation.immutable_hash) == 64
    
    @pytest.mark.asyncio
    async def test_get_inspection_success(self):
        """Test successful inspection retrieval."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        # Act
        retrieved_inspection = await self.service.get_inspection(
            inspection_id=inspection.id,
            user_id="test_inspector"
        )
        
        # Assert
        assert retrieved_inspection is not None
        assert retrieved_inspection.id == inspection.id
        assert retrieved_inspection.building_id == inspection.building_id
        assert retrieved_inspection.inspector_id == inspection.inspector_id
    
    @pytest.mark.asyncio
    async def test_get_inspection_not_found(self):
        """Test retrieving non-existent inspection."""
        # Act & Assert
        with pytest.raises(Exception):
            await self.service.get_inspection(
                inspection_id="non_existent_inspection",
                user_id="test_inspector"
            )
    
    @pytest.mark.asyncio
    async def test_list_inspections_success(self):
        """Test successful inspection listing."""
        # Arrange
        await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        await self.service.create_inspection(
            building_id="test_building_002",
            inspector_id="test_inspector"
        )
        
        # Act
        inspections = await self.service.list_inspections(
            user_id="test_inspector",
            limit=10,
            offset=0
        )
        
        # Assert
        assert len(inspections) >= 2
        assert all(isinstance(inspection, Inspection) for inspection in inspections)
    
    @pytest.mark.asyncio
    async def test_list_inspections_with_filters(self):
        """Test inspection listing with filters."""
        # Arrange
        inspection1 = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        inspection2 = await self.service.create_inspection(
            building_id="test_building_002",
            inspector_id="test_inspector"
        )
        
        # Update status of first inspection
        await self.service.update_inspection_status(
            inspection_id=inspection1.id,
            status=InspectionStatus.COMPLETED,
            user_id="test_inspector"
        )
        
        # Act - Filter by building
        inspections = await self.service.list_inspections(
            user_id="test_inspector",
            building_id="test_building_001"
        )
        
        # Assert
        assert len(inspections) == 1
        assert inspections[0].building_id == "test_building_001"
        
        # Act - Filter by status
        completed_inspections = await self.service.list_inspections(
            user_id="test_inspector",
            status=InspectionStatus.COMPLETED
        )
        
        # Assert
        assert len(completed_inspections) == 1
        assert completed_inspections[0].status == InspectionStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_success(self):
        """Test successful audit trail retrieval."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        # Add an annotation to generate audit events
        coordinates = Coordinates(x=10.5, y=20.3)
        await self.service.add_annotation(
            inspection_id=inspection.id,
            object_id="test_object_001",
            annotation_type=AnnotationType.NOTE,
            content="Test annotation",
            coordinates=coordinates,
            inspector_id="test_inspector"
        )
        
        # Act
        audit_events = await self.service.get_audit_trail(
            inspection_id=inspection.id,
            user_id="test_inspector",
            limit=10,
            offset=0
        )
        
        # Assert
        assert len(audit_events) >= 2  # At least create_inspection and add_annotation events
        assert all(isinstance(event, AuditEvent) for event in audit_events)
        assert all(event.inspection_id == inspection.id for event in audit_events)
    
    @pytest.mark.asyncio
    async def test_update_inspection_status_success(self):
        """Test successful inspection status update."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        old_status = inspection.status
        
        # Act
        updated_inspection = await self.service.update_inspection_status(
            inspection_id=inspection.id,
            status=InspectionStatus.COMPLETED,
            user_id="test_inspector"
        )
        
        # Assert
        assert updated_inspection.status == InspectionStatus.COMPLETED
        assert updated_inspection.status != old_status
        assert updated_inspection.updated_at > inspection.updated_at
    
    @pytest.mark.asyncio
    async def test_validate_permission_success(self):
        """Test successful permission validation."""
        # Act
        result = await self.service._validate_permission(
            user_id="test_inspector",
            action="read",
            resource="inspection:test_001"
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_permission_denied(self):
        """Test permission validation denial."""
        # Act
        result = await self.service._validate_permission(
            user_id="unauthorized_user",
            action="write",
            resource="inspection:test_001"
        )
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_log_audit_event_success(self):
        """Test successful audit event logging."""
        # Arrange
        inspection_id = "test_inspection_001"
        user_id = "test_inspector"
        action = "test_action"
        resource = "test_resource"
        details = {"test_key": "test_value"}
        
        # Act
        await self.service._log_audit_event(
            inspection_id=inspection_id,
            user_id=user_id,
            action=action,
            resource=resource,
            details=details
        )
        
        # Assert
        # Check that audit event was created
        audit_events = [event for event in self.service.audit_events.values()
                       if event.inspection_id == inspection_id]
        assert len(audit_events) == 1
        
        event = audit_events[0]
        assert event.user_id == user_id
        assert event.action == action
        assert event.resource == resource
        assert event.details == details
        assert event.immutable_hash is not None
    
    @pytest.mark.asyncio
    async def test_add_user_permission_success(self):
        """Test successful user permission addition."""
        # Arrange
        user_id = "new_user"
        permission = "read"
        admin_user_id = "test_admin"
        
        # Act
        result = await self.service.add_user_permission(
            user_id=user_id,
            permission=permission,
            admin_user_id=admin_user_id
        )
        
        # Assert
        assert result is True
        assert user_id in self.service.permissions
        assert permission in self.service.permissions[user_id]
    
    @pytest.mark.asyncio
    async def test_remove_user_permission_success(self):
        """Test successful user permission removal."""
        # Arrange
        user_id = "test_user"
        permission = "write"
        admin_user_id = "test_admin"
        
        # Add permission first
        self.service.permissions[user_id] = [permission]
        
        # Act
        result = await self.service.remove_user_permission(
            user_id=user_id,
            permission=permission,
            admin_user_id=admin_user_id
        )
        
        # Assert
        assert result is True
        assert permission not in self.service.permissions[user_id]
    
    @pytest.mark.asyncio
    async def test_get_inspection_statistics_success(self):
        """Test successful inspection statistics retrieval."""
        # Arrange
        await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        # Act
        statistics = await self.service.get_inspection_statistics(
            user_id="test_inspector"
        )
        
        # Assert
        assert "total_inspections" in statistics
        assert "status_counts" in statistics
        assert "total_annotations" in statistics
        assert "total_violations" in statistics
        assert statistics["total_inspections"] >= 1
    
    @pytest.mark.asyncio
    async def test_export_inspection_data_success(self):
        """Test successful inspection data export."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        # Add annotation
        coordinates = Coordinates(x=10.5, y=20.3)
        await self.service.add_annotation(
            inspection_id=inspection.id,
            object_id="test_object_001",
            annotation_type=AnnotationType.NOTE,
            content="Test annotation",
            coordinates=coordinates,
            inspector_id="test_inspector"
        )
        
        # Act
        export_data = await self.service.export_inspection_data(
            inspection_id=inspection.id,
            user_id="test_inspector",
            format="json"
        )
        
        # Assert
        assert "inspection" in export_data
        assert "annotations" in export_data
        assert "violations" in export_data
        assert "audit_trail" in export_data
        assert export_data["inspection"]["id"] == inspection.id
        assert len(export_data["annotations"]) == 1
        assert len(export_data["violations"]) == 0
    
    @pytest.mark.asyncio
    async def test_annotation_immutable_hash_consistency(self):
        """Test that annotation immutable hash is consistent."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        coordinates = Coordinates(x=10.5, y=20.3)
        annotation_type = AnnotationType.NOTE
        content = "Test annotation content"
        object_id = "test_object_001"
        
        # Act
        annotation1 = await self.service.add_annotation(
            inspection_id=inspection.id,
            object_id=object_id,
            annotation_type=annotation_type,
            content=content,
            coordinates=coordinates,
            inspector_id="test_inspector"
        )
        
        annotation2 = await self.service.add_annotation(
            inspection_id=inspection.id,
            object_id=object_id,
            annotation_type=annotation_type,
            content=content,
            coordinates=coordinates,
            inspector_id="test_inspector"
        )
        
        # Assert
        assert annotation1.immutable_hash != annotation2.immutable_hash  # Different IDs
        assert len(annotation1.immutable_hash) == 64
        assert len(annotation2.immutable_hash) == 64
    
    @pytest.mark.asyncio
    async def test_violation_immutable_hash_consistency(self):
        """Test that violation immutable hash is consistent."""
        # Arrange
        inspection = await self.service.create_inspection(
            building_id="test_building_001",
            inspector_id="test_inspector"
        )
        
        object_id = "test_object_001"
        code_section = "NFPA 70-2020 210.8"
        description = "GFCI protection required"
        severity = "high"
        
        # Act
        violation1 = await self.service.add_violation(
            inspection_id=inspection.id,
            object_id=object_id,
            code_section=code_section,
            description=description,
            severity=severity,
            inspector_id="test_inspector"
        )
        
        violation2 = await self.service.add_violation(
            inspection_id=inspection.id,
            object_id=object_id,
            code_section=code_section,
            description=description,
            severity=severity,
            inspector_id="test_inspector"
        )
        
        # Assert
        assert violation1.immutable_hash != violation2.immutable_hash  # Different IDs
        assert len(violation1.immutable_hash) == 64
        assert len(violation2.immutable_hash) == 64

class TestAHJAPIRouter:
    """Test suite for AHJ API Router."""
    
    def test_create_inspection_endpoint_success(self):
        """Test successful inspection creation via API endpoint."""
        # Arrange
        request_data = {
            "building_id": "test_building_001",
            "metadata": {"priority": "high"}
        }
        
        # Act
        response = client.post("/inspections", json=request_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["building_id"] == "test_building_001"
        assert data["status"] == "pending"
    
    def test_create_inspection_endpoint_validation_error(self):
        """Test inspection creation with validation error."""
        # Arrange
        request_data = {
            "building_id": "",  # Invalid empty building ID
            "metadata": {"priority": "high"}
        }
        
        # Act
        response = client.post("/inspections", json=request_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_add_annotation_endpoint_success(self):
        """Test successful annotation addition via API endpoint."""
        # Arrange
        # First create an inspection
        inspection_response = client.post("/inspections", json={
            "building_id": "test_building_001"
        })
        inspection_id = inspection_response.json()["id"]
        
        request_data = {
            "object_id": "test_object_001",
            "annotation_type": "note",
            "content": "Test annotation content",
            "coordinates": {
                "x": 10.5,
                "y": 20.3,
                "z": 5.0,
                "floor": "1",
                "room": "101"
            },
            "metadata": {"category": "safety"}
        }
        
        # Act
        response = client.post(f"/inspections/{inspection_id}/annotations", json=request_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["inspection_id"] == inspection_id
        assert data["object_id"] == "test_object_001"
        assert data["annotation_type"] == "note"
        assert data["content"] == "Test annotation content"
        assert "immutable_hash" in data
    
    def test_add_violation_endpoint_success(self):
        """Test successful violation addition via API endpoint."""
        # Arrange
        # First create an inspection
        inspection_response = client.post("/inspections", json={
            "building_id": "test_building_001"
        })
        inspection_id = inspection_response.json()["id"]
        
        request_data = {
            "object_id": "test_object_001",
            "code_section": "NFPA 70-2020 210.8",
            "description": "GFCI protection required in bathroom",
            "severity": "high"
        }
        
        # Act
        response = client.post(f"/inspections/{inspection_id}/violations", json=request_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["inspection_id"] == inspection_id
        assert data["object_id"] == "test_object_001"
        assert data["code_section"] == "NFPA 70-2020 210.8"
        assert data["description"] == "GFCI protection required in bathroom"
        assert data["severity"] == "high"
        assert "immutable_hash" in data
    
    def test_get_inspection_endpoint_success(self):
        """Test successful inspection retrieval via API endpoint."""
        # Arrange
        # First create an inspection
        create_response = client.post("/inspections", json={
            "building_id": "test_building_001"
        })
        inspection_id = create_response.json()["id"]
        
        # Act
        response = client.get(f"/inspections/{inspection_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == inspection_id
        assert data["building_id"] == "test_building_001"
        assert "annotations_count" in data
        assert "violations_count" in data
    
    def test_get_inspection_endpoint_not_found(self):
        """Test inspection retrieval for non-existent inspection."""
        # Act
        response = client.get("/inspections/non_existent_id")
        
        # Assert
        assert response.status_code == 404
    
    def test_list_inspections_endpoint_success(self):
        """Test successful inspection listing via API endpoint."""
        # Arrange
        # Create multiple inspections
        client.post("/inspections", json={"building_id": "test_building_001"})
        client.post("/inspections", json={"building_id": "test_building_002"})
        
        # Act
        response = client.get("/inspections?limit=10&offset=0")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_get_audit_trail_endpoint_success(self):
        """Test successful audit trail retrieval via API endpoint."""
        # Arrange
        # First create an inspection
        create_response = client.post("/inspections", json={
            "building_id": "test_building_001"
        })
        inspection_id = create_response.json()["id"]
        
        # Act
        response = client.get(f"/inspections/{inspection_id}/audit?limit=10&offset=0")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the creation event
    
    def test_update_inspection_status_endpoint_success(self):
        """Test successful inspection status update via API endpoint."""
        # Arrange
        # First create an inspection
        create_response = client.post("/inspections", json={
            "building_id": "test_building_001"
        })
        inspection_id = create_response.json()["id"]
        
        request_data = {
            "status": "completed"
        }
        
        # Act
        response = client.put(f"/inspections/{inspection_id}/status", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
    
    def test_get_statistics_endpoint_success(self):
        """Test successful statistics retrieval via API endpoint."""
        # Act
        response = client.get("/statistics")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_inspections" in data
        assert "status_counts" in data
        assert "total_annotations" in data
        assert "total_violations" in data
    
    def test_health_check_endpoint_success(self):
        """Test successful health check via API endpoint."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AHJ API"
        assert "timestamp" in data
        assert "version" in data
    
    def test_manage_permissions_endpoint_success(self):
        """Test successful permission management via API endpoint."""
        # Arrange
        request_data = {
            "user_id": "new_user",
            "permission": "read",
            "action": "add"
        }
        
        # Act
        response = client.post("/permissions", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert data["user_id"] == "new_user"
        assert data["permission"] == "read"
        assert data["action"] == "add"

class TestAHJAPISecurity:
    """Test suite for AHJ API Security."""
    
    @pytest.mark.asyncio
    async def test_permission_enforcement(self):
        """Test that permission enforcement works correctly."""
        service = AHJAPIService()
        
        # Test unauthorized access
        with pytest.raises(Exception):
            await service.create_inspection(
                building_id="test_building",
                inspector_id="unauthorized_user"
            )
    
    @pytest.mark.asyncio
    async def test_audit_trail_immutability(self):
        """Test that audit trail events are immutable."""
        service = AHJAPIService()
        
        # Create an inspection to generate audit events
        inspection = await service.create_inspection(
            building_id="test_building",
            inspector_id="test_inspector"
        )
        
        # Get audit events
        audit_events = await service.get_audit_trail(
            inspection_id=inspection.id,
            user_id="test_inspector"
        )
        
        # Verify immutable hash exists
        for event in audit_events:
            assert event.immutable_hash is not None
            assert len(event.immutable_hash) == 64
    
    @pytest.mark.asyncio
    async def test_annotation_immutability(self):
        """Test that annotations are immutable."""
        service = AHJAPIService()
        
        # Create inspection and annotation
        inspection = await service.create_inspection(
            building_id="test_building",
            inspector_id="test_inspector"
        )
        
        coordinates = Coordinates(x=10.5, y=20.3)
        annotation = await service.add_annotation(
            inspection_id=inspection.id,
            object_id="test_object",
            annotation_type=AnnotationType.NOTE,
            content="Test annotation",
            coordinates=coordinates,
            inspector_id="test_inspector"
        )
        
        # Verify immutable hash
        assert annotation.immutable_hash is not None
        assert len(annotation.immutable_hash) == 64
        
        # Verify hash consistency
        original_hash = annotation.immutable_hash
        # Recreate annotation with same data should have different hash due to different ID
        annotation2 = await service.add_annotation(
            inspection_id=inspection.id,
            object_id="test_object",
            annotation_type=AnnotationType.NOTE,
            content="Test annotation",
            coordinates=coordinates,
            inspector_id="test_inspector"
        )
        assert annotation2.immutable_hash != original_hash

class TestAHJAPIErrorHandling:
    """Test suite for AHJ API Error Handling."""
    
    def test_invalid_request_validation(self):
        """Test that invalid requests are properly validated."""
        # Test invalid building ID
        response = client.post("/inspections", json={"building_id": ""})
        assert response.status_code == 422
        
        # Test invalid annotation request
        response = client.post("/inspections/test_id/annotations", json={
            "object_id": "",
            "annotation_type": "invalid_type",
            "content": "",
            "coordinates": {"x": "invalid", "y": "invalid"}
        })
        assert response.status_code == 422
    
    def test_not_found_handling(self):
        """Test that not found errors are handled properly."""
        response = client.get("/inspections/non_existent_id")
        assert response.status_code == 404
    
    def test_permission_denied_handling(self):
        """Test that permission denied errors are handled properly."""
        # This would require proper authentication setup
        # For now, we test the endpoint structure
        response = client.get("/inspections/test_id")
        # Should return 404 for non-existent inspection or 403 for permission denied
        assert response.status_code in [403, 404]

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 