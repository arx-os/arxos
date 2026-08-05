# ARCHIVED — EVM contracts (not product)

**Status:** Archived 2026-08-04  
**Reason:** Arxos is a DePIN that settles rewards in **fiat**, not via token minting or
blockchain settlement.

This tree previously held a minimal `BuildingRegistry.sol` (and historically a larger
tokenomics suite removed in the greenfield rewrite). Historical reference only.

- **Do not** build, deploy, or extend these contracts for product features.  
- **Do not** reintroduce them into the Cargo workspace or CI.  
- Product docs: [`docs/architecture/ADR-001-fiat-settled-depin.md`](../../docs/architecture/ADR-001-fiat-settled-depin.md)

## Contents (snapshot)

| Path | Former role |
|------|-------------|
| `BuildingRegistry.sol` | EVM map of building id → official root + controllers |
| `script/Deploy.s.sol` | Foundry deploy script |
| `foundry.toml` | Foundry config |

Contributor scoring lives in `arxos-core` (`scoring`). Settlement is fiat, off-band.
