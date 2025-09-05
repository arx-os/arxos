# ArxOS RF-Only Deployment Overview

This document summarizes the offline-first posture, compile-time features, and onboarding flows implemented in Phase 5.

## Compile-time features

- rf_only (default):
  - Enforces local-only operation and disables outbound network code paths.
  - Displays a startup banner in terminal noting RF-only mode.

- internet_touchpoints (off by default):
  - Gates optional SMS onboarding code and related docs.
  - Must be explicitly enabled at build time.

- mobile_offline:
  - Enables BLE/USB bindings for mobile shells (no network permissions).

## RF invite tokens

- Encoded as 13B `ArxObject` with `object_types::ACCESS_INVITE`.
- Properties encode role and duration; MAC-authenticated using `PacketAuthenticator`.
- Terminal commands:
  - `invite generate <viewer|tech|admin> <hours>` → prints 13B hex.
  - `invite accept <13B-hex>` → validates and displays assigned role/duration.

## Security

- Sealed frames with 16B MAC and anti‑replay window on radio frames.
- Invite tokens include a compact MAC check to prevent tampering.

## Distribution

- District self‑provisioning: signed images + BOM + first‑boot pairing.
- Optional public read‑only mirror for transparency.

For a visual overview, see `docs/04-DEPLOYMENT.md`.
For provisioning steps and BOM, see `docs/PROVISIONING.md`.
For planning airtime/latency, see `docs/LATENCY_ESTIMATES.md`.
For onboarding steps, see `docs/ONBOARDING_WORKFLOW.md` and `docs/DAY_OF_SCAN_CHECKLIST.md`.
For feature flags, see `docs/FEATURE_FLAGS.md`.

## Concepts and Technical
- Concepts: `docs/concepts/BAS_BMS_SUPERVISORY.md`
- Wire format: `docs/technical/ARXOBJECT_WIRE_FORMAT.md`
- Terminal quick reference: `docs/technical/TERMINAL_API.md`
- Engineering Safety Profile: `docs/ENGINEERING_SAFETY_PROFILE.md`
# ArxOS Documentation

> **ArxOS: The Routing Company for Building Intelligence**

ArxOS routes building intelligence through RF mesh networks, creating a global infrastructure for smart buildings without internet connectivity.

## Core Documentation

| Document | Description |
|----------|-------------|
| **[01-VISION.md](01-VISION.md)** | What ArxOS is: A routing company leveraging schools as backbone infrastructure |
| **[02-ARCHITECTURE.md](02-ARCHITECTURE.md)** | Technical architecture: RF-only mesh, file storage, terminal interface |
| **[03-ARXOBJECT.md](03-ARXOBJECT.md)** | The 13-byte universal building protocol specification |
| **[04-DEPLOYMENT.md](04-DEPLOYMENT.md)** | How to deploy ArxOS at schools and commercial buildings |
| **[05-BUSINESS.md](05-BUSINESS.md)** | Revenue model: Data routing, aggregation, and BILT economics |

## Quick Start

### For School Districts
1. Order ArxOS nodes (Raspberry Pi + LoRa)
2. Deploy one per building
3. Scan with iPhone LiDAR app
4. Mesh network auto-forms
5. Get free routing + revenue share

### For Commercial Buildings  
1. Connect to nearby school mesh
2. Choose: Share data (free) or private routing (paid)
3. Earn BILT tokens for shared data
4. Access building intelligence via terminal

### For Developers
```bash
# Clone repository
git clone https://github.com/arxos/arxos.git

# Build for Raspberry Pi
cd arxos
cargo build --release --target arm-unknown-linux-gnueabihf

# Flash to device
./scripts/flash.sh /dev/sdb
```

## Key Concepts

### The 3 Internet Touch Points
ArxOS only touches the internet at three points:
1. **Software Updates** - GitHub/USB for firmware
2. **Data Marketplace** - Aggregated intelligence sales  
3. **Emergency Services** - 911 integration (optional)

After setup, ArxOS operates completely offline via RF mesh.

### School Backbone Model
- Schools provide physical infrastructure
- ArxOS provides free routing for education
- Commercial traffic generates revenue
- 70/20/10 split: Building owners/Schools/ArxOS

### Revenue Streams
- **70%** - Aggregated data sales to insurance/real estate
- **20%** - Private routing fees from enterprises
- **10%** - Support contracts and certification

## Technical Specifications

- **Protocol**: 13-byte ArxObject
- **Compression**: 10,000,000:1 (1GB → 13 bytes)
- **Network**: LoRa 915MHz (US) / 868MHz (EU)
- **Range**: 1-10 miles per node
- **Storage**: File-based (no database)
- **Interface**: Terminal-first ASCII

## Additional Resources

### Implementation Guides
- `examples/school-deployment.md` - Step-by-step school setup
- `examples/commercial-integration.md` - Connecting commercial buildings
- `examples/data-broker-setup.md` - Setting up data aggregation

### Technical Deep Dives
- `technical/mesh_architecture.md` - RF mesh routing details
- `technical/slow_bleed_architecture.md` - Progressive detail protocol
- `technical/arxobject_specification.md` - Binary format details

### Historical/Research (Archive)
- `archive/` - Previous iterations and research documents

## Contact & Support

- **Commercial**: sales@arxos.io
- **Schools**: education@arxos.io
- **Technical**: support@arxos.io
- **GitHub**: https://github.com/arxos/arxos

## License

ArxOS Core: MIT License
ArxObject Protocol: Open Specification
Commercial Router: Proprietary

---

*"We're building the AT&T of building intelligence, one school at a time."*