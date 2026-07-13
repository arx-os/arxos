#!/usr/bin/env bash
# Local Anvil E2E sketch for N3: deploy tokenomics → register → sign package → propose.
# Requires: forge, anvil, cargo, jq (optional)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ANVIL_KEY="${PRIVATE_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}"
export PRIVATE_KEY="$ANVIL_KEY"
export MAINTAINER_VAULT="${MAINTAINER_VAULT:-0x70997970C51812dc3A010C7d01b50e0d17dc79C8}"
export TREASURY="${TREASURY:-0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC}"

echo "==> Start Anvil in another terminal: anvil"
echo "==> Deploy (forge script)..."
cd contracts
forge script script/Deploy.s.sol:DeployArxos --rpc-url http://127.0.0.1:8545 --broadcast -vv || {
  echo "Deploy failed — is anvil running on :8545?"
  exit 1
}
cd "$ROOT"

echo "==> Build arx with blockchain feature..."
cargo build --features blockchain --quiet

TMP=$(mktemp -d)
cd "$TMP"
"$ROOT/target/debug/arx" init --name "Oracle E2E"
"$ROOT/target/debug/arx" contribute --output contribution.json

echo "==> Sign package (EIP-712)..."
# Set ARX_ORACLE to deployed oracle from forge broadcast logs
ORACLE="${ARX_ORACLE:-0x0000000000000000000000000000000000000001}"
"$ROOT/target/debug/arx" contribute \
  --sign \
  --private-key "$ANVIL_KEY" \
  --oracle "$ORACLE" \
  --chain-id 31337 \
  --output contribution.signed.json

echo "Signed package at $TMP/contribution.signed.json"
echo "Next manual steps (from Deploy logs):"
echo "  1. Register worker + building on ArxRegistry"
echo "  2. Fund/stake oracle role account on ArxOracleStaking"
echo "  3. arx contribute --sign --submit --worker <addr> --oracle <addr> --amount 100"
echo "  4. Second oracle confirms; wait FINALIZATION_DELAY (or use test cheatcodes)"
echo "Done package+sign path. Full mint needs registry/stake setup."
