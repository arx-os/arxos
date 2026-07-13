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

## Release artifacts

When published: download the release binary for your OS, place on `PATH`, run the same smoke check. Track D2 may add Docker later.

## See also

- `docs/pilot-runbook.md` — full field loop
- `arxos_manifest.md` §9 — supported surfaces
