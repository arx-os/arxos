#!/usr/bin/env python3
"""
Development Setup Script

This script sets up the Arxos development environment using the modern
dependency management approach with pyproject.toml.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description, check=True):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(f"✅ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return None


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")


def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return

    print("🔄 Creating virtual environment...")
    run_command("python -m venv venv", "Creating virtual environment")


def install_dependencies():
    """Install project dependencies."""
    # Install the project in editable mode with development dependencies
    run_command(
        "pip install -e '.[dev]'", "Installing project with development dependencies"
    )

    # Verify installation
    run_command(
        "python -c 'import application; print(\"✅ Application module imported\")'",
        "Verifying application module",
    )
    run_command(
        "python -c 'import api; print(\"✅ API module imported\")'",
        "Verifying API module",
    )


def setup_pre_commit():
    """Set up pre-commit hooks."""
    run_command("pre-commit install", "Installing pre-commit hooks")


def run_tests():
    """Run the test suite to verify setup."""
    print("🧪 Running test suite...")
    result = run_command(
        "python tests/test_integration_simple.py",
        "Running integration tests",
        check=False,
    )

    if result and result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("⚠️ Some tests failed - check the output above")


def create_env_file():
    """Create a .env file with default settings."""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return

    print("🔄 Creating .env file...")
    env_content = """# Arxos Development Environment

# Application Settings
ARXOS_ENV=development
ARXOS_DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=arxos
DB_USER=arxos_user
DB_PASSWORD=arxos_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Cache Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=10
REDIS_TTL_DEFAULT=3600

# Message Queue Settings
MQ_HOST=localhost
MQ_PORT=5672
MQ_VIRTUAL_HOST=/

# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=development

# Security Settings
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXIRE_MINUTES=30

# MCP-Engineering Settings
MCP_BUILDING_VALIDATION_API_KEY=your-api-key
MCP_COMPLIANCE_CHECKING_API_KEY=your-api-key
MCP_AI_RECOMMENDATIONS_API_KEY=your-api-key
MCP_KNOWLEDGE_BASE_API_KEY=your-api-key
MCP_ML_PREDICTIONS_API_KEY=your-api-key
"""

    with open(env_file, "w") as f:
        f.write(env_content)
    print("✅ .env file created")


def main():
    """Main setup function."""
    print("🚀 Setting up Arxos Development Environment")
    print("=" * 50)

    # Check Python version
    check_python_version()

    # Create virtual environment
    create_virtual_environment()

    # Install dependencies
    install_dependencies()

    # Set up pre-commit hooks
    setup_pre_commit()

    # Create .env file
    create_env_file()

    # Run tests
    run_tests()

    print("\n🎉 Development environment setup complete!")
    print("\n📋 Next Steps:")
    print("1. Activate virtual environment: source venv/bin/activate")
    print("2. Start the API server: python -m uvicorn api.main:app --reload")
    print("3. Run tests: pytest")
    print("4. Format code: black .")
    print("5. Check code quality: flake8")

    print("\n📚 Documentation:")
    print("- README.md: Project overview and quick start")
    print("- docs/: Detailed documentation")
    print("- application/services/README.md: Service architecture guide")


if __name__ == "__main__":
    main()
