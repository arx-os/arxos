#!/usr/bin/env python3
"""
Environment setup script for Arxos SVG-BIM Integration System.

This script sets up the Python environment, creates a virtual environment,
installs dependencies, and configures the development environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Optional


def run_command(command: List[str], cwd: Optional[Path] = None) -> bool:
    """
    Run a command and return success status.
    
    Args:
        command: Command to run
        cwd: Working directory
        
    Returns:
        True if command succeeded, False otherwise
    """
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Command completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Command failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def create_virtual_environment(venv_path: Path) -> bool:
    """
    Create a virtual environment.
    
    Args:
        venv_path: Path to virtual environment
        
    Returns:
        True if successful, False otherwise
    """
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return True
    
    print(f"Creating virtual environment at {venv_path}")
    return run_command([sys.executable, "-m", "venv", str(venv_path)])


def get_pip_command(venv_path: Path) -> List[str]:
    """Get the pip command for the virtual environment."""
    if platform.system() == "Windows":
        return [str(venv_path / "Scripts" / "pip.exe")]
    else:
        return [str(venv_path / "bin" / "pip")]


def get_python_command(venv_path: Path) -> List[str]:
    """Get the python command for the virtual environment."""
    if platform.system() == "Windows":
        return [str(venv_path / "Scripts" / "python.exe")]
    else:
        return [str(venv_path / "bin" / "python")]


def install_dependencies(venv_path: Path) -> bool:
    """
    Install project dependencies.
    
    Args:
        venv_path: Path to virtual environment
        
    Returns:
        True if successful, False otherwise
    """
    pip_cmd = get_pip_command(venv_path)
    
    # Upgrade pip
    if not run_command(pip_cmd + ["install", "--upgrade", "pip"]):
        return False
    
    # Install dependencies
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        if not run_command(pip_cmd + ["install", "-r", "requirements.txt"]):
            return False
    else:
        print("Warning: requirements.txt not found")
    
    # Install development dependencies
    if not run_command(pip_cmd + ["install", "-e", ".[dev]"]):
        return False
    
    return True


def create_directories() -> bool:
    """Create necessary directories."""
    directories = [
        "logs",
        "data",
        "data/partitions",
        "data/sample_rules",
        "data/versions",
        "tests/data",
        "docs/build",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True


def create_env_file() -> bool:
    """Create .env file with default configuration."""
    env_content = """# Arxos SVG-BIM Integration System Environment Configuration

# Application Settings
APP_NAME=arx_svg_parser
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=development

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/arx_svg_parser.log
LOG_JSON=true
LOG_CONSOLE=true
LOG_FILE_ENABLED=true
LOG_FORMAT=json

# Database Configuration
DATABASE_URL=sqlite:///./data/arx_svg_parser.db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true

# Security Configuration
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
CORS_ALLOW_CREDENTIALS=true

# Redis Configuration (for background tasks)
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Symbol Library Configuration
SYMBOL_LIBRARY_PATH=../arx-symbol-library
SYMBOL_CACHE_SIZE=1000
SYMBOL_CACHE_TTL=3600

# Validation Configuration
VALIDATION_ENABLED=true
SCHEMA_STRICT_MODE=false
VALIDATION_REPORT_PATH=logs/validation_reports

# Performance Configuration
MAX_FILE_SIZE=10485760  # 10MB
MAX_CONCURRENT_UPLOADS=5
BATCH_PROCESSING_SIZE=100

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_ENABLED=true

# Development Configuration
ENABLE_DEBUG_ENDPOINTS=false
ENABLE_SWAGGER_UI=true
ENABLE_REDOC=true
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        env_file.write_text(env_content)
        print("✓ Created .env file with default configuration")
        print("⚠️  Please update the secret keys in .env file for production use")
    else:
        print("✓ .env file already exists")
    
    return True


def run_tests(venv_path: Path) -> bool:
    """
    Run basic tests to verify installation.
    
    Args:
        venv_path: Path to virtual environment
        
    Returns:
        True if tests pass, False otherwise
    """
    python_cmd = get_python_command(venv_path)
    
    print("Running basic tests...")
    return run_command(python_cmd + ["-m", "pytest", "tests/", "-v", "--tb=short"])


def main():
    """Main setup function."""
    print("🚀 Setting up Arxos SVG-BIM Integration System")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Create virtual environment
    venv_path = project_root / "venv"
    if not create_virtual_environment(venv_path):
        print("Failed to create virtual environment")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("Failed to create directories")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("Failed to create .env file")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(venv_path):
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Run tests
    if not run_tests(venv_path):
        print("⚠️  Some tests failed, but setup completed")
    else:
        print("✓ All tests passed")
    
    print("\n" + "=" * 50)
    print("✅ Environment setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"   {venv_path}\\Scripts\\activate")
    else:
        print(f"   source {venv_path}/bin/activate")
    print("2. Update the .env file with your configuration")
    print("3. Run the application:")
    print("   python -m arx_svg_parser.main")
    print("4. Or start the development server:")
    print("   uvicorn arx_svg_parser.api.main:app --reload")
    print("\nFor more information, see the README.md file.")


if __name__ == "__main__":
    main() 