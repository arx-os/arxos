# Changelog

## Unreleased

### Removed

- Deleted the experimental commercial control-plane service and its documentation
  (including the long-form fiat-model audit that prescribed SaaS ledgers/accounts).
- EVM contracts remain only under `archive/contracts-evm-deprecated/` (not built).

### Breaking (retained)

- CLI: `arx score` / `arx verify` / `arx attest` (no `arx depin`).
- Core: `arxos_core::scoring` (formerly `depin`); no registry/on-chain handoff types.
- `ScoreReport` includes `policy_version` (default `1`).

### Changed

- Economic model: DePIN contribution → scoring; **fiat** settlement (not tokens).
  See `docs/architecture/ADR-001-fiat-settled-depin.md`.

### Notes

- Scoring is **diagnostic only** (type-count weights) until multi-signal quality
  scoring is intentional product work.
