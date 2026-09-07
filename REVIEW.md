# Arxos engineering review

Checkout: `/Users/joelpate/repos/arxos` on `main` (dirty `Cargo.lock` only). No source was edited. Graphify was used as an index; every finding below is from types, constructors, verify paths, and tests.

**Verdict for a founding engineer:** Core adopt/commit is load-bearing and, after first contact, fail-closed against Mallory forks. Do not trust a second replica or a phone scan as production history until the items in “Do not ship until” are closed. The store contract is real in `BuildingRepository`. The LAN product around it is a capability-ticket CAS oracle on Iroh’s public-relay preset, and merge will ingest untrusted non-Building objects.

---

## Commands run (this machine)

| Command | Outcome |
|---|---|
| `rustc --version` | rustc 1.96.0 (ac68faa20 2026-05-25) |
| `cargo test --workspace` (via tee, no pipefail) | Compile fail in tinyvec 1.13.0 (`vec!` macro vs `alloc::vec` module). Wrapper printed EXIT:0 because tee succeeded. Real cargo status is failure. |
| `cargo test -p arxos-core --offline` | ok. Lib 103 passed; multi_device 5; property_cid 3; scale_large 1; spatial_props 3; spatial_scale 1; verify_props 2. |
| `cargo test -p arxos-ifc --offline` | ok (unit + `ifc_roundtrip_identity`) |
| `cargo test -p arxos-usd --offline` | ok (`usd_roundtrip_identity`) |
| `cargo test -p arxos-ffi --offline --lib` | fail — same tinyvec 1.13.0 |
| `cargo clippy -p arxos-core --all-targets -- -D warnings` | fail (8 errors: unused imports, needless_borrow, `suspicious_open_options` on `store.lock` open) |
| `cargo test -p arxos-cli`, `arxos-networking`, `iroh_two_node` | not run — blocked by tinyvec |

Cause of workspace break: uncommitted `Cargo.lock` bump tinyvec 1.12.0 → 1.13.0. HEAD still pins 1.12.0. The lockfile was not reverted during this review.

Not run: Xcode, physical iPhone, NFS/Docker flock, Windows rename. Those are labeled unverified.

---

## 1. System map

```
                    ┌─────────────────────────────────────────┐
 Trust boundary     │  Building.controller_keys (ed25519)     │
 (heads)            │  RootBody.authors all-must-verify AND   │
                    │  all-must-be-controllers                │
                    └─────────────────────────────────────────┘
                                      │
     capture/commit/adopt/merge       │        derived readers
     BuildingRepository               │        ObjectRead / RootClosure
     (exclusive store.lock)           │        open_read: no flock
                                      │
 ┌────────────┐  put/get   ┌──────────────────┐  get_bytes   ┌─────────────┐
 │ CLI / FFI  │───────────▶│ ObjectStore CAS  │◀─────────────│ Iroh serve  │
 │ edge serve │            │ objects/<ab>/…   │              │ GetObject   │
 └────────────┘            │ meta/buildings/  │              │ GetRootCl.  │
                           │ keys/device.seed │              └──────┬──────┘
                           └──────────────────┘                     │
                                                                    │
                         USD/IFC export ◀── open_read               │
                         USD/IFC import ──▶ open_or_follow + adopt  │
                                                                    │
                         iOS Documents/arxos-store ── FFI ──────────┘
                         (UI does not call pull; UDL still exports it)
```

Write paths (must hold `store.lock`): `BuildingRepository::{init,open,open_or_follow}` → capture → stage → commit (`verify_with_store` only) → `put(root)` then `write_record(head)`. Ingest: `put_object_bytes` → `adopt_root`. Merge: `merge_root` → `merge_roots_with_replica` → `adopt_root`. Edge/arx net serve: lock for process lifetime, then Iroh accept loop.

Read paths: `open_read`, `RootClosure`/`ClosureView`, score/verify/export/spatial query. Documented TOCTOU: head file and object files are each atomic; a racing commit can leave a reader with a slightly stale head.

Trust boundaries:

- CAS bytes: BLAKE3 of canonical CBOR. No encryption. Anyone with a dial ticket can fetch.
- Head: controllers on the replica’s current Building + ancestry (`previous_root` / `merge_parents`).
- First `head_root == None`: TOFU after self-consistency.
- `allow_untrusted`: skips both checks and still sets head.

---

## 2. Invariant table

| Invariant | Documented | Enforced | Tested |
|---|---|---|---|
| CAS purity (`ObjectStore` = has/get/put) | yes (`core/README.md`) | mostly; `list_cids`/`rebuild_index` live on `ObjectStore` | index-not-on-put yes |
| Single domain writer | yes | core yes; FFI `put_blob`, CLI object put, serve path raw `ObjectStore` | lock cross-process yes |
| Derived layers are readers | yes | score/export/query take `ObjectRead`; `arx verify`/`merge plan` still `ObjectStore::open` | partial |
| Leaf sign header; CID includes sig | yes | `Object::sign` / `cid()` | roundtrip; no “CID changes after sign” assert |
| Root sign `body.authors`; header sig blank | yes | `RootBody::into_object` | `root_sign_verify`; no test that `Object::verify_signature` on a Root fails |
| Local commit = `verify_with_store` only | yes | `commit.rs` | e2e + repo tests |
| Production adopt = self-consistency + continuity | yes | `adopt_root_with_options` unless `allow_untrusted` | mallory fork, second genesis, descendant, `merge_parents` claim |
| First contact TOFU | yes | `local_head == None` → `FirstTrust` | `adopt_first_contact_tofu_succeeds` |
| Second genesis rejected | yes | checkpoint ∧ `previous_root=None` vs existing head | `continuity_rejects_second_genesis_against_existing_head` |
| `allow_untrusted` not fetch default | yes | CLI default false | clap tests + mallory pull |
| `created` not newest-wins for authority | yes (I3/I8) | continuity ignores `created`; entity/Building collapse and annotation dedupe use it | mallory Building cannot win; entity collapse tests |
| `MergeReplica`: untrusted Building cannot win | yes | domain `merge_root` yes; public `merge_roots` no replica | `merge_untrusted_newer_building_cannot_win` |
| Untrusted objects cannot enter merge | not documented as such | not enforced | missing (see ARX-007) |
| 4 MiB object cap | yes | `put`/`put_bytes` both backends | oversized put |
| Canonical wire on ingest | yes | `put_bytes` re-encode equality | non-canonical wire + signed zero |
| `from_cbor` rejects non-canonical | implied by “canonical CBOR” | no — raw ciborium | only via `put_bytes` |
| Serve only advertised buildings | implied by Hello ads | no | missing |
| LAN-only sync | README | no — `presets::N0` + relay in ticket | missing |
| IFC is not CoordinationView | README | file header claims it is | roundtrip does not assert MVD |
| App Attest verified | comments | structural `valid: true`; iOS never records | mock/structural unit tests |
| Seed file 0600 | yes | Unix `OpenOptionsExt`; no Windows ACL | Unix mode tests |

