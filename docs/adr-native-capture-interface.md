# ADR: Native iOS ↔ agent capture interface (thin hand-off)

| Property | Value |
| :--- | :--- |
| **Status** | **Accepted** (2026-07-24) — design only; **no implementation** in this decision |
| **Decision** | **11** |
| **Type** | Interface design (native peripheral → agent spine) |
| **Complements** | Decision 9 (web landing) · Decision 10 (proposed-first capture) |
| **Does not supersede** | IFC-only BIM · agent write authority · file LiDAR path · L1 pilot packet |
| **Related** | [`adr-capture-model.md`](./adr-capture-model.md) · agent `lidar.import` · `import_lidar_path` |

---

## Recommendation (primary hand-off for v1)

**Choose A — Reuse/extend existing file LiDAR ingest (PLY/LAS/XYZ) via the agent, with clear provenance.**

| Option | Verdict for v1 |
| :--- | :--- |
| **A — File LiDAR → existing agent `lidar.import` / CLI import** | **Primary** |
| **B — Domain-shaped RPC (proposed rooms only)** | Deferred until phone already has reduced structure |
| **C — Hybrid (file geometry + structure RPC)** | Evolution after A works; not v1 surface |

### Rationale (thinnest + principle-aligned)

1. **No new package format.** Decision 10 prefers extending existing ingest; the hardened file path already does geometry → proposed rooms → `finalize_ingest` → `building.yaml`.  
2. **One structure-extraction codebase** on the capture node (agent/CLI). Avoids dual heuristics (Swift + Rust) and dual bugs.  
3. **Geometry stays disposable** on the agent machine under `imports/`; not a second SSOT.  
4. **Authority is unchanged:** client never writes YAML; agent owns validate + durable write.  
5. **B is thinner on the wire** when RoomPlan already yields room polygons — but that **moves extraction to the phone** and invents a new contract before A is proven with real field files. Defer B until A is boring.  
6. **C is the eventual shape** (heavy cloud file + optional structure patch) — not required for first native vertical slice.

**v1 native job:** capture/export a point cloud (or RoomPlan mesh converted to PLY/XYZ) → deliver bytes + provenance to agent → reuse `lidar.import` (or equivalent file drop + import).

---

## 1. Goal of the interface

A future **native iOS** client supplies **geometry** (and later, optionally, already-reduced proposed structure). The **agent** (capture node) owns:

```text
receive → structure assist (if geometry) → mark proposed → finalize_ingest → validate → building.yaml
```

The client may show local previews and personal AR; **durable building truth** remains only on the capture node SSOT.

---

## 2. Primary hand-off style (A) — contract sketch

### 2.1 Transport (reuse)

| Mechanism | Role |
| :--- | :--- |
| Agent WebSocket JSON-RPC (existing) | Preferred for LAN/hotspot field use |
| Existing method shape | Extend **`lidar.import`** (base64 + filename + `merge` + `light_mode` + `voxel_size`) |
| Alternative | Client writes file into agent-watched `imports/` inbox if/when a drop-watcher is productized — same spine |

No new capture.json product format for v1.

### 2.2 What the client may send (v1)

| Allowed | Notes |
| :--- | :--- |
| Point cloud file bytes | PLY (ascii/binary as supported today), LAS/LAZ if agent path supports, XYZ |
| Filename + content type hint | For extension routing |
| Merge flag | Default **merge into existing** `building.yaml` when present |
| Light-mode / voxel hints | Optional; agent may override for resource safety |
| Provenance strings | Device id, capture timestamp, app version, coordinate note |

### 2.3 What the client must **not** send as durable truth

| Forbidden as authority | Why |
| :--- | :--- |
| Full `building.yaml` patch / replace | Dual SSOT |
| `review_status=accepted` on field capture | Decision 10 proposed-first |
| Official IFC export request as sole product path without host review | Export remains capture-node / CLI spine |
| “This is survey-grade official” flags | Honesty / liability |

### 2.4 Agent obligations after receive

1. Size/point refuse per `docs/resource-limits.md`.  
2. Run existing LiDAR pipeline (downsample → floors/rooms/equip assist → **proposed**).  
3. `finalize_ingest` + validation; refuse write on hard errors.  
4. Persist `building.yaml` only on success.  
5. Return honest summary: floors/rooms (segmented vs fallback), equipment count, LossReport lines, paths.

---

