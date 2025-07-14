#!/usr/bin/env python3
"""
Unit tests for Python SDK
Tests all major functionality including authentication, API calls, error handling
"""

import pytest
import subprocess
import json
import ast
from pathlib import Path
from typing import Dict, Any

class TestPythonSDK:
    """Test suite for Python SDK"""
    
    @pytest.fixture
    def sdk_path(self):
        """Get SDK path"""
        return Path("sdk/generated/python/arx_backend")
    
    @pytest.fixture
    def test_config(self):
        """Test configuration"""
        return {
            "base_url": "http://localhost:8080",
            "test_user": "test-user",
            "test_password": "test-password",
            "test_token": "test-token-12345"
        }
    
    def test_sdk_structure(self, sdk_path):
        """Test SDK file structure"""
        assert sdk_path.exists(), "SDK directory should exist"
        
        # Check for essential files
        essential_files = [
            "setup.py",
            "pyproject.toml",
            "README.md",
            "arx_backend/__init__.py",
            "arx_backend/api/__init__.py",
            "arx_backend/models/__init__.py"
        ]
        
        for file_path in essential_files:
            assert (sdk_path / file_path).exists(), f"Essential file {file_path} should exist"
    
    def test_setup_py_structure(self, sdk_path):
        """Test setup.py structure and metadata"""
        setup_py = sdk_path / "setup.py"
        assert setup_py.exists(), "setup.py should exist"
        
        with open(setup_py, 'r') as f:
            content = f.read()
        
        # Check for essential setup.py components
        required_components = [
            "setup(",
            "name=",
            "version=",
            "description=",
            "install_requires=",
            "packages="
        ]
        
        for component in required_components:
            assert component in content, f"setup.py should contain {component}"
    
    def test_pyproject_toml_structure(self, sdk_path):
        """Test pyproject.toml structure"""
        pyproject_toml = sdk_path / "pyproject.toml"
        assert pyproject_toml.exists(), "pyproject.toml should exist"
        
        with open(pyproject_toml, 'r') as f:
            content = f.read()
        
        # Check for essential pyproject.toml sections
        required_sections = [
            "[build-system]",
            "[project]",
            "[project.optional-dependencies]"
        ]
        
        for section in required_sections:
            assert section in content, f"pyproject.toml should contain {section}"
    
    def test_package_structure(self, sdk_path):
        """Test package structure and imports"""
        package_dir = sdk_path / "arx_backend"
        assert package_dir.exists(), "Package directory should exist"
        
        # Check for main package files
        package_files = [
            "__init__.py",
            "api_client.py",
            "configuration.py",
            "exceptions.py"
        ]
        
        for file_name in package_files:
            file_path = package_dir / file_name
            assert file_path.exists(), f"Package file {file_name} should exist"
    
    def test_api_structure(self, sdk_path):
        """Test API structure and modules"""
        api_dir = sdk_path / "arx_backend" / "api"
        assert api_dir.exists(), "API directory should exist"
        
        # Check for API modules
        api_modules = [
            "authentication",
            "health",
            "projects",
            "buildings", 
            "bim_objects",
            "assets",
            "cmms",
            "maintenance",
            "export",
            "compliance",
            "security",
            "admin",
            "symbols",
            "chat",
            "comments",
            "drawings",
            "markup",
            "routes",
            "objects",
            "logs"
        ]
        
        for module in api_modules:
            module_file = api_dir / f"{module}.py"
            assert module_file.exists(), f"API module {module}.py should exist"
    
    def test_models_structure(self, sdk_path):
        """Test models structure and classes"""
        models_dir = sdk_path / "arx_backend" / "models"
        assert models_dir.exists(), "Models directory should exist"
        
        # Check for model files
        model_files = [
            "authentication.py",
            "health.py",
            "project.py",
            "building.py",
            "bim_object.py",
            "asset.py",
            "cmms.py",
            "maintenance.py",
            "export.py",
            "compliance.py",
            "security.py",
            "admin.py",
            "symbol.py",
            "chat.py",
            "comment.py",
            "drawing.py",
            "markup.py",
            "route.py",
            "object.py",
            "log.py"
        ]
        
        for model_file in model_files:
            model_path = models_dir / model_file
            assert model_path.exists(), f"Model file {model_file} should exist"
    
    def test_client_class(self, sdk_path):
        """Test client class structure"""
        client_file = sdk_path / "arx_backend" / "api_client.py"
        assert client_file.exists(), "API client file should exist"
        
        with open(client_file, 'r') as f:
            content = f.read()
        
        # Should have ApiClient class
        assert "class ApiClient" in content, "Should have ApiClient class"
        assert "def __init__" in content, "Should have __init__ method"
        assert "base_url" in content, "Should have base_url configuration"
    
    def test_authentication_models(self, sdk_path):
        """Test authentication model classes"""
        auth_file = sdk_path / "arx_backend" / "models" / "authentication.py"
        assert auth_file.exists(), "Authentication models should exist"
        
        with open(auth_file, 'r') as f:
            content = f.read()
        
        # Should have authentication classes
        assert "class" in content, "Should have class definitions"
        assert "LoginRequest" in content, "Should have LoginRequest class"
        assert "LoginResponse" in content, "Should have LoginResponse class"
        assert "AuthToken" in content, "Should have AuthToken class"
    
    def test_error_handling(self, sdk_path):
        """Test error handling classes"""
        exceptions_file = sdk_path / "arx_backend" / "exceptions.py"
        assert exceptions_file.exists(), "Exceptions file should exist"
        
        with open(exceptions_file, 'r') as f:
            content = f.read()
        
        # Should have exception classes
        assert "class" in content, "Should have exception class definitions"
        assert "ApiException" in content, "Should have ApiException class"
        assert "ValidationException" in content, "Should have ValidationException class"
    
    def test_syntax_validation(self, sdk_path):
        """Test Python syntax validation"""
        python_files = []
        
        # Find all Python files
        for py_file in sdk_path.rglob("*.py"):
            python_files.append(py_file)
        
        assert len(python_files) > 0, "Should have Python files"
        
        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                # Parse Python syntax
                ast.parse(content)
                
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file}: {e}")
    
    def test_imports(self, sdk_path):
        """Test import structure"""
        init_file = sdk_path / "arx_backend" / "__init__.py"
        assert init_file.exists(), "__init__.py should exist"
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Should have imports and exports
        assert "import" in content, "Should have imports"
        assert "from" in content, "Should have from imports"
        assert "ApiClient" in content, "Should export ApiClient"
    
    def test_dependencies(self, sdk_path):
        """Test dependency requirements"""
        setup_py = sdk_path / "setup.py"
        assert setup_py.exists(), "setup.py should exist"
        
        with open(setup_py, 'r') as f:
            content = f.read()
        
        # Should have required dependencies
        required_deps = ["requests", "urllib3", "python-dateutil"]
        for dep in required_deps:
            assert dep in content, f"Should include {dep} dependency"
    
    def test_type_hints(self, sdk_path):
        """Test type hint usage"""
        python_files = []
        
        # Find all Python files
        for py_file in sdk_path.rglob("*.py"):
            python_files.append(py_file)
        
        type_hint_count = 0
        
        for py_file in python_files:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Check for type hints
            if "->" in content or ":" in content:
                type_hint_count += 1
        
        # At least some files should have type hints
        assert type_hint_count > 0, "Should have type hints in some files"
    
    def test_documentation(self, sdk_path):
        """Test documentation structure"""
        readme = sdk_path / "README.md"
        assert readme.exists(), "README.md should exist"
        
        with open(readme, 'r') as f:
            content = f.read()
        
        # Should have essential documentation sections
        required_sections = [
            "# Arx Backend API Client",
            "## Installation",
            "## Usage",
            "## API Reference",
            "## Examples"
        ]
        
        for section in required_sections:
            assert section in content, f"README should contain {section}"
    
    def test_examples(self, sdk_path):
        """Test example files"""
        examples_dir = sdk_path / "examples"
        assert examples_dir.exists(), "Examples directory should exist"
        
        example_files = [
            "basic_usage.py",
            "authentication.py",
            "api_calls.py",
            "error_handling.py"
        ]
        
        for example_file in example_files:
            example_path = examples_dir / example_file
            assert example_path.exists(), f"Example file {example_file} should exist"
    
    def test_tests_structure(self, sdk_path):
        """Test test file structure"""
        tests_dir = sdk_path / "tests"
        assert tests_dir.exists(), "Tests directory should exist"
        
        # Check for test files
        test_files = [
            "test_client.py",
            "test_authentication.py",
            "test_api.py",
            "test_models.py"
        ]
        
        for test_file in test_files:
            test_path = tests_dir / test_file
            assert test_path.exists(), f"Test file {test_file} should exist"
    
    def test_configuration(self, sdk_path):
        """Test configuration structure"""
        config_file = sdk_path / "arx_backend" / "configuration.py"
        assert config_file.exists(), "Configuration file should exist"
        
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Should have configuration class
        assert "class Configuration" in content, "Should have Configuration class"
        assert "def __init__" in content, "Should have __init__ method"
        assert "base_url" in content, "Should have base_url configuration"
    
    def test_utilities(self, sdk_path):
        """Test utility functions"""
        utils_dir = sdk_path / "arx_backend" / "utils"
        if utils_dir.exists():
            utils_files = [
                "request.py",
                "response.py",
                "validation.py",
                "serialization.py"
            ]
            
            for utils_file in utils_files:
                utils_path = utils_dir / utils_file
                if utils_path.exists():
                    with open(utils_path, 'r') as f:
                        content = f.read()
                    
                    # Should have function definitions
                    assert "def " in content, f"Utility file {utils_file} should have functions"
    
    def test_async_support(self, sdk_path):
        """Test async/await support"""
        async_files = []
        
        # Find files with async support
        for py_file in sdk_path.rglob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()
            
            if "async def" in content or "await" in content:
                async_files.append(py_file)
        
        # Should have some async support
        assert len(async_files) > 0, "Should have async/await support in some files"
    
    def test_validation(self, sdk_path):
        """Test validation methods"""
        validation_count = 0
        
        # Check for validation methods
        for py_file in sdk_path.rglob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()
            
            if "validate" in content or "ValidationError" in content:
                validation_count += 1
        
        # Should have validation
        assert validation_count > 0, "Should have validation methods"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 