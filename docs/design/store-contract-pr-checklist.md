# Store-contract PR checklist

The store contract is the product. Everything else is a client of it.

Source of truth: [core/README.md](../../core/README.md) (Store contract). Product identity: [README.md](../../README.md). If a PR fights these rules, the PR is wrong — do not “simplify” them for a demo.

This file is a reviewer checklist, not a second architecture. Encode failures as tests, not as new crates.

## Verdict

- [ ] **Reject** if any invariant below is weakened, bypassed, or re-explained away.
- [ ] **Reject** if a law test is deleted, skipped, or made `allow_untrusted` by default to go green.
- [ ] **Accept** only if the change is a thinner client of `BuildingRepository` / `ObjectRead` / `ObjectIngest`, or a bugfix that preserves the laws.

## 1. CAS purity

`ObjectStore` is `has` / `get` / `get_bytes` / `put` / `put_bytes`. No query, signing, collapse, scoring, or index logic on the store.

| Check | Fail if |
|---|---|
| New methods on `ObjectStore` | They are not CAS, lock, path-open, or filesystem tooling (`list_cids`, `rebuild_index`, `store.lock`) |
| Public API | Returns `&ObjectStore` |
| Callers | Pass a writable store into score / verify / export / spatial query / entity collapse |
| Tests | `put_does_not_write_index_file` (`core/src/store/mod.rs`) is broken or deleted |

Allowed `ObjectStore` construction (path open, not an API): CLI debug, FFI `put_blob` / `show_root`, `export_root_*` given only a path, `arxos-edge` serve, test temp dirs, `MemoryMesh::attach(path)`.

## 2. Single domain writer

Building data goes through `BuildingRepository` (capture → stage → commit, ingest → adopt, merge). Never exclusive-lock and `put` raw building objects.

| Check | Fail if |
|---|---|
| Building mutation | New write path that is not a method on `BuildingRepository::open` |
| Helpers taking `ObjectWrite` | Caller is not the repository (or commit) |
| CLI / FFI | `object put` / `root create` / `attest` presented as the field path (they are debug CAS) |
| iOS | `BuildingSession` writes CAS except via UniFFI repository methods |

`open` / `init` / `open_or_follow` hold `store.lock` for the handle lifetime. `open_read` takes no flock. Mutating methods on a read handle must return `Error::Store`.

## 3. Derived layers are readers

Scoring, verify, entity collapse, spatial *queries*, and export consume `ObjectRead` or a closed `RootClosure` / `ClosureView`. They must not take a writable store.

| Intent | Type |
|---|---|
| Read any CID | `R: ObjectRead + ?Sized` |
| Write CAS bytes (index builders, capture blob helpers) | `W: ObjectWrite + ?Sized` — repository is the caller |
| Building capture / commit / adopt / ingest | `BuildingRepository::open` (exclusive lock) |
| Read a building (score, verify, export, status) | `BuildingRepository::open_read` (no flock) |
| Export or verify a frozen root | `RootClosure::collect` then `ClosureView` |
| Wire ingest (sync / import) | `ObjectIngest` on the repository |

## 4. Two sign laws

- Leaf `Object::sign` is optional provenance (`header.author` / `header.signature`). CID includes the signature.
- `RootBody::sign` is required authority in `body.authors`. `into_object` blanks `header.signature`.
- `Object::verify_signature` on a Root is **defined to fail**. Use `RootBody::verify_authors` / `verify_with_store`.

| Check | Fail if |
|---|---|
| Root wrapping | `into_object` starts copying a header signature as root authority |
| Verify | Callers treat `Object::verify_signature` as root auth |
| Tests | `sign_and_verify` / `sign_covers_canonical_geometry` (`core/src/object/mod.rs`) or root author tests (`core/src/root/auth.rs`) regress |

## 5. Adopt is stricter than commit

