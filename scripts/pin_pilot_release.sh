#!/usr/bin/env bash
# Create an annotated pilot release tag after basic checks (R9).
# Usage:
#   ./scripts/pin_pilot_release.sh v2.0.0-pilot.1
#   ./scripts/pin_pilot_release.sh v2.0.0-pilot.1 --dry-run
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

echo "==> Quick checks (lib + spine)"
cargo test --lib -q
cargo test --test compiler_spine_test -q

echo "==> Tag message"
MSG="L1 pilot pin ${TAG}
Commit: ${SHA}
Supported workflow: docs/l1-supported-workflow.md
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
echo "Record tag + SHA in docs/pilot-charter.md for the active pilot."
