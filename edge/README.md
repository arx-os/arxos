# Arxos Edge Node

Edge deployment binary for local network and Raspberry Pi class nodes.

The edge holds official \(S\). Phones mint Facts and `net push` them into the
inbox. `inbox apply` is a controller commit through `$STORE/meta/serve.sock`
while serve is up. Folder copy of the store is disaster recovery / debug, not
the field loop. Public Iroh relays stay off.

## Commands

```bash
arxos-edge version
arxos-edge buildings
arxos-edge status
arxos-edge export-usd $BID -o out.usda
arxos-edge export-ifc $BID -o out.ifc

# Long-running node: exclusive store lock + Iroh (+ mDNS when enabled)
arxos-edge --store /var/lib/arxos/store serve
```

`status` is read-only: lock held?, sock up?, inbox pending, head CID. It does
not take a writer lock beyond a probe (same as `arx building status`).

`serve` holds `store.lock` for the process lifetime and binds
`$STORE/meta/serve.sock` (0600). The Iroh dial ticket is written once to
`$STORE/meta/serve.ticket` (0600). Stdout prints `ticket_file=` and
`ticket_len=` so systemd journals do not store the full ticket. Read the file
to build `arx://bldg/<id>?controllers=<pk>&inbox=<ticket>`.

`arx inbox apply $BID` talks to that socket while serve is running — **do not
stop the unit to apply**. `--local` forces an in-process open and fails if the
flock is held. Push (`PutObject` / `PushFacts`) never moves `head_root`.
Apply over Iroh is out of scope (local socket only).

## Backup

Copy `$STORE` while serve is **stopped**, or snapshot `objects/` + `meta/`
knowing a live copy can race a commit. There is no custom backup daemon.

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
