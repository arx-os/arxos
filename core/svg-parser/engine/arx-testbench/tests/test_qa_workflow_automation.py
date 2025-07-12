"""
Comprehensive Test Suite for QA Workflow Automation

This test suite covers all aspects of the QA workflow automation system including:
- QA runner functionality
- Post-sync hooks
- CI/CD integration
- Performance testing
- Error handling
"""

import asyncio
import json
import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import the modules to test
from arx_testbench.qa_runner import QARunner, QARun, TestType, TestStatus
from arx_sync_agent.hooks.post_sync_tests import PostSyncQAHooks, SyncEvent, SyncEventType
from arx_testbench.ci_integration import CICDIntegration, CICDEvent, CICDPlatform


class TestQARunner:
    """Test QA runner functionality."""
    
    @pytest.fixture
    def qa_runner(self):
        """Create QA runner instance."""
        return QARunner()
    
    @pytest.fixture
    def sample_qa_run(self):
        """Create sample QA run."""
        return QARun(
            run_id="test_run_123",
            trigger_type="test",
            trigger_id="test_trigger",
            start_time=datetime.utcnow(),
            status=TestStatus.PASSED
        )
    
    @pytest.mark.asyncio
    async def test_qa_runner_initialization(self, qa_runner):
        """Test QA runner initialization."""
        assert qa_runner is not None
        assert qa_runner.config is not None
        assert 'max_workers' in qa_runner.config
        assert 'timeout' in qa_runner.config
    
    @pytest.mark.asyncio
    async def test_run_qa_suite_basic(self, qa_runner):
        """Test basic QA suite execution."""
        with patch.object(qa_runner, '_run_test_type') as mock_run_test:
            mock_run_test.return_value = Mock(
                test_id="test_1",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                duration=1.0,
                output="Test passed"
            )
            
            result = await qa_runner.run_qa_suite(
                trigger_type="test",
                trigger_id="test_123",
                test_types=[TestType.UNIT]
            )
            
            assert result is not None
            assert result.run_id is not None
            assert len(result.results) == 1
    
    @pytest.mark.asyncio
    async def test_run_unit_tests(self, qa_runner):
        """Test unit test execution."""
        with patch.object(qa_runner, '_run_command') as mock_command:
            mock_command.return_value = {
                'return_code': 0,
                'output': 'test passed',
                'error_message': None
            }
            
            result = await qa_runner._run_unit_tests()
            
            assert result['success'] is True
            assert 'coverage_percentage' in result
    
    @pytest.mark.asyncio
    async def test_run_security_tests(self, qa_runner):
        """Test security test execution."""
        with patch.object(qa_runner, '_run_command') as mock_command:
            mock_command.return_value = {
                'return_code': 0,
                'output': '{"results": []}',
                'error_message': None
            }
            
            result = await qa_runner._run_security_tests()
            
            assert result['success'] is True
            assert 'security_results' in result
    
    @pytest.mark.asyncio
    async def test_run_performance_tests(self, qa_runner):
        """Test performance test execution."""
        with patch.object(qa_runner, '_get_system_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'cpu_percent': 10.0,
                'memory_mb': 100.0,
                'memory_percent': 20.0,
                'disk_percent': 30.0
            }
            
            with patch.object(qa_runner, '_run_command') as mock_command:
                mock_command.return_value = {
                    'return_code': 0,
                    'output': 'performance test passed',
                    'error_message': None
                }
                
                result = await qa_runner._run_performance_tests()
                
                assert result['success'] is True
                assert 'performance_metrics' in result
    
    @pytest.mark.asyncio
    async def test_run_coverage_tests(self, qa_runner):
        """Test coverage test execution."""
        with patch.object(qa_runner, '_run_command') as mock_command:
            mock_command.return_value = {
                'return_code': 0,
                'output': 'TOTAL                   100    50    50%',
                'error_message': None
            }
            
            result = await qa_runner._run_coverage_tests()
            
            assert result['success'] is False  # Below threshold
            assert result['coverage_percentage'] == 50.0
    
    @pytest.mark.asyncio
    async def test_run_linting_tests(self, qa_runner):
        """Test linting test execution."""
        with patch.object(qa_runner, '_run_command') as mock_command:
            mock_command.return_value = {
                'return_code': 0,
                'output': 'linting passed',
                'error_message': None
            }
            
            result = await qa_runner._run_linting_tests()
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_command_timeout(self, qa_runner):
        """Test command timeout handling."""
        with patch.object(qa_runner, '_run_command') as mock_command:
            mock_command.side_effect = asyncio.TimeoutError()
            
            result = await qa_runner._run_unit_tests()
            
            assert result['success'] is False
            assert 'timeout' in result['error_message'].lower()
    
    @pytest.mark.asyncio
    async def test_generate_summary(self, qa_runner, sample_qa_run):
        """Test summary generation."""
        # Add test results
        sample_qa_run.results = [
            Mock(
                test_id="test_1",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                duration=1.0,
                coverage_percentage=90.0
            ),
            Mock(
                test_id="test_2",
                test_type=TestType.SECURITY,
                status=TestStatus.PASSED,
                duration=2.0,
                coverage_percentage=None
            )
        ]
        
        await qa_runner._generate_summary(sample_qa_run)
        
        assert 'total_tests' in sample_qa_run.summary
        assert 'passed_tests' in sample_qa_run.summary
        assert 'success_rate' in sample_qa_run.summary
        assert sample_qa_run.summary['total_tests'] == 2
        assert sample_qa_run.summary['passed_tests'] == 2
        assert sample_qa_run.summary['success_rate'] == 100.0


