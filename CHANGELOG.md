# Changelog

## Unreleased

### Breaking

- **CLI:** removed `arx depin …` namespace.
  - Use `arx score <building_id>`, `arx verify <root_cid>`, `arx attest <root_cid>`.
  - Removed `arx depin registry` and all EVM / ABI handoff flags.
- **Core:** module `arxos_core::depin` renamed to `arxos_core::scoring`.
  - Removed `RegistrySnapshot` and `registry_snapshot`.
  - `ScoreReport` now includes `policy_version` (default `1`).

### Changed

- **Economic model:** pure fiat only. No tokens, minting, or blockchain settlement.
  See `docs/architecture/ADR-001-data-plane-vs-control-plane.md`.
- **Archive:** EVM contracts moved to `archive/contracts-evm-deprecated/` (not built).

### Notes

- Scoring remains **diagnostic only** until multi-signal policy and a control-plane
  points ledger land (P1). Do not use scores as a payment basis.
