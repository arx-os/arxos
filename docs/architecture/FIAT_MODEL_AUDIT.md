# Arxos Full Codebase Audit — Pure-Fiat Commercial Realignment

**Date:** 2026-08-04  
**Scope:** Entire current tree at `main` (post–greenfield Phase 0–5), plus git history of the pre-rewrite crypto economy.  
**Non-negotiable target:** Pure fiat commercial model — no tokens, minting, blockchain settlement, or $AXD economics.

> **P0 execution status (2026-08-04):** Course correction applied.
> - ADR-001 accepted and landed.
> - `contracts/` → `archive/contracts-evm-deprecated/`.
> - `core/src/depin` → `core/src/scoring` (registry snapshot removed).
> - CLI: `arx score` / `arx verify` / `arx attest` (no `depin`, no registry ABI).
> - Historical findings below remain valid as pre-P0 inventory; prefer ADR-001 + CHANGELOG for current tree.

---

## 0. Executive Summary

### What the codebase currently optimizes for

Arxos `main` is a **local-first, content-addressed spatial data repository** for the built environment. It is foundation-complete for:

| Strength | Reality |
|----------|---------|
| Deterministic CAS objects (BLAKE3 + CBOR) | Production-quality foundation |
| Signed delta roots + controller authorization | Fail-closed, well-tested |
| RoomPlan / capture → store → spatial query | Working capture loop |
| Multi-device sync (Iroh QUIC + mDNS) | Working LAN sync |
| IFC / OpenUSD gateways | Round-trip identity preserved |
| iOS UniFFI capture path | Real store only (shim deleted) |
| Edge packaging (Docker / systemd) | Thin admin/export binary |

It is **not** a commercial product platform. There is **no** buyer portal, API gateway, metering, billing, contributor accounts, KYC, or fiat payout ledger in the current tree.

### Critical historical context

Git history shows a **previous, much larger system** (pre–`ff55d505` greenfield rewrite) that implemented a full DePIN crypto economy:

- `$AXD` / `ArxosToken`, EIP-712 contribution proofs, multi-oracle consensus mint
- `ArxContributionOracle`, staking, disputes, payment router, buy-side `payForAccess`
- Web WASM/PWA (later purged), agent, Go-ish API layers in earlier eras
- Building YAML + quality scoring (`accuracy` / `completeness`) feeding mint amounts

That economy was **already largely deleted** by the greenfield rewrite (~20 commits on the new foundation). What remains is a **thin residual**:

1. `contracts/BuildingRegistry.sol` — minimal EVM registry (no mint/token)
2. `core/src/depin/` — count-weighted off-chain scoring + registry snapshot for on-chain handoff
3. CLI `arx depin …` surface and docs language that still assume DePIN / on-chain alignment
4. Schema docs promising “DID + on-chain registry (Base L2)”

**Honest assessment:** Realigning to pure fiat is **structurally easier than it would have been on the old tree**, because token mint, wallets, EIP-712, and payment routers are gone. The hard work is **building what never landed in the rewrite**: commercial access, identity, metering, billing, and a real Oracle → scoring → fiat-payout path.

### Gap vs. new target model

```
TARGET MODEL                              CURRENT TREE
─────────────────────────────────────     ────────────────────────────────────
Buyers pay fiat for data/API access  →    MISSING entirely
Contributors submit spatial data     →    PARTIAL (capture + CAS + iOS)
Oracle scores quality/depth/…        →    STUB (object-type weights only)
Contributors paid fiat by score      →    MISSING entirely
Revenue = buyer fiat − payouts       →    MISSING entirely
Identity / KYC / tax / settlement    →    MISSING (device ed25519 only)
Drop all crypto economics            →    NEARLY DONE (residual contracts + naming)
```

### Bottom line

