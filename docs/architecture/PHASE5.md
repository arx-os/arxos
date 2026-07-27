# Phase 5 — DePIN & Hardening

**Status:** Implemented (foundation, 2026-07-27) — ongoing by nature

## Goals

* App Attest integration (hooks + mock; structural App Attest verifier)
* Minimal Building registry contract (Base L2)
* Contribution attribution and off-chain scoring
* Verification of canonicalization and root transitions
* Edge node packaging (Docker + systemd, Pi-class)

## Design principles

1. **Signed contributions first.** Roots and important objects already carry ed25519 authors.
2. **Attestation is provenance.** Device statements become CAS `Provenance` objects.
3. **Score off-chain first.** Deterministic `ScoreReport` can later drive on-chain rewards.
4. **Minimal on-chain surface.** Registry = `BuildingId → officialRoot + controllers` only.
5. **Any node can verify.** `verify_root_transition` needs only the CAS.

## Core modules

| Module | Role |
|--------|------|
| `attest` | App Attest / mock statements + verifiers |
| `depin` | Attribution, scoring, registry snapshots |
| `verify` | Canonicalization + root chain checks |

## CLI

```bash
arx depin score $BID [--root CID] [--json]
arx depin verify $ROOT_CID [--json]
arx depin attest $ROOT_CID --device-id mock-1
arx depin registry $BID [--abi]   # JSON + optional bytes32 digests
```

## Contracts

`contracts/BuildingRegistry.sol` — EVM registry for Base.

CID encoding: raw 32-byte BLAKE3 (no `b3:` prefix).  
BuildingId on-chain: `bytes32(blake3(building_id_utf8))` (CLI `--abi` helper).

## Edge packaging

* `edge/Dockerfile` — multi-arch image with `arx` + `arxos-edge`
* `edge/systemd/arxos-edge.service` — net serve under systemd
* `edge/scripts/install-edge.sh` — install binaries (+ optional unit)

## App Attest

* Rust: `AttestationStatement::app_attest` + `AppAttestVerifier` (structural)
* Swift: `AppAttestClient` mock + `DCAppAttestService` wrappers when available
* **Production** must complete Apple certificate chain verification server-side

## Tests

* `attest` mock / structural App Attest
* `depin` scoring + registry snapshot
* `verify` root transition
* Property: random blob canon verify

## Ongoing

* Full App Attest chain verify + challenge binding
* On-chain rewards / staking
* Formal proofs (Lean/Kani) of transition rules
* Pi image CI builds
