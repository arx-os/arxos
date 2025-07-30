# Arxos Pipeline Definition

## Overview
This document defines the canonical pipeline for adding new systems and objects to the Arxos ecosystem, ensuring consistency, maintainability, and enterprise-grade quality. The pipeline uses a **hybrid approach** with Go backend orchestration and Python SVGX integration.

## Architecture: Hybrid Go + Python Approach

### **Go Backend (Primary Orchestration)**
- **Pipeline Orchestration**: Go handles the heavy lifting (file operations, validation, CLI)
- **Performance**: Fast execution for schema validation, registry updates, and CLI operations
- **Enterprise Ready**: Single binary deployment, better performance, consistent with existing Go backend
- **CLI Integration**: Leverages existing `arx` CLI patterns and infrastructure

### **Python Integration (SVGX-Specific Operations)**
- **SVGX Engine**: Direct access to Python-based SVGX engine for symbol validation and behavior profiles
- **Rapid Development**: Faster prototyping for SVGX-specific operations
- **Existing Codebase**: Leverages existing Python tools and libraries for SVGX operations
- **Bridge Service**: Python services called by Go for SVGX-specific operations

## Pipeline Definition

```yaml
arxos_pipeline:
  entry_point: "models/ and schemas/ directories (BIM object model)"
  orchestrator: "Go backend (arx-backend/internal/pipeline/)"
  svgx_integration: "Python bridge service (svgx_engine/services/pipeline_integration.py)"
  
  steps:
    - step: "Define Schema"
      applies_to: ["new_system", "new_object"]
      orchestrator: "Go"
      description: >
        Add or extend the BIM object schema. This includes system name, object types,
        property definitions, and upstream/downstream relationships.
      files:
        - schemas/<system>.json
        - models/<system>.py
      actions:
        - Follow naming conventions like "electrical.light_fixture.surface_mount"
        - Include behavior_profile stubs or references
        - Use existing systems (electrical, FA) as structure guides
        - Define property sets and relationships
        - Add validation rules and constraints
      validation:
        - arx pipeline validate-schema --system <system>
        - arx pipeline check-naming --system <system>
        - arx pipeline verify-relationships --system <system>

    - step: "Add Symbol(s)"
      applies_to: ["new_system", "new_object"]
      orchestrator: "Go + Python Bridge"
      description: >
        Create or update the SVGX symbol(s) associated with the system/object.
        Add embedded metadata in the SVGX (system, object_type, behavior_profile).
      files:
        - arx-symbol-library/<system>/<symbol_name>.svgx
        - arx-symbol-library/<system>/metadata/<symbol_name>.json
      actions:
        - Use template symbols (e.g., E_Panel_001) as a base
        - Validate with SVGX linter (Python bridge)
        - Register symbol in symbol_index.json (Go)
        - Add symbol metadata (properties, connections, behavior_profile)
        - Create symbol variants if needed (different sizes, types)
      validation:
        - arx pipeline validate-symbol --symbol <symbol_name>
        - arx pipeline check-metadata --symbol <symbol_name>
        - arx pipeline verify-behavior-reference --symbol <symbol_name>

    - step: "Implement Behavior Profiles"
      applies_to: ["new_system", "new_object"]
      orchestrator: "Python Bridge"
      description: >
        Add programmable behavior for the object(s) in the system. This includes physics,
        logic simulation, relationships, constraints, and control loops.
      files:
        - svgx_engine/services/behavior_profiles.py
        - svgx_engine/behavior/<system>.py (for complex systems)
        - svgx_engine/tests/test_<system>_behavior.py
      actions:
        - Follow I/O variable → formula → safe thresholds structure
        - Use pattern seen in FA_Detector or Panel behavior_profiles
        - Include logic hooks for simulation engine
        - Add state machine definitions
        - Implement constraint checking
        - Add performance monitoring hooks
      validation:
        - arx pipeline validate-behavior --system <system>
        - arx pipeline test-simulation --system <system>
        - arx pipeline check-performance --system <system>

    - step: "Update Registry & Index"
      applies_to: ["new_system", "new_object"]
      orchestrator: "Go"
      description: >
        Make the new system/object discoverable to the engine, UI, and CLI.
        Update any manifest/index/registry files used by the platform.
      files:
        - symbol_index.json
        - systems.json
        - arx_cli/commands/system_registry.py
        - svgx_engine/registry/<system>_registry.py
      actions:
        - Ensure autocomplete and CLI support for new entries
        - Sync with front-end manifest (if applicable)
        - Update system discovery mechanisms
        - Add to behavior profile registry
        - Update documentation index
      validation:
        - arx pipeline validate-registry --system <system>
        - arx pipeline test-discovery --system <system>
        - arx pipeline verify-ui-integration --system <system>

    - step: "Documentation & Test Coverage"
      applies_to: ["new_system", "new_object"]
      orchestrator: "Go + Python Bridge"
      description: >
        Add or update relevant documentation, test cases, and example building repos.
      files:
        - docs/systems/<system>.md
        - tests/test_<system>.py
        - tests/test_<system>_integration.py
        - example_buildings/<building>/symbols/
        - docs/behavior_profiles/<system>.md
      actions:
        - Include YAML/BIM config examples
        - Validate symbols with integration test suite
        - Update changelog and dev playbook
        - Add usage examples and tutorials
        - Create troubleshooting guides
      validation:
        - arx pipeline validate-coverage --system <system>
        - arx pipeline check-documentation --system <system>
        - arx pipeline validate-examples --system <system>

    - step: "Enterprise Compliance Validation"
      applies_to: ["new_system", "new_object"]
      orchestrator: "Go + Python Bridge"
      description: >
        Ensure the new system/object meets enterprise-grade standards including
        security, performance, and compliance requirements.
      files:
        - tests/test_<system>_compliance.py
        - tests/test_<system>_security.py
        - tests/test_<system>_performance.py
      actions:
        - Run security scanning on new code
        - Validate performance impact
        - Check compliance with enterprise standards
        - Verify error handling and resilience
        - Test integration with existing systems
      validation:
        - arx pipeline validate-compliance --system <system>
        - arx pipeline security-scan --system <system>
        - arx pipeline performance-benchmark --system <system>

  constraints:
    - "No system or object should bypass the canonical BIM model/schema."
    - "No SVGX should exist without a matching object_type and behavior_profile."
    - "All logic must be testable via simulated scenarios."
    - "All new systems must pass enterprise compliance validation."
    - "All symbols must be discoverable via CLI and UI."
    - "All behavior profiles must have comprehensive test coverage."
    - "Go orchestrates the pipeline, Python handles SVGX-specific operations."

  enforcement_tools:
    - arx pipeline validate-schema --system <name>
    - arx pipeline validate-symbol --symbol <name>
    - arx pipeline validate-behavior --system <name>
    - arx pipeline validate-registry --system <name>
    - arx pipeline validate-compliance --system <name>
    - arx pipeline execute --system <name> --type <operation>

  quality_gates:
    - "Schema validation passes"
    - "Symbol validation passes"
    - "Behavior profile validation passes"
    - "Registry updates complete"
    - "Test coverage > 90%"
    - "Enterprise compliance passes"
    - "Performance impact < 5%"
    - "Documentation complete"
    - "Go-Python bridge communication successful"

  rollback_procedures:
    - "Remove from registry if validation fails"
    - "Revert schema changes if symbol validation fails"
    - "Disable behavior profile if performance impact too high"
    - "Remove from CLI/UI if integration fails"
    - "Rollback Go registry changes if Python bridge fails"
```

