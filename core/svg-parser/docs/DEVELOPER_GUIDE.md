# Arxos SVG-BIM Developer Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Development Setup](#development-setup)
4. [Core Concepts](#core-concepts)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Performance Optimization](#performance-optimization)
8. [Deployment](#deployment)
9. [Contributing](#contributing)

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- Virtual environment (recommended)
- IDE with Python support (VS Code, PyCharm, etc.)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd arx_svg_parser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Quick Start
```python
from arx_svg_parser.services.bim_assembly import BIMAssemblyPipeline

# Create assembly pipeline
pipeline = BIMAssemblyPipeline()

# Assemble BIM from SVG
result = pipeline.assemble_bim({"svg": "<svg>...</svg>"})

print(f"Success: {result.success}")
print(f"Elements: {len(result.elements)}")
```

## Project Structure

```
arx_svg_parser/
├── models/                 # Data models
│   ├── bim.py             # BIM model classes
│   ├── svg.py             # SVG parsing models
│   └── __init__.py
├── services/              # Business logic
│   ├── bim_assembly.py    # BIM assembly pipeline
│   ├── svg_parser.py      # SVG parsing service
│   ├── geometry.py        # Geometry processing
│   └── __init__.py
├── api/                   # API layer
│   ├── api_layer.py       # FastAPI endpoints
│   └── __init__.py
├── tests/                 # Test suite
│   ├── test_bim_assembly.py
│   ├── test_svg_parser.py
│   └── __init__.py
├── docs/                  # Documentation
│   ├── API_DOCUMENTATION.md
│   └── PIPELINE_DIAGRAMS.md
├── examples/              # Usage examples
│   └── usage_examples.py
└── requirements.txt       # Dependencies
```

## Development Setup

### Environment Configuration
Create a `.env` file in the project root:
```env
# Development settings
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///dev.db

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key

# Performance settings
BATCH_SIZE=1000
MAX_WORKERS=4
CACHE_SIZE=1000
```

### IDE Configuration
For VS Code, create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black"
}
```

### Pre-commit Hooks
Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## Core Concepts

### 1. BIM Assembly Pipeline
The core workflow for converting SVG to BIM:

```python
# Pipeline stages
1. SVG Parsing → Extract elements and attributes
2. Type Classification → Identify BIM element types
3. Geometry Processing → Convert to 3D geometry
4. Property Extraction → Extract BIM properties
5. Relationship Building → Create spatial relationships
6. Validation → Ensure model consistency
7. Export → Output in various formats
```

### 2. Data Models
Key data structures:

```python
# BIM Model
class BIMModel:
    elements: List[BIMElement]      # Individual BIM elements
    systems: List[BIMSystem]        # Building systems
    spaces: List[BIMSpace]          # Spatial elements
    relationships: List[BIMRelationship]  # Element relationships

# BIM Element
class BIMElement:
    id: str
    type: str
    geometry: Geometry
    properties: Dict[str, Any]
    metadata: Dict[str, Any]

# Geometry
class Geometry:
    type: GeometryType
    coordinates: List[List[float]]
    properties: Dict[str, Any]
```

### 3. Service Architecture
Layered service architecture:

```
API Layer (FastAPI)
    ↓
Service Layer (Business Logic)
    ↓
Model Layer (Data Structures)
    ↓
Storage Layer (Database/Files)
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... edit files ...

# Run tests
pytest tests/

# Commit changes
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/new-feature
```

### 2. Code Quality
```bash
# Run linting
pylint arx_svg_parser/

# Run formatting
black arx_svg_parser/

# Run type checking
mypy arx_svg_parser/

# Run security checks
bandit -r arx_svg_parser/
```

### 3. Testing Strategy
```python
# Unit tests
def test_bim_element_creation():
    element = BIMElement(id="test", type="wall")
    assert element.id == "test"
    assert element.type == "wall"

# Integration tests
def test_svg_to_bim_pipeline():
    pipeline = BIMAssemblyPipeline()
    result = pipeline.assemble_bim({"svg": test_svg})
    assert result.success
    assert len(result.elements) > 0

# Property-based tests
@given(st.text())
def test_svg_parsing_property(svg_data):
    parser = SVGParser()
    result = parser.parse(svg_data)
    assert isinstance(result, SVGParsingResult)
```

### 4. Performance Testing
```python
# Performance benchmarks
def test_assembly_performance():
    pipeline = BIMAssemblyPipeline()
    start_time = time.time()
    result = pipeline.assemble_bim(large_svg_data)
    processing_time = time.time() - start_time
    assert processing_time < 5.0  # Should complete within 5 seconds
```

## Testing

### Test Structure
```
tests/
├── unit/                 # Unit tests
│   ├── test_models.py
│   └── test_services.py
├── integration/          # Integration tests
│   ├── test_pipeline.py
│   └── test_api.py
├── performance/          # Performance tests
│   └── test_benchmarks.py
└── fixtures/            # Test data
    ├── sample_svgs/
    └── expected_results/
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_bim_assembly.py

# Run with coverage
pytest --cov=arx_svg_parser

# Run performance tests
pytest tests/performance/

# Run integration tests
pytest tests/integration/
```

### Test Data Management
```python
# Fixture example
@pytest.fixture
def sample_svg_data():
    return """
    <svg width="800" height="600">
        <rect x="100" y="100" width="200" height="20" fill="gray"/>
        <circle cx="400" cy="300" r="30" fill="red"/>
    </svg>
    """

@pytest.fixture
def expected_bim_elements():
    return [
        {"type": "wall", "count": 1},
        {"type": "device", "count": 1}
    ]
```

## Performance Optimization

### 1. Profiling
```python
import cProfile
import pstats

def profile_assembly():
    profiler = cProfile.Profile()
    profiler.enable()
    
    pipeline = BIMAssemblyPipeline()
    result = pipeline.assemble_bim(large_svg_data)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

### 2. Memory Optimization
```python
# Use generators for large datasets
def process_large_svg(svg_data):
    for element in parse_svg_elements(svg_data):
        yield process_element(element)

# Implement caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_geometry_calculation(geometry_data):
    return calculate_geometry(geometry_data)
```

### 3. Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

def parallel_process_elements(elements):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_element, elements))
    return results
