# Design: Blob Tiering & Size Policy (Phase 2)

## Decision

- Large binary payloads live in `ObjectBody::Blob` objects.
- `PointCloudChunk` / `Mesh` hold metadata + optional `*_blob` CIDs.
- Legacy inline `points` / `vertices` / `indices` remain deserializable.
- New captures always externalize point payloads into a Blob.
- `ObjectStore::put` rejects objects larger than `MAX_OBJECT_BYTES` (4 MiB).
- Root closures support `include_blobs: false` for metadata-first sync.

## Size limit rationale

4 MiB is large enough for domain metadata and small blobs, small enough to
keep Pi-class sync and CAS puts bounded. Dense clouds must be chunked into
multiple Blob objects by the capture path.
