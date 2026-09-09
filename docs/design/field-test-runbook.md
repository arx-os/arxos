# 30-day field-test runbook

**Product:** one writer on a LiDAR iPhone; inspect and export on a Mac. The store contract does not change for this test.

**Success (day 30):** one real building, captured offline, verified, exported, pulled by a second replica without a second genesis.

Short device loop: [ios-field-loop.md](ios-field-loop.md). Review gates: [store-contract-pr-checklist.md](store-contract-pr-checklist.md). Contract: [core/README.md](../../core/README.md).

`docs/` is local-only (gitignored). Field notes, store copies, and IFC/USD artifacts stay out of the public tree.

## Hardware and software

| Role | What |
|---|---|
| Writer | Physical LiDAR iPhone, iOS 17+, full Xcode (not Command Line Tools) |
| Inspector | Mac with this repo, Rust 1.75+, `cargo` |
| Optional LAN | Second Mac or Pi-class node for `arxos-edge serve` / `arx net serve` |
| Interop | One external tool that opens IFC4 **or** USDA (pick one for the 30 days) |

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
./ios/scripts/prep.sh
open ios/ArxosApp/ArxosApp.xcodeproj
```

On device: Init → Start RoomPlan → walk → Stop (ingest + auto-commit) → force-quit → reopen same head → Export store. Store path: `Documents/arxos-store` (`UIFileSharingEnabled`).

On Mac, after AirDrop / Files copy (directory that contains `objects/` and `meta/`):

```bash
export ARXOS_STORE=/path/to/arxos-store
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building list
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building status "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" entity list "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" verify "$HEAD"
```

Do **not** merge on the phone. Field UX is create, capture, commit, share/pull. `merge plan` / `merge apply` is laptop work after a pull.

## Release checklist (promote from smoke)

Green before any field day counts:

```bash
cargo test -p arxos-cli --test smoke
# field_loop_init_capture_commit_status_entity_score
# root_create_rejects_unauthorized_seed
```

Also keep green: unauthorized FFI commit, second-genesis rejection, pull-fails-when-locked, IFC/USD identity roundtrip, iOS ingest + spatial query (names in the PR checklist).

## Days 1–10 — Field loop reliability

Goal: walk, stop, auto-commit, force-quit, same head, copy to Mac, `arx` status/entity/verify green.

| Day | Do | Bar |
|---|---|---|
| 1 | Prep + smoke tests. Confirm `prep.sh` and Xcode on a physical iPhone. | `field_loop_init_capture_commit_status_entity_score` green. App launches. |
| 2 | Init building, **Advanced simulate** once (not the product path), commit, force-quit, reopen. | Same `buildingId` and head in UI. UserDefaults restore (`BuildingSession`). |
| 3 | First real RoomPlan: one room, slow walk, Stop. | Auto-commit; status shows committed root; `hasUncommittedStaging` is false. |
| 4 | Force-quit after a real scan. Reopen. | Same head. If staged-only warning appeared, treat as a **fail** — auto-commit must have run. |
| 5 | Export store (Share / Files / Finder). Open on Mac. | `building status` and `entity list` work. Head CID matches the phone. |
| 6 | `arx verify $HEAD`. Note findings. | No authorization/signature failures on a self-captured root. |
| 7 | Second capture into the **same** building (another room or a pin note + RoomPlan). Commit. Re-export. | Head advanced; previous head still in CAS; entity ids stable on re-ingest (`test_ingest_room_plan_spatial_query` behavior). |
| 8 | Kill leftover product story in the tree you actually ship from: no control-plane, no EVM as a surface, `arx score` not described as payment. | CHANGELOG Unreleased already points this way; do not reintroduce. Scoring module comments that still say “DePIN oracle” are doc debt, not a field-day blocker. |
| 9 | Capture types check on the phone UI and CLI. | Field types: space, annotation, point cloud, RoomPlan. No mesh button. CLI: `capture space` / `annotation` / `point-cloud` / `simulate`. Mesh stays core/CLI-later. |
| 10 | **Building A** declared: one real space, exported store archived (local). | Written log: building id, head CID, object count, device, iOS version. |

Fail closed this slice: dual camera (RoomPlan must pause AR overlay), Command Line Tools-only builds, simulator as “the” capture path, merge on device.

## Days 11–20 — Trust on the wire

Goal: TOFU first contact, replica continuity on the second device, locked-store fail-closed, App Attest mock labeled as mock.

| Day | Do | Bar |
|---|---|---|
| 11 | Empty second store. Copy **only** the root closure (or full store once as control). `open_or_follow` / `arx net fetch` without `--allow-untrusted`. | First contact TOFU: head set, `ContinuityOutcome::FirstTrust` (test: `adopt_first_contact_tofu_succeeds`). |
| 12 | Second pull of a **descendant** root from Building A onto that replica. | Fast-forward; head advances; no second genesis. Test: `adopt_accepts_fast_forward_signed_by_local_controller`. |
| 13 | Attack: adopt a full-set checkpoint with `previous_root = None` (or a sibling history) against the existing head. | Rejected (`"second genesis"` / `"not a descendant"`). Head unchanged. |
| 14 | Outsider seed cannot commit. On device or FFI: overwrite `keys/device.seed` with a non-controller, capture, commit. | `Authorization` error. Tests: `unauthorized_commit_surfaces_as_authorization_error`, `root_create_rejects_unauthorized_seed`. Restore the real seed. |
| 15 | Hold `store.lock` (`arxos-edge serve` or `arx net serve`) and attempt pull ingest into that path. | Pull fails closed (`pull_ingest_fails_closed_when_store_locked`). One writer. |
| 16 | Optional LAN: one writer serves; second replica pulls. mDNS optional. | Serve holds lock until Ctrl-C. Document in the day’s log: nobody expects two phones to co-edit. |
| 17 | App Attest: run mock path; confirm UI/CLI strings say **mock**. Production `DCAppAttestService` only if the device supports it; do not mix mock bytes into a “production attest” claim. | `mock_attest_roundtrip`; `AppAttest.swift` mock vs `#if canImport(DeviceCheck)`. |
| 18 | `allow_untrusted` is off on fetch. Flip it on only as a named debug trial, then revert. | Default sync never adopts an unauthorized root. Import/debug only (IFC/USD unsigned import). |
| 19 | Closure completeness: delete one object from a copy of the store, try adopt. | Fails closed (`adopt_incomplete_closure_fails_by_default`, `closure_fails_closed_on_missing_object`). |
| 20 | **Replica B** declared: pulled Building A, verified, no second genesis. | Log: replica path, local head == writer head, `arx verify` green. |

