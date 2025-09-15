# ArxOS Packet Radio Transport Layer

## Overview

The packet radio transport layer enables ArxOS to operate over low-bandwidth, unreliable radio networks such as LoRaWAN, APRS, or other packet radio protocols. This transport layer is completely optional and transparent to the core ArxOS functionality.

## Design Principles

- **Protocol Agnostic**: Works with any packet radio technology
- **Transparent**: Same CLI commands work over radio or HTTP
- **Bandwidth Efficient**: Aggressive compression for radio constraints
- **Fault Tolerant**: Handles packet loss and network interruptions
- **Battery Conscious**: Minimizes radio transmission time

## Architecture

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  ArxOS CLI  │───▶│ Radio Transport │───▶│ Radio Hardware  │
│             │    │     Layer       │    │  (LoRaWAN/etc)  │
└─────────────┘    └─────────────────┘    └─────────────────┘
                           │                       │
                    ┌──────▼──────┐                │
                    │ Compression │                │
                    │   Engine    │                ▼
                    └─────────────┘    ┌─────────────────┐
                           │           │    Gateway      │
                    ┌──────▼──────┐    │   (Optional)    │
                    │ Packet      │    └─────────────────┘
                    │ Framing     │                │
                    └─────────────┘                ▼
                                        ┌─────────────────┐
                                        │  ArxOS Server   │
                                        │   (HTTP API)    │
                                        └─────────────────┘
```

## Protocol Specification

### Message Format

```
[HDR][CMD][PATH][ARGS][CRC]

HDR  : 1 byte  - Header (version + flags)
CMD  : 1 byte  - Command type
PATH : Variable - Compressed path
ARGS : Variable - Compressed arguments
CRC  : 2 bytes - Checksum
```

### Header Format (1 byte)

```
Bit 7-6: Protocol Version (00 = v1.0)
Bit 5  : Compression Level (0 = normal, 1 = high)
Bit 4  : Acknowledgment Required
Bit 3  : Fragmented Message
Bit 2-0: Reserved
```

## Compression Strategies

### Path Compression

**Building Context Establishment:**
```
# First message establishes building context
CONTEXT ARXOS-NA-US-NY-NYC-0001
# Server responds with building ID
ACK B1

# Subsequent messages use short building reference
GET B1/2/203E/O02    # Instead of full path
```

### Status Compression

```
OPERATIONAL -> O
DEGRADED   -> D
FAILED     -> F
MAINTENANCE -> M
OFFLINE    -> X
UNKNOWN    -> U
```

## Message Examples

### Uncompressed (HTTP equivalent)

```
GET /api/v1/buildings/ARXOS-NA-US-NY-NYC-0001/equipment/floor-02/room-203/electrical/outlet-02
```

### Compressed (Radio)

```bash
# Establish context first
CONTEXT ARXOS-NA-US-NY-NYC-0001
# Response: ACK B1

# Then send compressed command
GET B1/2/203E/O02
# 13 bytes total including framing

# Response
O02:O:Leviton_5320  # 15 bytes
```

## Performance Characteristics

### Compression Ratios

```
Original HTTP Request: ~180 bytes
Compressed Radio: ~15 bytes
Compression Ratio: ~92% reduction
```

### Latency Expectations

- **LoRaWAN**: 1-10 seconds per message
- **APRS**: 5-30 seconds per message
- **Local Radio**: 100ms-1 second

### Battery Life

- **Transmit**: ~50mA for 1 second per message
- **Receive**: ~20mA continuous listening
- **Sleep**: <1mA between operations

---

*Simple enough for a Raspberry Pi, powerful enough for global building networks.*