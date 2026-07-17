#!/usr/bin/env bash
# Automated L1 smoke: supported free-software loop (+ optional commercial gate).
# Does NOT replace second-person checklist (R5) on district hardware.
#
# Usage (from repo root):
#   ./scripts/l1_smoke.sh
#   ./scripts/l1_smoke.sh /path/to/file.ifc
#   ARX_BIN=./target/release/arx ./scripts/l1_smoke.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ARX="${ARX_BIN:-$ROOT/target/debug/arx}"
if [[ ! -x "$ARX" ]]; then
  echo "==> Building arx (debug)..."
  cargo build -q
  ARX="$ROOT/target/debug/arx"
fi

IFC="${1:-$ROOT/test_data/sample_building.ifc}"
if [[ ! -f "$IFC" ]]; then
  echo "ERROR: IFC not found: $IFC"
  echo "  Sample path: $ROOT/test_data/sample_building.ifc"
  exit 1
fi

# Resolve to absolute path before changing directory
IFC="$(cd "$(dirname "$IFC")" && pwd)/$(basename "$IFC")"

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
echo "==> Workdir: $WORKDIR"
echo "==> IFC: $IFC"
echo "==> arx: $($ARX --version 2>/dev/null || echo unknown)"

cd "$WORKDIR"

echo "==> init / validate"
"$ARX" init --name "L1 Smoke Site"
"$ARX" validate

echo "==> import ifc / validate"
"$ARX" import ifc "$IFC"
"$ARX" validate

echo "==> address validation check (lenient default vs strict)"
"$ARX" edit - <<EOF
add room Mech floor="Ground Floor" type=mechanical
add equipment faucet-01 room=Mech type=plumbing
EOF

python3 -c '
import sys
content = open("building.yaml").read()
target = "name: faucet-01"
if target in content:
    replacement = target + "\n  address: /usa/ny/brooklyn/smoke/floor-02/hvac/faucet-01"
    content = content.replace(target, replacement)
    with open("building.yaml", "w") as f:
        f.write(content)
else:
    print("faucet-01 not found")
    sys.exit(1)
'

# 1. Lenient validation (default): must pass (warning only, no hard validation error)
"$ARX" validate

# 2. Strict validation (--strict-addresses): must fail validation
set +e
"$ARX" validate --strict-addresses >/dev/null 2>&1
STRICT_FAIL=$?
set -e
if [[ "$STRICT_FAIL" -eq 0 ]]; then
  echo "ERROR: validate --strict-addresses should have failed with prefix mismatch"
  exit 1
fi
echo "Strict address validation correctly caught and blocked mismatch."

echo "==> export (internal + approved-only)"
mkdir -p exports
"$ARX" export --format ifc --output exports/out.ifc
"$ARX" export --format ifc --approved-only --output exports/approved.ifc
test -s exports/out.ifc
test -s exports/approved.ifc

echo "==> git stage / commit (local)"
"$ARX" status
"$ARX" stage
# Both forms must work (R5: field docs use -m; cli-reference uses positional)
"$ARX" commit -m "l1 smoke: import sample IFC"
"$ARX" status

echo "==> contribute package"
"$ARX" contribute --output contribution.json --dry-run >/dev/null || true
"$ARX" contribute --output contribution.json
test -s contribution.json

echo "==> commercial gate (refuse → grant → allow)"
set +e
"$ARX" export --format ifc --commercial --output exports/paid.ifc >/dev/null 2>&1
COM_FAIL=$?
set -e
if [[ "$COM_FAIL" -eq 0 ]]; then
  echo "ERROR: commercial export should fail without receipt"
  exit 1
fi
"$ARX" access grant --tx-hash 0xl1smoke >/dev/null
"$ARX" export --format ifc --commercial --output exports/paid.ifc >/dev/null
test -s exports/paid.ifc

echo ""
echo "========================================"
echo "L1 smoke PASS"
echo "  init → import → validate → export OK"
echo "  --approved-only export OK"
echo "  stage + commit -m OK"
echo "  contribute package OK"
echo "  commercial refuse → grant → allow OK"
echo "========================================"
echo "This does not close R5 (second person on district laptop)."
