#!/usr/bin/env bash
# Generate UniFFI Swift bindings from arxos-core.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT_DIR="$ROOT/ios/Arxos/Sources/ArxosCore/Generated"
UDL="$ROOT/core/src/arxos.udl"

mkdir -p "$OUT_DIR"

echo "Building arxos-core with uniffi feature…"
cargo build -p arxos-core --features uniffi --manifest-path "$ROOT/Cargo.toml"

echo "Generating Swift bindings…"
if command -v uniffi-bindgen >/dev/null 2>&1; then
  uniffi-bindgen generate "$UDL" --language swift --out-dir "$OUT_DIR"
elif cargo run -p uniffi-bindgen --quiet --generate --language swift --out-dir "$OUT_DIR" "$UDL" 2>/dev/null; then
  true
else
  # Use the library's built-in bindgen via a small helper if installed:
  cargo install uniffi-bindgen --version 0.28.3 --locked 2>/dev/null || true
  if command -v uniffi-bindgen >/dev/null 2>&1; then
    uniffi-bindgen generate "$UDL" --language swift --out-dir "$OUT_DIR"
  else
    echo "warning: uniffi-bindgen not available; leaving Phase 0 Swift shim in place."
    echo "Install with: cargo install uniffi-bindgen --version 0.28.3"
    exit 0
  fi
fi

echo "Bindings written to $OUT_DIR"
ls -la "$OUT_DIR"
