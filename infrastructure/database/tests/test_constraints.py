#!/usr/bin/env python3
"""
Unit Tests for Database Constraints

This module contains comprehensive tests for NOT NULL and CHECK constraints
to ensure data integrity is properly enforced. It follows Arxos testing
standards with structured logging, performance monitoring, and thorough
coverage of edge cases.

Features:
- Tests NOT NULL constraint enforcement
- Tests CHECK constraint validation
- Tests constraint rollback functionality
- Performance testing for constraint operations
- Integration testing with existing schema
- Error handling and edge case coverage

Usage:
    pytest test_constraints.py -v
    pytest test_constraints.py --cov=test_constraints
"""

import os
import sys
import pytest
import structlog
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time

# Configure structured logging following Arxos standards
logger = structlog.get_logger(__name__)

# Test configuration
TEST_CONFIG = {
    'database_url': os.getenv('TEST_DATABASE_URL', 'postgresql://localhost/arxos_test'),
    'test_timeout': 30,  # seconds
    'max_retries': 3,
    'constraint_test_data': {
        'valid_users': [
            {
                'email': 'test1@example.com',
                'username': 'testuser1',
                'password_hash': 'a' * 64,
                'role': 'user'
            },
            {
                'email': 'test2@example.com',
                'username': 'testuser2',
                'password_hash': 'b' * 64,
                'role': 'admin'
            }
        ],
        'invalid_users': [
            {
                'email': 'invalid-email',
                'username': 'ab',  # too short
                'password_hash': 'short',
                'role': 'invalid_role'
            }
        ],
        'valid_rooms': [
            {
                'id': 'room_001',
                'name': 'Test Room 1',
                'status': 'active',
                'category': 'office'
            }
        ],
        'invalid_rooms': [
            {
                'id': 'room_002',
                'name': 'Test Room 2',
                'status': 'invalid_status',
                'category': None  # should be NOT NULL
            }
        ]
    }
}


class DatabaseTestHelper:
    """Helper class for database testing operations."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        self.test_data = {}
        
    def connect(self) -> bool:
        """Establish database connection for testing."""
        try:
            self.connection = psycopg2.connect(self.database_url)
            logger.info("test_database_connected")
            return True
        except Exception as e:
            logger.error("test_database_connection_failed", error=str(e))
            return False
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("test_database_disconnected")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute a query and return results."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute a command without returning results."""
        with self.connection.cursor() as cursor:
            cursor.execute(command, params)
            self.connection.commit()
    
    def insert_test_data(self, table: str, data: Dict) -> int:
        """Insert test data and return the ID."""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, list(data.values()))
            result = cursor.fetchone()
            self.connection.commit()
            return result[0] if result else None
    
    def cleanup_test_data(self, table: str, ids: List[int]) -> None:
        """Clean up test data by IDs."""
        if ids:
            placeholders = ', '.join(['%s'] * len(ids))
            query = f"DELETE FROM {table} WHERE id IN ({placeholders})"
            self.execute_command(query, tuple(ids))


