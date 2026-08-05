# ADR-001: Data Plane vs Control Plane (Pure-Fiat Model)

**Status:** Accepted  
**Date:** 2026-08-04  
**Supersedes:** Any prior DePIN / on-chain / token settlement designs  
**Related:** [`FIAT_MODEL_AUDIT.md`](FIAT_MODEL_AUDIT.md)

---

## Context

Arxos historically explored a tokenized DePIN economy ($AXD, EVM oracles, minting, on-chain access payments). That path is permanently terminated. The greenfield CAS core is the data foundation. Commercial product needs accounts, access control, metering, buyer billing, and contributor payouts — none of which belong inside content-addressed building objects.

## Decision

### 1. Permanent plane split

| Plane | Responsibility | Location |
|-------|----------------|----------|
| **Data plane** | Content-addressed spatial data, capture, roots, spatial index, peer sync, IFC/USD gateways, **contributor scoring (deterministic, offline-replayable)** | Rust crates: `arxos-core`, networking, gateways, CLI, edge, iOS/FFI |
| **Control plane** | Human/org accounts, KYC/tax hooks, entitlements, API keys, metering, buyer fiat billing, **points ledger, fiat payout batches** | Separate commercial service (not the object CAS) |

### 2. What never enters the CID / object graph

- Money amounts, invoices, or payment provider IDs  
- KYC / tax profiles or payout methods  
- Subscription tiers, API keys, or entitlement grants  
- Fiat conversion rates or payout batch records  

Scoring **reports** may be hashed and referenced by the control plane; financial state lives only in the control plane.

### 3. Pure-fiat economic model

- **Buyers** pay fiat for data access, APIs, certified datasets, and enterprise features.  
- **Contributors** submit real-world building/spatial data.  
- The **Oracle / scoring engine** (data plane) attributes work and produces **points** (and later multi-dimension scores).  
- **Fiat conversion** of points is ops-controlled via published rate tables and explicit **payout batches** in the control plane.  
- There is **no** token, mint, wallet settlement, EIP-712 reward path, treasury-in-token, or blockchain settlement of any kind.

### 4. Scoring rules (data plane)

- Scoring is a pure, deterministic function of `(store, root, policy_version)` (and fixed weights/policy tables for that version).  
- Oracle operation is centralized / Arxos-operated for now; results must remain offline-replayable.  
- Current type-count scoring is **diagnostic only** and **must not** be used as a payment basis until multi-signal scoring and a control-plane points ledger exist (see audit P1).  
- Core never auto-converts points to fiat.

### 5. Source of truth for building data

- Sole source of truth: **CAS + canonical CBOR objects** with BLAKE3 CIDs.  
- The historical YAML / Git building model is not restored as primary storage.  
- Export/import gateways (IFC, USD, future formats) project from CAS only.

### 6. Rejection of blockchain settlement

- EVM contracts are archived under `archive/contracts-evm-deprecated/` and are not part of the product or active build.  
- No dual-mode “optional blockchain” path.  
- Device ed25519 signatures remain for **data integrity and authorization**, not for token economics.

## Consequences

**Positive**

- Clear ownership boundaries; data plane stays deterministic and local-first.  
- Commercial stack can use ordinary SaaS patterns (accounts, Stripe, Postgres) without polluting CIDs.  
- Crypto residual risk is reduced by archival rather than dual support.

**Trade-offs**

- Control plane is net-new work (P1+).  
- Contributors need an account layer binding device keys to humans (control plane).  
- Scoring policy versioning and multi-dimension signals must land before any real payouts.

## Extension points (not implemented here)

- Versioned scoring policy tables  
- Multi-dimension `ScoreReport`  
- Control-plane points ledger interface (consumes score event hashes)

## References

- Full audit: [`FIAT_MODEL_AUDIT.md`](FIAT_MODEL_AUDIT.md)  
- Architecture overview: [`ARCHITECTURE.md`](ARCHITECTURE.md)
