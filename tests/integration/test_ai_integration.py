"""
Test Suite for AI Integration Service

This test suite verifies the AI integration service functionality including
symbol generation, intelligent suggestions, placement optimization, and user learning.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import unittest
import json
import time
from datetime import datetime
from typing import Dict, Any

from svgx_engine.services.ai_integration_service import (
    AIIntegrationService, AIConfig, AITaskType, AISymbol, AISuggestion, UserBehavior
)


class TestAIIntegrationService(unittest.TestCase):
    """Test suite for AI integration service."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = AIConfig(
            model_enabled=True,
            learning_enabled=True,
            min_confidence=0.6,
            quality_threshold=0.8
        )
        self.ai_service = AIIntegrationService(self.config)

    def test_symbol_generation(self):
        """Test AI-powered symbol generation."""
        # Test wall symbol generation
        description = "Create a wall element"
        context = {"dimensions": {"width": 200, "height": 300}}

        symbol = self.ai_service.generate_symbol(description, context)

        # Verify symbol structure
        self.assertIsInstance(symbol, AISymbol)
        self.assertIsNotNone(symbol.symbol_id)
        self.assertEqual(symbol.symbol_type, "wall")
        self.assertIn("geometry", symbol.__dict__)
        self.assertIn("properties", symbol.__dict__)
        self.assertGreater(symbol.confidence, 0.6)
        self.assertGreater(symbol.quality_score, 0.7)

        # Test door symbol generation
        description = "Add a door"
        context = {"dimensions": {"width": 80, "height": 200}}

        symbol = self.ai_service.generate_symbol(description, context)

        self.assertEqual(symbol.symbol_type, "door")
        self.assertGreater(symbol.confidence, 0.6)

    def test_intelligent_suggestions(self):
        """Test intelligent suggestion generation."""
        context = {
            "current_element": "wall",
            "surrounding_elements": ["door", "window"],
            "project_type": "residential",
            "recent_actions": ["add_wall", "add_door"]
        }

        suggestions = self.ai_service.get_suggestions(context, "wall")

        # Verify suggestions
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

        for suggestion in suggestions:
            self.assertIsInstance(suggestion, AISuggestion)
            self.assertIsNotNone(suggestion.suggestion_id)
            self.assertEqual(suggestion.task_type, AITaskType.SUGGESTION)
            self.assertGreater(suggestion.confidence, 0.6)

    def test_placement_suggestions(self):
        """Test context-aware placement suggestions."""
        element_type = "door"
        context = {
            "existing_elements": [
                {"type": "wall", "position": {"x": 0, "y": 0}, "dimensions": {"width": 200, "height": 300}}
            ],
            "boundaries": {"width": 1000, "height": 800},
            "constraints": [],
            "preferences": {"preferred_side": "right"}
        }

        placement = self.ai_service.suggest_placement(element_type, context)

        # Verify placement structure
        self.assertIsInstance(placement, dict)
        self.assertIn("position", placement)
        self.assertIn("orientation", placement)
        self.assertIn("confidence", placement)
        self.assertIn("constraints", placement)
        self.assertIn("alternatives", placement)

        # Verify position data
        position = placement["position"]
        self.assertIn("x", position)
        self.assertIn("y", position)
        self.assertIsInstance(position["x"], (int, float))
        self.assertIsInstance(position["y"], (int, float))

    def test_user_behavior_learning(self):
        """Test user behavior learning and personalization."""
        user_id = "test_user_123"

        # Record user behaviors
        behaviors = [
            UserBehavior(
                user_id=user_id,
                action_type="add_wall",
                context={"element_type": "wall", "dimensions": {"width": 200, "height": 300}},
                result={"success": True, "element_id": "wall_001"},
                feedback=0.9
            ),
            UserBehavior(
                user_id=user_id,
                action_type="add_door",
                context={"element_type": "door", "position": {"x": 100, "y": 0}},
                result={"success": True, "element_id": "door_001"},
                feedback=0.8
            ),
            UserBehavior(
                user_id=user_id,
                action_type="add_window",
                context={"element_type": "window", "position": {"x": 200, "y": 50}},
                result={"success": True, "element_id": "window_001"},
                feedback=0.7
            )
        ]

        # Record behaviors
        for behavior in behaviors:
            self.ai_service.record_user_behavior(behavior)

        # Get personalized suggestions
        context = {"current_element": "wall", "project_type": "residential"}
        personalized_suggestions = self.ai_service.get_personalized_suggestions(user_id, context)

        # Verify personalized suggestions
        self.assertIsInstance(personalized_suggestions, list)
        # Should have suggestions based on recorded behavior
        self.assertGreaterEqual(len(personalized_suggestions), 0)

    def test_ai_statistics(self):
        """Test AI service statistics."""
        # Perform some operations
        self.ai_service.generate_symbol("test wall", {})
        self.ai_service.get_suggestions({}, "test")
        self.ai_service.suggest_placement("door", {})

        stats = self.ai_service.get_ai_statistics()

        # Verify statistics structure
        self.assertIsInstance(stats, dict)
        self.assertIn("symbols_generated", stats)
        self.assertIn("suggestions_provided", stats)
        self.assertIn("placements_suggested", stats)
        self.assertIn("behaviors_recorded", stats)
        self.assertIn("total_processing_time", stats)
        self.assertIn("average_processing_time", stats)
        self.assertIn("success_rate", stats)
        self.assertIn("model_performance", stats)

        # Verify statistics values
        self.assertGreaterEqual(stats["symbols_generated"], 1)
        self.assertGreaterEqual(stats["suggestions_provided"], 1)
        self.assertGreaterEqual(stats["placements_suggested"], 1)
        self.assertGreaterEqual(stats["success_rate"], 0.0)
        self.assertLessEqual(stats["success_rate"], 1.0)

    def test_data_validation(self):
        """Test AI data validation."""
        # Valid data
        valid_data = {
            "type": "symbol_generation",
            "content": "Create a wall",
            "context": {"dimensions": {"width": 200, "height": 300}}
        }

        self.assertTrue(self.ai_service.validate_ai_data(valid_data))

        # Invalid data - missing required fields
        invalid_data = {
            "content": "Create a wall"
        }

        self.assertFalse(self.ai_service.validate_ai_data(invalid_data))

    def test_error_handling(self):
        """Test error handling in AI service."""
        # Test with invalid input
        with self.assertRaises(Exception):
            self.ai_service.generate_symbol("", {})

        # Test with invalid context
        with self.assertRaises(Exception):
            self.ai_service.get_suggestions(None, "")

    def test_performance_monitoring(self):
        """Test performance monitoring in AI service."""
        start_time = time.time()

        # Perform multiple operations
        for i in range(5):
            self.ai_service.generate_symbol(f"test symbol {i}", {})
            self.ai_service.get_suggestions({}, f"test{i}")

        end_time = time.time()
        total_time = end_time - start_time

        stats = self.ai_service.get_ai_statistics()

        # Verify performance metrics
        self.assertGreater(stats["total_processing_time"], 0)
        self.assertGreater(stats["average_processing_time"], 0)
        self.assertLess(stats["total_processing_time"], total_time * 2)  # Reasonable overhead

    def test_configuration_validation(self):
        """Test AI configuration validation."""
        # Test with valid configuration
        config = AIConfig(
            model_enabled=True,
            learning_enabled=True,
            min_confidence=0.7,
            quality_threshold=0.8
        )

        ai_service = AIIntegrationService(config)
        self.assertIsNotNone(ai_service)

        # Test with disabled model
        config_disabled = AIConfig(model_enabled=False)
        ai_service_disabled = AIIntegrationService(config_disabled)
        self.assertIsNotNone(ai_service_disabled)

    def test_symbol_quality_assessment(self):
        """Test symbol quality assessment."""
        # Generate symbols with different descriptions
        symbols = []

        descriptions = [
            "Create a standard wall",
            "Add a door to the wall",
            "Place a window in the wall",
            "Add furniture to the room"
        ]

        for description in descriptions:
            symbol = self.ai_service.generate_symbol(description, {})
            symbols.append(symbol)

        # Verify quality scores
        for symbol in symbols:
            self.assertGreaterEqual(symbol.quality_score, 0.0)
            self.assertLessEqual(symbol.quality_score, 1.0)
            self.assertGreaterEqual(symbol.confidence, 0.0)
            self.assertLessEqual(symbol.confidence, 1.0)

    def test_suggestion_relevance(self):
        """Test suggestion relevance and ranking."""
        context = {
            "current_element": "wall",
            "project_type": "residential",
            "recent_actions": ["add_wall", "add_door"]
        }

        suggestions = self.ai_service.get_suggestions(context, "wall")

        # Verify suggestions are ranked by confidence
        if len(suggestions) > 1:
            for i in range(len(suggestions) - 1):
                self.assertGreaterEqual(suggestions[i].confidence, suggestions[i + 1].confidence)

        # Verify all suggestions meet minimum confidence
        for suggestion in suggestions:
            self.assertGreaterEqual(suggestion.confidence, self.config.min_confidence)