---

## 3. Findings

### ARX-001

- **Severity:** P1
- **Area:** H
- **Title:** Sync server is an unauthenticated CAS oracle (any CID, any building)
- **Evidence:** `IrohNode::handle_message` (`networking/src/iroh_node.rs`) dispatches `GetObject` / `GetRootClosure` to `serve_get_object` / `serve_root_closure_with_options` (`networking/src/sync.rs`), which `ObjectStore::open` + `get_bytes` with no check that the CID is in advertised heads. `include_blobs` defaults true.
- **Invariant violated:** Hello advertisements vs actual access; building-scoped sync.
- **How to reproduce:** Two buildings in one store; serve; `GetObject` for a CID from the non-advertised building (or any historical Root). Sketch: extend `iroh_two_node.rs`.
- **Blast radius:** Every object in that store (blobs, annotations, other sites) to anyone who can dial. Pullers still hash-check bytes; this is confidentiality/ACL, not CID-poison.
- **Recommended fix:** Serve through `BuildingRepository::open_read` (or a grant of advertised Root closures only). Reject `GetObject` unless CID ∈ closure of an advertised head.
- **Confidence:** high

### ARX-002

- **Severity:** P1
- **Area:** H / P
- **Title:** “LAN pull” binds Iroh `presets::N0` (relays) and prints a durable ticket
- **Evidence:** `IrohNode::bind_with_secret` uses `Endpoint::builder(presets::N0)` (`networking/src/iroh_node.rs`). Comment on `endpoint_addr`: “includes home relay when available.” Ticket is JSON `EndpointAddr` printed by `arx net serve` / `arxos-edge serve`. mDNS TXT also carries a (truncated) ticket plus root CIDs (`discovery.rs`).
- **Invariant violated:** README “LAN pull” / Phase 0 no public directory.
- **How to reproduce:** Serve, copy ticket off-LAN, dial via n0 relay. Unverified on this host (iroh tests did not compile). Code path is unambiguous.
- **Blast radius:** Store contents reachable beyond the building LAN if the ticket leaks (stdout, systemd journal, truncated mDNS still leaks CIDs).
- **Recommended fix:** Default `RelayMode::Disabled` + bind local interfaces; opt-in relay. Do not print full tickets to journal.
- **Confidence:** high (relay in API); medium (live WAN reachability not executed)

### ARX-003

- **Severity:** P1
- **Area:** H
- **Title:** `AnnounceRoot` from any connected peer poisons Hello advertisements
- **Evidence:** `handle_message` `Message::AnnounceRoot` mutates `self.buildings` in memory with no signature, no store check (`iroh_node.rs`). Hello returns that vec. Does not change on-disk `head_root`.
- **Invariant violated:** Hello ads vs actual heads.
- **How to reproduce:** Connect, send `AnnounceRoot` for a known `building_id` with a historical or attacker Root CID that exists in CAS; subsequent Hello advertises it; a client that fetches “the advertised head” pulls the wrong closure.
- **Blast radius:** Clients that trust Hello/mDNS instead of an operator-supplied `--root`. CLI fetch requires `--root` (mitigation). `pull_building_head` is local-ads confused.
- **Recommended fix:** Ignore inbound `AnnounceRoot`, or require it to match `building_ads_from_store` after a disk refresh. Ads should be read-only from meta.
- **Confidence:** high

### ARX-004

- **Severity:** P1
- **Area:** E / L
- **Title:** `--metadata-only` with default `set_head=true` adopts an incomplete root as head
- **Evidence:** `pull_root_with_options` sets `AdoptOptions { allow_partial: metadata_only }` when `set_head` (`networking/src/sync.rs`). CLI `NetCommands::Fetch`: `set_head` default true, `metadata_only` default false (`cli/src/args.rs`). `allow_partial` skips missing active objects / spatial index (`adopt.rs`).
- **Invariant violated:** Production pull (`set_head=true`) must not install an incomplete closure.
- **How to reproduce:** `arx net fetch --peer T --root CID --metadata-only` (no `--no-set-head`). Unit: `adopt_incomplete_closure_fails_by_default` already shows `allow_partial` is sufficient.
- **Blast radius:** Replica head that cannot materialize blobs; later merge/export/score lie; spatial index missing.
- **Recommended fix:** `allow_partial` only when `!set_head`, or require `--no-set-head` with `--metadata-only`.
- **Confidence:** high

### ARX-005

