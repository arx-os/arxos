# Changelog

## Unreleased

### Security / fail-closed

- In-process exclusive store lock (two handles / threads in one process fail closed).
- Decode rejects frames with length prefix > 64 MiB; serve refuses closures that
  would exceed the frame cap.
- `DefaultAttestationVerifier` rejects Mock outside tests; `arx attest` is labeled diagnostic.

- iOS UDL no longer exports `put_blob`, seed `generate_keypair`, `create_root`,
  or `allow_untrusted` pull.
- mDNS TXT no longer carries dial tickets (copy `ticket=` from serve stdout).
- `arx verify` uses a frozen `RootClosure`; `merge plan` uses `open_read`.
- Score JSON includes `diagnostic_only: true`. LICENSE-APACHE added for dual license.

- Merge LCA/fast-forward walk `previous_root ∪ merge_parents` (no deleted-CID
  resurrection across merge commits). Pose-less annotations are not deduped at
  the origin.
- `Object::sign` / `verify_signature` fail on Root objects.
- Continuity hop bound and missing-parent walks have tests.

- CAS `atomic_write` fsyncs the file and parent directory; leftover `*.tmp*`
  objects are GC'd on open; corrupt CID slots are replaced on put.
- First-contact TOFU can be pinned with `--trust-controllers` /
  `AdoptOptions.expected_controllers`.
- Extra unauthorized co-author on a Root is rejected (test).
- `schema_version` must equal `SCHEMA_VERSION` (currently 1).
- iOS controller seed is Keychain-backed; init does not persist `keys/device.seed`
  when a process seed is set; store export omits `keys/`.

- Merge of a remote parent whose authors are not local controllers is rejected
  (Authorization). Untrusted objects cannot enter official history.
- `--metadata-only` cannot adopt as head (`--no-set-head` required).
- `--allow-untrusted` help states that it skips Root-law/continuity and will set head.
- Unsigned IFC/USD import is refused; import requires `keys/device.seed`.
- Iroh serve uses `N0DisableRelay` (no public relays). `GetObject`/`GetRootClosure`
  are scoped to advertised head closures. Inbound `AnnounceRoot` is ignored.
- iOS store moved to Application Support and excluded from backup.
- FFI `pull_remote_root(..., allow_untrusted=true)` hard-fails; `put_blob` is
  unavailable on iOS.
- systemd unit runs `arxos-edge serve`; Docker runs as non-root.

### Build

- Workspace `rust-version` is 1.91 (iroh 1.1 MSRV). `tinyvec` pinned to 1.12.0.
- CI: `--locked` tests for core, gateways, networking, cli, workspace.

### Honesty

- IFC `FILE_DESCRIPTION` is `ViewDefinition [ArxosAsBuiltView]`, not CoordinationView.

### Removed

- Deleted the experimental commercial control-plane service and its documentation
  (including the long-form fiat-model audit that prescribed SaaS ledgers/accounts).
- Experimental EVM contracts were removed from this tree (they are not built).

### Breaking (retained)

- CLI: `arx score` / `arx verify` / `arx attest` (no `arx depin`).
- Core: `arxos_core::scoring` (formerly `depin`); no registry/on-chain handoff types.
- `ScoreReport` includes `policy_version` (default `1`).

### Changed

- Economic model: DePIN contribution → scoring; **fiat** settlement (not tokens).
  Public product identity and architecture live in the root `README.md` only.
- Design notes / ADRs are local-only (`docs/` gitignored); not part of the public tree.

### Notes

- Scoring is **diagnostic only** (type-count weights) until multi-signal quality
  scoring is intentional product work.
