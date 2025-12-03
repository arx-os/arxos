#!/bin/bash
# Build ArxOS
# This script builds the main crate, tests, and benchmarks

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building ArxOS...${NC}"
echo ""

# Check for cargo
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}❌ cargo not found. Please install Rust toolchain.${NC}"
    exit 1
fi

# Build main package
echo -e "${BLUE}📦 Building arx package...${NC}"
if cargo build --release; then
    echo -e "${GREEN}✅ arx built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build arx${NC}"
    exit 1
fi

echo ""

# Build tests
echo -e "${BLUE}🧪 Building tests...${NC}"
if cargo test --no-run; then
    echo -e "${GREEN}✅ Tests build successful${NC}"
else
    echo -e "${YELLOW}⚠️  Test build failed${NC}"
fi

echo ""

# Run IFC regression suite
echo -e "${BLUE}🏗️  Running IFC regression tests...${NC}"
if cargo test --test ifc_golden_tests --test downstream_validation_tests; then
    echo -e "${GREEN}✅ IFC regression tests passed${NC}"
else
    echo -e "${RED}❌ IFC regression tests failed${NC}"
    exit 1
fi

echo ""

echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo "To run the CLI:"
echo "  ./target/release/arx --help"