- **Severity:** P1
- **Area:** L / E
- **Title:** `--allow-untrusted` help is false; the flag skips continuity and still sets head
- **Evidence:** clap help: “Allow adopting untrusted roots (verification failure becomes warning)” (`cli/src/args.rs`). Code: `allow_untrusted` skips `verify_continuous_with_local` entirely; `let _ = root.verify_authors()` (`adopt.rs`). No warning is printed on the sync path.
- **Invariant violated:** `allow_untrusted` is import/debug, not a soft warning.
- **How to reproduce:** `arx net fetch --allow-untrusted` of a Mallory genesis against an existing head; head moves. Contrast default fetch test `pull_set_head_default_does_not_install_mallory_fork`.
- **Blast radius:** One mistyped flag rewrites official history.
- **Recommended fix:** Help text: “skips Root-law and replica continuity; will set head.” Consider requiring `--i-know-this-sets-head` or refusing `set_head` unless `--no-set-head`.
- **Confidence:** high

### ARX-006

- **Severity:** P1
- **Area:** K / E
- **Title:** Unsigned IFC/USD import adopts as head via `allow_untrusted`
- **Evidence:** `gateways/ifc/src/import.rs` and `gateways/usd/src/import.rs`: if no signer, `RootBody::new` + `into_object` (empty authors) then `adopt_root_with_options { allow_untrusted: true }`. CLI `--sign` defaults true but missing `device.seed` becomes `None`. Import has no `--no-set-head`. Building `controller_keys` can be empty (`sign.map(...).unwrap_or_default()`).
- **Invariant violated:** `allow_untrusted` not a silent production path; empty controllers fail-closed later (`resolve_controller_keys`).
- **How to reproduce:** Empty store, `arx import ifc file.ifc --sign=false` (or no seed). Head is an unsigned root. `empty_controller_keys_rejected` shows later trusted adopt dies.
- **Blast radius:** First-contact lock to an unsigned building; subsequent honest pulls fail; BIM file becomes genesis.
- **Recommended fix:** Refuse import without a device key. Never call `allow_untrusted` from the CLI default path. Require `--allow-untrusted` explicitly for unsigned import.
- **Confidence:** high

### ARX-007

- **Severity:** P1
- **Area:** F
- **Title:** `MergeReplica` gates only the winning Building; untrusted objects still enter the merged set
- **Evidence:** `eligible_building_winners` / `collapse_buildings` (`core/src/merge/mod.rs`). Three-way/union runs first. Disjoint histories fall back to union (comment: “should be rare”). `merge_untrusted_newer_building_cannot_win` succeeds `repo.merge_root(fork_cid)` then asserts Alice’s keys remain — Mallory’s Building is dropped, not the merge. Mallory’s genesis in that test contains only a Building.
- **Invariant violated:** Documented “remote parent whose authors are not local controllers cannot supply the winning Building” — not “cannot supply objects.” README merge of concurrent controller tips is the intended path; `net fetch --no-set-head` + merge apply is documented for any CID.
- **How to reproduce:** Alice head H. Mallory genesis same `building_id`, `previous_root=None`, objects `{mallory_building, mallory_space}`. put both, `repo.merge_root(mallory_root)`. Expect Mallory space in active set (union) and Alice Building kept. Not executed this turn; logic is direct from `find_common_ancestor` → `None` → union.
- **Blast radius:** Official history contains attacker spaces/annotations; exports/IFC/score include them; controllers unchanged so it looks honest.
- **Recommended fix:** In `merge_roots_with_replica`, drop (or reject) parents whose authors are not local controllers instead of unioning. Fast-forward only for local-controller tips. Treat disjoint untrusted history as Authorization.
- **Confidence:** high (mechanism); medium (exact object-set of the suggested fixture not run)

### ARX-008

- **Severity:** P1
- **Area:** K / P
- **Title:** IFC export stamps `ViewDefinition [CoordinationView]` while the product says it is not
- **Evidence:** `Writer::finish` in `gateways/ifc/src/export.rs`: `FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');`. Root README: “not a certified CoordinationView.” CLI help: “Export building head as IFC4 STEP” — no MVD disclaimer. Crate docs: “Geometry is minimal.”
- **Invariant violated:** Phase honesty; users must not treat IFC as lossless BIM.
- **How to reproduce:** `arx export ifc $BID -o out.ifc` and read the HEADER. Roundtrip test asserts ISO-10303-21 / `Pset_ArxosIdentity`, not the MVD string.
- **Blast radius:** Downstream BIM tools classify the file as CoordinationView. Wrong clash/quantities decisions.
- **Recommended fix:** Emit a custom view name (`ArxosAsBuiltView`) matching README. Put the same sentence in CLI `--help`.
- **Confidence:** high

### ARX-009

- **Severity:** P1
- **Area:** J / D
- **Title:** iOS store in `Documents/arxos-store` copies `device.seed` via Files/iCloud
- **Evidence:** `ArxosCore.defaultStorePath()` → document directory + `arxos-store` (`ios/Arxos/Sources/ArxosCore/ArxosCore.swift`). `Info.plist`: `UIFileSharingEnabled` + `LSSupportsOpeningDocumentsInPlace`. No `NSURLIsExcludedFromBackupKey`, no `NSFileProtectionComplete` in Swift. Seed via `write_secret_bytes` (0o600 Unix only). `BuildingSession.exportStoreForShare` copies the whole store. README tells you to AirDrop that folder.
- **Invariant violated:** Controller key is not treated as a secret on device; 0600 is not Data Protection.
- **How to reproduce:** Init a building on device; Files.app / unencrypted backup; `keys/device.seed` is 32 bytes. Device copy not executed here.
- **Blast radius:** Anyone with the folder is a controller. Stolen phone / iCloud backup = stolen replica identity.
- **Recommended fix:** Store seed in Keychain; CAS in Application Support with Data Protection + exclude-from-backup; export a keyless snapshot or wrap seed separately.
- **Confidence:** high (paths/plist); medium (iCloud actually backing up this container — default Documents behavior)

