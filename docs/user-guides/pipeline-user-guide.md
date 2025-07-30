# 🚀 Arxos Pipeline User Guide

## 📖 **Overview**

The Arxos Pipeline is a comprehensive system for integrating new building systems into the Arxos ecosystem. This guide covers all aspects of using the pipeline, from basic operations to advanced features.

---

## 🎯 **Quick Start**

### **1. Deploy the Pipeline**
```bash
# Deploy the complete pipeline
./scripts/deploy_pipeline.sh

# Set up production environment
./scripts/setup_production_environment.sh production localhost 5432 arxos_prod arxos_user arxos_password
```

### **2. Test the Pipeline**
```bash
# Run comprehensive tests
python3 tests/test_pipeline_comprehensive.py

# Run demonstration
python3 examples/pipeline_demo.py
```

### **3. Execute Your First Pipeline**
```bash
# Execute pipeline for a new system
python3 scripts/arx_pipeline.py --execute --system audiovisual

# Check status
python3 scripts/arx_pipeline.py --status
```

---

## 🛠️ **Core Operations**

### **Pipeline Execution**

#### **Full Pipeline Execution**
```bash
# Execute complete pipeline for a system
python3 scripts/arx_pipeline.py --execute --system electrical

# Execute with specific object type
python3 scripts/arx_pipeline.py --execute --system mechanical --object hvac_unit

# Dry run (test without making changes)
python3 scripts/arx_pipeline.py --execute --system plumbing --dry-run
```

#### **Step-by-Step Execution**
```bash
# Execute specific step
python3 scripts/arx_pipeline.py --step validate-schema --system electrical

# Execute multiple steps
python3 scripts/arx_pipeline.py --steps validate-schema,add-symbols --system fire_alarm
```

### **Validation Operations**

#### **Schema Validation**
```bash
# Validate system schema
python3 scripts/arx_pipeline.py --validate --system electrical

# Validate specific schema file
python3 scripts/arx_pipeline.py --validate-schema --file schemas/electrical/schema.json
```

#### **Symbol Validation**
```bash
# Validate all symbols for a system
python3 scripts/arx_pipeline.py --validate-symbols --system mechanical

# Validate specific symbol
python3 scripts/arx_pipeline.py --validate-symbol --symbol E_Panel_001
```

#### **Behavior Validation**
```bash
# Validate behavior profiles
python3 scripts/arx_pipeline.py --validate-behavior --system electrical

# Validate specific behavior
python3 scripts/arx_pipeline.py --validate-behavior --profile electrical_panel
```

### **Monitoring and Analytics**

#### **System Health**
```bash
# Check system health
python3 -c "
from svgx_engine.services.monitoring import get_monitoring
health = get_monitoring().get_system_health()
print(f'Overall Status: {health[\"overall_status\"]}')
for service, status in health['services'].items():
    print(f'{service}: {status[\"status\"]}')
"
```

#### **Performance Analytics**
```bash
# Generate performance report
python3 -c "
from svgx_engine.services.pipeline_analytics import get_analytics
report = get_analytics().create_performance_report('electrical')
print(f'Success Rate: {report[\"performance_summary\"][\"success_rate\"]:.1f}%')
print(f'Avg Execution Time: {report[\"performance_summary\"][\"avg_execution_time\"]:.1f}s')
"
```

#### **Create Visualizations**
```bash
# Generate analytics charts
python3 -c "
from svgx_engine.services.pipeline_analytics import get_analytics
get_analytics().generate_visualizations('electrical')
print('Charts generated in analytics_charts/')
"
```

### **Backup and Recovery**

#### **Create Backups**
```bash
# Create full backup
python3 -c "
from svgx_engine.services.rollback_recovery import get_rollback_recovery
backup_id = get_rollback_recovery().create_backup('electrical', 'full', 'Pre-update backup')
print(f'Backup created: {backup_id}')
"
```

#### **List Backups**
```bash
# List all backups
python3 -c "
from svgx_engine.services.rollback_recovery import get_rollback_recovery
backups = get_rollback_recovery().list_backups('electrical')
for backup in backups:
    print(f'{backup.id}: {backup.description} ({backup.backup_type})')
"
```

#### **Restore Backup**
```bash
# Restore from backup
python3 -c "
from svgx_engine.services.rollback_recovery import get_rollback_recovery
success = get_rollback_recovery().restore_backup('backup_id_here')
print(f'Restore successful: {success}')
"
```

---

## 🔧 **Advanced Features**

### **Custom System Integration**

#### **1. Define System Schema**
Create a schema file for your system:

```json
{
  "system": "audiovisual",
  "objects": {
    "display": {
      "properties": {
        "resolution": "1920x1080",
        "type": "LED",
        "brightness": "400 nits"
      },
      "relationships": {
        "connected_to": ["control_system", "power_supply"]
      },
      "behavior_profile": "display_behavior"
    },
    "projector": {
      "properties": {
        "brightness": "3000 lumens",
        "type": "DLP",
        "throw_ratio": "1.2:1"
      },
      "relationships": {
        "connected_to": ["control_system", "mounting_system"]
      },
      "behavior_profile": "projector_behavior"
    }
  }
}
```