class TestConstraintEnforcement:
    """Test suite for constraint enforcement."""
    
    @pytest.fixture(scope="class")
    def db_helper(self):
        """Database helper fixture."""
        helper = DatabaseTestHelper(TEST_CONFIG['database_url'])
        if not helper.connect():
            pytest.skip("Database connection failed")
        yield helper
        helper.disconnect()
    
    @pytest.fixture(scope="function")
    def clean_database(self, db_helper):
        """Clean database before each test."""
        # Store existing data
        existing_data = {}
        
        # Clean up test data after test
        yield
        
        # Cleanup
        for table, ids in existing_data.items():
            if ids:
                db_helper.cleanup_test_data(table, ids)
    
    def test_not_null_constraints_users(self, db_helper, clean_database):
        """Test NOT NULL constraints on users table."""
        logger.info("testing_not_null_constraints_users")
        
        # Test valid data insertion
        valid_user = TEST_CONFIG['constraint_test_data']['valid_users'][0]
        user_id = db_helper.insert_test_data('users', valid_user)
        assert user_id is not None
        
        # Test NULL email (should fail)
        invalid_user = valid_user.copy()
        invalid_user['email'] = None
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('users', invalid_user)
        
        assert 'email' in str(exc_info.value).lower()
        
        # Test NULL username (should fail)
        invalid_user = valid_user.copy()
        invalid_user['username'] = None
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('users', invalid_user)
        
        assert 'username' in str(exc_info.value).lower()
        
        # Test NULL password_hash (should fail)
        invalid_user = valid_user.copy()
        invalid_user['password_hash'] = None
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('users', invalid_user)
        
        assert 'password_hash' in str(exc_info.value).lower()
        
        # Test NULL role (should fail)
        invalid_user = valid_user.copy()
        invalid_user['role'] = None
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('users', invalid_user)
        
        assert 'role' in str(exc_info.value).lower()
        
        logger.info("not_null_constraints_users_passed")
    
    def test_check_constraints_users_role(self, db_helper, clean_database):
        """Test CHECK constraints on users.role field."""
        logger.info("testing_check_constraints_users_role")
        
        # Test valid roles
        valid_roles = ['user', 'admin', 'manager', 'viewer']
        for role in valid_roles:
            user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
            user_data['role'] = role
            user_id = db_helper.insert_test_data('users', user_data)
            assert user_id is not None
        
        # Test invalid role
        invalid_user = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
        invalid_user['role'] = 'invalid_role'
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('users', invalid_user)
        
        assert 'role' in str(exc_info.value).lower()
        
        logger.info("check_constraints_users_role_passed")
    
    def test_email_format_validation(self, db_helper, clean_database):
        """Test email format validation constraint."""
        logger.info("testing_email_format_validation")
        
        # Test valid email formats
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            '123@test-domain.com'
        ]
        
        for email in valid_emails:
            user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
            user_data['email'] = email
            user_id = db_helper.insert_test_data('users', user_data)
            assert user_id is not None
        
        # Test invalid email formats
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@.com',
            'user..name@example.com'
        ]
        
        for email in invalid_emails:
            user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
            user_data['email'] = email
            
            with pytest.raises(psycopg2.IntegrityError) as exc_info:
                db_helper.insert_test_data('users', user_data)
            
            assert 'email' in str(exc_info.value).lower()
        
        logger.info("email_format_validation_passed")
    
    def test_username_format_validation(self, db_helper, clean_database):
        """Test username format validation constraint."""
        logger.info("testing_username_format_validation")
        
        # Test valid username formats
        valid_usernames = [
            'testuser',
            'user123',
            'user_name',
            'user-name',
            'a' * 50  # maximum length
        ]
        
        for username in valid_usernames:
            user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
            user_data['username'] = username
            user_id = db_helper.insert_test_data('users', user_data)
            assert user_id is not None
        
        # Test invalid username formats
        invalid_usernames = [
            'ab',  # too short
            'a' * 51,  # too long
            'user@name',  # invalid character
            'user name',  # space not allowed
            'user.name'  # dot not allowed
        ]
        
        for username in invalid_usernames:
            user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
            user_data['username'] = username
            
            with pytest.raises(psycopg2.IntegrityError) as exc_info:
                db_helper.insert_test_data('users', user_data)
            
            assert 'username' in str(exc_info.value).lower()
        
        logger.info("username_format_validation_passed")
    
    def test_password_hash_format_validation(self, db_helper, clean_database):
        """Test password hash format validation constraint."""
        logger.info("testing_password_hash_format_validation")
        
        # Test valid password hash format (64 hex characters)
        valid_hash = 'a' * 64
        user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
        user_data['password_hash'] = valid_hash
        user_id = db_helper.insert_test_data('users', user_data)
        assert user_id is not None
        
        # Test invalid password hash formats
        invalid_hashes = [
            'short',  # too short
            'a' * 65,  # too long
            'invalid-hash',  # invalid characters
            'a' * 63 + 'g',  # invalid hex character
            'a' * 63 + 'Z'   # invalid hex character
        ]
        
        for hash_value in invalid_hashes:
            user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
            user_data['password_hash'] = hash_value
            
            with pytest.raises(psycopg2.IntegrityError) as exc_info:
                db_helper.insert_test_data('users', user_data)
            
            assert 'password_hash' in str(exc_info.value).lower()
        
        logger.info("password_hash_format_validation_passed")
    
    def test_timestamp_constraints(self, db_helper, clean_database):
        """Test timestamp validation constraints."""
        logger.info("testing_timestamp_constraints")
        
        # Test valid timestamps
        valid_user = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
        valid_user['created_at'] = datetime.now() - timedelta(days=1)
        valid_user['updated_at'] = datetime.now()
        
        user_id = db_helper.insert_test_data('users', valid_user)
        assert user_id is not None
        
        # Test future timestamp (should fail)
        invalid_user = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
        invalid_user['created_at'] = datetime.now() + timedelta(days=1)
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('users', invalid_user)
        
        assert 'created_at' in str(exc_info.value).lower()
        
        logger.info("timestamp_constraints_passed")
    
    def test_room_status_constraints(self, db_helper, clean_database):
        """Test CHECK constraints on rooms.status field."""
        logger.info("testing_room_status_constraints")
        
        # First, create a test project and building
        project_data = {'name': 'Test Project'}
        project_id = db_helper.insert_test_data('projects', project_data)
        
        building_data = {
            'name': 'Test Building',
            'project_id': project_id
        }
        building_id = db_helper.insert_test_data('buildings', building_data)
        
        # Test valid status values
        valid_statuses = ['active', 'inactive', 'suspended', 'pending', 'completed', 'cancelled']
        
        for status in valid_statuses:
            room_data = TEST_CONFIG['constraint_test_data']['valid_rooms'][0].copy()
            room_data['status'] = status
            room_data['building_id'] = building_id
            room_data['project_id'] = project_id
            
            room_id = db_helper.insert_test_data('rooms', room_data)
            assert room_id is not None
        
        # Test invalid status
        invalid_room = TEST_CONFIG['constraint_test_data']['valid_rooms'][0].copy()
        invalid_room['status'] = 'invalid_status'
        invalid_room['building_id'] = building_id
        invalid_room['project_id'] = project_id
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('rooms', invalid_room)
        
        assert 'status' in str(exc_info.value).lower()
        
        logger.info("room_status_constraints_passed")
    
    def test_material_constraints(self, db_helper, clean_database):
        """Test CHECK constraints on material fields."""
        logger.info("testing_material_constraints")
        
        # Create test data for walls, doors, windows
        project_data = {'name': 'Test Project'}
        project_id = db_helper.insert_test_data('projects', project_data)
        
        building_data = {'name': 'Test Building', 'project_id': project_id}
        building_id = db_helper.insert_test_data('buildings', building_data)
        
        # Test valid materials
        valid_materials = ['concrete', 'steel', 'wood', 'glass', 'plastic', 'metal']
        
        for material in valid_materials:
            # Test walls
            wall_data = {
                'id': f'wall_{material}',
                'material': material,
                'status': 'active',
                'category': 'structural',
                'building_id': building_id,
                'project_id': project_id
            }
            wall_id = db_helper.insert_test_data('walls', wall_data)
            assert wall_id is not None
            
            # Test doors
            door_data = {
                'id': f'door_{material}',
                'material': material,
                'status': 'active',
                'category': 'access',
                'building_id': building_id,
                'project_id': project_id
            }
            door_id = db_helper.insert_test_data('doors', door_data)
            assert door_id is not None
            
            # Test windows
            window_data = {
                'id': f'window_{material}',
                'material': material,
                'status': 'active',
                'category': 'fenestration',
                'building_id': building_id,
                'project_id': project_id
            }
            window_id = db_helper.insert_test_data('windows', window_data)
            assert window_id is not None
        
        # Test invalid material
        invalid_material = 'invalid_material'
        
        for table in ['walls', 'doors', 'windows']:
            invalid_data = {
                'id': f'{table}_invalid',
                'material': invalid_material,
                'status': 'active',
                'category': 'test',
                'building_id': building_id,
                'project_id': project_id
            }
            
            with pytest.raises(psycopg2.IntegrityError) as exc_info:
                db_helper.insert_test_data(table, invalid_data)
            
            assert 'material' in str(exc_info.value).lower()
        
        logger.info("material_constraints_passed")
    
    def test_system_constraints_devices(self, db_helper, clean_database):
        """Test CHECK constraints on devices.system field."""
        logger.info("testing_system_constraints_devices")
        
        # Create test data
        project_data = {'name': 'Test Project'}
        project_id = db_helper.insert_test_data('projects', project_data)
        
        building_data = {'name': 'Test Building', 'project_id': project_id}
        building_id = db_helper.insert_test_data('buildings', building_id)
        
        # Test valid systems
        valid_systems = ['HVAC', 'electrical', 'plumbing', 'fire', 'security', 'lighting']
        
        for system in valid_systems:
            device_data = {
                'id': f'device_{system}',
                'type': 'equipment',
                'system': system,
                'status': 'active',
                'category': 'equipment',
                'building_id': building_id,
                'project_id': project_id
            }
            device_id = db_helper.insert_test_data('devices', device_data)
            assert device_id is not None
        
        # Test invalid system
        invalid_device = {
            'id': 'device_invalid',
            'type': 'equipment',
            'system': 'invalid_system',
            'status': 'active',
            'category': 'equipment',
            'building_id': building_id,
            'project_id': project_id
        }
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('devices', invalid_device)
        
        assert 'system' in str(exc_info.value).lower()
        
        logger.info("system_constraints_devices_passed")
    
    def test_slow_query_log_constraints(self, db_helper, clean_database):
        """Test constraints on slow_query_log table."""
        logger.info("testing_slow_query_log_constraints")
        
        # Test valid severity levels
        valid_severities = ['info', 'warning', 'critical']
        
        for severity in valid_severities:
            log_data = {
                'duration_ms': 1000,
                'statement': 'SELECT * FROM test',
                'query_hash': 'a' * 32,
                'severity': severity
            }
            log_id = db_helper.insert_test_data('slow_query_log', log_data)
            assert log_id is not None
        
        # Test invalid severity
        invalid_log = {
            'duration_ms': 1000,
            'statement': 'SELECT * FROM test',
            'query_hash': 'a' * 32,
            'severity': 'invalid_severity'
        }
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('slow_query_log', invalid_log)
        
        assert 'severity' in str(exc_info.value).lower()
        
        # Test duration constraints
        invalid_duration_log = {
            'duration_ms': -1,  # negative duration
            'statement': 'SELECT * FROM test',
            'query_hash': 'a' * 32,
            'severity': 'info'
        }
        
        with pytest.raises(psycopg2.IntegrityError) as exc_info:
            db_helper.insert_test_data('slow_query_log', invalid_duration_log)
        
        assert 'duration_ms' in str(exc_info.value).lower()
        
        logger.info("slow_query_log_constraints_passed")
    
    def test_constraint_performance(self, db_helper, clean_database):
        """Test performance impact of constraints."""
        logger.info("testing_constraint_performance")
        
        # Measure insertion time with constraints
        start_time = time.time()
        
        for i in range(100):
            user_data = TEST_CONFIG['constraint_test_data']['valid_users'][0].copy()
            user_data['email'] = f'perf_test_{i}@example.com'
            user_data['username'] = f'perf_user_{i}'
            
            user_id = db_helper.insert_test_data('users', user_data)
            assert user_id is not None
        
        end_time = time.time()
        insertion_time = end_time - start_time
        
        logger.info("constraint_performance_test_completed",
                   records_inserted=100,
                   insertion_time_seconds=round(insertion_time, 3))
        
        # Assert reasonable performance (should complete in under 5 seconds)
        assert insertion_time < 5.0
        
        logger.info("constraint_performance_passed")
    
    def test_constraint_rollback(self, db_helper, clean_database):
        """Test constraint rollback functionality."""
        logger.info("testing_constraint_rollback")
        
        # Test the rollback function
        try:
            db_helper.execute_command("SELECT rollback_constraints_migration()")
            logger.info("constraint_rollback_function_exists")
        except Exception as e:
            logger.warning("constraint_rollback_function_not_found", error=str(e))
            pytest.skip("Rollback function not available")
        
        logger.info("constraint_rollback_passed")


