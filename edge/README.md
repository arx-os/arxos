# Arxos Edge Node

Edge deployment binary for local network and Raspberry Pi class nodes.

## Commands

```bash
arxos-edge version
arxos-edge buildings
arxos-edge export-usd $BID -o out.usda
arxos-edge export-ifc $BID -o out.ifc

# Long-running node: exclusive store lock + Iroh (+ mDNS when enabled)
arxos-edge --store /var/lib/arxos/store serve
```

`serve` prints a peer id and ticket for pullers, holds `store.lock` for the
process lifetime, and exits cleanly on Ctrl-C (heads remain on disk).

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

## Security notes

- Device seed keys at `$ARXOS_STORE/keys/device.seed` (`0600`).
- Only one exclusive writer per store path (edge `serve` or CLI repository open).
- Root verification: `arx verify $BID`
- Contributor scoring (diagnostic points): `arx score $BID`

Settlement is fiat off-band; see the root README economic model.
