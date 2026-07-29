# Arxos Edge Node

Edge deployment binary for local network and Raspberry Pi class nodes.

## Commands

```bash
arxos-edge version
arxos-edge buildings
arxos-edge export-usd $BID -o out.usda
arxos-edge export-ifc $BID -o out.ifc
```

To run networking and synchronize files across the network, use the main `arx` CLI:
```bash
arx --store /var/lib/arxos/store net serve
```

## Packaging & Deployment

### Docker Multi-Arch Build
Build for ARM64 (e.g., Raspberry Pi) and AMD64 platforms:
```bash
docker buildx build --platform linux/arm64,linux/amd64 -f edge/Dockerfile -t arxos-edge .
```

### systemd Service Installation
Install the service daemon and start:
```bash
sudo INSTALL_SYSTEMD=1 ./edge/scripts/install-edge.sh
sudo systemctl enable --now arxos-edge
```

## Security & Verification Utilities

- **Access Controls**: Device seed keys are stored locally at `$ARXOS_STORE/keys/device.seed` with restricted read-only permissions (`0600`).
- **Chain Verification**: Assert root transition validity via `arx depin verify $ROOT`.
- **Scoring**: Evaluate contributor score matrices via `arx depin score $BID`.
