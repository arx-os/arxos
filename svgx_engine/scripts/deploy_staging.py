#!/usr/bin/env python3
"""
SVGX Engine - Staging Deployment Script

This script handles the complete staging deployment process including:
- Docker image building
- Kubernetes deployment
- Health checks and validation
- Rollback procedures

Author: SVGX Engineering Team
Date: 2024
"""

import subprocess
import time
import sys
import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
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

class StagingDeployer:
    """Handles staging deployment process"""

    def __init__(self, config: Dict):
        self.config = config
        self.namespace = config.get('namespace', 'svgx-engine-staging')
        self.image_name = config.get('image_name', 'svgx-engine')
        self.image_tag = config.get('image_tag', 'staging')
        self.registry = config.get('registry', 'localhost:5000')
        self.k8s_manifest = config.get('k8s_manifest', 'k8s/staging-deployment.yaml')
        self.validation_script = config.get('validation_script', 'scripts/staging_validation.py')

    def build_docker_image(self) -> bool:
        """Build Docker image for staging"""
        logger.info("Building Docker image...")

        try:
            # Build the image
            build_cmd = [
                'docker', 'build',
                '-t', f'{self.image_name}:{self.image_tag}',
                '-t', f'{self.registry}/{self.image_name}:{self.image_tag}',
                '.'
            ]

            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info("Docker image built successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Docker build failed: {e}")
            logger.error(f"Build output: {e.stdout}")
            logger.error(f"Build errors: {e.stderr}")
            return False

    def push_docker_image(self) -> bool:
        """Push Docker image to registry"""
        logger.info("Pushing Docker image to registry...")

        try:
            push_cmd = [
                'docker', 'push',
                f'{self.registry}/{self.image_name}:{self.image_tag}'
            ]

            result = subprocess.run(
                push_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info("Docker image pushed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Docker push failed: {e}")
            logger.error(f"Push output: {e.stdout}")
            logger.error(f"Push errors: {e.stderr}")
            return False

    def create_namespace(self) -> bool:
        """Create Kubernetes namespace if it doesn't exist"""
        logger.info(f"Creating namespace {self.namespace}...")

        try:
            # Check if namespace exists
            check_cmd = ['kubectl', 'get', 'namespace', self.namespace]
            result = subprocess.run(check_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                # Create namespace
                create_cmd = ['kubectl', 'create', 'namespace', self.namespace]
                subprocess.run(create_cmd, check=True)
                logger.info(f"Namespace {self.namespace} created")
            else:
                logger.info(f"Namespace {self.namespace} already exists")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Namespace creation failed: {e}")
            return False

    def deploy_to_kubernetes(self) -> bool:
        """Deploy to Kubernetes"""
        logger.info("Deploying to Kubernetes...")

        try:
            # Apply the deployment
            apply_cmd = ['kubectl', 'apply', '-f', self.k8s_manifest]
            subprocess.run(apply_cmd, check=True)

            logger.info("Kubernetes deployment applied successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Kubernetes deployment failed: {e}")
            return False

    def wait_for_deployment(self, timeout_minutes: int = 10) -> bool:
        """Wait for deployment to be ready"""
        logger.info("Waiting for deployment to be ready...")

        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            try:
                # Check deployment status
                status_cmd = [
                    'kubectl', 'get', 'deployment', 'svgx-engine-staging',
                    '-n', self.namespace,
                    '-o', 'jsonpath={.status.conditions[?(@.type=="Available")].status}'
                ]

                result = subprocess.run(status_cmd, capture_output=True, text=True)

                if result.stdout.strip() == 'True':
                    logger.info("Deployment is ready!")
                    return True

                # Check pod status
                pods_cmd = [
                    'kubectl', 'get', 'pods',
                    '-n', self.namespace,
                    '-l', 'app=svgx-engine-staging',
                    '-o', 'jsonpath={.items[*].status.phase}'
                ]

                pods_result = subprocess.run(pods_cmd, capture_output=True, text=True)
                pod_statuses = pods_result.stdout.strip().split()

                if all(status == 'Running' for status in pod_statuses if status):
                    logger.info("All pods are running!")
                    return True

                logger.info("Waiting for deployment to be ready...")
                time.sleep(30)

            except subprocess.CalledProcessError as e:
                logger.warning(f"Status check failed: {e}")
                time.sleep(30)

        logger.error("Deployment timeout reached")
        return False

    def get_service_url(self) -> Optional[str]:
        """Get the service URL for validation"""
        try:
            # Get service URL
            url_cmd = [
                'kubectl', 'get', 'service', 'svgx-engine-staging-service',
                '-n', self.namespace,
                '-o', 'jsonpath={.status.loadBalancer.ingress[0].ip}'
            ]

            result = subprocess.run(url_cmd, capture_output=True, text=True)
            ip = result.stdout.strip()

            if ip:
                return f"http://{ip}"

            # Try to get port-forward
            port_forward_cmd = [
                'kubectl', 'port-forward',
                '-n', self.namespace,
                'service/svgx-engine-staging-service',
                '8000:80'
            ]

            # Start port-forward in background
            subprocess.run(port_forward_cmd, shell=False, capture_output=True, text=True)
            time.sleep(5)  # Wait for port-forward to establish

            return "http://localhost:8000"

        except Exception as e:
            logger.error(f"Failed to get service URL: {e}")
            return None

    def run_validation(self, service_url: str) -> bool:
        """Run staging validation"""
        logger.info("Running staging validation...")

        try:
            # Set environment variables for validation
            env = os.environ.copy()
            env['SVGX_STAGING_URL'] = service_url
            env['SVGX_API_KEY'] = 'staging-api-key-test'

            # Run validation script
            validation_cmd = ['python', self.validation_script]

            result = subprocess.run(
                validation_cmd,
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Validation passed!")
                return True
            else:
                logger.error("Validation failed!")
                logger.error(f"Validation output: {result.stdout}")
                logger.error(f"Validation errors: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Validation execution failed: {e}")
            return False

    def rollback_deployment(self) -> bool:
        """Rollback deployment if needed"""
        logger.info("Rolling back deployment...")

        try:
            # Delete the deployment
            delete_cmd = ['kubectl', 'delete', '-f', self.k8s_manifest]
            subprocess.run(delete_cmd, check=True)

            logger.info("Rollback completed")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def deploy(self) -> bool:
        """Execute complete deployment process"""
        logger.info("Starting staging deployment process...")

        # Step 1: Build Docker image
        if not self.build_docker_image():
            logger.error("Docker build failed - aborting deployment")
            return False

        # Step 2: Push Docker image
        if not self.push_docker_image():
            logger.error("Docker push failed - aborting deployment")
            return False

        # Step 3: Create namespace
        if not self.create_namespace():
            logger.error("Namespace creation failed - aborting deployment")
            return False

        # Step 4: Deploy to Kubernetes
        if not self.deploy_to_kubernetes():
            logger.error("Kubernetes deployment failed - aborting deployment")
            return False

        # Step 5: Wait for deployment
        if not self.wait_for_deployment():
            logger.error("Deployment timeout - rolling back")
            self.rollback_deployment()
            return False

        # Step 6: Get service URL
        service_url = self.get_service_url()
        if not service_url:
            logger.error("Failed to get service URL - rolling back")
            self.rollback_deployment()
            return False

        # Step 7: Run validation
        if not self.run_validation(service_url):
            logger.error("Validation failed - rolling back")
            self.rollback_deployment()
            return False

        logger.info("✅ Staging deployment completed successfully!")
        return True

def main():
    """Main deployment function"""
    # Configuration
    config = {
        'namespace': 'svgx-engine-staging',
        'image_name': 'svgx-engine',
        'image_tag': 'staging',
        'registry': 'localhost:5000',
        'k8s_manifest': 'k8s/staging-deployment.yaml',
        'validation_script': 'scripts/staging_validation.py'
    }

    # Override with environment variables
    for key in config:
        env_key = f'SVGX_{key.upper()}'
        if env_key in os.environ:
            config[key] = os.environ[env_key]

    logger.info("Starting SVGX Engine staging deployment")
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")

    # Create deployer and execute deployment
    deployer = StagingDeployer(config)

    try:
        success = deployer.deploy()

        if success:
            logger.info("🎉 Staging deployment successful!")
            print("\n" + "="*60)
            print("✅ SVGX ENGINE STAGING DEPLOYMENT SUCCESSFUL")
            print("="*60)
            print(f"Namespace: {config['namespace']}")
            print(f"Image: {config['registry']}/{config['image_name']}:{config['image_tag']}")
            print("Validation: PASSED")
            print("="*60)
            sys.exit(0)
        else:
            logger.error("💥 Staging deployment failed!")
            print("\n" + "="*60)
            print("❌ SVGX ENGINE STAGING DEPLOYMENT FAILED")
            print("="*60)
            print("Check logs for details")
            print("Rollback completed")
            print("="*60)
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        deployer.rollback_deployment()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during deployment: {e}")
        deployer.rollback_deployment()
        sys.exit(1)

if __name__ == "__main__":
    main()
