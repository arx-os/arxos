# Design: Stable Entity Identity (Phase 1)

Local-only note. Public summary lives in root README.

## Decision

- `EntityId` is a ULID string, stable across version updates of the same physical thing.
- Physical object bodies carry `entity_id: Option<EntityId>` (serde default `None`).
- `None` = legacy pure-CID identity: object never collapses with peers (singleton by CID).
- Every **version** remains a fully content-addressed object (CID = hash of bytes).
- A root’s active set still holds **version CIDs**, not EntityIds.
- At commit and merge, active sets are **collapsed** so at most one version CID
  per `EntityId` remains. Losers become `removed` relative to the parent set.

## Winner rule (deterministic)

Among versions of the same `EntityId`:

1. Higher `header.created` wins.
2. Tie → higher `Cid` wins.

## Explicit remove

`BuildingRepository::remove_object(cid)` / `remove_entity(entity_id)` stage CIDs
into `pending_removes` (persisted on `BuildingRecord`). Commit subtracts them
before collapse.

## Migration

Existing objects deserialize with `entity_id = None` and keep historical CIDs.
New captures assign a fresh `EntityId`. First intentional update of a legacy
object can stamp a new `EntityId` on the replacement version; the old CID is
removed from the active set via collapse/replace, not rewritten in place.