- **Keep and strengthen** the CAS core, capture, sync, gateways, verification, attestation hooks.
- **Delete/archive** EVM contracts and on-chain handoff assumptions.
- **Refactor** `depin` → pure **Scoring Engine** (no registry/mint framing).
- **Build new** commercial control plane: accounts, access control, metering, buyer billing, contributor payout ledger.
- **Do not** resurrect the old Solidity tokenomics; harvest **quality-scoring ideas** from git history only.

---

## 1. High-Level Architecture Map

### 1.1 Current dependency graph

```
                    ┌─────────────┐
                    │  ios/ (Swift│
                    │  RoomPlan)  │
                    └──────┬──────┘
                           │ UniFFI
                    ┌──────▼──────┐
   cli/ ───────────►│ arxos-core  │◄──── ffi/
   edge/ ──────────►│  (CAS, root,│
                    │   spatial,  │
                    │   depin,    │
                    │   attest,   │
                    │   verify)   │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
   arxos-networking   arxos-usd       arxos-ifc
   (Iroh sync)        (OpenUSD)       (IFC4 STEP)
           │
           └──── used by cli `net serve`

   contracts/  ── orphan (Solidity; not linked to Rust workspace)
```

### 1.2 Module inventory & classification

| Component | LOC (approx) | Current purpose | Classification |
|-----------|-------------:|-----------------|----------------|
| `core/` — object, store, root, repository | ~4.5k | CAS, versioned building state | **Keep / strengthen** |
| `core/spatial` | ~1k | R-tree spatial index | **Keep / strengthen** |
| `core/capture` | ~0.4k | RoomPlan matrix → objects | **Keep / strengthen** |
| `core/crypto` | ~0.2k | ed25519 device/author keys | **Keep** (integrity, not tokens) |
| `core/verify` | ~0.3k | Canonicalization / root transition checks | **Keep / strengthen** |
| `core/attest` | ~0.4k | App Attest / mock provenance | **Keep** (contributor trust signal) |
| `core/depin` | ~0.3k | Contribution scoring + registry snapshot | **Refactor heavily** → Scoring |
| `core/merge` | ~0.3k | Concurrent root merge | **Keep** |
| `networking/` | ~1.6k | Peer sync of CAS closures | **Keep** (contributor multi-device); not buyer delivery |
| `gateways/usd`, `gateways/ifc` | ~2.2k | CAD interop export/import | **Keep / strengthen** (buyer deliverable formats) |
| `cli/` | ~1.7k monofile | Admin, capture, net, depin | **Refactor** (split; rename depin) |
| `edge/` | ~0.1k | Site export/admin daemon | **Keep** (thin); expand later for edge scoring |
| `ffi/` + `ios/` | ~1k Rust + ~4k Swift | Mobile capture | **Keep / strengthen** |
| `contracts/` | ~140 sol | EVM BuildingRegistry | **Deprecate / remove** |
| Buyer portal / API / metering / billing | 0 | — | **New capability required** |
| Contributor accounts / KYC / fiat payout | 0 | — | **New capability required** |
| Real quality Oracle (depth, multi-source, …) | 0 | type-count weights only | **New capability required** |

### 1.3 What is *not* in the tree (user expectations vs reality)

These appear in product vision / old commits / audit brief, but **do not exist on `main`**:

- YAML building model / Git-based versioning of buildings (old tree had `building.yaml`; current is CBOR CAS only)
- Interactive PWA / WASM visualizer (explicitly purged, Decision 9)
- Agent daemon / field RPCs / lidar.import agent path (pre-greenfield)
- Token, mint, EIP-712, treasury, buy-and-burn, payment router
- Web portal, REST/GraphQL commercial API, API keys, quotas
- Stripe/ACH/wire payouts, tax forms, KYC
- Full hierarchical address / elec tree from old ADR work

**Assumption flagged:** Audit treats current `main` as source of truth. Recovering YAML/Git or agent layers is a product decision, not automatic.

---

## 2. Deep Dive by Key Area

### 2.1 Oracle / Contribution Scoring

**Location:** `core/src/depin/mod.rs`, CLI `arx depin score`

