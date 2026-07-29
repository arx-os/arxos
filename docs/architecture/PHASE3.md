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
   `spatial_index_root: Option<Cid>`, and the full index tree is fetched as part of the Root sync closure.

2. **Hierarchical AABB tree.**  
   Leaf capacity 16; split on longest axis by centroid median; max depth 24.
   Deterministic ordering and a fixed header creation time (0) ensure stable CIDs.

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

6. **Scale & Performance.**
   - **Delta Roots**: To scale root sizes to hundreds of thousands of objects, root commits are stored as deltas (`added`/`removed` CIDs).
   - **Checkpointing Policy**: A full-set checkpoint root is written every $N = 50$ commits (or on initial commit), bounding the history materialization walk to $O(checkpoint\_interval)$.
   - **Incremental R-Tree Updates**: Committing new geometry batches inserts into the versioned R-Tree incrementally in logarithmic $O(\log N)$ write time, using structural sharing to preserve unchanged node CIDs.
   - **Reachability & Read Caching**: R-tree build runs are optimized via an in-memory RefCell cache. Intermediate traversal reads and split nodes are cached in memory; at the end of the batch insertion, only reachable tree nodes are flushed in bulk to disk.
   - **Closure/Sync Bounding**: Bounded closure sync (`get_root_closure_blobs`) halts at the nearest checkpoint root to avoid transferring unbounded historical chains over the network.

## API surface

### Core

| API | Role |
|-----|------|
| `spatial::build_index` | Write initial index nodes; return root CID |
| `spatial::insert_incremental` | Recursively insert batches of entries in $O(\log N)$ time |
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

* Unit: AABB, index build/query, merge dedupe, and strict R-tree determinism
* Integration: `spatial_scale` floor grid + partial load, and `scale_large` 5,000-object incremental commits verifying constant root size and correct spatial hits
* CLI vertical slice: simulate → query → load → rebuild

## Out of scope (later)

* True distributed spatial index (queries remain single-building scoped)
* Tree compression/packing optimization
* R-tree / rstar library swap-in (internal API stays the same)
* 3-way CRDT merge with economic attribution
* GPU/accelerate index build

