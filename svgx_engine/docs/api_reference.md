# SVGX Engine API Reference

## Overview

This document provides comprehensive API documentation for the SVGX Engine, including all public interfaces, methods, parameters, and usage examples.

## Core API

### Parser API

#### SVGXParser

The main parser class for converting SVGX content into structured data.

```python
class SVGXParser:
    def __init__(self, config: Optional[ParserConfig] = None)
    def parse(self, content: str) -> SVGXAST
    def parse_file(self, file_path: str) -> SVGXAST
    def validate(self, ast: SVGXAST) -> ValidationResult
    def get_errors(self) -> List[ParseError]
```

**Parameters:**
- `config`: Optional parser configuration
- `content`: SVGX content as string
- `file_path`: Path to SVGX file
- `ast`: Abstract Syntax Tree to validate

**Returns:**
- `SVGXAST`: Parsed abstract syntax tree
- `ValidationResult`: Validation results
- `List[ParseError]`: List of parsing errors

**Example:**
```python
from svgx_engine.parser import SVGXParser

parser = SVGXParser()
ast = parser.parse(svgx_content)
validation = parser.validate(ast)

if validation.is_valid:
    print("SVGX content is valid")
else:
    for error in parser.get_errors():
        print(f"Error: {error.message}")
```

#### ParserConfig

Configuration class for parser behavior.

```python
class ParserConfig:
    def __init__(self,
                 strict_mode: bool = True,
                 enable_validation: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 allowed_namespaces: List[str] = None)
```

**Parameters:**
- `strict_mode`: Enable strict parsing mode
- `enable_validation`: Enable real-time validation
- `max_file_size`: Maximum file size in bytes
- `allowed_namespaces`: List of allowed XML namespaces

### Runtime API

#### SVGXRuntime

The runtime engine for executing SVGX behaviors and simulations.

```python
class SVGXRuntime:
    def __init__(self, config: Optional[RuntimeConfig] = None)
    def simulate(self, ast: SVGXAST) -> SimulationResult
    def get_state(self) -> RuntimeState
    def reset(self) -> None
    def pause(self) -> None
    def resume(self) -> None
    def step(self, steps: int = 1) -> SimulationResult
```

**Parameters:**
- `config`: Optional runtime configuration
- `ast`: Abstract Syntax Tree to simulate
- `steps`: Number of simulation steps

**Returns:**
- `SimulationResult`: Results of simulation
- `RuntimeState`: Current runtime state

**Example:**
```python
from svgx_engine.runtime import SVGXRuntime

runtime = SVGXRuntime()
result = runtime.simulate(ast)

print(f"Simulation completed in {result.duration}ms")
print(f"Final state: {result.final_state}")
```

#### RuntimeConfig

Configuration class for runtime behavior.

```python
class RuntimeConfig:
    def __init__(self,
                 max_iterations: int = 1000,
                 time_step: float = 0.01,
                 enable_physics: bool = True,
                 enable_behaviors: bool = True,
                 debug_mode: bool = False)
```

**Parameters:**
- `max_iterations`: Maximum simulation iterations
- `time_step`: Simulation time step in seconds
- `enable_physics`: Enable physics simulation
- `enable_behaviors`: Enable behavior execution
- `debug_mode`: Enable debug output

### Compiler API

#### SVGXCompiler

The compiler for converting SVGX content to various output formats.

```python
class SVGXCompiler:
    def __init__(self, config: Optional[CompilerConfig] = None)
    def compile(self, ast: SVGXAST, target: str = "svg") -> str
    def compile_file(self, input_path: str, output_path: str, target: str = "svg") -> None
    def get_supported_formats(self) -> List[str]
    def validate_target(self, target: str) -> bool
```

**Parameters:**
- `config`: Optional compiler configuration
- `ast`: Abstract Syntax Tree to compile
- `target`: Target output format
- `input_path`: Input file path
- `output_path`: Output file path

**Returns:**
- `str`: Compiled content
- `List[str]`: List of supported formats
- `bool`: Whether target format is supported

**Example:**
```python
from svgx_engine.compiler import SVGXCompiler

compiler = SVGXCompiler()
svg_output = compiler.compile(ast, target="svg")
ifc_output = compiler.compile(ast, target="ifc")

print(f"Supported formats: {compiler.get_supported_formats()}")
```

#### CompilerConfig

Configuration class for compiler behavior.

```python
class CompilerConfig:
    def __init__(self,
                 optimize_output: bool = True,
                 include_metadata: bool = True,
                 format_indent: bool = True,
                 validate_output: bool = True)
```

**Parameters:**
- `optimize_output`: Enable output optimization
- `include_metadata`: Include SVGX metadata in output
- `format_indent`: Format output with indentation
- `validate_output`: Validate compiled output

