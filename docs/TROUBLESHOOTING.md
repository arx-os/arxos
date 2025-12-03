# ArxOS Troubleshooting Guide

This guide helps you diagnose and resolve common issues with ArxOS.

---

## Table of Contents

1. [Common Error Messages](#common-error-messages)
2. [Performance Issues](#performance-issues)
3. [Git Integration Problems](#git-integration-problems)
4. [Mobile FFI Issues](#mobile-ffi-issues)
5. [Configuration Problems](#configuration-problems)
6. [IFC Import Issues](#ifc-import-issues)
7. [Build and Compilation Errors](#build-and-compilation-errors)
8. [Diagnostic Commands](#diagnostic-commands)

---

## Common Error Messages

### File Not Found Errors

**Error:** `File not found: building.ifc`

**Solution:**
```bash
# Verify file exists
ls -lh building.ifc

# Use absolute path if needed
arx import /absolute/path/to/building.ifc

# Check current directory
pwd
```

**Error:** `File not found: building.yaml`

**Solution:**
```bash
# Check if building data exists
ls -la *.yaml

# Initialize building if needed
arx init --name "Building Name"
```

---

### Permission Denied Errors

**Error:** `Permission denied: building.yaml`

**Solution:**
```bash
# Check file permissions
ls -l building.yaml

# Fix permissions if needed
chmod 644 building.yaml

# Check directory permissions
ls -ld .
```

---

### Configuration Errors

**Error:** `Configuration Error: Invalid email format`

**Solution:**
```bash
# Check configuration
arx config --show

# Fix email format
arx config --set user.email="user@example.com"

# Validate configuration
arx health --component config
```

**Error:** `Configuration Error: Path does not exist`

**Solution:**
```bash
# Create missing directories
mkdir -p ./buildings ./backups ./cache

# Update configuration
arx config --set paths.default_import_path="./buildings"
```

---

### Validation Errors

**Error:** `Validation Error: Invalid address format`

**Solution:**
```bash
# Check address format
# Address must be: /country/state/city/building/floor/room/fixture

# Example valid address
arx equipment add \
    --room "Conference Room" \
    --name "VAV-301" \
    --equipment-type "HVAC" \
    --at "/usa/ny/brooklyn/office-building/floor-02/mech/vav-301"
```

**Error:** `Validation Error: Equipment type not recognized`

**Solution:**
```bash
# Use valid equipment types
# Valid types: HVAC, Electrical, AV, Plumbing, Network, Other

# Check existing equipment types
arx equipment list --verbose
```

---

### Git Operation Errors

**Error:** `Git Operation Error: Repository not found`

**Solution:**
```bash
# Initialize Git repository
git init

# Or use ArxOS init with Git
arx init --name "Building Name" --git-init
```

**Error:** `Git Operation Error: Commit failed`

**Solution:**
```bash
# Check Git configuration
git config user.name
git config user.email

# Set Git user if needed
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Or use ArxOS config
arx config --set user.name="Your Name"
arx config --set user.email="your.email@example.com"
```

---

## Performance Issues

### Slow IFC Import

**Symptoms:**
- IFC import takes very long
- High CPU usage during import

**Solutions:**
```bash
# Use release build
cargo build --release

# Enable parallel processing
arx config --set performance.max_parallel_threads=8

# Check memory usage
arx health --component persistence --verbose
```

---

### Slow Search/Query Operations

**Symptoms:**
- Search commands are slow
- Query operations timeout

**Solutions:**
```bash
# Enable spatial indexing
arx render --building "Building Name" --spatial-index

# Use specific filters
arx filter --floor 2 --equipment-type "HVAC"

# Limit results
arx search "VAV" --limit 10
```

---

### High Memory Usage

**Symptoms:**
- System runs out of memory
- OOM errors

**Solutions:**
```bash
# Reduce memory limit
arx config --set performance.memory_limit_mb=512

# Enable caching
arx config --set performance.cache_enabled=true

# Clear cache if needed
rm -rf .arxos/cache
```

---

## Git Integration Problems

### Git Not Found

**Error:** `Git not found in PATH`

**Solution:**
```bash
# Check Git installation
which git
git --version

# Install Git if needed
# macOS: brew install git
# Linux: apt-get install git
# Windows: Download from git-scm.com
```

---

### Git Repository Issues

**Error:** `Git repository not initialized`

**Solution:**
```bash
# Initialize Git repository
git init

# Or use ArxOS init
arx init --name "Building Name" --git-init --commit
```

---

### Git Commit Issues

**Error:** `Commit failed: user.name not set`

**Solution:**
```bash
# Set Git user
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Or use ArxOS config
arx config --set user.name="Your Name"
arx config --set user.email="your.email@example.com"
```

---

## Mobile FFI Issues

### iOS Build Errors

**Error:** `XCFramework not found`

**Solution:**
```bash
# Build XCFramework
cargo build --release --target aarch64-apple-ios
cargo build --release --target x86_64-apple-ios

# Create XCFramework
# See docs/mobile/MOBILE_FFI_INTEGRATION.md
```


### FFI Function Errors

**Error:** `FFI error: Invalid data`

**Solution:**
```bash
# Check JSON format
# Ensure all required fields are present

# Verify data structure
# See docs/API_REFERENCE.md for expected formats

# Check error code
# Use arxos_last_error() and arxos_last_error_message()
```

---

## Configuration Problems

### Configuration Not Loading

**Error:** `Configuration file not found`

**Solution:**
```bash
# Check configuration locations
# Priority order:
# 1. Environment variables
# 2. .arxos/config.toml (project)
# 3. ~/.arxos/config.toml (user)
# 4. /etc/arxos/config.toml (global)
# 5. Defaults

# Create configuration file
mkdir -p .arxos
arx config --edit
```

---

### Invalid Configuration Values

**Error:** `Configuration validation failed`

**Solution:**
```bash
# Show current configuration
arx config --show

# Validate configuration
arx health --component config --verbose

# Reset to defaults if needed
arx config --reset
```

---

## IFC Import Issues

### IFC File Not Recognized

**Error:** `Invalid IFC file format`

**Solution:**
```bash
# Check file format
file building.ifc
# Should show: "IFC STEP"

# Verify file is not corrupted
head -20 building.ifc

# Try with different IFC file
arx import --dry-run building.ifc
```

---

### Import Errors

**Error:** `IFC Processing Error: Failed to parse entity`

**Solution:**
```bash
# Use dry run to see errors
arx import --dry-run building.ifc

# Check IFC file version
# ArxOS supports IFC2x3 and IFC4

# Validate IFC file with external tool
# Use IFC validator if available
```

---

### Missing Equipment/Rooms

**Error:** `Equipment not found after import`

**Solution:**
```bash
# Check import log
# Look for warnings about missing entities

# Verify IFC file contains equipment
# Check IFC file structure

# Manually add missing equipment
arx equipment add --room "Room Name" --name "Equipment" --equipment-type "HVAC"
```

---

## Build and Compilation Errors

### Rust Version Issues

**Error:** `Rust version mismatch`

**Solution:**
```bash
# Check Rust version
rustc --version
# Should be: rustc 1.70.0 or later

# Update Rust
rustup update stable

# Set default toolchain
rustup default stable
```

---

### Dependency Issues

**Error:** `Failed to resolve dependencies`

**Solution:**
```bash
# Update dependencies
cargo update

# Clean build cache
cargo clean

# Rebuild
cargo build
```

---

### Compilation Errors

**Error:** `Compilation failed`

**Solution:**
```bash
# Check for errors
cargo build 2>&1 | tee build.log

# Check Rust version
rustc --version

# Clean and rebuild
cargo clean
cargo build --release
```

---

## Diagnostic Commands

### Health Check

Run comprehensive health diagnostics:
```bash
# Full health check
arx health

# Check specific component
arx health --component git
arx health --component config
arx health --component persistence

# Verbose output
arx health --verbose

# Interactive dashboard
arx health --interactive
```

---

### System Information

Collect system information for debugging:
```bash
# Check ArxOS version
arx --version

# Check Rust version
rustc --version

# Check Git version
git --version

# Check system resources
# macOS/Linux: top, htop
# Windows: Task Manager
```

---

### Error Logging

Enable verbose logging:
```bash
# Set log level
export RUST_LOG=debug

# Run command with logging
RUST_LOG=debug arx import building.ifc

# Save logs to file
RUST_LOG=debug arx import building.ifc 2>&1 | tee import.log
```

---

## Quick Reference

### Error Code Mapping

| Error Code | Description | Solution |
|------------|-------------|----------|
| `IfcProcessing` | IFC file processing error | Check IFC file format, use dry-run |
| `Configuration` | Configuration error | Run `arx config --show`, fix invalid values |
| `GitOperation` | Git operation error | Check Git installation, repository status |
| `Validation` | Validation error | Check data format, use `arx validate` |
| `IoError` | I/O error | Check file permissions, disk space |
| `YamlProcessing` | YAML processing error | Validate YAML syntax |
| `SpatialData` | Spatial data error | Check coordinate systems, positions |
| `AddressValidation` | Address validation error | Check address format |
| `CounterOverflow` | Counter overflow | Reset counters in `.arxos/counters.toml` |
| `PathInvalid` | Path validation error | Check path format |

---

## Getting Help

If you're still experiencing issues:

1. **Check Documentation:**
   - [User Guide](docs/core/USER_GUIDE.md)
   - [API Reference](docs/API_REFERENCE.md)
   - [Integration Examples](docs/INTEGRATION_EXAMPLES.md)

2. **Run Diagnostics:**
   ```bash
   arx health --verbose > health-report.txt
   ```

3. **Collect Information:**
   - ArxOS version: `arx --version`
   - Rust version: `rustc --version`
   - Error messages and logs
   - System information

4. **Open an Issue:**
   - Include error messages
   - Include system information
   - Include steps to reproduce
   - Attach relevant logs

---

**Note:** This troubleshooting guide is continuously updated. For the latest information, see the [GitHub repository](https://github.com/arx-os/arxos).