| Path | Required checks | Default flags |
|---|---|---|
| Local `commit` | `verify_with_store` only (self-consistency vs Building in *that Root's* active set) | — |
| Adopt / production pull | Self-consistency **plus** replica continuity (`verify_continuous_with_local`) | `allow_untrusted = false`, `set_head = true` |
| First contact (`open_or_follow`, `head_root == None`) | Self-consistency, then TOFU (`ContinuityOutcome::FirstTrust`) | — |
| Full-set checkpoint with `previous_root = None` against an existing head | **Reject** — second genesis | — |
| `allow_untrusted` | IFC/USD unsigned import, explicit FFI/debug | Never default sync |

Do not fold the two checks together (`core/src/root/auth.rs`). Ingest may store untrusted bytes; heads do not advance on them by default.

## Law tests (the spec)

A change that breaks one of these is a protocol break. Run the named tests; do not substitute “related coverage.”

| Law | Test | Where |
|---|---|---|
| Field loop (release checklist) | `field_loop_init_capture_commit_status_entity_score` | `cli/tests/smoke.rs` |
| Unauthorized commit | `root_create_rejects_unauthorized_seed` | `cli/tests/smoke.rs` |
| Unauthorized commit (FFI) | `unauthorized_commit_surfaces_as_authorization_error` | `ffi/src/lib.rs` |
| Unauthorized valid signature | `unauthorized_valid_signature_rejected` | `core/src/root/auth.rs` |
| Second genesis | `verify_continuous_with_local` case containing `"second genesis"` | `core/src/root/auth.rs` |
| Checkpoint not descending | `adopt_rejects_full_set_checkpoint_not_descending_local_head` | `core/src/repository/adopt.rs` |
| Replaced-building fork | `adopt_rejects_replaced_building_full_set_fork` | `core/src/repository/adopt.rs` |
| Merge-parent fork claim | `adopt_rejects_fork_claiming_local_head_in_merge_parents` | `core/src/repository/adopt.rs` |
| TOFU first contact | `adopt_first_contact_tofu_succeeds` | `core/src/repository/adopt.rs` |
| Fast-forward | `adopt_accepts_fast_forward_signed_by_local_controller` | `core/src/repository/adopt.rs` |
| Incomplete closure | `adopt_incomplete_closure_fails_by_default` | `core/src/repository/mod.rs` |
| Pull fails when locked | `pull_ingest_fails_closed_when_store_locked` | `networking/src/sync.rs` |
| Exclusive lock | `exclusive_lock_blocks_other_process` (and `try_lock_exclusive`) | `core/src/store/mod.rs` |
| CAS purity | `put_does_not_write_index_file` | `core/src/store/mod.rs` |
| IFC identity | `ifc_roundtrip_identity` | `gateways/ifc/tests/roundtrip.rs` |
| USD identity | `usd_roundtrip_identity` | `gateways/usd/tests/roundtrip.rs` |
| iOS ingest + spatial query | `test_ingest_room_plan_spatial_query` | `ffi/src/lib.rs` |
| App Attest mock labeled as mock | `mock_attest_roundtrip` | `core/src/attest/mod.rs` |

Minimum command when the PR touches core / FFI / CLI / networking / gateways:

```bash
cargo test -p arxos-core
cargo test -p arxos-cli --test smoke
cargo test -p arxos-ffi
cargo test -p arxos-networking pull_ingest_fails_closed_when_store_locked
cargo test -p arxos-ifc ifc_roundtrip_identity
cargo test -p arxos-usd usd_roundtrip_identity
```

## Clients stay thin

| Surface | Allowed | Reject |
|---|---|---|
| UniFFI (`ffi/src/arxos.udl`) | Projection of `BuildingRepository` (init/open/capture/commit/ingest/query/export) | A second domain model; new write verbs that skip the repository |
| iOS `BuildingSession` / `CaptureHomeView` | create, capture, commit, share/export | Merge UI; mesh capture; cloud; multi-writer |
| Gateways | Readers + `ObjectIngest`; identity Psets (`Pset_ArxosIdentity`, `arxos:cid`) | Alternate writers; dropping `EntityId` / identity properties |
| `arxos-edge serve` / `arx net serve` | Long-running net serve with writer lock held | Two phones co-editing one store path |
| CLI `merge plan` / `merge apply` | Office/laptop after a pull | Field UX on the phone |
| `arx score` | Diagnostic type-count weights (`policy_version`) | Marketing as an economic / DePIN / settlement system |

Field capture types: **space, annotation, point cloud, RoomPlan**. `MeshCapture` exists in core (`core/src/capture/mod.rs`) and is not on `BuildingSession`. Do not imply the phone captures meshes.

`allow_untrusted` on `arx net fetch` defaults to `false`. Do not flip the default.

## Schema freeze

Field stores will outlive the next refactor.

- [ ] Object envelope `schema_version` stays `>= 1`; current `SCHEMA_VERSION` is `1` (`core/src/object/mod.rs`). Bumps are explicit and documented in `docs/schema/object-schema.md`.
- [ ] Root body fields (`previous_root`, `merge_parents`, `authors`, `added`/`removed`/`objects`) are not silently reinterpreted.
- [ ] `ScoreReport.policy_version` (default `1`) is the pattern: version the policy, do not mutate old reports in place.
- [ ] JSON sketches `docs/schema/object-envelope.schema.json` and `root-body.schema.json` match the Rust types if either side changes.

## Hygiene (do not re-open)

- [ ] No new commercial control-plane, fiat-ledger, or SaaS account surface.
- [ ] EVM / DePIN stays under `archive/` and unbuilt. Scoring stays diagnostic (`core/README.md`: fiat settlement is off-band).
- [ ] Do not add public methods that return `&ObjectStore`.
- [ ] Do not put merge on the phone UI. FFI `merge_building_root` may exist as a repository projection; `CaptureHomeView` must not call it.

Kernel seams (not a reason to block a field-loop PR; next internal refactor only): `entity.rs` ↔ `object/mod.rs` cycle; networking must not own CLI dispatch.

## Reviewer one-liner

> Freeze the kernel. Ship one writer on a LiDAR iPhone. Inspect and export on a Mac. Do not re-open economic, multi-writer, or cloud work until that loop has real buildings in it.