## Usage Examples

### Adding a New System (e.g., Audiovisual)

```bash
# 1. Define Schema
python scripts/arx_pipeline.py --step define-schema --system audiovisual

# 2. Add Symbols
python scripts/arx_pipeline.py --step add-symbols --system audiovisual --symbols display,projector,audio

# 3. Implement Behavior Profiles
python scripts/arx_pipeline.py --step implement-behavior --system audiovisual

# 4. Update Registry
python scripts/arx_pipeline.py --step update-registry --system audiovisual

# 5. Documentation & Tests
python scripts/arx_pipeline.py --step documentation --system audiovisual

# 6. Enterprise Compliance
python scripts/arx_pipeline.py --step compliance --system audiovisual
```

### Adding a New Object to Existing System

```bash
# Add new object to electrical system
python scripts/arx_pipeline.py --step add-object --system electrical --object smart_switch

# Validate the addition
python scripts/arx_pipeline.py --validate --system electrical --object smart_switch
```

## Integration with CI/CD

The pipeline integrates with the existing enterprise compliance workflow:

```yaml
# .github/workflows/arxos-pipeline.yml
name: Arxos Pipeline Validation

on:
  pull_request:
    paths:
      - 'models/**'
      - 'schemas/**'
      - 'arx-symbol-library/**'
      - 'svgx_engine/behavior/**'

jobs:
  pipeline-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate Pipeline Steps
        run: |
          python scripts/arx_pipeline.py --validate-all
      - name: Run Enterprise Compliance
        run: |
          python scripts/arx_pipeline.py --compliance-check
```

## Benefits of This Pipeline

1. **Consistency**: All systems follow the same structure and patterns
2. **Quality**: Built-in validation and compliance checking
3. **Maintainability**: Clear separation of concerns and rollback procedures
4. **Discoverability**: Automatic registration and indexing
5. **Testability**: Comprehensive test coverage requirements
6. **Enterprise-Grade**: Integration with security and compliance workflows

This pipeline ensures that every new system or object in Arxos is properly integrated, tested, and documented while maintaining the platform's architectural integrity. 