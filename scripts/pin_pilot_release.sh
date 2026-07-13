#!/usr/bin/env bash
# Create an annotated pilot release tag after compiler-core checks (R9).
# Usage:
#   ./scripts/pin_pilot_release.sh v2.0.0-pilot.4
#   ./scripts/pin_pilot_release.sh v2.0.0-pilot.4 --dry-run
#
# After compiler-core (empty default features), cut a new pin (e.g. pilot.4)
# so field installs include that packaging — do not leave pilots on pilot.3
# if they need the new defaults.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TAG="${1:-}"
DRY=0
if [[ "${2:-}" == "--dry-run" ]] || [[ "${1:-}" == "--dry-run" ]]; then
  DRY=1
fi
if [[ -z "$TAG" || "$TAG" == "--dry-run" ]]; then
  echo "Usage: $0 v2.0.0-pilot.N [--dry-run]"
  exit 1
fi

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+-pilot\.[0-9]+$ ]]; then
  echo "WARNING: tag '$TAG' does not match vX.Y.Z-pilot.N (continuing anyway)"
fi

echo "==> Working tree status"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: working tree not clean. Commit or stash first."
  git status -sb
  exit 1
fi

SHA=$(git rev-parse HEAD)
echo "    commit: $SHA"
echo "    branch: $(git rev-parse --abbrev-ref HEAD)"
echo "    features: default = tui + compiler spine"

echo "==> Compiler-core checks (lib + spine + clippy)"
cargo clippy --all-targets -- -D warnings
cargo test --lib -q
cargo test -q \
  --test compiler_spine_test \
  --test ifc_compiler_path_test \
  --test bidirectional_tests \
  --test lidar_tests \
  --test contribution_spine_test

if [[ "${PIN_SKIP_L1_SMOKE:-}" != "1" ]]; then
  echo "==> L1 smoke (set PIN_SKIP_L1_SMOKE=1 to skip)"
  cargo build -q
  ./scripts/l1_smoke.sh
else
  echo "==> L1 smoke skipped (PIN_SKIP_L1_SMOKE=1)"
fi

echo "==> Tag message"
MSG="L1 pilot pin ${TAG}
Commit: ${SHA}
Build: default features (tui + compiler; no hardware/render3d)
Supported workflow: docs/l1-supported-workflow.md
Resource limits: docs/resource-limits.md
Obligations: arxos_manifest.md §1.6 (R9)
"

if [[ "$DRY" -eq 1 ]]; then
  echo "[dry-run] would create annotated tag $TAG at $SHA"
  echo "$MSG"
  exit 0
fi

if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "ERROR: tag $TAG already exists"
  exit 1
fi

git tag -a "$TAG" -m "$MSG"
echo "Created tag $TAG -> $SHA"
echo "Push when policy allows: git push origin $TAG"
echo "Then update docs/pilot-release.md pin log + charter §2 with tag and SHA."
