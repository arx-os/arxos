# Engineering Safety Profile (Power of Ten applied to ArxOS)

This document adapts Gerard Holzmann’s “Power of Ten” rules (for safety‑critical C) to ArxOS in Rust. The goal is to keep RF/control‑path code simple, bounded, and analyzable, while keeping the rest of the system pragmatic.

## Scope
- Applies strictly to RF/control surfaces:
  - `src/core/radio/*` (framing, sealed frames)
  - `src/core/security/*` (MAC, anti‑replay)
  - `src/core/meshtastic_protocol.rs` (packet model)
  - Future BAS/BMS supervisory modules
- Recommended (but not mandatory) elsewhere.

## Principles (Rust‑adapted)
1) Simple control flow; no recursion in RF/control paths
- Ban recursion; prefer explicit loops and state machines.
- Multiple early returns are fine if they reduce nesting.

2) Bounded loops
- Loops must have clear, small upper bounds (e.g., by slice length, MTU math).
- Avoid unbounded `while` in control surfaces; prefer `for` over known ranges.

3) No dynamic allocation in hot/control paths
- Avoid heap allocation on packet hot paths; preallocate small buffers.
- Use stack or fixed‑capacity (e.g., arrayvec) where reasonable.

4) Small functions and tight scope
- Keep RF/control functions roughly ≤60 lines; split if larger.
- Minimize variable scope and reuse.

5) Assertions and recovery
- Use `debug_assert!` for invariants; use Result for recoverable errors.
- Validate inputs at module boundaries and return structured errors.

6) Return/parameter validation
- Check all Results; avoid `unwrap()`/`expect()` in non‑test code.
- Validate inputs at public APIs; document assumptions.

7) Macro hygiene and features
- Keep macros simple; no token pasting; avoid deep conditional compilation.
- Prefer feature flags (`rf_only`, `mobile_offline`, `internet_touchpoints`) over macro logic.

8) Pointer/unsafe restrictions
- `#![forbid(unsafe_code)]` in core crates; prefer safe APIs.
- No transmute; explicit `to_le_bytes`/`from_le_bytes`.

9) Zero warnings, strong linting, static checks
- Treat warnings as errors; enable Clippy (pedantic); run cargo‑audit/deny.
- Consider `proptest`/fuzz for serialization and framing.

10) Testability & determinism
- Deterministic helpers for nonce/seed in tests.
- Golden vectors for wire format (see `docs/technical/ARXOBJECT_WIRE_FORMAT.md`).

## Implementation Plan

Phase A: Controls & Linting
- Add crate headers: `#![forbid(unsafe_code)]` to `src/core` and RF/control submodules.
- CI posture: `-D warnings`, Clippy pedantic, cargo‑audit/deny.
- Sweep for `unwrap`/`expect` in core paths; replace with Result handling.

Phase B: Bounded & allocation‑light paths
- Audit `radio::frame`, `radio::secure_frame`, `radio_adapter`, `meshtastic_protocol` for bounded loops and remove incidental heap allocations in hot paths.
- Introduce small fixed‑capacity buffers where beneficial.

Phase C: Assertions & tests
- Add `debug_assert!` for framing invariants (header sizes, MAC/tag lengths, object counts).
- Property tests for `ArxObject` round‑trip and frame pack/unpack; reuse golden vectors.

Phase D: BAS/BMS supervisory profile
- Establish a `safety` module template for local PI control with:
  - no recursion, bounded loops, no allocation in loops
  - explicit TTLs/timeouts and recovery paths
- Document SLOs and acceptance criteria.

Deliverables
- Updated lint/CI config, crate attributes, and targeted code sweeps (A/B).
- Added assertions/property tests (C).
- BAS/BMS safety template and doc stubs (D).

## References
- Power of Ten (Holzmann): `powerof10.txt`
- Wire Format: `docs/technical/ARXOBJECT_WIRE_FORMAT.md`
- Latency: `docs/LATENCY_ESTIMATES.md`
- Feature Flags: `docs/FEATURE_FLAGS.md`
