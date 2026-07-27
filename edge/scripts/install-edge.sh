#!/usr/bin/env bash
# Install arxos + arxos-edge binaries and optional systemd unit (root).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PREFIX="${PREFIX:-/usr/local}"
STORE_DIR="${STORE_DIR:-/var/lib/arxos/store}"

echo "Building release binaries…"
cargo build --release -p arxos-cli -p arxos-edge --manifest-path "$ROOT/Cargo.toml"

install -d "$PREFIX/bin"
install -m 755 "$ROOT/target/release/arxos" "$PREFIX/bin/arxos"
install -m 755 "$ROOT/target/release/arxos-edge" "$PREFIX/bin/arxos-edge"

if [[ "${INSTALL_SYSTEMD:-0}" == "1" ]]; then
  install -d /var/lib/arxos
  if ! id arxos &>/dev/null; then
    useradd --system --home /var/lib/arxos --shell /usr/sbin/nologin arxos || true
  fi
  mkdir -p "$STORE_DIR"
  chown -R arxos:arxos /var/lib/arxos
  install -m 644 "$ROOT/edge/systemd/arxos-edge.service" /etc/systemd/system/arxos-edge.service
  systemctl daemon-reload
  echo "Enable with: systemctl enable --now arxos-edge"
fi

echo "Installed to $PREFIX/bin"
arxos-edge version