**What it does today:**

1. Materialize active objects under a root.
2. Attribute each object to `header.author` (or `"anonymous"`).
3. Apply fixed weights by `ObjectType` (annotation=1, space=3, point cloud=5, …).
4. Multiply by `signed_bonus` (1.25) if signature verifies.
5. Emit `ScoreReport` + per-author aggregates.

**What it does *not* do (vs. target Oracle):**

| Desired signal | Present? |
|----------------|----------|
| Depth / extensiveness of hierarchy | No (counts only) |
| Geometric quality / coverage | No |
| Multi-source confirmation | No |
| Human verification / review status | No (existed in old `quality.rs`) |
| Device attestation as score factor | Partial (attest exists; not in score formula) |
| Duplicate / overlap detection | No |
| Usefulness to buyers | No |
| Durable score ledger / points balance | No |
| Fiat conversion of score | No |
| Mint / token distribution | **No (good)** |

**Coupling to crypto:** Conceptual only. Module docs and `registry_snapshot` target on-chain handoff. Scoring math is pure Rust over the store — **easy to decouple**.

**Old system salvage (git, not tree):**

- `quality_from_building`: accuracy from validation + LiDAR review fraction; completeness from floors/rooms/equipment address fill.
- Contribution package: content hash + entity merkle + quality → commitment (was for EIP-712 mint).
- **Keep the scoring concepts; discard mint, wallets, 70/10/10/10 splits, dispute bonds.**

**Refactor target:**

```
core/src/scoring/          # rename from depin
  attribution.rs           # Contribution, author key
  weights.rs               # tunable ScoreWeights / policy version
  signals/                 # depth, coverage, attestation, review, multi-source
  report.rs                # ScoreReport (immutable, content-addressable later)
  ledger.rs                # (new crate or service) points accrual — NOT tokens

services/oracle/           # future: batch re-score, policy versioning
services/payout/           # fiat liabilities from score deltas
```

Scoring must remain **deterministic given (store, root, policy_version)** so audits and disputes are offline-replayable without blockchain.

---

### 2.2 Data Model & Persistence

**Model:** Building → Floor → Space (+ Equipment, System, Circuit, …) as typed `ObjectBody` variants in a **content-addressed file store** (Git-style fan-out by CID hex). Heads in `meta/buildings/<id>.cbor`.

| Concern | Verdict |
|---------|---------|
| Hierarchy types | **Keep** — schema already commercial-useful |
| CAS + delta roots + checkpoints | **Keep** — core moat |
| Spatial index | **Keep** |
| Determinism (CID, canon CBOR) | **Keep / improve** |
| Git-based YAML buildings | **Absent** — decide if buyers need YAML export as a product format |
| Token / on-chain settlement assumptions in objects | **None** in object bodies |
| `Building.controller_keys` | **Keep** as building write-auth; **not** buyer ACL |

**Persistence notes:**

- Local-first CAS is excellent for contributors and edge.
- Commercial product needs an additional **control-plane store** (Postgres or similar) for accounts, subscriptions, usage, payouts — **do not** force billing into the CAS.
- Separation of concerns: **Data plane** (CAS buildings) vs **Control plane** (identity, money, access).

---

### 2.3 Authentication, Identity & Contributor Accounts

| Layer | Today | Needed |
|-------|-------|--------|
| Device author | ed25519 seed in `keys/device.seed` | Keep for data integrity |
| Building write auth | `controller_keys` on Building object | Keep |
| App Attest | Provenance statements (mock + stub Apple path) | Strengthen for score trust |
| Human account | **None** | Email/OAuth/SSO account |
| KYC / tax profile | **None** | Status machine + document hooks |
| Payout method | **None** | ACH/wire/Stripe Connect etc. |
| Contributor balance | **None** | Points ledger + fiat liability ledger |

**Key design rule:** Map **many device keys → one contributor account**. Scores accrue to accounts; devices only prove contribution provenance.

---

