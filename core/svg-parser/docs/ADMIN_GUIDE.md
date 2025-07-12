# Arxos Admin Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Installation & Deployment](#installation--deployment)
3. [Configuration Management](#configuration-management)
4. [Security Administration](#security-administration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Backup & Recovery](#backup--recovery)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## System Overview

### Architecture

The Arxos platform consists of several key components:

- **API Server**: FastAPI-based REST API
- **Database**: SQLite with optional PostgreSQL
- **Cache Layer**: Redis for performance optimization
- **File Storage**: Local filesystem with cloud options
- **Security Services**: Multi-layer encryption and access control
- **Export Services**: Multi-format data export
- **Monitoring**: Real-time telemetry and logging

### System Requirements

**Minimum Requirements:**
- Python 3.8+
- 4GB RAM
- 10GB storage
- Linux/macOS/Windows

**Recommended Requirements:**
- Python 3.9+
- 8GB RAM
- 50GB storage
- SSD storage
- Multi-core CPU

---

## Installation & Deployment

### Production Deployment

#### 1. Environment Setup

```bash
# Create virtual environment
python -m venv arxos_env
source arxos_env/bin/activate  # Linux/macOS
# or
arxos_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configuration

Create environment file:
```bash
# .env
DATABASE_URL=sqlite:///./arxos.db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### 3. Database Setup

```bash
# Initialize database
python scripts/manage_database.py init

# Run migrations
alembic upgrade head
```

#### 4. Start Services

```bash
# Start API server
python main.py

# Start background workers (optional)
python -m services.background_workers
```

### Docker Deployment

#### 1. Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/arxos
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### 2. Build and Deploy

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Cloud Deployment

#### AWS Deployment

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Deploy to ECS
aws ecs create-cluster --cluster-name arxos-cluster
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster arxos-cluster --service-name arxos-api --task-definition arxos-api
```

#### Azure Deployment

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Create resource group
az group create --name arxos-rg --location eastus

# Deploy to App Service
az webapp create --resource-group arxos-rg --plan arxos-plan --name arxos-api
```

---

## Configuration Management

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | `sqlite:///./arxos.db` | No |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | No |
| `SECRET_KEY` | Application secret key | Random | Yes |
| `ENVIRONMENT` | Environment (dev/prod) | `development` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `*` | No |
| `MAX_FILE_SIZE` | Maximum file upload size | `50MB` | No |
| `ENCRYPTION_KEY` | Encryption key | Random | Yes |

### Configuration Files

#### 1. Application Config

```python
# config/app_config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./arxos.db"
    redis_url: str = "redis://localhost:6379"
    secret_key: str
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 2. Security Config

```python
# config/security_config.py
SECURITY_CONFIG = {
    "encryption": {
        "algorithm": "AES-256",
        "key_rotation_days": 90,
        "layers": ["transport", "storage", "application"]
    },
    "privacy": {
        "classification_levels": ["public", "internal", "confidential", "restricted"],
        "default_classification": "internal"
    },
    "audit": {
        "retention_days": 2555,
        "log_all_events": True,
        "sensitive_fields": ["password", "token", "key"]
    }
}
```

### Database Configuration

#### SQLite (Default)

```python
# For development
DATABASE_URL = "sqlite:///./arxos.db"

# For production (with WAL mode)
DATABASE_URL = "sqlite:///./arxos.db?mode=rwc&cache=shared"
```

#### PostgreSQL

```python
# For production
DATABASE_URL = "postgresql://user:password@localhost:5432/arxos"
```

#### Connection Pooling

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## Security Administration

### User Management

#### 1. Create Admin User

```python
from services.auth_service import AuthService
from services.rbac_service import RBACService

auth = AuthService()
rbac = RBACService()

# Create admin user
admin_user = auth.create_user(
    username="admin",
    email="admin@arxos.com",
    password="secure_password",
    role="administrator"
)

# Assign admin role
rbac.assign_user_to_role(admin_user.id, "administrator")
```

#### 2. Role Management

```python
# Create custom role
role = rbac.create_role(
    role_name="Building Inspector",
    permissions=[
        "building:read",
        "inspection:create",
        "violation:report",
        "compliance:view"
    ],
    description="Building inspection and compliance role"
)

# Assign user to role
rbac.assign_user_to_role("user123", role.id)
```

#### 3. Permission Auditing

```python
# Audit user permissions
permissions = rbac.get_user_permissions("user123")
print(f"User has {len(permissions)} permissions")

# Check specific permission
has_permission = rbac.check_permission("user123", "building", "write")
```

### Encryption Management

#### 1. Key Rotation

```python
from services.encryption_service import EncryptionService

encryption = EncryptionService()

# Rotate encryption keys
result = encryption.rotate_keys("all")
print(f"Rotated {result.keys_rotated} keys")

# Check key status
status = encryption.get_key_status()
print(f"Key status: {status}")
```

#### 2. Encryption Monitoring

```python
# Get encryption metrics
metrics = encryption.get_metrics()
print(f"Total operations: {metrics.total_operations}")
print(f"Average time: {metrics.average_time_ms}ms")
```

### Privacy Controls

#### 1. Data Classification

```python
from services.privacy_controls import PrivacyControls

privacy = PrivacyControls()

# Classify data
classification = privacy.classify_data("building_data", building_info)
print(f"Classification: {classification.classification_level}")

# Apply privacy controls
protected_data = privacy.apply_privacy_controls(data, classification)
```

#### 2. Anonymization

```python
# Anonymize sensitive data
anonymized_data = privacy.anonymize_data(
    data=user_data,
    fields_to_anonymize=["user_id", "email", "name"]
)
```

### Audit Trail Management

#### 1. Audit Configuration

```python
from services.audit_trail import AuditTrail

audit = AuditTrail()

# Configure audit settings
audit.configure(
    log_all_events=True,
    retention_days=2555,
    sensitive_fields=["password", "token", "key"]
)
```

#### 2. Audit Reports

```python
# Generate compliance report
report = audit.generate_compliance_report(
    report_type="data_access",
    start_date="2024-12-01T00:00:00Z",
    end_date="2024-12-19T23:59:59Z"
)

print(f"Total events: {report.total_events}")
print(f"Unique users: {report.unique_users}")
```

#### 3. Retention Enforcement

```python
# Enforce retention policies
result = audit.enforce_retention_policies()
print(f"Enforced {result.policies_enforced} policies")
```

---

## Monitoring & Maintenance

### Health Monitoring

#### 1. System Health Check

```python
from services.health_check import HealthCheck

health = HealthCheck()

# Check all services
status = health.check_all_services()
print(f"Overall status: {status.overall_status}")

# Check specific service
db_status = health.check_database()
print(f"Database status: {db_status}")
```

#### 2. Performance Monitoring

```python
from services.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()

# Get performance metrics
metrics = monitor.get_metrics()
print(f"CPU usage: {metrics.cpu_percent}%")
print(f"Memory usage: {metrics.memory_percent}%")
print(f"Disk usage: {metrics.disk_percent}%")
```

#### 3. API Monitoring

```python
# Monitor API endpoints
api_metrics = monitor.get_api_metrics()
print(f"Total requests: {api_metrics.total_requests}")
print(f"Average response time: {api_metrics.avg_response_time}ms")
print(f"Error rate: {api_metrics.error_rate}%")
```

### Log Management

#### 1. Log Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/arxos.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
```

#### 2. Log Analysis

```python
from services.log_analyzer import LogAnalyzer

analyzer = LogAnalyzer()

# Analyze error patterns
errors = analyzer.analyze_errors("logs/arxos.log")
print(f"Found {len(errors)} error patterns")

# Analyze performance
performance = analyzer.analyze_performance("logs/arxos.log")
print(f"Average response time: {performance.avg_response_time}ms")
```

### Maintenance Tasks

#### 1. Database Maintenance

```python
from services.database_maintenance import DatabaseMaintenance

maintenance = DatabaseMaintenance()

# Optimize database
maintenance.optimize_database()

# Clean up old data
maintenance.cleanup_old_data(days=90)

# Update statistics
maintenance.update_statistics()
```

#### 2. Cache Maintenance

```python
from services.cache_service import CacheService

cache = CacheService()

# Clear expired cache entries
cache.clear_expired()

# Optimize cache
cache.optimize()

# Get cache statistics
stats = cache.get_statistics()
print(f"Cache hit rate: {stats.hit_rate}%")
```

#### 3. File System Maintenance

```python
from services.file_maintenance import FileMaintenance

maintenance = FileMaintenance()

# Clean up temporary files
maintenance.cleanup_temp_files()

# Compress old files
maintenance.compress_old_files(days=30)

# Check disk usage
usage = maintenance.get_disk_usage()
print(f"Disk usage: {usage.percent}%")
```

---

## Backup & Recovery

### Database Backup

#### 1. Automated Backup

```python
from services.backup_service import BackupService

backup = BackupService()

# Create backup
backup.create_database_backup()

# Schedule daily backup
backup.schedule_backup(
    frequency="daily",
    time="02:00",
    retention_days=30
)
```

#### 2. Backup Verification

```python
# Verify backup integrity
is_valid = backup.verify_backup("backup_20241219.sql")
print(f"Backup valid: {is_valid}")

# Test backup restoration
restore_test = backup.test_restore("backup_20241219.sql")
print(f"Restore test successful: {restore_test}")
```

### File Backup

#### 1. Export Data Backup

```python
# Backup export files
backup.backup_export_files()

# Backup configuration files
backup.backup_config_files()

# Backup logs
backup.backup_log_files()
```

#### 2. Cloud Backup

```python
# Upload to cloud storage
backup.upload_to_cloud("backup_20241219.tar.gz")

# Sync with cloud
backup.sync_with_cloud()
```

### Disaster Recovery

#### 1. Recovery Plan

```python
from services.recovery_service import RecoveryService

recovery = RecoveryService()

# Create recovery plan
plan = recovery.create_recovery_plan()
print(f"Recovery time: {plan.estimated_time} minutes")

# Test recovery
test_result = recovery.test_recovery_plan()
print(f"Recovery test successful: {test_result}")
```

#### 2. Point-in-Time Recovery

```python
# Restore to specific point in time
recovery.restore_to_point_in_time("2024-12-19T10:30:00Z")

# Verify restoration
is_restored = recovery.verify_restoration()
print(f"Restoration successful: {is_restored}")
```

---

## Performance Tuning

### Database Optimization

#### 1. Index Optimization

```python
from services.database_optimizer import DatabaseOptimizer

optimizer = DatabaseOptimizer()

# Analyze index usage
index_analysis = optimizer.analyze_indexes()
print(f"Unused indexes: {len(index_analysis.unused_indexes)}")

# Create missing indexes
optimizer.create_missing_indexes()

# Remove unused indexes
optimizer.remove_unused_indexes()
```

#### 2. Query Optimization

```python
# Analyze slow queries
slow_queries = optimizer.analyze_slow_queries()
print(f"Found {len(slow_queries)} slow queries")

# Optimize queries
optimizer.optimize_queries(slow_queries)
```

### Cache Optimization

#### 1. Cache Strategy

```python
from services.cache_optimizer import CacheOptimizer

optimizer = CacheOptimizer()

# Analyze cache performance
performance = optimizer.analyze_cache_performance()
print(f"Cache hit rate: {performance.hit_rate}%")

# Optimize cache settings
optimizer.optimize_cache_settings()
```

#### 2. Memory Management

```python
# Monitor memory usage
memory_usage = optimizer.get_memory_usage()
print(f"Memory usage: {memory_usage.percent}%")

# Optimize memory
optimizer.optimize_memory_usage()
```

### API Performance

#### 1. Response Time Optimization

```python
from services.api_optimizer import APIOptimizer

optimizer = APIOptimizer()

# Analyze API performance
performance = optimizer.analyze_api_performance()
print(f"Average response time: {performance.avg_response_time}ms")

# Optimize slow endpoints
optimizer.optimize_slow_endpoints()
```

#### 2. Rate Limiting

```python
# Configure rate limiting
optimizer.configure_rate_limiting(
    requests_per_minute=100,
    requests_per_hour=1000,
    burst_limit=50
)
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

**Problem:** Database connection failures
**Diagnosis:**
```python
from services.diagnostic import Diagnostic

diagnostic = Diagnostic()

# Check database connectivity
db_status = diagnostic.check_database_connectivity()
print(f"Database status: {db_status}")

# Check connection pool
pool_status = diagnostic.check_connection_pool()
print(f"Pool status: {pool_status}")
```

**Solution:**
```python
# Restart database connection
from services.database_service import DatabaseService

db = DatabaseService()
db.restart_connection()

# Clear connection pool
db.clear_connection_pool()
```

#### 2. Memory Issues

**Problem:** High memory usage
**Diagnosis:**
```python
# Check memory usage
memory_usage = diagnostic.check_memory_usage()
print(f"Memory usage: {memory_usage.percent}%")

# Check memory leaks
leaks = diagnostic.check_memory_leaks()
print(f"Potential leaks: {len(leaks)}")
```

**Solution:**
```python
# Optimize memory
from services.memory_manager import MemoryManager

memory = MemoryManager()
memory.optimize_memory_usage()

# Clear caches
memory.clear_caches()
```

#### 3. Performance Issues

**Problem:** Slow response times
**Diagnosis:**
```python
# Analyze performance bottlenecks
bottlenecks = diagnostic.analyze_performance_bottlenecks()
print(f"Found {len(bottlenecks)} bottlenecks")

# Check slow queries
slow_queries = diagnostic.check_slow_queries()
print(f"Slow queries: {len(slow_queries)}")
```

**Solution:**
```python
# Optimize performance
from services.performance_optimizer import PerformanceOptimizer

optimizer = PerformanceOptimizer()
optimizer.optimize_performance()
```

### Emergency Procedures

#### 1. Service Restart

```python
from services.service_manager import ServiceManager

manager = ServiceManager()

# Restart all services
manager.restart_all_services()

# Restart specific service
manager.restart_service("api")
```

#### 2. Emergency Rollback

```python
from services.rollback_service import RollbackService

rollback = RollbackService()

# Rollback to previous version
rollback.rollback_to_version("v1.2.0")

# Verify rollback
is_rolled_back = rollback.verify_rollback()
print(f"Rollback successful: {is_rolled_back}")
```

#### 3. Emergency Contact

For critical issues:
- **Email**: admin@arxos.com
- **Phone**: +1-555-ARXOS-1
- **Slack**: #arxos-admin

---

## Support Resources

### Documentation
- [API Documentation](./API_DOCUMENTATION.md)
- [User Guide](./USER_GUIDE.md)
- [Developer Guide](./DEVELOPER_GUIDE.md)

### Monitoring Tools
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601

### Log Locations
- **Application logs**: `logs/arxos.log`
- **Error logs**: `logs/errors.log`
- **Access logs**: `logs/access.log`
- **Security logs**: `logs/security.log`

### Maintenance Schedule
- **Daily**: Database backup, log rotation
- **Weekly**: Performance analysis, cache cleanup
- **Monthly**: Security audit, system updates
- **Quarterly**: Full system review, capacity planning

---

**Version**: 1.0.0  
**Last Updated**: December 19, 2024  
**Contact**: admin@arxos.com 