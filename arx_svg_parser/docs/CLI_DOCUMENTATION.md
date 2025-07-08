# Arxos CLI Documentation

## Overview

The Arxos platform provides a suite of command-line tools for managing, validating, simulating, and analyzing SVG-BIM data, rules, telemetry, and more. Each CLI is modular, scriptable, and supports configuration via CLI options, environment variables, and config files.

## Configuration

- **Config file:** YAML or JSON (default: `arxos_cli_config.yaml` in CWD or home)
- **Environment variables:** Each CLI supports `ARXOS_<CLI>_*` env vars (e.g., `ARXOS_SYMBOL_MANAGER_LOG_LEVEL`)
- **Precedence:** CLI args > env vars > config file > default

## CLI Tools

### 1. Symbol Manager CLI (`symbol_manager_cli.py`)
- **Purpose:** Manage SVG symbols (create, update, delete, list, validate, bulk import/export)
- **Usage:**
  ```sh
  python -m arx_svg_parser.cmd.symbol_manager_cli [COMMAND] [OPTIONS]
  python -m arx_svg_parser.cmd.symbol_manager_cli --config arxos_cli_config.yaml list
  ARXOS_SYMBOL_MANAGER_LOG_LEVEL=DEBUG python -m arx_svg_parser.cmd.symbol_manager_cli list
  ```
- **Commands:** create, update, delete, list, get, bulk-import, bulk-export, stats, validate, validate-library
- **Config options:** `symbol_library_path`, `log_level`, `db_path`, ...

### 2. Geometry Resolver CLI (`geometry_resolver_cli.py`)
- **Purpose:** Validate, optimize, and analyze geometric constraints and layouts
- **Usage:**
  ```sh
  python -m arx_svg_parser.cmd.geometry_resolver_cli [COMMAND] [OPTIONS]
  ```
- **Commands:** load, save, validate, detect-conflicts, resolve, optimize, detect-collisions, analyze, export, create-sample, comprehensive

### 3. Validate Building CLI (`validate_building.py`)
- **Purpose:** Validate building design JSON against building codes
- **Usage:**
  ```sh
  python -m arx_svg_parser.cmd.validate_building my_building.json --db custom_regulations.db --report compliance_report.json
  python -m arx_svg_parser.cmd.validate_building my_building.json --config arxos_cli_config.yaml
  ARXOS_VALIDATE_BUILDING_DB=custom.db python -m arx_svg_parser.cmd.validate_building my_building.json
  ```
- **Config options:** `db`, `report`

### 4. Rule Manager CLI (`rule_manager.py`)
- **Purpose:** Manage building code validation rules (load, list, test, enable/disable, validate)
- **Usage:**
  ```sh
  python -m arx_svg_parser.cmd.rule_manager [COMMAND] [OPTIONS]
  python -m arx_svg_parser.cmd.rule_manager --config arxos_cli_config.yaml list
  ARXOS_RULE_MANAGER_LOG_LEVEL=DEBUG python -m arx_svg_parser.cmd.rule_manager list
  ```
- **Commands:** load, list, test, enable, disable, validate
- **Config options:** `log_level`, ...

### 5. Realtime Telemetry CLI (`realtime_telemetry_cli.py`)
- **Purpose:** Start telemetry server, ingest/generate data, monitor alerts, manage alert rules
- **Usage:**
  ```sh
  python -m arx_svg_parser.cmd.realtime_telemetry_cli [COMMAND] [OPTIONS]
  python -m arx_svg_parser.cmd.realtime_telemetry_cli --config arxos_cli_config.yaml start-server
  ARXOS_TELEMETRY_CLI_LOG_LEVEL=DEBUG python -m arx_svg_parser.cmd.realtime_telemetry_cli monitor-alerts
  ```
- **Commands:** start-server, ingest-data, generate-simulated, monitor-alerts, list-alert-rules, add-alert-rule, remove-alert-rule, get-dashboard, get-patterns, ...
- **Config options:** `log_level`, ...

### 6. Failure Detection CLI (`failure_detection_cli.py`)
- **Purpose:** Anomaly detection, trend analysis, pattern recognition, failure prediction, risk assessment
- **Usage:**
  ```sh
  python -m arx_svg_parser.cmd.failure_detection_cli [COMMAND] [OPTIONS]
  python -m arx_svg_parser.cmd.failure_detection_cli --config arxos_cli_config.yaml analyze-trends data.csv
  ARXOS_FAILURE_DETECTION_LOG_LEVEL=DEBUG python -m arx_svg_parser.cmd.failure_detection_cli find-patterns data.csv
  ```
- **Commands:** analyze-trends, find-patterns, assess-risks, generate-sample, ...
- **Config options:** `log_level`, ...

### 7. System Simulator CLI (`system_simulator.py`)
- **Purpose:** Simulate power, HVAC, plumbing, fire suppression, comprehensive system simulation
- **Usage:**
  ```sh
  python -m arx_svg_parser.cmd.system_simulator [COMMAND] [OPTIONS]
  python -m arx_svg_parser.cmd.system_simulator --config arxos_cli_config.yaml power --input power.json
  ARXOS_SYSTEM_SIMULATOR_LOG_LEVEL=DEBUG python -m arx_svg_parser.cmd.system_simulator hvac --input hvac.json
  ```
- **Commands:** power, hvac, plumbing, fire, comprehensive, generate-sample
- **Config options:** `log_level`, ...

## Testing

- All CLIs are tested using `pytest` and `subprocess` (see `arx_svg_parser/tests/`).
- Example test: `pytest arx_svg_parser/tests/test_symbol_manager_cli.py`
- Tests cover: `--help`, main commands, config/env/CLI precedence, and error handling.

## Best Practices
- Use `--help` for command-specific options and examples.
- Prefer YAML config for readability, but JSON is also supported.
- Use environment variables for CI/CD or scripting.
- Always validate your config file before use.

---
For more details, see the docstrings and help output of each CLI, or contact the Arxos development team. 