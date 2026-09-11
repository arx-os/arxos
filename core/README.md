# arxos-core

Core library for Arxos: local-first content-addressed as-built repository.

## Responsibilities

- **Content addressing**: Canonical CBOR + BLAKE3 CIDs
- **Object schema**: Building, Floor, Space, Surface, Opening, Equipment, Run, Annotation, … + signatures. Schema v2 adds optional Fact fields (`extent`, `sigma_mm`, `support_count`, `evidence`, `host_entity`); v1 objects still load.
- **State / fuse / realize**: `BuildingState` is \(S : EntityId \to Fact\). `fuse` geometrically merges two versions of the same entity on commit/merge. `realize` produces solids \(B = R(S)\) (v1 boxes; v2 clipped `outline_xy` + `voids`, box fallback). Projectors (IFC / USD / ASCII) consume \(B\), never a writable store.
- **Roots**: Delta commits, checkpoints, materialization, sync closures, controller auth
  (two sign laws; adopt = self-consistency + replica continuity; first contact is TOFU)
- **Spatial index**: Versioned R-tree as ordinary CAS objects
- **Repository**: Building head, working set, capture/commit (RoomPlan mapping in `capture::roomplan`)
- **Scoring**: Deterministic contributor points (diagnostic; fiat settlement is off-band). `SIGMA_EXCLUDE_MM` lives in `measure`; scoring must not import `realize`. `Object` is the envelope; fuse / realize / capture hold behavior.

See the root [README](../README.md) for product identity, architecture, and Phase-0 boundaries.

## Store contract

These rules are non-negotiable. New code that violates them will be rejected.

1. **CAS purity.** `ObjectStore` is a filesystem content-addressed store: `has` / `get` / `get_bytes` / `put` / `put_bytes`. No query, signing, collapse, scoring, or indexing algorithms live on it.
2. **Single domain writer.** Building-scoped objects and roots go through `BuildingRepository` (capture → stage → commit, ingest → adopt, merge). Do not take an exclusive lock and `put` on a raw `ObjectStore` for building data.
3. **Derived layers are readers.** Working set, scoring, verification, entity collapse, spatial *queries*, and export consume `ObjectRead` or a closed `RootClosure` / `ClosureView`. They must not take a writable store.

### Roots: two sign laws, two checks

- **Leaves** (`Object::sign`): optional provenance on `header.author` / `header.signature`. CID includes the signature.
- **Roots** (`RootBody::sign`): required authority in `body.authors`. `into_object` blanks `header.signature`. `Object::verify_signature` on a Root is defined to fail.
- **`verify_with_store`**: self-consistency of a Root versus the Building in *that Root's* active set. Local `commit` uses this and nothing else.
- **Adopt / production pull** (`allow_untrusted = false`, `set_head = true`): self-consistency **plus** replica continuity (`verify_continuous_with_local`). Remote authors must be controllers of *this replica's* current Building, and the remote Root must descend from `head_root` (`previous_root` / `merge_parents`). A full-set checkpoint with `previous_root = None` against an existing head is a second genesis and is rejected.
- **First contact** (`open_or_follow` with `head_root == None`): TOFU after self-consistency, unless `AdoptOptions.expected_controllers` / `--trust-controllers` pins the remote Building keys.
- **`allow_untrusted`**: explicit disaster-recovery hatch. Not import, not the production fetch default, not a warning — the head moves. Ingest may store untrusted bytes; heads do not advance on them by default.
- **`allow_partial`**: cannot become head. Metadata-only ingest must leave `head_root` unchanged.

### Preferred types for new code

| Intent | Type |
|---|---|
| Read any CID | `R: ObjectRead + ?Sized` |
| Write CAS bytes (index builders, capture blob helpers) | `W: ObjectWrite + ?Sized` |
| Building capture / commit / adopt / ingest | `BuildingRepository::open` (exclusive lock) |
| Read a building (score, verify, export, status) | `BuildingRepository::open_read` (no flock) |
| Export or verify a frozen root | `RootClosure::collect` then `ClosureView` |
| Wire ingest (sync / import) | `ObjectIngest` on the repository |

`open` / `init` / `open_or_follow` hold `store.lock` exclusively for the handle lifetime (single writer). `open_read` takes no flock: concurrent readers are allowed, and they neither block nor wait for a writer. Object files and `BuildingRecord` are written with temp+rename, so each read is a consistent snapshot of one file; a commit racing a read can still leave the head pointer slightly stale relative to new objects (TOCTOU). Mutating methods on a read handle return `Error::Store`.

### Inbox (push ≠ adopt)

Pending contributor Facts live in **meta**, not a new object type:

```text
<meta/inbox/<building_id>.json>
```

`PutObject` / `PushFacts` ingest canonical bytes into the CAS and append leaf CIDs to that file. They **never** call adopt or move `head_root`. `BuildingRepository::inbox_apply` (controller key) stages those CIDs and `commit`s — the same fuse-on-commit path as capture.

When `net serve` holds `store.lock`, apply runs **in that process** via `$STORE/meta/serve.sock` (`BuildingRepository::open_assuming_exclusive`). A second `open` from another process still fails closed. Stale sockets are unlinked only after flock is taken.

### Allowed `ObjectStore` construction

The concrete filesystem type is for **opening a path**, not for passing around as an API:

- Process edges: CLI debug commands, FFI `put_blob` / `show_root`, `export_root_*` given only a path, `arxos-edge` serve
- Test setup that creates a temp directory
- Filesystem tooling (`list_cids`, `rebuild_index`, `store.lock`)

Do not add public methods that return `&ObjectStore`. `MemoryMesh::attach` takes a path.

### How to extend

- **New reader** (score, verify, query, export): take `R: ObjectRead + ?Sized`. For a whole root, prefer `RootClosure` so you do not hold a live handle.
- **New writer path** for building data: add a method on `BuildingRepository`. Helpers may take `ObjectWrite` only if the repository (or commit) is the caller.
- **New store backend**: implement `ObjectRead` + `ObjectWrite` (`Send + Sync`). Do not fork `ObjectStore` internals into callers.

## Verification

```bash
cargo test -p arxos-core
```