### ARX-010

- **Severity:** P1
- **Area:** J / D
- **Title:** UniFFI production surface exports `allow_untrusted`, raw `put_blob`, and plaintext seeds
- **Evidence:** `ffi/src/arxos.udl`: `pull_remote_root(..., boolean allow_untrusted)`, `put_blob`, `create_root(..., seed_hex)`, `generate_keypair` → `KeypairData.seed`. Generated Swift is in the app target. Façade does not wrap `put_blob`/`generate_keypair`; UI does not call pull. There is no Rust clamp of `allow_untrusted` for iOS.
- **Invariant violated:** Preferred types / single domain writer; `allow_untrusted` not a hidden FFI default.
- **How to reproduce:** Call generated `uniffiPullRemoteRoot(..., allowUntrusted: true)` from any Swift. Compile-time surface, not current UI.
- **Blast radius:** Next engineer wiring “sync” in the app can TOFU-or-skip-auth with one bool. Seed bytes on the Swift heap (`Vec<u8>`, `Clone`).
- **Recommended fix:** Drop debug ops from the iOS UDL (or cfg them). `pull_remote_root` should not take `allow_untrusted`; hardcode false.
- **Confidence:** high

### ARX-011

- **Severity:** P2
- **Area:** B
- **Title:** `from_cbor` / `from_canonical_bytes` do not require canonical CBOR
- **Evidence:** `canonical.rs`: raw `ciborium::{into_writer,from_reader}`. `Object::from_canonical_bytes` = decode + validate only. Fail-closed re-encode is only `ObjectStore::put_bytes` / `MemObjectStore::put_bytes`. Extra fields: no `deny_unknown_fields`.
- **Invariant violated:** Unique canonical encoding for every stored object at decode, not only at ingest.
- **How to reproduce:** Already tested: `put_bytes_rejects_non_canonical_wire`. Missing: `from_canonical_bytes` on extra-key CBOR succeeds. get of a planted extra-key file → CID mismatch.
- **Blast radius:** Tooling that `from_cbor`s without `put_bytes` can accept aliases; two encodings of “the same” object. Ingest path is safe.
- **Recommended fix:** Re-encode check inside `from_canonical_bytes`, or rename it. Keep `put_bytes` as the wire gate.
- **Confidence:** high

### ARX-012

- **Severity:** P2
- **Area:** B / G
- **Title:** CAS writes are rename-atomic, not crash-durable (no fsync)
- **Evidence:** `atomic_write` = `fs::write` + `fs::rename` (`store/mod.rs`). Contrast `write_secret_bytes` which `sync_all`. Docs: “Crash-safe on the same filesystem.”
- **Invariant violated:** After put/commit returns, power loss still has the object/head.
- **How to reproduce:** Code inspection. No fault injector in tree.
- **Blast radius:** Empty or old `BuildingRecord` after crash; orphan roots (commit puts root before `write_record` — captures not lost, head may not advance).
- **Recommended fix:** fsync file + parent dir in `atomic_write` (same discipline as seed files).
- **Confidence:** high (missing fsync); medium (actual loss on APFS)

### ARX-013

- **Severity:** P2
- **Area:** G
- **Title:** Idempotent put trusts `path.exists()`; leftover temps are never GC’d
- **Evidence:** `put_canonical_bytes`: if path exists, return CID without hashing. `list_cids` skips `is_tmp_name`; nothing deletes leftovers. Test `list_cids_skips_tmp_artifacts` asserts skip, not deletion.
- **Invariant violated:** CID path bytes == BLAKE3⁻¹(cid); failed writes do not leak disk.
- **How to reproduce:** Plant garbage at the object path; put of the real object returns Ok; get → CID mismatch. `get_bytes` / serve still ships garbage (ARX-001).
- **Blast radius:** Corrupt slot stays forever; serve can emit it; honest puller rejects. Disk fill from crash temps.
- **Recommended fix:** On exists, hash and replace if mismatch (or error). GC `*.tmp.*` on open.
- **Confidence:** high

### ARX-014

- **Severity:** P2
- **Area:** E
- **Title:** First-contact TOFU can lock a replica to attacker controllers
- **Evidence:** `verify_continuous_with_local`: `local_head == None` → `FirstTrust` after `verify_with_store` only (`root/auth.rs`). `open_or_follow` does not pin expected keys. Default CLI fetch `set_head=true`. Tests encode this as success (`adopt_first_contact_tofu_succeeds`).
- **Invariant violated:** none vs docs — this is the spec. It is still a landmine for a second replica.
- **How to reproduce:** Empty follow store, fetch Mallory genesis for Alice’s `building_id` (from mDNS). Later Alice pull: not a local controller / second genesis.
- **Blast radius:** Replica must be wiped. No out-of-band pin.
- **Recommended fix:** `open_or_follow(..., expected_controllers: &[PublicKey])` or print Building keys and require `--trust-controllers`. Keep TOFU only with an explicit flag.
- **Confidence:** high

### ARX-015

- **Severity:** P2
- **Area:** F
- **Title:** Merge LCA/fast-forward walk `previous_root` only; `merge_parents` can resurrect CIDs
- **Evidence:** `ancestor_chain` sets `cur = body.previous_root` (`merge/mod.rs`). Merge commits set `previous_root` to the newer timestamp tip, `merge_parents = {A,B}`. Adopt does walk `merge_parents`.
- **Invariant violated:** Stated “NCA on the `previous_root` chain” vs DAG merge history.
- **How to reproduce:** Criss-cross merge after an earlier merge (see slice notes). No test in tree.
- **Blast radius:** Deleted objects reappear in official history after a second merge generation.
- **Recommended fix:** LCA over `previous_root ∪ merge_parents`, or always checkpoint on merge (already sometimes true).
- **Confidence:** medium (fixture not executed)

