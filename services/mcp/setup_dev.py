#!/usr/bin/env python3
"""
Development Setup Script for MCP Service

This script sets up the development environment and verifies
core functionality without requiring all dependencies.
"""

import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def install_dependencies():
    """Install Python dependencies"""
    logger.info("📦 Installing Python dependencies...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False


def test_core_components():
    """Test core components without external dependencies"""
    logger.info("🔍 Testing core components...")

    test_results = {}

    # Test 1: Check if all required files exist
    required_files = [
        "main.py",
        "websocket/websocket_manager.py",
        "websocket/websocket_routes.py",
        "cache/redis_manager.py",
        "auth/authentication.py",
        "monitoring/prometheus_metrics.py",
        "validate/rule_engine.py",
        "models/mcp_models.py",
        "requirements.txt",
        "docker-compose.dev.yml",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        test_results["file_structure"] = f"❌ FAILED: Missing files: {missing_files}"
    else:
        test_results["file_structure"] = "✅ PASSED"

    # Test 2: Check Python syntax
    python_files = [
        "main.py",
        "websocket/websocket_manager.py",
        "websocket/websocket_routes.py",
        "cache/redis_manager.py",
        "auth/authentication.py",
        "monitoring/prometheus_metrics.py",
    ]

    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, "r") as f:
                compile(f.read(), file_path, "exec")
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")

    if syntax_errors:
        test_results["python_syntax"] = f"❌ FAILED: Syntax errors: {syntax_errors}"
    else:
        test_results["python_syntax"] = "✅ PASSED"

    # Test 3: Check imports (basic)
    try:
        # Test basic imports that don't require external packages
        import json
        import logging
        import asyncio
        import time
        from datetime import datetime
        from typing import Dict, Any, List, Optional
        from dataclasses import dataclass
        from enum import Enum

        test_results["basic_imports"] = "✅ PASSED"
    except ImportError as e:
        test_results["basic_imports"] = f"❌ FAILED: {e}"

    # Test 4: Check configuration files
    config_files = ["requirements.txt", "docker-compose.dev.yml"]

    config_errors = []
    for file_path in config_files:
        if not Path(file_path).exists():
            config_errors.append(file_path)

    if config_errors:
        test_results["config_files"] = (
            f"❌ FAILED: Missing config files: {config_errors}"
        )
    else:
        test_results["config_files"] = "✅ PASSED"

    return test_results


def test_rule_engine_basic():
    """Test basic rule engine functionality"""
    logger.info("🔍 Testing basic rule engine...")

    try:
        # Test basic rule engine initialization
        from validate.rule_engine import MCPRuleEngine
        from models.mcp_models import BuildingModel, BuildingObject

        # Create a simple building model
        building_model = BuildingModel(
            building_id="test_building",
            building_name="Test Building",
            objects=[],
            metadata={},
        )

        # Initialize rule engine
        rule_engine = MCPRuleEngine()

        # Test jurisdiction info (should work without MCP files)
        jurisdiction_info = rule_engine.get_jurisdiction_info(building_model)

        if "location_found" in jurisdiction_info:
            return "✅ PASSED"
        else:
            return "❌ FAILED: Missing jurisdiction info"

    except Exception as e:
        return f"❌ FAILED: {str(e)}"


def print_results(test_results):
    """Print test results"""
    logger.info("=" * 60)
    logger.info("📊 CORE COMPONENT TEST RESULTS")
    logger.info("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in test_results.items():
        logger.info(f"{test_name}: {result}")
        if "PASSED" in result:
            passed += 1
        else:
            failed += 1

    logger.info("=" * 60)
    logger.info(f"✅ PASSED: {passed}")
    logger.info(f"❌ FAILED: {failed}")
    logger.info("=" * 60)

    if failed == 0:
        logger.info("🎉 All core component tests passed!")
        logger.info("🚀 Ready for dependency installation and full testing.")
    else:
        logger.warning(f"⚠️  {failed} test(s) failed. Please check the issues above.")

    return failed == 0


def main():
    """Main setup function"""
    logger.info("🚀 MCP Service Development Setup")
    logger.info("=" * 60)

    # Test core components first
    test_results = test_core_components()

    # Test rule engine
    test_results["rule_engine_basic"] = test_rule_engine_basic()

    # Print results
    success = print_results(test_results)

    if success:
        logger.info("\n📦 Ready to install dependencies...")
        logger.info("Run: pip install -r requirements.txt")
        logger.info("Then run: python3 test_integration.py")
    else:
        logger.error("\n❌ Core component tests failed.")
        logger.error("Please fix the issues before proceeding.")

    return success


if __name__ == "__main__":
    main()