```

## Deployment

### 1. Production Setup
```bash
# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export DEBUG=False
export DATABASE_URL=postgresql://user:pass@host:port/db

# Run with production server
gunicorn arx_svg_parser.api.api_layer:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 2. Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "arx_svg_parser.api.api_layer:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Environment Configuration
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
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

## Contributing

### 1. Code Standards
- Follow PEP 8 style guide
- Use type hints for all functions
- Write comprehensive docstrings
- Keep functions small and focused

### 2. Commit Messages
```
feat: add new BIM element type
fix: resolve geometry calculation bug
docs: update API documentation
test: add performance benchmarks
refactor: optimize assembly pipeline
```

### 3. Pull Request Process
1. Create feature branch
2. Make changes with tests
3. Ensure all tests pass
4. Update documentation
5. Create pull request
6. Address review comments
7. Merge after approval

### 4. Documentation
- Update docstrings for new functions
- Add examples for new features
- Update API documentation
- Create diagrams for complex workflows

### 5. Testing Requirements
- Unit tests for new functions
- Integration tests for new features
- Performance tests for optimizations
- Property-based tests for data processing

## Troubleshooting

### Common Development Issues

#### 1. Import Errors
**Problem:** Module not found errors
**Solution:** Check PYTHONPATH and virtual environment

#### 2. Test Failures
**Problem:** Tests failing unexpectedly
**Solution:** Check test data and environment setup

#### 3. Performance Issues
**Problem:** Slow processing times
**Solution:** Profile code and optimize bottlenecks

#### 4. Memory Leaks
**Problem:** Increasing memory usage
**Solution:** Check for circular references and large objects

### Debug Tools
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb
pdb.set_trace()

# Memory profiling
import tracemalloc
tracemalloc.start()
# ... code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
```

### Getting Help
- Check existing documentation
- Review test examples
- Search issue tracker
- Contact development team
- Join community discussions

## Best Practices

### 1. Code Organization
- Keep related functionality together
- Use clear, descriptive names
- Minimize dependencies between modules
- Follow single responsibility principle

### 2. Error Handling
- Use custom exception classes
- Provide meaningful error messages
- Implement graceful degradation
- Log errors for debugging

### 3. Performance
- Profile before optimizing
- Use appropriate data structures
- Implement caching where beneficial
- Consider memory usage

### 4. Security
- Validate all input data
- Sanitize SVG content
- Use parameterized queries
- Implement rate limiting

### 5. Testing
- Write tests first (TDD)
- Test edge cases
- Use property-based testing
- Maintain high test coverage

This developer guide provides a comprehensive overview of the Arxos SVG-BIM system development process, from initial setup to production deployment. 