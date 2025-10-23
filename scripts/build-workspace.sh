#!/bin/bash
echo "Building ArxOS workspace..."

echo ""
echo "Building arxos-core with git features..."
cargo build -p arxos-core

echo ""
echo "Building arxos-cli..."
cargo build -p arxos-cli

echo ""
echo "Building arxos-mobile with core-only features..."
cargo build -p arxos-mobile --no-default-features --features core-only

echo ""
echo "Building root arxos package..."
cargo build -p arxos

echo ""
echo "All builds completed successfully!"
