# ArxOS RF Latency Estimates (Draft)

This document provides simple planning estimates for airtime and end-to-end latency when transmitting variable-length markups composed of 13-byte ArxObjects over sealed radio frames. These numbers are theoretical placeholders and will be refined with field measurements.

## Framing and payload budget

- Radio payload MTU (typical): 255 bytes
- Frame header (routing/sequence): 4 bytes
- Security header (sender_id, key_version, nonce): 8 bytes
- MAC tag: 16 bytes
- Bytes available for ArxObjects: 255 - 4 - 8 - 16 = 227 bytes
- Objects per sealed frame: floor(227 / 13) = 17 objects

Frames required for N objects: frames = ceil(N / 17).

## Airtime per frame (single hop)

Effective user throughput depends on radio settings and range. For planning:

- Range-optimized: about 300 to 1,200 bps -> 1.5 to 6.0 seconds per 255-byte frame
- Speed-optimized: about 5 to 20 kbps -> 0.08 to 0.32 seconds per 255-byte frame

Multiply by hop count for mesh paths. Congestion, retries, and backoff increase totals.

## End-to-end examples (single hop, no retries)

- Tiny edit (e.g., circuit text change)
  - Objects: 3 (header + 1–2 atoms) -> 1 frame
  - Latency: 0.08–0.32 s (speed) or 1.5–6 s (range)

- Small object add (e.g., one fixture with attributes)
  - Objects: 40 -> 3 frames
  - Latency: 0.24–0.96 s (speed) or 4.5–18 s (range)

- Medium scene change (e.g., several fixtures/segments)
  - Objects: 200 -> 12 frames
  - Latency: 1.0–3.8 s (speed) or 18–72 s (range)

- Large scan (e.g., new wall structure)
  - Objects: 500 -> 30 frames
  - Latency: 2.4–9.6 s (speed) or 45–180 s (range)

For multi-hop routes, multiply by hops (e.g., 3 hops -> 3x).

## Operational guidance

- Prioritize critical atoms first and stream the rest gradually.
- Use deltas instead of full objects where possible.
- Render progressively in the terminal as frames arrive.
- Duty-cycle and regulatory backoff can stretch tails in busy air.

Note: these figures are for planning only and will be updated with empirical measurements.
