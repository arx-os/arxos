# Onboarding Workflow (Offline, RF‑Only)

This guide outlines the end‑to‑end process to bring a new building into ArxOS, from phone capture to terminal ASCII and mobile AR overlay, staying fully offline.

## 1) Prepare the school gateway (once per building)
- Image the Raspberry Pi gateway and pair the Meshtastic node.
- Verify RF‑only mode at startup; confirm sealed frames (MAC + anti‑replay) on logs.
- Create workspace directories under `/application/arxos/<building>/` for config/data.
- Generate RF invite tokens for on‑site operators if needed.
- Review feature flags: `docs/FEATURE_FLAGS.md`.

## 2) Capture LiDAR scans by zones (phone)
- Walk the building by floors/wings/segments to keep files manageable.
- Name zones meaningfully (e.g., `F1_WestWing_A`, `F2_Gym`).
- Export PLY per zone.

## 3) Transfer PLY to gateway (offline)
- Preferred: USB/Lightning tether; alt: BLE via `mobile_offline` binder (slower).
- Verify checksums; place files under `/application/arxos/<building>/incoming/`.

## 4) Ingest and compress into ArxObjects (gateway)
- Run ingest: load PLY → normalize → segment → quantize → emit 13‑byte ArxObjects.
- Artifacts (per zone):
  - `arxobjects.bin` (13B × N)
  - ASCII 2D preview (`ascii.txt`)
  - Optional coarse 3D data (`coarse3d.bin`)
  - Spatial index (`index.bin`)
- Terminal shows previews as batches complete; fix issues early.

## 5) Anchor AR to the building frame
- Define building origin and scale (QR/AprilTag or measured corners).
- Store transforms as small ArxObjects so all viewers share alignment.
- See: `docs/AR_ANCHORING.md`.

## 6) Review and apply markups
- Use the terminal to inspect ASCII BIM; make small edits as deltas.
- Save deltas as ArxObjects grouped by a small header atom.

## 7) Publish over the RF mesh
- Scheduler fragments ArxObjects into sealed frames and prioritizes:
  - Control/invites > small deltas > bulk geometry.
- Large updates slow‑bleed off‑peak.
- Gateways store‑and‑forward; nearby schools cache zones for local viewers.

## 8) Mobile AR subscription (offline)
- Phone connects via USB/BLE; fetches the current zone and subscribes to deltas.
- Renders overlay using stored anchors; updates stream progressively.

## References
- Latency planning: `docs/LATENCY_ESTIMATES.md`
- Provisioning: `docs/PROVISIONING.md`
- Terminal commands (invite, mobile, latency): see `docs/technical/TERMINAL_API.md`
- Feature flags: `docs/FEATURE_FLAGS.md`
