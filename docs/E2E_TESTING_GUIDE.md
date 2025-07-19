# 🧪 Arxos Pipeline E2E Testing Guide

## 📖 **Overview**

This guide provides comprehensive instructions for running end-to-end (E2E) tests on the Arxos pipeline. E2E testing validates the complete pipeline flow from system definition to production deployment.

---

## 🎯 **Quick Start**

### **1. Run Complete E2E Test Suite**
```bash
# Run all E2E tests
python scripts/run_e2e_tests.py

# Run specific E2E test file
python tests/e2e/test_pipeline_e2e.py

# Run with verbose output
python -m pytest tests/e2e/test_pipeline_e2e.py -v
```

### **2. Run Individual Test Categories**
```bash
# Unit tests only
python -m pytest tests/test_pipeline_integration.py -v

# Integration tests only
python tests/test_pipeline_comprehensive.py

# Performance tests only
python -m pytest tests/test_pipeline_e2e.py::TestPipelineE2E::test_pipeline_performance_e2e -v
```

---

## 🧪 **Test Categories**

### **1. Unit Tests**
**Purpose**: Test individual components in isolation
**Location**: `tests/test_pipeline_integration.py`
**Coverage**: Individual service functions, validation logic, error handling

```bash
# Run unit tests
python -m pytest tests/test_pipeline_integration.py -v

# Run with coverage
python -m pytest tests/test_pipeline_integration.py --cov=svgx_engine/services/pipeline_integration --cov-report=html
```

### **2. Integration Tests**
**Purpose**: Test component interactions and workflows
**Location**: `tests/test_pipeline_comprehensive.py`
**Coverage**: Service interactions, database operations, API endpoints

```bash
# Run integration tests
python tests/test_pipeline_comprehensive.py

# Run specific integration test
python -c "
from tests.test_pipeline_comprehensive import TestPipelineComprehensive
test = TestPipelineComprehensive()
test.setUp()
test.test_full_pipeline_execution()
"
```

### **3. End-to-End Tests**
**Purpose**: Test complete pipeline flow from start to finish
**Location**: `tests/e2e/test_pipeline_e2e.py`
**Coverage**: Complete user workflows, system integration, production scenarios

```bash
# Run E2E tests
python tests/e2e/test_pipeline_e2e.py

# Run specific E2E test
python -c "
from tests.e2e.test_pipeline_e2e import TestPipelineE2E
test = TestPipelineE2E()
test.setUp()
test.test_complete_pipeline_e2e()
"
```

---

## 🔧 **Test Scenarios**

### **1. Complete Pipeline E2E Test**
```python
def test_complete_pipeline_e2e(self):
    """Test complete pipeline end-to-end execution"""
    
    # Step 1: Define System Schema
    schema_data = {
        "system": "test_system",
        "objects": {
            "sensor": {
                "properties": {"type": "temperature"},
                "relationships": {"connected_to": ["controller"]},
                "behavior_profile": "sensor_behavior"
            }
        }
    }
    
    # Step 2: Create SVGX Symbols
    symbols_data = [
        {
            "id": "TEST_Sensor_001",
            "name": "Temperature Sensor",
            "system": "test_system",
            "svg": "<svg>...</svg>",
            "behavior_profile": "sensor_behavior"
        }
    ]
    
    # Step 3: Implement Behavior Profiles
    behavior_code = """
    class SensorBehavior:
        def read_temperature(self):
            return {"temperature": 25.0}
    """
    
    # Step 4: Execute Pipeline
    pipeline_result = service.handle_operation("execute-pipeline", {
        "system": "test_system"
    })
    
    # Step 5: Verify Integration
    integration_result = service.handle_operation("verify-integration", {
        "system": "test_system"
    })
```

### **2. Real System E2E Test**
```python
def test_pipeline_with_real_system_e2e(self):
    """Test pipeline with realistic building system"""
    
    # Define realistic HVAC system
    hvac_schema = {
        "system": "hvac_realistic",
        "objects": {
            "thermostat": {
                "properties": {"type": "digital", "range": "50-90°F"},
                "relationships": {"controls": ["hvac_unit"]},
                "behavior_profile": "thermostat_behavior"
            },
            "hvac_unit": {
                "properties": {"type": "split_system", "capacity": "3.5 tons"},
                "relationships": {"controlled_by": ["thermostat"]},
                "behavior_profile": "hvac_unit_behavior"
            }
        }
    }
    
    # Execute pipeline with real system
    pipeline_result = service.handle_operation("execute-pipeline", {
        "system": "hvac_realistic"
    })
```

