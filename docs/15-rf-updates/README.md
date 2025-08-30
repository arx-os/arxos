# RF-Only Software Updates

## How to Update 10,000 Buildings Without Internet

Arxos delivers software updates entirely through RF mesh networks. No internet connection required, ever. This document describes how updates propagate from Arxos HQ to every node in the field.

## 🎯 The Challenge and Solution

### Traditional Update Problems
- Requires internet connectivity
- Vulnerable to cyber attacks during update
- Can be blocked by firewalls
- Creates security holes
- Depends on cloud infrastructure

### Arxos RF-Only Solution
- Updates via radio frequency only
- Air-gapped security maintained
- Works during internet outages
- Cannot be hacked remotely
- Self-propagating mesh distribution

## 📡 Update Distribution Architecture

```
┌─────────────────────────────────────────────────────────┐
│              ARXOS HEADQUARTERS                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Development Team → Build System → Signed Binary        │
│                                                          │
│  Cryptographic Signature:                               │
│  - SHA-256 hash of binary                               │
│  - Ed25519 signature                                    │
│  - Version metadata                                     │
│                                                          │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│          RF BROADCAST STATION (Regional)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  High-Power Transmitter:                                │
│  - Frequency: 915MHz ISM band                           │
│  - Power: 1W (FCC Part 15 compliant)                   │
│  - Range: 50km radius                                   │
│  - Protocol: Meshtastic broadcast                       │
│                                                          │
└────────────────┬─────────────────────────────────────────┘
                 │ RF Broadcast
                 ▼
┌─────────────────────────────────────────────────────────┐
│            PRIMARY MESH NODES (City-level)               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Gateway Nodes with External Antennas:                  │
│  - Receive broadcast updates                            │
│  - Verify cryptographic signature                       │
│  - Begin mesh propagation                               │
│                                                          │
└────────────────┬─────────────────────────────────────────┘
                 │ Mesh Network
                 ▼
┌─────────────────────────────────────────────────────────┐
│         BUILDING MESH NETWORKS (Local)                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Standard Nodes:                                        │
│  - Receive update from nearby nodes                     │
│  - Verify signature before installing                   │
│  - Forward to other nodes (epidemic routing)            │
│  - Automatic rollback on failure                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 🔄 Update Propagation Protocol

### 1. Update Announcement Phase
```rust
struct UpdateAnnouncement {
    version: Version,
    size: u32,
    hash: [u8; 32],  // SHA-256
    signature: [u8; 64],  // Ed25519
    priority: UpdatePriority,
    release_notes_hash: [u8; 32],
}

enum UpdatePriority {
    Critical,    // Security fixes - immediate installation
    Important,   // Bug fixes - install within 24 hours
    Normal,      // Features - install within 7 days
    Optional,    // Enhancements - user choice
}
```

### 2. Chunk Distribution Phase
```rust
struct UpdateChunk {
    version: Version,
    chunk_index: u16,
    total_chunks: u16,
    data: [u8; 240],  // Fits in LoRa packet
    checksum: u16,
}

// Updates are split into chunks for mesh transmission
impl UpdateDistributor {
    fn broadcast_update(&self, binary: &[u8]) {
        let chunks = self.split_into_chunks(binary, 240);
        
        for chunk in chunks {
            // Broadcast each chunk multiple times
            for _ in 0..3 {
                self.rf_broadcast(chunk);
                thread::sleep(Duration::from_secs(10));
            }
        }
    }
}
```

### 3. Mesh Propagation Phase
```rust
impl MeshNode {
    fn handle_update_chunk(&mut self, chunk: UpdateChunk) {
        // Store chunk
        self.update_cache.insert(chunk.chunk_index, chunk.data);
        
        // Forward to neighbors (epidemic routing)
        for neighbor in &self.neighbors {
            if !neighbor.has_chunk(chunk.chunk_index) {
                self.forward_chunk(neighbor, &chunk);
            }
        }
        
        // Check if complete
        if self.update_cache.is_complete() {
            self.verify_and_install();
        }
    }
}
```

## 🛡️ Security Mechanisms

### Cryptographic Verification
```rust
struct UpdateVerification {
    // Only updates signed by Arxos HQ are accepted
    const PUBLIC_KEY: &'static [u8; 32] = include_bytes!("arxos_public_key.pub");
    
    fn verify_update(&self, update: &[u8], signature: &[u8; 64]) -> bool {
        // Ed25519 signature verification
        ed25519::verify(signature, update, Self::PUBLIC_KEY)
    }
    
