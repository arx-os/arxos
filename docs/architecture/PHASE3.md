# Phase 3 — Spatial & Scale

**Status:** Implemented (2026-07-27)

## Goals

* Versioned spatial index (content-addressed)
* Partial loading by volume / floor
* Merge of two concurrent scans (union + simple conflict rules)
* Stress test with floor-sized synthetic data

## Design principles

1. **Index is data, not a sidecar DB.**  
   Nodes are `SpatialIndexNode` objects in the CAS. The Root stores
   `spatial_index_root: Option<Cid>`.

2. **Hierarchical AABB tree.**  
   Leaf capacity 16; split on longest axis by centroid median; max depth 24.
   Deterministic ordering for stable CIDs.

3. **Partial by default (enforced).**  
   `open` / `adopt_root` pin only the head Root (+ building). Domain objects
   enter the working set via `load_region`, `load_floor`, or query-driven
   materialization (`annotations_near`).

4. **Query path.**  
   Coarse traverse of index nodes → refine by loading hit objects and testing
   true bounds. Falls back to linear scan if no index is attached.

5. **Merge rules.**  
   - Union of object CIDs  
   - Annotation proximity ≤ 0.35 m **and** same normalized text → keep newer  
   - Same pose region, different text → **keep both**  
   - Rebuild spatial index on merge  

6. **Scale.**  
   CI scale test: 40×40 annotation grid (~1.6k objects), index build + partial
   load of a 5×5 m region. Larger floors use the same algorithms.

## API surface

### Core

| API | Role |
|-----|------|
| `spatial::build_index` | Write index nodes; return root CID |
| `spatial::query_index_refined` | Volume query |
| `BuildingRepository::query_volume` | Head-aware query |
| `BuildingRepository::load_region` | Partial materialize |
| `BuildingRepository::load_floor` | Floor slab / floor-link load |
| `BuildingRepository::merge_root` | Concurrent scan merge |
| `merge::merge_roots` / `plan_merge` | Pure store-level merge |

### CLI

```bash
arx spatial build $BID --commit
arx spatial query $BID --min-x … --max-z …
arx spatial load  $BID --min-x … --max-z … [--limit N]
arx spatial load-floor $BID $FLOOR_CID

arx merge plan  $ROOT_A $ROOT_B
arx merge apply $BID $OTHER_ROOT [--message …]
```

## Tests

* Unit: AABB, index build/query, merge dedupe  
* Integration: `spatial_scale` floor grid + partial load  
* CLI vertical slice: simulate → query → load → rebuild  

## Out of scope (later)

* R-tree / rstar swap-in (API stays the same)  
* 3-way CRDT merge with economic attribution  
* GPU/accelerate index build  
