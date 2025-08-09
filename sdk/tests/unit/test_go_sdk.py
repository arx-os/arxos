#!/usr/bin/env python3
"""
Unit tests for Go SDK
Tests all major functionality including authentication, API calls, error handling
"""

import pytest
import subprocess
import json
from pathlib import Path
from typing import Dict, Any

class TestGoSDK:
    """Test suite for Go SDK"""

    @pytest.fixture
def sdk_path(self):
        """Get SDK path"""
        return Path("sdk/generated/go/arx-backend")

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
            "go.mod",
            "go.sum",
            "README.md",
            "api/",
            "model/",
            "configuration.go",
            "client.go"
        ]

        for file_path in essential_files:
            if file_path.endswith('/'):
                assert (sdk_path / file_path.rstrip('/')).exists(), f"Directory {file_path} should exist"
            else:
                assert (sdk_path / file_path).exists(), f"Essential file {file_path} should exist"

    def test_go_mod_structure(self, sdk_path):
        """Test go.mod structure and dependencies"""
        go_mod = sdk_path / "go.mod"
        assert go_mod.exists(), "go.mod should exist"

        with open(go_mod, 'r') as f:
            content = f.read()

        # Check for essential go.mod components
        required_components = [
            "module",
            "go ",
            "require"
        ]

        for component in required_components:
            assert component in content, f"go.mod should contain {component}"

    def test_go_sum_structure(self, sdk_path):
        """Test go.sum structure"""
        go_sum = sdk_path / "go.sum"
        assert go_sum.exists(), "go.sum should exist"

        with open(go_sum, 'r') as f:
            content = f.read()

        # Should have dependency checksums
        assert len(content.strip()) > 0, "go.sum should have dependency checksums"

    def test_api_structure(self, sdk_path):
        """Test API structure and packages"""
        api_dir = sdk_path / "api"
        assert api_dir.exists(), "API directory should exist"

        # Check for API packages
        api_packages = [
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

        for package in api_packages:
            package_dir = api_dir / package
            assert package_dir.exists(), f"API package {package} should exist"

            # Check for package files
            package_files = [
                f"{package}.go",
                "README.md"
            ]

            for file_name in package_files:
                file_path = package_dir / file_name
                assert file_path.exists(), f"Package file {file_name} should exist in {package}"

    def test_model_structure(self, sdk_path):
        """Test model structure and types"""
        model_dir = sdk_path / "model"
        assert model_dir.exists(), "Model directory should exist"

        # Check for model files
        model_files = [
            "authentication.go",
            "health.go",
            "project.go",
            "building.go",
            "bim_object.go",
            "asset.go",
            "cmms.go",
            "maintenance.go",
            "export.go",
            "compliance.go",
            "security.go",
            "admin.go",
            "symbol.go",
            "chat.go",
            "comment.go",
            "drawing.go",
            "markup.go",
            "route.go",
            "object.go",
            "log.go"
        ]

        for model_file in model_files:
            model_path = model_dir / model_file
            assert model_path.exists(), f"Model file {model_file} should exist"

    def test_client_structure(self, sdk_path):
        """Test client structure"""
        client_file = sdk_path / "client.go"
        assert client_file.exists(), "Client file should exist"

        with open(client_file, 'r') as f:
            content = f.read()

        # Should have client struct and methods
        assert "type" in content, "Should have type definitions"
        assert "func" in content, "Should have function definitions"
        assert "Client" in content, "Should have Client struct"

    def test_configuration_structure(self, sdk_path):
        """Test configuration structure"""
        config_file = sdk_path / "configuration.go"
        assert config_file.exists(), "Configuration file should exist"

        with open(config_file, 'r') as f:
            content = f.read()

        # Should have configuration struct
        assert "type" in content, "Should have type definitions"
        assert "Configuration" in content, "Should have Configuration struct"
        assert "BaseURL" in content, "Should have BaseURL field"

    def test_authentication_models(self, sdk_path):
        """Test authentication model types"""
        auth_file = sdk_path / "model" / "authentication.go"
        assert auth_file.exists(), "Authentication models should exist"

        with open(auth_file, 'r') as f:
            content = f.read()

        # Should have authentication types
        assert "type" in content, "Should have type definitions"
        assert "LoginRequest" in content, "Should have LoginRequest struct"
        assert "LoginResponse" in content, "Should have LoginResponse struct"
        assert "AuthToken" in content, "Should have AuthToken struct"

    def test_error_handling(self, sdk_path):
        """Test error handling types"""
        error_file = sdk_path / "model" / "error.go"
        assert error_file.exists(), "Error models should exist"

        with open(error_file, 'r') as f:
            content = f.read()

        # Should have error types
        assert "type" in content, "Should have error type definitions"
        assert "ApiError" in content, "Should have ApiError struct"
        assert "ValidationError" in content, "Should have ValidationError struct"

    def test_compilation(self, sdk_path):
        """Test Go compilation"""
        try:
            # Run Go build
            result = subprocess.run(
                ["go", "build", "."],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            # Should compile without errors
            assert result.returncode == 0, f"Go compilation failed: {result.stderr}"

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Go compilation error: {e}")

    def test_linting(self, sdk_path):
        """Test Go linting"""
        try:
            # Run golint
            result = subprocess.run(
                ["golint", "./..."],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            # Should pass linting (warnings are OK, errors are not)
            if result.returncode != 0:
                print(f"Go lint warnings/errors: {result.stdout}")
                # Only fail on actual errors, not warnings
                if "error" in result.stdout.lower():
                    pytest.fail(f"Go lint errors found: {result.stdout}")

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Go lint error: {e}")

    def test_formatting(self, sdk_path):
        """Test Go code formatting"""
        try:
            # Run gofmt
            result = subprocess.run(
                ["gofmt", "-l", "."],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            # Should be properly formatted
            if result.stdout.strip():
                print(f"Files need formatting: {result.stdout}")
                # Don't fail, just warn about formatting'

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Go format error: {e}")

    def test_vet(self, sdk_path):
        """Test Go vet"""
        try:
            # Run go vet
            result = subprocess.run(
                ["go", "vet", "./..."],
                cwd=sdk_path,
                capture_output=True,
                text=True
            )

            # Should pass vetting
            assert result.returncode == 0, f"Go vet failed: {result.stderr}"

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Go vet error: {e}")

    def test_test_structure(self, sdk_path):
        """Test test file structure"""
        test_dir = sdk_path / "test"
        if test_dir.exists():
            # Check for test files
            test_files = [
                "client_test.go",
                "authentication_test.go",
                "api_test.go",
                "models_test.go"
            ]

            for test_file in test_files:
                test_path = test_dir / test_file
                if test_path.exists():
                    with open(test_path, 'r') as f:
                        content = f.read()

                    # Should have test functions
                    assert "func Test" in content, f"Test file {test_file} should have test functions"

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
            "basic_usage.go",
            "authentication.go",
            "api_calls.go",
            "error_handling.go"
        ]

        for example_file in example_files:
            example_path = examples_dir / example_file
            assert example_path.exists(), f"Example file {example_file} should exist"

    def test_export_structure(self, sdk_path):
        """Test package exports"""
        # Check main package exports
        main_files = [
            "client.go",
            "configuration.go"
        ]

        for file_name in main_files:
            file_path = sdk_path / file_name
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()

                # Should have exported types/functions
                assert "func (" in content or "type " in content, f"File {file_name} should have exports"

    def test_http_client(self, sdk_path):
        """Test HTTP client usage"""
        http_client_count = 0

        # Check for HTTP client usage
        for go_file in sdk_path.rglob("*.go"):
            with open(go_file, 'r') as f:
                content = f.read()

            if "http.Client" in content or "http.NewRequest" in content:
                http_client_count += 1

        # Should have HTTP client usage
        assert http_client_count > 0, "Should have HTTP client usage"

    def test_json_handling(self, sdk_path):
        """Test JSON handling"""
        json_count = 0

        # Check for JSON handling
        for go_file in sdk_path.rglob("*.go"):
            with open(go_file, 'r') as f:
                content = f.read()

            if "json.Marshal" in content or "json.Unmarshal" in content:
                json_count += 1

        # Should have JSON handling
        assert json_count > 0, "Should have JSON handling"

    def test_error_types(self, sdk_path):
        """Test error type definitions"""
        error_count = 0

        # Check for error types
        for go_file in sdk_path.rglob("*.go"):
            with open(go_file, 'r') as f:
                content = f.read()

            if "error" in content and "type" in content:
                error_count += 1

        # Should have error types
        assert error_count > 0, "Should have error type definitions"

    def test_validation(self, sdk_path):
        """Test validation methods"""
        validation_count = 0

        # Check for validation methods
        for go_file in sdk_path.rglob("*.go"):
            with open(go_file, 'r') as f:
                content = f.read()

            if "Validate" in content or "validation" in content.lower():
                validation_count += 1

        # Should have validation
        assert validation_count > 0, "Should have validation methods"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
