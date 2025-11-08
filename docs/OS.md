# Arx Operating System (ArxOS) — Detailed Architecture Plan

## Core Principles (Non-Negotiable)

### One Binary, Two Domains

Same firmware runs on a $5 ESP32 sensor or a $500 x86 core router.

### ArxAddress = Universal Identifier

Every device, port, sensor, or process has a path:

- `/usa/fl/hillsborough/lithia/gaither/floor-01/mech/boiler-01`
- `/usa/fl/hillsborough/lithia/gaither/network/core-router-01/ge-0/0/1`

### YAML + Git = Truth

No databases. No drift. All state is versioned.

### Rust + eBPF + RTOS

Safe, fast, extensible — from bare metal to white-box routers.

### Zero-Touch, White-Box Ready

Flash any compatible hardware → auto-joins the district.

## Layered Architecture

```
+--------------------------------------------------+
|  User Apps (Lua/WASM)                            |
|  arx CLI / TUI / Mobile                          |
+--------------------------------------------------+
|  ArxOS Core (Rust)                               |
|  ├─ Path Engine                                  |
|  ├─ YAML Sync (Git over MQTT/QUIC)               |
|  ├─ Policy Engine (ACLs, Rate Limits)            |
|  └─ Plugin System                                |
+--------------------------------------------------+
|  Middleware                                      |
|  ├─ BACnet/Modbus/MQTT                           |
|  ├─ NetFlow/sFlow                                |
|  └─ DPDK/eBPF/XDP (network fast path)            |
+--------------------------------------------------+
|  Kernel (RIOT OS / Zephyr + Embassy-RS)          |
|  ├─ Real-Time Scheduler                          |
|  ├─ HAL (GPIO, I2C, Ethernet, WiFi)              |
|  └─ Power Management                             |
+--------------------------------------------------+
|  Hardware                                        |
|  ESP32 | RTL8380 | Intel N100 | AMD EPYC          |
+--------------------------------------------------+
```

## Hardware Tiers (All Run Same OS)

| Tier | Role | CPU | RAM | Flash | Cost | Example |
|------|------|-----|-----|-------|------|---------|
| Tier 0 | Sensor/Actuator | ESP32-S3 | 512KB | 8MB | $5 | Temp sensor, valve |
| Tier 1 | Access Point | RTL8380 | 256MB | 128MB | $80 | Classroom PoE switch |
| Tier 2 | Edge Router | RK3568 | 2GB | 16GB | $150 | Building gateway |
| Tier 3 | Core Router | Intel N100 | 16GB | 64GB | $300 | 10G district backbone |
| Tier 4 | Firewall/DC | AMD EPYC | 64GB | 1TB | $1k | DMZ, logging |

## ArxOS Boot Flow (Zero-Touch)

1. **Power On**
2. **Load ArxAddress** from flash (or DHCP option 200)
3. **Join MQTT broker**: `mqtt.arxos.net`
4. **Pull latest config**: `building.yaml` + `network.yaml`
5. **Apply config**:
   - GPIO → sensors
   - Interfaces → VLANs, OSPF, ACLs
6. **Start eBPF programs**
7. **Announce**: "online at `/gaither/network/core-router-01`"

## Data Model (YAML First)

### Building Configuration

```yaml
# building.yaml
- address: /gaither/floor-01/mech/boiler-01
  type: boiler
  model: Lochinvar KNIGHT-199
  grid: D-4
  install_date: 2025-03-15
```

### Network Configuration

```yaml
# network.yaml
- address: /gaither/network/core-router-01
  type: router
  role: core
  interfaces:
    - name: ge-0/0/1
      speed: 10G
      vlan: 100
      ospf: true
      acl_in: student-internet
  bgp:
    asn: 65001
    neighbors:
      - 10.0.0.2
```

## Networking Stack (White-Box Killer)

| Feature | Implementation |
|---------|----------------|
| L2 Switching | eBPF + TC (Traffic Control) |
| L3 Routing | FRR (Forked, Rust-wrapped) |
| ACLs | ArxAddress-based policies |
| QoS | YAML-defined rate limits |
| Telemetry | sFlow → telemetry.yaml |
| Config Sync | Git push = apply |

### Network Configuration Example

```bash
arx net apply --at /gaither/network/* --commit "Enable OSPF"
```

## Security Model

### Device Identity

ArxAddress + Ed25519 keypair

### Network Policy

```yaml
from: /gaither/students/*
to: /internet
allow: [http, https]
rate: 50Mbps
```

### Zero Trust

All traffic filtered by eBPF at ingress

## Firmware & Update System

```bash
arx firmware build --target tier3
arx firmware push --to /gaither/network/core-router-01
```

**Features:**
- Signed OTA updates
- Rollback via Git revert
- A/B partitions

## CLI / TUI Integration

```bash
arx net show --at /gaither/network/core-router-01
arx tui --netflow
arx log tail --at /gaither/network/*
```

## Extensibility (Plugin System)

```rust
// plugins/hvac_control.rs
arx_plugin! {
    name: "hvac-schedule"
    on_event: |event| {
        if event.path.starts_with("/hvac") && event.temp > 78 {
            toggle("/hvac/ac-01", false)
        }
    }
}
```