### ARX-016

- **Severity:** P2
- **Area:** A / H
- **Title:** 64 MiB protocol frames vs 4 MiB objects; closure built in RAM on the accept task
- **Evidence:** `MAX_MESSAGE_BYTES = 64MiB` (`protocol.rs`); `MAX_OBJECT_BYTES = 4MiB`. `handle_message` calls `serve_root_closure_*` synchronously on the Tokio worker (`iroh_node.rs`). `encode_message` encodes then rejects. No test for len > `MAX_MESSAGE_BYTES`.
- **Invariant violated:** Resource safety of serve; object cap as the real bound.
- **How to reproduce:** `GetRootClosure` of a large building; or send length prefix 64MiB+1.
- **Blast radius:** Edge OOM / stall while holding `store.lock`.
- **Recommended fix:** Stream objects; cap closure by object count × 4MiB; `spawn_blocking`; test oversized frames.
- **Confidence:** high

### ARX-017

- **Severity:** P2
- **Area:** C / A
- **Title:** `SCHEMA_VERSION` accepts any ≥ 1; unknown types fail closed only via serde enums
- **Evidence:** `Object::validate`: reject `schema_version == 0` only (`object/mod.rs`). `SCHEMA_VERSION = 1`. No `deny_unknown_fields`. Closed `ObjectType`/`ObjectBody` enums → unknown kind deserialize error (fail-closed). v2 with same shape stores.
- **Invariant violated:** Fail closed on future schema (or explicit migrate).
- **How to reproduce:** `put_bytes` of otherwise valid object with `schema_version: 99`.
- **Blast radius:** Mixed-version replicas silently accept junk versions; no migration story.
- **Recommended fix:** Reject `schema_version != SCHEMA_VERSION` on put/ingest until a v2 reader exists.
- **Confidence:** high

### ARX-018

- **Severity:** P2
- **Area:** D / J
- **Title:** App Attest is recorded nowhere on iOS and “verified” structurally; Mock sits on `DefaultAttestationVerifier`
- **Evidence:** `AppAttestVerifier` returns `valid: true` after keyId/non-empty checks (`attest/mod.rs`: “do not treat as secure production verification”). `DefaultAttestationVerifier` routes Mock in all builds. CLI `arx attest` always builds mock. iOS `AppAttest.swift` has zero call sites from capture/commit. Adopt does not consult provenance.
- **Invariant violated:** Device authenticity as a trusted path (if anyone thought Phase 5 shipped).
- **How to reproduce:** `arx attest $ROOT`; object is mock provenance, not a gate. iOS: grep shows no `AppAttestClient` use from `CapturePipeline`.
- **Blast radius:** None on heads today (ed25519 only). High if product claims “attested capture.”
- **Recommended fix:** Keep as diagnostic. Reject `AttestationKind::Mock` outside tests. Do not advertise App Attest as enforced.
- **Confidence:** high

### ARX-019

- **Severity:** P2
- **Area:** M / O
- **Title:** No CI; `cargo test --workspace` is broken on this dirty lockfile; clippy `-D warnings` fails; MSRV 1.75 is implausible with iroh 1.1
- **Evidence:** No `.github/`, no `rustfmt.toml`/`clippy.toml`/`rust-toolchain`. This tree: tinyvec 1.13.0 does not compile on rustc 1.96. `cargo clippy -p arxos-core --all-targets -- -D warnings` → 8 errors. Workspace `rust-version = "1.75"` while cli depends on `arxos-networking` default features iroh. `default-members = ["core","cli"]` so plain `cargo test` skips gateways/ffi/networking tests except cli pulls networking in.
- **Invariant violated:** README `cargo test --workspace`; `rust-version` as a real MSRV.
- **How to reproduce:** Commands in the table above.
- **Blast radius:** Nobody is running iroh/FFI/CLI smoke on PRs. A lockfile bump silently kills the product crates.
- **Recommended fix:** Pin tinyvec `<1.13` or wait for a fix; add CI on a toolchain that actually builds iroh; bump `rust-version` to match; `--locked`.
- **Confidence:** high (this checkout); medium (iroh 1.1 exact MSRV not fetched from crates.io this turn)

### ARX-020

- **Severity:** P2
- **Area:** H / L
- **Title:** systemd unit runs `arx net serve`, not `arxos-edge`; Docker runs as root
- **Evidence:** `edge/systemd/arxos-edge.service` `ExecStart=/usr/local/bin/arx --store ${ARXOS_STORE} net serve`. `install-edge.sh` installs both binaries. `edge/Dockerfile`: no `USER`. Hardening on systemd is partial (`NoNewPrivileges`, `ProtectSystem=strict`) but no `UMask=0077`.
- **Invariant violated:** Documented `arxos-edge serve` as the long-running node.
- **How to reproduce:** Read the unit vs `edge/README.md`.
- **Blast radius:** Wrong binary in production; root container; journal contains tickets (ARX-002).
- **Recommended fix:** `ExecStart=/usr/local/bin/arxos-edge --store … serve`; non-root Docker `USER`; `UMask=0077`.
- **Confidence:** high

### ARX-021

- **Severity:** P2
- **Area:** N / G
- **Title:** Same-process two-thread exclusive lock is untested; Unix flock is a weak single-writer
- **Evidence:** `try_lock_exclusive` via fs2 (`store/mod.rs`). Test `exclusive_lock_blocks_other_process` only. FFI + CLI can open twice in one process. fs2 0.4.3 is unmaintained (2018).
- **Invariant violated:** “One process writes a given store at a time” vs “one handle.”
- **How to reproduce:** Two threads `BuildingRepository::open` on one path. Not run.
- **Blast radius:** Torn `BuildingRecord` if two writers in one process (iOS less likely; tests/tools more).
- **Recommended fix:** In-process `OnceLock`/pid file in addition to flock; test two threads.
- **Confidence:** medium

