# Field language (CLI + agent + iOS)

**Status:** Living direction (2026-07-24)  
**Authority:** Decision 10 · 11 · 12 · [agent-client-interface.md](./agent-client-interface.md)

This document is the **shared vocabulary** for growing the building model from the capture node and peripheral clients. It is **not** a second SSOT and **not** a finished product language.

---

## Current honesty

| Surface | What exists | What does not |
| :--- | :--- | :--- |
| **CLI `arx edit`** | Text DSL → finalize → `building.yaml` | Polished interactive editor |
| **Agent** | JSON-RPC methods + **structured `field.*`** | Domain-only RoomPlan RPC (path B deferred) |
| **iOS companion** | Lab terminal: connect, file scan, label, commit, export | Camera / RoomPlan view, rich review UI |
| **Grammar** | `arx edit help` · this doc · ingest `text.rs` | Stable “product English” without DSL |

**Lab green (2026-07-24):** iOS companion **connects** to agent via **HTTP `POST /rpc`**, can call building/git methods. Full scan→label→commit→IFC lab pass is the next system test, not a claim of field readiness.

---

## Layers (do not collapse them)

```text
Human / app intent     “Label this switch in Room 1 as proposed”
        │
        ▼
Structured field RPC   field.label { room, equipment }     ← prefer for clients
        │
        ▼
Text DSL (quoted)      add equipment "Light Switch" room="Room 1" …
        │
        ▼
Ingest spine           apply → finalize_ingest → validate → building.yaml
```

Free-form `edit.apply` / `arx edit file` remains for power users and scripts.  
**Mobile clients must not invent quoting** — use `field.label` / `field.accept_room`.

---

## Structured agent methods (v1 additive)

| Method | Params | Effect |
| :--- | :--- | :--- |
| `session.hello` | `{}` | Protocol version, supported transports/methods |
| `field.label` | `room`, `equipment` | Add/mark equipment **proposed**; create **proposed** room if missing |
| `field.accept_room` | `room` | `review_status=accepted` for room |

Implementation builds quoted DSL in core (`src/ingest/field_script.rs`) and applies via the same path as `edit.apply`.

Capability: `field.*` requires `edit.apply` capability on the agent token.

---

## Text DSL (power path)

Print live grammar:

```bash
arx edit help
```

Rules that repeatedly bite field work:

1. **Multi-word names need double quotes:** `"Room 1"`, `"Light Switch"`.  
2. **No embedded `"` or newlines** in names.  
3. **Field capture is proposed** until an explicit accept.  
4. **Accept is human** — not automatic on import.

Full grammar source: `src/ingest/text.rs` · builders: `src/ingest/field_script.rs`.

---

## Direction (recommended build order)

| Priority | Work | Repo |
| :---: | :--- | :--- |
| **1** | Structured `field.*` + `session.hello` + docs | **core** (this pass) |
| **2** | iOS uses `field.*` / HTTP; honest status docs | **ios** + core |
| **3** | CLI verbs / better errors / `arx field …` thin wrappers | core |
| **4** | In-app RoomPlan → file → `lidar.import` (still path A) | ios |
| **5** | Domain structure RPC (path B) only after A is boring | core + ios |
| **6** | Operator review UI (not monospaced log forever) | ios / optional desktop |

**Out of scope until explicit open:** Horizon C rewards, browser capture, dual SSOT on phone.

---

## Related

- [agent-client-interface.md](./agent-client-interface.md) — wire contract  
- [ios-lab-loop.md](./ios-lab-loop.md) — lab E2E  
- [adr-native-capture-interface.md](./adr-native-capture-interface.md) — Decision 11  
- [adr-capture-model.md](./adr-capture-model.md) — Decision 10 proposed-first  