### 2.4 Buyer / Consumer Access Layer

**Today:** CLI + local store + optional peer sync. Export USD/IFC to disk. No multi-tenant host, no API keys, no quotas.

**Distance to commercial access:** Far. Required building blocks:

1. Hosted **read API** over building datasets (query, export, stream).
2. **AuthN/AuthZ**: org, roles, API keys, building-level grants.
3. **Metering**: request count, bytes exported, spatial query volume, certified dataset downloads.
4. **Entitlements**: subscription tiers, enterprise contracts, trial.
5. **Delivery**: signed short-lived URLs or streaming with watermarking/audit log.

Edge nodes remain valuable for **on-site contributor** ops, not as the buyer marketplace.

---

### 2.5 Blockchain / Crypto / Token inventory

| Artifact | Status on main | Action |
|----------|----------------|--------|
| `ArxosToken`, PaymentRouter, ContributionOracle, staking, disputes | **Deleted** (pre-greenfield only) | Do not restore |
| `$AXD` access path, EIP-712, merkle mint | **Deleted** | Do not restore |
| `contracts/BuildingRegistry.sol` | Present, minimal | **Archive/remove** |
| `contracts/script/Deploy.s.sol` | Present | **Archive/remove** |
| `core/depin::registry_snapshot` | Present | Remove or repurpose as **catalog metadata** |
| CLI `arx depin registry --abi` | Present | Remove with contracts |
| Docs “on-chain / Base L2 / DePIN” | Present | Rewrite for fiat |
| `core/crypto` ed25519 | Present | **Keep** (signatures ≠ tokens) |
| Wallet / buy-and-burn / treasury in $AXD | Absent | N/A |

**Safe removal plan (when approved):**

1. Move `contracts/` → `archive/contracts-evm-deprecated/` or delete in a dedicated PR.
2. Rename `depin` → `scoring`; drop `RegistrySnapshot` or move to catalog service.
3. CLI: `arx score`, `arx verify`, `arx attest` (no `depin` namespace, no registry ABI).
4. Docs: remove Base L2 / token incentive language.
5. CI: ensure no Foundry job required for core product.

**Risk of removal:** Near zero for Rust product path (contracts not in workspace members).

---

### 2.6 Agent, Daemon, WebSocket, PWA, TUI, Render, Edge

| Surface | Current | Fiat-model role |
|---------|---------|-----------------|
| CLI `arx` | Primary admin tool | Keep; modularize; commercial admin later |
| Edge daemon | Export + list buildings | Keep for site ops; optional score worker |
| Networking sync | Contributor multi-device | Keep |
| iOS app | Capture | Keep; first-class contributor client |
| PWA / WASM | Purged | Do not restore as product core; optional marketing site only |
| Agent / field RPC | Not on main | Reintroduce only if field ops need thin peripheral (ADR 11 era) |
| TUI / 3D render | Not on main | Buyer visualization = separate product; not core CAS |
| WebSocket streams | Not on main | Future buyer streaming API |

---

### 2.7 Payment & Financial Primitives

**Exist today:** None (no Stripe, invoices, ledgers, tax).

**Required minimum viable commercial stack:**

```
┌──────────────┐     ┌────────────────┐     ┌─────────────────┐
│ Buyer Billing│     │ Access Control │     │ Usage Metering  │
│ (Stripe etc.)│────►│ Entitlements   │◄────│ Append-only log │
└──────────────┘     └───────┬────────┘     └─────────────────┘
                             │ grants
                             ▼
                     ┌───────────────┐
                     │ Data Plane API│──► CAS / exports
                     └───────────────┘

┌──────────────┐     ┌────────────────┐     ┌─────────────────┐
│ Scoring Engine│───►│ Points Ledger  │───►│ Payout Ledger   │
│ (Oracle)      │     │ (immutable)    │     │ (fiat liability)│
└──────────────┘     └────────────────┘     └────────┬────────┘
                                                     │
                                                     ▼
                                            Payment provider
                                            (ACH / Connect)
```

