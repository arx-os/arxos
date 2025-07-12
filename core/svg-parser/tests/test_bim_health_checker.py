"""
Comprehensive Test Suite for BIM Health Checker Service

This test suite covers all aspects of the BIM health checking functionality including:
- Floorplan validation and issue detection
- Behavior profile management
- Fix application and resolution
- Performance metrics and monitoring
- Error handling and edge cases
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

from services.bim_health_checker import (
    BIMHealthCheckerService,
    ValidationStatus,
    IssueType,
    FixType,
    ValidationIssue,
    ValidationResult,
    BehaviorProfile
)


class TestBIMHealthCheckerService:
    """Test suite for the BIMHealthCheckerService."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            import os
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.fixture
    def bim_health_service(self, temp_db_path):
        """Create a BIM health service instance for testing."""
        return BIMHealthCheckerService(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_floorplan_data(self):
        """Sample floorplan data for testing."""
        return {
            "floorplan_id": "floorplan_001",
            "name": "Test Floorplan",
            "objects": {
                "object_001": {
                    "id": "object_001",
                    "name": "HVAC Unit 1",
                    "type": "equipment",
                    "category": "hvac",
                    "location": {"x": 100, "y": 200, "z": 0},
                    "properties": {
                        "status": "active",
                        "priority": "high",
                        "capacity": "5000 BTU"
                    },
                    "last_updated": int(datetime.now().timestamp())
                },
                "object_002": {
                    "id": "object_002",
                    "name": "Electrical Panel A",
                    "type": "equipment",
                    "category": "electrical",
                    "location": {"x": 300, "y": 400, "z": 0},
                    "properties": {
                        "status": "active",
                        "priority": "critical",
                        "voltage": "480V"
                    },
                    "last_updated": int(datetime.now().timestamp())
                },
                "object_003": {
                    "id": "object_003",
                    "name": "Water Heater",
                    "type": "equipment",
                    "category": "plumbing",
                    "location": {"x": 500, "y": 600, "z": 0},
                    "properties": {
                        "status": "active",
                        "priority": "medium",
                        "capacity": "50 gallons"
                    },
                    "last_updated": int(datetime.now().timestamp())
                }
            }
        }
    
    @pytest.fixture
    def sample_floorplan_with_issues(self):
        """Sample floorplan data with known issues."""
        return {
            "floorplan_id": "floorplan_002",
            "name": "Test Floorplan with Issues",
            "objects": {
                "object_001": {
                    "id": "object_001",
                    "name": "Invalid HVAC Unit",
                    "type": "equipment",
                    "category": "hvac",
                    "location": {"x": -100, "y": 200, "z": 0},  # Invalid coordinates
                    "properties": {
                        "status": "active"
                    },
                    "last_updated": int((datetime.now() - timedelta(days=60)).timestamp())  # Stale
                },
                "object_002": {
                    "id": "object_002",
                    "name": "Missing Symbol Object",
                    "type": "equipment",
                    "category": "electrical",
                    "location": {"x": 300, "y": 400, "z": 0},
                    "properties": {
                        "status": "active"
                    },
                    "last_updated": int(datetime.now().timestamp())
                },
                "object_003": {
                    "id": "object_003",
                    "name": "Duplicate Object",
                    "type": "equipment",
                    "category": "hvac",
                    "location": {"x": 100, "y": 200, "z": 0},
                    "properties": {
                        "status": "active",
                        "priority": "high"
                    },
                    "last_updated": int(datetime.now().timestamp())
                },
                "object_004": {
                    "id": "object_004",
                    "name": "Duplicate Object",  # Duplicate of object_003
                    "type": "equipment",
                    "category": "hvac",
                    "location": {"x": 100, "y": 200, "z": 0},
                    "properties": {
                        "status": "active",
                        "priority": "high"
                    },
                    "last_updated": int(datetime.now().timestamp())
                }
            }
        }
    
    def test_service_initialization(self, bim_health_service):
        """Test service initialization and database setup."""
        assert bim_health_service is not None
        assert bim_health_service.db_path is not None
        assert bim_health_service.lock is not None
        assert isinstance(bim_health_service.metrics, dict)
        assert len(bim_health_service.behavior_profiles) > 0
    
    def test_generate_validation_id(self, bim_health_service):
        """Test validation ID generation."""
        floorplan_id = "test_floorplan_001"
        
        validation_id = bim_health_service._generate_validation_id(floorplan_id)
        
        assert validation_id is not None
        assert floorplan_id in validation_id
        assert "validation_" in validation_id
    
    def test_generate_issue_id(self, bim_health_service):
        """Test issue ID generation."""
        validation_id = "validation_test_001"
        object_id = "object_001"
        issue_type = IssueType.INVALID_COORDINATES
        
        issue_id = bim_health_service._generate_issue_id(validation_id, object_id, issue_type)
        
        assert issue_id is not None
        assert validation_id in issue_id
        assert object_id in issue_id
        assert issue_type.value in issue_id
    
    def test_validate_coordinates_valid(self, bim_health_service):
        """Test coordinate validation with valid coordinates."""
        coordinates = {"x": 100, "y": 200, "z": 0}
        bounds = {"x": [0, 1000], "y": [0, 1000], "z": [0, 100]}
        
        is_valid, error_message, suggested_value = bim_health_service._validate_coordinates(coordinates, bounds)
        
        assert is_valid is True
        assert error_message == ""
        assert suggested_value == coordinates
    
    def test_validate_coordinates_invalid(self, bim_health_service):
        """Test coordinate validation with invalid coordinates."""
        coordinates = {"x": -100, "y": 2000, "z": 0}
        bounds = {"x": [0, 1000], "y": [0, 1000], "z": [0, 100]}
        
        is_valid, error_message, suggested_value = bim_health_service._validate_coordinates(coordinates, bounds)
        
        assert is_valid is False
        assert "X coordinate" in error_message
        assert "Y coordinate" in error_message
        assert suggested_value["x"] == 0  # Clamped to bounds
        assert suggested_value["y"] == 1000  # Clamped to bounds
    
    def test_validate_coordinates_missing(self, bim_health_service):
        """Test coordinate validation with missing coordinates."""
        coordinates = {}
        bounds = {"x": [0, 1000], "y": [0, 1000], "z": [0, 100]}
        
        is_valid, error_message, suggested_value = bim_health_service._validate_coordinates(coordinates, bounds)
        
        assert is_valid is False
        assert "Missing coordinates" in error_message
        assert suggested_value == {"x": 0, "y": 0, "z": 0}
    
    def test_check_missing_behavior_profile(self, bim_health_service):
        """Test missing behavior profile detection."""
        object_data = {
            "id": "test_object",
            "type": "unknown_type",
            "category": "unknown_category"
        }
        
        issue = bim_health_service._check_missing_behavior_profile(object_data)
        
        # Should find a suitable profile or create an issue
        assert issue is not None or len(bim_health_service.behavior_profiles) > 0
    
    def test_check_invalid_coordinates(self, bim_health_service):
        """Test invalid coordinate detection."""
        object_data = {
            "id": "test_object",
            "location": {"x": -100, "y": 2000, "z": 0}
        }
        
        # Get a behavior profile
        profile = list(bim_health_service.behavior_profiles.values())[0]
        
        issue = bim_health_service._check_invalid_coordinates(object_data, profile)
        
        assert issue is not None
        assert issue.issue_type == IssueType.INVALID_COORDINATES
        assert issue.severity == "high"
        assert issue.fix_type == FixType.AUTO_FIX
    
    def test_check_unlinked_symbol(self, bim_health_service):
        """Test unlinked symbol detection."""
        object_data = {
            "id": "test_object",
            "type": "equipment",
            "category": "electrical"
        }
        
        # Get a behavior profile
        profile = list(bim_health_service.behavior_profiles.values())[0]
        
        issue = bim_health_service._check_unlinked_symbol(object_data, profile)
        
        # May or may not have an issue depending on symbol requirements
        if issue:
            assert issue.issue_type == IssueType.UNLINKED_SYMBOL
            assert issue.fix_type == FixType.SUGGESTED_FIX
    
    def test_check_stale_metadata(self, bim_health_service):
        """Test stale metadata detection."""
        # Create object with old timestamp
        old_timestamp = int((datetime.now() - timedelta(days=60)).timestamp())
        object_data = {
            "id": "test_object",
            "last_updated": old_timestamp
        }
        
        # Get a behavior profile
        profile = list(bim_health_service.behavior_profiles.values())[0]
        
        issue = bim_health_service._check_stale_metadata(object_data, profile)
        
        assert issue is not None
        assert issue.issue_type == IssueType.STALE_METADATA
        assert issue.severity == "low"
        assert issue.fix_type == FixType.SUGGESTED_FIX
    
    def test_check_duplicate_objects(self, bim_health_service):
        """Test duplicate object detection."""
        objects = [
            {
                "id": "object_001",
                "name": "Test Object 1",
                "type": "equipment",
                "location": {"x": 100, "y": 200},
                "properties": {"status": "active"}
            },
            {
                "id": "object_002",
                "name": "Test Object 2",
                "type": "equipment",
                "location": {"x": 100, "y": 200},  # Same location
                "properties": {"status": "active"}  # Same properties
            }
        ]
        
        issues = bim_health_service._check_duplicate_objects(objects)
        
        assert len(issues) > 0
        assert all(issue.issue_type == IssueType.DUPLICATE_OBJECT for issue in issues)
        assert all(issue.severity == "high" for issue in issues)
        assert all(issue.fix_type == FixType.MANUAL_FIX for issue in issues)
    
    def test_calculate_object_hash(self, bim_health_service):
        """Test object hash calculation."""
        obj1 = {
            "id": "test_object",
            "name": "Test Object",
            "type": "equipment",
            "location": {"x": 100, "y": 200},
            "properties": {"status": "active"}
        }
        
        obj2 = {
            "id": "test_object",
            "name": "Test Object",
            "type": "equipment",
            "location": {"x": 100, "y": 200},
            "properties": {"status": "active"}
        }
        
        hash1 = bim_health_service._calculate_object_hash(obj1)
        hash2 = bim_health_service._calculate_object_hash(obj2)
        
        # Same objects should have same hash
        assert hash1 == hash2
        
        # Different objects should have different hash
        obj3 = obj1.copy()
        obj3["name"] = "Different Object"
        hash3 = bim_health_service._calculate_object_hash(obj3)
        
        assert hash1 != hash3
    
    def test_find_default_symbol(self, bim_health_service):
        """Test default symbol finding."""
        # Test with known category
        symbol = bim_health_service._find_default_symbol("electrical", "equipment")
        assert symbol is not None
        
        # Test with unknown category
        symbol = bim_health_service._find_default_symbol("unknown", "equipment")
        assert symbol is not None
    
    def test_validate_floorplan_success(self, bim_health_service, sample_floorplan_data):
        """Test successful floorplan validation."""
        floorplan_id = "test_floorplan_001"
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_data
        )
        
        assert result.validation_id is not None
        assert result.floorplan_id == floorplan_id
        assert result.status == ValidationStatus.COMPLETED
        assert result.total_objects == 3
        assert result.validation_time > 0
        assert result.timestamp is not None
    
    def test_validate_floorplan_with_issues(self, bim_health_service, sample_floorplan_with_issues):
        """Test floorplan validation with known issues."""
        floorplan_id = "test_floorplan_002"
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_with_issues
        )
        
        assert result.validation_id is not None
        assert result.floorplan_id == floorplan_id
        assert result.status == ValidationStatus.COMPLETED
        assert result.total_objects == 4
        assert result.issues_found > 0  # Should find issues
        assert result.validation_time > 0
        
        # Check for specific issue types
        issue_types = [issue.issue_type for issue in result.issues]
        assert IssueType.INVALID_COORDINATES in issue_types
        assert IssueType.STALE_METADATA in issue_types
        assert IssueType.DUPLICATE_OBJECT in issue_types
    
    def test_validate_floorplan_empty(self, bim_health_service):
        """Test floorplan validation with empty data."""
        floorplan_id = "test_floorplan_empty"
        floorplan_data = {
            "floorplan_id": floorplan_id,
            "name": "Empty Floorplan",
            "objects": {}
        }
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=floorplan_data
        )
        
        assert result.validation_id is not None
        assert result.floorplan_id == floorplan_id
        assert result.status == ValidationStatus.COMPLETED
        assert result.total_objects == 0
        assert result.issues_found == 0
    
    def test_validate_floorplan_invalid_data(self, bim_health_service):
        """Test floorplan validation with invalid data."""
        floorplan_id = "test_floorplan_invalid"
        floorplan_data = {
            "floorplan_id": floorplan_id,
            "name": "Invalid Floorplan",
            "objects": "invalid_data"  # Should be dict or list
        }
        
        with pytest.raises(Exception):
            bim_health_service.validate_floorplan(
                floorplan_id=floorplan_id,
                floorplan_data=floorplan_data
            )
    
    def test_apply_fixes_success(self, bim_health_service, sample_floorplan_data):
        """Test successful fix application."""
        # First validate a floorplan
        floorplan_id = "test_floorplan_fixes"
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_data
        )
        
        # Apply fixes
        fix_selections = {}
        for issue in result.issues:
            fix_selections[issue.issue_id] = "apply"
        
        fix_result = bim_health_service.apply_fixes(
            validation_id=result.validation_id,
            fix_selections=fix_selections
        )
        
        assert fix_result["validation_id"] == result.validation_id
        assert fix_result["status"] == "completed"
        assert fix_result["applied_fixes"] >= 0
        assert fix_result["total_issues"] == len(result.issues)
    
    def test_apply_fixes_invalid_validation_id(self, bim_health_service):
        """Test fix application with invalid validation ID."""
        with pytest.raises(ValueError):
            bim_health_service.apply_fixes(
                validation_id="invalid_validation_id",
                fix_selections={"issue_001": "apply"}
            )
    
    def test_get_validation_history(self, bim_health_service, sample_floorplan_data):
        """Test validation history retrieval."""
        floorplan_id = "test_floorplan_history"
        
        # Perform multiple validations
        for i in range(3):
            bim_health_service.validate_floorplan(
                floorplan_id=floorplan_id,
                floorplan_data=sample_floorplan_data
            )
        
        # Get history
        history = bim_health_service.get_validation_history(floorplan_id, limit=10)
        
        assert len(history) > 0
        assert all("validation_id" in validation for validation in history)
        assert all("timestamp" in validation for validation in history)
        assert all("status" in validation for validation in history)
    
    def test_get_metrics(self, bim_health_service, sample_floorplan_data):
        """Test metrics retrieval."""
        # Perform some validations to generate metrics
        for i in range(3):
            bim_health_service.validate_floorplan(
                floorplan_id=f"metrics_floorplan_{i}",
                floorplan_data=sample_floorplan_data
            )
        
        metrics = bim_health_service.get_metrics()
        
        assert "metrics" in metrics
        assert "behavior_profiles" in metrics
        assert "database_size" in metrics
        assert metrics["behavior_profiles"] > 0
        assert metrics["database_size"] > 0
    
    def test_add_behavior_profile(self, bim_health_service):
        """Test adding a behavior profile."""
        profile = BehaviorProfile(
            profile_id="test_profile",
            object_type="test_equipment",
            category="test_category",
            properties={
                "required_fields": ["id", "name", "type"],
                "coordinate_bounds": {"x": [0, 1000], "y": [0, 1000]}
            },
            validation_rules={
                "coordinate_validation": True,
                "symbol_linking": True
            },
            fix_suggestions={
                "missing_coordinates": "auto_calculate",
                "invalid_coordinates": "snap_to_grid"
            }
        )
        
        initial_count = len(bim_health_service.behavior_profiles)
        
        bim_health_service.add_behavior_profile(profile)
        
        assert len(bim_health_service.behavior_profiles) == initial_count + 1
        assert "test_profile" in bim_health_service.behavior_profiles
    
    def test_get_behavior_profiles(self, bim_health_service):
        """Test behavior profile retrieval."""
        profiles = bim_health_service.get_behavior_profiles()
        
        assert len(profiles) > 0
        assert all("profile_id" in profile for profile in profiles)
        assert all("object_type" in profile for profile in profiles)
        assert all("category" in profile for profile in profiles)
    
    def test_performance_targets(self, bim_health_service, sample_floorplan_data):
        """Test that validation meets performance targets."""
        import time
        
        floorplan_id = "performance_test_floorplan"
        
        start_time = time.time()
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_data
        )
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Performance targets
        assert validation_time < 300  # Should complete within 5 minutes
        assert result.validation_time < 300  # Validation time should be < 5 minutes
        assert result.status == ValidationStatus.COMPLETED
    
    def test_issue_detection_accuracy(self, bim_health_service, sample_floorplan_with_issues):
        """Test issue detection accuracy."""
        floorplan_id = "accuracy_test_floorplan"
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_with_issues
        )
        
        # Should detect issues in the problematic floorplan
        assert result.issues_found > 0
        
        # Check for specific known issues
        issue_types = [issue.issue_type for issue in result.issues]
        
        # Should detect invalid coordinates
        assert IssueType.INVALID_COORDINATES in issue_types
        
        # Should detect stale metadata
        assert IssueType.STALE_METADATA in issue_types
        
        # Should detect duplicate objects
        assert IssueType.DUPLICATE_OBJECT in issue_types
    
    def test_fix_suggestion_accuracy(self, bim_health_service, sample_floorplan_with_issues):
        """Test fix suggestion accuracy."""
        floorplan_id = "fix_accuracy_test_floorplan"
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_with_issues
        )
        
        # Check that issues have appropriate fix types
        for issue in result.issues:
            if issue.issue_type == IssueType.INVALID_COORDINATES:
                assert issue.fix_type == FixType.AUTO_FIX
                assert issue.suggested_value is not None
            elif issue.issue_type == IssueType.STALE_METADATA:
                assert issue.fix_type == FixType.SUGGESTED_FIX
            elif issue.issue_type == IssueType.DUPLICATE_OBJECT:
                assert issue.fix_type == FixType.MANUAL_FIX
    
    def test_automated_fix_resolution(self, bim_health_service, sample_floorplan_with_issues):
        """Test automated fix resolution."""
        floorplan_id = "auto_fix_test_floorplan"
        
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_with_issues
        )
        
        # Count auto fixes
        auto_fixes = [issue for issue in result.issues if issue.fix_type == FixType.AUTO_FIX]
        
        # Should have some auto fixes
        assert len(auto_fixes) > 0
        
        # Auto fixes should have high confidence
        for issue in auto_fixes:
            assert issue.confidence >= 0.8
    
    def test_concurrent_validation(self, bim_health_service, sample_floorplan_data):
        """Test concurrent validation operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def validate_worker(floorplan_id):
            try:
                result = bim_health_service.validate_floorplan(
                    floorplan_id=floorplan_id,
                    floorplan_data=sample_floorplan_data
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple concurrent validations
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=validate_worker,
                args=(f"concurrent_floorplan_{i}",)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent validation errors: {errors}"
        assert len(results) == 5
        assert all(result.status == ValidationStatus.COMPLETED for result in results)
    
    def test_large_floorplan_validation(self, bim_health_service):
        """Test validation with large floorplan data."""
        # Create large floorplan data
        large_floorplan = {
            "floorplan_id": "large_floorplan",
            "name": "Large Floorplan",
            "objects": {}
        }
        
        # Add 1000 objects
        for i in range(1000):
            large_floorplan["objects"][f"object_{i:04d}"] = {
                "id": f"object_{i:04d}",
                "name": f"Large Object {i}",
                "type": "equipment",
                "category": "electrical" if i % 2 == 0 else "hvac",
                "location": {"x": i * 10, "y": i * 20, "z": 0},
                "properties": {
                    "status": "active" if i % 2 == 0 else "inactive",
                    "priority": "high" if i % 3 == 0 else "medium",
                    "data": "x" * 100  # Large data field
                },
                "last_updated": int(datetime.now().timestamp())
            }
        
        # Perform validation
        start_time = time.time()
        result = bim_health_service.validate_floorplan(
            floorplan_id="large_floorplan",
            floorplan_data=large_floorplan
        )
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Performance checks
        assert validation_time < 300  # Should complete within 5 minutes
        assert result.total_objects == 1000
        assert result.status == ValidationStatus.COMPLETED
    
    def test_error_handling_invalid_data(self, bim_health_service):
        """Test error handling with invalid data."""
        floorplan_id = "error_test_floorplan"
        
        # Test with invalid floorplan data
        invalid_data = {
            "floorplan_id": floorplan_id,
            "objects": "invalid_objects"  # Should be dict or list
        }
        
        with pytest.raises(Exception):
            bim_health_service.validate_floorplan(
                floorplan_id=floorplan_id,
                floorplan_data=invalid_data
            )
    
    def test_database_persistence(self, temp_db_path, sample_floorplan_data):
        """Test that validation data persists across service instances."""
        floorplan_id = "persistence_test_floorplan"
        
        # Create first service instance and perform validation
        service1 = BIMHealthCheckerService(db_path=temp_db_path)
        result1 = service1.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_data
        )
        
        # Create second service instance and check history
        service2 = BIMHealthCheckerService(db_path=temp_db_path)
        history = service2.get_validation_history(floorplan_id, limit=10)
        
        assert len(history) > 0
        assert history[0]["floorplan_id"] == floorplan_id
    
    def test_performance_metrics(self, bim_health_service, sample_floorplan_data):
        """Test performance metrics collection."""
        floorplan_id = "metrics_test_floorplan"
        
        # Perform validation and check metrics
        result = bim_health_service.validate_floorplan(
            floorplan_id=floorplan_id,
            floorplan_data=sample_floorplan_data
        )
        
        metrics = bim_health_service.get_metrics()
        
        assert metrics["metrics"]["total_validations"] > 0
        assert metrics["metrics"]["successful_validations"] > 0
        assert metrics["metrics"]["issues_detected"] >= 0
        assert metrics["metrics"]["auto_fixes_applied"] >= 0
        assert metrics["metrics"]["average_validation_time"] >= 0
    
    def test_behavior_profile_validation(self, bim_health_service):
        """Test behavior profile validation rules."""
        # Test with valid profile
        valid_profile = BehaviorProfile(
            profile_id="test_valid_profile",
            object_type="test_equipment",
            category="test_category",
            properties={
                "required_fields": ["id", "name", "type"],
                "coordinate_bounds": {"x": [0, 1000], "y": [0, 1000]}
            },
            validation_rules={
                "coordinate_validation": True,
                "symbol_linking": True
            },
            fix_suggestions={
                "missing_coordinates": "auto_calculate",
                "invalid_coordinates": "snap_to_grid"
            }
        )
        
        bim_health_service.add_behavior_profile(valid_profile)
        
        # Verify profile was added
        profiles = bim_health_service.get_behavior_profiles()
        profile_ids = [p["profile_id"] for p in profiles]
        assert "test_valid_profile" in profile_ids
    
    def test_edge_cases(self, bim_health_service):
        """Test various edge cases."""
        # Test with empty floorplan
        empty_result = bim_health_service.validate_floorplan(
            floorplan_id="empty_floorplan",
            floorplan_data={"floorplan_id": "empty", "objects": {}}
        )
        assert empty_result.total_objects == 0
        
        # Test with very large object IDs
        large_id = "x" * 1000
        large_floorplan = {
            "floorplan_id": "large_id_floorplan",
            "objects": {large_id: {"id": large_id, "name": "Large ID Object"}}
        }
        
        large_result = bim_health_service.validate_floorplan(
            floorplan_id="large_id_floorplan",
            floorplan_data=large_floorplan
        )
        assert large_result.status == ValidationStatus.COMPLETED
        
        # Test with special characters in floorplan ID
        special_floorplan_id = "floorplan-with-special-chars!@#$%^&*()"
        special_result = bim_health_service.validate_floorplan(
            floorplan_id=special_floorplan_id,
            floorplan_data={"floorplan_id": special_floorplan_id, "objects": {}}
        )
        assert special_result.status == ValidationStatus.COMPLETED


class TestIssueDetection:
    """Test suite for issue detection functionality."""
    
    @pytest.fixture
    def bim_health_service(self, temp_db_path):
        """Create a BIM health service instance for testing."""
        return BIMHealthCheckerService(db_path=temp_db_path)
    
    def test_missing_behavior_profile_detection(self, bim_health_service):
        """Test detection of missing behavior profiles."""
        object_data = {
            "id": "test_object",
            "type": "unknown_type",
            "category": "unknown_category"
        }
        
        issue = bim_health_service._check_missing_behavior_profile(object_data)
        
        # Should either find a suitable profile or create an issue
        if issue:
            assert issue.issue_type == IssueType.MISSING_BEHAVIOR_PROFILE
            assert issue.severity == "medium"
            assert issue.fix_type == FixType.AUTO_FIX
    
    def test_invalid_coordinate_detection(self, bim_health_service):
        """Test detection of invalid coordinates."""
        object_data = {
            "id": "test_object",
            "location": {"x": -100, "y": 2000, "z": -50}
        }
        
        profile = list(bim_health_service.behavior_profiles.values())[0]
        
        issue = bim_health_service._check_invalid_coordinates(object_data, profile)
        
        assert issue is not None
        assert issue.issue_type == IssueType.INVALID_COORDINATES
        assert issue.severity == "high"
        assert issue.fix_type == FixType.AUTO_FIX
        assert issue.suggested_value is not None
    
    def test_stale_metadata_detection(self, bim_health_service):
        """Test detection of stale metadata."""
        # Create object with very old timestamp
        old_timestamp = int((datetime.now() - timedelta(days=100)).timestamp())
        object_data = {
            "id": "test_object",
            "last_updated": old_timestamp
        }
        
        profile = list(bim_health_service.behavior_profiles.values())[0]
        
        issue = bim_health_service._check_stale_metadata(object_data, profile)
        
        assert issue is not None
        assert issue.issue_type == IssueType.STALE_METADATA
        assert issue.severity == "low"
        assert issue.fix_type == FixType.SUGGESTED_FIX
    
    def test_duplicate_object_detection(self, bim_health_service):
        """Test detection of duplicate objects."""
        objects = [
            {
                "id": "object_001",
                "name": "Test Object",
                "type": "equipment",
                "location": {"x": 100, "y": 200},
                "properties": {"status": "active"}
            },
            {
                "id": "object_002",
                "name": "Test Object",  # Same name
                "type": "equipment",
                "location": {"x": 100, "y": 200},  # Same location
                "properties": {"status": "active"}  # Same properties
            }
        ]
        
        issues = bim_health_service._check_duplicate_objects(objects)
        
        assert len(issues) > 0
        assert all(issue.issue_type == IssueType.DUPLICATE_OBJECT for issue in issues)
        assert all(issue.severity == "high" for issue in issues)


class TestPerformanceAndScalability:
    """Test suite for performance and scalability aspects."""
    
    @pytest.fixture
    def bim_health_service(self, temp_db_path):
        """Create a BIM health service instance for testing."""
        return BIMHealthCheckerService(db_path=temp_db_path)
    
    def test_validation_performance_targets(self, bim_health_service):
        """Test that validation meets performance targets."""
        import time
        
        # Create test floorplan
        floorplan_data = {
            "floorplan_id": "performance_test",
            "objects": {}
        }
        
        # Add 100 objects
        for i in range(100):
            floorplan_data["objects"][f"object_{i:03d}"] = {
                "id": f"object_{i:03d}",
                "name": f"Performance Object {i}",
                "type": "equipment",
                "category": "electrical" if i % 2 == 0 else "hvac",
                "location": {"x": i * 10, "y": i * 20, "z": 0},
                "properties": {"status": "active", "priority": "high"},
                "last_updated": int(datetime.now().timestamp())
            }
        
        # Measure validation performance
        start_time = time.time()
        result = bim_health_service.validate_floorplan(
            floorplan_id="performance_test",
            floorplan_data=floorplan_data
        )
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Performance targets
        assert validation_time < 300  # Should complete within 5 minutes
        assert result.validation_time < 300  # Validation time should be < 5 minutes
        assert result.status == ValidationStatus.COMPLETED
        assert result.total_objects == 100
    
    def test_issue_detection_accuracy(self, bim_health_service):
        """Test issue detection accuracy."""
        # Create floorplan with known issues
        floorplan_data = {
            "floorplan_id": "accuracy_test",
            "objects": {
                "invalid_coords": {
                    "id": "invalid_coords",
                    "name": "Invalid Coordinates",
                    "type": "equipment",
                    "location": {"x": -100, "y": 2000, "z": 0},
                    "properties": {"status": "active"},
                    "last_updated": int(datetime.now().timestamp())
                },
                "stale_metadata": {
                    "id": "stale_metadata",
                    "name": "Stale Metadata",
                    "type": "equipment",
                    "location": {"x": 100, "y": 200, "z": 0},
                    "properties": {"status": "active"},
                    "last_updated": int((datetime.now() - timedelta(days=60)).timestamp())
                }
            }
        }
        
        result = bim_health_service.validate_floorplan(
            floorplan_id="accuracy_test",
            floorplan_data=floorplan_data
        )
        
        # Should detect issues
        assert result.issues_found > 0
        
        # Check for specific issues
        issue_types = [issue.issue_type for issue in result.issues]
        assert IssueType.INVALID_COORDINATES in issue_types
        assert IssueType.STALE_METADATA in issue_types
    
    def test_fix_suggestion_accuracy(self, bim_health_service):
        """Test fix suggestion accuracy."""
        # Create floorplan with issues that should have fix suggestions
        floorplan_data = {
            "floorplan_id": "fix_accuracy_test",
            "objects": {
                "invalid_coords": {
                    "id": "invalid_coords",
                    "name": "Invalid Coordinates",
                    "type": "equipment",
                    "location": {"x": -100, "y": 2000, "z": 0},
                    "properties": {"status": "active"},
                    "last_updated": int(datetime.now().timestamp())
                }
            }
        }
        
        result = bim_health_service.validate_floorplan(
            floorplan_id="fix_accuracy_test",
            floorplan_data=floorplan_data
        )
        
        # Check that issues have appropriate fix suggestions
        for issue in result.issues:
            if issue.issue_type == IssueType.INVALID_COORDINATES:
                assert issue.suggested_value is not None
                assert issue.confidence >= 0.8
                assert issue.fix_type == FixType.AUTO_FIX


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 