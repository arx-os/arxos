#!/usr/bin/env python3
"""
Fixed SVGX Engine Test Script

This script tests the core functionality of the SVGX Engine with proper
imports and data formats.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_runtime_imports():
    """Test that runtime modules can be imported."""
    logger.info("Testing runtime imports...")

    try:
        from runtime import SVGXRuntime

        logger.info("✅ Runtime module imported successfully")

        from runtime.advanced_behavior_engine import AdvancedBehaviorEngine

        logger.info("✅ Advanced behavior engine imported successfully")

        from runtime.physics_engine import SVGXPhysicsEngine

        logger.info("✅ Physics engine imported successfully")

        from runtime.evaluator import SVGXEvaluator

        logger.info("✅ Evaluator imported successfully")

        return True

    except Exception as e:
        logger.error(f"❌ Runtime import test failed: {e}")
        return False


def test_services_imports():
    """Test that service modules can be imported."""
    logger.info("Testing services imports...")

    try:
        from services.logic_engine import LogicEngine

        logger.info("✅ Logic engine service imported successfully")

        from services.realtime_collaboration import RealtimeCollaboration

        logger.info("✅ Realtime collaboration service imported successfully")

        return True

    except Exception as e:
        logger.error(f"❌ Services import test failed: {e}")
        return False


def test_runtime_initialization():
    """Test that the runtime can be initialized."""
    logger.info("Testing runtime initialization...")

    try:
        from runtime import SVGXRuntime

        runtime = SVGXRuntime()
        logger.info("✅ Runtime initialized successfully")

        # Test basic functionality
        status = runtime.get_advanced_behavior_status()
        logger.info(f"✅ Advanced behavior status: {status}")

        return True

    except Exception as e:
        logger.error(f"❌ Runtime initialization failed: {e}")
        return False


def test_logic_engine():
    """Test the logic engine functionality."""
    logger.info("Testing logic engine...")

    try:
        from services.logic_engine import LogicEngine, RuleType

        engine = LogicEngine()
        logger.info("✅ Logic engine initialized successfully")

        # Test creating a simple rule with correct action format
        rule_id = engine.create_rule(
            name="Test Rule",
            description="A test rule",
            rule_type=RuleType.CONDITIONAL,
            conditions=[{"field": "temperature", "operator": ">", "value": 25}],
            actions=[{"type": "log", "message": "Temperature is high"}],
            priority=1,
            tags=["test"],
        )

        logger.info(f"✅ Created test rule: {rule_id}")

        # Test executing the rule
        result = engine.execute_rule(rule_id, {"temperature": 30})
        logger.info(f"✅ Rule execution result: {result}")

        return True

    except Exception as e:
        logger.error(f"❌ Logic engine test failed: {e}")
        return False


def test_advanced_behavior_engine():
    """Test the advanced behavior engine."""
    logger.info("Testing advanced behavior engine...")

    try:
        from runtime.advanced_behavior_engine import (
            AdvancedBehaviorEngine,
            BehaviorRule,
            BehaviorState,
            RuleType,
            StateType,
        )

        engine = AdvancedBehaviorEngine()
        logger.info("✅ Advanced behavior engine initialized successfully")

        # Test registering a simple rule with correct constructor
        rule = BehaviorRule(
            rule_id="test_rule",
            rule_type=RuleType.BUSINESS,
            conditions=[
                {
                    "type": "threshold",
                    "field": "temperature",
                    "operator": ">",
                    "value": 25,
                }
            ],
            actions=[{"type": "state_change", "target_state": "warning"}],
            priority=1,
        )

        engine.register_rule(rule)
        logger.info("✅ Registered test behavior rule")

        # Test state machine with correct constructor
        states = [
            BehaviorState(
                state_id="normal",
                state_type=StateType.EQUIPMENT,
                properties={"status": "normal"},
                transitions=[{"target": "warning", "condition": "temperature > 25"}],
            ),
            BehaviorState(
                state_id="warning",
                state_type=StateType.EQUIPMENT,
                properties={"status": "warning"},
                transitions=[{"target": "normal", "condition": "temperature <= 25"}],
            ),
        ]

        engine.register_state_machine("test_element", states, "normal")
        logger.info("✅ Registered test state machine")

        return True

    except Exception as e:
        logger.error(f"❌ Advanced behavior engine test failed: {e}")
        return False


def test_app_initialization():
    """Test that the FastAPI app can be initialized."""
    logger.info("Testing app initialization...")

    try:
        from app import app

        logger.info("✅ FastAPI app imported successfully")

        # Test that app has the expected attributes
        assert hasattr(app, "routes")
        logger.info("✅ App has expected attributes")

        return True

    except Exception as e:
        logger.error(f"❌ App initialization test failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without problematic imports."""
    logger.info("Testing basic functionality...")

    try:
        # Test that we can create basic objects
        from runtime.advanced_behavior_engine import AdvancedBehaviorEngine

        engine = AdvancedBehaviorEngine()
        logger.info("✅ Basic behavior engine created")

        # Test that we can access basic methods
        rules = engine.get_registered_rules()
        logger.info(f"✅ Registered rules: {len(rules)}")

        state_machines = engine.get_registered_state_machines()
        logger.info(f"✅ Registered state machines: {len(state_machines)}")

        return True

    except Exception as e:
        logger.error(f"❌ Basic functionality test failed: {e}")
        return False


def run_fixed_tests():
    """Run all fixed functionality tests."""
    logger.info("🚀 Starting fixed SVGX Engine test suite...")

    tests = [
        ("Runtime Imports", test_runtime_imports),
        ("Services Imports", test_services_imports),
        ("Runtime Initialization", test_runtime_initialization),
        ("Logic Engine", test_logic_engine),
        ("Advanced Behavior Engine", test_advanced_behavior_engine),
        ("App Initialization", test_app_initialization),
        ("Basic Functionality", test_basic_functionality),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")

        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")

    logger.info(f"\n{'='*50}")
    logger.info(f"TEST SUMMARY: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")

    if passed == total:
        logger.info(
            "🎉 ALL FIXED TESTS PASSED! SVGX Engine core functionality is working."
        )
        return True
    else:
        logger.error(
            f"❌ {total - passed} tests failed. Please fix issues before production deployment."
        )
        return False


if __name__ == "__main__":
    success = run_fixed_tests()
    sys.exit(0 if success else 1)
