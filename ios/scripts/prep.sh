#!/usr/bin/env bash
# Prepare the iOS field-client artifacts: UniFFI bindings + aarch64 staticlib.
#
# Run from anywhere; paths resolve relative to the repo root.
#
# Steps:
#   1. cargo build -p arxos-ffi  (host, for uniffi-bindgen)
#   2. regenerate Swift + C headers
#   3. cross-compile libarxos_core.a for aarch64-apple-ios
#   4. stamp Vendor/BUILD_ID (git rev + UDL sha256)
#
# Xcode: a Run Script phase calls check-bindings.sh before compile and fails
# closed if Generated/arxos_core.swift is missing or older than the UDL.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "==> [1/4] Build arxos-ffi (host)…"
cargo build -p arxos-ffi --manifest-path "$ROOT/Cargo.toml"

echo "==> [2/4] Generate UniFFI Swift bindings…"
"$ROOT/ios/Arxos/Scripts/generate_bindings.sh"

echo "==> [3/4] Cross-compile iOS static library…"
"$ROOT/ios/scripts/build-ios-lib.sh"

echo "==> [4/4] Stamp BUILD_ID…"
UDL="$ROOT/ffi/src/arxos.udl"
GEN_SWIFT="$ROOT/ios/Arxos/Sources/ArxosCore/Generated/arxos_core.swift"
VENDOR="$ROOT/ios/ArxosApp/Vendor"
mkdir -p "$VENDOR"

GIT_REV="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo "nogit")"
if command -v shasum >/dev/null 2>&1; then
  UDL_HASH="$(shasum -a 256 "$UDL" | awk '{print $1}')"
elif command -v sha256sum >/dev/null 2>&1; then
  UDL_HASH="$(sha256sum "$UDL" | awk '{print $1}')"
else
  UDL_HASH="unknown"
fi
SWIFT_MTIME="$(stat -f '%m' "$GEN_SWIFT" 2>/dev/null || stat -c '%Y' "$GEN_SWIFT" 2>/dev/null || echo 0)"
UDL_MTIME="$(stat -f '%m' "$UDL" 2>/dev/null || stat -c '%Y' "$UDL" 2>/dev/null || echo 0)"

{
  echo "git=${GIT_REV}"
  echo "udl_sha256=${UDL_HASH}"
  echo "udl_mtime=${UDL_MTIME}"
  echo "swift_mtime=${SWIFT_MTIME}"
  echo "prepared_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$VENDOR/BUILD_ID"

# Also copy stamp next to generated bindings for SPM consumers.
cp -f "$VENDOR/BUILD_ID" "$ROOT/ios/Arxos/Sources/ArxosCore/Generated/BUILD_ID" 2>/dev/null || true

echo ""
echo "iOS prep complete."
echo "  lib:      $VENDOR/libarxos_core.a"
echo "  bindings: $GEN_SWIFT"
echo "  BUILD_ID: $VENDOR/BUILD_ID"
cat "$VENDOR/BUILD_ID"
echo ""
echo "Open Xcode: open ios/ArxosApp/ArxosApp.xcodeproj"
