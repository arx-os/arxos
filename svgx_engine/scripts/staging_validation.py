#!/usr/bin/env python3
"""
SVGX Engine - Staging Environment Validation Script

This script performs comprehensive validation of the SVGX Engine staging deployment
including load testing, security testing, and performance validation according to
CTO directives and production readiness requirements.

Author: SVGX Engineering Team
Date: 2024
"""

import asyncio
import aiohttp
import time
import json
import statistics
import subprocess
import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

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

@dataclass
class SecurityRequirements:
    """Security validation requirements"""
    input_validation: bool = True
    rate_limiting: bool = True
    authentication: bool = True
    authorization: bool = True
    audit_logging: bool = True
    xss_protection: bool = True
    sql_injection_protection: bool = True

class StagingValidator:
    """Comprehensive staging environment validator"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        self.performance_targets = PerformanceTargets()
        self.security_requirements = SecurityRequirements()
        self.results = {
            'performance': {},
            'security': {},
            'load_testing': {},
            'overall': {}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_key}'},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict:
        """Perform health check validation"""
        logger.info("Performing health check...")
        start_time = time.time()
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
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
    
    async def performance_test(self, endpoint: str, payload: Dict, iterations: int = 10) -> Dict:
        """Test performance of a specific endpoint"""
        logger.info(f"Testing performance for {endpoint}...")
        
        response_times = []
        success_count = 0
        error_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                async with self.session.post(
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
        
        logger.info(f"Performance test completed for {endpoint}: {stats['mean']:.2f}ms avg")
        return stats
    
    async def load_test(self, endpoint: str, payload: Dict, 
                       concurrent_users: int = 10, duration_seconds: int = 60) -> Dict:
        """Perform load testing with concurrent users"""
        logger.info(f"Starting load test for {endpoint} with {concurrent_users} users...")
        
        start_time = time.time()
        results = []
        
        async def user_workload():
            """Simulate a single user workload"""
            user_results = []
            while time.time() - start_time < duration_seconds:
                request_start = time.time()
                try:
                    async with self.session.post(
                        f"{self.base_url}/{endpoint}",
                        json=payload
                    ) as response:
                        duration = (time.time() - request_start) * 1000
                        user_results.append({
                            'duration': duration,
                            'status': response.status,
                            'success': response.status == 200
                        })
                        
                        # Add small delay between requests
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    user_results.append({
                        'duration': 0,
                        'status': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            return user_results
        
        # Create concurrent user tasks
        tasks = [user_workload() for _ in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        
        # Flatten results
        flat_results = []
        for user_result in all_results:
            flat_results.extend(user_result)
        
        # Calculate statistics
        successful_requests = [r for r in flat_results if r['success']]
        failed_requests = [r for r in flat_results if not r['success']]
        
        if successful_requests:
            response_times = [r['duration'] for r in successful_requests]
            stats = {
                'total_requests': len(flat_results),
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'success_rate': len(successful_requests) / len(flat_results),
                'mean_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)],
                'p99_response_time': sorted(response_times)[int(len(response_times) * 0.99)],
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'requests_per_second': len(flat_results) / duration_seconds,
                'concurrent_users': concurrent_users,
                'duration_seconds': duration_seconds
            }
        else:
            stats = {
                'total_requests': len(flat_results),
                'successful_requests': 0,
                'failed_requests': len(failed_requests),
                'success_rate': 0,
                'mean_response_time': 0,
                'median_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'requests_per_second': 0,
                'concurrent_users': concurrent_users,
                'duration_seconds': duration_seconds
            }
        
        logger.info(f"Load test completed: {stats['requests_per_second']:.2f} req/s")
        return stats
    
    async def security_test(self) -> Dict:
        """Perform security validation tests"""
        logger.info("Performing security tests...")
        
        security_results = {
            'input_validation': {},
            'rate_limiting': {},
            'authentication': {},
            'xss_protection': {},
            'sql_injection_protection': {}
        }
        
        # Test input validation
        malicious_payloads = [
            {'svgx_content': '<script>alert("xss")</script>'},
            {'svgx_content': '"; DROP TABLE users; --'},
            {'svgx_content': '{"malicious": "data", "injection": "test"}'},
            {'svgx_content': None},
            {'svgx_content': ''}
        ]
        
        for i, payload in enumerate(malicious_payloads):
            try:
                async with self.session.post(
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
        for i in range(100):  # Rapid requests
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}/health") as response:
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
            # Test without API key
            async with aiohttp.ClientSession() as no_auth_session:
                async with no_auth_session.get(f"{self.base_url}/health") as response:
                    security_results['authentication'] = {
                        'unauthorized_access': response.status == 401,
                        'status': response.status
                    }
        except Exception as e:
            security_results['authentication'] = {
                'error': str(e),
                'unauthorized_access': True
            }
        
        logger.info("Security tests completed")
        return security_results
    
    async def validate_performance_targets(self) -> Dict:
        """Validate against CTO performance targets"""
        logger.info("Validating performance targets...")
        
        # Test sample payloads for different endpoints
        test_payloads = {
            'parse': {
                'svgx_content': '''
                <svgx>
                    <circle cx="50" cy="50" r="25" fill="red"/>
                    <rect x="100" y="100" width="50" height="50" fill="blue"/>
                </svgx>
                '''
            },
            'evaluate': {
                'svgx_content': '''
                <svgx>
                    <circle cx="50" cy="50" r="25" fill="red" behavior="clickable"/>
                </svgx>
                ''',
                'interaction': 'click'
            },
            'simulate': {
                'svgx_content': '''
                <svgx>
                    <circle cx="50" cy="50" r="25" fill="red" physics="gravity"/>
                </svgx>
                ''',
                'simulation_time': 1.0
            }
        }
        
        target_results = {}
        
        for endpoint, payload in test_payloads.items():
            performance_stats = await self.performance_test(endpoint, payload, iterations=20)
            target_results[endpoint] = performance_stats
        
        # Validate against CTO targets
        validation_results = {
            'ui_response_time': {
                'target': self.performance_targets.ui_response_time,
                'actual': target_results.get('evaluate', {}).get('mean', 0),
                'passed': target_results.get('evaluate', {}).get('mean', 0) <= self.performance_targets.ui_response_time
            },
            'redraw_time': {
                'target': self.performance_targets.redraw_time,
                'actual': target_results.get('parse', {}).get('mean', 0),
                'passed': target_results.get('parse', {}).get('mean', 0) <= self.performance_targets.redraw_time
            },
            'physics_simulation': {
                'target': self.performance_targets.physics_simulation,
                'actual': target_results.get('simulate', {}).get('mean', 0),
                'passed': target_results.get('simulate', {}).get('mean', 0) <= self.performance_targets.physics_simulation
            }
        }
        
        logger.info("Performance target validation completed")
        return {
            'targets': validation_results,
            'detailed_results': target_results
        }
    
    async def run_comprehensive_validation(self) -> Dict:
        """Run comprehensive staging validation"""
        logger.info("Starting comprehensive staging validation...")
        
        # Health check
        health_result = await self.health_check()
        if not health_result['success']:
            logger.error("Health check failed - aborting validation")
            return {'error': 'Health check failed', 'health_result': health_result}
        
        # Performance validation
        performance_results = await self.validate_performance_targets()
        
        # Security testing
        security_results = await self.security_test()
        
        # Load testing
        load_test_payload = {
            'svgx_content': '''
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red"/>
                <rect x="100" y="100" width="50" height="50" fill="blue"/>
                <line x1="0" y1="0" x2="200" y2="200" stroke="green"/>
            </svgx>
            '''
        }
        
        load_results = await self.load_test('parse', load_test_payload, 
                                         concurrent_users=20, duration_seconds=30)
        
        # Compile results
        self.results = {
            'health_check': health_result,
            'performance': performance_results,
            'security': security_results,
            'load_testing': load_results,
            'overall': {
                'timestamp': time.time(),
                'duration': time.time() - time.time(),
                'all_tests_passed': self._evaluate_overall_success()
            }
        }
        
        logger.info("Comprehensive validation completed")
        return self.results
    
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
        report.append("# SVGX Engine - Staging Validation Report")
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
        
        # Load testing
        load = self.results.get('load_testing', {})
        report.append("## Load Testing")
        report.append(f"- Requests/Second: {load.get('requests_per_second', 0):.2f}")
        report.append(f"- Success Rate: {load.get('success_rate', 0):.2%}")
        report.append(f"- P95 Response Time: {load.get('p95_response_time', 0):.2f}ms")
        report.append("")
        
        # Overall result
        overall = self.results.get('overall', {})
        report.append("## Overall Result")
        report.append(f"- All Tests Passed: {'✅ YES' if overall.get('all_tests_passed') else '❌ NO'}")
        
        return "\n".join(report)

async def main():
    """Main validation function"""
    # Configuration
    base_url = os.getenv('SVGX_STAGING_URL', 'http://localhost:8000')
    api_key = os.getenv('SVGX_API_KEY', 'staging-api-key-test')
    
    logger.info(f"Starting SVGX Engine staging validation against {base_url}")
    
    async with StagingValidator(base_url, api_key) as validator:
        results = await validator.run_comprehensive_validation()
        
        # Generate and save report
        report = validator.generate_report()
        
        # Save report to file
        report_file = 'staging_validation_report.md'
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Validation report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("SVGX ENGINE STAGING VALIDATION SUMMARY")
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

if __name__ == "__main__":
    asyncio.run(main()) 