    fn verify_integrity(&self, chunks: &[UpdateChunk]) -> bool {
        // Reassemble and hash
        let binary = self.reassemble_chunks(chunks);
        let hash = sha256::hash(&binary);
        
        // Compare with announced hash
        hash == self.announced_hash
    }
}
```

### Rollback Protection
```rust
struct UpdateSafety {
    fn safe_update(&mut self) -> Result<(), UpdateError> {
        // Keep previous version
        self.backup_current_version()?;
        
        // Install new version
        self.install_update()?;
        
        // Self-test
        if !self.self_test() {
            // Automatic rollback
            self.restore_backup()?;
            return Err(UpdateError::SelfTestFailed);
        }
        
        Ok(())
    }
}
```

## 📊 Update Distribution Timeline

### Normal Update (Feature Release)
```
Hour 0:   Arxos HQ broadcasts update
Hour 1:   Regional towers receive and rebroadcast
Hour 6:   Major cities have 80% coverage
Hour 24:  Suburban areas have 90% coverage
Hour 48:  Rural areas have 95% coverage
Day 7:    99.9% of nodes updated
```

### Critical Update (Security Fix)
```
Hour 0:   Emergency broadcast on priority channel
Hour 1:   All gateway nodes force-receive
Hour 2:   Mesh networks enter priority mode
Hour 4:   Urban areas 100% updated
Hour 8:   Suburban areas 100% updated
Hour 12:  Rural areas 95% updated
Hour 24:  Manual intervention for remaining 5%
```

## 🔧 Update Management Commands

### For Arxos HQ
```bash
# Build and sign update
$ arxos-dev build --release
$ arxos-dev sign --key=private.key --version=2.1.0

# Broadcast update
$ arxos-dev broadcast --priority=normal --region=north-america
> Broadcasting version 2.1.0 to RF network...
> Estimated propagation: 48 hours

# Monitor deployment
$ arxos-dev monitor-update --version=2.1.0
> Nodes updated: 8,457 / 10,000 (84.5%)
> Estimated completion: 14 hours
```

### For End Users (via Terminal)
```bash
# Check for updates (via mesh)
$ arxos update-status
> Current version: 2.0.9
> Available update: 2.1.0 (received 47/50 chunks)
> Priority: Normal
> ETA: 20 minutes

# Manual update trigger
$ arxos update-now
> Assembling update from mesh cache...
> Verifying signature... OK
> Installing version 2.1.0...
> Restarting services...
> Update complete ✓

# View update history
$ arxos update-history
> 2.1.0 - Installed 2024-03-15 (RF mesh)
> 2.0.9 - Installed 2024-02-28 (RF mesh)
> 2.0.8 - Installed 2024-02-14 (RF mesh)
> [Never connected to internet]
```

## 🌍 Regional Broadcasting Infrastructure

### Arxos RF Broadcast Stations
```yaml
North America:
  - Location: Denver, CO (central US)
  - Power: 1W omnidirectional
  - Coverage: 2000km radius
  - Backup: Los Angeles, New York

Europe:
  - Location: Frankfurt, Germany
  - Power: 500mW (EU regulations)
  - Coverage: 1500km radius
  - Backup: London, Madrid

Asia-Pacific:
  - Location: Singapore
  - Power: 1W directional array
  - Coverage: 2500km radius
  - Backup: Tokyo, Sydney
```

### Mobile Update Vehicles
For remote installations:
```yaml
Update Truck:
  - High-gain antenna array
  - 100W amplifier (licensed)
  - Range: 200km
  - Purpose: Rural/remote buildings
  
Update Drone:
  - Autonomous flight
  - LoRa transmitter
  - Range: 50km
  - Purpose: Disaster areas
```

## 📈 Update Metrics

### Success Rates
```
Standard mesh propagation: 99.7% within 48 hours
Emergency updates: 99.9% within 12 hours
Remote locations: 95% within 7 days
Disaster recovery: 90% within 24 hours
```

### Bandwidth Usage
```
Update size: 5-10MB typical
Chunk size: 240 bytes
Total chunks: ~40,000
Transmission time per chunk: 100ms
Total air time: ~67 minutes
Spread over: 48 hours
Efficiency: 0.2% bandwidth usage
```

## 🚀 Future Enhancements

### Satellite Distribution
```rust
// For truly global coverage
struct SatelliteUpdate {
    // LoRa satellites broadcast updates globally
    // No ground infrastructure needed
    // Works in Antarctica, oceans, space stations
}
```

### Differential Updates
```rust
// Only send changed bytes
struct DeltaUpdate {
    base_version: Version,
    patches: Vec<BinaryPatch>,
    compressed_size: usize,  // 90% smaller
}
```

## 🎯 Why RF-Only Updates Are Superior

1. **Security**: Air-gapped, impossible to hack remotely
2. **Reliability**: Works during internet outages
3. **Privacy**: No tracking, no analytics, no cloud
4. **Sovereignty**: Countries control their own updates
5. **Resilience**: Survives cyber wars and disasters

## 📝 Regulatory Compliance

### FCC Part 15 (USA)
- ISM band usage (915MHz)
- 1W power limit without license
- Frequency hopping spread spectrum

### ETSI (Europe)
- 868MHz band
- 500mW power limit
- Duty cycle restrictions

### Global
- ITU Region 1/2/3 compliance
- Local amateur radio cooperation
- Emergency services coordination

---

*"Updates without internet. Security through isolation."*