## 3. Data contract (minimal)

### 3.1 Request (logical fields — map onto `lidar.import` params)

```text
filename: string          # e.g. scan-2026-07-24.ply
data: base64              # file bytes
merge: bool               # default true when building.yaml exists
light_mode: bool          # default true on mobile-originated uploads
voxel_size: number        # meters; agent may clamp
provenance: {
  client: "ios_native"    # required when from phone
  client_version: string
  captured_at: ISO-8601
  device_model?: string
  note?: string           # e.g. "RoomPlan mesh → PLY export"
}
```

**Implemented on agent:** optional `provenance` object on `lidar.import` is stamped onto building metadata and rooms (`capture_client`, …). Pipeline still uses `capture_source=lidar_file`. See [native-file-handoff.md](./native-file-handoff.md).

### 3.2 Proposed marking (mandatory)

| Entity from this path | Required |
| :--- | :--- |
| Auto rooms / equipment | `review_status=proposed` |
| Provenance | `capture_source=lidar_file` (or `ios_native` once distinguished) |
| Heuristic | `occupancy_grid` / `bbox_fallback` as produced by agent today |

Client cannot force `accepted`.

### 3.3 Response (logical)

```text
ok | error
building_name, floors, rooms, equipment
proposed_rooms, proposed_equipment
report_summary[]          # LossReport honesty lines
yaml_path                 # always building.yaml on capture node
```

### 3.4 Explicitly out of band

| Concern | Owner |
| :--- | :--- |
| Durable YAML content | Agent/CLI spine only |
| Official IFC export | Capture node `arx export` / agent export RPC (same exporter); review-gated |
| Municipal / ownership | Later product |
| Personal AR rendering | Client-local; not ArxOS product requirement |

---

## 4. Authority rules

| Role | Authority |
| :--- | :--- |
| **Native iOS client** | Peripheral: capture geometry, optional local UX, upload to agent |
| **Agent** | Capture node / bridge: only durable writer of `building.yaml` |
| **CLI/TUI** | Same spine on host; primary operator UI |
| **Static web** | Landing only (Decision 9) — not a party to this interface |

```text
iOS native  ──geometry file──►  Agent  ──finalize/validate──►  building.yaml
                                      │
                                      └── LossReport + proposed entities
```

---

## 5. Deferred path B (domain RPC) — not v1

When (and only when) the phone already reduces RoomPlan/ARKit output to **domain candidates**:

```text
proposed_rooms[]: { name?, bbox|polygon, floor?, provenance }
```

- All items **proposed**.  
- Agent merges via structure merge policy + finalize — **no** client YAML.  
- Still no mesh product store.  
- Implement only if A is proven and phone-side reduction is clearly better than agent re-extraction.

Path **C** = A + optional B in one session; design later.

---

## 6. Non-goals (this decision)

- No Xcode project, Swift code, or app scaffold.  
- No ownership / municipal / reward flows.  
- No 3D viewer or mesh editor inside ArxOS.  
- No return of interactive PWA capture.  
- No heavy multi-file capture package as the v1 product format.  
- No Horizon C work.

---

## 7. Open questions (need human input before implement)

1. **v1 geometry format on phone:** export PLY from RoomPlan/ARKit pipeline vs third-party scan app — which is first pilot hardware path?  
2. **Upload size:** is base64 over WS acceptable for room-scale PLY, or must v1 use HTTP multipart / chunked upload / local inbox drop?  
3. **Auth model for native:** reuse agent root token, or separate capability-scoped device token?  
4. **When to open B:** after first real file-from-phone success, or only if agent extraction quality fails RoomPlan-class data?  
5. **Coordinate systems:** require client to declare units/meters and “building_local” assumption, or agent always treats as unitless-local meters?

---

## 8. Implementation sequence

1. ~~Prove A with laptop file path~~ — file ingest hardened + agent import.  
2. ~~Provenance on wire~~ — optional `provenance` on `lidar.import` (agent).  
3. **Next:** Native app (when opened): capture → export cloud file → `lidar.import` with provenance.  
4. Field-test one room; log false +/− (R1) in [field-truth-log.md](./field-truth-log.md).  
5. Only then consider B for RoomPlan-native structure.

---

## One-sentence summary

**v1 native interface is “send a LiDAR file to the agent”; the agent alone turns geometry into proposed structure and writes building.yaml — no new package format, no client-side SSOT.**
