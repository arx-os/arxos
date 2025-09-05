# ArxOS Provisioning Guide (RF-Only)

This guide covers the minimal Bill of Materials (BOM) and imaging checklist to stand up an RF-only ArxOS gateway and optional room nodes. No internet is required for runtime operation; transfer images via USB or other offline means.

## Bill of Materials (BOM)

- Gateway (choose one)
  - Raspberry Pi 4 (4GB) or Pi 5
    - Storage: 32–64GB microSD or USB SSD
    - Power: official PSU or PoE HAT
  - x86 mini PC (fanless, low-power) with 64GB SSD
- LoRa radio (Meshtastic-compatible)
  - SX1262 HAT (for Pi) or USB dongle
  - Antenna: 915MHz (US) or 868MHz (EU), 3–6 dBi
  - Coax pigtail/bulkhead if enclosing
- Enclosure (indoor) with strain relief
- Optional room node (per room)
  - ESP32‑S3 + SX1262 (Meshtastic)
  - Small LiPo or mains + enclosure

Notes:
- Use correct regional antenna (915MHz US / 868MHz EU)
- Outdoor coverage: IP‑rated enclosures, surge protection

## Imaging Checklist (Gateway)

1) Prepare artifacts (offline)
- Obtain signed ArxOS gateway image (district staging or trusted USB)
- Verify signature (hash/signature alongside image)

2) Flash image
- Raspberry Pi: Raspberry Pi Imager/Balena Etcher or dd
- x86 mini PC: write image to SSD or install from USB

3) First boot settings (local console/HDMI)
- Set hostname: `arxos-gw-<site>`
- Set locale/timezone
- Set radio region/frequency (e.g., US 915MHz)
- Confirm RF-only banner in terminal at startup

4) Attach and verify LoRa radio
- Connect SX1262 HAT/USB dongle + antenna
- Ensure secure connections and correct orientation
- Open ArxOS terminal; check radio status

5) Pairing & onboarding (RF invite tokens)
- Generate invite on gateway terminal:
  - `invite generate <viewer|tech|admin> <hours>`
  - Distribute the 13-byte hex (QR/printed card)
- Accept on receiving terminal:
  - `invite accept <13B-hex>`
  - Role/duration displayed if valid

6) Sanity checks
- Load staged ArxObjects; verify broadcast/reception
- Confirm sealed frames (MAC) and anti‑replay active
- Ensure no outbound routes; RF-only posture maintained

## Imaging Checklist (Room Nodes, Optional)

1) Flash Meshtastic on ESP32‑S3 + SX1262 (per Meshtastic docs)
2) Configure channel/region to match gateway
3) Mount nodes; perform “hello” broadcast test

## Operational Notes

- Updates: apply signed images/offline bundles via USB
- Logs: export to USB; no remote uploads in RF-only mode
- Hardware: verify antenna seating; check moisture ingress

## Security Posture

- RF‑only by default (internet touchpoints are feature‑gated and off)
- Radio frames: 16‑byte MAC + replay protection
- Invite tokens: MAC‑checked role/duration in 13 bytes

See also: `docs/02-ARCHITECTURE.md`, `docs/04-DEPLOYMENT.md`.
