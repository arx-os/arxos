# Day‑of‑Scan Checklist (Offline Onboarding)

Use this checklist on‑site to capture, ingest, and publish a building into ArxOS efficiently.

## Pre‑arrival
- Confirm gateway is provisioned and powered (UPS preferred).
- Verify Meshtastic link up; run terminal health/status.
- Prepare RF invites for operators (optional).
- Ensure enough storage on gateway and phone.

## Zoning and naming
- Define zones (per floor/wing/area) before you start.
- Use consistent names: `F<floor>_<wing>_<segment>` (e.g., `F1_West_A`).
- Note anchor points to capture later (QR/AprilTag or measured corners).

## Capture (phone LiDAR)
- Walk steady, maintain overlap between passes.
- One file per zone; avoid multi‑GB single files when possible.
- Immediately rename files to the zone naming scheme.

## Transfer to gateway (offline)
- Preferred: USB/Lightning tether; alternative: BLE via binder.
- Verify checksums; place under `/application/arxos/<building>/incoming/`.

## Ingest & preview
- Start ingestion for each zone; monitor progress.
- Verify ASCII preview per zone:
  - Rooms look plausible
  - Walls align, no massive skew
  - Major fixtures present
- If a zone is bad, rescan that zone immediately.

## Anchoring (per floor)
- Place or identify anchors; measure known distances if needed.
- Record origin/scale; store transforms as ArxObjects.
- Verify overlay alignment with a quick phone check.
- See: `docs/AR_ANCHORING.md`.

## Markups and QA
- Make small deltas first (labels, circuits) so they distribute quickly.
- Tag any questionable zones for follow‑up rescan.

## Publish
- Push deltas; schedule bulk geometry for off‑peak slow‑bleed.
- Confirm neighboring gateways receive and cache.

## Wrap‑up
- Export a summary (zones ingested, frames queued, errors).
- Back up raw PLY and generated artifacts to removable media.

## Quick commands (reference)
- Invite generate/accept: `invite ...`
- Mobile loopback test: `mobile init`, `mobile send ...`, `mobile recv`
- Latency estimate: `latency <objects> hops=H profile=range|speed`
- See: `docs/technical/TERMINAL_API.md`

See also: `docs/ONBOARDING_WORKFLOW.md`, `docs/LATENCY_ESTIMATES.md`, `docs/PROVISIONING.md`.
