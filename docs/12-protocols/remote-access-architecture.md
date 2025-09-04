# ArxOS Remote Access Architecture
**Version:** 1.0  
**Date:** August 31, 2025  
**Status:** Proposed Architecture

## Executive Summary

This document defines the hybrid remote access architecture for Arxos that maintains complete air-gap security while providing practical connectivity options. The system uses three complementary access methods, each optimized for different scenarios while preserving the core principle: **no internet connectivity ever**.

> Canonicals: For mesh and protocol specs, see `MESH_PROTOCOL.md` and `../technical/mesh_architecture.md`. This document focuses on access modes without internet.

## Design Principles

1. **Air-Gap First**: All communication methods bypass the internet entirely
2. **Progressive Capability**: Basic access for everyone, advanced features for power users
3. **Hardware Optional**: Core functionality without special equipment, enhanced with dongles
4. **Emergency Ready**: Critical access methods that work in disasters
5. **Privacy Preserved**: No cloud services, telemetry, or external dependencies
6. **Terminal-Only Interface**: No web interfaces, SSH, or traditional network protocols

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Mobile Device                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Arxos Mobile App                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐      │   │
│  │  │   LoRa   │  │Bluetooth │  │     SMS      │      │   │
│  │  │  Driver  │  │   BLE    │  │   Gateway    │      │   │
│  │  └─────┬────┘  └────┬─────┘  └──────┬───────┘      │   │
│  └────────┼─────────────┼───────────────┼──────────────┘   │
└───────────┼─────────────┼───────────────┼──────────────────┘
            │             │               │
     ┌──────▼──────┐      │               │
     │ USB-C LoRa  │      │               │
     │   Dongle    │      │               │
     └──────┬──────┘      │               │
            │             │               │
   ════════════════════════════════════════════════════
            │             │               │
     ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
     │ Building    │ │ ESP32    │ │   Cellular   │
     │ LoRa Mesh   │ │ BLE Node │ │ Modem + RPi  │
     └──────┬──────┘ └────┬─────┘ └──────┬───────┘
            │             │               │
     ═══════▼═════════════▼═══════════════▼═══════
                  Building Mesh Network
     ═════════════════════════════════════════════
```

## Access Methods

### 1. Primary: LoRa USB-C Dongle

**Purpose**: Long-range, high-bandwidth access for power users and facility managers

**Specifications**:
- **Range**: 2-10km urban, 10-40km rural
- **Bandwidth**: 0.3-37.5 kbps (adaptive)
- **Frequency**: 915MHz (US) / 868MHz (EU) / 433MHz (Asia)
- **Power**: 100mW max, powered by phone
- **Cost**: $25-35 per dongle

**Use Cases**:
- Facility managers monitoring multiple buildings
- Contractors accessing building data from parking lot
- Emergency responders approaching incident
- Remote diagnostics and control

### 2. Fallback: Bluetooth Mesh Bridge

**Purpose**: Zero-hardware access when near building

**Specifications**:
- **Range**: 100m from nearest ESP32 node
- **Bandwidth**: 1 Mbps theoretical, 100 kbps practical
- **Protocol**: BLE 5.0 with mesh extensions
- **Security**: AES-128 encryption, rolling codes
- **Power**: Uses existing ESP32 nodes

**Use Cases**:
- Occupants checking room availability
- Maintenance staff on-site
- Visitors requesting access
- Quick status checks

### 3. Emergency: SMS Gateway

**Purpose**: Universal access in emergencies, works with any phone

**Specifications**:
- **Coverage**: Anywhere with cellular service
- **Message Size**: 160 characters per SMS
- **Response Time**: 5-30 seconds
- **Cost**: Standard SMS rates
- **Hardware**: One cellular modem per building

**Use Cases**:
- First responders without app
- Emergency evacuation queries
- Power outage situations
- International visitors

## Component Specifications

### LoRa USB-C Dongle Hardware

```
┌─────────────────────────────────┐
│         USB-C Dongle             │
│  ┌────────────────────────────┐  │
│  │  SX1262 LoRa Module        │  │
│  │  - 915/868/433 MHz         │  │
│  │  - +22dBm TX power         │  │
│  │  - -148dBm sensitivity     │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │  SAMD21 Microcontroller    │  │
│  │  - USB serial bridge       │  │
│  │  - Firmware updates        │  │
│  │  - LED status indicator    │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │  Antenna (Internal)        │  │
│  │  - 2dBi gain               │  │
│  │  - Tuned for region        │  │
│  └────────────────────────────┘  │
└─────────────────────────────────┘