**Invariants (must test):**

- Points ledger append-only; score events reference `(root_cid, policy_version, report_hash)`.
- Fiat payout rows never invent points; always derived from ledger balances.
- Buyer usage events are immutable after commit; billing reconciliation is deterministic.
- No double-pay: payout batch idempotency keys.

---

### 2.8 Testing, Observability, Determinism

**Current (workspace):** ~63 tests, all green at audit time.

| Strength | Gap |
|----------|-----|
| CID property tests | No commercial API tests |
| Root auth fail-closed | No scoring policy versioning tests |
| Spatial query equivalence | No multi-source / quality signal tests |
| IFC/USD identity round-trip | No ledger double-entry tests |
| Sync closure fail-closed | No metering / quota enforcement tests |
| Scale tests (large buildings) | Limited CLI/edge coverage (0 CLI unit tests) |

**Preserve while changing economics:**

- Never put money math in the CAS object CID path.
- Version scoring policies; store `policy_version` on every score event.
- Keep `verify_root_transition` and canonicalization properties as regression gates.
- Add golden-file tests for score reports under fixed fixtures.

---

## 3. Risk & Technical Debt Assessment

| Risk | Severity | Notes |
|------|----------|-------|
| Product/docs still say DePIN / on-chain | Medium | Misaligns sales, hires, and contributors |
| Residual contracts invite re-expansion of crypto path | Medium | Delete to make “no crypto” irreversible |
| Scoring too naïve for real payouts | High if used for money | Must not pay fiat on type-counts alone |
| No control plane | High for commercial launch | Greenfield build required |
| CLI monofile (1.7k LOC) | Low–Med | Maintainability |
| Single-writer store, no flock | Med for multi-process edge | Already on engineering roadmap |
| Point clouds inline in objects | Med | Blob tiering needed for mobile/edge |
| Identity = device key only | High for KYC/payouts | Account layer mandatory |
| Over-engineering crypto *in current tree* | Low | Already stripped |
| Rebuilding old YAML monolith “just because” | High if done blindly | Prefer CAS + export adapters |

---

## 4. Proposed Target Architecture (Pure Fiat)

```
                         ┌────────────────────────────┐
                         │     Commercial Control     │
                         │  Accounts · Orgs · Roles   │
                         │  Subscriptions · Contracts │
                         │  API keys · Entitlements   │
                         │  Metering · Invoices (fiat)│
                         │  Points · Payout batches   │
                         └─────────────┬──────────────┘
                                       │ authz + usage
          Contributor                  │                  Buyer
          ┌──────────┐                 │                 ┌──────────┐
          │ iOS / CLI│                 │                 │ Portal / │
          │ Edge cap.│                 │                 │ API SDK  │
          └────┬─────┘                 │                 └────┬─────┘
               │ contribute            │                      │ consume
               ▼                       ▼                      ▼
          ┌─────────────────────────────────────────────────────────┐
          │                    Data Plane (arxos-core)              │
          │  CAS · Roots · Spatial · Capture · Gateways · Sync      │
          └───────────────────────────┬─────────────────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │   Scoring Engine      │
                          │   (Oracle, offline-   │
                          │    replayable)        │
                          └───────────────────────┘
```

**Principles:**

1. Data plane stays local-first, deterministic, crypto-signature-based for integrity.
2. Money never touches the object CID graph.
3. Scoring is pure functions + versioned policy; payouts are a separate ledger.
4. Buyers never need wallets; contributors never need tokens.
5. Prefer deletion of EVM path over dual-mode “optional blockchain.”

---

## 5. Concrete Oracle → Scoring + Fiat Payout Plan

### Phase A — Decouple (1–3 days)

1. Rename module `depin` → `scoring` (keep type aliases if needed for one release).
2. Remove `RegistrySnapshot` / CLI registry ABI (or quarantine behind `#[cfg(feature = "legacy-registry")]` only if migration needs it — default off).
3. Rename CLI `depin` → top-level `score` / `verify` / `attest`.
4. Rewrite module docs: “contributor scoring,” zero on-chain language.
5. Archive `contracts/`.

