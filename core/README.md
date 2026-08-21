# arxos-core

Core library for Arxos: local-first content-addressed as-built repository.

## Responsibilities

- **Content addressing**: Canonical CBOR + BLAKE3 CIDs
- **Object schema**: Building, Floor, Space, Equipment, Annotation, … + signatures
- **Roots**: Delta commits, checkpoints, materialization, sync closures, controller auth
- **Spatial index**: Versioned R-tree as ordinary CAS objects
- **Repository**: Building head, working set, capture/commit
- **Scoring**: Deterministic contributor points (diagnostic; fiat settlement is off-band)

See the root [README](../README.md) for product identity, architecture, and Phase-0 boundaries.

## Store contract

These rules are non-negotiable. New code that violates them will be rejected.

1. **CAS purity.** `ObjectStore` is a filesystem content-addressed store: `has` / `get` / `get_bytes` / `put` / `put_bytes`. No query, signing, collapse, scoring, or indexing algorithms live on it.
2. **Single domain writer.** Building-scoped objects and roots go through `BuildingRepository` (capture → stage → commit, ingest → adopt, merge). Do not take an exclusive lock and `put` on a raw `ObjectStore` for building data.
3. **Derived layers are readers.** Working set, scoring, verification, entity collapse, spatial *queries*, and export consume `ObjectRead` or a closed `RootClosure` / `ClosureView`. They must not take a writable store.

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