### ARX-022

- **Severity:** P3
- **Area:** F
- **Title:** Pose-less annotations collapse to origin; transcript is ignored in dedupe
- **Evidence:** `collect_annotations`: `pose.unwrap_or_default()`, `text.unwrap_or_default()`; empty text → keep both (`merge/mod.rs`). `transcript` unused. Spatial `entry_from_object` drops pose-less annotations from the index.
- **Invariant violated:** Documented 0.35 m identical-text rule as spatial; actually “origin if missing.”
- **How to reproduce:** Two pose-less `text="same"` → one dropped. Two transcript-only → both kept.
- **Blast radius:** Voice notes / unposed labels silently deleted or invisible to spatial query.
- **Recommended fix:** Do not default pose; skip distance dedupe when pose is `None`.
- **Confidence:** high

### ARX-023

- **Severity:** P3
- **Area:** D / L
- **Title:** CLI `key generate` and `root create --seed` put secrets on stdout/argv; FFI `generate_keypair` returns `Vec<u8>` seed
- **Evidence:** `KeyCommands::Generate` prints `seed=` (`cli/src/commands/mod.rs`). `RootCommands::Create` requires `--seed`. `KeypairData.seed: Vec<u8>` (`ffi/src/lib.rs`). Core `Keypair`/`SecretKey` are correctly not `Clone`, not `Debug`, `ZeroizeOnDrop` — this is the export surface.
- **Invariant violated:** Secrets not in argv/foreign heap except explicit export — the export is too easy.
- **How to reproduce:** `arx key generate`; `ps` during `arx root create --seed …`.
- **Blast radius:** Shell history, crash logs, Swift heap dumps.
- **Recommended fix:** Keep generate as the only explicit export; refuse `--seed` in favor of `keys/device.seed`.
- **Confidence:** high

### ARX-024

- **Severity:** P3
- **Area:** E
- **Title:** Missing negative tests: extra unauthorized co-author; hop bound; multiple Buildings; CID-lying peer
- **Evidence:** `verify_authorized` loops all authors (logic rejects extras) but no test with controller+Mallory co-sign. `MAX_CONTINUITY_ANCESTOR_HOPS=4096` untested. `resolve_controller_keys` multiple-Building branch untested. Pull CID mismatch is coded (`sync.rs`) but no test that a lying `ObjectBlob` is rejected. `Object::verify_signature` on a Root is comment-only.
- **Invariant violated:** Tests that would fail if the invariant broke.
- **How to reproduce:** Add those cases; they should exist.
- **Blast radius:** Refactors can drop fail-closed branches unnoticed. No CI (ARX-019) makes this worse.
- **Recommended fix:** Add the list in §6.
- **Confidence:** high

### ARX-025

- **Severity:** P3
- **Area:** P / O
- **Title:** Product leftovers and license mismatch
- **Evidence:** `core/src/lib.rs` crate docs: “Arxos DePIN data plane.” `scoring/mod.rs`: “DePIN oracle input.” CHANGELOG: “EVM contracts remain only under `archive/contracts-evm-deprecated/`” — directory does not exist. `workspace.package.license = "MIT OR Apache-2.0"`; `LICENSE` is MIT-only. `docs/` gitignored but present locally. `arx score --json` omits the text-mode `diagnostic_only` note.
- **Invariant violated:** CHANGELOG/README as the public identity; dual license.
- **How to reproduce:** Grep DePIN; `ls archive`; read `LICENSE` vs `Cargo.toml`.
- **Blast radius:** Legal/docs; score JSON looking like a payment oracle to scripts.
- **Recommended fix:** Delete DePIN sentences; add `LICENSE-APACHE` or drop Apache from `Cargo.toml`; fix CHANGELOG archive sentence; put diagnostic flag in JSON.
- **Confidence:** high

### ARX-026

- **Severity:** P3
- **Area:** H
- **Title:** mDNS tickets truncated at 200 chars are unusable; CIDs still leak
- **Evidence:** `discovery.rs` truncates ticket with `…`; receivers drop truncated tickets. Still publishes building/root.
- **Invariant violated:** mDNS as a working dial path.
- **How to reproduce:** `arx net peers` vs a real Iroh JSON ticket length.
- **Blast radius:** Operators think discovery works; it often cannot dial; LAN still learns Root CIDs (feeds ARX-001).
- **Recommended fix:** Don’t put tickets in TXT; publish a short lookup token, or skip ticket entirely and use peer id + local addrs.
- **Confidence:** high

### ARX-027

- **Severity:** P3
- **Area:** A / L
- **Title:** `ObjectStore` still used for domain reads (`arx verify`, merge plan); tracing is a stub
- **Evidence:** `cli/src/commands/mod.rs` opens `ObjectStore` for verify/plan. One `tracing::warn` in the Iroh accept loop; no subscriber in CLI/edge; zero tracing in core.
- **Invariant violated:** Preferred types table; supportability of a stuck merge.
- **How to reproduce:** Read those command arms.
- **Blast radius:** Operators get English `Error::Authorization(String)` only (`core/src/error.rs` is stringly).
- **Recommended fix:** `open_read` / `RootClosure` for verify/plan; structured error codes; a tracing subscriber on serve.
- **Confidence:** high

### ARX-028