## Service APIs

### Security Service

#### SecurityService

Provides authentication, authorization, and security features.

```python
class SecurityService:
    def __init__(self, config: Optional[SecurityConfig] = None)
    def authenticate(self, credentials: Dict[str, str]) -> AuthResult
    def authorize(self, user: User, resource: str, action: str) -> bool
    def validate_input(self, content: str) -> ValidationResult
    def encrypt_data(self, data: str) -> str
    def decrypt_data(self, encrypted_data: str) -> str
    def audit_log(self, event: str, details: Dict[str, Any]) -> None
```

**Parameters:**
- `config`: Optional security configuration
- `credentials`: User credentials
- `user`: User object
- `resource`: Resource to access
- `action`: Action to perform
- `content`: Content to validate
- `data`: Data to encrypt/decrypt
- `event`: Audit event name
- `details`: Audit event details

**Returns:**
- `AuthResult`: Authentication result
- `bool`: Authorization result
- `ValidationResult`: Input validation result
- `str`: Encrypted/decrypted data

**Example:**
```python
from svgx_engine.services.security import SecurityService

security = SecurityService()
auth_result = security.authenticate({"username": "user", "password": "pass"})

if auth_result.success:
    is_authorized = security.authorize(auth_result.user, "file.svgx", "read")
    if is_authorized:
        print("Access granted")
```

### Caching Service

#### AdvancedCachingService

Provides intelligent caching for performance optimization.

```python
class AdvancedCachingService:
    def __init__(self, config: Optional[CacheConfig] = None)
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None
    def delete(self, key: str) -> None
    def clear(self) -> None
    def get_or_compute(self, key: str, compute_func: Callable, ttl: Optional[int] = None) -> Any
    def invalidate_pattern(self, pattern: str) -> None
    def get_stats(self) -> CacheStats
```

**Parameters:**
- `config`: Optional cache configuration
- `key`: Cache key
- `value`: Value to cache
- `ttl`: Time to live in seconds
- `compute_func`: Function to compute value if not cached
- `pattern`: Pattern for invalidation

**Returns:**
- `Any`: Cached value
- `CacheStats`: Cache statistics

**Example:**
```python
from svgx_engine.services.advanced_caching import AdvancedCachingService

cache = AdvancedCachingService()

# Get or compute value
result = cache.get_or_compute("parsed_ast", lambda: parser.parse(content))

# Get cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
```

### Telemetry Service

#### TelemetryService

Collects metrics and performance data.

```python
class TelemetryService:
    def __init__(self, config: Optional[TelemetryConfig] = None)
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None
    def record_event(self, name: str, properties: Optional[Dict[str, Any]] = None) -> None
    def record_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None
    def get_metrics(self, name: str, duration: str = "1h") -> List[MetricPoint]
    def get_events(self, name: str, duration: str = "1h") -> List[Event]
    def export_metrics(self, format: str = "json") -> str
```

**Parameters:**
- `config`: Optional telemetry configuration
- `name`: Metric or event name
- `value`: Metric value
- `tags`: Metric tags
- `properties`: Event properties
- `error`: Exception to record
- `context`: Error context
- `duration`: Time duration for queries
- `format`: Export format

**Returns:**
- `List[MetricPoint]`: List of metric points
- `List[Event]`: List of events
- `str`: Exported metrics

**Example:**
```python
from svgx_engine.services.telemetry import TelemetryService

telemetry = TelemetryService()

# Record metrics
telemetry.record_metric("parse_time", 150.5, {"file_size": "1MB"})
telemetry.record_event("file_processed", {"format": "svgx", "size": 1024})

# Get metrics
metrics = telemetry.get_metrics("parse_time", "1h")
for metric in metrics:
    print(f"{metric.timestamp}: {metric.value}")
```

### Realtime Service

#### RealtimeService

Provides real-time monitoring and alerting.

```python
class RealtimeService:
    def __init__(self, config: Optional[RealtimeConfig] = None)
    def start_monitoring(self) -> None
    def stop_monitoring(self) -> None
    def send_alert(self, alert_type: str, message: str, severity: str = "info") -> None
    def get_status(self) -> SystemStatus
    def subscribe(self, event_type: str, callback: Callable) -> str
    def unsubscribe(self, subscription_id: str) -> None
    def broadcast(self, event_type: str, data: Any) -> None
```

**Parameters:**
- `config`: Optional realtime configuration
- `alert_type`: Type of alert
- `message`: Alert message
- `severity`: Alert severity level
- `event_type`: Type of event
- `callback`: Event callback function
- `subscription_id`: Subscription identifier
- `data`: Event data

