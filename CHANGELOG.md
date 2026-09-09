# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Docs / hygiene

- Public `SECURITY.md` and `CONTRIBUTING.md`. `REVIEW.md` removed from `main`.
- `docs/` may be committed; scratch stays in `docs/_scratch/` and `*.local.md`.

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
  Doors/windows are Opening Facts hosted on the nearest wall.
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
