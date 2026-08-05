# ARCHIVED — EVM contracts (not product)

**Status:** Archived 2026-08-04  
**Reason:** Arxos pure-fiat commercial model permanently drops blockchain settlement, tokens, and on-chain registries.

This tree previously held a minimal `BuildingRegistry.sol` (and historically a much larger tokenomics suite removed in the greenfield rewrite). It is preserved only for historical reference.

- **Do not** build, deploy, or extend these contracts for product features.  
- **Do not** reintroduce them into the Cargo workspace or CI.  
- Active product docs: [`docs/architecture/ADR-001-data-plane-vs-control-plane.md`](../../docs/architecture/ADR-001-data-plane-vs-control-plane.md) and [`docs/architecture/FIAT_MODEL_AUDIT.md`](../../docs/architecture/FIAT_MODEL_AUDIT.md).

## Contents (snapshot)

| Path | Former role |
|------|-------------|
| `BuildingRegistry.sol` | EVM map of building id → official root + controllers |
| `script/Deploy.s.sol` | Foundry deploy script |
| `foundry.toml` | Foundry config |

Contributor scoring and commercial access live entirely off-chain in the data plane (`arxos-core` scoring) and a future control-plane service.