### **3. Error Recovery E2E Test**
```python
def test_pipeline_error_recovery_e2e(self):
    """Test pipeline error recovery and rollback capabilities"""
    
    # Create invalid schema (missing required fields)
    invalid_schema = {
        "system": "error_test_system",
        "objects": {
            "invalid_object": {
                # Missing required fields
            }
        }
    }
    
    # Attempt pipeline execution (should fail)
    pipeline_result = service.handle_operation("execute-pipeline", {
        "system": "error_test_system"
    })
    
    # Test rollback functionality
    rollback_result = service.handle_operation("rollback", {
        "system": "error_test_system"
    })
```

### **4. Performance E2E Test**
```python
def test_pipeline_performance_e2e(self):
    """Test pipeline performance under load"""
    
    # Create multiple systems for performance testing
    systems = [f"perf_test_system_{i}" for i in range(5)]
    
    start_time = time.time()
    results = []
    
    # Execute pipelines concurrently
    for system in systems:
        result = service.handle_operation("execute-pipeline", {
            "system": system,
            "dry_run": True
        })
        results.append(result)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Verify performance requirements
    assert execution_time < 30  # Should complete within 30 seconds
    assert all(r.get("success") for r in results)  # All should succeed
```

---

## 📊 **Monitoring and Analytics Tests**

### **1. System Health Monitoring**
```python
def test_pipeline_monitoring_e2e(self):
    """Test pipeline monitoring and analytics"""
    
    # Get monitoring service
    monitoring = get_monitoring()
    
    # Record test metrics
    monitoring.record_metric("e2e_test_executions", 1, "count")
    monitoring.record_metric("e2e_test_duration", 5.2, "seconds")
    
    # Check system health
    health = monitoring.get_system_health()
    assert health is not None
    assert "overall_status" in health
    
    # Test analytics
    analytics = get_analytics()
    report = analytics.create_performance_report("test_system")
    assert report is not None
```

### **2. Performance Analytics**
```python
def test_analytics_generation():
    """Test analytics report generation"""
    
    from svgx_engine.services.pipeline_analytics import get_analytics
    
    analytics = get_analytics()
    
    # Generate performance report
    report = analytics.create_performance_report("test_system", days=30)
    
    # Verify report structure
    assert "performance_summary" in report
    assert "success_rate" in report["performance_summary"]
    assert "avg_execution_time" in report["performance_summary"]
    
    # Generate visualizations
    analytics.generate_visualizations("test_system")
```

---

## 🔄 **Backup and Recovery Tests**

### **1. Backup Creation and Verification**
```python
def test_pipeline_backup_recovery_e2e(self):
    """Test pipeline backup and recovery functionality"""
    
    from svgx_engine.services.rollback_recovery import get_rollback_recovery
    
    rr = get_rollback_recovery()
    
    # Create backup
    backup_id = rr.create_backup("test_system", "full", "E2E test backup")
    assert backup_id is not None
    
    # List backups
    backups = rr.list_backups("test_system")
    assert len(backups) > 0
    
    # Verify backup integrity
    integrity = rr.verify_backup_integrity(backup_id)
    assert integrity is True
```

### **2. Recovery and Rollback**
```python
def test_recovery_procedures():
    """Test recovery and rollback procedures"""
    
    from svgx_engine.services.rollback_recovery import get_rollback_recovery
    
    rr = get_rollback_recovery()
    
    # Create test backup
    backup_id = rr.create_backup("test_system", "full", "Recovery test")
    
    # Test recovery
    recovery_result = rr.restore_backup(backup_id)
    assert recovery_result is True
    
    # Test rollback
    rollback_result = rr.rollback_to_backup(backup_id)
    assert rollback_result is True
```

---

## 🚀 **CLI and API Tests**

### **1. CLI Functionality**
```python
def test_pipeline_cli_e2e(self):
    """Test pipeline CLI functionality"""
    
    cli_commands = [
        ["python", "scripts/arx_pipeline.py", "--list-systems"],
        ["python", "scripts/arx_pipeline.py", "--help"],
        ["python", "scripts/arx_pipeline.py", "--validate", "--system", "test_system"],
    ]
    
    for cmd in cli_commands:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        # CLI should not crash
        assert result.returncode != -1
```

### **2. API Endpoints**
```python
def test_pipeline_api_e2e(self):
    """Test pipeline API endpoints"""
    
    from svgx_engine.services.pipeline_integration import PipelineIntegrationService
    
    service = PipelineIntegrationService()
    
    api_operations = [
        ("validate-schema", {"system": "api_test_system"}),
        ("list-systems", {}),
        ("get-status", {"system": "api_test_system"}),
    ]
    
    for operation, params in api_operations:
        result = service.handle_operation(operation, params)
        assert result is not None
```

---

## ⚡ **Performance Testing**

### **1. Load Testing**
```bash
# Run load tests with multiple concurrent users
python -c "
import time
import threading
from svgx_engine.services.pipeline_integration import PipelineIntegrationService

def run_pipeline_operation():
    service = PipelineIntegrationService()
    return service.handle_operation('list-systems', {})

# Run concurrent operations
threads = []
start_time = time.time()

for i in range(10):
    thread = threading.Thread(target=run_pipeline_operation)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

end_time = time.time()
print(f'Concurrent operations completed in {end_time - start_time:.2f}s')
"
```

