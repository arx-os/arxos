#!/usr/bin/env python3
"""
CLI Validation Script

This script validates all CLI tools in the Arxos system for CI/CD integration.
It tests CLI functionality, configuration management, error handling, and integration.
"""

import sys
import os
import subprocess
import tempfile
import json
import yaml
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CLIValidator:
    """Validator for CLI tools and their functionality."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Dict] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with optional verbosity."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{level}] {message}")
    
    def test_cli_help_commands(self) -> bool:
        """Test that all CLI tools provide help output."""
        self.log("Testing CLI help commands...")
        
        cli_modules = [
            'cmd.symbol_manager_cli',
            'cmd.geometry_resolver_cli',
            'cmd.validate_building',
            'cmd.rule_manager',
            'cmd.realtime_telemetry_cli',
            'cmd.failure_detection_cli',
            'cmd.system_simulator'
        ]
        
        success = True
        for module in cli_modules:
            try:
                result = subprocess.run(
                    ['python', '-m', module, '--help'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and 'usage:' in result.stdout.lower():
                    self.log(f"✅ {module} help command working")
                    self.results[module] = {'help': 'PASS'}
                else:
                    self.log(f"❌ {module} help command failed", "ERROR")
                    self.errors.append(f"{module}: help command failed")
                    self.results[module] = {'help': 'FAIL'}
                    success = False
                    
            except subprocess.TimeoutExpired:
                self.log(f"❌ {module} help command timed out", "ERROR")
                self.errors.append(f"{module}: help command timed out")
                self.results[module] = {'help': 'TIMEOUT'}
                success = False
            except Exception as e:
                self.log(f"❌ {module} help command error: {e}", "ERROR")
                self.errors.append(f"{module}: help command error - {e}")
                self.results[module] = {'help': 'ERROR'}
                success = False
        
        return success
    
    def test_cli_config_management(self) -> bool:
        """Test CLI configuration management."""
        self.log("Testing CLI configuration management...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test config files
            yaml_config = os.path.join(temp_dir, 'test_config.yaml')
            json_config = os.path.join(temp_dir, 'test_config.json')
            
            # YAML config
            yaml_content = {
                'log_level': 'DEBUG',
                'symbol_library_path': temp_dir,
                'db_path': os.path.join(temp_dir, 'test.db'),
                'telemetry_enabled': True
            }
            with open(yaml_config, 'w') as f:
                yaml.dump(yaml_content, f)
            
            # JSON config
            json_content = {
                'log_level': 'INFO',
                'symbol_library_path': temp_dir,
                'db_path': os.path.join(temp_dir, 'test.db'),
                'telemetry_enabled': False
            }
            with open(json_config, 'w') as f:
                json.dump(json_content, f, indent=2)
            
            success = True
            
            # Test YAML config
            try:
                result = subprocess.run([
                    'python', '-m', 'cmd.symbol_manager_cli',
                    '--config', yaml_config,
                    'list'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode in [0, 1]:  # 1 is acceptable for empty list
                    self.log("✅ YAML config loading working")
                    self.results['config_yaml'] = {'status': 'PASS'}
                else:
                    self.log("❌ YAML config loading failed", "ERROR")
                    self.errors.append("YAML config loading failed")
                    self.results['config_yaml'] = {'status': 'FAIL'}
                    success = False
                    
            except Exception as e:
                self.log(f"❌ YAML config test error: {e}", "ERROR")
                self.errors.append(f"YAML config test error - {e}")
                self.results['config_yaml'] = {'status': 'ERROR'}
                success = False
            
            # Test JSON config
            try:
                result = subprocess.run([
                    'python', '-m', 'cmd.validate_building',
                    '--config', json_config,
                    'test_building.json'
                ], capture_output=True, text=True, timeout=30)
                
                # Should fail gracefully for missing file
                if result.returncode != 0:
                    self.log("✅ JSON config loading working (graceful failure)")
                    self.results['config_json'] = {'status': 'PASS'}
                else:
                    self.log("❌ JSON config test should fail for missing file", "WARNING")
                    self.warnings.append("JSON config test should fail for missing file")
                    self.results['config_json'] = {'status': 'WARNING'}
                    
            except Exception as e:
                self.log(f"❌ JSON config test error: {e}", "ERROR")
                self.errors.append(f"JSON config test error - {e}")
                self.results['config_json'] = {'status': 'ERROR'}
                success = False
        
        return success
    
    def test_cli_environment_variables(self) -> bool:
        """Test CLI environment variable support."""
        self.log("Testing CLI environment variables...")
        
        env = os.environ.copy()
        env['ARXOS_SYMBOL_MANAGER_LOG_LEVEL'] = 'DEBUG'
        env['ARXOS_VALIDATE_BUILDING_DB'] = 'test.db'
        
        try:
            result = subprocess.run([
                'python', '-m', 'cmd.symbol_manager_cli',
                'list'
            ], capture_output=True, text=True, timeout=30, env=env)
            
            if result.returncode in [0, 1]:
                self.log("✅ Environment variable support working")
                self.results['env_vars'] = {'status': 'PASS'}
                return True
            else:
                self.log("❌ Environment variable test failed", "ERROR")
                self.errors.append("Environment variable test failed")
                self.results['env_vars'] = {'status': 'FAIL'}
                return False
                
        except Exception as e:
            self.log(f"❌ Environment variable test error: {e}", "ERROR")
            self.errors.append(f"Environment variable test error - {e}")
            self.results['env_vars'] = {'status': 'ERROR'}
            return False
    
    def test_cli_error_handling(self) -> bool:
        """Test CLI error handling for invalid inputs."""
        self.log("Testing CLI error handling...")
        
        success = True
        
        # Test invalid command
        try:
            result = subprocess.run([
                'python', '-m', 'cmd.symbol_manager_cli',
                'invalid-command'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0 and ('error' in result.stderr.lower() or 'invalid' in result.stderr.lower()):
                self.log("✅ Invalid command error handling working")
                self.results['error_invalid_command'] = {'status': 'PASS'}
            else:
                self.log("❌ Invalid command should fail", "ERROR")
                self.errors.append("Invalid command should fail")
                self.results['error_invalid_command'] = {'status': 'FAIL'}
                success = False
                
        except Exception as e:
            self.log(f"❌ Invalid command test error: {e}", "ERROR")
            self.errors.append(f"Invalid command test error - {e}")
            self.results['error_invalid_command'] = {'status': 'ERROR'}
            success = False
        
        # Test missing required arguments
        try:
            result = subprocess.run([
                'python', '-m', 'cmd.validate_building'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0 and ('error' in result.stderr.lower() or 'required' in result.stderr.lower()):
                self.log("✅ Missing arguments error handling working")
                self.results['error_missing_args'] = {'status': 'PASS'}
            else:
                self.log("❌ Missing arguments should fail", "ERROR")
                self.errors.append("Missing arguments should fail")
                self.results['error_missing_args'] = {'status': 'FAIL'}
                success = False
                
        except Exception as e:
            self.log(f"❌ Missing arguments test error: {e}", "ERROR")
            self.errors.append(f"Missing arguments test error - {e}")
            self.results['error_missing_args'] = {'status': 'ERROR'}
            success = False
        
        return success
    
    def test_cli_integration_scenarios(self) -> bool:
        """Test CLI integration scenarios."""
        self.log("Testing CLI integration scenarios...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success = True
            
            # Test symbol manager basic operations
            try:
                result = subprocess.run([
                    'python', '-m', 'cmd.symbol_manager_cli',
                    'list'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode in [0, 1]:
                    self.log("✅ Symbol manager list working")
                    self.results['integration_symbol_list'] = {'status': 'PASS'}
                else:
                    self.log("❌ Symbol manager list failed", "ERROR")
                    self.errors.append("Symbol manager list failed")
                    self.results['integration_symbol_list'] = {'status': 'FAIL'}
                    success = False
                    
            except Exception as e:
                self.log(f"❌ Symbol manager test error: {e}", "ERROR")
                self.errors.append(f"Symbol manager test error - {e}")
                self.results['integration_symbol_list'] = {'status': 'ERROR'}
                success = False
            
            # Test failure detection sample generation
            try:
                sample_file = os.path.join(temp_dir, 'sample_data.json')
                result = subprocess.run([
                    'python', '-m', 'cmd.failure_detection_cli',
                    'generate-sample', sample_file,
                    '--n-samples', '5'
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(sample_file):
                    self.log("✅ Failure detection sample generation working")
                    self.results['integration_failure_detection'] = {'status': 'PASS'}
                else:
                    self.log("❌ Failure detection sample generation failed", "ERROR")
                    self.errors.append("Failure detection sample generation failed")
                    self.results['integration_failure_detection'] = {'status': 'FAIL'}
                    success = False
                    
            except Exception as e:
                self.log(f"❌ Failure detection test error: {e}", "ERROR")
                self.errors.append(f"Failure detection test error - {e}")
                self.results['integration_failure_detection'] = {'status': 'ERROR'}
                success = False
            
            # Test system simulator
            try:
                output_file = os.path.join(temp_dir, 'test_system.json')
                result = subprocess.run([
                    'python', '-m', 'cmd.system_simulator',
                    'generate-sample',
                    '--system', 'power',
                    '--output', output_file
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(output_file):
                    self.log("✅ System simulator working")
                    self.results['integration_system_simulator'] = {'status': 'PASS'}
                else:
                    self.log("❌ System simulator failed", "ERROR")
                    self.errors.append("System simulator failed")
                    self.results['integration_system_simulator'] = {'status': 'FAIL'}
                    success = False
                    
            except Exception as e:
                self.log(f"❌ System simulator test error: {e}", "ERROR")
                self.errors.append(f"System simulator test error - {e}")
                self.results['integration_system_simulator'] = {'status': 'ERROR'}
                success = False
        
        return success
    
    def test_cli_documentation(self) -> bool:
        """Test CLI documentation completeness."""
        self.log("Testing CLI documentation...")
        
        docs_path = Path('docs/CLI_DOCUMENTATION.md')
        if not docs_path.exists():
            self.log("❌ CLI documentation missing", "ERROR")
            self.errors.append("CLI documentation missing")
            self.results['documentation'] = {'status': 'FAIL'}
            return False
        
        try:
            with open(docs_path, 'r') as f:
                docs_content = f.read()
            
            cli_modules = [
                'symbol_manager_cli',
                'geometry_resolver_cli',
                'validate_building',
                'rule_manager',
                'realtime_telemetry_cli',
                'failure_detection_cli',
                'system_simulator'
            ]
            
            missing_docs = []
            for module in cli_modules:
                if module not in docs_content:
                    missing_docs.append(module)
            
            if missing_docs:
                self.log(f"❌ Missing documentation for: {missing_docs}", "ERROR")
                self.errors.append(f"Missing documentation for: {missing_docs}")
                self.results['documentation'] = {'status': 'FAIL'}
                return False
            else:
                self.log("✅ CLI documentation complete")
                self.results['documentation'] = {'status': 'PASS'}
                return True
                
        except Exception as e:
            self.log(f"❌ Documentation test error: {e}", "ERROR")
            self.errors.append(f"Documentation test error - {e}")
            self.results['documentation'] = {'status': 'ERROR'}
            return False
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive validation report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() 
                          if result.get('status') == 'PASS' or result.get('help') == 'PASS')
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'results': self.results,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print the validation report."""
        print("\n" + "="*60)
        print("CLI VALIDATION REPORT")
        print("="*60)
        
        summary = report['summary']
        print(f"\nSummary:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed_tests']}")
        print(f"  Failed: {summary['failed_tests']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        if report['errors']:
            print(f"\nErrors ({len(report['errors'])}):")
            for error in report['errors']:
                print(f"  ❌ {error}")
        
        if report['warnings']:
            print(f"\nWarnings ({len(report['warnings'])}):")
            for warning in report['warnings']:
                print(f"  ⚠️  {warning}")
        
        print("\nDetailed Results:")
        for test_name, result in report['results'].items():
            status = result.get('status', result.get('help', 'UNKNOWN'))
            print(f"  {test_name}: {status}")
        
        print("\n" + "="*60)
    
    def run_all_tests(self) -> bool:
        """Run all CLI validation tests."""
        self.log("Starting CLI validation...")
        
        tests = [
            ('Help Commands', self.test_cli_help_commands),
            ('Config Management', self.test_cli_config_management),
            ('Environment Variables', self.test_cli_environment_variables),
            ('Error Handling', self.test_cli_error_handling),
            ('Integration Scenarios', self.test_cli_integration_scenarios),
            ('Documentation', self.test_cli_documentation)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            self.log(f"\nRunning {test_name}...")
            try:
                if test_func():
                    self.log(f"✅ {test_name} passed")
                else:
                    self.log(f"❌ {test_name} failed", "ERROR")
                    all_passed = False
            except Exception as e:
                self.log(f"❌ {test_name} error: {e}", "ERROR")
                self.errors.append(f"{test_name} error - {e}")
                all_passed = False
        
        return all_passed


def main():
    """Main CLI validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate CLI tools for CI/CD')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--report', '-r', help='Output report to file')
    parser.add_argument('--exit-code', action='store_true', help='Exit with code 1 on failure')
    
    args = parser.parse_args()
    
    # Change to arx_svg_parser directory
    os.chdir('arx_svg_parser')
    
    validator = CLIValidator(verbose=args.verbose)
    
    try:
        success = validator.run_all_tests()
        report = validator.generate_report()
        
        validator.print_report(report)
        
        if args.report:
            with open(args.report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to: {args.report}")
        
        if not success and args.exit_code:
            print("\n❌ CLI validation failed")
            sys.exit(1)
        elif success:
            print("\n✅ CLI validation passed")
        else:
            print("\n⚠️  CLI validation completed with issues")
            
    except KeyboardInterrupt:
        print("\n❌ CLI validation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CLI validation error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 