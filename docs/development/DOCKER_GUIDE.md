# ArxOS Docker Guide

This guide covers official ArxOS container images, how they are built, and how to run them in local and CI environments.

---

## Image Catalog

| Image | Purpose | Key Contents |
|-------|---------|--------------|
| `ghcr.io/arx-os/arxos:builder` | Reproducible build + test environment | Rust toolchain, `cargo`, `cbindgen`, `wasm-pack`, Linux build deps |
| `ghcr.io/arx-os/arxos:runtime` | Lightweight execution environment for CLI and automation jobs | `arx` binary, schemas |

Tagging aligns with `package.version` from the top-level `Cargo.toml`. Each release publishes semantic tags (e.g., `2.0.0`) plus rolling `latest`.

---

## Builder Image

- Dockerfile: root `Dockerfile` (`builder` stage).
- Base: `rust:1.75-bookworm`.
- Tooling: `clang`, `pkg-config`, `libssl-dev`, `libclang-dev`, `cmake`, `protobuf-compiler`, Python, Git, `cbindgen`, `wasm-pack`.
- Workflow:
  1. Copy manifests and run `cargo fetch` (layer caching).
  2. Copy source and run `cargo build --release`.
  3. Export artifacts (`arx` binary, schemas, CLI reference) to `/artifacts`.
- Usage examples:

```bash
# Build the builder image locally
docker build -t arxos:builder --target builder .

# Run cargo commands inside the builder environment
docker run --rm -it \
  -v "$(pwd)":/workspace \
  -w /workspace \
  arxos:builder \
  cargo test
```

> The builder image runs as root to simplify dependency installation. For CI, mount caches (`/usr/local/cargo`, `/workspace/target`) to accelerate builds.

---

## Runtime Image

- Dockerfile: root `Dockerfile` (`runtime` stage).
- Base: `debian:bookworm-slim`, installs only `ca-certificates` and `git`.
- Runtime layout:
  - Binary: `/usr/local/bin/arx`.
  - Assets: `/opt/arxos/{schemas,CLI_REFERENCE.md}`.
  - Volume: `/workspace` (mount Git repos, IFC data, outputs).
  - Non-root user `arxos` (UID/GID `10001`).
- Environment variables:
  - `ARX_HOME` – root directory for bundled assets (`/opt/arxos`).
  - Set Git credentials via standard env vars (`GIT_ASKPASS`, `GIT_SSH_COMMAND`) or mount SSH keys into `/home/arxos/.ssh`.
- Common commands:

```bash
# Inspect CLI help
docker run --rm ghcr.io/arx-os/arxos:runtime --help

# Import an IFC file and commit to Git
docker run --rm \
  -v "$(pwd)":/workspace \
  -w /workspace \
  ghcr.io/arx-os/arxos:runtime \
  arx import Building-Architecture.ifc --output building
```

---

## CI Integration

1. **Pull Request / Main Builds** – GitHub Actions job `docker-images.yml` builds both `builder` and `runtime` stages with `push: false` to ensure Dockerfiles stay valid.
2. **Release Publishing** – On semantic release tags, GitHub Actions pushes images to GHCR (`ghcr.io/arx-os/arxos`). The workflow:
   - Builds Dockerfile stages.
   - Generates SBOM using Syft.
   - Signs images with Cosign using GitHub OIDC.
   - Attaches image references to the GitHub Release.
3. **Cache Strategy** – Use `actions/cache` for `~/.cargo/registry` and `~/.cargo/git`. Alternatively enable GitHub Actions cache for `docker/build-push-action`.

Workflow file: `.github/workflows/docker-images.yml`.

---

## Security Practices

- Non-root runtime user, limited packages, no shell entrypoint.
- Supply-chain:
  - SBOM generation with `syft packages`.
  - Image signing with `cosign`.
  - Vulnerability scanning via Trivy in CI.
- Recommended runtime flags:
  - `--read-only` root filesystem.
  - `--tmpfs /tmp`.
  - Drop capabilities (`--cap-drop=ALL`).
  - Provide necessary volumes (`/workspace`, optional `/tmp`).

---

## Operational Patterns

### Scheduled Exports

Example GitHub Actions Workflow dispatch:

```yaml
jobs:
  nightly-docs:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/arx-os/arxos:runtime
    steps:
      - uses: actions/checkout@v4
      - run: arx docs --building "HQ" --output docs/hq
      - run: git commit -am "Nightly docs"
      - run: git push
```

---

## Release Checklist Updates

Add the following to the release checklist:

- [ ] Run `.github/workflows/docker-images.yml` on the release tag.
- [ ] Verify `ghcr.io/arx-os/arxos:<version>` pulls and executes `arx --version`.
- [ ] Publish SBOM and Cosign signatures alongside the release notes.
- [ ] Update `docs/development/DOCKER_GUIDE.md` with any breaking changes.

---

## Troubleshooting

| Symptom | Resolution |
|---------|------------|
| `arx` binary missing in runtime | Ensure builder stage completed and exported artifacts; rerun build. |
| Permission errors on mounted volumes | Set matching UID/GID via run flags (`--user $(id -u):$(id -g)`), or adjust host permissions. |
| Git operations fail | Mount SSH keys into `/home/arxos/.ssh` and set correct permissions (`600` files). |

---

## Next Steps

- Integrate container usage examples into automation templates.
- Evaluate publishing nightly snapshot tags for bleeding-edge testing.
- Track image size and trim dependencies quarterly.