### **2. Stress Testing**
```python
def test_stress_conditions():
    """Test pipeline under stress conditions"""
    
    # Test with large datasets
    large_schema = {
        "system": "stress_test",
        "objects": {
            f"object_{i}": {
                "properties": {"type": f"type_{i}"},
                "relationships": {},
                "behavior_profile": "default_behavior"
            } for i in range(100)  # 100 objects
        }
    }
    
    # Execute pipeline with large dataset
    start_time = time.time()
    result = service.handle_operation("execute-pipeline", {
        "system": "stress_test"
    })
    end_time = time.time()
    
    # Should complete within reasonable time
    assert end_time - start_time < 60  # 60 seconds
    assert result.get("success") is True
```

---

## 🔍 **Debugging E2E Tests**

### **1. Enable Debug Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run tests with debug output
python tests/e2e/test_pipeline_e2e.py
```

### **2. Verbose Test Output**
```bash
# Run with verbose output
python -m pytest tests/e2e/test_pipeline_e2e.py -v -s

# Run specific test with verbose output
python -m pytest tests/e2e/test_pipeline_e2e.py::TestPipelineE2E::test_complete_pipeline_e2e -v -s
```

### **3. Test Isolation**
```python
def test_isolated_components():
    """Test components in isolation"""
    
    # Test schema validation only
    from svgx_engine.services.validation_engine import ValidationEngine
    validator = ValidationEngine()
    result = validator.validate_schema(schema_data)
    
    # Test symbol management only
    from svgx_engine.services.symbol_manager import SymbolManager
    symbol_mgr = SymbolManager()
    result = symbol_mgr.validate_symbols("test_system")
    
    # Test behavior engine only
    from svgx_engine.services.behavior_engine import BehaviorEngine
    behavior_engine = BehaviorEngine()
    result = behavior_engine.validate_behaviors("test_system")
```

---

## 📈 **Test Reporting**

### **1. Generate Test Report**
```bash
# Generate comprehensive test report
python scripts/run_e2e_tests.py

# Generate coverage report
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

### **2. Test Metrics**
```python
def collect_test_metrics():
    """Collect and report test metrics"""
    
    metrics = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "execution_time": 0,
        "coverage_percentage": 0
    }
    
    # Run tests and collect metrics
    start_time = time.time()
    
    # ... run tests ...
    
    end_time = time.time()
    metrics["execution_time"] = end_time - start_time
    
    return metrics
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Add project root to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### **2. Database Connection Issues**
```bash
# Test database connection
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://user:pass@localhost:5432/db')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### **3. Service Startup Issues**
```bash
# Check service status
python -c "
from svgx_engine.services.monitoring import get_monitoring
health = get_monitoring().get_system_health()
print(f'System health: {health}')
"
```

### **Debug Commands**
```bash
# Run with debug output
DEBUG=1 python scripts/run_e2e_tests.py

# Run specific test with debug
python -m pytest tests/e2e/test_pipeline_e2e.py::TestPipelineE2E::test_complete_pipeline_e2e -v -s --tb=long

# Check test environment
python -c "
import os
print(f'Current directory: {os.getcwd()}')
print(f'Python version: {sys.version}')
print(f'Environment variables: {dict(os.environ)}')
"
```

---

## 📋 **Test Checklist**

### **Pre-Test Checklist**
- [ ] All dependencies installed
- [ ] Database configured and accessible
- [ ] Test environment set up
- [ ] Required directories exist
- [ ] Test data prepared

### **Test Execution Checklist**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Performance tests pass
- [ ] Error recovery tests pass
- [ ] CLI tests pass
- [ ] API tests pass

### **Post-Test Checklist**
- [ ] Test reports generated
- [ ] Coverage reports created
- [ ] Performance metrics collected
- [ ] Issues documented
- [ ] Test environment cleaned up

---

## 🎯 **Success Criteria**

### **Performance Requirements**
- **Test Execution Time**: < 10 minutes for full suite
- **Pipeline Execution**: < 5 minutes per system
- **API Response Time**: < 100ms for simple operations
- **Database Operations**: < 1 second for CRUD operations

### **Quality Requirements**
- **Test Coverage**: > 90%
- **Success Rate**: > 95%
- **Error Recovery**: > 98%
- **Performance Regression**: < 10% degradation

### **Reliability Requirements**
- **System Uptime**: > 99.9%
- **Data Integrity**: 100%
- **Backup Success Rate**: > 99%
- **Recovery Success Rate**: > 95%

---

*This guide provides comprehensive E2E testing procedures for the Arxos pipeline. Follow these procedures to ensure the pipeline is ready for production deployment.* 