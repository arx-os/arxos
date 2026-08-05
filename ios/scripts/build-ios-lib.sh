#!/usr/bin/env bash
# Build arxos-ffi static library for physical iPhone (aarch64-apple-ios).
#
# Output:
#   ios/ArxosApp/Vendor/libarxos_core.a
#   ios/ArxosApp/Vendor/include/ (headers for reference)
#
# Requires full Xcode (not Command Line Tools only):
#   export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$ROOT/ios/ArxosApp/Vendor"
TARGET=aarch64-apple-ios
DEPLOY=${IPHONEOS_DEPLOYMENT_TARGET:-16.0}

if [[ -d /Applications/Xcode.app/Contents/Developer ]]; then
  export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
fi

if ! xcrun --sdk iphoneos --show-sdk-path >/dev/null 2>&1; then
  echo "error: iphoneos SDK not found. Install Xcode and run:" >&2
  echo "  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer" >&2
  exit 1
fi

export SDKROOT
SDKROOT="$(xcrun --sdk iphoneos --show-sdk-path)"
export IPHONEOS_DEPLOYMENT_TARGET="$DEPLOY"

echo "Building arxos-ffi for $TARGET (SDK=$SDKROOT)…"
cargo build -p arxos-ffi --release --target "$TARGET" --manifest-path "$ROOT/Cargo.toml"

LIB="$ROOT/target/$TARGET/release/libarxos_core.a"
if [[ ! -f "$LIB" ]]; then
  echo "error: expected $LIB" >&2
  exit 1
fi

mkdir -p "$OUT_DIR/include"
cp -f "$LIB" "$OUT_DIR/libarxos_core.a"
# Copy UniFFI C header if present
HDR="$ROOT/ios/Arxos/Sources/CArxosCoreFFI/arxos_coreFFI.h"
if [[ -f "$HDR" ]]; then
  cp -f "$HDR" "$OUT_DIR/include/arxos_coreFFI.h"
fi

echo "Wrote $OUT_DIR/libarxos_core.a"
file "$OUT_DIR/libarxos_core.a"
ls -lh "$OUT_DIR/libarxos_core.a"
