# Horizon A ops runbook — mint + pay without reading Solidity

**Goal:** Cold engineer completes deploy → register → contribute path + access payment + commercial export gate.

## Prerequisites

- `anvil`, `forge`, `cast`, `python3`
- Rust toolchain; optional: `cargo build --features blockchain`

## 1. Start Anvil

```bash
anvil
# leave running — RPC http://127.0.0.1:8545
```

## 2. Deploy + write `.env.arx`

```bash
# From repo root
./scripts/horizon_a_deploy_env.sh
source .env.arx
```

Creates `.env.arx` with `ARX_ORACLE`, `ARX_REGISTRY`, `ARX_TOKEN`, `ARX_PAYMENT_ROUTER`, etc.

## 3. Init project + register building UUID

```bash
mkdir /tmp/arx-horizon-a && cd /tmp/arx-horizon-a
arx init --name "Horizon A Site"
# Copy or symlink repo .env.arx, or re-run deploy from repo with --register after cd

# From repo (with building.yaml in cwd) OR export BUILDING_ID manually:
cd /path/to/arxos
# If you have a project building.yaml in cwd:
./scripts/horizon_a_deploy_env.sh --register
```

`--register` parses `building.yaml` `id` (UUID) and runs `Register.s.sol`.

Manual cast alternative:

```bash
source .env.arx
cast send $ARX_REGISTRY "registerBuilding(string,address)" "$BUILDING_ID" $BUILDING_WALLET \
  --rpc-url $RPC_URL --private-key $PRIVATE_KEY
cast send $ARX_REGISTRY "registerWorker(address,string)" $ARX_WORKER "meta" \
  --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

## 4. Contributor loop (free software)

```bash
arx import …   # or edit scripts
arx edit corrections.txt   # set review_status=accepted as needed
arx validate
arx contribute --output contribution.json
```

## 5. Sign + propose (blockchain feature)

```bash
cargo build --features blockchain --manifest-path /path/to/arxos/Cargo.toml
source .env.arx

arx contribute --sign --submit \
  --oracle $ARX_ORACLE \
  --worker $ARX_WORKER \
  --amount 100 \
  --rpc-url $RPC_URL \
  --private-key $ARX_PRIVATE_KEY
```

**Note:** Mint finalization needs **2 oracle confirms** + **24h delay** on-chain.  
In Foundry tests we warp time; on Anvil you can:

```bash
# Second confirmation from another oracle key (if granted ORACLE_ROLE + staked)
# Then advance time:
cast rpc anvil_increaseTime 86401 --rpc-url $RPC_URL
cast rpc anvil_mine --rpc-url $RPC_URL
cast send $ARX_ORACLE "finalizeContribution(bytes32)" $CONTRIBUTION_ID \
  --rpc-url $RPC_URL --private-key $PRIVATE_KEY
```

Full automated mint with two oracles is covered by `forge test --match-contract BuildingContributionE2E`.

## 6. Buyer pays for data access

```bash
arx access quote --amount 1 --output access-request.json
arx access pay --request access-request.json \
  --router $ARX_PAYMENT_ROUTER \
  --token $ARX_TOKEN \
  --rpc-url $RPC_URL
# Writes access-receipt.json
```

Manual receipt (if paid elsewhere):

```bash
arx access grant --tx-hash 0x... 
```

## 7. Host gate (N7) — commercial export only with receipt

```bash
# Free export still works for field ops:
arx export --format ifc -o internal.ifc

# Commercial / paid delivery:
arx export --format ifc --commercial -o paid.ifc
# Fails without access-receipt.json matching building.id
```

## Exit criteria (Horizon A)

- [ ] `.env.arx` generated without reading forge logs by hand  
- [ ] Worker + building UUID registered  
- [ ] `arx contribute` package produced  
- [ ] `arx access pay` (or grant) wrote `access-receipt.json`  
- [ ] `arx export --commercial` succeeds only with receipt  
- [ ] Foundry E2E still green: `cd contracts && forge test`  

Next: **Horizon B** — one real building (`docs/field-trial.md`).
