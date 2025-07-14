#!/usr/bin/env python3
"""
Unit tests for TypeScript SDK
Tests all major functionality including authentication, API calls, error handling
"""

import pytest
import subprocess
import json
from pathlib import Path
from typing import Dict, Any

class TestTypeScriptSDK:
    """Test suite for TypeScript SDK"""
    
    @pytest.fixture
    def sdk_path(self):
        """Get SDK path"""
        return Path("sdk/generated/typescript/arx-backend")
    
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
            "package.json",
            "tsconfig.json",
            "src/index.ts",
            "src/api/index.ts",
            "src/models/index.ts"
        ]
        
        for file_path in essential_files:
            assert (sdk_path / file_path).exists(), f"Essential file {file_path} should exist"
    
    def test_package_json_structure(self, sdk_path):
        """Test package.json structure and dependencies"""
        package_json = sdk_path / "package.json"
        assert package_json.exists(), "package.json should exist"
        
        with open(package_json, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ["name", "version", "description", "main", "types"]
        for field in required_fields:
            assert field in data, f"package.json should contain {field}"
        
        # Check dependencies
        assert "dependencies" in data, "package.json should have dependencies"
        assert "devDependencies" in data, "package.json should have devDependencies"
        
        # Check for required dependencies
        required_deps = ["axios", "typescript"]
        for dep in required_deps:
            assert dep in data.get("dependencies", {}), f"Should include {dep} dependency"
    
    def test_typescript_config(self, sdk_path):
        """Test TypeScript configuration"""
        tsconfig = sdk_path / "tsconfig.json"
        assert tsconfig.exists(), "tsconfig.json should exist"
        
        with open(tsconfig, 'r') as f:
            config = json.load(f)
        
        # Check essential TypeScript settings
        assert "compilerOptions" in config, "tsconfig.json should have compilerOptions"
        assert "target" in config["compilerOptions"], "Should specify TypeScript target"
        assert "module" in config["compilerOptions"], "Should specify module system"
        assert "declaration" in config["compilerOptions"], "Should generate declaration files"
    
    def test_api_structure(self, sdk_path):
        """Test API structure and exports"""
        api_index = sdk_path / "src" / "api" / "index.ts"
        assert api_index.exists(), "API index file should exist"
        
        # Check for main API modules
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
            module_file = sdk_path / "src" / "api" / f"{module}.ts"
            assert module_file.exists(), f"API module {module}.ts should exist"
    
    def test_models_structure(self, sdk_path):
        """Test models structure and type definitions"""
        models_index = sdk_path / "src" / "models" / "index.ts"
        assert models_index.exists(), "Models index file should exist"
        
        # Check for essential model types
        model_files = [
            "authentication.ts",
            "health.ts",
            "project.ts",
            "building.ts", 
            "bim_object.ts",
            "asset.ts",
            "cmms.ts",
            "maintenance.ts",
            "export.ts",
            "compliance.ts",
            "security.ts",
            "admin.ts",
            "symbol.ts",
            "chat.ts",
            "comment.ts",
            "drawing.ts",
            "markup.ts",
            "route.ts",
            "object.ts",
            "log.ts"
        ]
        
        for model_file in model_files:
            model_path = sdk_path / "src" / "models" / model_file
            assert model_path.exists(), f"Model file {model_file} should exist"
    
    def test_client_initialization(self, sdk_path):
        """Test client initialization and configuration"""
        client_file = sdk_path / "src" / "client.ts"
        assert client_file.exists(), "Client file should exist"
        
        # Check client class structure
        with open(client_file, 'r') as f:
            content = f.read()
        
        # Should have client class
        assert "class" in content, "Should have class definition"
        assert "constructor" in content, "Should have constructor"
        assert "baseURL" in content, "Should have baseURL configuration"
    
    def test_authentication_types(self, sdk_path):
        """Test authentication type definitions"""
        auth_file = sdk_path / "src" / "models" / "authentication.ts"
        assert auth_file.exists(), "Authentication models should exist"
        
        with open(auth_file, 'r') as f:
            content = f.read()
        
        # Should have authentication types
        assert "interface" in content, "Should have interface definitions"
        assert "LoginRequest" in content, "Should have LoginRequest interface"
        assert "LoginResponse" in content, "Should have LoginResponse interface"
        assert "AuthToken" in content, "Should have AuthToken interface"
    
    def test_error_handling(self, sdk_path):
        """Test error handling types and structures"""
        error_file = sdk_path / "src" / "models" / "error.ts"
        assert error_file.exists(), "Error models should exist"
        
        with open(error_file, 'r') as f:
            content = f.read()
        
        # Should have error types
        assert "interface" in content, "Should have error interface definitions"
        assert "ApiError" in content, "Should have ApiError interface"
        assert "ValidationError" in content, "Should have ValidationError interface"
    
    def test_compilation(self, sdk_path):
        """Test TypeScript compilation"""
        try:
            # Run TypeScript compilation
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )
            
            # Should compile without errors
            assert result.returncode == 0, f"TypeScript compilation failed: {result.stderr}"
            
        except subprocess.CalledProcessError as e:
            pytest.fail(f"TypeScript compilation error: {e}")
    
    def test_linting(self, sdk_path):
        """Test ESLint configuration and rules"""
        eslint_config = sdk_path / ".eslintrc.js"
        assert eslint_config.exists(), "ESLint config should exist"
        
        try:
            # Run ESLint
            result = subprocess.run(
                ["npx", "eslint", "src/", "--ext", ".ts"],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )
            
            # Should pass linting (warnings are OK, errors are not)
            if result.returncode != 0:
                print(f"ESLint warnings/errors: {result.stdout}")
                # Only fail on actual errors, not warnings
                if "error" in result.stdout.lower():
                    pytest.fail(f"ESLint errors found: {result.stdout}")
                    
        except subprocess.CalledProcessError as e:
            pytest.fail(f"ESLint error: {e}")
    
    def test_test_structure(self, sdk_path):
        """Test test file structure"""
        test_dir = sdk_path / "tests"
        assert test_dir.exists(), "Tests directory should exist"
        
        # Check for test files
        test_files = [
            "client.test.ts",
            "authentication.test.ts",
            "api.test.ts",
            "models.test.ts"
        ]
        
        for test_file in test_files:
            test_path = test_dir / test_file
            assert test_path.exists(), f"Test file {test_file} should exist"
    
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
            "basic-usage.ts",
            "authentication.ts",
            "api-calls.ts",
            "error-handling.ts"
        ]
        
        for example_file in example_files:
            example_path = examples_dir / example_file
            assert example_path.exists(), f"Example file {example_file} should exist"
    
    def test_export_structure(self, sdk_path):
        """Test module exports"""
        index_file = sdk_path / "src" / "index.ts"
        assert index_file.exists(), "Main index file should exist"
        
        with open(index_file, 'r') as f:
            content = f.read()
        
        # Should export main client
        assert "export" in content, "Should have exports"
        assert "ArxBackendClient" in content, "Should export ArxBackendClient"
    
    def test_type_definitions(self, sdk_path):
        """Test TypeScript type definitions"""
        types_file = sdk_path / "src" / "types.ts"
        if types_file.exists():
            with open(types_file, 'r') as f:
                content = f.read()
            
            # Should have type definitions
            assert "type" in content or "interface" in content, "Should have type definitions"
    
    def test_utilities(self, sdk_path):
        """Test utility functions"""
        utils_dir = sdk_path / "src" / "utils"
        if utils_dir.exists():
            utils_files = [
                "request.ts",
                "response.ts", 
                "validation.ts",
                "serialization.ts"
            ]
            
            for utils_file in utils_files:
                utils_path = utils_dir / utils_file
                if utils_path.exists():
                    with open(utils_path, 'r') as f:
                        content = f.read()
                    
                    # Should have function definitions
                    assert "function" in content or "const" in content, f"Utility file {utils_file} should have functions"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 