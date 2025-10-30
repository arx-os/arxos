#!/bin/bash
# Build ArxOS workspace
# This script builds the main crate, tests, and benchmarks

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building ArxOS workspace...${NC}"
echo ""

# Build main package
echo -e "${BLUE}📦 Building arxos package with git features...${NC}"
if cargo build --features git; then
    echo -e "${GREEN}✅ Build successful${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo ""

# Build tests
echo -e "${BLUE}🧪 Building tests...${NC}"
if cargo test --no-run; then
    echo -e "${GREEN}✅ Tests build successful${NC}"
else
    echo -e "${RED}❌ Test build failed${NC}"
    exit 1
fi

echo ""

# Build benchmarks
echo -e "${BLUE}⚡ Building benchmarks...${NC}"
if cargo bench --no-run; then
    echo -e "${GREEN}✅ Benchmarks build successful${NC}"
else
    echo -e "${RED}❌ Benchmark build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All builds completed successfully!${NC}"
echo ""
echo "To run the CLI:"
echo "  cargo run --bin arxos -- --help"