- **Severity:** P4
- **Area:** D
- **Title:** Two sign laws are adapter convention, not a type check
- **Evidence:** `Object::sign` does not reject `ObjectType::Root`. `into_object` blanks header signature. Adopt uses `verify_authors`, so this is not a head bypass.
- **Invariant violated:** “`Object::verify_signature` on a Root is defined to fail” — true only for `into_object` output.
- **How to reproduce:** `Object::new(Root(...)); obj.sign(&kp); obj.verify_signature()` succeeds.
- **Recommended fix:** `Object::sign`/`verify_signature` error on `ObjectType::Root`; add the test.
- **Confidence:** high

### ARX-029

- **Severity:** P4
- **Area:** B
- **Title:** Windows rename-over-existing for idempotent put is unverified
- **Evidence:** `atomic_write` uses `fs::rename` with no “already exists ⇒ Ok”. POSIX replace vs Windows fail-if-exists. Not tested (macos host).
- **Invariant violated:** Portable atomic put.
- **How to reproduce:** Two concurrent same-CID puts on NTFS.
- **Blast radius:** Flaky ingest on Windows only.
- **Recommended fix:** Treat `AlreadyExists` after rename as success if hash matches.
- **Confidence:** low (platform)

---

## 4. Scores (1–5) with evidence

| Dim | Score | Why |
|---|---|---|
| A Architecture | 3 | Preferred types are real in core generics (`ObjectRead`/`ObjectWrite`, `BuildingRepository`). Process-edge `ObjectStore` is documented and used (FFI `put_blob`, serve, `export_root`). Not an API firewall. |
| B CAS / canonicalization | 4 | `put_bytes` re-encode + 4 MiB + BLAKE3-of-full-object including signature/`created`. `from_cbor` is not a canonical gate. No fsync. Dirty-slot `exists()` skip. |
| C Object model | 3 | Closed enums fail-closed on unknown type. Schema v≥1 accepted. Entity collapse is tested. Pose/AABB float policy is tested (signed zero, hemisphere, NaN reject). |
| D Crypto / keys | 4 | `Keypair`/`SecretKey` not `Clone`, `ZeroizeOnDrop`, Unix 0600. Seed export via CLI/FFI/argv. Windows ACL absent. |
| E Auth / TOFU / continuity | 4 | Production adopt is fail-closed; second genesis, mallory fork, `merge_parents` claim, fast-forward are tested. TOFU and `--allow-untrusted`/`--metadata-only` are the holes. Extra-author test missing. |
| F Merge | 3 | Real three-way + entity collapse + Building replica gate. Untrusted objects union; LCA ignores `merge_parents`; `merge_roots` without replica is public. |
| G Repo / lock / durability | 4 | Cross-process flock tested; `open_read` documented TOCTOU; commit order CAS-then-head is right. No fsync; leftover tmp; same-process lock untested. |
| H Networking / edge | 2 | Protocol framing is fine. Serve is a CAS oracle on N0 relays; `AnnounceRoot` poison; 64 MiB frames; systemd/Docker sloppy. Pull ingest correctly uses `BuildingRepository`. |
| I Spatial | 4 | Versioned CAS R-tree; incremental vs rebuild tests; merge rebuilds. No crash/partial-index test; pose-less anns omitted from index. |
| J Capture / iOS / FFI | 2 | RoomPlan path uses repository + lock; no mesh chunking (honest README). Seed in Documents; UDL footguns; App Attest unwired. Bindings gitignored + mtime check. |
| K Gateways | 2 | Head projection is real. CoordinationView lie; unsigned adopt; IFC import drops poses (`pose = None`); USD parse never Err; identity-only roundtrips. |
| L CLI / UX | 3 | `--no-set-head` is first-class and tested. `--allow-untrusted` help lies. Import always adopts. Score text is diagnostic; JSON is not. Errors are strings. |
| M Tests / CI | 2 | Core unit/prop/multi_device are serious. No CI. Workspace compile broken on dirty lockfile. Networking/FFI untested this turn. Many listed negatives missing. |
| N Performance | 3 | Working set 512 objects; score/collapse get every CID; serve blocks the runtime on full closures. 4 vs 64 MiB. |
| O Supply chain | 2 | fs2 0.4.3 unmaintained; tinyvec 1.13 breaks rustc 1.96; dual ed25519-dalek majors (core 2.2 vs iroh 3) reported from lockfile; MIT file vs MIT OR Apache; uniffi 0.28. |
| P Product honesty | 3 | Root README Phase 0 is mostly accurate (iOS pull not in UI — true). IFC header, DePIN crate docs, missing `archive/`, N0-as-LAN are not. |

---

## 5. Threat notes

**Malicious peer on LAN** (has ticket or can connect via N0). Can `GetObject`/`GetRootClosure` anything in the CAS (ARX-001). Can `AnnounceRoot` poison Hello (ARX-003). Cannot, by default, adopt a Mallory fork onto a replica that already TOFU’d an honest head (`pull_set_head_default_does_not_install_mallory_fork`, `adopt_rejects_replaced_building_full_set_fork`). Can get untrusted objects into official history if an operator merge applys a fetched CID (ARX-007). First empty replica: TOFU (ARX-014).

**Copied store.** Flock is per path: two edges both write. `keys/device.seed` and `keys/iroh.seed` copy with the folder → same controller and same Iroh `EndpointId`. That is also the documented Mac inspect path.

**Stolen `device.seed`.** Full controller: commit, adopt (if also a controller on the Building), merge sign. Seed is 32 bytes, Unix 0600, not in Keychain on iOS (ARX-009). CLI `key generate` prints another.

**TOFU first contact.** Empty `open_or_follow` + default fetch installs whatever self-consistent Root arrives. Later honest history is “not a local controller.” Operator must wipe.

**Untrusted IFC import.** Unsigned import is an `allow_untrusted` head (ARX-006). Parser is unbounded RAM; USD parse never returns Err. Poses are dropped on IFC import — a “roundtrip” is identity metadata, not geometry.

