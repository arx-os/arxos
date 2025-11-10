# ArxOS Economy Guide

This document describes the on-chain economy layer introduced in this iteration of ArxOS. It covers the Rust service architecture, smart-contract toolchain, CLI integration, mobile FFI surfaces, and operational playbooks for configuration, testing, and automation.

## Overview

The economy layer enables on-chain minting, staking, revenue distribution, and reporting workflows that complement the Git-first building management workflow. The implementation spans:

- A Hardhat-based contract suite for `ArxosToken`, `ArxStaking`, `RevenueSplitter`, `TaxOracle`, and supporting mocks.
- New Rust economy services (`crates/arxos/src/economy`) that wrap Polygon RPC access, Chainlink oracle calls, IPFS/Ocean integrations, and mobile-friendly workflows.
- Domain models (`crates/arx/src/domain/economy.rs`) and persistence helpers for Git-native economic ledgers.
- CLI and mobile bindings to expose staking/rewards functionality for operators in the field.
- Observability hooks and tests to validate the flow end-to-end.

## Smart Contract Tooling (`contracts/`)

- Node toolchain defined via `contracts/package.json` (Hardhat + TypeScript + OpenZeppelin + Chainlink + Uniswap).
- `hardhat.config.ts` provides polygon-amoy/mumbai defaults with runtime env overrides (`POLYGON_MUMBAI_RPC_URL`, `PRIVATE_KEY`, etc.).
- Contracts live under `contracts/contracts/…` with mocks for local testing.
- Tests in `contracts/test/arxos.spec.ts` validate minting, staking, and revenue splitting with deterministic mocks.
- Deployment script `contracts/scripts/deploy.ts` wires token, staking, splitter, and oracle contracts with environment-configurable addresses.
- Runbook:
  ```bash
  cd contracts
  npm install
  npm test
  npx hardhat compile
  npx hardhat run --network polygonMumbai scripts/deploy.ts
  ```

## Rust Economy Services (`crates/arxos/src/economy`)

- `EconomyConfig::from_env` reads required configuration:
  - `ARXO_POLYGON_RPC` / `ARXO_POLYGON_CHAIN_ID`
  - Wallet keys: `ARXO_WALLET_PRIVATE_KEY`, `ARXO_WALLET_SENDER`
  - Contract addresses: `ARXO_CONTRACT_TOKEN`, `ARXO_CONTRACT_STAKING`, `ARXO_CONTRACT_REVENUE`, `ARXO_CONTRACT_ORACLE`, optional `ARXO_CONTRACT_USDC`, `ARXO_CONTRACT_LINK`, `ARXO_CONTRACT_ROUTER`
  - Optional services: `ARXO_IPFS_*`, `ARXO_OCEAN_*`
- `ArxoEconomyService` offers async APIs for verification, staking, revenue splits, dataset publishing, and balance queries. Each entry point is instrumented with `tracing::instrument`.
- Helper clients (`token.rs`, `staking.rs`, `revenue.rs`, `oracle.rs`) rely on `ethers` bindings with deterministic ABIs generated via `abigen!`.
- IPFS and Ocean clients expose trait-based abstractions (`GatewayIpfsClient`, `OceanProtocolClient`) so mobile/CLI workflows can plug in alternative gateways.

## Domain & Persistence (`crates/arx`)

- `domain::economy` defines:
  - `Money` (cents + currency)
  - `BuildingValuation`, `ContributionRecord`, `RevenuePayout`, `EconomySnapshot`
- `persistence::economy` implements Git-native storage:
  - `.arxos/economy/snapshot.yaml` for valuations, contributions, revenue history.
  - `.arxos/economy/contributions.yaml` ledger maintained via `append_contribution`.
- Tests (`persistence::economy::tests`) validate round-trips and ledger append semantics using `tempfile` sandboxes.

## CLI & TUI Integration (`crates/arxui`)