### Phase B — Real signals (1–2 weeks)

Extend `ScoreReport` with structured dimensions (all 0–100 or rational scores, versioned):

| Dimension | Initial heuristic (deterministic) |
|-----------|-----------------------------------|
| `volume` | Weighted object counts (current) |
| `structure_depth` | Floors/spaces/equipment graph depth & fill |
| `coverage` | Spatial bounds coverage vs building AABB (when available) |
| `integrity` | Signature validity + attestation present |
| `freshness` | Recency of contribution relative to building activity |
| `review` | Human accept/reject once review objects exist |
| `confirmation` | Overlap with independent authors (multi-source) |

Composite score = policy-weighted sum; store full vector, not just scalar.

### Phase C — Ledger (2–3 weeks)

New service crate or schema (Postgres recommended for control plane):

```sql
-- illustrative
score_events(id, account_id, building_id, root_cid, policy_version,
             report_hash, points_delta, created_at)
point_balances(account_id, balance, updated_at)
payout_batches(id, period_start, period_end, status, total_fiat_cents)
payout_lines(batch_id, account_id, points, fiat_cents, status, external_ref)
```

Conversion: periodic batch `points → fiat` under published rate tables (ops-controlled), never automatic mint.

### Phase D — Gamification hooks (later)

Ranks, streaks, badges as **views over** `score_events` — no new economic assumptions.

---

## 6. Prioritized Backlog

### P0 — Course correction & correctness (do first)

| ID | Work | Complexity | Notes |
|----|------|------------|-------|
| P0-1 | Publish this audit; product decision freeze on “no crypto” | S | Done (this doc) |
| P0-2 | Archive/remove `contracts/`; strip registry CLI + docs | S | Needs explicit OK |
| P0-3 | Rename `depin` → `scoring`; kill on-chain framing | S | Low risk |
| P0-4 | ADR: data plane vs control plane split | S | Architecture lock |
| P0-5 | Do **not** pay anyone from type-count scores | Policy | Safety |

### P1 — Commercial MVP spine

| ID | Work | Complexity |
|----|------|------------|
| P1-1 | Control-plane service skeleton (auth accounts, orgs) | L |
| P1-2 | Contributor account ↔ device key binding | M |
| P1-3 | Scoring policy v1 with multi-dimension signals | M |
| P1-4 | Points ledger + immutable score events | M |
| P1-5 | Hosted read API + API keys + basic metering | L |
| P1-6 | Buyer subscription / entitlement check on API | M |
| P1-7 | Fiat billing integration (Stripe or equivalent) for buyers | M |
| P1-8 | Payout batch job + admin review (manual ACH first OK) | M |
| P1-9 | KYC/tax profile fields + export hooks (1099 etc.) | M |

### P2 — Product hardening

| ID | Work | Complexity |
|----|------|------------|
| P2-1 | Blob tiering for point clouds / meshes | M |
| P2-2 | Store single-writer lock / edge exclusive writer | M |
| P2-3 | CLI modularization | S |
| P2-4 | Structured core errors for UniFFI | S |
| P2-5 | Human review workflow objects (proposed/accepted) | M |
| P2-6 | Multi-source confirmation scoring | M |
| P2-7 | Buyer portal UI | L |
| P2-8 | Certified dataset packaging + watermarking | M |
| P2-9 | Gamification: ranks, leaderboards, streaks | M |
| P2-10 | Controller rotation / multi-device policy | M |

---

## 7. Delete / Archive List

**Immediate candidates (high confidence):**

| Path | Action |
|------|--------|
| `contracts/` entire tree | Archive or delete |
| `core/src/depin` name + registry snapshot | Rename/refactor |
| CLI `DepinCommands::Registry` + `--abi` | Delete |
| Docs references to DePIN, Base L2 registry, token incentives | Rewrite |
| README item “On-chain / off-chain alignment” | Remove |

