"""
Tests for Access Control Service
Tests role-based permissions, floor-specific access controls, audit trails, and permission inheritance
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from arx_svg_parser.services.access_control import (
    AccessControlService, UserRole, ResourceType, ActionType, 
    PermissionLevel, User, Permission, AuditLog, RoleHierarchy
)

class TestAccessControlService:
    """Test cases for AccessControlService"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def access_control(self, temp_db):
        """Create AccessControlService instance with temporary database"""
        return AccessControlService(db_path=temp_db)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "primary_role": UserRole.CONTRACTOR,
            "secondary_roles": [UserRole.INSPECTOR],
            "organization": "Test Corp"
        }
    
    @pytest.fixture
    def sample_permission_data(self):
        """Sample permission data for testing"""
        return {
            "role": UserRole.CONTRACTOR,
            "resource_type": ResourceType.FLOOR,
            "resource_id": "floor_001",
            "permission_level": PermissionLevel.WRITE,
            "floor_id": "floor_001",
            "building_id": "building_001"
        }

    def test_init_database(self, temp_db):
        """Test database initialization"""
        service = AccessControlService(db_path=temp_db)
        
        # Check if tables were created
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['users', 'permissions', 'audit_logs', 'role_hierarchy']
        for table in expected_tables:
            assert table in tables
        
        conn.close()

    def test_init_role_hierarchy(self, access_control):
        """Test role hierarchy initialization"""
        conn = sqlite3.connect(access_control.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT role FROM role_hierarchy")
        roles = [row[0] for row in cursor.fetchall()]
        
        # Check if all expected roles are present
        expected_roles = [
            'owner', 'admin', 'management', 'architect', 'engineer',
            'contractor', 'inspector', 'tenant', 'team'
        ]
        
        for role in expected_roles:
            assert role in roles
        
        conn.close()

    def test_create_user_success(self, access_control, sample_user_data):
        """Test successful user creation"""
        result = access_control.create_user(**sample_user_data)
        
        assert result["success"] is True
        assert "user_id" in result
        
        # Verify user was created in database
        conn = sqlite3.connect(access_control.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, email, primary_role FROM users WHERE user_id = ?", 
                      (result["user_id"],))
        user_data = cursor.fetchone()
        
        assert user_data is not None
        assert user_data[0] == sample_user_data["username"]
        assert user_data[1] == sample_user_data["email"]
        assert user_data[2] == sample_user_data["primary_role"].value
        
        conn.close()

    def test_create_user_duplicate_username(self, access_control, sample_user_data):
        """Test user creation with duplicate username"""
        # Create first user
        result1 = access_control.create_user(**sample_user_data)
        assert result1["success"] is True
        
        # Try to create second user with same username
        result2 = access_control.create_user(**sample_user_data)
        assert result2["success"] is False
        assert "duplicate" in result2["message"].lower()

    def test_get_user_success(self, access_control, sample_user_data):
        """Test successful user retrieval"""
        # Create user first
        create_result = access_control.create_user(**sample_user_data)
        user_id = create_result["user_id"]
        
        # Get user
        result = access_control.get_user(user_id)
        
        assert result["success"] is True
        assert result["user"]["username"] == sample_user_data["username"]
        assert result["user"]["email"] == sample_user_data["email"]
        assert result["user"]["primary_role"] == sample_user_data["primary_role"].value

    def test_get_user_not_found(self, access_control):
        """Test user retrieval for non-existent user"""
        result = access_control.get_user("nonexistent_id")
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_grant_permission_success(self, access_control, sample_permission_data):
        """Test successful permission granting"""
        result = access_control.grant_permission(**sample_permission_data)
        
        assert result["success"] is True
        assert "permission_id" in result
        
        # Verify permission was created in database
        conn = sqlite3.connect(access_control.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT role, resource_type, permission_level FROM permissions WHERE permission_id = ?", 
                      (result["permission_id"],))
        perm_data = cursor.fetchone()
        
        assert perm_data is not None
        assert perm_data[0] == sample_permission_data["role"].value
        assert perm_data[1] == sample_permission_data["resource_type"].value
        assert perm_data[2] == sample_permission_data["permission_level"].value
        
        conn.close()

    def test_grant_permission_with_expiry(self, access_control, sample_permission_data):
        """Test permission granting with expiry date"""
        expires_at = datetime.utcnow() + timedelta(days=30)
        sample_permission_data["expires_at"] = expires_at
        
        result = access_control.grant_permission(**sample_permission_data)
        
        assert result["success"] is True
        
        # Verify expiry date was saved
        conn = sqlite3.connect(access_control.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT expires_at FROM permissions WHERE permission_id = ?", 
                      (result["permission_id"],))
        saved_expiry = cursor.fetchone()[0]
        
        assert saved_expiry is not None
        assert datetime.fromisoformat(saved_expiry) == expires_at
        
        conn.close()

    def test_revoke_permission_success(self, access_control, sample_permission_data):
        """Test successful permission revocation"""
        # Grant permission first
        grant_result = access_control.grant_permission(**sample_permission_data)
        permission_id = grant_result["permission_id"]
        
        # Revoke permission
        result = access_control.revoke_permission(permission_id)
        
        assert result["success"] is True
        
        # Verify permission was removed from database
        conn = sqlite3.connect(access_control.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM permissions WHERE permission_id = ?", (permission_id,))
        count = cursor.fetchone()[0]
        
        assert count == 0
        
        conn.close()

    def test_revoke_permission_not_found(self, access_control):
        """Test permission revocation for non-existent permission"""
        result = access_control.revoke_permission("nonexistent_id")
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_check_permission_success(self, access_control, sample_user_data, sample_permission_data):
        """Test successful permission check"""
        # Create user
        user_result = access_control.create_user(**sample_user_data)
        user_id = user_result["user_id"]
        
        # Grant permission
        access_control.grant_permission(**sample_permission_data)
        
        # Check permission
        result = access_control.check_permission(
            user_id=user_id,
            resource_type=ResourceType.FLOOR,
            action=ActionType.UPDATE,
            resource_id="floor_001",
            floor_id="floor_001",
            building_id="building_001"
        )
        
        assert result["success"] is True
        assert result["permission"] is not None

    def test_check_permission_insufficient(self, access_control, sample_user_data):
        """Test permission check with insufficient permissions"""
        # Create user with limited role
        user_data = sample_user_data.copy()
        user_data["primary_role"] = UserRole.TEAM
        
        user_result = access_control.create_user(**user_data)
        user_id = user_result["user_id"]
        
        # Check permission for action requiring higher level
        result = access_control.check_permission(
            user_id=user_id,
            resource_type=ResourceType.FLOOR,
            action=ActionType.DELETE,
            resource_id="floor_001"
        )
        
        assert result["success"] is False
        assert "insufficient" in result["message"].lower()

    def test_check_permission_inheritance(self, access_control, sample_user_data):
        """Test permission inheritance from parent roles"""
        # Create user with role that inherits permissions
        user_data = sample_user_data.copy()
        user_data["primary_role"] = UserRole.ENGINEER  # Inherits from CONTRACTOR
        
        user_result = access_control.create_user(**user_data)
        user_id = user_result["user_id"]
        
        # Grant permission to parent role (CONTRACTOR)
        access_control.grant_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            permission_level=PermissionLevel.WRITE
        )
        
        # Check if ENGINEER inherits the permission
        result = access_control.check_permission(
            user_id=user_id,
            resource_type=ResourceType.FLOOR,
            action=ActionType.UPDATE
        )
        
        assert result["success"] is True

    def test_log_audit_event_success(self, access_control):
        """Test successful audit event logging"""
        result = access_control.log_audit_event(
            user_id="test_user",
            action=ActionType.CREATE,
            resource_type=ResourceType.FLOOR,
            resource_id="floor_001",
            details={"test": "data"},
            ip_address="192.168.1.1",
            user_agent="test-agent"
        )
        
        assert result["success"] is True
        assert "log_id" in result
        
        # Verify audit log was created
        conn = sqlite3.connect(access_control.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, action, resource_type FROM audit_logs WHERE log_id = ?", 
                      (result["log_id"],))
        log_data = cursor.fetchone()
        
        assert log_data is not None
        assert log_data[0] == "test_user"
        assert log_data[1] == ActionType.CREATE.value
        assert log_data[2] == ResourceType.FLOOR.value
        
        conn.close()

    def test_log_audit_event_failure(self, access_control):
        """Test audit event logging for failed action"""
        result = access_control.log_audit_event(
            user_id="test_user",
            action=ActionType.DELETE,
            resource_type=ResourceType.FLOOR,
            resource_id="floor_001",
            success=False,
            error_message="Permission denied"
        )
        
        assert result["success"] is True
        
        # Verify failure was logged
        conn = sqlite3.connect(access_control.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT success, error_message FROM audit_logs WHERE log_id = ?", 
                      (result["log_id"],))
        log_data = cursor.fetchone()
        
        assert log_data[0] == 0  # False
        assert log_data[1] == "Permission denied"
        
        conn.close()

    def test_get_audit_logs_with_filters(self, access_control):
        """Test audit log retrieval with filters"""
        # Create multiple audit logs
        access_control.log_audit_event(
            user_id="user1",
            action=ActionType.CREATE,
            resource_type=ResourceType.FLOOR,
            resource_id="floor_001"
        )
        
        access_control.log_audit_event(
            user_id="user2",
            action=ActionType.UPDATE,
            resource_type=ResourceType.BUILDING,
            resource_id="building_001"
        )
        
        # Get logs filtered by user
        result = access_control.get_audit_logs(user_id="user1")
        
        assert result["success"] is True
        assert len(result["logs"]) == 1
        assert result["logs"][0]["user_id"] == "user1"

    def test_get_floor_permissions(self, access_control, sample_permission_data):
        """Test floor permissions retrieval"""
        # Grant multiple permissions for the same floor
        floor_id = "floor_001"
        building_id = "building_001"
        
        # Grant permission to CONTRACTOR
        access_control.grant_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            permission_level=PermissionLevel.WRITE,
            floor_id=floor_id,
            building_id=building_id
        )
        
        # Grant permission to INSPECTOR
        access_control.grant_permission(
            role=UserRole.INSPECTOR,
            resource_type=ResourceType.ANNOTATION,
            permission_level=PermissionLevel.WRITE,
            floor_id=floor_id,
            building_id=building_id
        )
        
        # Get floor permissions
        result = access_control.get_floor_permissions(floor_id, building_id)
        
        assert result["success"] is True
        assert len(result["permissions"]) == 2
        
        # Verify both permissions are for the correct floor
        for permission in result["permissions"]:
            assert permission["floor_id"] == floor_id
            assert permission["building_id"] == building_id

    def test_get_required_permission_level(self, access_control):
        """Test required permission level calculation"""
        # Test different actions
        assert access_control._get_required_permission_level(ActionType.READ) == PermissionLevel.READ
        assert access_control._get_required_permission_level(ActionType.CREATE) == PermissionLevel.WRITE
        assert access_control._get_required_permission_level(ActionType.UPDATE) == PermissionLevel.WRITE
        assert access_control._get_required_permission_level(ActionType.DELETE) == PermissionLevel.ADMIN
        assert access_control._get_required_permission_level(ActionType.APPROVE) == PermissionLevel.ADMIN

    def test_get_role_permission_specific_resource(self, access_control, sample_permission_data):
        """Test getting permission for specific resource"""
        # Grant permission for specific resource
        access_control.grant_permission(**sample_permission_data)
        
        # Get permission for that specific resource
        permission = access_control._get_role_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            resource_id="floor_001"
        )
        
        assert permission is not None
        assert permission.resource_id == "floor_001"
        assert permission.permission_level == PermissionLevel.WRITE

    def test_get_role_permission_floor_specific(self, access_control):
        """Test getting floor-specific permission"""
        # Grant floor-specific permission
        access_control.grant_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            permission_level=PermissionLevel.WRITE,
            floor_id="floor_001",
            building_id="building_001"
        )
        
        # Get permission for that floor
        permission = access_control._get_role_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            floor_id="floor_001",
            building_id="building_001"
        )
        
        assert permission is not None
        assert permission.floor_id == "floor_001"
        assert permission.building_id == "building_001"

    def test_get_role_permission_general(self, access_control):
        """Test getting general resource type permission"""
        # Grant general permission
        access_control.grant_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            permission_level=PermissionLevel.READ
        )
        
        # Get general permission
        permission = access_control._get_role_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR
        )
        
        assert permission is not None
        assert permission.resource_id is None
        assert permission.floor_id is None
        assert permission.building_id is None

    def test_get_inherited_permission(self, access_control):
        """Test permission inheritance from parent roles"""
        # Grant permission to parent role (CONTRACTOR)
        access_control.grant_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            permission_level=PermissionLevel.WRITE
        )
        
        # Check if ENGINEER (child of CONTRACTOR) inherits the permission
        permission = access_control._get_inherited_permission(
            role=UserRole.ENGINEER,
            resource_type=ResourceType.FLOOR
        )
        
        assert permission is not None
        assert permission.role == UserRole.CONTRACTOR

    def test_permission_expiry(self, access_control):
        """Test permission expiry functionality"""
        # Grant permission with past expiry date
        past_expiry = datetime.utcnow() - timedelta(days=1)
        access_control.grant_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR,
            permission_level=PermissionLevel.WRITE,
            expires_at=past_expiry
        )
        
        # Try to get the expired permission
        permission = access_control._get_role_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.FLOOR
        )
        
        # Should not return expired permission
        assert permission is None

    def test_row_to_permission(self, access_control):
        """Test database row to Permission object conversion"""
        # Create a sample row
        row = (
            "perm_001",
            "contractor",
            "floor",
            "floor_001",
            2,  # WRITE level
            "floor_001",
            "building_001",
            "2023-01-01T00:00:00",
            "2023-12-31T23:59:59",
            '{"test": "data"}'
        )
        
        permission = access_control._row_to_permission(row)
        
        assert permission.permission_id == "perm_001"
        assert permission.role == UserRole.CONTRACTOR
        assert permission.resource_type == ResourceType.FLOOR
        assert permission.resource_id == "floor_001"
        assert permission.permission_level == PermissionLevel.WRITE
        assert permission.floor_id == "floor_001"
        assert permission.building_id == "building_001"
        assert permission.metadata == {"test": "data"}

    def test_complex_permission_scenario(self, access_control):
        """Test complex permission scenario with multiple users and resources"""
        # Create multiple users
        user1 = access_control.create_user(
            username="architect1",
            email="arch1@example.com",
            primary_role=UserRole.ARCHITECT
        )
        
        user2 = access_control.create_user(
            username="contractor1",
            email="cont1@example.com",
            primary_role=UserRole.CONTRACTOR
        )
        
        user3 = access_control.create_user(
            username="inspector1",
            email="insp1@example.com",
            primary_role=UserRole.INSPECTOR
        )
        
        # Grant different permissions
        access_control.grant_permission(
            role=UserRole.ARCHITECT,
            resource_type=ResourceType.FLOOR,
            permission_level=PermissionLevel.WRITE
        )
        
        access_control.grant_permission(
            role=UserRole.CONTRACTOR,
            resource_type=ResourceType.ANNOTATION,
            permission_level=PermissionLevel.WRITE
        )
        
        access_control.grant_permission(
            role=UserRole.INSPECTOR,
            resource_type=ResourceType.COMMENT,
            permission_level=PermissionLevel.WRITE
        )
        
        # Test permission checks
        assert access_control.check_permission(
            user_id=user1["user_id"],
            resource_type=ResourceType.FLOOR,
            action=ActionType.UPDATE
        )["success"] is True
        
        assert access_control.check_permission(
            user_id=user2["user_id"],
            resource_type=ResourceType.ANNOTATION,
            action=ActionType.CREATE
        )["success"] is True
        
        assert access_control.check_permission(
            user_id=user3["user_id"],
            resource_type=ResourceType.COMMENT,
            action=ActionType.UPDATE
        )["success"] is True
        
        # Test denied permissions
        assert access_control.check_permission(
            user_id=user1["user_id"],
            resource_type=ResourceType.FLOOR,
            action=ActionType.DELETE
        )["success"] is False

    def test_audit_trail_completeness(self, access_control):
        """Test audit trail captures all necessary information"""
        # Perform various actions
        access_control.log_audit_event(
            user_id="test_user",
            action=ActionType.CREATE,
            resource_type=ResourceType.FLOOR,
            resource_id="floor_001",
            floor_id="floor_001",
            building_id="building_001",
            details={"operation": "floor_creation"},
            ip_address="192.168.1.100",
            user_agent="test-browser"
        )
        
        # Retrieve audit logs
        result = access_control.get_audit_logs(user_id="test_user")
        
        assert result["success"] is True
        assert len(result["logs"]) == 1
        
        log = result["logs"][0]
        assert log["user_id"] == "test_user"
        assert log["action"] == ActionType.CREATE.value
        assert log["resource_type"] == ResourceType.FLOOR.value
        assert log["resource_id"] == "floor_001"
        assert log["floor_id"] == "floor_001"
        assert log["building_id"] == "building_001"
        assert log["details"] == {"operation": "floor_creation"}
        assert log["ip_address"] == "192.168.1.100"
        assert log["user_agent"] == "test-browser"
        assert log["success"] is True

if __name__ == "__main__":
    pytest.main([__file__]) 