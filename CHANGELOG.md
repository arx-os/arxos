# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Internals

- `SIGMA_EXCLUDE_MM` lives in `core::measure` (Fact layer). Scoring no longer
  imports `realize`. `realize` and `arxos_core::SIGMA_EXCLUDE_MM` re-export
  the same 500 mm law.
- RoomPlan host heuristic and hall fixtures extracted to `capture::host` and
  `capture::fixtures`. Mapping stays in `capture::roomplan`. Public paths
  through `roomplan::*` are unchanged.

## 0.2.0 - 2026-09-10

Complete capture → inbox → fuse → realize v2 → export loop on a developer
machine (simulate fixtures; field walk is out of band). Scoring policy v2 is
part of this cut (`policy_version = 2`, still diagnostic).

### Edge

- `arxos-edge status`: lock, sock, ticket file, inbox pending, head CID
  (read-only). Serve writes `$STORE/meta/serve.ticket` (0600) and does not
  print the full ticket to stdout (systemd journals). Apply does not restart
  the unit. Backup: copy the store while serve is stopped.

### Scoring (diagnostic)

- Policy v2: `support_count` bonus, penalty for unresolved opening hosts, penalty
  when \(\sigma > 500\) mm. `ScoreReport.policy_version` is 2. Same store +
  root + policy → same report. Still `diagnostic_only`; not payroll.

### Thin client

- After `PushFactsOk`, staged pending is cleared (CAS bytes remain). Incomplete
  or failed push writes `$STORE/meta/push_retry/<id>.json` (0600) and keeps
  staging so a force-quit can retry. iOS: ticket path does not local-commit
  on push failure; status is “pushed, pending apply” vs “local only (no ticket)”.

### Projectors

- IFC: `IfcRelVoidsElement` from hosted openings / `Solid.voids`; `IfcDoor` /
  `IfcWindow` from opening kind; extrusion from `outline_xy` when clipped.
  HEADER remains `ViewDefinition [ArxosAsBuiltView]`.
- USD: cubes plus `arxos:voids` / `arxos:hasOutline` metadata (honest cube, not
  a guessed mesh).

### Realize v2

- Wall solids clip against neighboring non-parallel planes (same storey,
  `|n_i·n_j| < 0.95`). Result is `Solid.outline_xy`; fewer than 3 vertices
  keeps the v1 box. Hosted openings are listed on `Solid.voids`. A 2D notch
  is subtracted only when it stays one polygon; otherwise void list only.

### Field / RoomPlan hosting

- Opening host assignment projects the opening origin onto wall planes
  (`surface_kind = wall` only). Reject plane distance `> 0.35 m` or a
  projection outside wall `extent` padded by `0.15 m`. Winner: nearest plane,
  then larger face area, then higher CID. No host → `host_entity = None` and
  property `host=unresolved` (realize / IFC skip the void relationship).
- Identical Apple UUIDs still map to `rp:` + lowercase uuid (FFI does not mint
  random RoomPlan ids).
- `arx capture simulate` emits a hosted door on the south wall (stable UUID) so
  fuse and voids are testable with `--dx` / `--sigma-mm` and no phone.
- Operator checklist: `docs/field/ROOM_WALK.md`.

### Docs / hygiene

- Public `SECURITY.md` and `CONTRIBUTING.md`. `REVIEW.md` removed from `main`.
- `docs/` may be committed; scratch stays in `docs/_scratch/` and `*.local.md`.
- Split CLI commands, repository open/capture, merge tests, networking sync,
  and FFI capture/inbox/locator into focused modules. No wire or fuse change.

### Serve-owned apply + locator

- `arx://bldg/<id>?controllers=&inbox=` parser in core (`BuildingLocator`).
- `$STORE/meta/serve.sock` (0600): `inbox apply` while `net serve` holds the flock.
- `building follow --uri`, `net push --uri`; iOS Join field accepts the URI.

### Inbox / thin client

- Meta inbox `$STORE/meta/inbox/<building_id>.json`. Push never sets `head_root`.
- `arx inbox list|apply|reject`, `arx building follow`, `arx net push --staged`.
- Additive `arxos/sync/1` messages: `PutObject`, `PushFacts`.

### Facts / state / realize

- Schema v2: optional `extent`, `sigma_mm`, `support_count`, `evidence` on
  Surface / Opening / Equipment, `host_entity` on Opening, new `ObjectType::Run`.
  v1 objects still load (`MIN_SCHEMA_VERSION..=SCHEMA_VERSION` is 1..=2).
- RoomPlan ingest in `core::capture::roomplan`. Apple UUIDs become `rp:` + lowercase uuid.
  Doors/windows are Opening Facts hosted on a wall when the plane+extent
  heuristic accepts one (otherwise `host=unresolved`).
- `BuildingState`, `fuse` on commit/merge, `realize` v1 (oriented boxes).
- IFC/USD projectors consume \(R(S)\): `IFCWALL` + `Pset_ArxosMeasure`; USD Cube prims.
- `arx building slice` ASCII occupancy. `arx capture simulate` mints wall Facts (σ 40 mm).

### Security / fail-closed

- Exclusive `store.lock` (two handles in one process fail closed).
- Frames with length prefix > 64 MiB rejected. Serve closures refuse oversize frames.
- Iroh serve uses `N0DisableRelay`. `GetObject` / `GetRootClosure` scoped to advertised
  head closures. Inbound `AnnounceRoot` is ignored (ads from disk).
- Push never adopts. Inbox apply is a controller commit.
- First-contact TOFU pin: `--trust-controllers` / `AdoptOptions.expected_controllers`.
- Merge of a remote parent whose authors are not local controllers is rejected.
- Unsigned IFC/USD import refused. iOS FFI `allow_untrusted` pull hard-fails; `put_blob`
  is not on the iOS UDL. iOS seed is Keychain-backed; store export omits `keys/`.
- IFC `FILE_DESCRIPTION` is `ViewDefinition [ArxosAsBuiltView]`, not CoordinationView.

### Build

- Workspace `rust-version` is 1.91. Scoring is diagnostic (`arx score`); settlement is
  fiat off-band. No currency in CIDs.