`arxos-edge serve` is a long-running net serve with the writer lock held (`edge/README.md`). Treat it as the office replica, not a second field writer.

## Days 21–30 — One interop customer + freeze

Goal: identity-preserving handoff at supported quality; schema treated as frozen; field types documented by what you actually captured.

Pick **one** format for the 30 days. The other stays in-tree tests only.

| Day | Do | Bar |
|---|---|---|
| 21 | Export Building A: `arx export ifc` **or** `arx export usd`. | File opens; contains identity (`Pset_ArxosIdentity` / `arxos:cid`). |
| 22 | Open in the chosen external tool (IfcOpenShell / a BIM viewer, or `usdview`). | Hierarchy visible (building / storey / space or Building → Floor → Space). Screenshot + notes local. |
| 23 | Roundtrip import into a **fresh** store. | `EntityId` / identity properties survive. Tests: `ifc_roundtrip_identity` / `usd_roundtrip_identity`. Building id matches. |
| 24 | Spatial query on Mac: `arx building near $BID --x … --radius …` against the field store. | Hits include RoomPlan surfaces/objects; no writable-store misuse. |
| 25 | Schema freeze review: `SCHEMA_VERSION = 1`, `ScoreReport.policy_version = 1`, root body fields unchanged. | Any proposed object-type change is a new version, not a silent edit of field data. |
| 26 | Capture-type inventory from Building A. | Record what landed: space, surface, annotation, point cloud, RoomPlan objects. Confirm no mesh objects from the phone. |
| 27 | Re-run the law-test set on the same commit you field-tested. | Protocol tests still green. If a field store fails verify, that is a product bug, not a reason to relax adopt. |
| 28 | Second-genesis regression on the **field** store: try to adopt an unrelated genesis for the same building id. | Rejected; head unchanged. |
| 29 | Write the one-page field report (local): building, rooms walked, head CID, replica pull, export tool, failures. | Report answers: captured offline? verified? exported? pulled without second genesis? |
| 30 | Go / no-go. | **Go** only if success criteria below are all true. Otherwise the next 30 days repeat this runbook, not new crates. |

## Success criteria (all required)

1. One LiDAR iPhone captured a real building offline (RoomPlan start/stop, auto-commit).
2. Force-quit restored the same building id and head.
3. Store copied to a Mac; `arx building status` / `entity list` / `verify` green.
4. Unauthorized seed cannot commit (FFI or CLI law test, and a device or seed-swap check).
5. A second replica pulled the head: first contact TOFU, later pull is continuity, never a second genesis.
6. Pull fails closed while `store.lock` is held.
7. One identity-preserving export (IFC **or** USD) opens in an external tool and roundtrips `EntityId` / identity Pset.
8. No merge, no mesh, no second writer, no cloud, no economic/DePIN product surface used in the loop.

## Out of scope until this loop is boring

- Multi-writer merge as field UX (exists: `MergeCommands`, `core/src/merge/mod.rs`, `run_sync` can `plan_merge` — laptop only).
- Mesh capture on `BuildingSession`.
- Cloud, control-plane, EVM, DePIN, fiat ledger.
- Marketing `arx score` as settlement. Diagnostic type-count weights only.
- Schema migrations of object types / root bodies.

## Field log template (copy per building)

```text
Date:
Device / iOS:
Core version (ArxosCore.version / arx version):
Building id:
Head CID (after last commit):
Rooms / notes:
Force-quit restore (yes/no, head match):
Mac status / entity list / verify:
Replica pull (TOFU / fast-forward / error):
Export format / tool / identity preserved:
Failures:
```
