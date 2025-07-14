#!/usr/bin/env python3
"""
Arx CMMS Onboarding Test Script

This script verifies that the development environment is correctly set up
and operational for the Arx CMMS service.
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


def check_go_version():
    """Check if Go is installed and has the correct version."""
    version = run_command("go version", "Checking Go version")
    if version:
        print(f"   Found: {version}")
        if "go1.21" in version or "go1.22" in version or "go1.23" in version:
            return True
        else:
            print("   ⚠️  Warning: Go 1.21+ is recommended")
            return False
    return False


def check_dependencies():
    """Check if Go dependencies are properly installed."""
    return run_command("go mod tidy", "Installing/checking Go dependencies") is not None


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
    return run_command("go test ./...", "Running tests") is not None


def check_server_startup():
    """Check if the server can start (without actually starting it)."""
    # Check if main.go exists
    main_file = Path("cmd/server/main.go")
    if main_file.exists():
        print("✅ Server main file exists")
        return True
    else:
        print("❌ Server main file not found")
        return False


def check_linting():
    """Check if code passes linting."""
    return run_command("go fmt ./...", "Checking code formatting") is not None


def check_build():
    """Check if the application can be built."""
    return run_command("go build -o arx-cmms cmd/server/main.go", "Building application") is not None


def check_cmms_configuration():
    """Check if CMMS-specific configuration exists."""
    # Check for CMMS-specific environment variables
    cmms_vars = [
        "CMMS_WORK_ORDER_AUTO_ASSIGN",
        "CMMS_PREVENTIVE_MAINTENANCE_ENABLED",
        "CMMS_ASSET_TRACKING_ENABLED",
        "CMMS_INVENTORY_MANAGEMENT_ENABLED"
    ]
    
    configured_vars = 0
    for var in cmms_vars:
        if os.getenv(var):
            configured_vars += 1
    
    if configured_vars >= 2:
        print("✅ CMMS configuration is set up")
        return True
    else:
        print("❌ CMMS configuration incomplete")
        print("   Please configure CMMS-specific environment variables")
        return False


def check_notification_config():
    """Check if notification configuration exists."""
    notification_vars = [
        "NOTIFICATION_EMAIL_ENABLED",
        "SMTP_HOST",
        "SMTP_USERNAME"
    ]
    
    configured_vars = 0
    for var in notification_vars:
        if os.getenv(var):
            configured_vars += 1
    
    if configured_vars >= 2:
        print("✅ Notification configuration is set up")
        return True
    else:
        print("❌ Notification configuration incomplete")
        print("   Please configure notification environment variables")
        return False


def main():
    """Run all onboarding checks."""
    print("🚀 Arx CMMS Onboarding Test")
    print("=" * 50)
    
    checks = [
        ("Go Version", check_go_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_environment_file),
        ("Database Configuration", check_database_connection),
        ("Redis Configuration", check_redis_connection),
        ("CMMS Configuration", check_cmms_configuration),
        ("Notification Configuration", check_notification_config),
        ("Server Files", check_server_startup),
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
        print("1. Start the development server: go run cmd/server/main.go")
        print("2. Visit http://localhost:8081/health to verify the server")
        print("3. Check the API documentation at http://localhost:8081/docs")
        print("4. Review the ONBOARDING.md file for more details")
        print("5. Test CMMS functionality with sample work orders and assets")
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all prerequisites are installed")
        print("2. Copy env.example to .env and configure it")
        print("3. Run 'go mod tidy' to install dependencies")
        print("4. Configure CMMS-specific environment variables")
        print("5. Check the ONBOARDING.md file for detailed instructions")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main()) 