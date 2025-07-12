"""
CI/CD Integration for Arxos QA Runner

This module provides integration with various CI/CD platforms to automatically
trigger QA testing on commits, pull requests, and deployments.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclass import dataclass, field
from enum import Enum
import aiohttp
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from arx_testbench.qa_runner import QARunner, QARun, TestType, TestStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CICDPlatform(Enum):
    """Supported CI/CD platforms."""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    CIRCLECI = "circleci"
    TRAVIS_CI = "travis_ci"
    AZURE_DEVOPS = "azure_devops"
    BITBUCKET_PIPELINES = "bitbucket_pipelines"


@dataclass
class CICDEvent:
    """Represents a CI/CD event."""
    platform: CICDPlatform
    event_type: str
    event_id: str
    repository: str
    branch: str
    commit: str
    user: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CICDConfig:
    """Configuration for CI/CD integration."""
    enabled: bool = True
    platforms: List[CICDPlatform] = field(default_factory=lambda: [
        CICDPlatform.GITHUB_ACTIONS,
        CICDPlatform.GITLAB_CI
    ])
    auto_trigger: bool = True
    test_types: List[TestType] = field(default_factory=lambda: [
        TestType.UNIT,
        TestType.INTEGRATION,
        TestType.SECURITY,
        TestType.COVERAGE
    ])
    performance_tests: bool = True
    timeout: int = 1800  # 30 minutes
    parallel_execution: bool = True
    artifact_upload: bool = True
    notifications: Dict[str, Any] = field(default_factory=lambda: {
        'slack': False,
        'email': False,
        'webhook': False
    })


class CICDIntegration:
    """
    CI/CD integration for automated QA testing.
    
    Features:
    - Multi-platform CI/CD support
    - Automatic event detection
    - Configurable test execution
    - Artifact management
    - Notification integration
    """
    
    def __init__(self, config: Optional[CICDConfig] = None):
        """Initialize CI/CD integration."""
        self.config = config or CICDConfig()
        self.qa_runner = QARunner()
        self.active_runs: Dict[str, QARun] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Load platform-specific configurations
        self._load_platform_configs()
        
        logger.info("CI/CD integration initialized")
    
    def _load_platform_configs(self):
        """Load platform-specific configurations."""
        config_dir = Path(__file__).parent / "config" / "ci_cd"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        for platform in self.config.platforms:
            config_file = config_dir / f"{platform.value}.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        platform_config = json.load(f)
                    
                    # Store platform-specific config
                    setattr(self, f"{platform.value}_config", platform_config)
                    logger.info(f"Loaded config for {platform.value}")
                    
                except Exception as e:
                    logger.warning(f"Could not load config for {platform.value}: {e}")
    
    async def start_session(self):
        """Start aiohttp session for external API calls."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def detect_ci_environment(self) -> Optional[CICDEvent]:
        """Detect current CI/CD environment and create event."""
        try:
            # Check for GitHub Actions
            if os.getenv('GITHUB_ACTIONS'):
                return self._create_github_actions_event()
            
            # Check for GitLab CI
            elif os.getenv('GITLAB_CI'):
                return self._create_gitlab_ci_event()
            
            # Check for Jenkins
            elif os.getenv('JENKINS_URL'):
                return self._create_jenkins_event()
            
            # Check for CircleCI
            elif os.getenv('CIRCLECI'):
                return self._create_circleci_event()
            
            # Check for Travis CI
            elif os.getenv('TRAVIS'):
                return self._create_travis_ci_event()
            
            # Check for Azure DevOps
            elif os.getenv('BUILD_BUILDID'):
                return self._create_azure_devops_event()
            
            # Check for Bitbucket Pipelines
            elif os.getenv('BITBUCKET_BUILD_NUMBER'):
                return self._create_bitbucket_pipelines_event()
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting CI environment: {e}")
            return None
    
    def _create_github_actions_event(self) -> CICDEvent:
        """Create GitHub Actions event."""
        return CICDEvent(
            platform=CICDPlatform.GITHUB_ACTIONS,
            event_type=os.getenv('GITHUB_EVENT_NAME', 'push'),
            event_id=os.getenv('GITHUB_RUN_ID', 'unknown'),
            repository=os.getenv('GITHUB_REPOSITORY', 'unknown'),
            branch=os.getenv('GITHUB_REF_NAME', 'unknown'),
            commit=os.getenv('GITHUB_SHA', 'unknown'),
            user=os.getenv('GITHUB_ACTOR', 'unknown'),
            timestamp=datetime.utcnow(),
            metadata={
                'workflow': os.getenv('GITHUB_WORKFLOW'),
                'job': os.getenv('GITHUB_JOB'),
                'run_number': os.getenv('GITHUB_RUN_NUMBER'),
                'event_path': os.getenv('GITHUB_EVENT_PATH')
            }
        )
    
    def _create_gitlab_ci_event(self) -> CICDEvent:
        """Create GitLab CI event."""
        return CICDEvent(
            platform=CICDPlatform.GITLAB_CI,
            event_type='pipeline',
            event_id=os.getenv('CI_PIPELINE_ID', 'unknown'),
            repository=os.getenv('CI_PROJECT_PATH', 'unknown'),
            branch=os.getenv('CI_COMMIT_REF_NAME', 'unknown'),
            commit=os.getenv('CI_COMMIT_SHA', 'unknown'),
            user=os.getenv('GITLAB_USER_NAME', 'unknown'),
            timestamp=datetime.utcnow(),
            metadata={
                'job_id': os.getenv('CI_JOB_ID'),
                'project_id': os.getenv('CI_PROJECT_ID'),
                'pipeline_url': os.getenv('CI_PIPELINE_URL')
            }
        )
    
    def _create_jenkins_event(self) -> CICDEvent:
        """Create Jenkins event."""
        return CICDEvent(
            platform=CICDPlatform.JENKINS,
            event_type='build',
            event_id=os.getenv('BUILD_NUMBER', 'unknown'),
            repository=os.getenv('JOB_NAME', 'unknown'),
            branch=os.getenv('BRANCH_NAME', 'unknown'),
            commit=os.getenv('GIT_COMMIT', 'unknown'),
            user=os.getenv('BUILD_USER', 'unknown'),
            timestamp=datetime.utcnow(),
            metadata={
                'build_url': os.getenv('BUILD_URL'),
                'workspace': os.getenv('WORKSPACE')
            }
        )
    
    def _create_circleci_event(self) -> CICDEvent:
        """Create CircleCI event."""
        return CICDEvent(
            platform=CICDPlatform.CIRCLECI,
            event_type='build',
            event_id=os.getenv('CIRCLE_BUILD_NUM', 'unknown'),
            repository=os.getenv('CIRCLE_PROJECT_REPONAME', 'unknown'),
            branch=os.getenv('CIRCLE_BRANCH', 'unknown'),
            commit=os.getenv('CIRCLE_SHA1', 'unknown'),
            user=os.getenv('CIRCLE_USERNAME', 'unknown'),
            timestamp=datetime.utcnow(),
            metadata={
                'build_url': os.getenv('CIRCLE_BUILD_URL'),
                'job': os.getenv('CIRCLE_JOB')
            }
        )
    
    def _create_travis_ci_event(self) -> CICDEvent:
        """Create Travis CI event."""
        return CICDEvent(
            platform=CICDPlatform.TRAVIS_CI,
            event_type='build',
            event_id=os.getenv('TRAVIS_BUILD_NUMBER', 'unknown'),
            repository=os.getenv('TRAVIS_REPO_SLUG', 'unknown'),
            branch=os.getenv('TRAVIS_BRANCH', 'unknown'),
            commit=os.getenv('TRAVIS_COMMIT', 'unknown'),
            user=os.getenv('TRAVIS_COMMIT_AUTHOR', 'unknown'),
            timestamp=datetime.utcnow(),
            metadata={
                'build_url': os.getenv('TRAVIS_BUILD_WEB_URL'),
                'job_number': os.getenv('TRAVIS_JOB_NUMBER')
            }
        )
    
    def _create_azure_devops_event(self) -> CICDEvent:
        """Create Azure DevOps event."""
        return CICDEvent(
            platform=CICDPlatform.AZURE_DEVOPS,
            event_type='build',
            event_id=os.getenv('BUILD_BUILDID', 'unknown'),
            repository=os.getenv('BUILD_REPOSITORY_NAME', 'unknown'),
            branch=os.getenv('BUILD_SOURCEBRANCHNAME', 'unknown'),
            commit=os.getenv('BUILD_SOURCEVERSION', 'unknown'),
            user=os.getenv('BUILD_REQUESTEDFOR', 'unknown'),
            timestamp=datetime.utcnow(),
            metadata={
                'build_url': os.getenv('BUILD_BUILDURI'),
                'project': os.getenv('SYSTEM_TEAMPROJECT')
            }
        )
    
    def _create_bitbucket_pipelines_event(self) -> CICDEvent:
        """Create Bitbucket Pipelines event."""
        return CICDEvent(
            platform=CICDPlatform.BITBUCKET_PIPELINES,
            event_type='pipeline',
            event_id=os.getenv('BITBUCKET_BUILD_NUMBER', 'unknown'),
            repository=os.getenv('BITBUCKET_REPO_SLUG', 'unknown'),
            branch=os.getenv('BITBUCKET_BRANCH', 'unknown'),
            commit=os.getenv('BITBUCKET_COMMIT', 'unknown'),
            user=os.getenv('BITBUCKET_STEP_TRIGGERER_UUID', 'unknown'),
            timestamp=datetime.utcnow(),
            metadata={
                'pipeline_url': os.getenv('BITBUCKET_PIPELINE_URL'),
                'workspace': os.getenv('BITBUCKET_WORKSPACE')
            }
        )
    
    async def trigger_qa_on_ci_event(
        self,
        ci_event: CICDEvent,
        test_types: Optional[List[TestType]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> QARun:
        """
        Trigger QA testing on a CI/CD event.
        
        Args:
            ci_event: The CI/CD event
            test_types: Specific test types to run
            context: Additional context
            
        Returns:
            QARun: QA run results
        """
        if not self.config.enabled:
            logger.info("CI/CD integration disabled, skipping QA run")
            return None
        
        await self.start_session()
        
        logger.info(f"Triggering QA on CI event {ci_event.event_id}")
        
        # Prepare context
        qa_context = {
            'ci_event': {
                'platform': ci_event.platform.value,
                'event_type': ci_event.event_type,
                'event_id': ci_event.event_id,
                'repository': ci_event.repository,
                'branch': ci_event.branch,
                'commit': ci_event.commit,
                'user': ci_event.user,
                'timestamp': ci_event.timestamp.isoformat()
            },
            'ci_metadata': ci_event.metadata,
            'platform_config': getattr(self, f"{ci_event.platform.value}_config", {})
        }
        
        if context:
            qa_context.update(context)
        
        try:
            # Determine test types to run
            if test_types is None:
                test_types = self.config.test_types.copy()
                
                # Add performance tests if enabled
                if self.config.performance_tests and TestType.PERFORMANCE not in test_types:
                    test_types.append(TestType.PERFORMANCE)
            
            # Run QA suite
            qa_run = await self.qa_runner.run_qa_suite(
                trigger_type='ci_cd',
                trigger_id=ci_event.event_id,
                test_types=test_types,
                context=qa_context
            )
            
            # Store active run
            self.active_runs[qa_run.run_id] = qa_run
            
            # Generate artifacts
            await self._generate_artifacts(qa_run, ci_event)
            
            # Send notifications
            await self._send_ci_notifications(qa_run, ci_event)
            
            # Update CI/CD status
            await self._update_ci_status(qa_run, ci_event)
            
            logger.info(f"QA completed for CI event {ci_event.event_id}")
            return qa_run
            
        except Exception as e:
            logger.error(f"Error in QA for CI event {ci_event.event_id}: {e}")
            raise
    
    async def _generate_artifacts(self, qa_run: QARun, ci_event: CICDEvent):
        """Generate CI/CD artifacts."""
        try:
            artifacts_dir = Path("artifacts") / "qa" / ci_event.event_id
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate JSON artifact
            artifact_data = {
                'qa_run': {
                    'run_id': qa_run.run_id,
                    'status': qa_run.status.value,
                    'start_time': qa_run.start_time.isoformat(),
                    'end_time': qa_run.end_time.isoformat() if qa_run.end_time else None,
                    'summary': qa_run.summary
                },
                'ci_event': {
                    'platform': ci_event.platform.value,
                    'event_type': ci_event.event_type,
                    'event_id': ci_event.event_id,
                    'repository': ci_event.repository,
                    'branch': ci_event.branch,
                    'commit': ci_event.commit,
                    'user': ci_event.user,
                    'timestamp': ci_event.timestamp.isoformat()
                },
                'results': [
                    {
                        'test_id': result.test_id,
                        'test_type': result.test_type.value,
                        'status': result.status.value,
                        'duration': result.duration,
                        'coverage_percentage': result.coverage_percentage,
                        'performance_metrics': result.performance_metrics,
                        'error_message': result.error_message
                    }
                    for result in qa_run.results
                ]
            }
            
            # Save JSON artifact
            json_path = artifacts_dir / "qa_results.json"
            with open(json_path, 'w') as f:
                json.dump(artifact_data, f, indent=2)
            
            # Generate JUnit XML for CI/CD platforms
            junit_path = artifacts_dir / "qa_results.xml"
            await self._generate_junit_xml(qa_run, junit_path)
            
            # Generate coverage report
            coverage_path = artifacts_dir / "coverage.xml"
            await self._generate_coverage_xml(qa_run, coverage_path)
            
            # Upload artifacts if configured
            if self.config.artifact_upload:
                await self._upload_artifacts(artifacts_dir, ci_event)
            
            logger.info(f"Generated artifacts in {artifacts_dir}")
            
        except Exception as e:
            logger.error(f"Error generating artifacts: {e}")
    
    async def _generate_junit_xml(self, qa_run: QARun, output_path: Path):
        """Generate JUnit XML report."""
        try:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_content += '<testsuites>\n'
            xml_content += f'  <testsuite name="QA Tests" tests="{len(qa_run.results)}" '
            xml_content += f'failures="{len([r for r in qa_run.results if r.status == TestStatus.FAILED])}" '
            xml_content += f'errors="{len([r for r in qa_run.results if r.status == TestStatus.ERROR])}">\n'
            
            for result in qa_run.results:
                xml_content += f'    <testcase name="{result.test_type.value}" '
                xml_content += f'time="{result.duration:.3f}">\n'
                
                if result.status == TestStatus.FAILED:
                    xml_content += f'      <failure message="{result.error_message or "Test failed"}">'
                    xml_content += f'{result.output}</failure>\n'
                elif result.status == TestStatus.ERROR:
                    xml_content += f'      <error message="{result.error_message or "Test error"}">'
                    xml_content += f'{result.output}</error>\n'
                
                xml_content += '    </testcase>\n'
            
            xml_content += '  </testsuite>\n'
            xml_content += '</testsuites>\n'
            
            with open(output_path, 'w') as f:
                f.write(xml_content)
                
        except Exception as e:
            logger.error(f"Error generating JUnit XML: {e}")
    
    async def _generate_coverage_xml(self, qa_run: QARun, output_path: Path):
        """Generate coverage XML report."""
        try:
            # This would integrate with coverage.py to generate Cobertura XML
            # For now, create a simple coverage report
            coverage_results = [r for r in qa_run.results if r.coverage_percentage is not None]
            
            if coverage_results:
                avg_coverage = sum(r.coverage_percentage for r in coverage_results) / len(coverage_results)
                
                xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
                xml_content += '<coverage version="1">\n'
                xml_content += f'  <sources>\n'
                xml_content += f'    <source>.</source>\n'
                xml_content += f'  </sources>\n'
                xml_content += f'  <packages>\n'
                xml_content += f'    <package name="arxos" line-rate="{avg_coverage/100:.3f}" '
                xml_content += f'branch-rate="0.0" complexity="0.0">\n'
                xml_content += f'      <classes>\n'
                xml_content += f'        <class name="qa_tests" filename="qa_tests.py" '
                xml_content += f'line-rate="{avg_coverage/100:.3f}" branch-rate="0.0" complexity="0.0">\n'
                xml_content += f'        </class>\n'
                xml_content += f'      </classes>\n'
                xml_content += f'    </package>\n'
                xml_content += f'  </packages>\n'
                xml_content += f'</coverage>\n'
                
                with open(output_path, 'w') as f:
                    f.write(xml_content)
                    
        except Exception as e:
            logger.error(f"Error generating coverage XML: {e}")
    
    async def _upload_artifacts(self, artifacts_dir: Path, ci_event: CICDEvent):
        """Upload artifacts to CI/CD platform."""
        try:
            if ci_event.platform == CICDPlatform.GITHUB_ACTIONS:
                await self._upload_to_github_actions(artifacts_dir)
            elif ci_event.platform == CICDPlatform.GITLAB_CI:
                await self._upload_to_gitlab_ci(artifacts_dir)
            # Add other platform upload methods as needed
            
        except Exception as e:
            logger.error(f"Error uploading artifacts: {e}")
    
    async def _upload_to_github_actions(self, artifacts_dir: Path):
        """Upload artifacts to GitHub Actions."""
        # GitHub Actions uses a specific directory for artifacts
        github_artifacts_dir = Path(os.getenv('GITHUB_WORKSPACE', '.')) / "qa-artifacts"
        github_artifacts_dir.mkdir(exist_ok=True)
        
        # Copy artifacts to GitHub Actions directory
        import shutil
        for artifact_file in artifacts_dir.glob("*"):
            if artifact_file.is_file():
                shutil.copy2(artifact_file, github_artifacts_dir / artifact_file.name)
        
        logger.info(f"Artifacts prepared for GitHub Actions upload")
    
    async def _upload_to_gitlab_ci(self, artifacts_dir: Path):
        """Upload artifacts to GitLab CI."""
        # GitLab CI artifacts are automatically uploaded from the artifacts directory
        logger.info(f"Artifacts ready for GitLab CI upload")
    
    async def _send_ci_notifications(self, qa_run: QARun, ci_event: CICDEvent):
        """Send notifications for CI/CD QA results."""
        if not self.config.notifications:
            return
        
        try:
            notification_data = {
                'type': 'ci_qa_result',
                'platform': ci_event.platform.value,
                'event_id': ci_event.event_id,
                'repository': ci_event.repository,
                'branch': ci_event.branch,
                'commit': ci_event.commit,
                'qa_run_id': qa_run.run_id,
                'status': qa_run.status.value,
                'summary': qa_run.summary,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send Slack notification
            if self.config.notifications.get('slack'):
                await self._send_slack_notification(notification_data)
            
            # Send email notification
            if self.config.notifications.get('email'):
                await self._send_email_notification(notification_data)
            
            # Send webhook notification
            if self.config.notifications.get('webhook'):
                await self._send_webhook_notification(notification_data)
                
        except Exception as e:
            logger.error(f"Error sending CI notifications: {e}")
    
    async def _send_slack_notification(self, data: Dict[str, Any]):
        """Send notification to Slack."""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return
        
        try:
            message = {
                "text": f"QA Results for {data['repository']}",
                "attachments": [
                    {
                        "color": "good" if data['status'] == 'passed' else "danger",
                        "fields": [
                            {"title": "Status", "value": data['status'], "short": True},
                            {"title": "Repository", "value": data['repository'], "short": True},
                            {"title": "Branch", "value": data['branch'], "short": True},
                            {"title": "Commit", "value": data['commit'][:8], "short": True},
                            {"title": "Success Rate", "value": f"{data['summary'].get('success_rate', 0):.1f}%", "short": True},
                            {"title": "Coverage", "value": f"{data['summary'].get('average_coverage', 0):.1f}%", "short": True}
                        ]
                    }
                ]
            }
            
            if self.session:
                async with self.session.post(webhook_url, json=message) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent")
                    else:
                        logger.warning(f"Failed to send Slack notification: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    async def _send_email_notification(self, data: Dict[str, Any]):
        """Send email notification."""
        # This would integrate with email service
        logger.info("Email notification would be sent")
    
    async def _send_webhook_notification(self, data: Dict[str, Any]):
        """Send webhook notification."""
        webhook_url = os.getenv('QA_WEBHOOK_URL')
        if not webhook_url:
            return
        
        try:
            if self.session:
                async with self.session.post(webhook_url, json=data) as response:
                    if response.status == 200:
                        logger.info("Webhook notification sent")
                    else:
                        logger.warning(f"Failed to send webhook notification: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    async def _update_ci_status(self, qa_run: QARun, ci_event: CICDEvent):
        """Update CI/CD platform status."""
        try:
            if ci_event.platform == CICDPlatform.GITHUB_ACTIONS:
                await self._update_github_status(qa_run, ci_event)
            elif ci_event.platform == CICDPlatform.GITLAB_CI:
                await self._update_gitlab_status(qa_run, ci_event)
            # Add other platform status updates as needed
            
        except Exception as e:
            logger.error(f"Error updating CI status: {e}")
    
    async def _update_github_status(self, qa_run: QARun, ci_event: CICDEvent):
        """Update GitHub commit status."""
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            return
        
        try:
            status_data = {
                'state': 'success' if qa_run.status == TestStatus.PASSED else 'failure',
                'target_url': f"https://github.com/{ci_event.repository}/actions/runs/{ci_event.event_id}",
                'description': f"QA Tests: {qa_run.summary.get('success_rate', 0):.1f}% passed",
                'context': 'QA Tests'
            }
            
            api_url = f"https://api.github.com/repos/{ci_event.repository}/statuses/{ci_event.commit}"
            
            if self.session:
                headers = {'Authorization': f'token {github_token}'}
                async with self.session.post(api_url, json=status_data, headers=headers) as response:
                    if response.status == 201:
                        logger.info("GitHub status updated")
                    else:
                        logger.warning(f"Failed to update GitHub status: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error updating GitHub status: {e}")
    
    async def _update_gitlab_status(self, qa_run: QARun, ci_event: CICDEvent):
        """Update GitLab pipeline status."""
        # GitLab CI automatically handles status updates
        logger.info("GitLab status would be updated")
    
    def get_active_runs(self) -> Dict[str, QARun]:
        """Get currently active QA runs."""
        return self.active_runs.copy()
    
    async def cleanup_old_runs(self, max_age_hours: int = 24):
        """Clean up old QA runs."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        runs_to_remove = []
        for run_id, qa_run in self.active_runs.items():
            if qa_run.end_time and qa_run.end_time.timestamp() < cutoff_time:
                runs_to_remove.append(run_id)
        
        for run_id in runs_to_remove:
            del self.active_runs[run_id]
        
        if runs_to_remove:
            logger.info(f"Cleaned up {len(runs_to_remove)} old QA runs")


# Global instance for easy access
ci_integration = CICDIntegration()


# Convenience functions for integration
async def trigger_qa_on_ci_detection() -> Optional[QARun]:
    """Automatically detect CI environment and trigger QA."""
    ci_event = ci_integration.detect_ci_environment()
    if ci_event:
        return await ci_integration.trigger_qa_on_ci_event(ci_event)
    return None


async def trigger_qa_on_github_actions(
    event_id: str,
    repository: str,
    commit: str,
    **kwargs
) -> QARun:
    """Trigger QA on GitHub Actions event."""
    ci_event = CICDEvent(
        platform=CICDPlatform.GITHUB_ACTIONS,
        event_type='push',
        event_id=event_id,
        repository=repository,
        branch=kwargs.get('branch', 'main'),
        commit=commit,
        user=kwargs.get('user', 'unknown'),
        timestamp=datetime.utcnow(),
        metadata=kwargs
    )
    
    return await ci_integration.trigger_qa_on_ci_event(ci_event)


async def trigger_qa_on_gitlab_ci(
    pipeline_id: str,
    project_path: str,
    commit: str,
    **kwargs
) -> QARun:
    """Trigger QA on GitLab CI event."""
    ci_event = CICDEvent(
        platform=CICDPlatform.GITLAB_CI,
        event_type='pipeline',
        event_id=pipeline_id,
        repository=project_path,
        branch=kwargs.get('branch', 'main'),
        commit=commit,
        user=kwargs.get('user', 'unknown'),
        timestamp=datetime.utcnow(),
        metadata=kwargs
    )
    
    return await ci_integration.trigger_qa_on_ci_event(ci_event)


if __name__ == "__main__":
    # Example usage
    async def main():
        # Auto-detect CI environment and trigger QA
        result = await trigger_qa_on_ci_detection()
        
        if result:
            print(f"QA triggered in CI environment: {result.run_id}")
            print(f"Status: {result.status}")
            print(f"Summary: {result.summary}")
        else:
            print("No CI environment detected")
    
    asyncio.run(main()) 