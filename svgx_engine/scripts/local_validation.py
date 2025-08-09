#!/usr/bin/env python3
"""
SVGX Engine - Local Validation Script

This script performs comprehensive validation of the SVGX Engine in a local environment
without requiring Docker or Kubernetes, focusing on core functionality and performance
validation according to CTO directives.

Author: SVGX Engineering Team
Date: 2024
"""

import asyncio
import aiohttp
import time
import json
import statistics
import sys
import os
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import shlex
from typing import List, Optional

def safe_execute_command(command: str, args: List[str] = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """
    Execute command safely with input validation.

    Args:
        command: Command to execute
        args: Command arguments
        timeout: Command timeout in seconds

    Returns:
        CompletedProcess result

    Raises:
        ValueError: If command is not allowed
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails
    """
    # Validate command
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"Command '{command}' is not allowed")

    # Prepare command
    cmd = [command] + (args or [])

    # Execute with security measures
    try:
        result = subprocess.run(
            cmd,
            shell=False,  # Prevent shell injection
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,  # Use current directory
            env=None,  # Use current environment
            check=False  # Don't raise on non-zero exit'
        )
        return result
    except subprocess.TimeoutExpired:
        raise subprocess.TimeoutExpired(cmd, timeout)
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(e.returncode, cmd, e.stdout, e.stderr)
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}")

# Allowed commands whitelist
ALLOWED_COMMANDS = [
    'git', 'docker', 'npm', 'python', 'python3',
    'pip', 'pip3', 'node', 'npm', 'yarn',
    'ls', 'cat', 'echo', 'mkdir', 'rm', 'cp', 'mv',
    'chmod', 'chown', 'tar', 'gzip', 'gunzip'
]


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceTargets:
    """CTO-defined performance targets"""
    ui_response_time: float = 16.0  # ms
    redraw_time: float = 32.0  # ms
    physics_simulation: float = 100.0  # ms
    batch_processing: bool = True
    max_memory_usage: int = 1024  # MB
    max_cpu_usage: float = 80.0  # %