#### **2. Create SVGX Symbols**
Add symbols to `arx-symbol-library/audiovisual/`:

```json
{
  "id": "AV_Display_001",
  "name": "LED Display",
  "system": "audiovisual",
  "category": "display",
  "svg": "<svg>...</svg>",
  "properties": {
    "resolution": "1920x1080",
    "type": "LED"
  },
  "connections": ["control", "power", "video"],
  "behavior_profile": "display_behavior"
}
```

#### **3. Implement Behavior Profiles**
Create behavior profiles in `svgx_engine/behavior/`:

```python
class DisplayBehavior:
    def __init__(self):
        self.power_state = "off"
        self.brightness = 50
    
    def power_on(self):
        self.power_state = "on"
        return {"status": "powered_on", "brightness": self.brightness}
    
    def set_brightness(self, level):
        self.brightness = max(0, min(100, level))
        return {"status": "brightness_set", "level": self.brightness}
    
    def validate_connections(self, connections):
        required = ["power", "control"]
        return all(conn in connections for conn in required)
```

#### **4. Execute Pipeline**
```bash
# Execute pipeline for your system
python3 scripts/arx_pipeline.py --execute --system audiovisual

# Monitor progress
python3 scripts/arx_pipeline.py --status --system audiovisual
```

### **API Integration**

#### **REST API Usage**
```bash
# Execute pipeline via API
curl -X POST http://localhost:8080/api/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{
    "system": "audiovisual",
    "object_type": "display",
    "dry_run": false
  }'

# Get pipeline status
curl http://localhost:8080/api/pipeline/status/{execution_id}

# List executions
curl http://localhost:8080/api/pipeline/executions?system=audiovisual
```

#### **Python API Usage**
```python
from svgx_engine.services.pipeline_integration import PipelineIntegrationService

# Initialize service
service = PipelineIntegrationService()

# Execute pipeline
result = service.handle_operation("execute-pipeline", {
    "system": "audiovisual",
    "object_type": "display"
})

print(f"Pipeline execution: {result['success']}")
```

### **Monitoring and Alerting**

#### **Custom Metrics**
```python
from svgx_engine.services.monitoring import get_monitoring

# Record custom metric
monitoring = get_monitoring()
monitoring.record_metric(
    "custom_operation_duration",
    150.5,
    "milliseconds",
    {"system": "audiovisual", "operation": "symbol_creation"}
)
```

#### **Custom Health Checks**
```python
# Update health check
monitoring.update_health_check(
    "audiovisual_service",
    "healthy",
    {"version": "1.0.0", "connections": 5}
)
```

#### **Create Alerts**
```python
# Create custom alert
monitoring.create_alert(
    "high_execution_time",
    "warning",
    "Pipeline execution time exceeded 5 minutes"
)
```

---

## 📊 **Analytics and Reporting**

### **Performance Reports**

#### **Generate Comprehensive Report**
```python
from svgx_engine.services.pipeline_analytics import get_analytics

analytics = get_analytics()

# Generate performance report
report = analytics.create_performance_report("electrical", days=30)

print(f"Success Rate: {report['performance_summary']['success_rate']:.1f}%")
print(f"Total Executions: {report['performance_summary']['total_executions']}")
print(f"Bottlenecks: {report['bottlenecks']}")
```

#### **Export Analytics Data**
```python
# Export as JSON
json_data = analytics.export_analytics_data("json", "electrical")

# Export as CSV
csv_data = analytics.export_analytics_data("csv", "electrical")

# Save to file
with open("analytics_report.json", "w") as f:
    f.write(json_data)
```

### **Trend Analysis**

#### **Analyze Trends**
```python
# Analyze success rate trend
trend = analytics.analyze_trends("success_rate", days=30)
print(f"Trend: {trend.trend_direction}")
print(f"Change: {trend.change_percentage:.1f}%")
```

#### **Generate Insights**
```python
# Generate insights
insights = analytics.generate_insights("electrical")
for insight in insights:
    print(f"{insight.title}: {insight.description}")
    print(f"Recommendation: {insight.recommendation}")
```

---

## 🔄 **Backup and Recovery**

### **Automated Backups**

#### **Schedule Backups**
```bash
# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/scripts/backup_pipeline.sh") | crontab -

# Manual backup
./scripts/backup_pipeline.sh
```

#### **Backup Types**
```python
from svgx_engine.services.rollback_recovery import get_rollback_recovery

rr = get_rollback_recovery()

# Full backup (everything)
backup_id = rr.create_backup("electrical", "full", "Complete system backup")

# Schema-only backup
backup_id = rr.create_backup("electrical", "schema", "Schema backup")

# Symbols-only backup
backup_id = rr.create_backup("electrical", "symbols", "Symbols backup")

# Behavior-only backup
backup_id = rr.create_backup("electrical", "behavior", "Behavior backup")
```

