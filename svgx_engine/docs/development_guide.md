# SVGX Engine Development Guide

## Overview

This guide provides comprehensive instructions for developing, testing, and contributing to the SVGX Engine project. It covers setup, development workflow, testing strategies, and best practices.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Code Quality](#code-quality)
7. [Performance Guidelines](#performance-guidelines)
8. [Security Guidelines](#security-guidelines)
9. [Documentation](#documentation)
10. [Contributing](#contributing)
11. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- **Python**: 3.8 or higher
- **Git**: Latest version
- **IDE**: ArxIDE, PyCharm, or similar
- **OS**: Windows, macOS, or Linux

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/arxos/svgx-engine.git
   cd svgx-engine
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Verify installation**
   ```bash
   python -c "import svgx_engine; print('Installation successful')"
   ```

### Quick Start

```python
from svgx_engine.parser import SVGXParser
from svgx_engine.runtime import SVGXRuntime

# Parse SVGX content
parser = SVGXParser()
ast = parser.parse(svgx_content)

# Run simulation
runtime = SVGXRuntime()
result = runtime.simulate(ast)

print(f"Simulation completed: {result.is_success()}")
```

## Development Environment

### IDE Setup

#### ArxIDE Configuration

1. **Workspace settings** (`.arxide/settings.json`)
   ```json
   {
     "python.defaultInterpreterPath": "./venv/bin/python",
     "python.testing.pytestEnabled": true,
     "python.testing.unittestEnabled": false,
     "python.testing.pytestArgs": ["tests"],
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": false,
     "python.linting.flake8Enabled": true,
     "python.formatting.provider": "black"
   }
   ```

#### PyCharm Configuration

1. **Configure interpreter**
   - File → Settings → Project → Python Interpreter
   - Add existing environment → Select `venv/bin/python`

2. **Configure testing**
   - File → Settings → Tools → Python Integrated Tools
   - Testing: pytest
   - Default test runner: pytest

### Development Tools

#### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
pip install pre-commit
pre-commit install
```

#### Code Formatting

```bash
# Format code with black
black svgx_engine/

# Sort imports with isort
isort svgx_engine/

# Check formatting
black --check svgx_engine/
```

#### Linting

```bash
# Run flake8
flake8 svgx_engine/

# Run mypy for type checking
mypy svgx_engine/
```

## Project Structure

```
svgx_engine/
├── __init__.py              # Package initialization
├── parser/                  # Parsing and validation
│   ├── __init__.py
│   ├── parser.py           # Main parser
│   ├── validator.py        # Content validation
│   └── ast_builder.py      # AST construction
├── runtime/                 # Behavior and physics execution
│   ├── __init__.py
│   ├── runtime.py          # Main runtime
│   ├── behavior_engine.py  # Behavior execution
│   └── physics_engine.py   # Physics simulation
├── compiler/               # Format conversion
│   ├── __init__.py
│   ├── compiler.py        # Main compiler
│   ├── svg_compiler.py    # SVG output
│   ├── ifc_compiler.py    # IFC output
│   └── json_compiler.py   # JSON output
├── services/               # Business logic services
│   ├── __init__.py
│   ├── security.py        # Security service
│   ├── advanced_caching.py # Caching service
│   ├── telemetry.py       # Telemetry service
│   └── realtime.py        # Realtime service
├── tools/                  # Development tools
│   ├── __init__.py
│   ├── linter.py          # SVGX linter
│   ├── validator.py       # Content validator
│   └── web_ide.py         # Web IDE
├── utils/                  # Shared utilities
│   ├── __init__.py
│   ├── constants.py       # Constants
│   ├── errors.py          # Error definitions
│   └── helpers.py         # Helper functions
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_parser.py     # Parser tests
│   ├── test_runtime.py    # Runtime tests
│   ├── test_compiler.py   # Compiler tests
│   └── test_services.py   # Service tests
└── docs/                   # Documentation
    ├── svgx_spec.md       # SVGX specification
    ├── architecture.md     # Architecture documentation
    ├── api_reference.md    # API reference
    └── development_guide.md # This guide
```

## Development Workflow

### Feature Development

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement feature**
   - Follow coding standards
   - Write tests
   - Update documentation

3. **Test your changes**
   ```bash
   pytest tests/
   pytest tests/ -v --cov=svgx_engine --cov-report=html
   ```

4. **Code quality checks**
   ```bash
   black --check svgx_engine/
   flake8 svgx_engine/
   mypy svgx_engine/
   ```

5. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Bug Fixes

1. **Create bug fix branch**
   ```bash
   git checkout -b fix/issue-description
   ```

2. **Write failing test**
   - Reproduce the bug
   - Write test that fails
   - Commit the failing test

3. **Fix the bug**
   - Implement the fix
   - Ensure all tests pass
   - Update documentation if needed

4. **Commit and push**
   ```bash
   git add .
   git commit -m "fix: resolve issue description"
   git push origin fix/issue-description
   ```

### Code Review Process

1. **Self-review checklist**
   - [ ] Code follows style guidelines
   - [ ] Tests are written and passing
   - [ ] Documentation is updated
   - [ ] No security vulnerabilities
   - [ ] Performance impact considered

2. **Review request**
   - Create pull request
   - Add detailed description
   - Link related issues
   - Request reviewers

3. **Address feedback**
   - Respond to comments
   - Make requested changes
   - Update PR description

## Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── conftest.py            # Pytest configuration
├── test_parser.py         # Parser tests
├── test_runtime.py        # Runtime tests
├── test_compiler.py       # Compiler tests
├── test_services.py       # Service tests
├── test_tools.py          # Tool tests
├── test_utils.py          # Utility tests
├── integration/           # Integration tests
│   ├── test_workflow.py
│   └── test_performance.py
└── fixtures/              # Test fixtures
    ├── sample.svgx
    └── expected_outputs/
```

### Test Categories

#### Unit Tests

Test individual components in isolation:

```python
import pytest
from svgx_engine.parser import SVGXParser

class TestSVGXParser:
    def test_parse_valid_svgx(self):
        parser = SVGXParser()
        content = '<svg xmlns:arx="http://arxos.io/svgx"><rect arx:object="test"/></svg>'
        ast = parser.parse(content)
        assert ast is not None
        assert len(ast.get_root().get_children()) > 0

    def test_parse_invalid_svgx(self):
        parser = SVGXParser()
        content = '<invalid>content</invalid>'
        with pytest.raises(ParseError):
            parser.parse(content)
```

#### Integration Tests

Test component interactions:

```python
import pytest
from svgx_engine.parser import SVGXParser
from svgx_engine.runtime import SVGXRuntime

class TestWorkflow:
    def test_parse_and_simulate(self):
        parser = SVGXParser()
        runtime = SVGXRuntime()
        
        content = self.load_test_svgx()
        ast = parser.parse(content)
        result = runtime.simulate(ast)
        
        assert result.is_success()
        assert result.get_duration() > 0
```

#### Performance Tests

Test performance characteristics:

```python
import pytest
import time
from svgx_engine.parser import SVGXParser

class TestPerformance:
    def test_parse_performance(self):
        parser = SVGXParser()
        content = self.load_large_svgx()
        
        start_time = time.time()
        ast = parser.parse(content)
        duration = time.time() - start_time
        
        assert duration < 1.0  # Should parse in under 1 second
        assert ast is not None
```

### Test Best Practices

1. **Test naming**
   - Use descriptive test names
   - Follow pattern: `test_<method>_<scenario>_<expected_result>`

2. **Test isolation**
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Avoid shared state

3. **Test coverage**
   - Aim for 95%+ coverage
   - Test edge cases and error conditions
   - Test both success and failure paths

4. **Test data**
   - Use realistic test data
   - Include edge cases
   - Keep test data minimal but complete

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=svgx_engine --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::TestSVGXParser::test_parse_valid_svgx

# Run with verbose output
pytest -v

# Run with parallel execution
pytest -n auto
```

## Code Quality

### Style Guidelines

#### Python Style

Follow PEP 8 with these additions:

```python
# Good
def parse_svgx_content(content: str, config: Optional[ParserConfig] = None) -> SVGXAST:
    """Parse SVGX content into an AST.
    
    Args:
        content: SVGX content as string
        config: Optional parser configuration
        
    Returns:
        Parsed abstract syntax tree
        
    Raises:
        ParseError: If content cannot be parsed
    """
    if not content:
        raise ValueError("Content cannot be empty")
    
    parser = SVGXParser(config or ParserConfig())
    return parser.parse(content)

# Bad
def parse_svgx_content(content,config=None):
    if not content:raise ValueError("Content cannot be empty")
    parser=SVGXParser(config or ParserConfig())
    return parser.parse(content)
```

#### Naming Conventions

- **Classes**: PascalCase (`SVGXParser`)
- **Functions/Methods**: snake_case (`parse_content`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_FILE_SIZE`)
- **Variables**: snake_case (`file_path`)
- **Private methods**: Leading underscore (`_validate_content`)

#### Documentation

```python
class SVGXParser:
    """Parser for SVGX content.
    
    This class provides functionality to parse SVGX content into a structured
    Abstract Syntax Tree (AST) for further processing.
    
    Attributes:
        config: Parser configuration
        errors: List of parsing errors
    """
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """Initialize the parser.
        
        Args:
            config: Optional parser configuration
        """
        self.config = config or ParserConfig()
        self.errors = []
    
    def parse(self, content: str) -> SVGXAST:
        """Parse SVGX content into an AST.
        
        Args:
            content: SVGX content as string
            
        Returns:
            Parsed abstract syntax tree
            
        Raises:
            ParseError: If content cannot be parsed
            ValidationError: If content fails validation
        """
        # Implementation here
```

### Error Handling

```python
class SVGXError(Exception):
    """Base exception for SVGX Engine errors."""
    
    def __init__(self, message: str, code: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

class ParseError(SVGXError):
    """Exception raised during parsing operations."""
    
    def __init__(self, message: str, line: int, column: int, code: str = None):
        super().__init__(message, code)
        self.line = line
        self.column = column

# Usage
def parse_content(content: str) -> SVGXAST:
    try:
        return parser.parse(content)
    except ParseError as e:
        logger.error(f"Parse error at line {e.line}: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise SVGXError("Unexpected parsing error", context={"original_error": str(e)})
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

class SVGXParser:
    def parse(self, content: str) -> SVGXAST:
        logger.debug(f"Parsing content of length {len(content)}")
        
        try:
            ast = self._parse_content(content)
            logger.info("Content parsed successfully")
            return ast
        except Exception as e:
            logger.error(f"Failed to parse content: {e}")
            raise
```

## Performance Guidelines

### Optimization Strategies

1. **Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def parse_svgx_content(content: str) -> SVGXAST:
       # Expensive parsing operation
       pass
   ```

2. **Lazy Loading**
   ```python
   class SVGXParser:
       def __init__(self):
           self._validator = None
       
       @property
       def validator(self):
           if self._validator is None:
               self._validator = SVGXValidator()
           return self._validator
   ```

3. **Batch Processing**
   ```python
   def process_multiple_files(file_paths: List[str]) -> List[SVGXAST]:
       results = []
       for file_path in file_paths:
           with open(file_path, 'r') as f:
               content = f.read()
               ast = parser.parse(content)
               results.append(ast)
       return results
   ```

### Memory Management

```python
class MemoryManager:
    def __init__(self, max_memory: int = 100 * 1024 * 1024):  # 100MB
        self.max_memory = max_memory
        self.current_usage = 0
    
    def check_memory(self, estimated_size: int) -> bool:
        if self.current_usage + estimated_size > self.max_memory:
            self._cleanup()
            return False
        return True
    
    def _cleanup(self):
        # Implement cleanup logic
        pass
```

### Performance Testing

```python
import time
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start_time
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result, duration
```

## Security Guidelines

### Input Validation

```python
import re
from typing import Optional

class InputValidator:
    @staticmethod
    def validate_svgx_content(content: str) -> bool:
        """Validate SVGX content for security."""
        if not content or len(content) > 10 * 1024 * 1024:  # 10MB limit
            return False
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'data:text/html',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
```

### Authentication and Authorization

```python
class SecurityService:
    def __init__(self):
        self.sessions = {}
    
    def authenticate(self, credentials: Dict[str, str]) -> AuthResult:
        # Implement secure authentication
        pass
    
    def authorize(self, user: User, resource: str, action: str) -> bool:
        # Implement role-based access control
        pass
    
    def validate_session(self, session_id: str) -> bool:
        # Validate session token
        pass
```

### Data Protection

```python
import hashlib
import secrets

class DataProtector:
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data."""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"
    
    @staticmethod
    def encrypt_data(data: str, key: bytes) -> bytes:
        """Encrypt sensitive data."""
        # Implement encryption
        pass
```

## Documentation

### Code Documentation

1. **Docstrings**
   - Use Google style docstrings
   - Include type hints
   - Document exceptions

2. **Comments**
   - Explain complex logic
   - Document workarounds
   - Keep comments up to date

3. **README files**
   - Update README for new features
   - Include usage examples
   - Document breaking changes

### API Documentation

```python
def parse_svgx_content(content: str, config: Optional[ParserConfig] = None) -> SVGXAST:
    """Parse SVGX content into an Abstract Syntax Tree.
    
    This function takes SVGX content as a string and parses it into a structured
    AST that can be used for further processing, simulation, or compilation.
    
    Args:
        content: The SVGX content to parse. Must be a valid SVGX string.
        config: Optional parser configuration. If not provided, default settings
               will be used.
    
    Returns:
        An SVGXAST object representing the parsed content.
    
    Raises:
        ParseError: If the content cannot be parsed due to syntax errors.
        ValidationError: If the content fails validation checks.
        ValueError: If the content is empty or None.
    
    Example:
        >>> content = '<svg xmlns:arx="http://arxos.io/svgx"><rect arx:object="test"/></svg>'
        >>> ast = parse_svgx_content(content)
        >>> print(ast.get_root().get_type())
        'svg'
    
    Note:
        The parser is thread-safe and can be used concurrently.
    """
    # Implementation here
```

## Contributing

### Contribution Guidelines

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Write tests**
5. **Update documentation**
6. **Submit a pull request**

### Pull Request Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass

## Documentation
- [ ] Code documentation updated
- [ ] API documentation updated
- [ ] README updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No security vulnerabilities
- [ ] Performance impact considered
```

### Code Review Checklist

- [ ] Code is readable and well-documented
- [ ] Tests are comprehensive and passing
- [ ] No security vulnerabilities introduced
- [ ] Performance impact is acceptable
- [ ] Documentation is updated
- [ ] Error handling is appropriate
- [ ] Logging is adequate

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Issue: Module not found
ImportError: No module named 'svgx_engine'

# Solution: Install in development mode
pip install -e .
```

#### Test Failures

```bash
# Issue: Tests failing
pytest tests/ -v

# Solution: Check test output and fix issues
# Common causes:
# - Missing dependencies
# - Incorrect test data
# - Environment issues
```

#### Performance Issues

```bash
# Issue: Slow performance
# Solution: Profile the code
python -m cProfile -o profile.stats your_script.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

#### Memory Issues

```bash
# Issue: Memory leaks
# Solution: Use memory profiler
pip install memory_profiler
python -m memory_profiler your_script.py
```

### Debugging

#### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()
```

#### Error Tracking

```python
import traceback

try:
    # Your code here
    pass
except Exception as e:
    logger.error(f"Error: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise
```

### Getting Help

1. **Check documentation**
   - API reference
   - Architecture documentation
   - This development guide

2. **Search issues**
   - GitHub issues
   - Stack Overflow

3. **Create issue**
   - Provide minimal reproduction
   - Include error messages
   - Describe expected behavior

4. **Ask community**
   - GitHub discussions
   - Discord/Slack channels

---

This development guide provides comprehensive instructions for contributing to the SVGX Engine project. Follow these guidelines to ensure high-quality, maintainable code that meets the project's standards. 