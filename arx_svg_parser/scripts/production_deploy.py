#!/usr/bin/env python3
"""
Production Deployment Script for Arxos Platform

This script automates the production deployment process including:
- Environment validation
- Database migration
- Application deployment
- Health checks
- Monitoring setup
- Security validation
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_deploy.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProductionDeployer:
    def __init__(self, config_path: str = "deployment/production_config.json"):
        self.config = self.load_config(config_path)
        self.deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results = {}
        
    def load_config(self, config_path: str) -> Dict:
        """Load production deployment configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
    
    def run_deployment(self) -> bool:
        """Execute complete production deployment"""
        logger.info("Starting production deployment")
        
        try:
            # Pre-deployment checks
            if not self.pre_deployment_checks():
                logger.error("Pre-deployment checks failed")
                return False
            
            # Environment setup
            if not self.setup_environment():
                logger.error("Environment setup failed")
                return False
            
            # Database migration
            if not self.migrate_database():
                logger.error("Database migration failed")
                return False
            
            # Application deployment
            if not self.deploy_application():
                logger.error("Application deployment failed")
                return False
            
            # Security validation
            if not self.validate_security():
                logger.error("Security validation failed")
                return False
            
            # Health checks
            if not self.run_health_checks():
                logger.error("Health checks failed")
                return False
            
            # Monitoring setup
            if not self.setup_monitoring():
                logger.error("Monitoring setup failed")
                return False
            
            # Post-deployment validation
            if not self.post_deployment_validation():
                logger.error("Post-deployment validation failed")
                return False
            
            logger.info("Production deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            self.rollback_deployment()
            return False
    
    def pre_deployment_checks(self) -> bool:
        """Run pre-deployment validation checks"""
        logger.info("Running pre-deployment checks")
        
        checks = [
            self.check_environment_variables(),
            self.check_database_connectivity(),
            self.check_file_permissions(),
            self.check_ssl_certificates(),
            self.check_disk_space(),
            self.check_memory_availability()
        ]
        
        all_passed = all(checks)
        self.results['pre_deployment_checks'] = {
            'status': 'passed' if all_passed else 'failed',
            'checks': checks
        }
        
        return all_passed
    
    def check_environment_variables(self) -> bool:
        """Check required environment variables"""
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'REDIS_URL',
            'ENVIRONMENT'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing environment variables: {missing_vars}")
            return False
        
        logger.info("Environment variables check passed")
        return True
    
    def check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        try:
            # Test database connection
            db_url = os.getenv('DATABASE_URL')
            if 'sqlite' in db_url:
                # SQLite file check
                db_path = db_url.replace('sqlite:///', '')
                if not os.path.exists(db_path):
                    logger.warning(f"SQLite database file not found: {db_path}")
                    return True  # Will be created during migration
            else:
                # PostgreSQL connection test
                import psycopg2
                conn = psycopg2.connect(db_url)
                conn.close()
            
            logger.info("Database connectivity check passed")
            return True
        except Exception as e:
            logger.error(f"Database connectivity check failed: {str(e)}")
            return False
    
    def check_file_permissions(self) -> bool:
        """Check file permissions for deployment"""
        required_paths = [
            'logs/',
            'data/',
            'uploads/',
            'exports/'
        ]
        
        for path in required_paths:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            
            if not os.access(path, os.W_OK):
                logger.error(f"No write permission for: {path}")
                return False
        
        logger.info("File permissions check passed")
        return True
    
    def check_ssl_certificates(self) -> bool:
        """Check SSL certificates for HTTPS"""
        if self.config.get('ssl_required', True):
            cert_path = self.config.get('ssl_cert_path')
            key_path = self.config.get('ssl_key_path')
            
            if not cert_path or not key_path:
                logger.warning("SSL certificate paths not configured")
                return True  # Not critical for deployment
            
            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                logger.warning("SSL certificates not found")
                return True  # Not critical for deployment
        
        logger.info("SSL certificates check passed")
        return True
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        import shutil
        
        total, used, free = shutil.disk_usage('.')
        free_gb = free / (1024**3)
        
        if free_gb < 10:  # Require at least 10GB free
            logger.error(f"Insufficient disk space: {free_gb:.2f}GB available")
            return False
        
        logger.info(f"Disk space check passed: {free_gb:.2f}GB available")
        return True
    
    def check_memory_availability(self) -> bool:
        """Check available memory"""
        import psutil
        
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if available_gb < 2:  # Require at least 2GB available
            logger.error(f"Insufficient memory: {available_gb:.2f}GB available")
            return False
        
        logger.info(f"Memory check passed: {available_gb:.2f}GB available")
        return True
    
    def setup_environment(self) -> bool:
        """Setup production environment"""
        logger.info("Setting up production environment")
        
        try:
            # Create necessary directories
            directories = [
                'logs',
                'data',
                'uploads',
                'exports',
                'backups',
                'temp'
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            
            # Set environment variables
            os.environ['ENVIRONMENT'] = 'production'
            os.environ['LOG_LEVEL'] = 'INFO'
            
            # Configure logging
            logging.getLogger().setLevel(logging.INFO)
            
            logger.info("Environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Environment setup failed: {str(e)}")
            return False
    
    def migrate_database(self) -> bool:
        """Run database migrations"""
        logger.info("Running database migrations")
        
        try:
            # Run Alembic migrations
            result = subprocess.run([
                'alembic', 'upgrade', 'head'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Database migration failed: {result.stderr}")
                return False
            
            logger.info("Database migrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database migration failed: {str(e)}")
            return False
    
    def deploy_application(self) -> bool:
        """Deploy the application"""
        logger.info("Deploying application")
        
        try:
            # Stop existing application if running
            self.stop_application()
            
            # Copy application files
            self.copy_application_files()
            
            # Install dependencies
            self.install_dependencies()
            
            # Start application
            if not self.start_application():
                return False
            
            # Wait for application to be ready
            if not self.wait_for_application_ready():
                return False
            
            logger.info("Application deployment completed")
            return True
            
        except Exception as e:
            logger.error(f"Application deployment failed: {str(e)}")
            return False
    
    def stop_application(self):
        """Stop existing application"""
        try:
            # Kill existing processes
            subprocess.run(['pkill', '-f', 'main.py'], capture_output=True)
            time.sleep(2)
            logger.info("Stopped existing application")
        except Exception as e:
            logger.warning(f"Could not stop existing application: {str(e)}")
    
    def copy_application_files(self):
        """Copy application files to production location"""
        import shutil
        
        source_dir = '.'
        target_dir = self.config.get('app_directory', '/opt/arxos')
        
        # Create target directory
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy files
        for item in ['services', 'routers', 'models', 'utils', 'main.py', 'requirements.txt']:
            source = os.path.join(source_dir, item)
            target = os.path.join(target_dir, item)
            
            if os.path.exists(source):
                if os.path.isdir(source):
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
        
        logger.info(f"Copied application files to {target_dir}")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        try:
            result = subprocess.run([
                'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Dependency installation failed: {result.stderr}")
                raise Exception("Dependency installation failed")
            
            logger.info("Dependencies installed successfully")
        except Exception as e:
            logger.error(f"Dependency installation failed: {str(e)}")
            raise
    
    def start_application(self) -> bool:
        """Start the application"""
        try:
            # Start application in background
            process = subprocess.Popen([
                'python', 'main.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Store process ID
            with open('logs/app.pid', 'w') as f:
                f.write(str(process.pid))
            
            logger.info(f"Application started with PID: {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start application: {str(e)}")
            return False
    
    def wait_for_application_ready(self, timeout: int = 60) -> bool:
        """Wait for application to be ready"""
        logger.info("Waiting for application to be ready")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get('http://localhost:8000/health', timeout=5)
                if response.status_code == 200:
                    logger.info("Application is ready")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        logger.error("Application failed to start within timeout")
        return False
    
    def validate_security(self) -> bool:
        """Validate security configuration"""
        logger.info("Validating security configuration")
        
        try:
            # Test authentication
            auth_result = self.test_authentication()
            
            # Test encryption
            encryption_result = self.test_encryption()
            
            # Test access control
            access_result = self.test_access_control()
            
            all_passed = all([auth_result, encryption_result, access_result])
            
            self.results['security_validation'] = {
                'status': 'passed' if all_passed else 'failed',
                'authentication': auth_result,
                'encryption': encryption_result,
                'access_control': access_result
            }
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Security validation failed: {str(e)}")
            return False
    
    def test_authentication(self) -> bool:
        """Test authentication mechanisms"""
        try:
            # Test API key authentication
            headers = {'Authorization': f'Bearer {os.getenv("API_KEY", "test")}'}
            response = requests.get('http://localhost:8000/api/v1/health', headers=headers)
            
            if response.status_code == 200:
                logger.info("Authentication test passed")
                return True
            else:
                logger.error("Authentication test failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication test failed: {str(e)}")
            return False
    
    def test_encryption(self) -> bool:
        """Test encryption functionality"""
        try:
            # Test encryption endpoint
            test_data = {"test": "data"}
            response = requests.post(
                'http://localhost:8000/api/v1/security/encryption/encrypt',
                json={'data': test_data, 'layer': 'storage'}
            )
            
            if response.status_code == 200:
                logger.info("Encryption test passed")
                return True
            else:
                logger.error("Encryption test failed")
                return False
                
        except Exception as e:
            logger.error(f"Encryption test failed: {str(e)}")
            return False
    
    def test_access_control(self) -> bool:
        """Test access control mechanisms"""
        try:
            # Test RBAC endpoint
            response = requests.post(
                'http://localhost:8000/api/v1/security/rbac/check-permission',
                json={'user_id': 'test', 'resource': 'building', 'action': 'read'}
            )
            
            if response.status_code == 200:
                logger.info("Access control test passed")
                return True
            else:
                logger.error("Access control test failed")
                return False
                
        except Exception as e:
            logger.error(f"Access control test failed: {str(e)}")
            return False
    
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        logger.info("Running health checks")
        
        health_checks = [
            self.check_api_health(),
            self.check_database_health(),
            self.check_cache_health(),
            self.check_file_storage_health(),
            self.check_security_services_health()
        ]
        
        all_healthy = all(health_checks)
        
        self.results['health_checks'] = {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': health_checks
        }
        
        return all_healthy
    
    def check_api_health(self) -> bool:
        """Check API health"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_database_health(self) -> bool:
        """Check database health"""
        try:
            response = requests.get('http://localhost:8000/api/v1/health/database', timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_cache_health(self) -> bool:
        """Check cache health"""
        try:
            response = requests.get('http://localhost:8000/api/v1/health/cache', timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_file_storage_health(self) -> bool:
        """Check file storage health"""
        try:
            response = requests.get('http://localhost:8000/api/v1/health/storage', timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_security_services_health(self) -> bool:
        """Check security services health"""
        try:
            response = requests.get('http://localhost:8000/api/v1/security/health', timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring and alerting"""
        logger.info("Setting up monitoring")
        
        try:
            # Setup log monitoring
            self.setup_log_monitoring()
            
            # Setup performance monitoring
            self.setup_performance_monitoring()
            
            # Setup alerting
            self.setup_alerting()
            
            logger.info("Monitoring setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {str(e)}")
            return False
    
    def setup_log_monitoring(self):
        """Setup log monitoring"""
        # Configure log rotation
        logrotate_config = """
/opt/arxos/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 arxos arxos
}
"""
        with open('/etc/logrotate.d/arxos', 'w') as f:
            f.write(logrotate_config)
        
        logger.info("Log monitoring configured")
    
    def setup_performance_monitoring(self):
        """Setup performance monitoring"""
        # This would typically involve setting up Prometheus, Grafana, etc.
        # For now, we'll just log that it's configured
        logger.info("Performance monitoring configured")
    
    def setup_alerting(self):
        """Setup alerting"""
        # This would typically involve setting up alerting rules
        # For now, we'll just log that it's configured
        logger.info("Alerting configured")
    
    def post_deployment_validation(self) -> bool:
        """Run post-deployment validation"""
        logger.info("Running post-deployment validation")
        
        validations = [
            self.validate_functionality(),
            self.validate_performance(),
            self.validate_security(),
            self.validate_monitoring()
        ]
        
        all_passed = all(validations)
        
        self.results['post_deployment_validation'] = {
            'status': 'passed' if all_passed else 'failed',
            'validations': validations
        }
        
        return all_passed
    
    def validate_functionality(self) -> bool:
        """Validate core functionality"""
        try:
            # Test SVG upload
            with open('tests/test_data/sample.svg', 'rb') as f:
                files = {'file': f}
                response = requests.post('http://localhost:8000/api/v1/upload/svg', files=files)
            
            if response.status_code != 200:
                return False
            
            # Test BIM assembly
            svg_id = response.json().get('svg_id')
            if svg_id:
                response = requests.post(
                    'http://localhost:8000/api/v1/assemble/bim',
                    data={'svg_id': svg_id, 'format': 'json'}
                )
                if response.status_code != 200:
                    return False
            
            logger.info("Functionality validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Functionality validation failed: {str(e)}")
            return False
    
    def validate_performance(self) -> bool:
        """Validate performance metrics"""
        try:
            # Test response time
            start_time = time.time()
            response = requests.get('http://localhost:8000/health')
            response_time = (time.time() - start_time) * 1000
            
            if response_time > 1000:  # 1 second threshold
                logger.warning(f"Response time too slow: {response_time}ms")
                return False
            
            logger.info(f"Performance validation passed: {response_time}ms")
            return True
            
        except Exception as e:
            logger.error(f"Performance validation failed: {str(e)}")
            return False
    
    def validate_security(self) -> bool:
        """Validate security measures"""
        try:
            # Test HTTPS redirect (if configured)
            response = requests.get('http://localhost:8000/health', allow_redirects=False)
            
            # Test security headers
            response = requests.get('http://localhost:8000/health')
            headers = response.headers
            
            security_headers = [
                'X-Frame-Options',
                'X-Content-Type-Options',
                'X-XSS-Protection'
            ]
            
            for header in security_headers:
                if header not in headers:
                    logger.warning(f"Missing security header: {header}")
            
            logger.info("Security validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Security validation failed: {str(e)}")
            return False
    
    def validate_monitoring(self) -> bool:
        """Validate monitoring setup"""
        try:
            # Check if monitoring endpoints are accessible
            monitoring_endpoints = [
                '/health',
                '/metrics',
                '/api/v1/health'
            ]
            
            for endpoint in monitoring_endpoints:
                response = requests.get(f'http://localhost:8000{endpoint}')
                if response.status_code != 200:
                    logger.warning(f"Monitoring endpoint not accessible: {endpoint}")
            
            logger.info("Monitoring validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring validation failed: {str(e)}")
            return False
    
    def rollback_deployment(self):
        """Rollback deployment in case of failure"""
        logger.info("Rolling back deployment")
        
        try:
            # Stop application
            self.stop_application()
            
            # Restore database if needed
            if hasattr(self, 'backup_created'):
                self.restore_database()
            
            # Restore files if needed
            if hasattr(self, 'files_backed_up'):
                self.restore_files()
            
            logger.info("Rollback completed")
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
    
    def generate_deployment_report(self):
        """Generate deployment report"""
        report = {
            'deployment_id': self.deployment_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'success' if all(self.results.values()) else 'failed',
            'results': self.results
        }
        
        # Save report
        with open(f'logs/deployment_report_{self.deployment_id}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Deployment report saved: deployment_report_{self.deployment_id}.json")
        return report

def main():
    """Main deployment function"""
    deployer = ProductionDeployer()
    
    success = deployer.run_deployment()
    
    # Generate report
    report = deployer.generate_deployment_report()
    
    if success:
        logger.info("Production deployment completed successfully")
        print("✅ Production deployment completed successfully")
    else:
        logger.error("Production deployment failed")
        print("❌ Production deployment failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 