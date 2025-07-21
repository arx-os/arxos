"""
Tests for Robust Error Handling & Reporting System

This module tests the comprehensive error handling features including:
- Assembly warnings collection and reporting
- Recovery strategies for partial/incomplete data
- Structured error/warning output for UI/API consumption
- Fallback mechanisms for unknown types and missing data
"""

import unittest
import json
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from core.services.robust_error_handling
    WarningCollector, RecoveryManager, ErrorReporter, RobustErrorHandler,
    WarningLevel, RecoveryStrategy, AssemblyWarning, RecoveryAction, ErrorReport,
    create_error_handler, handle_assembly_warning, handle_recovery_action,
    generate_error_report
)


class TestWarningCollector(unittest.TestCase):
    """Test warning collection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.collector = WarningCollector()
    
    def test_initialization(self):
        """Test collector initialization."""
        self.assertEqual(len(self.collector.warnings), 0)
        self.assertEqual(len(self.collector.warning_counts), 0)
        self.assertEqual(len(self.collector.categories), 0)
    
    def test_add_warning(self):
        """Test adding a basic warning."""
        warning_id = self.collector.add_warning(
            level=WarningLevel.WARNING,
            category="test_category",
            message="Test warning message"
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(self.collector.warnings), 1)
        self.assertEqual(self.collector.warning_counts["test_category"], 1)
        
        warning = self.collector.warnings[0]
        self.assertEqual(warning.level, WarningLevel.WARNING)
        self.assertEqual(warning.category, "test_category")
        self.assertEqual(warning.message, "Test warning message")
    
    def test_add_warning_with_element_info(self):
        """Test adding warning with element information."""
        warning_id = self.collector.add_warning(
            level=WarningLevel.ERROR,
            category="geometry_error",
            message="Invalid geometry detected",
            element_id="element_123",
            element_type="wall",
            property_name="coordinates",
            expected_value=[0, 0, 100, 100],
            actual_value=None,
            recommendation="Add valid geometry data"
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(self.collector.warnings), 1)
        
        warning = self.collector.warnings[0]
        self.assertEqual(warning.level, WarningLevel.ERROR)
        self.assertEqual(warning.element_id, "element_123")
        self.assertEqual(warning.element_type, "wall")
        self.assertEqual(warning.property_name, "coordinates")
        self.assertEqual(warning.expected_value, [0, 0, 100, 100])
        self.assertIsNone(warning.actual_value)
        self.assertEqual(warning.recommendation, "Add valid geometry data")
    
    def test_add_missing_geometry_warning(self):
        """Test adding missing geometry warning."""
        warning_id = self.collector.add_missing_geometry_warning(
            element_id="wall_1",
            element_type="wall"
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(self.collector.warnings), 1)
        
        warning = self.collector.warnings[0]
        self.assertEqual(warning.level, WarningLevel.WARNING)
        self.assertEqual(warning.category, "missing_geometry")
        self.assertEqual(warning.element_id, "wall_1")
        self.assertEqual(warning.element_type, "wall")
        self.assertIn("Missing geometry", warning.message)
    
    def test_add_ambiguous_type_warning(self):
        """Test adding ambiguous type warning."""
        detected_types = ["wall", "partition", "barrier"]
        warning_id = self.collector.add_ambiguous_type_warning(
            element_id="element_1",
            detected_types=detected_types
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(self.collector.warnings), 1)
        
        warning = self.collector.warnings[0]
        self.assertEqual(warning.level, WarningLevel.WARNING)
        self.assertEqual(warning.category, "ambiguous_type")
        self.assertEqual(warning.element_id, "element_1")
        self.assertEqual(warning.actual_value, detected_types)
        self.assertIn("wall, partition, barrier", warning.recommendation)
    
    def test_add_property_conflict_warning(self):
        """Test adding property conflict warning."""
        warning_id = self.collector.add_property_conflict_warning(
            element_id="door_1",
            property_name="height",
            expected_value=2.1,
            actual_value=2.4
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(self.collector.warnings), 1)
        
        warning = self.collector.warnings[0]
        self.assertEqual(warning.level, WarningLevel.WARNING)
        self.assertEqual(warning.category, "property_conflict")
        self.assertEqual(warning.element_id, "door_1")
        self.assertEqual(warning.property_name, "height")
        self.assertEqual(warning.expected_value, 2.1)
        self.assertEqual(warning.actual_value, 2.4)
    
    def test_add_unknown_type_warning(self):
        """Test adding unknown type warning."""
        warning_id = self.collector.add_unknown_type_warning(
            element_id="element_1",
            unknown_type="custom_fixture"
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(self.collector.warnings), 1)
        
        warning = self.collector.warnings[0]
        self.assertEqual(warning.level, WarningLevel.WARNING)
        self.assertEqual(warning.category, "unknown_type")
        self.assertEqual(warning.element_id, "element_1")
        self.assertEqual(warning.element_type, "custom_fixture")
        self.assertIn("custom_fixture", warning.message)
    
    def test_add_validation_warning(self):
        """Test adding validation warning."""
        validation_errors = ["Invalid coordinates", "Missing required property"]
        warning_id = self.collector.add_validation_warning(
            element_id="window_1",
            validation_errors=validation_errors
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(self.collector.warnings), 1)
        
        warning = self.collector.warnings[0]
        self.assertEqual(warning.level, WarningLevel.ERROR)
        self.assertEqual(warning.category, "validation_error")
        self.assertEqual(warning.element_id, "window_1")
        self.assertEqual(warning.actual_value, validation_errors)
    
    def test_get_warnings_by_category(self):
        """Test getting warnings by category."""
        # Add warnings in different categories
        self.collector.add_warning(WarningLevel.WARNING, "geometry", "Geometry warning")
        self.collector.add_warning(WarningLevel.ERROR, "validation", "Validation error")
        self.collector.add_warning(WarningLevel.WARNING, "geometry", "Another geometry warning")
        
        geometry_warnings = self.collector.get_warnings_by_category("geometry")
        validation_warnings = self.collector.get_warnings_by_category("validation")
        
        self.assertEqual(len(geometry_warnings), 2)
        self.assertEqual(len(validation_warnings), 1)
        self.assertEqual(len(self.collector.get_warnings_by_category("nonexistent")), 0)
    
    def test_get_warnings_by_level(self):
        """Test getting warnings by level."""
        # Add warnings with different levels
        self.collector.add_warning(WarningLevel.INFO, "test", "Info message")
        self.collector.add_warning(WarningLevel.WARNING, "test", "Warning message")
        self.collector.add_warning(WarningLevel.ERROR, "test", "Error message")
        
        info_warnings = self.collector.get_warnings_by_level(WarningLevel.INFO)
        warning_warnings = self.collector.get_warnings_by_level(WarningLevel.WARNING)
        error_warnings = self.collector.get_warnings_by_level(WarningLevel.ERROR)
        
        self.assertEqual(len(info_warnings), 1)
        self.assertEqual(len(warning_warnings), 1)
        self.assertEqual(len(error_warnings), 1)
    
    def test_get_warning_summary(self):
        """Test getting warning summary."""
        # Add various warnings
        self.collector.add_warning(WarningLevel.INFO, "geometry", "Info message")
        self.collector.add_warning(WarningLevel.WARNING, "geometry", "Warning message")
        self.collector.add_warning(WarningLevel.ERROR, "validation", "Error message")
        self.collector.add_warning(WarningLevel.CRITICAL, "system", "Critical message")
        
        summary = self.collector.get_warning_summary()
        
        self.assertEqual(summary["total_warnings"], 4)
        self.assertEqual(summary["critical_count"], 1)
        self.assertEqual(summary["error_count"], 1)
        self.assertEqual(summary["warning_count"], 1)
        self.assertEqual(summary["info_count"], 1)
        self.assertEqual(summary["by_category"]["geometry"], 2)
        self.assertEqual(summary["by_category"]["validation"], 1)
        self.assertEqual(summary["by_category"]["system"], 1)


class TestRecoveryManager(unittest.TestCase):
    """Test recovery management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = RecoveryManager()
    
    def test_initialization(self):
        """Test manager initialization."""
        self.assertEqual(len(self.manager.recovery_actions), 0)
        self.assertIn("geometry", self.manager.fallback_values)
        self.assertIn("unknown_type", self.manager.recovery_strategies)
    
    def test_add_recovery_action(self):
        """Test adding recovery action."""
        action_id = self.manager.add_recovery_action(
            strategy=RecoveryStrategy.FALLBACK,
            original_error="Missing geometry",
            recovery_method="Using placeholder geometry",
            fallback_value={"type": "placeholder"},
            context={"element_id": "test_element"}
        )
        
        self.assertIsInstance(action_id, str)
        self.assertEqual(len(self.manager.recovery_actions), 1)
        
        action = self.manager.recovery_actions[0]
        self.assertEqual(action.strategy, RecoveryStrategy.FALLBACK)
        self.assertEqual(action.original_error, "Missing geometry")
        self.assertEqual(action.recovery_method, "Using placeholder geometry")
        self.assertEqual(action.fallback_value, {"type": "placeholder"})
        self.assertTrue(action.success)
    
    def test_recover_missing_geometry(self):
        """Test recovering missing geometry."""
        recovered_geometry = self.manager.recover_missing_geometry(
            element_id="wall_1",
            element_type="wall"
        )
        
        self.assertIsInstance(recovered_geometry, dict)
        self.assertEqual(recovered_geometry["element_id"], "wall_1")
        self.assertEqual(recovered_geometry["element_type"], "wall")
        self.assertEqual(len(self.manager.recovery_actions), 1)
        
        action = self.manager.recovery_actions[0]
        self.assertEqual(action.strategy, RecoveryStrategy.FALLBACK)
        self.assertEqual(action.original_error, "Missing geometry")
    
    def test_recover_unknown_type(self):
        """Test recovering unknown type."""
        recovered_type = self.manager.recover_unknown_type(
            element_id="element_1",
            unknown_type="custom_fixture"
        )
        
        self.assertEqual(recovered_type, "generic")
        self.assertEqual(len(self.manager.recovery_actions), 1)
        
        action = self.manager.recovery_actions[0]
        self.assertEqual(action.strategy, RecoveryStrategy.GENERIC)
        self.assertIn("custom_fixture", action.original_error)
    
    def test_recover_ambiguous_type(self):
        """Test recovering ambiguous type."""
        detected_types = ["wall", "partition", "barrier"]
        recovered_type = self.manager.recover_ambiguous_type(
            element_id="element_1",
            detected_types=detected_types
        )
        
        self.assertEqual(recovered_type, "wall")  # First detected type
        self.assertEqual(len(self.manager.recovery_actions), 1)
        
        action = self.manager.recovery_actions[0]
        self.assertEqual(action.strategy, RecoveryStrategy.FALLBACK)
        self.assertEqual(action.fallback_value, "wall")
    
    def test_recover_property_conflict(self):
        """Test recovering property conflict."""
        recovered_value = self.manager.recover_property_conflict(
            element_id="door_1",
            property_name="height",
            expected_value=2.1,
            actual_value=2.4
        )
        
        self.assertEqual(recovered_value, 2.1)  # Expected value
        self.assertEqual(len(self.manager.recovery_actions), 1)
        
        action = self.manager.recovery_actions[0]
        self.assertEqual(action.strategy, RecoveryStrategy.DEFAULT)
        self.assertEqual(action.fallback_value, 2.1)
    
    def test_recover_validation_error(self):
        """Test recovering validation error."""
        validation_errors = ["Invalid coordinates", "Missing required property"]
        recovered_properties = self.manager.recover_validation_error(
            element_id="window_1",
            validation_errors=validation_errors
        )
        
        self.assertIsInstance(recovered_properties, dict)
        self.assertFalse(recovered_properties["valid"])
        self.assertEqual(recovered_properties["validation_errors"], validation_errors)
        self.assertTrue(recovered_properties["recovered"])
        
        self.assertEqual(len(self.manager.recovery_actions), 1)
        
        action = self.manager.recovery_actions[0]
        self.assertEqual(action.strategy, RecoveryStrategy.DEFAULT)
    
    def test_get_recovery_summary(self):
        """Test getting recovery summary."""
        # Add various recovery actions
        self.manager.add_recovery_action(
            RecoveryStrategy.FALLBACK, "Error 1", "Method 1", success=True
        )
        self.manager.add_recovery_action(
            RecoveryStrategy.DEFAULT, "Error 2", "Method 2", success=True
        )
        self.manager.add_recovery_action(
            RecoveryStrategy.GENERIC, "Error 3", "Method 3", success=False
        )
        
        summary = self.manager.get_recovery_summary()
        
        self.assertEqual(summary["total_actions"], 3)
        self.assertEqual(summary["successful_recoveries"], 2)
        self.assertEqual(summary["failed_recoveries"], 1)
        self.assertEqual(summary["by_strategy"]["fallback"], 1)
        self.assertEqual(summary["by_strategy"]["default"], 1)
        self.assertEqual(summary["by_strategy"]["generic"], 1)