**Returns:**
- `SystemStatus`: Current system status
- `str`: Subscription identifier

**Example:**
```python
from svgx_engine.services.realtime import RealtimeService

realtime = RealtimeService()
realtime.start_monitoring()

# Subscribe to events
def on_performance_alert(data):
    print(f"Performance alert: {data}")

subscription_id = realtime.subscribe("performance_alert", on_performance_alert)

# Send alert
realtime.send_alert("performance_degradation", "High memory usage", "warning")
```

## Tool APIs

### Linter API

#### SVGXLinter

Validates SVGX content for correctness and style.

```python
class SVGXLinter:
    def __init__(self, config: Optional[LinterConfig] = None)
    def lint_content(self, content: str) -> LintResult
    def lint_file(self, file_path: str) -> LintResult
    def get_rules(self) -> List[LintRule]
    def set_rules(self, rules: List[LintRule]) -> None
    def format_content(self, content: str) -> str
```

**Parameters:**
- `config`: Optional linter configuration
- `content`: Content to lint
- `file_path`: File to lint
- `rules`: Linting rules

**Returns:**
- `LintResult`: Linting results
- `List[LintRule]`: List of linting rules
- `str`: Formatted content

**Example:**
```python
from svgx_engine.tools.linter import SVGXLinter

linter = SVGXLinter()
result = linter.lint_content(svgx_content)

if result.is_valid:
    print("Content is valid")
else:
    for issue in result.issues:
        print(f"Issue: {issue.message} at line {issue.line}")
```

### Validator API

#### SVGXValidator

Performs comprehensive validation of SVGX content.

```python
class SVGXValidator:
    def __init__(self, config: Optional[ValidatorConfig] = None)
    def validate_content(self, content: str) -> ValidationResult
    def validate_file(self, file_path: str) -> ValidationResult
    def validate_schema(self, content: str) -> SchemaValidationResult
    def validate_business_rules(self, ast: SVGXAST) -> BusinessRuleResult
    def get_validation_rules(self) -> List[ValidationRule]
```

**Parameters:**
- `config`: Optional validator configuration
- `content`: Content to validate
- `file_path`: File to validate
- `ast`: Abstract Syntax Tree to validate

**Returns:**
- `ValidationResult`: Validation results
- `SchemaValidationResult`: Schema validation results
- `BusinessRuleResult`: Business rule validation results
- `List[ValidationRule]`: List of validation rules

**Example:**
```python
from svgx_engine.tools.validator import SVGXValidator

validator = SVGXValidator()
result = validator.validate_content(svgx_content)

if result.is_valid:
    print("Content is valid")
else:
    for error in result.errors:
        print(f"Validation error: {error.message}")
```

## Data Models

### SVGXAST

Abstract Syntax Tree representation of SVGX content.

```python
class SVGXAST:
    def __init__(self, root: SVGXNode)
    def get_root(self) -> SVGXNode
    def find_nodes(self, node_type: str) -> List[SVGXNode]
    def find_by_id(self, node_id: str) -> Optional[SVGXNode]
    def validate(self) -> ValidationResult
    def to_dict(self) -> Dict[str, Any]
    def from_dict(self, data: Dict[str, Any]) -> None
```

### SVGXNode

Individual node in the SVGX AST.

```python
class SVGXNode:
    def __init__(self, node_type: str, attributes: Dict[str, str] = None)
    def get_type(self) -> str
    def get_attributes(self) -> Dict[str, str]
    def get_children(self) -> List[SVGXNode]
    def add_child(self, child: SVGXNode) -> None
    def remove_child(self, child: SVGXNode) -> None
    def find_child(self, node_type: str) -> Optional[SVGXNode]
    def get_attribute(self, name: str) -> Optional[str]
    def set_attribute(self, name: str, value: str) -> None
```

### SimulationResult

Results from runtime simulation.

```python
class SimulationResult:
    def __init__(self, success: bool, duration: float, final_state: Dict[str, Any])
    def is_success(self) -> bool
    def get_duration(self) -> float
    def get_final_state(self) -> Dict[str, Any]
    def get_errors(self) -> List[RuntimeError]
    def get_warnings(self) -> List[str]
    def to_dict(self) -> Dict[str, Any]
```

### ValidationResult

Results from validation operations.

```python
class ValidationResult:
    def __init__(self, is_valid: bool, errors: List[ValidationError] = None)
    def is_valid(self) -> bool
    def get_errors(self) -> List[ValidationError]
    def get_error_count(self) -> int
    def has_errors(self) -> bool
    def to_dict(self) -> Dict[str, Any]
```

## Error Types

### ParseError

Error during parsing operations.

