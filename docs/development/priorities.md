# Arxos Development Priorities

## 🔴 Week 1-2: iOS Scanner (BLOCKING)

The entire system depends on capturing building data. Without the iOS app, we have no input.

### Implementation Plan
```swift
// 1. Create new Xcode project: ArxosScanner
// 2. Integrate RoomPlan API
// 3. Add these core features:

struct ScannedRoom {
    let pointCloud: ARPointCloud
    let dimensions: RoomDimensions
    let objects: [DetectedObject]
}

func convertToArxObjects(_ room: ScannedRoom) -> [ArxObject] {
    // Semantic compression here
}

func exportViaUSB(_ objects: [ArxObject]) {
    // Send to terminal via Lightning/USB-C
}
```

### Deliverables
- [ ] Basic RoomPlan scanning
- [ ] ArxObject conversion
- [ ] USB data export
- [ ] Simple equipment marking UI
- [ ] Test with 5 different rooms

## 🔴 Week 2-3: Hardware Validation

Must prove the RF mesh actually works before continuing.

### Hardware Shopping List
```
5x ESP32-S3-DevKitC-1 ($10 each) = $50
5x SX1262 LoRa Module ($15 each) = $75
5x Antennas + cables = $25
Total: $150
```

### Testing Checklist
- [ ] Flash firmware to all nodes
- [ ] Verify mesh formation (minimum 3 nodes)
- [ ] Test indoor range (expect 100-300m)
- [ ] Test outdoor range (expect 1-5km)
- [ ] Measure packet loss and retry rates
- [ ] Verify SQLite works on ESP32
- [ ] Test battery life (target: 30 days)

### Test Locations
1. Single building - full coverage test
2. Campus setting - multi-building mesh
3. Interference test - near WiFi/Bluetooth

## 🟡 Week 3-4: Mesh Routing Implementation

Current routing is just a stub. Need real implementation.

### Algorithm: Epidemic Routing with TTL
```rust
impl MeshRouter {
    fn route_packet(&mut self, packet: Packet) {
        // 1. Check if we've seen this packet (by ID)
        if self.seen_packets.contains(&packet.id) {
            return; // Prevent loops
        }
        
        // 2. Record packet
        self.seen_packets.insert(packet.id);
        
        // 3. Process locally if for us
        if packet.dest == self.node_id || packet.dest == BROADCAST {
            self.process_local(packet.clone());
        }
        
        // 4. Forward if TTL > 0
        if packet.ttl > 0 {
            packet.ttl -= 1;
            self.broadcast_to_neighbors(packet);
        }
    }
}
```

### Features to Implement
- [ ] Packet deduplication
- [ ] TTL (Time To Live) management  
- [ ] Neighbor discovery protocol
- [ ] Link quality estimation
- [ ] Adaptive routing based on RSSI
- [ ] Network partition detection

## 🟢 Week 4-5: Integration & Testing

### System Integration Tests
- [ ] iOS → Terminal → Mesh → Database flow
- [ ] PDF → Terminal → ArxObjects → Mesh flow
- [ ] Multi-node query propagation
- [ ] Network partition and healing
- [ ] Power failure recovery

### Performance Benchmarks
- [ ] Compression ratio: Must achieve 10,000:1
- [ ] Query time: Must be <50ms local, <500ms mesh
- [ ] Packet delivery: >95% success rate
- [ ] Battery life: >30 days per node
- [ ] Mesh formation: <30 seconds

## 📊 Success Metrics

### MVP Completion Criteria
1. **Data Input**: iOS app can scan and export room data ✓
2. **Compression**: Achieves 10,000:1 ratio (50MB → 5KB) ✓  
3. **Mesh Network**: 5+ nodes maintain stable mesh ✓
4. **Queries**: Can query objects across mesh network ✓
5. **Reliability**: System recovers from node failures ✓

### Demo Scenario
```bash
# 1. Scan classroom with iPhone (20 seconds)
# 2. Connect iPhone to laptop via USB
# 3. Terminal auto-imports scan data
# 4. SSH to mesh gateway node
# 5. Deploy objects to mesh network
# 6. Query from any node:
arxos query "room:127 type:outlet"
# Results return in <500ms
```

## 🚫 NOT Priorities Right Now

These can wait until after MVP:
- BILT token economics
- Advanced visualization
- Multi-building federation  
- Predictive maintenance
- Cloud backup (never - violates air-gap)
- Web interface (never - RF only)

## 📝 Development Notes

### Resource Constraints
- Single developer
- $150 hardware budget
- 5-6 week timeline
- Must maintain air-gap principle

### Risk Mitigation
1. **iOS App Store**: Use TestFlight for distribution
2. **Hardware availability**: Order ESP32s immediately
3. **RF interference**: Test in multiple environments
4. **Battery life**: Accept wall power for MVP

## 🎯 THE Goal

**In 6 weeks**: Demonstrate a complete scan-to-query workflow where:
1. iPhone scans a room in 20 seconds
2. Data compresses 10,000:1 
3. Distributes via RF mesh (no internet)
4. Queryable from any SSH terminal

This proves the concept and unlocks funding/resources for full development.

---

*Focus on the MVP. Everything else can wait.*