class TestErrorReporter(unittest.TestCase):
    """Test error reporting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.warning_collector = WarningCollector()
        self.recovery_manager = RecoveryManager()
        self.reporter = ErrorReporter(self.warning_collector, self.recovery_manager)
    
    def test_initialization(self):
        """Test reporter initialization."""
        self.assertIs(self.reporter.warning_collector, self.warning_collector)
        self.assertIs(self.reporter.recovery_manager, self.recovery_manager)
    
    def test_generate_error_report(self):
        """Test generating error report."""
        # Add some warnings and recovery actions
        self.warning_collector.add_warning(
            WarningLevel.WARNING, "geometry", "Test warning"
        )
        self.recovery_manager.add_recovery_action(
            RecoveryStrategy.FALLBACK, "Test error", "Test recovery"
        )
        
        report = self.reporter.generate_error_report(
            success=True,
            errors=["Test error"],
            metadata={"test": "data"}
        )
        
        self.assertIsInstance(report, ErrorReport)
        self.assertTrue(report.success)
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(len(report.recovery_actions), 1)
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(report.metadata["test"], "data")
    
    def test_generate_recommendations(self):
        """Test generating recommendations."""
        # Add various warnings to trigger recommendations
        self.warning_collector.add_warning(
            WarningLevel.CRITICAL, "system", "Critical issue"
        )
        self.warning_collector.add_warning(
            WarningLevel.ERROR, "validation", "Validation error"
        )
        self.warning_collector.add_missing_geometry_warning("element_1", "wall")
        self.warning_collector.add_unknown_type_warning("element_2", "custom_type")
        
        # Add recovery actions
        self.recovery_manager.add_recovery_action(
            RecoveryStrategy.FALLBACK, "Error", "Recovery", success=True
        )
        self.recovery_manager.add_recovery_action(
            RecoveryStrategy.DEFAULT, "Error", "Recovery", success=False
        )
        
        recommendations = self.reporter._generate_recommendations()
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for specific recommendations
        recommendation_text = " ".join(recommendations).lower()
        self.assertIn("critical", recommendation_text)
        self.assertIn("validation", recommendation_text)
        self.assertIn("geometry", recommendation_text)
        self.assertIn("type", recommendation_text)
    
    def test_to_json(self):
        """Test converting report to JSON."""
        report = self.reporter.generate_error_report(success=True)
        json_str = self.reporter.to_json(report)
        
        self.assertIsInstance(json_str, str)
        
        # Parse JSON to verify structure
        parsed = json.loads(json_str)
        self.assertIn("report_id", parsed)
        self.assertIn("success", parsed)
        self.assertIn("warnings", parsed)
        self.assertIn("recovery_actions", parsed)
        self.assertIn("errors", parsed)
        self.assertIn("recommendations", parsed)
    
    def test_to_dict(self):
        """Test converting report to dictionary."""
        report = self.reporter.generate_error_report(success=True)
        report_dict = self.reporter.to_dict(report)
        
        self.assertIsInstance(report_dict, dict)
        self.assertIn("report_id", report_dict)
        self.assertIn("success", report_dict)
        self.assertIn("warnings", report_dict)
        self.assertIn("recovery_actions", report_dict)
        self.assertIn("errors", report_dict)
        self.assertIn("recommendations", report_dict)
        self.assertIn("summary", report_dict)


class TestRobustErrorHandler(unittest.TestCase):
    """Test robust error handler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = RobustErrorHandler()
    
    def test_initialization(self):
        """Test handler initialization."""
        self.assertIsInstance(self.handler.warning_collector, WarningCollector)
        self.assertIsInstance(self.handler.recovery_manager, RecoveryManager)
        self.assertIsInstance(self.handler.error_reporter, ErrorReporter)
        self.assertEqual(len(self.handler.errors), 0)
    
    def test_handle_missing_geometry(self):
        """Test handling missing geometry."""
        recovered_geometry = self.handler.handle_missing_geometry(
            element_id="wall_1",
            element_type="wall"
        )
        
        self.assertIsInstance(recovered_geometry, dict)
        self.assertEqual(recovered_geometry["element_id"], "wall_1")
        self.assertEqual(recovered_geometry["element_type"], "wall")
        
        # Check that warning was added
        self.assertEqual(len(self.handler.warning_collector.warnings), 1)
        warning = self.handler.warning_collector.warnings[0]
        self.assertEqual(warning.category, "missing_geometry")
        
        # Check that recovery action was added
        self.assertEqual(len(self.handler.recovery_manager.recovery_actions), 1)
    
    def test_handle_unknown_type(self):
        """Test handling unknown type."""
        recovered_type = self.handler.handle_unknown_type(
            element_id="element_1",
            unknown_type="custom_fixture"
        )
        
        self.assertEqual(recovered_type, "generic")
        
        # Check that warning was added
        self.assertEqual(len(self.handler.warning_collector.warnings), 1)
        warning = self.handler.warning_collector.warnings[0]
        self.assertEqual(warning.category, "unknown_type")
        
        # Check that recovery action was added
        self.assertEqual(len(self.handler.recovery_manager.recovery_actions), 1)
    
    def test_handle_ambiguous_type(self):
        """Test handling ambiguous type."""
        detected_types = ["wall", "partition", "barrier"]
        recovered_type = self.handler.handle_ambiguous_type(
            element_id="element_1",
            detected_types=detected_types
        )
        
        self.assertEqual(recovered_type, "wall")
        
        # Check that warning was added
        self.assertEqual(len(self.handler.warning_collector.warnings), 1)
        warning = self.handler.warning_collector.warnings[0]
        self.assertEqual(warning.category, "ambiguous_type")
        
        # Check that recovery action was added
        self.assertEqual(len(self.handler.recovery_manager.recovery_actions), 1)
    
    def test_handle_property_conflict(self):
        """Test handling property conflict."""
        recovered_value = self.handler.handle_property_conflict(
            element_id="door_1",
            property_name="height",
            expected_value=2.1,
            actual_value=2.4
        )
        
        self.assertEqual(recovered_value, 2.1)
        
        # Check that warning was added
        self.assertEqual(len(self.handler.warning_collector.warnings), 1)
        warning = self.handler.warning_collector.warnings[0]
        self.assertEqual(warning.category, "property_conflict")
        
        # Check that recovery action was added
        self.assertEqual(len(self.handler.recovery_manager.recovery_actions), 1)
    
    def test_handle_validation_error(self):
        """Test handling validation error."""
        validation_errors = ["Invalid coordinates", "Missing required property"]
        recovered_properties = self.handler.handle_validation_error(
            element_id="window_1",
            validation_errors=validation_errors
        )
        
        self.assertIsInstance(recovered_properties, dict)
        self.assertFalse(recovered_properties["valid"])
        self.assertEqual(recovered_properties["validation_errors"], validation_errors)
        
        # Check that warning was added
        self.assertEqual(len(self.handler.warning_collector.warnings), 1)
        warning = self.handler.warning_collector.warnings[0]
        self.assertEqual(warning.category, "validation_error")
        
        # Check that recovery action was added
        self.assertEqual(len(self.handler.recovery_manager.recovery_actions), 1)
    
    def test_handle_exception(self):
        """Test handling exceptions."""
        test_exception = ValueError("Test error")
        self.handler.handle_exception(test_exception, "Test context")
        
        self.assertEqual(len(self.handler.errors), 1)
        self.assertIn("Test context", self.handler.errors[0])
        self.assertIn("Test error", self.handler.errors[0])
    
    def test_generate_report(self):
        """Test generating error report."""
        # Add some warnings and errors
        self.handler.handle_missing_geometry("element_1", "wall")
        self.handler.handle_exception(ValueError("Test error"), "Test context")
        
        report = self.handler.generate_report(success=True, metadata={"test": "data"})
        
        self.assertIsInstance(report, ErrorReport)
        self.assertTrue(report.success)
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(report.metadata["test"], "data")
    
    def test_get_report_json(self):
        """Test getting report as JSON."""
        self.handler.handle_missing_geometry("element_1", "wall")
        json_str = self.handler.get_report_json(success=True)
        
        self.assertIsInstance(json_str, str)
        
        # Parse JSON to verify structure
        parsed = json.loads(json_str)
        self.assertIn("report_id", parsed)
        self.assertIn("success", parsed)
        self.assertIn("warnings", parsed)
    
    def test_get_report_dict(self):
        """Test getting report as dictionary."""
        self.handler.handle_missing_geometry("element_1", "wall")
        report_dict = self.handler.get_report_dict(success=True)
        
        self.assertIsInstance(report_dict, dict)
        self.assertIn("report_id", report_dict)
        self.assertIn("success", report_dict)
        self.assertIn("warnings", report_dict)
    
    def test_clear(self):
        """Test clearing all data."""
        # Add some data
        self.handler.handle_missing_geometry("element_1", "wall")
        self.handler.handle_exception(ValueError("Test error"))
        
        # Clear
        self.handler.clear()
        
        # Verify everything is cleared
        self.assertEqual(len(self.handler.warning_collector.warnings), 0)
        self.assertEqual(len(self.handler.recovery_manager.recovery_actions), 0)
        self.assertEqual(len(self.handler.errors), 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_create_error_handler(self):
        """Test creating error handler."""
        handler = create_error_handler()
        
        self.assertIsInstance(handler, RobustErrorHandler)
        self.assertIsInstance(handler.warning_collector, WarningCollector)
        self.assertIsInstance(handler.recovery_manager, RecoveryManager)
    
    def test_handle_assembly_warning(self):
        """Test handling assembly warning."""
        handler = create_error_handler()
        
        warning_id = handle_assembly_warning(
            handler, WarningLevel.WARNING, "test_category", "Test message",
            element_id="test_element"
        )
        
        self.assertIsInstance(warning_id, str)
        self.assertEqual(len(handler.warning_collector.warnings), 1)
    
    def test_handle_recovery_action(self):
        """Test handling recovery action."""
        handler = create_error_handler()
        
        action_id = handle_recovery_action(
            handler, RecoveryStrategy.FALLBACK, "Test error", "Test recovery"
        )
        
        self.assertIsInstance(action_id, str)
        self.assertEqual(len(handler.recovery_manager.recovery_actions), 1)
    
    def test_generate_error_report(self):
        """Test generating error report."""
        handler = create_error_handler()
        
        # Add some data
        handler.handle_missing_geometry("element_1", "wall")
        
        report = generate_error_report(handler, success=True)
        
        self.assertIsInstance(report, dict)
        self.assertIn("report_id", report)
        self.assertIn("success", report)
        self.assertIn("warnings", report)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling system."""
    
    def test_complete_error_handling_workflow(self):
        """Test complete error handling workflow."""
        handler = create_error_handler()
        
        # Simulate various error scenarios
        handler.handle_missing_geometry("wall_1", "wall")
        handler.handle_unknown_type("element_1", "custom_fixture")
        handler.handle_ambiguous_type("element_2", ["wall", "partition"])
        handler.handle_property_conflict("door_1", "height", 2.1, 2.4)
        handler.handle_validation_error("window_1", ["Invalid coordinates"])
        handler.handle_exception(ValueError("Test error"), "Test context")
        
        # Generate comprehensive report
        report = handler.generate_report(success=True, metadata={"operation": "test"})
        
        # Verify report structure
        self.assertIsInstance(report, ErrorReport)
        self.assertTrue(report.success)
        self.assertEqual(len(report.warnings), 5)  # 5 different warning types
        self.assertEqual(len(report.recovery_actions), 5)  # 5 recovery actions
        self.assertEqual(len(report.errors), 1)  # 1 exception
        self.assertGreater(len(report.recommendations), 0)
        self.assertEqual(report.metadata["operation"], "test")
        
        # Convert to JSON for UI/API consumption
        json_str = handler.get_report_json(success=True)
        parsed = json.loads(json_str)
        
        self.assertIn("warnings", parsed)
        self.assertIn("recovery_actions", parsed)
        self.assertIn("errors", parsed)
        self.assertIn("recommendations", parsed)
        self.assertIn("summary", parsed)
    
    def test_error_handling_with_recovery_failures(self):
        """Test error handling when recovery actions fail."""
        handler = create_error_handler()
        
        # Simulate recovery failure by adding an error
        handler.handle_exception(Exception("Recovery failed"), "Recovery context")
        
        # Generate report
        report = handler.generate_report(success=False)
        
        self.assertFalse(report.success)
        self.assertEqual(len(report.errors), 1)
        self.assertIn("Recovery failed", report.errors[0])
    
    def test_structured_output_for_ui(self):
        """Test structured output suitable for UI consumption."""
        handler = create_error_handler()
        
        # Add various warnings and errors
        handler.handle_missing_geometry("wall_1", "wall")
        handler.handle_unknown_type("element_1", "custom_fixture")
        handler.handle_exception(ValueError("Test error"))
        
        # Get structured output
        report_dict = handler.get_report_dict(success=True)
        
        # Verify structure is suitable for UI
        self.assertIn("warnings", report_dict)
        self.assertIn("recovery_actions", report_dict)
        self.assertIn("errors", report_dict)
        self.assertIn("recommendations", report_dict)
        self.assertIn("summary", report_dict)
        
        # Verify warning structure
        warnings = report_dict["warnings"]
        self.assertGreater(len(warnings), 0)
        
        for warning in warnings:
            self.assertIn("id", warning)
            self.assertIn("level", warning)
            self.assertIn("category", warning)
            self.assertIn("message", warning)
            self.assertIn("element_id", warning)
            self.assertIn("recommendation", warning)
        
        # Verify recovery action structure
        recovery_actions = report_dict["recovery_actions"]
        self.assertGreater(len(recovery_actions), 0)
        
        for action in recovery_actions:
            self.assertIn("id", action)
            self.assertIn("strategy", action)
            self.assertIn("original_error", action)
            self.assertIn("recovery_method", action)
            self.assertIn("success", action)


if __name__ == "__main__":
    unittest.main() 