Dimensions: 25mm x 15mm x 8mm
Weight: 12g
Enclosure: Aluminum for RF shielding
```

### ESP32 BLE Bridge Configuration

```yaml
# ESP32 Node Configuration
bluetooth:
  enabled: true
  mode: mesh_bridge
  
  # BLE Settings
  advertising:
    interval_ms: 100
    tx_power: 4  # dBm
    service_uuid: "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    
  # Security
  security:
    mode: just_works  # For quick access
    passkey: null     # Optional 6-digit PIN
    bonding: false    # Don't store connections
    
  # Mesh Bridge
  bridge:
    max_connections: 4
    buffer_size: 4096
    timeout_ms: 30000
    
  # Data Rate Control
  throughput:
    max_kbps: 100
    chunk_size: 244  # BLE MTU - overhead
```

### SMS Gateway Protocol

```
Command Format:
[AUTH] [COMMAND] [PARAMS]

Examples:
"4729 STATUS room:127"
"4729 QUERY floor:2 type:exit"
"4729 HELP"
"4729 MAP 1"

Response Format:
"[1/3] Room 127: 2 outlets, 1 "
"[2/3] light, temp 72F, occupied"
"[3/3] Last update: 5min ago"

Emergency Commands (No Auth):
"911 EXITS"     -> List all emergency exits
"911 FIRE"      -> Fire system status
"911 EVACUATE"  -> Evacuation routes
"911 AED"       -> AED locations
```

## Data Flow Protocols

### LoRa Protocol Stack

```
Application Layer (ArxQL Queries)
        ↓
Compression Layer (LZ4 + Delta)
        ↓
Packet Layer (255-byte chunks)
        ↓
Security Layer (AES-128-CTR)
        ↓
LoRa PHY (SF7-SF12 adaptive)
```

### Bluetooth Protocol Stack

```
Application Layer (ArxQL/JSON)
        ↓
GATT Services (Read/Write/Notify)
        ↓
L2CAP Channels (Connection-oriented)
        ↓
BLE Link Layer (1 Mbps/2 Mbps)
        ↓
BLE PHY (2.4 GHz GFSK)
```

### SMS Protocol Stack

```
Application Layer (Compressed Text)
        ↓
Encoding Layer (Base64/Hex)
        ↓
SMS PDU (140 octets)
        ↓
Cellular Network (GSM/CDMA/LTE)
```

## Security Architecture

### Authentication Modes

1. **LoRa Dongle**: Ed25519 key pairs
   - Private key stored in dongle
   - Public key registered with building
   - Challenge-response authentication

2. **Bluetooth**: Rotating session tokens
   - Initial pairing with building app
   - 24-hour session tokens
   - Automatic token refresh

3. **SMS**: Time-based OTP
   - 4-digit codes valid for 5 minutes
   - Derived from building seed + timestamp
   - Emergency override for 911

### Encryption

```rust
// All methods use different encryption appropriate to medium
pub enum EncryptionMethod {
    LoRa {
        algorithm: "AES-128-CTR",
        key_exchange: "ECDH-P256",
        mac: "HMAC-SHA256",
    },
    Bluetooth {
        algorithm: "AES-CCM",  // BLE standard
        key_size: 128,
        pairing: "Numeric Comparison",
    },
    SMS {
        algorithm: "None",  // Cleartext
        obfuscation: "Custom compression",
        auth: "TOTP",
    },
}
```

## Mobile App Architecture

### Core Components

```
arxos_mobile/
├── core/
│   ├── arxql_parser.rs       # Query language parser
│   ├── cache_manager.rs      # Offline data cache
│   └── protocol_router.rs    # Route to available transport
├── transport/
│   ├── lora_dongle.rs       # USB serial to LoRa
│   ├── bluetooth_mesh.rs    # BLE mesh client
│   └── sms_gateway.rs       # SMS encode/decode
├── ui/
│   ├── terminal_view.rs     # ASCII terminal emulator
│   ├── floor_plan.rs        # Visual floor plans
│   └── quick_actions.rs     # Common commands
└── platform/
    ├── ios/                  # Swift bindings
    └── android/              # Kotlin bindings
```

### Platform-Specific Implementations

#### iOS (Swift)
```swift
// iOS External Accessory Framework for LoRa dongle
import ExternalAccessory

class LoRaDongleManager: NSObject {
    private var session: EASession?
    private let protocolString = "com.arxos.lora"
    
    func connectDongle() {
        if let accessory = EAAccessoryManager.shared()
            .connectedAccessories
            .first(where: { $0.protocolStrings.contains(protocolString) }) {
            session = EASession(accessory: accessory, forProtocol: protocolString)
            session?.inputStream?.open()
            session?.outputStream?.open()
        }
    }
    