### **Recovery Procedures**

#### **Point-in-Time Recovery**
```python
# List available backups
backups = rr.list_backups("electrical")
for backup in backups:
    print(f"{backup.id}: {backup.description}")

# Restore specific backup
success = rr.restore_backup("backup_id_here")
```

#### **Conflict Resolution**
```python
# Restore with automatic conflict resolution
success = rr.restore_backup("backup_id", conflict_resolution="auto")

# Restore with manual conflict resolution
success = rr.restore_backup("backup_id", conflict_resolution="manual")
```

---

## 🛡️ **Security and Compliance**

### **Security Scanning**

#### **Run Security Scans**
```bash
# Run Bandit security scan
bandit -r svgx_engine/services/ -f json -o security-report.json

# Run Safety vulnerability scan
safety check --json --output vulnerabilities.json
```

#### **Compliance Checking**
```bash
# Run compliance tests
python3 -m pytest tests/test_pipeline_integration.py::TestPipelineIntegration::test_validate_schema_success -v

# Generate compliance report
python3 scripts/arx_pipeline.py --step compliance --system electrical
```

### **Access Control**

#### **User Permissions**
```python
# Check user permissions
def check_permission(user, system, operation):
    # Implement your permission logic here
    return user.has_permission(system, operation)

# Secure pipeline execution
if check_permission(current_user, "electrical", "execute"):
    result = service.handle_operation("execute-pipeline", {"system": "electrical"})
else:
    raise PermissionError("Insufficient permissions")
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Pipeline Execution Fails**
```bash
# Check pipeline status
python3 scripts/arx_pipeline.py --status

# Check logs
tail -f logs/pipeline.log

# Run health check
./scripts/health_check.sh
```

#### **2. Database Connection Issues**
```bash
# Test database connection
psql -h localhost -p 5432 -U arxos_user -d arxos_prod -c "SELECT 1;"

# Check database status
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://arxos_user:password@localhost:5432/arxos_prod')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### **3. Performance Issues**
```bash
# Check system resources
top
df -h
free -h

# Check pipeline performance
python3 -c "
from svgx_engine.services.pipeline_analytics import get_analytics
report = get_analytics().create_performance_report()
print(f'Success Rate: {report[\"performance_summary\"][\"success_rate\"]:.1f}%')
print(f'Avg Execution Time: {report[\"performance_summary\"][\"avg_execution_time\"]:.1f}s')
"
```

#### **4. Backup/Restore Issues**
```bash
# Verify backup integrity
python3 -c "
from svgx_engine.services.rollback_recovery import get_rollback_recovery
rr = get_rollback_recovery()
backups = rr.list_backups('electrical')
for backup in backups:
    integrity = rr.verify_backup_integrity(backup.id)
    print(f'{backup.id}: {integrity}')
"
```

### **Debug Mode**

#### **Enable Debug Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run pipeline with debug output
python3 scripts/arx_pipeline.py --execute --system electrical --debug
```

#### **Verbose Output**
```bash
# Run with verbose output
python3 scripts/arx_pipeline.py --execute --system electrical --verbose

# Check detailed logs
tail -f logs/pipeline.log | grep DEBUG
```

---

## 📈 **Best Practices**

### **1. System Design**
- **Modular Design**: Keep systems independent and modular
- **Clear Naming**: Use consistent naming conventions
- **Documentation**: Document all schemas and behavior profiles
- **Version Control**: Use version control for all configurations

### **2. Performance Optimization**
- **Caching**: Implement caching for frequently accessed data
- **Parallel Processing**: Use parallel processing for independent operations
- **Resource Monitoring**: Monitor system resources continuously
- **Regular Cleanup**: Clean up old data and backups regularly

### **3. Security**
- **Input Validation**: Validate all inputs thoroughly
- **Access Control**: Implement proper access controls
- **Audit Logging**: Log all operations for audit purposes
- **Regular Updates**: Keep dependencies and security tools updated

### **4. Monitoring**
- **Health Checks**: Implement comprehensive health checks
- **Alerting**: Set up proper alerting for critical issues
- **Metrics Collection**: Collect and analyze performance metrics
- **Regular Reports**: Generate regular performance reports

### **5. Backup and Recovery**
- **Regular Backups**: Schedule regular automated backups
- **Test Recovery**: Regularly test backup and recovery procedures
- **Multiple Locations**: Store backups in multiple locations
- **Documentation**: Document all backup and recovery procedures

---

## 📞 **Support and Resources**

### **Documentation**
- **API Documentation**: Available at `/docs/api/`
- **Architecture Guide**: See `docs/ARCHITECTURE.md`
- **Deployment Guide**: See `docs/DEPLOYMENT.md`

### **Community**
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Join community discussions
- **Contributing**: See `CONTRIBUTING.md`

### **Support**
- **Email**: support@arxos.com
- **Documentation**: https://docs.arxos.com
- **Training**: Available training sessions

---

*This guide covers all aspects of using the Arxos Pipeline. For additional help, refer to the documentation or contact support.* 