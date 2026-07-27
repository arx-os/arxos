# Arxos Technical Architecture, Design & Engineering Plan

**Greenfield rebuild based on the lived-experience architecture**  
**Version 0.1 — 2026-07-27**

This document is the single source of truth for rebuilding Arxos from scratch according to the architecture we defined. It prioritizes the lived experience (iOS LiDAR + text capture, AR registration in physical space, building-as-repository, databaseless, DePIN) and explicitly excludes general 3D rendering ownership.

## 1. Guiding Principles

* **Lived experience first**: The primary loop is a person standing in a real building with a phone.
* **Databaseless**: No central or general-purpose database in the critical path. State is content-addressed objects + signed Merkle roots.
* **Building = Repository**: Each building is an independent, versioned, forkable object graph identified by a stable ID and a current root hash.
* **No 3D rendering by Arxos**: Geometry exists as data for spatial reasoning, AR anchoring, and export only. Visualization belongs to external tools.
* **Partial by default**: Devices only ever materialize the objects they need (spatial region, system, or explicit set).
* **Interoperability as projection**: The object graph is canonical. USD is the preferred modern interchange; IFC is a first-class legacy gateway; native CAD plugins are optional accelerators.
* **DePIN native**: Every meaningful write is signed and attributable. Economic signals can flow to real-world contributors.
* **Rust core, thin native shells**: Shared logic in Rust; iOS is a first-class client via UniFFI; edge nodes run the same core natively.

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    iOS Capture / AR Client                  │
│          (SwiftUI + ARKit + RealityKit + UniFFI)            │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     Rust Core Library                       │
│  Object Model · Hashing · Merkle Roots · Spatial Index ·    │
│  Validation · Canonicalization · Format Translators         │
└──────┬──────────────────────────────┬───────────────────────┘
       │                              │
       ▼                              ▼
┌──────────────┐              ┌──────────────────────┐
│ Local Object │              │  Networking Fabric   │
│ Store (CAS)  │◄────────────►│  (Iroh primary)      │
└──────────────┘              └──────────────────────┘
       │                              │
       │                              ▼
       │                      ┌──────────────────────┐
       │                      │ Discovery & Root     │
       │                      │ Anchoring (mDNS +    │
       │                      │ optional L2 registry)│
       │                      └──────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Interop Gateways (projections)                 │
│         OpenUSD (primary) · IFC · Native CAD plugins        │
└─────────────────────────────────────────────────────────────┘
```

DePIN verification and incentive logic sits alongside root transitions and can be evaluated by any node that holds the relevant objects.

## 3. Core Data Model

### 3.1 Object

Every piece of data is an immutable, content-addressed object:

```rust
struct Object {
    header: ObjectHeader,          // type, schema version, created, author, signature
    body: ObjectBody,              // typed payload
}
```

* **CID**: BLAKE3 hash of the canonical CBOR serialization of the object.
* **Types (initial set)**: Building, Floor, Space, Surface, Opening, Equipment, System, Circuit, Sensor, Fixture, Annotation, PointCloudChunk, Mesh, BoundingVolume, Relationship, SpatialIndexNode, Root, Provenance / attestation wrappers.
* Objects may reference other objects only by CID. No mutable pointers.

### 3.2 Root (Repository State)

```rust
struct Root {
    building_id: BuildingId,
    previous_root: Option<Cid>,
    objects: BTreeSet<Cid>,
    spatial_index_root: Option<Cid>,
    timestamp: u64,
    authors: Vec<Signature>,
}
```

The CID of a Root is the current state of the building repository.

### 3.3 Building Identity

* Stable BuildingId (DID or ULID + controller keys).
* Controller key(s) or multisig that can designate “official” roots.
* Anyone can fork by creating a new root that references a previous one.

### 3.4 Spatial Handling

* Every spatially relevant object carries a pose or is attached to a parent that does.
* A versioned spatial index (R-tree or hierarchical grid) is stored as ordinary objects and referenced from the Root.
* Queries are “give me all objects intersecting this volume / floor / frustum”.

## 4. Key Subsystems

### 4.1 Local Content-Addressed Store

Directory of objects named by CID (Git-style fan-out). Optional thin index (rebuildable) mapping CID → type + coarse bounds for fast filtering.

### 4.2 Rust Core Library (arxos-core)

Canonical serialization (CBOR), BLAKE3 + CID generation, Merkle / root computation, spatial index construction and query, object validation and schema evolution rules, signature verification, UniFFI surface for Swift.

### 4.3 iOS Client

AR session management and relocalization, LiDAR / RoomPlan capture pipeline → object creation, annotation UI, working-set management, commit flow, AR overlay of nearby annotations (no general 3D model viewer).

### 4.4 Networking (Iroh)

Announce new Roots via gossip, request objects by CID, direct connections preferred; relays as fallback, local-network discovery via mDNS.

### 4.5 Interop Gateways

* `arxos-usd`: high-quality bidirectional OpenUSD mapping
* `arxos-ifc`: bidirectional IFC translator with identity preservation
* Future: thin native plugins (Revit etc.)

### 4.6 DePIN Layer

All Roots and important objects are signed; App Attest + optional spatial consistency proofs; minimal on-chain registry on Base or equivalent; scoring and rewards can begin off-chain.

## 5. Technology Stack (Locked)

| Layer | Choice | Notes |
|-------|--------|-------|
| Core logic | Rust | Single source of truth |
| Hashing | BLAKE3 | Fast, secure |
| Object serialization | CBOR (ciborium) | Compact + deterministic |
| Signatures | ed25519-dalek | |
| Spatial index | rstar or custom hierarchical | Versioned as objects |
| Mobile UI / AR | Swift + SwiftUI + ARKit + RealityKit | |
| Rust ↔ Swift | UniFFI | |
| Local store | Content-addressed files | |
| Networking | Iroh (primary) | |
| USD | OpenUSD | Preferred interchange |
| IFC | Custom Rust translator | Strong legacy support |
| Discovery | mDNS + optional L2 registry | |
| Token / anchoring | Base L2 | Minimal contracts only |

## 6. Repository & Project Structure

```
arxos/
├── core/                 # arxos-core (Rust)
├── gateways/
│   ├── usd/
│   └── ifc/
├── networking/           # Iroh integration
├── ios/                  # SwiftUI app
├── edge/                 # Native edge node binary
├── cli/                  # Inspection & admin tools
├── contracts/            # Minimal L2 registry (optional early)
└── docs/
    └── architecture/     # This document
```

## 7. Phased Engineering Plan

| Phase | Focus | Duration |
|-------|--------|----------|
| **0** | Foundation: Object, CAS, Root, UniFFI, CLI | 2–3 weeks |
| **1** | Mobile capture loop (AR + LiDAR + commit) | 3–4 weeks |
| **2** | Multi-device & Iroh networking | 3 weeks |
| **3** | Spatial index, partial load, merge | 2–3 weeks |
| **4** | OpenUSD + IFC interop | 4 weeks |
| **5** | DePIN & hardening | ongoing |

Each phase ends with a working, demonstrable vertical slice and automated tests.

## 8–10. Testing, Risks, Next Steps

See the full plan in project history. Phase 0 deliverables:

1. Monorepo structure
2. arxos-core skeleton
3. UniFFI + Swift hello-world
4. CLI (`arx`): `object put`, `root create`, `root show`
5. Initial object schema documentation