    func sendCommand(_ arxql: String) {
        guard let data = arxql.data(using: .utf8),
              let outputStream = session?.outputStream else { return }
        data.withUnsafeBytes { bytes in
            outputStream.write(bytes, maxLength: data.count)
        }
    }
}
```

#### Android (Kotlin)
```kotlin
// Android USB Host API for LoRa dongle
class LoRaDongleManager(private val context: Context) {
    private var usbDevice: UsbDevice? = null
    private var connection: UsbDeviceConnection? = null
    
    fun connectDongle() {
        val usbManager = context.getSystemService(Context.USB_SERVICE) as UsbManager
        val deviceList = usbManager.deviceList
        
        deviceList.values.find { device ->
            device.vendorId == ARXOS_VENDOR_ID && 
            device.productId == LORA_DONGLE_PID
        }?.let { device ->
            val permissionIntent = PendingIntent.getBroadcast(
                context, 0, Intent(ACTION_USB_PERMISSION), 0)
            usbManager.requestPermission(device, permissionIntent)
        }
    }
    
    fun sendCommand(arxql: String) {
        connection?.let { conn ->
            val bytes = arxql.toByteArray()
            conn.bulkTransfer(outEndpoint, bytes, bytes.size, TIMEOUT)
        }
    }
}
```

## Performance Specifications

### Bandwidth Utilization

| Method | Raw Bandwidth | Effective Throughput | Latency | Range |
|--------|--------------|---------------------|---------|-------|
| LoRa SF7 | 37.5 kbps | 25 kbps | 100ms | 2km |
| LoRa SF12 | 0.3 kbps | 0.2 kbps | 2s | 10km |
| BLE 5.0 | 1 Mbps | 100 kbps | 20ms | 100m |
| SMS | 1.2 kbps | 0.8 kbps | 5-30s | Global |

### Query Response Times

```
Simple Query (e.g., "STATUS room:127"):
- LoRa: 200ms - 2s
- Bluetooth: 50ms - 200ms  
- SMS: 5s - 30s

Floor Plan Request:
- LoRa: 2s - 10s
- Bluetooth: 500ms - 2s
- SMS: 30s - 2min (multi-part)

Bulk Data Transfer (100 ArxObjects):
- LoRa: 5s - 60s
- Bluetooth: 1s - 5s
- SMS: Not recommended
```

## Implementation Roadmap

### Phase 1: LoRa Dongle (Weeks 1-4)
- [ ] Design PCB for USB-C dongle
- [ ] Implement SAMD21 firmware
- [ ] Create mobile app serial drivers
- [ ] Test range and reliability

### Phase 2: Bluetooth Bridge (Weeks 5-8)
- [ ] Update ESP32 firmware for BLE
- [ ] Implement mesh bridge protocol
- [ ] Add BLE to mobile app
- [ ] Security and pairing flow

### Phase 3: SMS Gateway (Weeks 9-12)
- [ ] Set up cellular modem hardware
- [ ] Implement SMS parser
- [ ] Create compression algorithm
- [ ] Emergency command set

### Phase 4: Integration (Weeks 13-16)
- [ ] Unified mobile app UI
- [ ] Automatic transport selection
- [ ] Offline caching strategy
- [ ] Field testing all methods

## Testing Strategy

### Range Testing
```bash
# LoRa range test script
./test_lora_range.sh --sf 7 --power 20 --distance 1000
./test_lora_range.sh --sf 12 --power 20 --distance 10000

# Bluetooth coverage mapping
./map_ble_coverage.sh --building "School A" --floor 1
```

### Reliability Metrics
- Packet loss rate < 1% at nominal range
- Connection establishment < 5 seconds
- Automatic reconnection on signal loss
- Graceful degradation with interference

### Security Validation
- Penetration testing of all protocols
- Fuzzing of parser implementations
- Authentication bypass attempts
- Replay attack prevention

## Cost Analysis

### Per-Building Setup
| Component | Quantity | Unit Cost | Total |
|-----------|----------|-----------|-------|
| ESP32 nodes (BLE) | Existing | $0 | $0 |
| Cellular modem | 1 | $150 | $150 |
| SIM card (annual) | 1 | $60 | $60 |
| **Total** | | | **$210** |

### Per-User Hardware
| Component | Cost | Optional |
|-----------|------|----------|
| LoRa dongle | $30 | Yes |
| Mobile app | Free | No |
| SMS credits | Pay-per-use | Yes |

## Conclusion

This hybrid approach provides multiple pathways for remote building access while maintaining Arxos's core principle of air-gapped operation. Users can choose their preferred method based on needs, with seamless fallback between options. The architecture scales from emergency SMS access that works on any phone to high-bandwidth LoRa connections for power users, all without ever touching the internet.

The true innovation is proving that practical remote access doesn't require cloud services or internet connectivity - just clever use of existing radio technologies and thoughtful protocol design.