**Do not delete:**

| Path | Why |
|------|-----|
| `core/src/crypto` | Integrity signatures |
| `core/src/attest` | Trust for scoring |
| `core/src/verify` | Safety properties |
| `networking` | Contributor sync |
| Gateways | Buyer export formats |

**Historical salvage only (git archaeology, not restore as-is):**

- `src/contribution/quality.rs` — quality heuristics
- `docs/contribution-path.md` / `docs/data-access.md` — product flows (rewrite without token)
- Old Foundry E2E tests — **do not** reintroduce; use as threat model for what *not* to rebuild

---

## 8. Immediate Safe Changes (this pass)

Applied or recommended without large destructive moves:

1. **This audit document** under `docs/architecture/FIAT_MODEL_AUDIT.md`.
2. **Soft-deprecate** `contracts/` via README banner (no file deletion without confirmation).
3. **Reframe** `core/src/depin` module docs toward pure scoring / fiat payout (no on-chain rewards language).

**Not done without confirmation:** deleting `contracts/`, renaming public module `depin`, breaking CLI flags.

---

## 9. Open Questions (need human input)

1. **Contracts:** Delete entirely, or move to `archive/` for historical reference?
2. **Control plane language/stack:** Rust service in monorepo vs separate TypeScript/Go service?
3. **Payment provider:** Stripe (incl. Connect for payouts) vs bank ops-only MVP?
4. **YAML/Git buildings:** Permanently retire in favor of CAS+CBOR, or support YAML as export/import gateway only?
5. **Who runs the Oracle?** Centralized Arxos ops only, or multi-party review later (still off-chain)?
6. **Score → fiat rate:** Fixed published schedule, market-based budget pool, or per-building bounty?
7. **Buyer data residency / multi-tenant isolation:** Single global CAS mirror, or per-customer silos?
8. **iOS App Attest production verification:** Priority for payout eligibility?
9. **Recover agent/field client** from pre-greenfield, or re-spec from scratch?

---

## 10. Dependency on Engineering Principles (compliance check)

| Principle | Audit compliance |
|-----------|------------------|
| Prefer deletion over clever abstraction for crypto | Yes — delete contracts, don’t dual-mode |
| Maintain determinism / auditability | Scoring must stay pure + versioned |
| Local-first / edge where valuable | Keep CAS + edge + iOS |
| Separate scoring / commercial / payout | Explicit control plane |
| Gamification without crypto | Points ledger, not tokens |
| Security first on verification & money | Don’t pay on naïve scores |
| Commercial access first-class | P1 new work |
| Avoid premature optimization | Simple Stripe + Postgres OK for MVP |
| Document decisions | This doc + follow-up ADR |

---

## 11. Suggested First Implementation PR Sequence

```
PR1  docs: fiat model audit + ADR data/control plane   (this)
PR2  chore: archive contracts + strip registry CLI
PR3  refactor: depin → scoring (API rename, tests)
PR4  feat(scoring): multi-dimension ScoreReport v1
PR5  feat(control-plane): accounts + device binding (skeleton)
PR6  feat(api): read access + API keys + usage events
PR7  feat(ledger): points events + balances
PR8  feat(billing): buyer subscriptions (provider)
PR9  feat(payout): batch fiat liabilities + export
```

---

## 12. Summary Judgment

Arxos has a **strong, honest data foundation** and has already escaped most of the crypto complexity through a greenfield rewrite. The residual DePIN surface is thin and should be removed cleanly. The pure-fiat model is **not a refactor of mint contracts** — it is a **new commercial control plane** sitting beside a preserved spatial data plane, with the Oracle evolved into a **deterministic scoring engine** that feeds a **fiat points/payout ledger**.

Until scoring is multi-signal and ledgers exist, treat current `arx depin score` as a **diagnostic tool only**, never as a payment basis.

---

*End of audit.*
