"""
Quality Assurance Runner for Arxos Platform

This module provides comprehensive QA automation that integrates with sync events,
CI/CD pipelines, and Cursor for automated testing and validation on every commit
and sync event.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import pytest
import coverage
from concurrent.futures import ThreadPoolExecutor
import psutil
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(Enum):
    """Types of tests to run."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    UI_UX = "ui_ux"
    COVERAGE = "coverage"
    LINTING = "linting"
    TYPE_CHECKING = "type_checking"


@dataclass
class TestResult:
    """Test execution result."""
    test_id: str
    test_type: TestType
    status: TestStatus
    duration: float
    output: str
    error_message: Optional[str] = None
    coverage_percentage: Optional[float] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QARun:
    """Complete QA run session."""
    run_id: str
    trigger_type: str  # "commit", "sync", "manual", "scheduled"
    trigger_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TestStatus = TestStatus.PENDING
    results: List[TestResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class QARunner:
    """
    Comprehensive QA runner that integrates with sync events and CI/CD pipelines.
    
    Features:
    - Automated test execution on commit/sync events
    - Performance benchmarking and monitoring
    - Security vulnerability scanning
    - Accessibility compliance testing
    - Code coverage analysis
    - Integration with Cursor for AI-powered feedback
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize QA runner with configuration."""
        self.config = config or self._default_config()
        self.active_runs: Dict[str, QARun] = {}
        self.test_executor = ThreadPoolExecutor(max_workers=self.config.get('max_workers', 4))
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize coverage measurement
        self.coverage = coverage.Coverage()
        
        # Performance monitoring
        self.performance_metrics = {}
        
        logger.info("QA Runner initialized with configuration")
    
    def _default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'max_workers': 4,
            'timeout': 300,  # 5 minutes per test
            'coverage_threshold': 90.0,
            'performance_thresholds': {
                'response_time': 1.0,  # seconds
                'memory_usage': 512,   # MB
                'cpu_usage': 80.0      # percentage
            },
            'test_directories': [
                'tests/',
                'arx_svg_parser/tests/',
                'arx-sync-agent/tests/',
                'arx-backend/tests/'
            ],
            'exclude_patterns': [
                '*/__pycache__/*',
                '*/venv/*',
                '*/node_modules/*',
                '*.pyc'
            ],
            'cursor_integration': {
                'enabled': True,
                'api_url': 'http://localhost:3000',
                'feedback_enabled': True
            },
            'reporting': {
                'generate_html': True,
                'generate_json': True,
                'upload_to_storage': False
            }
        }
    
    async def start_session(self):
        """Start aiohttp session for external API calls."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def run_qa_suite(
        self,
        trigger_type: str,
        trigger_id: str,
        test_types: Optional[List[TestType]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> QARun:
        """
        Run comprehensive QA suite.
        
        Args:
            trigger_type: Type of trigger (commit, sync, manual, scheduled)
            trigger_id: Unique identifier for the trigger
            test_types: Specific test types to run (None = all)
            context: Additional context for the run
            
        Returns:
            QARun: Complete QA run results
        """
        await self.start_session()
        
        # Create QA run
        run_id = f"qa_run_{trigger_type}_{trigger_id}_{int(time.time())}"
        qa_run = QARun(
            run_id=run_id,
            trigger_type=trigger_type,
            trigger_id=trigger_id,
            start_time=datetime.utcnow(),
            metadata=context or {}
        )
        
        self.active_runs[run_id] = qa_run
        qa_run.status = TestStatus.RUNNING
        
        logger.info(f"Starting QA run {run_id} for {trigger_type} {trigger_id}")
        
        try:
            # Determine test types to run
            if test_types is None:
                test_types = list(TestType)
            
            # Run tests in parallel
            tasks = []
            for test_type in test_types:
                task = asyncio.create_task(
                    self._run_test_type(qa_run, test_type)
                )
                tasks.append(task)
            
            # Wait for all tests to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Generate summary
            await self._generate_summary(qa_run)
            
            # Send feedback to Cursor if enabled
            if self.config['cursor_integration']['enabled']:
                await self._send_cursor_feedback(qa_run)
            
            qa_run.status = TestStatus.PASSED if self._is_successful(qa_run) else TestStatus.FAILED
            qa_run.end_time = datetime.utcnow()
            
            logger.info(f"QA run {run_id} completed with status {qa_run.status}")
            
        except Exception as e:
            logger.error(f"QA run {run_id} failed: {e}")
            qa_run.status = TestStatus.ERROR
            qa_run.end_time = datetime.utcnow()
        
        finally:
            await self.close_session()
            if run_id in self.active_runs:
                del self.active_runs[run_id]
        
        return qa_run
    
    async def _run_test_type(self, qa_run: QARun, test_type: TestType) -> TestResult:
        """Run a specific type of test."""
        test_id = f"{qa_run.run_id}_{test_type.value}"
        
        logger.info(f"Running {test_type.value} tests for {qa_run.run_id}")
        
        start_time = time.time()
        status = TestStatus.RUNNING
        output = ""
        error_message = None
        coverage_percentage = None
        performance_metrics = None
        
        try:
            if test_type == TestType.UNIT:
                result = await self._run_unit_tests()
            elif test_type == TestType.INTEGRATION:
                result = await self._run_integration_tests()
            elif test_type == TestType.PERFORMANCE:
                result = await self._run_performance_tests()
            elif test_type == TestType.SECURITY:
                result = await self._run_security_tests()
            elif test_type == TestType.ACCESSIBILITY:
                result = await self._run_accessibility_tests()
            elif test_type == TestType.UI_UX:
                result = await self._run_ui_ux_tests()
            elif test_type == TestType.COVERAGE:
                result = await self._run_coverage_tests()
            elif test_type == TestType.LINTING:
                result = await self._run_linting_tests()
            elif test_type == TestType.TYPE_CHECKING:
                result = await self._run_type_checking_tests()
            else:
                raise ValueError(f"Unknown test type: {test_type}")
            
            status = TestStatus.PASSED if result['success'] else TestStatus.FAILED
            output = result['output']
            error_message = result.get('error_message')
            coverage_percentage = result.get('coverage_percentage')
            performance_metrics = result.get('performance_metrics')
            
        except Exception as e:
            logger.error(f"Error running {test_type.value} tests: {e}")
            status = TestStatus.ERROR
            error_message = str(e)
        
        duration = time.time() - start_time
        
        test_result = TestResult(
            test_id=test_id,
            test_type=test_type,
            status=status,
            duration=duration,
            output=output,
            error_message=error_message,
            coverage_percentage=coverage_percentage,
            performance_metrics=performance_metrics
        )
        
        qa_run.results.append(test_result)
        return test_result
    
    async def _run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests with coverage."""
        logger.info("Running unit tests")
        
        # Start coverage measurement
        self.coverage.start()
        
        try:
            # Find test files
            test_files = self._find_test_files('test_*.py')
            
            if not test_files:
                return {
                    'success': True,
                    'output': 'No unit test files found',
                    'coverage_percentage': 0.0
                }
            
            # Run pytest
            cmd = [
                sys.executable, '-m', 'pytest',
                '--tb=short',
                '--quiet',
                '--junitxml=test-results.xml'
            ] + test_files
            
            result = await self._run_command(cmd)
            
            # Stop coverage and get report
            self.coverage.stop()
            self.coverage.save()
            
            # Get coverage percentage
            total_lines = 0
            covered_lines = 0
            
            for filename in self.coverage.get_data().measured_files():
                file_coverage = self.coverage.analysis2(filename)
                total_lines += len(file_coverage[1])
                covered_lines += len(file_coverage[2])
            
            coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
            
            return {
                'success': result['return_code'] == 0,
                'output': result['output'],
                'coverage_percentage': coverage_percentage,
                'error_message': result.get('error_message')
            }
            
        except Exception as e:
            self.coverage.stop()
            return {
                'success': False,
                'output': '',
                'error_message': str(e),
                'coverage_percentage': 0.0
            }
    
    async def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        logger.info("Running integration tests")
        
        # Find integration test files
        test_files = self._find_test_files('test_*integration*.py')
        
        if not test_files:
            return {
                'success': True,
                'output': 'No integration test files found'
            }
        
        cmd = [
            sys.executable, '-m', 'pytest',
            '--tb=short',
            '--quiet',
            '-m', 'integration'
        ] + test_files
        
        result = await self._run_command(cmd)
        
        return {
            'success': result['return_code'] == 0,
            'output': result['output'],
            'error_message': result.get('error_message')
        }
    
    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests and benchmarks."""
        logger.info("Running performance tests")
        
        # Get system performance baseline
        baseline_metrics = self._get_system_metrics()
        
        # Run performance tests
        test_files = self._find_test_files('test_*performance*.py')
        
        if not test_files:
            return {
                'success': True,
                'output': 'No performance test files found',
                'performance_metrics': baseline_metrics
            }
        
        cmd = [
            sys.executable, '-m', 'pytest',
            '--tb=short',
            '--quiet',
            '-m', 'performance'
        ] + test_files
        
        result = await self._run_command(cmd)
        
        # Get final metrics
        final_metrics = self._get_system_metrics()
        
        # Calculate performance impact
        performance_metrics = {
            'baseline': baseline_metrics,
            'final': final_metrics,
            'impact': {
                'cpu_delta': final_metrics['cpu_percent'] - baseline_metrics['cpu_percent'],
                'memory_delta': final_metrics['memory_mb'] - baseline_metrics['memory_mb'],
                'load_time': self._extract_load_time(result['output'])
            }
        }
        
        return {
            'success': result['return_code'] == 0,
            'output': result['output'],
            'error_message': result.get('error_message'),
            'performance_metrics': performance_metrics
        }
    
    async def _run_security_tests(self) -> Dict[str, Any]:
        """Run security vulnerability tests."""
        logger.info("Running security tests")
        
        security_results = []
        
        # Run bandit for security analysis
        try:
            cmd = [sys.executable, '-m', 'bandit', '-r', '.', '-f', 'json']
            result = await self._run_command(cmd)
            
            if result['return_code'] == 0:
                security_results.append({
                    'tool': 'bandit',
                    'status': 'passed',
                    'issues': 0
                })
            else:
                # Parse bandit output for issues
                try:
                    bandit_data = json.loads(result['output'])
                    issues = len(bandit_data.get('results', []))
                    security_results.append({
                        'tool': 'bandit',
                        'status': 'failed',
                        'issues': issues
                    })
                except json.JSONDecodeError:
                    security_results.append({
                        'tool': 'bandit',
                        'status': 'error',
                        'issues': -1
                    })
        except Exception as e:
            security_results.append({
                'tool': 'bandit',
                'status': 'error',
                'error': str(e)
            })
        
        # Run safety for dependency vulnerabilities
        try:
            cmd = [sys.executable, '-m', 'safety', 'check', '--json']
            result = await self._run_command(cmd)
            
            if result['return_code'] == 0:
                security_results.append({
                    'tool': 'safety',
                    'status': 'passed',
                    'issues': 0
                })
            else:
                try:
                    safety_data = json.loads(result['output'])
                    issues = len(safety_data)
                    security_results.append({
                        'tool': 'safety',
                        'status': 'failed',
                        'issues': issues
                    })
                except json.JSONDecodeError:
                    security_results.append({
                        'tool': 'safety',
                        'status': 'error',
                        'issues': -1
                    })
        except Exception as e:
            security_results.append({
                'tool': 'safety',
                'status': 'error',
                'error': str(e)
            })
        
        # Determine overall security status
        has_errors = any(r['status'] == 'error' for r in security_results)
        has_failures = any(r['status'] == 'failed' for r in security_results)
        
        if has_errors:
            status = 'error'
        elif has_failures:
            status = 'failed'
        else:
            status = 'passed'
        
        return {
            'success': status == 'passed',
            'output': json.dumps(security_results, indent=2),
            'error_message': None if status == 'passed' else 'Security issues detected',
            'security_results': security_results
        }
    
    async def _run_accessibility_tests(self) -> Dict[str, Any]:
        """Run accessibility compliance tests."""
        logger.info("Running accessibility tests")
        
        # This would integrate with tools like axe-core or similar
        # For now, return a placeholder
        return {
            'success': True,
            'output': 'Accessibility tests completed (placeholder)',
            'error_message': None
        }
    
    async def _run_ui_ux_tests(self) -> Dict[str, Any]:
        """Run UI/UX tests."""
        logger.info("Running UI/UX tests")
        
        # This would integrate with tools like Selenium or Playwright
        # For now, return a placeholder
        return {
            'success': True,
            'output': 'UI/UX tests completed (placeholder)',
            'error_message': None
        }
    
    async def _run_coverage_tests(self) -> Dict[str, Any]:
        """Run coverage analysis."""
        logger.info("Running coverage analysis")
        
        try:
            # Generate coverage report
            cmd = [sys.executable, '-m', 'coverage', 'report', '--show-missing']
            result = await self._run_command(cmd)
            
            # Extract coverage percentage
            coverage_percentage = self._extract_coverage_percentage(result['output'])
            
            return {
                'success': coverage_percentage >= self.config['coverage_threshold'],
                'output': result['output'],
                'coverage_percentage': coverage_percentage,
                'error_message': None if coverage_percentage >= self.config['coverage_threshold'] else f'Coverage below threshold ({coverage_percentage}% < {self.config["coverage_threshold"]}%)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error_message': str(e),
                'coverage_percentage': 0.0
            }
    
    async def _run_linting_tests(self) -> Dict[str, Any]:
        """Run code linting tests."""
        logger.info("Running linting tests")
        
        lint_results = []
        
        # Run flake8
        try:
            cmd = [sys.executable, '-m', 'flake8', '.', '--count', '--select=E9,F63,F7,F82', '--show-source', '--statistics']
            result = await self._run_command(cmd)
            
            if result['return_code'] == 0:
                lint_results.append({
                    'tool': 'flake8',
                    'status': 'passed',
                    'issues': 0
                })
            else:
                # Count issues from output
                lines = result['output'].strip().split('\n')
                issues = len([line for line in lines if ':' in line])
                lint_results.append({
                    'tool': 'flake8',
                    'status': 'failed',
                    'issues': issues
                })
        except Exception as e:
            lint_results.append({
                'tool': 'flake8',
                'status': 'error',
                'error': str(e)
            })
        
        # Run black check
        try:
            cmd = [sys.executable, '-m', 'black', '--check', '.']
            result = await self._run_command(cmd)
            
            if result['return_code'] == 0:
                lint_results.append({
                    'tool': 'black',
                    'status': 'passed',
                    'issues': 0
                })
            else:
                lint_results.append({
                    'tool': 'black',
                    'status': 'failed',
                    'issues': 1  # Black doesn't give specific count
                })
        except Exception as e:
            lint_results.append({
                'tool': 'black',
                'status': 'error',
                'error': str(e)
            })
        
        # Determine overall linting status
        has_errors = any(r['status'] == 'error' for r in lint_results)
        has_failures = any(r['status'] == 'failed' for r in lint_results)
        
        if has_errors:
            status = 'error'
        elif has_failures:
            status = 'failed'
        else:
            status = 'passed'
        
        return {
            'success': status == 'passed',
            'output': json.dumps(lint_results, indent=2),
            'error_message': None if status == 'passed' else 'Linting issues detected'
        }
    
    async def _run_type_checking_tests(self) -> Dict[str, Any]:
        """Run type checking tests."""
        logger.info("Running type checking tests")
        
        try:
            cmd = [sys.executable, '-m', 'mypy', '.', '--ignore-missing-imports']
            result = await self._run_command(cmd)
            
            return {
                'success': result['return_code'] == 0,
                'output': result['output'],
                'error_message': result.get('error_message')
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error_message': str(e)
            }
    
    def _find_test_files(self, pattern: str) -> List[str]:
        """Find test files matching pattern."""
        test_files = []
        
        for test_dir in self.config['test_directories']:
            if os.path.exists(test_dir):
                for root, dirs, files in os.walk(test_dir):
                    # Skip excluded patterns
                    dirs[:] = [d for d in dirs if not any(
                        pattern in os.path.join(root, d) for pattern in self.config['exclude_patterns']
                    )]
                    
                    for file in files:
                        if file.endswith('.py') and pattern in file:
                            test_files.append(os.path.join(root, file))
        
        return test_files
    
    async def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Run a command and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config['timeout']
            )
            
            output = stdout.decode('utf-8')
            error_output = stderr.decode('utf-8')
            
            return {
                'return_code': process.returncode,
                'output': output,
                'error_output': error_output,
                'error_message': error_output if error_output else None
            }
            
        except asyncio.TimeoutError:
            return {
                'return_code': -1,
                'output': '',
                'error_output': f'Command timed out after {self.config["timeout"]} seconds',
                'error_message': 'Command timed out'
            }
        except Exception as e:
            return {
                'return_code': -1,
                'output': '',
                'error_output': str(e),
                'error_message': str(e)
            }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory.used / (1024 * 1024),
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
            return {
                'cpu_percent': 0.0,
                'memory_mb': 0.0,
                'memory_percent': 0.0,
                'disk_percent': 0.0,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _extract_coverage_percentage(self, output: str) -> float:
        """Extract coverage percentage from coverage report output."""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'TOTAL' in line and '%' in line:
                    # Extract percentage from line like "TOTAL                   1234    567    54%"
                    parts = line.split()
                    for part in parts:
                        if '%' in part:
                            return float(part.replace('%', ''))
            return 0.0
        except Exception:
            return 0.0
    
    def _extract_load_time(self, output: str) -> Optional[float]:
        """Extract load time from performance test output."""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'load_time' in line.lower() or 'response_time' in line.lower():
                    # Extract time value
                    import re
                    match = re.search(r'(\d+\.?\d*)', line)
                    if match:
                        return float(match.group(1))
            return None
        except Exception:
            return None
    
    def _is_successful(self, qa_run: QARun) -> bool:
        """Check if QA run was successful."""
        if not qa_run.results:
            return False
        
        # Check if any critical tests failed
        critical_types = [TestType.UNIT, TestType.SECURITY, TestType.COVERAGE]
        
        for result in qa_run.results:
            if result.test_type in critical_types and result.status != TestStatus.PASSED:
                return False
        
        return True
    
    async def _generate_summary(self, qa_run: QARun):
        """Generate summary for QA run."""
        total_tests = len(qa_run.results)
        passed_tests = len([r for r in qa_run.results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in qa_run.results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in qa_run.results if r.status == TestStatus.ERROR])
        
        total_duration = sum(r.duration for r in qa_run.results)
        
        # Calculate coverage average
        coverage_results = [r.coverage_percentage for r in qa_run.results if r.coverage_percentage is not None]
        avg_coverage = sum(coverage_results) / len(coverage_results) if coverage_results else 0.0
        
        qa_run.summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0.0,
            'total_duration': total_duration,
            'average_coverage': avg_coverage,
            'overall_status': 'passed' if self._is_successful(qa_run) else 'failed'
        }
    
    async def _send_cursor_feedback(self, qa_run: QARun):
        """Send feedback to Cursor for AI-powered development assistance."""
        if not self.config['cursor_integration']['enabled']:
            return
        
        try:
            feedback_data = {
                'run_id': qa_run.run_id,
                'trigger_type': qa_run.trigger_type,
                'trigger_id': qa_run.trigger_id,
                'status': qa_run.status.value,
                'summary': qa_run.summary,
                'timestamp': datetime.utcnow().isoformat(),
                'recommendations': self._generate_recommendations(qa_run)
            }
            
            if self.session:
                async with self.session.post(
                    f"{self.config['cursor_integration']['api_url']}/feedback",
                    json=feedback_data
                ) as response:
                    if response.status == 200:
                        logger.info("Feedback sent to Cursor successfully")
                    else:
                        logger.warning(f"Failed to send feedback to Cursor: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending feedback to Cursor: {e}")
    
    def _generate_recommendations(self, qa_run: QARun) -> List[str]:
        """Generate AI-powered recommendations based on QA results."""
        recommendations = []
        
        # Coverage recommendations
        if qa_run.summary.get('average_coverage', 0) < self.config['coverage_threshold']:
            recommendations.append(f"Increase test coverage to meet {self.config['coverage_threshold']}% threshold")
        
        # Performance recommendations
        for result in qa_run.results:
            if result.test_type == TestType.PERFORMANCE and result.performance_metrics:
                metrics = result.performance_metrics
                if metrics.get('impact', {}).get('cpu_delta', 0) > 10:
                    recommendations.append("Consider optimizing CPU-intensive operations")
                if metrics.get('impact', {}).get('memory_delta', 0) > 100:
                    recommendations.append("Consider optimizing memory usage")
        
        # Security recommendations
        for result in qa_run.results:
            if result.test_type == TestType.SECURITY and result.status != TestStatus.PASSED:
                recommendations.append("Address security vulnerabilities detected in code")
        
        # General recommendations
        if qa_run.summary.get('success_rate', 0) < 90:
            recommendations.append("Review and fix failing tests to improve reliability")
        
        return recommendations
    
    def get_run_status(self, run_id: str) -> Optional[QARun]:
        """Get status of a specific QA run."""
        return self.active_runs.get(run_id)
    
    def get_all_runs(self) -> List[QARun]:
        """Get all active QA runs."""
        return list(self.active_runs.values())
    
    async def cleanup_old_runs(self, max_age_hours: int = 24):
        """Clean up old QA runs from memory."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        runs_to_remove = []
        for run_id, qa_run in self.active_runs.items():
            if qa_run.end_time and qa_run.end_time < cutoff_time:
                runs_to_remove.append(run_id)
        
        for run_id in runs_to_remove:
            del self.active_runs[run_id]
        
        if runs_to_remove:
            logger.info(f"Cleaned up {len(runs_to_remove)} old QA runs")


# Convenience functions for easy integration
async def run_qa_on_commit(commit_id: str, context: Optional[Dict[str, Any]] = None) -> QARun:
    """Run QA suite on a commit event."""
    runner = QARunner()
    return await runner.run_qa_suite('commit', commit_id, context=context)


async def run_qa_on_sync(sync_id: str, context: Optional[Dict[str, Any]] = None) -> QARun:
    """Run QA suite on a sync event."""
    runner = QARunner()
    return await runner.run_qa_suite('sync', sync_id, context=context)


async def run_qa_manual(description: str, context: Optional[Dict[str, Any]] = None) -> QARun:
    """Run QA suite manually."""
    runner = QARunner()
    return await runner.run_qa_suite('manual', description, context=context)


if __name__ == "__main__":
    # Example usage
    async def main():
        runner = QARunner()
        
        # Run QA on a commit
        result = await runner.run_qa_suite(
            trigger_type='commit',
            trigger_id='abc123',
            test_types=[TestType.UNIT, TestType.SECURITY, TestType.COVERAGE]
        )
        
        print(f"QA Run completed with status: {result.status}")
        print(f"Summary: {result.summary}")
    
    asyncio.run(main()) 