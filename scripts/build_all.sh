#!/bin/bash

# Arxos Complete Build Script
# Builds all components for RF-only mesh network

set -e  # Exit on error

echo "╔════════════════════════════════════════╗"
echo "║     Arxos RF Mesh Build System         ║"
echo "║         100% Air-Gapped                ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 not found. Please install it first.${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ $1 found${NC}"
    fi
}

echo "Checking prerequisites..."
check_command rustc
check_command cargo
check_command sqlite3

# Build core library
echo ""
echo -e "${YELLOW}Building Core Library...${NC}"
cd src/core
cargo build --release
cargo test
echo -e "${GREEN}✓ Core library built successfully${NC}"

# Build terminal client
echo ""
echo -e "${YELLOW}Building Terminal Client...${NC}"
cd ../terminal
cargo build --release
echo -e "${GREEN}✓ Terminal client built successfully${NC}"

# Build ESP32 firmware
echo ""
echo -e "${YELLOW}Building ESP32 Firmware...${NC}"
cd ../../firmware/esp32

# Check for ESP32 targets
if rustup target list --installed | grep -q "riscv32imc-unknown-none-elf"; then
    cargo build --release --target riscv32imc-unknown-none-elf
    echo -e "${GREEN}✓ ESP32 firmware built successfully${NC}"
else
    echo -e "${YELLOW}⚠ ESP32 target not installed. Run:${NC}"
    echo "  rustup target add riscv32imc-unknown-none-elf"
    echo "  cargo install espflash"
fi

# Initialize database
echo ""
echo -e "${YELLOW}Initializing Database...${NC}"
cd ../..
if [ ! -f "arxos.db" ]; then
    sqlite3 arxos.db < migrations/001_initial_schema.sql
    sqlite3 arxos.db < migrations/002_spatial_functions.sql
    echo -e "${GREEN}✓ Database initialized${NC}"
else
    echo -e "${GREEN}✓ Database already exists${NC}"
fi

# Generate SSH host key
echo ""
echo -e "${YELLOW}Generating SSH Host Key...${NC}"
if [ ! -f "/tmp/arxos_host_key" ]; then
    ssh-keygen -t ed25519 -f /tmp/arxos_host_key -N "" -C "arxos@mesh"
    echo -e "${GREEN}✓ SSH host key generated${NC}"
else
    echo -e "${GREEN}✓ SSH host key already exists${NC}"
fi

# Build summary
echo ""
echo "╔════════════════════════════════════════╗"
echo "║          Build Complete!               ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Artifacts created:"
echo "  • Core library: target/release/libarxos_core.rlib"
echo "  • Terminal: target/release/arxos"
echo "  • Database: arxos.db"
echo ""
echo "Next steps:"
echo "  1. Flash firmware to ESP32:"
echo "     espflash /dev/ttyUSB0 firmware/esp32/target/riscv32imc-unknown-none-elf/release/arxos-firmware"
echo ""
echo "  2. Run terminal client:"
echo "     ./target/release/arxos --simulate"
echo ""
echo "  3. Connect to mesh node:"
echo "     ssh arxos@mesh-node.local"
echo ""
echo -e "${GREEN}Ready for deployment!${NC}"