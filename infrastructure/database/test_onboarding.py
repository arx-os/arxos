#!/usr/bin/env python3
"""
Arx Database Infrastructure Onboarding Test Script

This script verifies that the development environment is correctly set up
and operational for the Arx Database Infrastructure.
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path


def run_command(command, description, check=True):
    """Run a command and return the result."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=check
        )
        print(f"✅ {description} - SUCCESS")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"   Error: {e.stderr}")
        return None


def check_python_version():
    """Check if Python is installed and has the correct version."""
    version = run_command("python --version", "Checking Python version")
    if version:
        print(f"   Found: {version}")
        if "Python 3.11" in version or "Python 3.12" in version:
            return True
        else:
            print("   ⚠️  Warning: Python 3.11+ is recommended")
            return False
    return False


def check_virtual_environment():
    """Check if virtual environment is activated."""
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("✅ Virtual environment is activated")
        return True
    else:
        print("❌ Virtual environment not activated")
        print("   Please activate your virtual environment")
        return False


def check_dependencies():
    """Check if Python dependencies are properly installed."""
    return (
        run_command(
            "pip install -r requirements.txt", "Installing/checking Python dependencies"
        )
        is not None
    )


def check_database_connection():
    """Check if database connection is working."""
    # This would require a database connection test
    # For now, we'll just check if the environment variable is set
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print("✅ Database URL is configured")
        return True
    else:
        print("❌ Database URL not configured")
        return False


def check_environment_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file not found")
        print("   Please copy env.example to .env and configure it")
        return False


def run_tests():
    """Run the test suite."""
    return run_command("pytest", "Running tests") is not None


def check_alembic_configuration():
    """Check if Alembic is properly configured."""
    alembic_ini = Path("alembic.ini")
    if alembic_ini.exists():
        print("✅ Alembic configuration exists")
        return True
    else:
        print("❌ Alembic configuration not found")
        return False


def check_tools_directory():
    """Check if tools directory exists with required scripts."""
    tools_dir = Path("tools")
    if tools_dir.exists():
        required_tools = [
            "generate_docs.py",
            "validate_schema.py",
            "performance_analysis.py",
            "health_check.py",
        ]

        missing_tools = []
        for tool in required_tools:
            if not (tools_dir / tool).exists():
                missing_tools.append(tool)

        if not missing_tools:
            print("✅ All required tools are present")
            return True
        else:
            print(f"❌ Missing tools: {', '.join(missing_tools)}")
            return False
    else:
        print("❌ Tools directory not found")
        return False


def check_documentation_templates():
    """Check if documentation templates exist."""
    templates_dir = Path("templates")
    if templates_dir.exists():
        required_templates = [
            "schema_template.md",
            "migration_template.md",
            "performance_template.md",
        ]

        missing_templates = []
        for template in required_templates:
            if not (templates_dir / template).exists():
                missing_templates.append(template)

        if not missing_templates:
            print("✅ All documentation templates are present")
            return True
        else:
            print(f"❌ Missing templates: {', '.join(missing_templates)}")
            return False
    else:
        print("❌ Templates directory not found")
        return False


def check_linting():
    """Check if code passes linting."""
    return run_command("black --check tools/", "Checking code formatting") is not None


def check_documentation_generation():
    """Check if documentation can be generated."""
    return (
        run_command(
            "python tools/generate_docs.py --help", "Checking documentation generation"
        )
        is not None
    )


def check_schema_validation():
    """Check if schema validation tools work."""
    return (
        run_command(
            "python tools/validate_schema.py --help", "Checking schema validation"
        )
        is not None
    )


def check_performance_tools():
    """Check if performance analysis tools work."""
    return (
        run_command(
            "python tools/performance_analysis.py --help", "Checking performance tools"
        )
        is not None
    )


def main():
    """Run all onboarding checks."""
    print("🚀 Arx Database Infrastructure Onboarding Test")
    print("=" * 50)

    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Environment File", check_environment_file),
        ("Database Configuration", check_database_connection),
        ("Alembic Configuration", check_alembic_configuration),
        ("Tools Directory", check_tools_directory),
        ("Documentation Templates", check_documentation_templates),
        ("Code Formatting", check_linting),
        ("Documentation Generation", check_documentation_generation),
        ("Schema Validation", check_schema_validation),
        ("Performance Tools", check_performance_tools),
        ("Test Suite", run_tests),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}")
        print("-" * 30)
        result = check_func()
        results.append((name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 ONBOARDING TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<25} {status}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! Your development environment is ready.")
        print("\nNext steps:")
        print("1. Generate documentation: python tools/generate_docs.py")
        print("2. Validate schema: python tools/validate_schema.py")
        print("3. Run performance analysis: python tools/performance_analysis.py")
        print("4. Check database health: python tools/health_check.py")
        print("5. Review the ONBOARDING.md file for more details")
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all prerequisites are installed")
        print("2. Activate your virtual environment")
        print("3. Copy env.example to .env and configure it")
        print("4. Run 'pip install -r requirements.txt' to install dependencies")
        print("5. Check the ONBOARDING.md file for detailed instructions")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
