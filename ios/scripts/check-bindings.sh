#!/usr/bin/env bash
# Fail closed if UniFFI Swift bindings are missing or stale vs ffi/src/arxos.udl.
#
# Used by the Xcode "Check UniFFI bindings" Run Script phase and by prep.sh
# consumers. Does not rebuild — only verifies artifacts exist and are fresh.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UDL="$ROOT/ffi/src/arxos.udl"
GEN_SWIFT="$ROOT/ios/Arxos/Sources/ArxosCore/Generated/arxos_core.swift"
GEN_H="$ROOT/ios/Arxos/Sources/CArxosCoreFFI/arxos_coreFFI.h"
LIB="$ROOT/ios/ArxosApp/Vendor/libarxos_core.a"

fail() {
  echo "error: $*" >&2
  echo "error: run from repo root: ./ios/scripts/prep.sh" >&2
  exit 1
}

[[ -f "$UDL" ]] || fail "UDL not found: $UDL"
[[ -f "$GEN_SWIFT" ]] || fail "generated Swift missing: $GEN_SWIFT"
[[ -f "$GEN_H" ]] || fail "C header missing: $GEN_H"

# Optional: static lib (device builds need it; SPM macOS demo uses host lib).
if [[ "${REQUIRE_IOS_LIB:-1}" == "1" ]]; then
  [[ -f "$LIB" ]] || fail "iOS static lib missing: $LIB"
fi

mtime() {
  # macOS stat first, then GNU.
  if stat -f '%m' "$1" >/dev/null 2>&1; then
    stat -f '%m' "$1"
  else
    stat -c '%Y' "$1"
  fi
}

UDL_M=$(mtime "$UDL")
SWIFT_M=$(mtime "$GEN_SWIFT")
if [[ "$SWIFT_M" -lt "$UDL_M" ]]; then
  fail "generated Swift is older than UDL ($GEN_SWIFT mtime < $UDL mtime). Re-run ./ios/scripts/prep.sh"
fi

# Sanity: public RoomPlan / store APIs still present after regen.
if ! grep -q 'public func ingestRoomPlan' "$GEN_SWIFT"; then
  fail "generated bindings missing ingestRoomPlan — regenerate with prep.sh"
fi
if ! grep -q 'public enum ArxosError' "$GEN_SWIFT"; then
  fail "generated bindings missing ArxosError"
fi

echo "check-bindings: ok (swift fresh vs UDL)"