- New `Economy` command group with subcommands:
  - `arx economy verify --property-id P123 --recipient 0x… --tax-value 1250000`
  - `arx economy stake --amount 100.5`
  - `arx economy unstake --amount 25`
  - `arx economy claim`
  - `arx economy rewards [--address 0x…]`
  - `arx economy distribute --usdc-amount 1200`
  - `arx economy publish --name dataset --payload payload.json [--metadata meta.json]`
  - `arx economy balance [--address 0x…]`
  - `arx economy total-value`
  - `arx economy show-config`
- `commands/economy.rs` uses `tokio::runtime::Builder::new_multi_thread()` to orchestrate async calls without requiring a global runtime.
- `arxui/Cargo.toml` enables the `economy` feature by default, pulling in Tokio and ethers.

## Mobile FFI Surfaces (`crates/arxos/src/mobile_ffi`)

- New APIs exposed for iOS/Android:
  - `arxos_economy_snapshot(address?)`
  - `arxos_economy_stake(amount)`
  - `arxos_economy_unstake(amount)`
  - `arxos_economy_claim()`
- `mobile_ffi::economy_account_snapshot` et al. share parsing helpers and are instrumented with tracing.
- iOS (`ios/ArxOSMobile/.../ArxOSCoreFFI.swift`):
  - Adds `_silgen_name` imports.
  - Provides async-friendly wrappers returning `EconomySnapshot`.
  - Includes stake/unstake/claim wrappers and JSON decoding types.
- Android (`android/app/.../ArxOSCoreJNI.kt` + `ArxOSCoreService.kt`):
  - Declares new JNI externals.
  - Wrapper methods parse JSON responses into `EconomySnapshot`.
  - Service layer exposes coroutine-based helpers for app view models.
- Update bridging header via:
  ```bash
  cbindgen --config cbindgen.toml --crate arxos --output include/arxos_mobile.h
  ```

## Testing & Observability

- Rust unit tests:
  ```bash
  cargo test -p arx
  cargo test -p arxos --features "std,economy"
  ```
- Contract tests: `npm test` in `contracts/`.
- Hardhat compile: `npx hardhat compile`.
- CLI smoke tests: `cargo run -p arxui -- economy show-config`.
- Observability:
  - `tracing` instrumentation on economy service methods, mobile FFI helpers, and CLI commands.
  - Use `RUST_LOG=info` or `RUST_LOG=debug` with `arx` CLI to inspect spans.
  - Runtime warnings will list economy operations with span IDs, aiding distributed tracing back to Polygon/Chainlink transactions.

## CI/CD Notes

- Ensure CI pipeline installs Node dependencies under `contracts/` and runs `npm test`.
- Add `cbindgen` step in build pipelines whenever the FFI surface changes.
- Economic tests require the `economy` feature; update build matrix to run `cargo test -p arxos --features "std,economy"` in addition to existing test jobs.
- Environment secrets:
  - RPC endpoint: `ARXO_POLYGON_RPC`
  - Wallet private key: `ARXO_WALLET_PRIVATE_KEY`
  - Contract addresses: `ARXO_CONTRACT_*`
  - Optional integration secrets for IPFS/Ocean.

## Quick Reference

| Component | Path/Command |
|-----------|--------------|
| Contracts | `contracts/` (`npm test`, `npx hardhat compile`) |
| Economy services | `crates/arxos/src/economy/` |
| Domain models | `crates/arx/src/domain/economy.rs` |
| Persistence | `crates/arx/src/persistence/economy.rs` |
| CLI commands | `arx economy ...` |
| iOS bindings | `ios/ArxOSMobile/ArxOSMobile/Services/ArxOSCoreFFI.swift` |
| Android bindings | `android/app/src/main/java/com/arxos/mobile/service/ArxOSCoreJNI.kt` |
| Tests | `cargo test -p arx`, `cargo test -p arxos --features "std,economy"`, `npm test` |
| Generated header | `include/arxos_mobile.h` (via `cbindgen`) |

For detailed API discussions see `economy.md` (planning doc) and the code references above.

