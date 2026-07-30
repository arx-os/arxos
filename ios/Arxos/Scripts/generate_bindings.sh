#!/usr/bin/env bash
# Generate UniFFI Swift bindings from arxos-ffi (real CAS path only — no shims).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT_DIR="$ROOT/ios/Arxos/Sources/ArxosCore/Generated"
UDL="$ROOT/ffi/src/arxos.udl"

mkdir -p "$OUT_DIR"

echo "Building arxos-ffi…"
cargo build -p arxos-ffi --manifest-path "$ROOT/Cargo.toml"

cargo run --manifest-path "$ROOT/Cargo.toml" -p arxos-ffi --bin uniffi-bindgen generate "$UDL" \
  --language swift --out-dir "$OUT_DIR"

# Keep C headers in the system library target (not the Swift target).
C_DIR="$ROOT/ios/Arxos/Sources/CArxosCoreFFI"
mkdir -p "$C_DIR"
if [ -f "$OUT_DIR/arxos_coreFFI.h" ]; then
  cp "$OUT_DIR/arxos_coreFFI.h" "$C_DIR/arxos_coreFFI.h"
fi
cat > "$C_DIR/module.modulemap" <<'EOF'
module arxos_coreFFI {
    header "arxos_coreFFI.h"
    export *
}
EOF
rm -f "$OUT_DIR/module.modulemap" "$OUT_DIR/arxos_coreFFI.modulemap"

# UniFFI still emits try! for a few infallible scaffolding buffer ops and pure
# helpers (hello/version). Public store/capture/commit paths must use try + throws.
# Fail the generator if any *throwing* public API regressed to try!.
if grep -E 'public func (initBuilding|openBuilding|commitBuilding|capture|listBuildings|annotationsNear|ingestRoomPlan|mergeBuildingRoot|pullRemoteRoot|putBlob|createRoot|exportUsd|exportIfc|showRoot|querySpatialVolume)' \
  "$OUT_DIR/arxos_core.swift" | grep -q 'try!'; then
  echo "error: public throwing UniFFI APIs must not use try!" >&2
  exit 1
fi

if ! grep -q 'public enum ArxosError' "$OUT_DIR/arxos_core.swift"; then
  echo "error: regenerated bindings missing ArxosError" >&2
  exit 1
fi

echo "Bindings written to $OUT_DIR"
ls -la "$OUT_DIR"