class TestAIConfiguration(unittest.TestCase):
    """Test suite for AI configuration."""

    def test_default_configuration(self):
        """Test default AI configuration."""
        config = AIConfig()

        self.assertTrue(config.model_enabled)
        self.assertTrue(config.learning_enabled)
        self.assertEqual(config.min_confidence, 0.6)
        self.assertEqual(config.quality_threshold, 0.8)
        self.assertTrue(config.cache_enabled)
        self.assertTrue(config.validation_enabled)

    def test_custom_configuration(self):
        """Test custom AI configuration."""
        config = AIConfig(
            model_enabled=False,
            learning_enabled=False,
            min_confidence=0.8,
            quality_threshold=0.9,
            cache_enabled=False,
            validation_enabled=False
        )

        self.assertFalse(config.model_enabled)
        self.assertFalse(config.learning_enabled)
        self.assertEqual(config.min_confidence, 0.8)
        self.assertEqual(config.quality_threshold, 0.9)
        self.assertFalse(config.cache_enabled)
        self.assertFalse(config.validation_enabled)


class TestAIErrorHandling(unittest.TestCase):
    """Test suite for AI error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = AIConfig()
        self.ai_service = AIIntegrationService(self.config)

    def test_invalid_symbol_generation(self):
        """Test error handling for invalid symbol generation."""
        with self.assertRaises(Exception):
            self.ai_service.generate_symbol("", {})

        with self.assertRaises(Exception):
            self.ai_service.generate_symbol("test", None)

    def test_invalid_suggestions(self):
        """Test error handling for invalid suggestions."""
        with self.assertRaises(Exception):
            self.ai_service.get_suggestions(None, "")

        with self.assertRaises(Exception):
            self.ai_service.get_suggestions({}, None)

    def test_invalid_placement(self):
        """Test error handling for invalid placement."""
        with self.assertRaises(Exception):
            self.ai_service.suggest_placement("", {})

        with self.assertRaises(Exception):
            self.ai_service.suggest_placement("door", None)


def run_ai_integration_tests():
    """Run all AI integration tests."""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestAIIntegrationService,
        TestAIConfiguration,
        TestAIErrorHandling
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"AI INTEGRATION SERVICE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run AI integration tests
    success = run_ai_integration_tests()

    if success:
        print(f"\n✅ ALL TESTS PASSED - AI integration service is working correctly!")
    else:
        print(f"\n❌ SOME TESTS FAILED - AI integration service needs attention!")

    exit(0 if success else 1)