**Compromised iOS app.** Generated UniFFI in-process: `allow_untrusted` pull, `put_blob`, seed export (ARX-010). Capture/commit themselves go through `BuildingRepository`. App Attest is not on the commit path (ARX-018). `NSLocalNetworkUsageDescription` is already in the plist.

---

## 6. Test gap list (priority)

1. Merge of disjoint Mallory genesis with extra Space/Annotation — assert reject or drop (ARX-007). Do not ship merge-apply of fetch CIDs until this exists.
2. `--metadata-only` default `set_head` incomplete head (ARX-004).
3. Extra unauthorized author co-signed with a controller (ARX-024).
4. `GetObject` / `GetRootClosure` for a CID not in advertised buildings (ARX-001).
5. `AnnounceRoot` does not change subsequent Hello (ARX-003).
6. `decode_message` len > `MAX_MESSAGE_BYTES` (ARX-016).
7. Lying `ObjectBlob` CID ≠ BLAKE3(bytes) rejected (coded, untested).
8. `Object::verify_signature` on `RootBuilder::build_signed` output fails (ARX-028).
9. Continuity hop bound 4096; missing parent fail-closed.
10. Multiple Building objects in one active set.
11. First-contact Mallory then honest Alice rejected.
12. Rotated-out key cannot adopt after local Building CID change.
13. Pose-less / transcript-only annotation dedupe (ARX-022).
14. LCA/`merge_parents` resurrection (ARX-015).
15. Canonical CBOR across ciborium versions (pin + fixture bytes).
16. `cargo test -p arxos-networking --no-default-features`.
17. Two-thread `try_lock_exclusive` (ARX-021).

---

## 7. Do not ship until (P0/P1)

There is no demonstrated production-adopt bypass after an honest first head: Mallory full-set forks are rejected, second genesis is rejected, `set_head` default does not install a Mallory fork. That is the load-bearing core.

Do not trust a second replica or a field scan until:

1. **ARX-007** — merge of a non-controller parent cannot add/delete domain objects. Until then, `fetch --no-set-head` + merge apply is a landmine, not a workflow.
2. **ARX-004 / ARX-005 / ARX-006** — incomplete/untrusted flags cannot silently become head (CLI help + import + metadata-only).
3. **ARX-001 / ARX-002** — either disable N0 relays by default and scope `Get*` to advertised closures, or stop calling this “LAN pull” and treat tickets as the only ACL (and keep them out of journals/mDNS).
4. **ARX-009** — phone `device.seed` out of shared Documents / iCloud.
5. **ARX-008** — stop labeling IFC as CoordinationView.
6. **ARX-010** — remove `allow_untrusted` / seed export from the iOS UDL (or hard-fail them).
7. **ARX-019** — a CI job that actually compiles networking (`--locked` on a lockfile that builds) and runs `arxos-core` + `net_fetch` + gateway roundtrips.

Until (1)+(3)+(4), a second replica is a TOFU’d CAS copy, not a second trusted historian.

---

## 8. What is actually good (evidenced)

- `put_bytes` is fail-closed: size, typed decode, exact re-encode, store wire bytes under BLAKE3(wire). Tests: `put_bytes_rejects_non_canonical_wire`, `put_bytes_rejects_non_canonical_signed_zero`, `put_rejects_oversized_object` (FS + mem).
- Production adopt is fail-closed after first head: `verify_continuous_with_local` does self-consistency, local-controller intersection, second-genesis reject, DAG walk of `previous_root` and `merge_parents`, missing parent fail-closed, hop cap. Tests: `continuity_rejects_second_genesis_against_existing_head`, `adopt_rejects_replaced_building_full_set_fork`, `adopt_rejects_fork_claiming_local_head_in_merge_parents`, `adopt_accepts_fast_forward_signed_by_local_controller`, `pull_set_head_default_does_not_install_mallory_fork`.
- `resolve_controller_keys` fail-closed on missing Building and empty keys (tests exist). Multiple Buildings is coded fail-closed.
- All authors must be controllers (not M-of-N). Extra unauthorized author cannot sneak in (logic; test missing).
- Commit uses `verify_with_store` only (self-consistency of that root). Correct split from adopt.
- Float CID policy is real: NaN/Inf rejected, -0.0 folded, quaternion hemisphere. Tests in `object/mod.rs` and `property_cid.rs`.
- Cross-process `store.lock` works (`exclusive_lock_blocks_other_process`; `open_read` does not block serve).
- Pull ingest goes through `BuildingRepository::open_or_follow` + `ObjectIngest`, not anonymous CAS puts. CID mismatch on the wire is checked before write.
- Domain merge passes `MergeReplica`; Mallory Building cannot win (`merge_untrusted_newer_building_cannot_win`). Networking does not auto-merge.
- iOS UI capture uses `BuildingRepository` (lock, stage, commit). README “network pull is not wired in the UI” matches `CaptureHomeView` / `BuildingSession`.
- `arxos-core` tests on this host: 103 + integration/prop tests listed above, all passed.

---

## 9. Recommended follow-ups (no patches in this review)

- Gate merge parents on local controllers before three-way (ARX-007). Keep `plan_merge` dry-run.
- Hard-bind `allow_partial` to `!set_head`; fix clap help for `allow_untrusted`.
- Serve advertised closures only; default Iroh without relays.
- Move iOS seed to Keychain; exclude store keys from backup.
- IFC `FILE_DESCRIPTION` + CLI help aligned with README.
- Shrink iOS UDL to capture/commit/query/export.
- CI: toolchain file, `--locked`, `cargo test --workspace`, clippy not `-D warnings` until the 8 errors are triaged (do not “fix” them in this review).
- Revert or pin tinyvec so networking compiles; do not commit the current lockfile bump blindly.
- Add Apache text or drop dual-license claim.
