#!/usr/bin/env bash
# Automated L1 smoke: init → import sample IFC → validate → export → contribute package
# Does NOT replace second-person checklist (R5) on district hardware.
# Usage (from repo root): ./scripts/l1_smoke.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ARX="${ARX_BIN:-$ROOT/target/debug/arx}"
if [[ ! -x "$ARX" ]]; then
  echo "==> Building arx..."
  cargo build -q
  ARX="$ROOT/target/debug/arx"
fi

IFC="${1:-$ROOT/test_data/sample_building.ifc}"
if [[ ! -f "$IFC" ]]; then
  echo "ERROR: IFC not found: $IFC"
  exit 1
fi

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
echo "==> Workdir: $WORKDIR"
echo "==> IFC: $IFC"
echo "==> arx: $($ARX --version 2>/dev/null || echo unknown)"

cd "$WORKDIR"
"$ARX" init --name "L1 Smoke Site"
"$ARX" validate
# import needs relative or absolute path
"$ARX" import ifc "$IFC" || {
  echo "NOTE: import failed on sample — try: $ROOT/test_data/sample_building.ifc"
  exit 1
}
"$ARX" validate
mkdir -p exports
"$ARX" export --format ifc --output exports/out.ifc
"$ARX" contribute --output contribution.json --dry-run || true
"$ARX" contribute --output contribution.json

# commercial gate: must fail then succeed
set +e
"$ARX" export --format ifc --commercial --output exports/paid.ifc
COM_FAIL=$?
set -e
if [[ "$COM_FAIL" -eq 0 ]]; then
  echo "ERROR: commercial export should fail without receipt"
  exit 1
fi
"$ARX" access grant --tx-hash 0xl1smoke
"$ARX" export --format ifc --commercial --output exports/paid.ifc

echo ""
echo "========================================"
echo "L1 smoke PASS"
echo "  model import/validate/export OK"
echo "  contribute package written"
echo "  commercial gate refuse → grant → allow OK"
echo "========================================"
echo "This does not close R5 (second person on district laptop)."
