# Command Line Tools

Command line utilities and tools for the ARXOS platform.

## Purpose

This directory contains Go-based command line tools for various ARXOS operations including database management, testing, and utility functions.

## Structure

```
cmd/
└── arxos/               # Main ARXOS CLI tool
    └── main.go          # CLI entry point
```

## Usage

```bash
# Build CLI tool
cd cmd/arxos
go build -o arxos-cli

# Run CLI tool
./arxos-cli --help
```

## Documentation

For detailed CLI documentation, see [CLI Reference](../../docs/cli/README.md).
