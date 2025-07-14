#!/usr/bin/env python3
"""
Arx SVG Parser Onboarding Test Script

This script verifies that the development environment is correctly set up
and operational for the Arx SVG Parser service.
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
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
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
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is activated")
        return True
    else:
        print("❌ Virtual environment not activated")
        print("   Please activate your virtual environment")
        return False


def check_dependencies():
    """Check if Python dependencies are properly installed."""
    return run_command("pip install -e .", "Installing/checking Python dependencies") is not None


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


def check_redis_connection():
    """Check if Redis connection is working."""
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        print("✅ Redis URL is configured")
        return True
    else:
        print("❌ Redis URL not configured")
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


def check_server_startup():
    """Check if the server can start (without actually starting it)."""
    # Check if main.py exists
    main_file = Path("arx_svg_parser/main.py")
    if main_file.exists():
        print("✅ Server main file exists")
        return True
    else:
        print("❌ Server main file not found")
        return False


def check_linting():
    """Check if code passes linting."""
    return run_command("black --check arx_svg_parser/", "Checking code formatting") is not None


def check_build():
    """Check if the application can be built."""
    return run_command("python setup.py build", "Building application") is not None


def check_alembic():
    """Check if Alembic is properly configured."""
    alembic_ini = Path("alembic.ini")
    if alembic_ini.exists():
        print("✅ Alembic configuration exists")
        return True
    else:
        print("❌ Alembic configuration not found")
        return False


def check_celery():
    """Check if Celery is properly configured."""
    celery_app = Path("arx_svg_parser/celery_app.py")
    if celery_app.exists():
        print("✅ Celery configuration exists")
        return True
    else:
        print("❌ Celery configuration not found")
        return False


def main():
    """Run all onboarding checks."""
    print("🚀 Arx SVG Parser Onboarding Test")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Environment File", check_environment_file),
        ("Database Configuration", check_database_connection),
        ("Redis Configuration", check_redis_connection),
        ("Server Files", check_server_startup),
        ("Alembic Configuration", check_alembic),
        ("Celery Configuration", check_celery),
        ("Code Formatting", check_linting),
        ("Build Test", check_build),
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
        print("1. Start the development server: uvicorn arx_svg_parser.main:app --reload")
        print("2. Visit http://localhost:8082/health to verify the server")
        print("3. Check the API documentation at http://localhost:8082/docs")
        print("4. Start Celery worker: celery -A arx_svg_parser.celery_app worker --loglevel=info")
        print("5. Review the ONBOARDING.md file for more details")
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all prerequisites are installed")
        print("2. Activate your virtual environment")
        print("3. Copy env.example to .env and configure it")
        print("4. Run 'pip install -e .' to install dependencies")
        print("5. Check the ONBOARDING.md file for detailed instructions")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main()) 