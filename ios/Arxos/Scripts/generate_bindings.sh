#!/usr/bin/env bash
# Generate UniFFI Swift bindings from arxos-core.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT_DIR="$ROOT/ios/Arxos/Sources/ArxosCore/Generated"
UDL="$ROOT/ffi/src/arxos.udl"

mkdir -p "$OUT_DIR"

echo "Building arxos-ffi…"
cargo build -p arxos-ffi --manifest-path "$ROOT/Cargo.toml"

cargo run --manifest-path "$ROOT/Cargo.toml" -p arxos-ffi --bin uniffi-bindgen generate "$UDL" --language swift --out-dir "$OUT_DIR"

SWIFT_FILE="$OUT_DIR/arxos_core.swift"
if [ -f "$SWIFT_FILE" ]; then
  echo "Wrapping generated swift bindings in conditional compilation gates..."
  TMP_FILE=$(mktemp)
  echo "#if canImport(ArxosCoreFFI)" > "$TMP_FILE"
  cat "$SWIFT_FILE" >> "$TMP_FILE"
  echo "" >> "$TMP_FILE"
  echo "#endif" >> "$TMP_FILE"
  mv "$TMP_FILE" "$SWIFT_FILE"
fi

echo "Bindings written to $OUT_DIR"
ls -la "$OUT_DIR"
