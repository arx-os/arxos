# Contribution path: building data → reward package

**Vision:** Arxos is free to use. Peers build, review, and are **rewarded** for verified as-built data. Data buyers pay $AXD for access; contributors mint on verified input.

## What counts as a contribution (locked)

| Unit | Status |
| :--- | :--- |
| Validated `Building` / `building.yaml` content (+ optional Git commit) | **Primary** |
| Human review of LiDAR autos (`review_status`) | Affects **quality** |
| Sensor `DeviceState` hashes | **Secondary only** (hardware), not the as-built labor unit |

## Local flow (implemented)

```bash
arx init --name "Site"
# … import / edit / review / validate …
arx contribute --output contribution.json
# optional: --latitude --longitude --git-commit <oid>
```

`arx contribute`:

1. Loads `building.yaml`
2. Requires clean validation (unless `--allow-invalid`)
3. Computes deterministic **content hash** + **entity merkle root** → combined `merkle_root`
4. Scores **accuracy / completeness** from validation + LiDAR review coverage
5. Writes `contribution.json` (`ContributionPackage`)

## Package fields (v1)

See `ContributionPackage` in `src/contribution/package.rs`:

- `building_id` — model UUID; **must** match `ArxRegistry.registerBuilding(buildingId, …)`
- `merkle_root_hex` — primary commitment for oracle `ContributionProof.merkleRoot`
- `content_hash_hex` — YAML body hash
- `accuracy` / `completeness` — 0–100 quality
- `git_commit` — HEAD oid when available
- `hash_algorithm` — `sha256-v1` off-chain; on-chain path may re-encode with keccak under `--features blockchain`

## EIP-712 sign + submit (N2–N3)

Rebuild CLI with chain support:

```bash
cargo build --features blockchain
```

```bash
# Package + sign (offline EIP-712; default key = Anvil account #0)
arx contribute --sign --oracle 0xYourOracle --chain-id 31337

# Propose on local Anvil (caller must have ORACLE_ROLE + min stake; worker registered)
arx contribute --sign --submit \
  --oracle 0xYourOracle \
  --worker 0xWorker \
  --amount 100 \
  --rpc-url http://127.0.0.1:8545
```

Helpers:

| API | Role |
| :--- | :--- |
| `ContributionProof::from_package` | Package → Solidity-shaped proof + quality |
| `sign_package_offline` | EIP-712 signature without RPC |
| `OracleClient::report_from_package` | `proposeContribution` on-chain |

Local deploy sketch: `scripts/local_oracle_e2e.sh` (requires `anvil` + `forge`).

Mint finalization follows contract rules: **2-of-3** confirms + **24h** delay.

### On-chain E2E (Foundry) — **Done**

```bash
cd contracts
forge test --match-contract BuildingContributionE2E -vv
# Full suite:
forge test
```

`BuildingContributionE2E` proves:

1. Register worker + **building UUID** (`Building.id` / package `building_id`)
2. Stake two oracles
3. Worker-signed proof over building merkle root + quality
4. Both oracles propose the **same** proof
5. Warp 24h → finalize → **$AXD mint 70/10/10/10** (quality-scaled)
6. Unregistered UUID reverts

Oracle proof hash is locked on first propose (second oracle cannot swap merkle roots).

## Remaining

| Step | Status |
| :--- | :--- |
| EIP-712 sign package as Solidity `ContributionProof` | **Done** |
| Submit `proposeContribution` | **Done** (CLI + contracts) |
| Building UUID ↔ Registry `buildingId` E2E mint | **Done** (Foundry `BuildingContributionE2E`) |
| Live Anvil script auto-register/stake/mint | Partial — `scripts/local_oracle_e2e.sh` + forge E2E is source of truth |
| Buyer pay-for-query in $AXD | **Done** (N5 — see `docs/lab/data-access.md`) |

## Module map

| Path | Role |
| :--- | :--- |
| `src/contribution/` | Always-on commitment + quality + package |
| `src/cli/commands/contribute.rs` | `arx contribute` |
| `src/blockchain/` | Feature-gated chain client / EIP-712 |
| `contracts/src/ArxContributionOracle.sol` | On-chain verify + mint |
