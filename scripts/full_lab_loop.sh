#!/usr/bin/env bash
# Full ArxOS *engineering* closed loop (lab evidence — not district L1 exit).
#
# Proves, in order:
#   1) Compiler spine unit/integration tests
#   2) Free-software pilot loop + commercial host gate (l1_smoke)
#   3) On-chain mint E2E (Foundry BuildingContributionE2E)
#   4) On-chain buyer access E2E (Foundry DataAccessPaymentE2E)
#   5) Optional: Anvil deploy → .env.arx (RUN_ANVIL=1)
#
# Does NOT close R5 (second person), R1/R2 (field truth), or L3 mainnet.
#
# Usage (repo root):
#   ./scripts/full_lab_loop.sh
#   SKIP_FORGE=1 ./scripts/full_lab_loop.sh      # compiler-only (no Foundry)
#   RUN_ANVIL=1 ./scripts/full_lab_loop.sh       # also deploy local stack
#   QUICK=1 ./scripts/full_lab_loop.sh           # skip full lib suite; smoke + forge E2E
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SKIP_FORGE="${SKIP_FORGE:-0}"
RUN_ANVIL="${RUN_ANVIL:-0}"
QUICK="${QUICK:-0}"
FAIL=0

phase() {
  echo ""
  echo "========================================"
  echo "PHASE $1 — $2"
  echo "========================================"
}

ok() { echo "  PASS: $1"; }
bad() { echo "  FAIL: $1"; FAIL=1; }

phase "1" "Compiler tests (Rust)"
if [[ "$QUICK" == "1" ]]; then
  cargo test --lib -q
  cargo test --test compiler_spine_test --test contribution_spine_test -q
else
  cargo test --lib -q
  cargo test --test compiler_spine_test --test contribution_spine_test \
    --test ifc_compiler_path_test -q
fi
ok "Rust compiler + contribution spine"

phase "2" "L1 free-software loop + commercial gate"
./scripts/l1_smoke.sh
ok "l1_smoke (init→import→validate→export→git→contribute→commercial)"

phase "3" "Foundry: contribution mint E2E (N3/N4)"
if [[ "$SKIP_FORGE" == "1" ]]; then
  echo "  SKIP (SKIP_FORGE=1)"
elif ! command -v forge >/dev/null 2>&1; then
  echo "  SKIP (forge not installed)"
else
  (
    cd "$ROOT/contracts"
    forge test --match-contract BuildingContributionE2E -q
  )
  ok "BuildingContributionE2E (package→propose→finalize mint)"
fi

phase "4" "Foundry: buyer access payment E2E (N5)"
if [[ "$SKIP_FORGE" == "1" ]]; then
  echo "  SKIP (SKIP_FORGE=1)"
elif ! command -v forge >/dev/null 2>&1; then
  echo "  SKIP (forge not installed)"
else
  (
    cd "$ROOT/contracts"
    forge test --match-contract DataAccessPaymentE2E -q
  )
  ok "DataAccessPaymentE2E (payForAccess AXD)"
fi

phase "5" "Optional Anvil deploy env (N8)"
if [[ "$RUN_ANVIL" != "1" ]]; then
  echo "  SKIP (set RUN_ANVIL=1 to deploy local stack → .env.arx)"
elif ! command -v anvil >/dev/null 2>&1 || ! command -v cast >/dev/null 2>&1; then
  echo "  SKIP (anvil/cast not installed)"
else
  ANVIL_PID=""
  cleanup_anvil() {
    if [[ -n "${ANVIL_PID}" ]] && kill -0 "$ANVIL_PID" 2>/dev/null; then
      kill "$ANVIL_PID" 2>/dev/null || true
      wait "$ANVIL_PID" 2>/dev/null || true
    fi
  }
  trap cleanup_anvil EXIT

  if ! cast block-number --rpc-url http://127.0.0.1:8545 >/dev/null 2>&1; then
    echo "  Starting anvil on :8545..."
    anvil --silent >/tmp/arx-anvil-full-loop.log 2>&1 &
    ANVIL_PID=$!
    for _ in $(seq 1 30); do
      if cast block-number --rpc-url http://127.0.0.1:8545 >/dev/null 2>&1; then
        break
      fi
      sleep 0.2
    done
  fi

  if ! cast block-number --rpc-url http://127.0.0.1:8545 >/dev/null 2>&1; then
    bad "Anvil not reachable on :8545"
  else
    # Deploy stack → .env.arx; register demo building when no building.yaml
    export BUILDING_ID="${BUILDING_ID:-lab-full-loop-demo}"
    ./scripts/horizon_a_deploy_env.sh --register
    test -f "$ROOT/.env.arx"
    grep -q 'ARX_ORACLE=' "$ROOT/.env.arx"
    ok "Anvil deploy → .env.arx + register helpers (N8)"
  fi
  cleanup_anvil
  trap - EXIT
fi

echo ""
echo "========================================"
if [[ "$FAIL" -ne 0 ]]; then
  echo "FULL LAB LOOP FAILED"
  exit 1
fi
echo "FULL LAB LOOP PASS (engineering)"
echo "  Compiler + L1 smoke + chain mint/pay E2E"
echo "  District obligations R1/R5/R7/R10 still field-gated"
echo "========================================"
