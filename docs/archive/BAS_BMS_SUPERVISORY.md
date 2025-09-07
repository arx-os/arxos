# BAS/BMS Supervisory Over RF Mesh (Concept)

This concept outlines how ArxOS can support Building Automation/Management Systems using simple open-source hardware (e.g., Raspberry Pi) while honoring RF-only, zero-trust, offline constraints.

## Scope
- Goal: county-wide supervisory control and monitoring, not hard real-time loops.
- Local controllers (per building) execute fast control; mesh carries small supervisory commands and telemetry.

## Control classes
- Class 0 – Hard real-time (local only): PID loops for valves/fans, safeties, interlocks (100–1000 ms).
- Class 1 – Near real-time (intra-building): local setpoint tweaks, overrides (sub-second to few seconds).
- Class 2 – Supervisory remote (cross-county): setpoints, modes, schedules (seconds to tens of seconds).
- Class 3 – Trends/Bulk (off-peak): low-rate streaming, slow-bleed archives.

## Architecture
- Per-building Raspberry Pi (gateway/controller):
  - Talks GPIO/Modbus/BACnet locally to plant/field devices.
  - Enforces safety limits, schedules, and fallback on mesh loss.
  - Stores recent telemetry and event logs.
- RF mesh backbone:
  - Sealed frames (MAC + anti-replay) with priority queues.
  - Store-and-forward; backbone nodes keep cross-school hops ≤ 8.

## Command model
- Command frame (small): equipment_id, point, value, TTL, idempotent command_id.
- Ack frame: echoes command_id + status; optional applied value.
- Idempotent, retriable; scheduler prioritizes command/ack over bulk.
- Local PI validates and clamps values; rejects unsafe or out-of-range inputs.

## Latency expectations
- Reference `docs/LATENCY_ESTIMATES.md` for frames and airtime.
- Command+Ack (one frame each):
  - 3 hops: ~0.5–2 s (speed profile) or ~9–36 s (range profile).
  - 8 hops: ~1.3–5.1 s (speed) or ~24–96 s (range).
- Suitable for supervisory actions; not for hard real-time control.

## Security and trust
- Zero-trust per frame: 16B MAC, replay windows, role-based invites.
- Role scopes: operator, supervisor, admin; per-building keys and key_version rotation.
- Rate limiting, lockouts, and audit logs on local PI.

## Operator UX
- Terminal shows: pending → applied → verified with ETA from hop map.
- Batch operations queue as multiple commands with progress.
- Progressive feedback: alarms high-priority; trends low-rate.

## Failure modes / resilience
- Mesh loss: local PI continues on schedules; caches pending commands with TTL.
- Power: place PI on UPS; safe-state on brownouts.
- Congestion: slow-bleed trends, backoff and fairness in scheduler.

## Deployment patterns
- One PI per building with Meshtastic node; a sparse elevated backbone across the county.
- Keep critical cross-building paths ≤ 8 hops; elevate antennas as allowed.

## Roadmap
- Trends streaming and compression; demand-response and load-shed policies.
- Analytics at gateway with periodic summaries over mesh.
- Configuration profiles per district; secure key rotation procedures.
