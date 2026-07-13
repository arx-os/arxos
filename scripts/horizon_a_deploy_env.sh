#!/usr/bin/env bash
# Horizon A1–A2: deploy local tokenomics stack and write .env.arx
#
# Prerequisites: anvil running on :8545, forge, cast, python3
# Usage (from repo root):
#   ./scripts/horizon_a_deploy_env.sh
#   ./scripts/horizon_a_deploy_env.sh --register   # also register worker + building.yaml id
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
RPC="${RPC_URL:-http://127.0.0.1:8545}"
# Anvil account #0
export PRIVATE_KEY="${PRIVATE_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}"
export MAINTAINER_VAULT="${MAINTAINER_VAULT:-0x70997970C51812dc3A010C7d01b50e0d17dc79C8}"
export TREASURY="${TREASURY:-0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC}"
# Anvil #1 as worker by default
WORKER_ADDRESS="${WORKER_ADDRESS:-0x70997970C51812dc3A010C7d01b50e0d17dc79C8}"
BUILDING_WALLET="${BUILDING_WALLET:-0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC}"
# Anvil #2 as second oracle
ORACLE2_ADDRESS="${ORACLE2_ADDRESS:-0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC}"
ORACLE2_KEY="${ORACLE2_KEY:-0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a}"

DO_REGISTER=0
for arg in "$@"; do
  case "$arg" in
    --register) DO_REGISTER=1 ;;
  esac
done

echo "==> Checking Anvil at $RPC"
if ! cast block-number --rpc-url "$RPC" >/dev/null 2>&1; then
  echo "ERROR: Anvil not reachable at $RPC"
  echo "Start: anvil"
  exit 1
fi

echo "==> Deploying contracts (forge)..."
# Deploy.s.sol writes contracts/deployed.env via vm.writeFile (fs-safe).
export ARX_ENV_OUT="./deployed.env"
export RPC_URL="$RPC"
cd "$ROOT/contracts"
rm -f deployed.env
forge script script/Deploy.s.sol:DeployArxos \
  --rpc-url "$RPC" \
  --broadcast \
  -vv

if [[ ! -f "$ROOT/contracts/deployed.env" ]]; then
  echo "ERROR: Deploy did not write contracts/deployed.env"
  exit 1
fi

cp "$ROOT/contracts/deployed.env" "$ROOT/.env.arx"
# Ensure RPC is set
if ! grep -q '^RPC_URL=' "$ROOT/.env.arx"; then
  echo "RPC_URL=$RPC" >> "$ROOT/.env.arx"
fi

echo "==> Deployed env (copied to $ROOT/.env.arx):"
grep -E '^(ARX_|RPC_|CHAIN_|WORKER_|BUILDING_WALLET)' "$ROOT/.env.arx" || true

# Fail closed if critical addresses missing
python3 - "$ROOT/.env.arx" <<'PY'
import sys
from pathlib import Path
env = {}
for line in Path(sys.argv[1]).read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
required = ["ARX_REGISTRY", "ARX_TOKEN", "ARX_ORACLE", "ARX_PAYMENT_ROUTER"]
missing = [k for k in required if not env.get(k)]
if missing:
    sys.exit(f"ERROR: .env.arx missing: {', '.join(missing)}")
print("  env OK:", ", ".join(required))
PY

cd "$ROOT"
# shellcheck disable=SC1091
set -a
source .env.arx
set +a

if [[ "$DO_REGISTER" -eq 1 ]]; then
  echo "==> Resolving BUILDING_ID from building.yaml (if present)..."
  if [[ -f building.yaml ]]; then
    BUILDING_ID=$(python3 - <<'PY'
import re, sys
from pathlib import Path
text = Path("building.yaml").read_text()
# BuildingData shape: building:\n  id: "..."
m = re.search(r"(?m)^\s*id:\s*[\"']?([0-9a-fA-F-]{36})[\"']?", text)
if not m:
    # nested under building:
    m = re.search(r"(?ms)^building:.*?^\s+id:\s*[\"']?([0-9a-fA-F-]{36})", text)
if m:
    print(m.group(1))
else:
    sys.exit("Could not parse building id from building.yaml")
PY
)
    export BUILDING_ID
    echo "    BUILDING_ID=$BUILDING_ID"
  else
    export BUILDING_ID="${BUILDING_ID:-horizon-a-demo-building}"
    echo "    No building.yaml — using BUILDING_ID=$BUILDING_ID"
  fi
  export WORKER_ADDRESS BUILDING_WALLET
  export ARX_REGISTRY ARX_ORACLE ARX_TOKEN
  export ARX_STAKING="${ARX_STAKING:-}"

  echo "==> Register worker + building (forge)..."
  cd "$ROOT/contracts"
  forge script script/Register.s.sol:RegisterArxos \
    --rpc-url "$RPC" \
    --broadcast \
    -vv
  cd "$ROOT"
  # Append / update building id in env
  python3 - "$BUILDING_ID" <<'PY'
import sys
from pathlib import Path
bid = sys.argv[1]
p = Path(".env.arx")
lines = p.read_text().splitlines() if p.exists() else []
out, found = [], False
for line in lines:
    if line.startswith("BUILDING_ID="):
        out.append(f"BUILDING_ID={bid}")
        found = True
    else:
        out.append(line)
if not found:
    out.append(f"BUILDING_ID={bid}")
p.write_text("\n".join(out) + "\n")
print(f"    .env.arx BUILDING_ID={bid}")
PY
fi

echo ""
echo "========================================"
echo "Horizon A deploy env ready"
echo "  source $ROOT/.env.arx"
echo "  See docs/lab/horizon-a-ops.md for mint/pay steps"
echo "========================================"
