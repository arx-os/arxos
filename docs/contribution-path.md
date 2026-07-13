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

- `building_id` — model UUID (Registry candidate)
- `merkle_root_hex` — primary commitment for oracle `ContributionProof.merkleRoot`
- `content_hash_hex` — YAML body hash
- `accuracy` / `completeness` — 0–100 quality
- `git_commit` — HEAD oid when available
- `hash_algorithm` — `sha256-v1` off-chain; on-chain path may re-encode with keccak under `--features blockchain`

## Not yet wired (next engineering)

| Step | Status |
| :--- | :--- |
| EIP-712 sign package as Solidity `ContributionProof` | Partial (`blockchain` proof module) |
| Submit to Anvil `ArxContributionOracle` | Open |
| 2-of-3 confirm + mint 70/10/10/10 | Contracts exist; not end-to-end from CLI |
| Buyer pay-for-query in $AXD | Open |

## Module map

| Path | Role |
| :--- | :--- |
| `src/contribution/` | Always-on commitment + quality + package |
| `src/cli/commands/contribute.rs` | `arx contribute` |
| `src/blockchain/` | Feature-gated chain client / EIP-712 |
| `contracts/src/ArxContributionOracle.sol` | On-chain verify + mint |
