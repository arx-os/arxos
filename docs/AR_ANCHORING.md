# AR Anchoring Guide (Origin, Scale, Floors)

This guide describes how to align mobile AR overlays to the building coordinate frame used by ArxObjects.

## Anchoring Options
- Fiducials: QR/AprilTag markers placed at known points.
- Measured geometry: known corners/lengths measured with a tape/laser.
- Hybrid: fiducial at origin + measured scale along a corridor.

## Recommended Workflow (per floor)
1. Choose an origin (e.g., southwest corner of main corridor) and a primary axis (x along corridor).
2. Place a fiducial at origin; record orientation.
3. Measure one or two long baselines (for scale verification).
4. Capture these into small ArxObjects (anchor type) with:
   - building_id, object_type = ANCHOR (reserved)
   - x,y,z (millimeters) = 0,0,0 for origin; other reference points at measured positions
   - properties encode axis/orientation/version
5. Verify by walking with mobile viewer; overlay should “snap” to structure.

## Tips
- Repeat per floor; keep origins consistent (z offset between floors).
- Store transforms centrally so terminal and mobile render the same frame.
- Re-verify after significant building changes.

See also: `docs/ONBOARDING_WORKFLOW.md`, `docs/DAY_OF_SCAN_CHECKLIST.md`.