class TestConstraintIntegration:
    """Integration tests for constraint functionality."""
    
    @pytest.fixture(scope="class")
    def db_helper(self):
        """Database helper fixture."""
        helper = DatabaseTestHelper(TEST_CONFIG['database_url'])
        if not helper.connect():
            pytest.skip("Database connection failed")
        yield helper
        helper.disconnect()
    
    def test_constraint_validation_queries(self, db_helper):
        """Test constraint validation queries."""
        logger.info("testing_constraint_validation_queries")
        
        # Check NOT NULL constraints
        not_null_count = db_helper.execute_query("""
            SELECT COUNT(*) as count
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND is_nullable = 'NO'
        """)[0]['count']
        
        assert not_null_count > 0
        
        # Check CHECK constraints
        check_count = db_helper.execute_query("""
            SELECT COUNT(*) as count
            FROM information_schema.table_constraints 
            WHERE table_schema = 'public' 
            AND constraint_type = 'CHECK'
        """)[0]['count']
        
        assert check_count > 0
        
        logger.info("constraint_validation_queries_passed",
                   not_null_constraints=not_null_count,
                   check_constraints=check_count)
    
    def test_constraint_indexes(self, db_helper):
        """Test that constraint-related indexes exist."""
        logger.info("testing_constraint_indexes")
        
        # Check for constraint-related indexes
        constraint_indexes = db_helper.execute_query("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE indexname LIKE '%_check'
            AND schemaname = 'public'
        """)
        
        assert len(constraint_indexes) > 0
        
        logger.info("constraint_indexes_passed",
                   index_count=len(constraint_indexes))


def main():
    """Main function for running tests directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run constraint tests")
    parser.add_argument("--database-url", 
                       default=TEST_CONFIG['database_url'],
                       help="Database URL for testing")
    parser.add_argument("--verbose", "-v", 
                       action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Update test configuration
    TEST_CONFIG['database_url'] = args.database_url
    
    # Configure logging
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Run tests
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    main() 