```python
class ParseError:
    def __init__(self, message: str, line: int, column: int, code: str = None)
    def get_message(self) -> str
    def get_line(self) -> int
    def get_column(self) -> int
    def get_code(self) -> Optional[str]
    def to_dict(self) -> Dict[str, Any]
```

### ValidationError

Error during validation operations.

```python
class ValidationError:
    def __init__(self, message: str, severity: str, path: str = None)
    def get_message(self) -> str
    def get_severity(self) -> str
    def get_path(self) -> Optional[str]
    def to_dict(self) -> Dict[str, Any]
```

### RuntimeError

Error during runtime operations.

```python
class RuntimeError:
    def __init__(self, message: str, error_type: str, context: Dict[str, Any] = None)
    def get_message(self) -> str
    def get_error_type(self) -> str
    def get_context(self) -> Dict[str, Any]
    def to_dict(self) -> Dict[str, Any]
```

## Configuration Classes

### ParserConfig

```python
class ParserConfig:
    strict_mode: bool = True
    enable_validation: bool = True
    max_file_size: int = 10 * 1024 * 1024
    allowed_namespaces: List[str] = None
```

### RuntimeConfig

```python
class RuntimeConfig:
    max_iterations: int = 1000
    time_step: float = 0.01
    enable_physics: bool = True
    enable_behaviors: bool = True
    debug_mode: bool = False
```

### CompilerConfig

```python
class CompilerConfig:
    optimize_output: bool = True
    include_metadata: bool = True
    format_indent: bool = True
    validate_output: bool = True
```

### SecurityConfig

```python
class SecurityConfig:
    enable_encryption: bool = True
    enable_audit_logging: bool = True
    max_login_attempts: int = 5
    session_timeout: int = 3600
```

### CacheConfig

```python
class CacheConfig:
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    max_disk_size: int = 1024 * 1024 * 1024   # 1GB
    default_ttl: int = 3600  # 1 hour
    enable_compression: bool = True
```

### TelemetryConfig

```python
class TelemetryConfig:
    enable_metrics: bool = True
    enable_events: bool = True
    enable_error_tracking: bool = True
    flush_interval: int = 60  # seconds
```

### RealtimeConfig

```python
class RealtimeConfig:
    enable_websockets: bool = True
    enable_http_endpoints: bool = True
    max_connections: int = 1000
    heartbeat_interval: int = 30  # seconds
```

## Usage Examples

### Complete Workflow

```python
from svgx_engine.parser import SVGXParser
from svgx_engine.runtime import SVGXRuntime
from svgx_engine.compiler import SVGXCompiler
from svgx_engine.services.security import SecurityService
from svgx_engine.services.advanced_caching import AdvancedCachingService

# Initialize services
security = SecurityService()
cache = AdvancedCachingService()

# Parse SVGX content
parser = SVGXParser()
ast = parser.parse(svgx_content)

# Validate content
if not parser.validate(ast).is_valid:
    print("Invalid SVGX content")
    exit(1)

# Run simulation
runtime = SVGXRuntime()
result = runtime.simulate(ast)

# Compile to different formats
compiler = SVGXCompiler()
svg_output = compiler.compile(ast, target="svg")
ifc_output = compiler.compile(ast, target="ifc")

print(f"Simulation completed: {result.is_success()}")
print(f"SVG output length: {len(svg_output)}")
print(f"IFC output length: {len(ifc_output)}")
```

### Error Handling

```python
from svgx_engine.parser import SVGXParser, ParseError

parser = SVGXParser()

try:
    ast = parser.parse(svgx_content)
except ParseError as e:
    print(f"Parse error at line {e.get_line()}, column {e.get_column()}: {e.get_message()}")
    exit(1)

validation = parser.validate(ast)
if not validation.is_valid:
    for error in parser.get_errors():
        print(f"Validation error: {error.get_message()}")
    exit(1)
```

### Caching Integration

```python
from svgx_engine.services.advanced_caching import AdvancedCachingService

cache = AdvancedCachingService()

def expensive_parsing_operation(content):
    parser = SVGXParser()
    return parser.parse(content)

# Use cached result if available
ast = cache.get_or_compute("parsed_ast", lambda: expensive_parsing_operation(svgx_content))
```

### Real-time Monitoring

```python
from svgx_engine.services.realtime import RealtimeService

realtime = RealtimeService()
realtime.start_monitoring()

def on_performance_alert(data):
    print(f"Performance issue detected: {data}")

realtime.subscribe("performance_alert", on_performance_alert)

# Send alert when performance degrades
if performance_metric > threshold:
    realtime.send_alert("performance_degradation", f"Performance: {performance_metric}", "warning")
```

---

This API reference provides comprehensive documentation for all public interfaces in the SVGX Engine. For implementation details and advanced usage, see the architecture documentation and examples.
