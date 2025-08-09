# Test Organization Summary

## Directory Structure

### Unit Tests
Location: `tests/unit/`

**Purpose:** Test individual components and functions in isolation

**Test Files:**
- test_basic.py
- test_application_layer.py
- test_domain_layer.py
- test_infrastructure_layer.py
- test_api_layer.py
- test_clean_architecture.py
- test_use_cases_simple.py
- test_dev_plan_simple.py
- test_bim_behavior_simple.py
- test_enhanced_physics_integration_simple.py

### Integration Tests
Location: `tests/integration/`

**Purpose:** Test interactions between components and services

**Test Files:**
- test_basic_integration.py
- test_service_layer_integration.py
- test_pipeline_integration.py
- test_physics_integration.py
- test_enhanced_physics_integration.py
- test_ai_integration.py
- test_building_service_integration.py
- test_av_system_integration.py
- test_cad_system_comprehensive.py
- test_cmms_integration_comprehensive.py
- test_bim_behavior_comprehensive.py
- test_cad_components_comprehensive.py
- test_plugin_system_comprehensive.py
- test_notification_system_comprehensive.py
- test_performance_monitoring_comprehensive.py
- test_ai_integration_comprehensive.py
- test_cad_system_comprehensive.py
- test_bim_behavior_engine.py
- test_advanced_export_features.py
- test_advanced_thermal_analysis.py
- test_pdf_analysis_integration.py
- test_pdf_to_svgx_transformation.py
- test_phase2_data_persistence.py
- test_phase2_implementation.py
- test_phase3_enhancements.py
- test_phase3_physics_simulation.py
- test_dev_plan_implementation.py
- test_phase1_critical_fixes.py
- test_phase2_enhancements.py
- test_phase3_enhancements.py
- test_elite_parser.py
- test_browser_cad_completion.py
- cad_ai_integration_test.py
- cad_api_integration_test.py
- cad_collaboration_test.py
- cad_system_test.py
- cad_test_report.py

### Performance Tests
Location: `tests/performance/`

**Purpose:** Test system performance, load, and scalability

**Test Files:**
- test_production_performance.py
- test_performance_monitoring_comprehensive.py

### Security Tests
Location: `tests/security/`

**Purpose:** Test security features, vulnerabilities, and hardening

**Test Files:**
- test_security_hardening_comprehensive.py

### Validation Tests
Location: `tests/validation/`

**Purpose:** Test data validation, precision, and compliance

**Test Files:**
- test_precision_math.py
- test_precision_validation_integration.py
- test_precision_validator.py
- test_precision_coordinate.py
- test_precision_input.py
- test_geometric_calculations_precision.py
- test_coordinate_transformations_precision.py
- test_constraint_system_precision.py
- test_import_compliance.py
- test_signal_propagation.py

### E2E Tests
Location: `tests/e2e/`

**Purpose:** Test complete user workflows and system behavior

**Test Files:**
- test_pipeline_comprehensive.py
- test_enhanced_physics_integration.py

### Svgx_Engine Tests
Location: `tests/svgx_engine/`

**Purpose:** Test SVGX engine specific functionality

**Test Files:**

### Health Tests
Location: `tests/health/`

**Purpose:** Test system health checks and monitoring

**Test Files:**

### Smoke Tests
Location: `tests/smoke/`

**Purpose:** Test basic functionality and critical paths

**Test Files:**

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test types
pytest tests/unit/     # Unit tests
pytest tests/integration/  # Integration tests
pytest tests/performance/  # Performance tests
pytest tests/security/     # Security tests
pytest tests/validation/   # Validation tests
pytest tests/e2e/          # End-to-end tests
```