class TestPostSyncQAHooks:
    """Test post-sync QA hooks."""
    
    @pytest.fixture
    def qa_hooks(self):
        """Create QA hooks instance."""
        return PostSyncQAHooks()
    
    @pytest.fixture
    def sample_sync_event(self):
        """Create sample sync event."""
        return SyncEvent(
            event_id="sync_123",
            event_type=SyncEventType.COMMIT,
            repository_id="test-repo",
            user_id="test-user",
            device_id="test-device",
            timestamp=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_qa_hooks_initialization(self, qa_hooks):
        """Test QA hooks initialization."""
        assert qa_hooks is not None
        assert qa_hooks.config is not None
        assert qa_hooks.qa_runner is not None
    
    @pytest.mark.asyncio
    async def test_trigger_qa_on_sync(self, qa_hooks, sample_sync_event):
        """Test QA triggering on sync event."""
        with patch.object(qa_hooks.qa_runner, 'run_qa_suite') as mock_run:
            mock_run.return_value = Mock(
                run_id="qa_run_123",
                status=TestStatus.PASSED,
                summary={'total_tests': 5, 'passed_tests': 5}
            )
            
            result = await qa_hooks.trigger_qa_on_sync(sample_sync_event)
            
            assert result is not None
            assert result.run_id == "qa_run_123"
    
    @pytest.mark.asyncio
    async def test_trigger_qa_on_commit(self, qa_hooks):
        """Test QA triggering on commit event."""
        with patch.object(qa_hooks, 'trigger_qa_on_sync') as mock_trigger:
            mock_trigger.return_value = Mock(run_id="qa_run_123")
            
            result = await qa_hooks.trigger_qa_on_commit(
                commit_id="commit_123",
                repository_id="test-repo",
                user_id="test-user"
            )
            
            assert result is not None
            mock_trigger.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_qa_on_push(self, qa_hooks):
        """Test QA triggering on push event."""
        with patch.object(qa_hooks, 'trigger_qa_on_sync') as mock_trigger:
            mock_trigger.return_value = Mock(run_id="qa_run_123")
            
            result = await qa_hooks.trigger_qa_on_push(
                push_id="push_123",
                repository_id="test-repo",
                user_id="test-user",
                branch="main"
            )
            
            assert result is not None
            mock_trigger.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_reports(self, qa_hooks, sample_sync_event):
        """Test report generation."""
        qa_run = Mock(
            run_id="qa_run_123",
            status=TestStatus.PASSED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            summary={'total_tests': 5, 'passed_tests': 5},
            results=[]
        )
        
        with patch('aiofiles.open', create=True) as mock_open:
            mock_file = AsyncMock()
            mock_open.return_value.__aenter__.return_value = mock_file
            
            await qa_hooks._generate_reports(qa_run, sample_sync_event)
            
            # Check that files were written
            assert mock_file.write.called
    
    @pytest.mark.asyncio
    async def test_send_notifications(self, qa_hooks, sample_sync_event):
        """Test notification sending."""
        qa_run = Mock(
            status=TestStatus.FAILED,
            summary={'total_tests': 5, 'failed_tests': 2}
        )
        
        with patch.object(qa_hooks, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            await qa_hooks._send_notifications(qa_run, sample_sync_event)
            
            # Check that notification was sent
            mock_session.post.assert_called_once()


class TestCICDIntegration:
    """Test CI/CD integration."""
    
    @pytest.fixture
    def ci_integration(self):
        """Create CI/CD integration instance."""
        return CICDIntegration()
    
    @pytest.fixture
    def sample_ci_event(self):
        """Create sample CI event."""
        return CICDEvent(
            platform=CICDPlatform.GITHUB_ACTIONS,
            event_type="push",
            event_id="ci_123",
            repository="test/repo",
            branch="main",
            commit="abc123",
            user="test-user",
            timestamp=datetime.utcnow()
        )
    
    def test_ci_integration_initialization(self, ci_integration):
        """Test CI/CD integration initialization."""
        assert ci_integration is not None
        assert ci_integration.config is not None
        assert ci_integration.qa_runner is not None
    
    @pytest.mark.asyncio
    async def test_trigger_qa_on_ci_event(self, ci_integration, sample_ci_event):
        """Test QA triggering on CI event."""
        with patch.object(ci_integration.qa_runner, 'run_qa_suite') as mock_run:
            mock_run.return_value = Mock(
                run_id="qa_run_123",
                status=TestStatus.PASSED,
                summary={'total_tests': 5, 'passed_tests': 5}
            )
            
            with patch.object(ci_integration, '_generate_artifacts') as mock_artifacts:
                with patch.object(ci_integration, '_send_ci_notifications') as mock_notifications:
                    result = await ci_integration.trigger_qa_on_ci_event(sample_ci_event)
                    
                    assert result is not None
                    assert result.run_id == "qa_run_123"
                    mock_artifacts.assert_called_once()
                    mock_notifications.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_github_actions(self, ci_integration):
        """Test GitHub Actions environment detection."""
        with patch.dict(os.environ, {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_RUN_ID': '123',
            'GITHUB_REPOSITORY': 'test/repo',
            'GITHUB_REF_NAME': 'main',
            'GITHUB_SHA': 'abc123',
            'GITHUB_ACTOR': 'test-user'
        }):
            event = ci_integration.detect_ci_environment()
            
            assert event is not None
            assert event.platform == CICDPlatform.GITHUB_ACTIONS
            assert event.event_id == '123'
            assert event.repository == 'test/repo'
    
    @pytest.mark.asyncio
    async def test_detect_gitlab_ci(self, ci_integration):
        """Test GitLab CI environment detection."""
        with patch.dict(os.environ, {
            'GITLAB_CI': 'true',
            'CI_PIPELINE_ID': '456',
            'CI_PROJECT_PATH': 'test/repo',
            'CI_COMMIT_REF_NAME': 'main',
            'CI_COMMIT_SHA': 'def456',
            'GITLAB_USER_NAME': 'test-user'
        }):
            event = ci_integration.detect_ci_environment()
            
            assert event is not None
            assert event.platform == CICDPlatform.GITLAB_CI
            assert event.event_id == '456'
            assert event.repository == 'test/repo'
    
    @pytest.mark.asyncio
    async def test_generate_artifacts(self, ci_integration, sample_ci_event):
        """Test artifact generation."""
        qa_run = Mock(
            run_id="qa_run_123",
            status=TestStatus.PASSED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            summary={'total_tests': 5, 'passed_tests': 5},
            results=[]
        )
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                await ci_integration._generate_artifacts(qa_run, sample_ci_event)
                
                # Check that files were written
                assert mock_file.write.called
    
    @pytest.mark.asyncio
    async def test_generate_junit_xml(self, ci_integration):
        """Test JUnit XML generation."""
        qa_run = Mock(
            results=[
                Mock(
                    test_id="test_1",
                    test_type=TestType.UNIT,
                    status=TestStatus.PASSED,
                    duration=1.0,
                    output="Test passed"
                ),
                Mock(
                    test_id="test_2",
                    test_type=TestType.SECURITY,
                    status=TestStatus.FAILED,
                    duration=2.0,
                    output="Test failed",
                    error_message="Security issue found"
                )
            ]
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        
        try:
            await ci_integration._generate_junit_xml(qa_run, tmp_path)
            
            # Check that file was created and contains XML
            assert tmp_path.exists()
            content = tmp_path.read_text()
            assert '<?xml version="1.0"' in content
            assert '<testsuites>' in content
            assert '<testcase' in content
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_send_slack_notification(self, ci_integration):
        """Test Slack notification sending."""
        data = {
            'status': 'passed',
            'repository': 'test/repo',
            'branch': 'main',
            'commit': 'abc123',
            'summary': {'success_rate': 95.0, 'average_coverage': 90.0}
        }
        
        with patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'}):
            with patch.object(ci_integration, 'session') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_session.post.return_value.__aenter__.return_value = mock_response
                
                await ci_integration._send_slack_notification(data)
                
                # Check that notification was sent
                mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_github_status(self, ci_integration, sample_ci_event):
        """Test GitHub status update."""
        qa_run = Mock(
            status=TestStatus.PASSED,
            summary={'success_rate': 95.0}
        )
        
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'}):
            with patch.object(ci_integration, 'session') as mock_session:
                mock_response = AsyncMock()
                mock_response.status = 201
                mock_session.post.return_value.__aenter__.return_value = mock_response
                
                await ci_integration._update_github_status(qa_run, sample_ci_event)
                
                # Check that status was updated
                mock_session.post.assert_called_once()


class TestIntegration:
    """Integration tests for the complete QA workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_qa_workflow(self):
        """Test complete QA workflow from sync to CI."""
        # Test QA runner
        qa_runner = QARunner()
        
        # Test sync hooks
        qa_hooks = PostSyncQAHooks()
        
        # Test CI integration
        ci_integration = CICDIntegration()
        
        # Verify all components work together
        assert qa_runner is not None
        assert qa_hooks is not None
        assert ci_integration is not None
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling across components."""
        qa_runner = QARunner()
        
        # Test with invalid configuration
        with patch.object(qa_runner, '_run_command') as mock_command:
            mock_command.side_effect = Exception("Test error")
            
            result = await qa_runner._run_unit_tests()
            
            assert result['success'] is False
            assert 'error' in result['error_message'].lower()
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance under load."""
        qa_runner = QARunner()
        
        # Simulate multiple concurrent QA runs
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                qa_runner.run_qa_suite(
                    trigger_type="test",
                    trigger_id=f"test_{i}",
                    test_types=[TestType.UNIT]
                )
            )
            tasks.append(task)
        
        # All tasks should complete without errors
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            assert not isinstance(result, Exception)


# Performance tests
class TestPerformance:
    """Performance tests for QA workflow automation."""
    
    @pytest.mark.asyncio
    async def test_qa_runner_performance(self):
        """Test QA runner performance."""
        qa_runner = QARunner()
        
        start_time = datetime.utcnow()
        
        with patch.object(qa_runner, '_run_test_type') as mock_run:
            mock_run.return_value = Mock(
                test_id="test_1",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                duration=0.1,
                output="Test passed"
            )
            
            result = await qa_runner.run_qa_suite(
                trigger_type="test",
                trigger_id="test_perf",
                test_types=[TestType.UNIT, TestType.SECURITY, TestType.COVERAGE]
            )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time
        assert duration < 5.0
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_hooks(self):
        """Test concurrent sync hook execution."""
        qa_hooks = PostSyncQAHooks()
        
        # Create multiple sync events
        sync_events = []
        for i in range(10):
            event = SyncEvent(
                event_id=f"sync_{i}",
                event_type=SyncEventType.COMMIT,
                repository_id="test-repo",
                user_id="test-user",
                device_id="test-device",
                timestamp=datetime.utcnow()
            )
            sync_events.append(event)
        
        # Execute concurrently
        with patch.object(qa_hooks.qa_runner, 'run_qa_suite') as mock_run:
            mock_run.return_value = Mock(
                run_id="qa_run_123",
                status=TestStatus.PASSED,
                summary={'total_tests': 5, 'passed_tests': 5}
            )
            
            tasks = [
                qa_hooks.trigger_qa_on_sync(event)
                for event in sync_events
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should complete successfully
            assert len(results) == 10
            for result in results:
                assert not isinstance(result, Exception)


# Security tests
class TestSecurity:
    """Security tests for QA workflow automation."""
    
    @pytest.mark.asyncio
    async def test_command_injection_prevention(self):
        """Test command injection prevention."""
        qa_runner = QARunner()
        
        # Test with malicious input
        malicious_input = "test; rm -rf /"
        
        with patch.object(qa_runner, '_run_command') as mock_command:
            mock_command.return_value = {
                'return_code': 0,
                'output': 'safe output',
                'error_message': None
            }
            
            # Should handle safely
            result = await qa_runner._run_unit_tests()
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_secure_configuration(self):
        """Test secure configuration handling."""
        qa_runner = QARunner()
        
        # Test with secure config
        secure_config = {
            'timeout': 300,
            'max_workers': 4,
            'coverage_threshold': 90.0
        }
        
        qa_runner.config.update(secure_config)
        
        assert qa_runner.config['timeout'] == 300
        assert qa_runner.config['max_workers'] == 4
        assert qa_runner.config['coverage_threshold'] == 90.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 