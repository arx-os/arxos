"""
SVGX Engine - Behavior Management System Tests

Comprehensive test suite for the Behavior Management System covering discovery, registration, validation, versioning, and documentation.
Tests behavior lifecycle management, conflict resolution, and performance analytics.
Follows Arxos engineering standards: absolute imports, global instances, comprehensive test coverage.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.behavior_management_system import (
    behavior_management_system, BehaviorManagementSystem,
    Behavior, BehaviorMetadata, BehaviorValidation, BehaviorVersion,
    BehaviorType, BehaviorStatus, ValidationLevel
)
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority

class TestBehaviorManagementSystemLogic:
    """Test core behavior management system logic and functionality."""

    def test_register_behavior(self):
        """Test registering a behavior."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for registration",
            tags=["test", "registration"],
            dependencies=[],
            performance_metrics={},
            usage_examples=["behavior_management_system.register_behavior(behavior)"]
        )

        behavior = Behavior(
            id="test_behavior",
            name="Test Behavior",
            behavior_type=BehaviorType.EVENT_DRIVEN,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_method",
                "system_type": "TestSystem",
                "signature": "def test_method(self, event: Event)",
                "docstring": "Test method for behavior registration",
                "is_async": False
            }
        )

        # Register behavior
        result = behavior_management_system.register_behavior(behavior)
        assert result is True

        # Verify registration
        registered_behavior = behavior_management_system.get_behavior("test_behavior")
        assert registered_behavior is not None
        assert registered_behavior.name == "Test Behavior"
        assert registered_behavior.behavior_type == BehaviorType.EVENT_DRIVEN

        # Clean up
        behavior_management_system.delete_behavior("test_behavior")

    def test_validate_behavior_basic(self):
        """Test behavior validation with basic level."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for validation",
            tags=["test", "validation"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior = Behavior(
            id="test_validation_behavior",
            name="Test Validation Behavior",
            behavior_type=BehaviorType.STATE_MACHINE,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_validation_method",
                "system_type": "TestSystem",
                "signature": "def test_validation_method(self, state: str)",
                "docstring": "Test method for validation",
                "is_async": False
            }
        )

        # Validate behavior
        validation = behavior_management_system.validate_behavior(behavior, ValidationLevel.BASIC)
        assert validation.is_valid is True
        assert validation.validation_score > 0.0
        assert validation.validation_level == ValidationLevel.BASIC

    def test_validate_behavior_strict(self):
        """Test behavior validation with strict level."""
        # Create test behavior with comprehensive metadata
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Comprehensive test behavior for strict validation with detailed description and usage examples",
            tags=["test", "validation", "strict"],
            dependencies=[],
            performance_metrics={"response_time": 50, "throughput": 1000},
            usage_examples=[
                "behavior_management_system.validate_behavior(behavior, ValidationLevel.STRICT)",
                "validation = behavior_management_system.validate_behavior(behavior)"
            ],
            documentation_url="https://docs.example.com/test-behavior"
        )

        behavior = Behavior(
            id="test_strict_validation_behavior",
            name="Test Strict Validation Behavior",
            behavior_type=BehaviorType.CONDITIONAL_LOGIC,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_strict_validation_method",
                "system_type": "TestSystem",
                "signature": "def test_strict_validation_method(self, condition: str) -> bool",
                "docstring": "Comprehensive test method for strict validation with detailed documentation",
                "is_async": False
            }
        )

        # Validate behavior with strict level
        validation = behavior_management_system.validate_behavior(behavior, ValidationLevel.STRICT)
        assert validation.is_valid is True
        assert validation.validation_score > 0.5  # Should have a good score with comprehensive data
        assert validation.validation_level == ValidationLevel.STRICT

    def test_validate_behavior_invalid(self):
        """Test behavior validation with invalid data."""
        # Create invalid behavior (missing required fields)
        metadata = BehaviorMetadata(
            author="",  # Empty author
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="",  # Empty description
            tags=[],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior = Behavior(
            id="invalid_behavior",
            name="",  # Empty name
            behavior_type=BehaviorType.EVENT_DRIVEN,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={}  # Empty implementation
        )

        # Validate behavior
        validation = behavior_management_system.validate_behavior(behavior, ValidationLevel.STANDARD)
        assert validation.is_valid is False
        assert len(validation.errors) > 0
        assert validation.validation_score < 1.0

    def test_behavior_versioning(self):
        """Test behavior versioning capabilities."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for versioning",
            tags=["test", "versioning"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior = Behavior(
            id="test_versioning_behavior",
            name="Test Versioning Behavior",
            behavior_type=BehaviorType.PERFORMANCE_OPTIMIZATION,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_versioning_method",
                "system_type": "TestSystem",
                "signature": "def test_versioning_method(self)",
                "docstring": "Test method for versioning",
                "is_async": False
            }
        )

        # Register behavior
        assert behavior_management_system.register_behavior(behavior) is True

        # Create version
        changes = ["Added new optimization algorithm", "Improved performance by 20%"]
        result = behavior_management_system.version_behavior(
            "test_versioning_behavior", "1.1.0", changes, "Test Author"
        )
        assert result is True

        # Check version was created
        updated_behavior = behavior_management_system.get_behavior("test_versioning_behavior")
        assert len(updated_behavior.versions) == 2  # Initial version + new version
        assert updated_behavior.versions[1].version == "1.1.0"  # Second version (index 1)
        assert updated_behavior.versions[1].changes == changes

        # Clean up
        behavior_management_system.delete_behavior("test_versioning_behavior")

    def test_behavior_rollback(self):
        """Test behavior rollback capabilities."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for rollback",
            tags=["test", "rollback"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior = Behavior(
            id="test_rollback_behavior",
            name="Test Rollback Behavior",
            behavior_type=BehaviorType.UI_SELECTION,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_rollback_method",
                "system_type": "TestSystem",
                "signature": "def test_rollback_method(self)",
                "docstring": "Test method for rollback",
                "is_async": False
            }
        )

        # Register behavior
        assert behavior_management_system.register_behavior(behavior) is True

        # Create multiple versions
        behavior_management_system.version_behavior(
            "test_rollback_behavior", "1.1.0", ["Added feature A"], "Test Author"
        )
        behavior_management_system.version_behavior(
            "test_rollback_behavior", "1.2.0", ["Added feature B"], "Test Author"
        )

        # Rollback to version 1.0.0
        result = behavior_management_system.rollback_behavior("test_rollback_behavior", "1.0.0")
        assert result is True

        # Check rollback was successful
        updated_behavior = behavior_management_system.get_behavior("test_rollback_behavior")
        assert updated_behavior.metadata.version == "1.0.0"
        assert len(updated_behavior.versions) == 4  # Original + 2 versions + rollback

        # Clean up
        behavior_management_system.delete_behavior("test_rollback_behavior")

    def test_behavior_documentation(self):
        """Test behavior documentation generation."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for documentation",
            tags=["test", "documentation"],
            dependencies=[],
            performance_metrics={"response_time": 25, "throughput": 2000},
            usage_examples=[
                "behavior_management_system.document_behavior('test_doc_behavior')",
                "doc = behavior_management_system.document_behavior(behavior_id)"
            ],
            documentation_url="https://docs.example.com/test-doc-behavior"
        )

        behavior = Behavior(
            id="test_doc_behavior",
            name="Test Documentation Behavior",
            behavior_type=BehaviorType.UI_EDITING,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_doc_method",
                "system_type": "TestSystem",
                "signature": "def test_doc_method(self, data: Dict[str, Any])",
                "docstring": "Test method for documentation generation",
                "is_async": False
            }
        )

        # Register behavior
        assert behavior_management_system.register_behavior(behavior) is True

        # Generate documentation
        documentation = behavior_management_system.document_behavior("test_doc_behavior")
        assert documentation is not None
        assert documentation["id"] == "test_doc_behavior"
        assert documentation["name"] == "Test Documentation Behavior"
        assert documentation["type"] == "ui_editing"
        assert documentation["status"] == "active"
        assert documentation["description"] == "Test behavior for documentation"
        assert "implementation" in documentation
        assert "validation" in documentation

        # Clean up
        behavior_management_system.delete_behavior("test_doc_behavior")

    def test_behavior_conflict_detection(self):
        """Test behavior conflict detection."""
        # Create first behavior
        metadata1 = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="First test behavior",
            tags=["test", "conflict"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior1 = Behavior(
            id="test_conflict_behavior_1",
            name="Test Conflict Behavior",
            behavior_type=BehaviorType.TIME_BASED_TRIGGER,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata1,
            implementation={
                "method_name": "test_conflict_method",
                "system_type": "TestSystem",
                "signature": "def test_conflict_method(self)",
                "docstring": "Test method for conflict detection",
                "is_async": False
            }
        )

        # Register first behavior
        assert behavior_management_system.register_behavior(behavior1) is True

        # Create second behavior with same name (conflict)
        metadata2 = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Second test behavior with same name",
            tags=["test", "conflict"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior2 = Behavior(
            id="test_conflict_behavior_2",
            name="Test Conflict Behavior",  # Same name as first behavior
            behavior_type=BehaviorType.TIME_BASED_TRIGGER,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata2,
            implementation={
                "method_name": "test_conflict_method",  # Same method name
                "system_type": "TestSystem",
                "signature": "def test_conflict_method(self)",
                "docstring": "Test method for conflict detection",
                "is_async": False
            }
        )

        # Register second behavior (should detect conflicts)
        result = behavior_management_system.register_behavior(behavior2)
        assert result is True  # Registration succeeds but with conflicts

        # Check conflicts were detected
        behavior2_registered = behavior_management_system.get_behavior("test_conflict_behavior_2")
        assert len(behavior2_registered.conflicts) > 0

        # Clean up
        behavior_management_system.delete_behavior("test_conflict_behavior_1")
        behavior_management_system.delete_behavior("test_conflict_behavior_2")

    def test_behavior_management_operations(self):
        """Test behavior management operations."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for management operations",
            tags=["test", "management"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior = Behavior(
            id="test_management_behavior",
            name="Test Management Behavior",
            behavior_type=BehaviorType.RULE_ENGINE,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_management_method",
                "system_type": "TestSystem",
                "signature": "def test_management_method(self)",
                "docstring": "Test method for management operations",
                "is_async": False
            }
        )

        # Register behavior
        assert behavior_management_system.register_behavior(behavior) is True

        # Test get by type
        rule_engine_behaviors = behavior_management_system.get_behaviors_by_type(BehaviorType.RULE_ENGINE)
        assert len(rule_engine_behaviors) >= 1
        assert any(b.id == "test_management_behavior" for b in rule_engine_behaviors)

        # Test get by status
        active_behaviors = behavior_management_system.get_behaviors_by_status(BehaviorStatus.ACTIVE)
        assert len(active_behaviors) >= 1
        assert any(b.id == "test_management_behavior" for b in active_behaviors)

        # Test get by tag
        test_behaviors = behavior_management_system.get_behaviors_by_tag("test")
        assert len(test_behaviors) >= 1
        assert any(b.id == "test_management_behavior" for b in test_behaviors)

        # Test update behavior
        updates = {"status": BehaviorStatus.TESTING}
        assert behavior_management_system.update_behavior("test_management_behavior", updates) is True

        updated_behavior = behavior_management_system.get_behavior("test_management_behavior")
        assert updated_behavior.status == BehaviorStatus.TESTING

        # Test delete behavior
        assert behavior_management_system.delete_behavior("test_management_behavior") is True
        assert behavior_management_system.get_behavior("test_management_behavior") is None

class TestBehaviorManagementSystemAsync:
    """Test asynchronous behavior management system operations."""

    @pytest.mark.asyncio
    async def test_discover_behaviors(self):
        """Test behavior discovery functionality."""
        # Discover behaviors from all systems
        discovered_behaviors = await behavior_management_system.discover_behaviors()
        assert isinstance(discovered_behaviors, list)

        # Should discover behaviors from all registered systems
        behavior_types = [b.behavior_type for b in discovered_behaviors]
        expected_types = [
            BehaviorType.EVENT_DRIVEN,
            BehaviorType.STATE_MACHINE,
            BehaviorType.CONDITIONAL_LOGIC,
            BehaviorType.PERFORMANCE_OPTIMIZATION,
            BehaviorType.UI_SELECTION,
            BehaviorType.UI_EDITING,
            BehaviorType.UI_NAVIGATION,
            BehaviorType.UI_ANNOTATION,
            BehaviorType.TIME_BASED_TRIGGER,
            BehaviorType.RULE_ENGINE
        ]

        # Check that we have behaviors from different types
        for expected_type in expected_types:
            assert expected_type in behavior_types, f"Missing behaviors for type: {expected_type}"

    @pytest.mark.asyncio
    async def test_discover_behaviors_by_type(self):
        """Test behavior discovery filtered by type."""
        # Discover only event-driven behaviors
        event_driven_behaviors = await behavior_management_system.discover_behaviors(
            behavior_types=[BehaviorType.EVENT_DRIVEN]
        )

        assert isinstance(event_driven_behaviors, list)
        for behavior in event_driven_behaviors:
            assert behavior.behavior_type == BehaviorType.EVENT_DRIVEN

    @pytest.mark.asyncio
    async def test_discover_behaviors_with_element(self):
        """Test behavior discovery with element focus."""
        # Discover behaviors for a specific element
        element_behaviors = await behavior_management_system.discover_behaviors(
            element_id="test_element"
        )

        assert isinstance(element_behaviors, list)
        # All discovered behaviors should be valid
        for behavior in element_behaviors:
            assert behavior.id is not None
            assert behavior.name is not None
            assert behavior.behavior_type is not None

class TestBehaviorManagementSystemIntegration:
    """Test integration with other behavior systems."""

    def test_performance_analytics(self):
        """Test performance analytics functionality."""
        # Get analytics for all behaviors
        analytics = behavior_management_system.get_performance_analytics()
        assert isinstance(analytics, dict)
        assert "total_behaviors" in analytics
        assert "active_behaviors" in analytics
        assert "average_validation_score" in analytics
        assert "behaviors_by_type" in analytics
        assert "behaviors_by_status" in analytics

        # Analytics should have reasonable values
        assert analytics["total_behaviors"] >= 0
        assert analytics["active_behaviors"] >= 0
        assert 0.0 <= analytics["average_validation_score"] <= 1.0

    def test_performance_analytics_specific(self):
        """Test performance analytics for specific behavior."""
        # Create test behavior for analytics
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for analytics",
            tags=["test", "analytics"],
            dependencies=[],
            performance_metrics={"response_time": 30, "throughput": 1500},
            usage_examples=[]
        )

        behavior = Behavior(
            id="test_analytics_behavior",
            name="Test Analytics Behavior",
            behavior_type=BehaviorType.CUSTOM,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_analytics_method",
                "system_type": "TestSystem",
                "signature": "def test_analytics_method(self)",
                "docstring": "Test method for analytics",
                "is_async": False
            }
        )

        # Register behavior
        assert behavior_management_system.register_behavior(behavior) is True

        # Get analytics for specific behavior
        behavior_analytics = behavior_management_system.get_performance_analytics("test_analytics_behavior")
        assert isinstance(behavior_analytics, dict)
        assert behavior_analytics["behavior_id"] == "test_analytics_behavior"
        assert "performance_history" in behavior_analytics
        assert "validation_score" in behavior_analytics
        assert "conflicts" in behavior_analytics
        assert "versions" in behavior_analytics

        # Clean up
        behavior_management_system.delete_behavior("test_analytics_behavior")

    def test_validation_levels(self):
        """Test different validation levels."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for validation levels",
            tags=["test", "validation"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior = Behavior(
            id="test_validation_levels_behavior",
            name="Test Validation Levels Behavior",
            behavior_type=BehaviorType.CUSTOM,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_validation_levels_method",
                "system_type": "TestSystem",
                "signature": "def test_validation_levels_method(self)",
                "docstring": "Test method for validation levels",
                "is_async": False
            }
        )

        # Test different validation levels
        for level in ValidationLevel:
            validation = behavior_management_system.validate_behavior(behavior, level)
            assert isinstance(validation, BehaviorValidation)
            assert validation.validation_level == level
            assert 0.0 <= validation.validation_score <= 1.0

    def test_behavior_lifecycle(self):
        """Test complete behavior lifecycle."""
        # Create test behavior
        metadata = BehaviorMetadata(
            author="Test Author",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version="1.0.0",
            description="Test behavior for lifecycle",
            tags=["test", "lifecycle"],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        )

        behavior = Behavior(
            id="test_lifecycle_behavior",
            name="Test Lifecycle Behavior",
            behavior_type=BehaviorType.CUSTOM,
            status=BehaviorStatus.ACTIVE,
            metadata=metadata,
            implementation={
                "method_name": "test_lifecycle_method",
                "system_type": "TestSystem",
                "signature": "def test_lifecycle_method(self)",
                "docstring": "Test method for lifecycle",
                "is_async": False
            }
        )

        # 1. Register behavior
        assert behavior_management_system.register_behavior(behavior) is True

        # 2. Validate behavior
        validation = behavior_management_system.validate_behavior(behavior, ValidationLevel.STANDARD)
        assert validation.is_valid is True

        # 3. Version behavior
        assert behavior_management_system.version_behavior(
            "test_lifecycle_behavior", "1.1.0", ["Added new feature"], "Test Author"
        ) is True

        # 4. Generate documentation
        documentation = behavior_management_system.document_behavior("test_lifecycle_behavior")
        assert documentation is not None

        # 5. Update behavior
        assert behavior_management_system.update_behavior(
            "test_lifecycle_behavior", {"status": BehaviorStatus.TESTING}
        ) is True

        # 6. Get performance analytics
        analytics = behavior_management_system.get_performance_analytics("test_lifecycle_behavior")
        assert analytics is not None

        # 7. Delete behavior
        assert behavior_management_system.delete_behavior("test_lifecycle_behavior") is True

        # Verify deletion
        assert behavior_management_system.get_behavior("test_lifecycle_behavior") is None
