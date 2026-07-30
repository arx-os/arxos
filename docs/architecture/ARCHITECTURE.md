# Arxos Technical Architecture & Design Specification

This document provides the formal architectural specification for Arxos, a local-first, content-addressed spatial data repository system designed for the built environment.

---

## 1. System Overview

Arxos functions as a versioned, local-first object graph representing buildings and spatial structures. The system is designed to run on resource-constrained mobile hardware and edge devices without requiring a centralized database in the critical path.

```
┌─────────────────────────────────────────────────────────────┐
│                    iOS Capture Client                       │
│          (SwiftUI + RoomPlan Ingestion + UniFFI)            │
│                            │                                │
│                            ▼                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                  UniFFI FFI Gateway                     │ │
│ └──────────────────────────┬──────────────────────────────┘ │
│                            │                                │
│ ┌──────────────────────────▼──────────────────────────────┐ │
│ │                     Rust Core Library                   │ │
│ │   Object Model · Hashing · signed Roots · R-Tree        │ │
│ └──────┬──────────────────────────────┬───────────────────┘ │
│        │                              │                     │
│        ▼                              ▼                     │
│ ┌──────────────┐              ┌──────────────────────┐      │
│ │ Local Object │              │  Networking Fabric   │      │
│ │ Store (CAS)  │◄────────────►│  (Iroh Sync Protocol)│      │
│ └──────────────┘              └──────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Data Model & Content Addressing

### 2.1 Immutable Objects
Every data element is stored as an immutable, content-addressed envelope:

```rust
pub struct Object {
    pub header: ObjectHeader,
    pub body: ObjectBody,
}

