# ADR-001: Fiat-Settled DePIN (No Token Settlement)

**Status:** Accepted  
**Date:** 2026-08-04  
**Supersedes:** Token/mint settlement; any commercial control-plane / SaaS ledger service

---

## Context

Arxos is a **DePIN for the built environment**: local-first, content-addressed capture, versioning, verification, and scoring of building and spatial data.

Token minting and on-chain reward settlement are terminated. A separate SaaS-style control-plane service is **not** part of this project.

## Decision

### Architecture

| Layer | Role | In this repo |
|-------|------|----------------|
| **Data & scoring** | CAS, roots, capture, spatial index, sync, gateways, deterministic scoring | Yes — core product |
| **Fiat settlement** | Buyers pay fiat; contributors paid fiat from scores | Off-band (ops); **not** an in-repo ledger/account service |

### Economics

- Contribution → scoring → **fiat** compensation (not tokens).
- No native token, mint path, wallet settlement, or chain rewards.
- Scoring (`arxos_core::scoring`) is pure and offline-replayable; current weights are **diagnostic only**.
- Money, invoices, and payment identity **never** enter the CID / object graph.

### Contracts

EVM code lives only under `archive/contracts-evm-deprecated/` and is not built or shipped.

## Consequences

**Keep:** local-first CAS, device ed25519 integrity keys, multi-device sync, capture, gateways, `arx score` / `verify` / `attest`.

**Out of scope for this codebase:** commercial control-plane services, account/KYC products, points ledgers, and billing platforms as core architecture.

## References

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