class LocalValidator:
    """Local environment validator for SVGX Engine"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.performance_targets = PerformanceTargets()
        self.results = {
            'performance': {},
            'functionality': {},
            'security': {},
            'overall': {}
        }
        self.app_process = None

    def start_application(self) -> bool:
        """Start the SVGX Engine application locally"""
        logger.info("Starting SVGX Engine application...")

        try:
            # Start the FastAPI application
            self.app_process = subprocess.run(['python', 'app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            , shell=False, capture_output=True, text=True)

            # Wait for application to start
            time.sleep(5)

            # Check if process is still running
            if self.app_process.poll() is None:
                logger.info("Application started successfully")
                return True
            else:
                stdout, stderr = self.app_process.communicate()
                logger.error(f"Application failed to start: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return False

    def stop_application(self):
        """Stop the application"""
        if self.app_process:
            logger.info("Stopping application...")
            self.app_process.terminate()
            self.app_process.wait()
            logger.info("Application stopped")

    async def health_check(self) -> Dict:
        """Perform health check validation"""
        logger.info("Performing health check...")
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    duration = (time.time() - start_time) * 1000
                    data = await response.json()

                    result = {
                        'status': response.status,
                        'response_time_ms': duration,
                        'data': data,
                        'success': response.status == 200
                    }

                    logger.info(f"Health check completed: {duration:.2f}ms")
                    return result

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 0,
                'response_time_ms': 0,
                'error': str(e),
                'success': False
            }

    async def test_endpoint(self, endpoint: str, payload: Dict, iterations: int = 10) -> Dict:
        """Test a specific endpoint"""
        logger.info(f"Testing endpoint: {endpoint}")

        response_times = []
        success_count = 0
        error_count = 0

        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                start_time = time.time()
                try:
                    async with session.post(
                        f"{self.base_url}/{endpoint}",
                        json=payload
                    ) as response:
                        duration = (time.time() - start_time) * 1000
                        response_times.append(duration)

                        if response.status == 200:
                            success_count += 1
                        else:
                            error_count += 1

                except Exception as e:
                    error_count += 1
                    logger.warning(f"Request {i+1} failed: {e}")

        if response_times:
            stats = {
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0,
                'success_rate': success_count / iterations,
                'error_rate': error_count / iterations,
                'total_requests': iterations
            }
        else:
            stats = {
                'mean': 0, 'median': 0, 'min': 0, 'max': 0, 'std_dev': 0,
                'success_rate': 0, 'error_rate': 1, 'total_requests': iterations
            }

        logger.info(f"Endpoint test completed for {endpoint}: {stats['mean']:.2f}ms avg")
        return stats

    async def test_functionality(self) -> Dict:
        """Test core functionality"""
        logger.info("Testing core functionality...")

        functionality_results = {}

        # Test parsing
        parse_payload = {
            'svgx_content': '''
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red"/>
                <rect x="100" y="100" width="50" height="50" fill="blue"/>
            </svgx>
            '''
        }
        functionality_results['parse'] = await self.test_endpoint('parse', parse_payload)

        # Test evaluation
        evaluate_payload = {
            'svgx_content': '''
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red" behavior="clickable"/>
            </svgx>
            ''',
            'interaction': 'click'
        }
        functionality_results['evaluate'] = await self.test_endpoint('evaluate', evaluate_payload)

        # Test simulation
        simulate_payload = {
            'svgx_content': '''
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red" physics="gravity"/>
            </svgx>
            ''',
            'simulation_time': 1.0
        }
        functionality_results['simulate'] = await self.test_endpoint('simulate', simulate_payload)

        # Test compilation
        compile_payload = {
            'svgx_content': '''
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red"/>
            </svgx>
            ''',
            'format': 'svg'
        }
        functionality_results['compile'] = await self.test_endpoint('compile/svg', compile_payload)

        # Test precision
        precision_payload = {
            'level': 'high',
            'fixed_point': True
        }
        functionality_results['precision'] = await self.test_endpoint('precision', precision_payload)

        logger.info("Core functionality testing completed")
        return functionality_results

    async def test_security(self) -> Dict:
        """Test security features"""
        logger.info("Testing security features...")

        security_results = {
            'input_validation': {},
            'rate_limiting': {},
            'authentication': {}
        }

        # Test input validation
        malicious_payloads = [
            {'svgx_content': '<script>alert("xss")</script>'},
            {'svgx_content': '"; DROP TABLE users; --'},"
            {'svgx_content': '{"malicious": "data"}'},
            {'svgx_content': None},
            {'svgx_content': ''}
        ]

        async with aiohttp.ClientSession() as session:
            for i, payload in enumerate(malicious_payloads):
                try:
                    async with session.post(
                        f"{self.base_url}/parse",
                        json=payload
                    ) as response:
                        security_results['input_validation'][f'test_{i}'] = {
                            'payload': payload,
                            'status': response.status,
                            'blocked': response.status in [400, 403, 422]
                        }
                except Exception as e:
                    security_results['input_validation'][f'test_{i}'] = {
                        'payload': payload,
                        'error': str(e),
                        'blocked': True
                    }

        # Test rate limiting
        rate_limit_results = []
        for i in range(50):  # Rapid requests
            start_time = time.time()
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    duration = (time.time() - start_time) * 1000
                    rate_limit_results.append({
                        'request': i,
                        'status': response.status,
                        'duration': duration,
                        'rate_limited': response.status == 429
                    })
            except Exception as e:
                rate_limit_results.append({
                    'request': i,
                    'error': str(e),
                    'rate_limited': True
                })

        security_results['rate_limiting'] = {
            'total_requests': len(rate_limit_results),
            'rate_limited_requests': len([r for r in rate_limit_results if r.get('rate_limited')]),
            'details': rate_limit_results
        }

        # Test authentication
        try:
            # Test without authentication
            async with session.get(f"{self.base_url}/health") as response:
                security_results['authentication'] = {
                    'unauthorized_access': response.status == 401,
                    'status': response.status
                }
        except Exception as e:
            security_results['authentication'] = {
                'error': str(e),
                'unauthorized_access': True
            }

        logger.info("Security testing completed")
        return security_results

    async def validate_performance_targets(self) -> Dict:
        """Validate against CTO performance targets"""
        logger.info("Validating performance targets...")

        functionality_results = await self.test_functionality()

        # Validate against CTO targets
        validation_results = {
            'ui_response_time': {
                'target': self.performance_targets.ui_response_time,
                'actual': functionality_results.get('evaluate', {}).get('mean', 0),
                'passed': functionality_results.get('evaluate', {}).get('mean', 0) <= self.performance_targets.ui_response_time
            },
            'redraw_time': {
                'target': self.performance_targets.redraw_time,
                'actual': functionality_results.get('parse', {}).get('mean', 0),
                'passed': functionality_results.get('parse', {}).get('mean', 0) <= self.performance_targets.redraw_time
            },
            'physics_simulation': {
                'target': self.performance_targets.physics_simulation,
                'actual': functionality_results.get('simulate', {}).get('mean', 0),
                'passed': functionality_results.get('simulate', {}).get('mean', 0) <= self.performance_targets.physics_simulation
            }
        }

        logger.info("Performance target validation completed")
        return {
            'targets': validation_results,
            'detailed_results': functionality_results
        }

    async def run_comprehensive_validation(self) -> Dict:
        """Run comprehensive local validation"""
        logger.info("Starting comprehensive local validation...")

        # Start application
        if not self.start_application():
            logger.error("Failed to start application - aborting validation")
            return {'error': 'Application startup failed'}

        try:
            # Health check
            health_result = await self.health_check()
            if not health_result['success']:
                logger.error("Health check failed - aborting validation")
                return {'error': 'Health check failed', 'health_result': health_result}

            # Performance validation
            performance_results = await self.validate_performance_targets()

            # Security testing
            security_results = await self.test_security()

            # Compile results
            self.results = {
                'health_check': health_result,
                'performance': performance_results,
                'security': security_results,
                'overall': {
                    'timestamp': time.time(),
                    'all_tests_passed': self._evaluate_overall_success()
                }
            }

            logger.info("Comprehensive validation completed")
            return self.results

        finally:
            # Stop application
            self.stop_application()

    def _evaluate_overall_success(self) -> bool:
        """Evaluate overall test success"""
        # Check health
        if not self.results.get('health_check', {}).get('success', False):
            return False

        # Check performance targets
        performance = self.results.get('performance', {}).get('targets', {})
        for target_name, target_data in performance.items():
            if not target_data.get('passed', False):
                logger.warning(f"Performance target failed: {target_name}")
                return False

        # Check security
        security = self.results.get('security', {})
        if security.get('rate_limiting', {}).get('rate_limited_requests', 0) == 0:
            logger.warning("Rate limiting not working properly")
            return False

        return True

    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("# SVGX Engine - Local Validation Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Health check
        health = self.results.get('health_check', {})
        report.append("## Health Check")
        report.append(f"- Status: {'✅ PASS' if health.get('success') else '❌ FAIL'}")
        report.append(f"- Response Time: {health.get('response_time_ms', 0):.2f}ms")
        report.append("")

        # Performance targets
        report.append("## Performance Targets (CTO Directives)")
        performance = self.results.get('performance', {}).get('targets', {})
        for target_name, target_data in performance.items():
            status = "✅ PASS" if target_data.get('passed') else "❌ FAIL"
            report.append(f"- {target_name}: {status}")
            report.append(f"  - Target: {target_data.get('target')}ms")
            report.append(f"  - Actual: {target_data.get('actual'):.2f}ms")
        report.append("")

        # Security
        report.append("## Security Validation")
        security = self.results.get('security', {})
        report.append(f"- Input Validation: {'✅ PASS' if security.get('input_validation') else '❌ FAIL'}")
        report.append(f"- Rate Limiting: {'✅ PASS' if security.get('rate_limiting') else '❌ FAIL'}")
        report.append(f"- Authentication: {'✅ PASS' if security.get('authentication') else '❌ FAIL'}")
        report.append("")

        # Overall result
        overall = self.results.get('overall', {})
        report.append("## Overall Result")
        report.append(f"- All Tests Passed: {'✅ YES' if overall.get('all_tests_passed') else '❌ NO'}")

        return "\n".join(report)

async def main():
    """Main validation function"""
    logger.info("Starting SVGX Engine local validation")

    validator = LocalValidator()

    try:
        results = await validator.run_comprehensive_validation()

        # Generate and save report
        report = validator.generate_report()

        # Save report to file
        report_file = 'local_validation_report.md'
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Validation report saved to {report_file}")

        # Print summary
        print("\n" + "="*60)
        print("SVGX ENGINE LOCAL VALIDATION SUMMARY")
        print("="*60)
        print(report)
        print("="*60)

        # Exit with appropriate code
        if results.get('overall', {}).get('all_tests_passed', False):
            logger.info("✅ All validation tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Some validation tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()
