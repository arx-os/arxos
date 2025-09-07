# ArxObject Wire Format (Little-Endian)

This document captures byte-level details and test vectors for the 13‑byte ArxObject and sealed frame packing.

## ArxObject (13 bytes)

Layout (all LE):
- Bytes 0–1: building_id (u16)
- Byte 2:     object_type (u8)
- Bytes 3–4:  x (i16)
- Bytes 5–6:  y (i16)
- Bytes 7–8:  z (i16)
- Bytes 9–12: properties ([u8;4])

### Golden vectors

1) Outlet example
```
Hex: 34 02 10 50 14 A4 1F 2C 01 78 0F 14 0B
Fields:
  building_id = 0x0234 (564)
  object_type = 0x10
  x = 0x1450 (5200)
  y = 0x1FA4 (8100)
  z = 0x012C (300)
  properties = 78 0F 14 0B
```

2) Exit sign example
```
Hex: 56 04 52 E0 2E C4 09 F0 0A 12 FF 01 00
Fields:
  building_id = 0x0456 (1110)
  object_type = 0x52
  x = 0x2EE0 (12000)
  y = 0x09C4 (2500)
  z = 0x0AF0 (2800)
  properties = 12 FF 01 00
```

## Sealed frames (application level, 255 MTU)

- Security header (8B): sender_id (u16), key_version (u8), reserved (u8), nonce (u32)
- App header (4B typical): frame_index (u16), total_frames (u16)
- Payload: N × 13B ArxObjects
- MAC tag: 16B

Available payload for objects: 255 − 8 − 4 − 16 = 227 bytes → 17 objects per sealed frame.

## Test checklist
- Serialize and parse vectors exactly as above (byte-for-byte).
- Verify frame packing: with 34 objects, packing yields 2 frames (17 + 17).
- Verify MAC over (security header || app header || payload), then append 16B tag.
