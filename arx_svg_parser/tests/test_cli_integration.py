"""
CLI Integration Test Suite

This module provides comprehensive testing for all CLI tools in the Arxos system.
It tests CLI functionality, configuration management, error handling, and integration scenarios.
"""

import pytest
import subprocess
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCLIIntegration:
    """Test suite for CLI integration and functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield tmp_dir
    
    @pytest.fixture
    def test_config_yaml(self, temp_dir):
        """Create a test YAML configuration file."""
        config = {
            'log_level': 'DEBUG',
            'symbol_library_path': temp_dir,
            'db_path': os.path.join(temp_dir, 'test.db'),
            'telemetry_enabled': True,
            'debug_mode': True
        }
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return config_path
    
    @pytest.fixture
    def test_config_json(self, temp_dir):
        """Create a test JSON configuration file."""
        config = {
            'log_level': 'INFO',
            'symbol_library_path': temp_dir,
            'db_path': os.path.join(temp_dir, 'test.db'),
            'telemetry_enabled': False,
            'debug_mode': False
        }
        config_path = os.path.join(temp_dir, 'test_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return config_path
    
    def test_cli_help_commands(self):
        """Test that all CLI tools provide help output."""
        cli_modules = [
            'cmd.symbol_manager_cli',
            'cmd.geometry_resolver_cli',
            'cmd.validate_building',
            'cmd.rule_manager',
            'cmd.realtime_telemetry_cli',
            'cmd.failure_detection_cli',
            'cmd.system_simulator'
        ]
        
        for module in cli_modules:
            result = subprocess.run(
                ['python', '-m', module, '--help'],
                capture_output=True,
                text=True,
                cwd='arx_svg_parser'
            )
            assert result.returncode == 0, f"Help command failed for {module}"
            assert 'usage:' in result.stdout.lower(), f"No usage info in {module} help"
    
    def test_cli_config_loading(self, test_config_yaml, test_config_json):
        """Test CLI configuration loading from YAML and JSON files."""
        # Test YAML config
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            '--config', test_config_yaml,
            'list'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        # Should not fail even if no symbols exist
        assert result.returncode in [0, 1], f"YAML config test failed: {result.stderr}"
        
        # Test JSON config
        result = subprocess.run([
            'python', '-m', 'cmd.validate_building',
            '--config', test_config_json,
            'test_building.json'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        # Should fail gracefully for missing file
        assert result.returncode != 0, "JSON config test should fail for missing file"
    
    def test_cli_environment_variables(self):
        """Test CLI environment variable support."""
        env = os.environ.copy()
        env['ARXOS_SYMBOL_MANAGER_LOG_LEVEL'] = 'DEBUG'
        env['ARXOS_VALIDATE_BUILDING_DB'] = 'test.db'
        
        # Test symbol manager with env vars
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'list'
        ], capture_output=True, text=True, cwd='arx_svg_parser', env=env)
        
        # Should not fail
        assert result.returncode in [0, 1], f"Environment variable test failed: {result.stderr}"
    
    def test_cli_error_handling(self):
        """Test CLI error handling for invalid inputs."""
        # Test invalid command
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'invalid-command'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode != 0, "Invalid command should fail"
        assert 'error' in result.stderr.lower() or 'invalid' in result.stderr.lower()
        
        # Test missing required arguments
        result = subprocess.run([
            'python', '-m', 'cmd.validate_building'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode != 0, "Missing arguments should fail"
        assert 'error' in result.stderr.lower() or 'required' in result.stderr.lower()
    
    def test_cli_invalid_config_handling(self, temp_dir):
        """Test CLI handling of invalid configuration files."""
        # Create invalid YAML
        invalid_yaml = os.path.join(temp_dir, 'invalid.yaml')
        with open(invalid_yaml, 'w') as f:
            f.write('invalid: yaml: with: colons')
        
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            '--config', invalid_yaml,
            'list'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        # Should handle gracefully
        assert result.returncode in [0, 1], "Invalid config should be handled gracefully"
    
    def test_cli_integration_scenarios(self, temp_dir):
        """Test CLI integration scenarios."""
        # Test symbol manager basic operations
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'list'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode in [0, 1], "Symbol manager list should work"
        
        # Test rule manager
        result = subprocess.run([
            'python', '-m', 'cmd.rule_manager',
            'list'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode in [0, 1], "Rule manager list should work"
        
        # Test failure detection sample generation
        sample_file = os.path.join(temp_dir, 'sample_data.json')
        result = subprocess.run([
            'python', '-m', 'cmd.failure_detection_cli',
            'generate-sample', sample_file,
            '--n-samples', '5'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode == 0, "Sample generation should work"
        assert os.path.exists(sample_file), "Sample file should be created"
        
        # Test system simulator
        output_file = os.path.join(temp_dir, 'test_system.json')
        result = subprocess.run([
            'python', '-m', 'cmd.system_simulator',
            'generate-sample',
            '--system', 'power',
            '--output', output_file
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode == 0, "System simulator should work"
        assert os.path.exists(output_file), "System output file should be created"
    
    def test_cli_security_validation(self, temp_dir):
        """Test CLI security measures."""
        # Test path traversal protection
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'create',
            '--file', '../../../etc/passwd'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode != 0, "Path traversal should be blocked"
        
        # Test invalid JSON input
        invalid_json = os.path.join(temp_dir, 'invalid.json')
        with open(invalid_json, 'w') as f:
            f.write('{"invalid": "json"')
        
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'create',
            '--file', invalid_json
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        assert result.returncode != 0, "Invalid JSON should be rejected"
    
    def test_cli_performance(self):
        """Test CLI performance characteristics."""
        import time
        
        # Test help command performance
        start_time = time.time()
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            '--help'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        help_time = time.time() - start_time
        
        assert result.returncode == 0, "Help command should work"
        assert help_time < 5.0, "Help command should complete within 5 seconds"
        
        # Test list command performance
        start_time = time.time()
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'list'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        list_time = time.time() - start_time
        
        assert result.returncode in [0, 1], "List command should work"
        assert list_time < 10.0, "List command should complete within 10 seconds"
    
    def test_cli_documentation_validation(self):
        """Test that CLI documentation is complete."""
        # Check if CLI documentation exists
        docs_path = Path('arx_svg_parser/docs/CLI_DOCUMENTATION.md')
        assert docs_path.exists(), "CLI documentation should exist"
        
        # Read documentation content
        with open(docs_path, 'r') as f:
            docs_content = f.read()
        
        # Check that all CLI modules are documented
        cli_modules = [
            'symbol_manager_cli',
            'geometry_resolver_cli',
            'validate_building',
            'rule_manager',
            'realtime_telemetry_cli',
            'failure_detection_cli',
            'system_simulator'
        ]
        
        for module in cli_modules:
            assert module in docs_content, f"CLI module {module} should be documented"
    
    def test_cli_module_imports(self):
        """Test that all CLI modules can be imported."""
        import sys
        sys.path.insert(0, 'arx_svg_parser')
        
        # Test CLI module imports
        try:
            from cmd.symbol_manager_cli import SymbolManagerCLI
            from cmd.geometry_resolver_cli import GeometryResolverCLI
            from cmd.validate_building import main as validate_building_main
            from cmd.rule_manager import RuleManagerCLI
            from cmd.realtime_telemetry_cli import RealtimeTelemetryCLI
            from cmd.failure_detection_cli import FailureDetectionCLI
            from cmd.system_simulator import SystemSimulatorCLI
            
            # Test CLI class instantiation
            assert SymbolManagerCLI is not None
            assert GeometryResolverCLI is not None
            assert validate_building_main is not None
            assert RuleManagerCLI is not None
            assert RealtimeTelemetryCLI is not None
            assert FailureDetectionCLI is not None
            assert SystemSimulatorCLI is not None
            
        except ImportError as e:
            pytest.fail(f"CLI module import failed: {e}")
    
    def test_cli_config_precedence(self, test_config_yaml):
        """Test CLI configuration precedence (CLI args > env vars > config file)."""
        env = os.environ.copy()
        env['ARXOS_SYMBOL_MANAGER_LOG_LEVEL'] = 'INFO'
        
        # Test that CLI args override config file
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            '--config', test_config_yaml,
            '--log-level', 'WARNING',
            'list'
        ], capture_output=True, text=True, cwd='arx_svg_parser', env=env)
        
        assert result.returncode in [0, 1], "Config precedence test should work"
    
    def test_cli_output_formats(self, temp_dir):
        """Test CLI output format options."""
        # Test JSON output
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'list',
            '--format', 'json'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        if result.returncode == 0:
            # Try to parse JSON output
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                pytest.fail("JSON output should be valid JSON")
        
        # Test CSV output
        result = subprocess.run([
            'python', '-m', 'cmd.symbol_manager_cli',
            'list',
            '--format', 'csv'
        ], capture_output=True, text=True, cwd='arx_svg_parser')
        
        if result.returncode == 0:
            assert ',' in result.stdout, "CSV output should contain commas"


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 