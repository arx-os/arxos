# Arxos edge node

Site / Raspberry Pi class deployment of the shared Rust core.

## Commands

```bash
arxos-edge version
arxos-edge buildings
arxos-edge export-usd $BID -o out.usda
arxos-edge export-ifc $BID -o out.ifc
```

Networking (Iroh serve) uses the main CLI:

```bash
arxos --store /var/lib/arxos/store net serve
```

## Packaging

### Docker

```bash
docker build -f edge/Dockerfile -t arxos-edge .
docker run --rm -v arxos-data:/data -e ARXOS_STORE=/data/store arxos-edge version
```

Multi-arch (Pi + x86):

```bash
docker buildx build --platform linux/arm64,linux/amd64 -f edge/Dockerfile -t arxos-edge .
```

### systemd

```bash
sudo INSTALL_SYSTEMD=1 ./edge/scripts/install-edge.sh
sudo systemctl enable --now arxos-edge
```

## Phase 5 hardening

- Device keys under `$ARXOS_STORE/keys/device.seed` (mode 0600)
- Root verification: `arxos depin verify $ROOT`
- Contribution scores: `arxos depin score $BID`
- Registry snapshot: `arxos depin registry $BID --abi`
