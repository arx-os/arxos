# Arxos Object Schema (Phase 0)

**Schema version:** `1`  
**Serialization:** Canonical CBOR via `ciborium` + Serde  
**CID:** `b3:` + hex(BLAKE3-256(canonical_cbor_bytes))

Objects are immutable. References to other objects are always CIDs.

## Envelope

```text
Object
├── header: ObjectHeader
│   ├── object_type: ObjectType      # must match body kind
│   ├── schema_version: u32          # >= 1
│   ├── created: u64                 # unix seconds
│   ├── author: Option<PublicKey>    # ed25519
│   └── signature: Option<AuthorSignature>
│       ├── public_key: PublicKey
│       └── signature: Signature     # over unsigned envelope CBOR
└── body: ObjectBody                 # tagged union (kind + data)
```

### Signing

1. Build object with `signature = None` (author may already be set).
2. Canonical-CBOR encode that unsigned object.
3. ed25519-sign the bytes; store `AuthorSignature` on the header.
4. Final CID is BLAKE3 of the **signed** object’s canonical CBOR.

Roots additionally carry a multi-author `authors` list on the root body; each
signs the root body with `authors` cleared.

## Object Types

| Type | Kind tag | Purpose |
|------|----------|---------|
| `building` | Building | Stable building identity + controllers |
| `floor` | Floor | Level within a building |
| `space` | Space | Room / zone |
| `surface` | Surface | Wall, floor plane, ceiling, etc. |
| `opening` | Opening | Door, window, penetration |
| `equipment` | Equipment | Installed equipment instance |
| `system` | System | Logical system grouping |
| `circuit` | Circuit | Electrical / control circuit |
| `sensor` | Sensor | Sensor instance |
| `fixture` | Fixture | Lighting / plumbing fixture |
| `annotation` | Annotation | Text / transcript + optional pose |
| `point_cloud_chunk` | PointCloudChunk | LiDAR chunk payload |
| `mesh` | Mesh | Geometry as data (not for Arxos rendering) |
| `bounding_volume` | BoundingVolume | AABB wrapper |
| `relationship` | Relationship | Typed edge between two CIDs |
| `spatial_index_node` | SpatialIndexNode | Versioned spatial index node |
| `root` | Root | Repository commit / head |
| `provenance` | Provenance | Attestation wrapper |
| `blob` | Blob | Opaque bytes (Phase 0 utility) |

## Shared geometry types

```text
Pose
├── position: [f64; 3]           # meters, building-local
└── orientation: [f64; 4]        # quaternion x,y,z,w

Aabb
├── min: [f64; 3]
└── max: [f64; 3]
```

## Root body

```text
RootBody
├── building_id: BuildingId
├── previous_root: Option<Cid>           # linear primary parent
├── merge_parents: BTreeSet<Cid>         # concurrent parents when this is a merge
├── objects: Option<BTreeSet<Cid>>
├── added: BTreeSet<Cid>
├── removed: BTreeSet<Cid>
├── spatial_index_root: Option<Cid>
├── timestamp: u64
├── authors: Vec<AuthorSignature>
└── message: Option<String>
```

The **object CID** of a `Root` object is the repository state identifier.

### Root authorization

Root authors must present valid ed25519 signatures over the unsigned root payload
**and** every author public key must appear in `Building.controller_keys` for the
building object in the root's active set. Adoption and commit fail closed when
authorization fails. `AdoptOptions::allow_untrusted` is an explicit escape hatch.

### Closure completeness

Serving or adopting a root requires the full active object set (and spatial index
root, when present) to be present in the local store unless
`AdoptOptions::allow_partial` / `ClosureOptions::allow_partial` is set.

## Building identity

Phase 0: `BuildingId` is a ULID string.  
Later: account/DID-linked controllers in the commercial control plane (pure fiat; no on-chain registry).

`Building.controller_keys` is the authoritative set of keys allowed to sign
repository roots for that building.

## JSON Schema (documentation)

Machine-readable JSON Schema sketches live alongside this file:

* `object-envelope.schema.json` — header + body envelope
* `root-body.schema.json` — root commit body

Validation in Rust is performed by typed Serde decode + `Object::validate()`.
Runtime JSON Schema validation is optional and not on the critical path.
