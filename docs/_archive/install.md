# Install ArxOS (capture node)

## Development install

```bash
git clone <repo-url> arxos && cd arxos
cargo install --path .
arx --version
arx --help
```

Requires a recent stable Rust toolchain (`rustup default stable`).

## Default features

| Feature | Default | Notes |
| :--- | :---: | :--- |
| `tui` | yes | Spreadsheet / merge UI (optional for pilot CLI loop) |
| `render3d` | no | Not required for pilot |
| `agent` | no | Edge agent |
| `web` | no | PWA |
| `blockchain` | no | Deferred |

Minimal CLI-oriented build:

```bash
cargo install --path . --no-default-features
```

## Smoke check

```bash
mkdir /tmp/arx-pilot && cd /tmp/arx-pilot
arx init --name "Smoke Site"
arx validate
# expect success (Ground Floor seed)
```

## Release artifacts / pilot pin (R9)

For **L1 district pilot**, do **not** install floating `main`.

1. Follow **`docs/pilot-release.md`** (tag + commit SHA in the charter).  
2. Use **`docs/l1-supported-workflow.md`** only for supported commands.  
3. Cut tags with `./scripts/pin_pilot_release.sh v2.0.0-pilot.N`.

When binary artifacts are published later: install that artifact and still record its version in the charter.

## See also

- `docs/full-lab-loop.md` — eng closed-loop proof (`./scripts/full_lab_loop.sh`)
- `docs/field-handoff.md` — ordered B0–B3 packet (start here for pilot)
- `docs/pilot-charter.md` — L1 sign-off (R10)
- `docs/l1-supported-workflow.md` — supported free-software loop
- `docs/second-person-checklist.md` — R5 transfer
- `docs/pilot-runbook.md` — broader field notes
- `docs/field-trial.md` — Horizon B one-pager
- `docs/horizon-a-ops.md` — optional chain demo (not L1 success)
- `arxos_manifest.md` §1.6 — obligation register
