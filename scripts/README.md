# Arxos Scripts

Centralized scripts for the Arxos platform, organized by purpose and responsibility.

## Directory Structure

```
scripts/
├── ops/              # Operational scripts for running the platform
├── processing/       # Data processing and analysis scripts
├── testing/          # Test automation and validation
├── deployment/       # Deployment and infrastructure scripts
└── utils/            # Utility scripts and helpers
```

## Quick Start

### Starting Services

```bash
# Start all services
./scripts/ops/start.sh

# Stop all services
./scripts/ops/clean.sh

# Manage access control
./scripts/ops/manage-access.sh
```

### Running Tests

```bash
# Run all tests
./scripts/testing/test.sh

# Mobile-specific tests
./scripts/testing/mobile-test.sh
```

## Script Categories

### Operations (`ops/`)

Daily operational scripts for managing the Arxos platform:

| Script | Purpose | Usage |
|--------|---------|-------|
| `start.sh` | Start all Arxos services | `./start.sh [--dev\|--prod]` |
| `clean.sh` | Stop services and clean up | `./clean.sh` |
| `manage-access.sh` | Configure access control | `./manage-access.sh` |

**Best Practices:**
- Always use `start.sh` to launch services (ensures proper initialization)
- Run `clean.sh` before switching environments
- Check logs in `/logs` if services fail to start

### Processing (`processing/`)

Data processing and analysis scripts used by the backend:

#### Python Scripts (`processing/python/`)
- `extract_floor_plan.py` - Extract architectural elements from PDFs
- `cv_extraction.py` - Computer vision processing for images
- `analyze_floorplan.py` - Spatial analysis of floor plans
- `process_real_floorplan.py` - Process real-world floor plan data
- `real_extraction.py` - Extract real geometry from plans
- `extract_simple.py` - Simplified extraction for testing

#### Shell Scripts (`processing/shell/`)
- `process_floor_plan.sh` - Orchestrate floor plan processing pipeline
- `extract_real_geometry.sh` - Extract geometry from CAD files
- `test_arxobject_pipeline.sh` - Test ArxObject creation pipeline
- `test_sqlite_windows.bat` - Windows SQLite testing

#### JavaScript (`processing/js/`)
- `capture_ui.js` - Capture UI state for debugging
- `capture_current.js` - Capture current view state

**Usage Examples:**

```bash
# Process a PDF floor plan
python scripts/processing/python/extract_floor_plan.py input.pdf

# Run the full processing pipeline
./scripts/processing/shell/process_floor_plan.sh input.pdf output.json

# Test ArxObject pipeline
./scripts/processing/shell/test_arxobject_pipeline.sh
```

### Testing (`testing/`)

Automated testing scripts organized by test type:

```
testing/
├── test.sh           # Main test runner
├── mobile-test.sh    # Mobile-specific tests
├── unit/            # Unit test scripts
├── integration/     # Integration test scripts
└── performance/     # Performance test scripts
```

**Running Tests:**

```bash
# Run all tests
./scripts/testing/test.sh

# Run specific test suites
./scripts/testing/test.sh --unit
./scripts/testing/test.sh --integration
./scripts/testing/test.sh --performance

# Mobile testing
./scripts/testing/mobile-test.sh --device=iphone
```

### Deployment (`deployment/`)

Scripts for deploying and configuring the platform:

| Script | Purpose | Environment |
|--------|---------|-------------|
| `https-mobile.sh` | Configure HTTPS for mobile | Development |

**Deployment Workflows:**

```bash
# Set up HTTPS for mobile development
./scripts/deployment/https-mobile.sh

# Deploy to staging (future)
./scripts/deployment/deploy-staging.sh

# Deploy to production (future)
./scripts/deployment/deploy-production.sh
```

### Utilities (`utils/`)

Helper scripts for common tasks:

```bash
# Future utility scripts
./scripts/utils/backup.sh          # Backup data
./scripts/utils/restore.sh         # Restore from backup
./scripts/utils/migrate.sh         # Run migrations
./scripts/utils/seed.sh           # Seed test data
```

## Environment Variables

Scripts respect these environment variables:

```bash
# Core settings
ARXOS_ENV=development|staging|production
ARXOS_DEBUG=true|false

# Service URLs
BACKEND_URL=http://localhost:8080
AI_SERVICE_URL=http://localhost:8000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=arxos
```

## Script Standards

All scripts follow these standards:

### 1. **Shebang and Set Options**
```bash
#!/bin/bash
set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure
```

### 2. **Help Documentation**
```bash
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]
Description of what the script does

Options:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -d, --debug     Enable debug mode
EOF
}
```

### 3. **Color Output**
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}✓${NC} Success message"
echo -e "${RED}✗${NC} Error message"
echo -e "${YELLOW}⚠${NC} Warning message"
echo -e "${BLUE}ℹ${NC} Info message"
```

### 4. **Error Handling**
```bash
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit "${2:-1}"
}

# Usage
command || error_exit "Command failed" 1
```

### 5. **Logging**
```bash
LOG_FILE="${LOG_FILE:-/tmp/arxos-$(date +%Y%m%d).log}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}
```

## Python Script Standards

### 1. **Module Documentation**
```python
#!/usr/bin/env python3
"""
Script purpose and description.

Usage:
    python script.py [options] <input> <output>
    
Requirements:
    - Python 3.9+
    - opencv-python
    - numpy
"""
```

### 2. **Main Guard**
```python
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Script description')
    args = parser.parse_args()
    # Implementation

if __name__ == "__main__":
    main()
```

### 3. **Error Handling**
```python
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    result = process_data()
except Exception as e:
    logger.error(f"Processing failed: {e}")
    sys.exit(1)
```

## Dependencies

### System Requirements
- Bash 4.0+
- Python 3.9+
- Node.js 18+ (for JS scripts)
- Git

### Python Dependencies
```bash
# Install Python dependencies
pip install -r scripts/requirements.txt
```

### Common Issues

#### Permission Denied
```bash
# Make scripts executable
chmod +x scripts/**/*.sh
```

#### Service Won't Start
```bash
# Check for existing processes
./scripts/ops/clean.sh

# Check logs
tail -f logs/arxos.log
```

#### Python Module Not Found
```bash
# Install dependencies
pip install -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Contributing

When adding new scripts:

1. **Choose the right directory** based on script purpose
2. **Follow naming conventions**:
   - Lowercase with hyphens: `process-data.sh`
   - Descriptive names: `extract-floor-plan.py` not `extract.py`
3. **Add documentation**:
   - Include help/usage in the script
   - Update this README
4. **Make executable**: `chmod +x script.sh`
5. **Test thoroughly** before committing

## Security

- **Never commit credentials** - Use environment variables
- **Validate inputs** - Sanitize user-provided data
- **Use absolute paths** when dealing with sensitive operations
- **Set restrictive permissions** on sensitive scripts

## Support

For script-related issues:
- Check logs in `/tmp/arxos-*.log`
- Run with `--debug` flag for verbose output
- See troubleshooting section above

## License

Proprietary - Arxos Inc.