pub struct ObjectHeader {
    pub object_type: ObjectType,
    pub schema_version: u32,
    pub created: u64,
    pub author: Option<PublicKey>,
    pub signature: Option<AuthorSignature>,
}
```

- **Content Address (CID)**: The unique identifier of an object is a `Cid`, computed as the BLAKE3-256 hash of the canonical CBOR serialization of the entire object (including header and body payload).
- **Signing Flow**:
  1. Construct the object with `signature = None`.
  2. Serialize using canonical CBOR (`ciborium`).
  3. Sign the bytes using Ed25519; store the resulting `AuthorSignature` in the header.
  4. Compute the final CID over the signed canonical CBOR bytes.

---

## 3. Roots, Version Control, & History Materialization

### 3.1 Root Schema
A `Root` object represents a repository commit and defines the active state of a building.

```rust
pub struct RootBody {
    pub building_id: BuildingId,
    pub previous_root: Option<Cid>,
    pub merge_parents: BTreeSet<Cid>, // concurrent tips when this is a merge
    pub added: BTreeSet<Cid>,
    pub removed: BTreeSet<Cid>,
    pub objects: Option<BTreeSet<Cid>>,
    pub spatial_index_root: Option<Cid>,
    pub timestamp: u64,
    pub authors: Vec<AuthorSignature>,
    pub message: Option<String>,
}
```

### 3.1.1 Root authorization

Every root author signature is verified cryptographically **and** against the
building's controller set: each author public key must appear in
`Building.controller_keys` for the Building object in the root's materialized
active set. Commit and adopt fail closed on unauthorized authors. The optional
`AdoptOptions::allow_untrusted` flag disables this check for import / recovery
paths only.

### 3.2 Checkpoint Policy
- **Delta-Friendly Commits**: To prevent the CBOR size of roots from scaling linearly with the number of objects, commits write only the `added` and `removed` sets relative to the parent.
- **Emission Policy**: A full-set checkpoint root (where the `objects` field is populated with `Some(BTreeSet)`) is emitted:
  - On the initial commit (`previous_root = None`).
  - When the delta depth (number of consecutive delta commits since the last checkpoint) reaches $N = 50$.
- **Materialization Walk**: Reconstructing the active object set starts at the head root and walks backwards along the `previous_root` chain, accumulating additions and subtracting removals. The walk terminates immediately when it hits the nearest checkpoint root, bounding materialization latency to $O(\text{checkpoint\_interval})$.

### 3.3 Bounded Closure Sync
Sync operations utilize `get_root_closure_blobs` to calculate the minimal set of objects required to transfer a root state:
1. Walk the root history backwards, terminating at the nearest checkpoint root.
2. Collect the bytes of all traversed roots and the active domain objects within the materialized active set of the target tip.
3. Recursively collect all `SpatialIndexNode`s branching from the root's `spatial_index_root`.
- **Guarantee**: Devices sync complete, queryable root states without fetching unbounded history.
- **Fail closed**: Missing active objects or index nodes cause the closure collection (and subsequent adopt) to fail unless an explicit `allow_partial` option is set. Incomplete closures must not become head under normal operation.

### 3.4 Merge parents
When two concurrent roots are merged, the result records both tips in
`merge_parents` while keeping a single linear `previous_root` (the newer tip)
for delta materialization. This preserves honest multi-device history without
requiring a full multi-parent CRDT.

---

## 4. Spatial Indexing

Spatially queryable geometry is stored in a versioned binary R-tree index structured as ordinary content-addressed objects (`SpatialIndexNode`).

### 4.1 Index Construction Determinism
To guarantee that identical geometry produces identical CIDs across different runs:
- Nodes use a fixed timestamp of `created: 0` in their headers.
- Centroids are sorted stably, tie-breaking by CID comparison during splits.
- Leaf node lists and child references are sorted deterministically.

### 4.2 Incremental R-Tree Builder
Instead of rebuilding the R-tree from scratch on every commit, new geometry is added via `insert_incremental` in $O(\log N)$ logarithmic write time:
- **Structural Sharing**: Unchanged subtrees are reused by reference, keeping new index node allocations minimal.
- **In-Memory Caching**: Reads and parent splits are cached inside an in-memory `RefCell<BTreeMap<Cid, Object>>` during insertion traversal.
- **Reachability Garbage Collection**: A DFS sweep starting from the final mutated root CID checks the cache, flushing only reachable index nodes to the disk store. Unreferenced intermediate split states are discarded in-memory.

---

## 5. Repository State & Partial Materialization

### 5.1 Caching & Staging
- **Memory Cache**: `BuildingRepository` maintains a private `active_objects: BTreeSet<Cid>` representing the materialized set of the current head root. This cache is populated at repository open time and updated incrementally during commit or adopt operations, keeping active membership checks at $O(1)$.
- **Partial Materialization**: Opening or adopting a root pins only the head Root and the core Building metadata in memory. Domain objects (surfaces, spaces) are lazily loaded into the session `WorkingSet` via spatial query refinement filters (`load_region`, `load_floor`).

---

## 6. Mobile Capture & RoomPlan Ingestion

### 6.1 Matrix Transformation Math
Ingesting ARKit/RoomPlan geometry (Y-up, right-handed, meters) requires explicit coordinate transformation into the canonical Arxos object schema:
- **Pose Extraction**: The 4x4 column-major matrix `T` is decomposed. Translation is mapped directly from column 3: `[tx, ty, tz] = [T[12], T[13], T[14]]`. The upper-left 3x3 rotation matrix is converted to a normalized quaternion `[qx, qy, qz, qw]`.
- **World Bounding Box (AABB)**: Local boundary dimensions `[w, h, d]` are used to reconstruct the 8 local vertices `[+/- w/2, +/- h/2, +/- d/2]`. These are transformed to world coordinates via matrix multiplication, and the absolute minimum and maximum values along each axis are computed to yield a tight world-space `Aabb`.
- **Timestamp Gating**: Ingested geometry structures are assigned a stable `created: 0` timestamp to ensure stable CID generation.

### 6.2 Xcode Linking Gating
The Swift façade utilizes a compile-time hard-gate to prevent debug shims from leaking into production:
```swift
#if !canImport(ArxosCoreFFI) && !ALLOW_SHIM
#error("Real UniFFI backend (ArxosCoreFFI) is required for production builds. Define ALLOW_SHIM if you are working on UI styling / demo without the Rust backend.")
#endif
```

---

## 7. Interop Gateways

Gateways project the canonical Arxos object graph into standardized engineering formats.

| Gateway | Crate | Role & Projection Mechanics |
|---------|-------|-----------------------------|
| **OpenUSD** | `arxos-usd` | Generates human-readable OpenUSD ASCII (`.usda`) layers. Spatial bounding volumes map to USD Xforms. Identity is preserved by embedding `arxos:cid` and `arxos:buildingId` layer metadata. |
| **IFC** | `arxos-ifc` | Converts spaces and surfaces into standard IFC4 STEP text files. identity is preserved by attaching `Pset_ArxosIdentity` property sets containing the BLAKE3 CID, and deriving stable IFC GlobalIds deterministically from the object CIDs. |

---

## 8. Guarantees & Limitations

### 8.1 Factual System Guarantees
- **Integrity**: Any object read is verified by recalculating its BLAKE3 hash. Signature validation fails closed on invalid remote root pulls by default.
- **Authorization**: Root authors must be members of `Building.controller_keys` (fail closed on commit/adopt).
- **Complete Closures**: Root sync closures and adopt require all active objects (and spatial index root when set) to be present unless `allow_partial` is explicit.
- **Bounded Sync**: Networking fetches only the objects back to the nearest checkpoint, avoiding full repository history transfers.
- **CAS hot path**: Object puts write only content-addressed files (temp + rename). The optional thin `index.cbor` is rebuild-on-demand, not updated per put.
- **Logarithmic Commits**: Incremental indexing aims for $O(\log N)$ spatial write complexity relative to building size (binary tree implementation; fanout improvements are future work).

### 8.2 Current Design Limitations
- **No Rendering**: Arxos does not perform 3D graphics rendering; geometry translation is limited to spatial reasoning, queries, and file export formats.
- **Scope Limits**: True distributed multi-building spatial indexing, tree compression/packing, MEP system details in IFC export, and C++ OpenUSD bindings are explicitly out of scope.
