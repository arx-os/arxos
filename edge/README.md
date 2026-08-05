# Arxos Edge Node

Edge deployment binary for local network and Raspberry Pi class nodes.

## Commands

```bash
arxos-edge version
arxos-edge buildings
arxos-edge export-usd $BID -o out.usda
arxos-edge export-ifc $BID -o out.ifc
```

To synchronize files across the network, use the main `arx` CLI:

```bash
arx --store /var/lib/arxos/store net serve
```

## Packaging & Deployment

### Docker Multi-Arch Build

```bash
docker buildx build --platform linux/arm64,linux/amd64 -f edge/Dockerfile -t arxos-edge .
```

### systemd Service Installation

```bash
sudo INSTALL_SYSTEMD=1 ./edge/scripts/install-edge.sh
sudo systemctl enable --now arxos-edge
```

## Security & Verification Utilities

- **Access controls**: Device seed keys are stored locally at `$ARXOS_STORE/keys/device.seed` with restricted permissions (`0600`).
- **Root verification**: `arx verify $ROOT`
- **Contributor scoring** (diagnostic points only): `arx score $BID`

Scoring is data-plane only and is **not** a payment basis. Fiat payouts are a control-plane concern (see ADR-001).
