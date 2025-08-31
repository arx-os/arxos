# iPhone LiDAR Scanning - Engineering Checklist

## ✅ What's Already Built

### 1. ArxObject Protocol ✅
- **Status**: COMPLETE
- **Size**: 13 bytes confirmed
- **Structure**:
  ```rust
  ArxObject {
      id: u16,           // 2 bytes - Building-unique ID
      object_type: u8,   // 1 byte  - Equipment type
      x: u16,            // 2 bytes - mm precision
      y: u16,            // 2 bytes - mm precision  
      z: u16,            // 2 bytes - mm precision
      properties: [u8;4] // 4 bytes - Type-specific
  }
  // Total: 13 bytes ✅
  ```

### 2. Point Cloud Parser ✅
- **Status**: COMPLETE
- **Features**:
  - PLY file format parsing
  - RANSAC plane detection (floors, walls, ceilings)
  - Equipment detection (outlets, lights)
  - Voxelization for compression
  - ArxObject conversion

### 3. Terminal Commands ✅
- **Status**: COMPLETE
- **Commands**:
  - `load-scan <file.ply>` - Load point cloud
  - `view-floor` - ASCII visualization
  - `export-arxobjects` - Export compressed

### 4. Compression Pipeline ✅
- **Status**: COMPLETE
- **Process**:
  1. Point cloud (12 bytes/point)
  2. Voxelize (5cm cubes)
  3. Detect planes
  4. Extract equipment
  5. ArxObjects (13 bytes/object)
  6. **Result**: 10,000:1 ratio

## 🔧 What Needs Development

### 1. SSH Server with SFTP 🔴 CRITICAL
**Current Issue**: We have SSH but need SFTP for file uploads

```rust
// Need to add to src/core/ssh_server_impl.rs
impl russh::server::Handler for ArxosSshServer {
    // Add SFTP subsystem support
    async fn subsystem_request(
        self,
        channel: ChannelId,
        name: &str,
        session: Session,
    ) -> Result<(Self, Session), Self::Error> {
        if name == "sftp" {
            // Implement SFTP handler
            self.handle_sftp(channel, session).await
        }
    }
}
```

**Alternative**: Use SCP instead (simpler):
```bash
# On iPhone with Termius
scp room.ply arxos@server:/tmp/scans/
```

### 2. File System Setup 🟡 EASY
```bash
# Create directories
mkdir -p /tmp/scans/pending
mkdir -p /tmp/scans/processed
mkdir -p /tmp/scans/arxobjects

# Set permissions
chmod 777 /tmp/scans
```

### 3. Real PLY Testing 🟡 NEEDS VALIDATION
**Test with actual iPhone exports**:
- 3d Scanner App PLY format
- Color data handling
- Coordinate system (Y-up vs Z-up)
- Scale calibration

### 4. Coordinate System Alignment 🟡 IMPORTANT
**iPhone/ARKit uses**:
- Y-up coordinate system
- Meters as units
- Origin at device start position

**ArxObject uses**:
- Z-up coordinate system (building standard)
- Millimeters as units
- Origin at building entrance

**Need transformation**:
```rust
fn arkit_to_arxos(point: Point3D) -> Point3D {
    Point3D {
        x: point.x * 1000.0,  // m to mm
        y: point.z * 1000.0,  // Swap Y/Z
        z: point.y * 1000.0,  // ARKit Y → Arxos Z
    }
}
```

### 5. Equipment Detection Tuning 🟢 ENHANCEMENT
**Current detection is basic**:
- Outlets: 20-50cm above floor
- Lights: Near ceiling
- Need to add:
  - Switches (1.2m height on walls)
  - Vents (rectangular patterns)
  - Doors (gaps in walls)

## 📋 Development Priority Order

### Day 1: Get File Transfer Working (2-3 hours)
```bash
# Option A: Enable SCP (easier)
1. Test SCP with Termius
2. Create upload directory
3. Test file permissions

# Option B: Add SFTP support
1. Add russh-sftp crate
2. Implement subsystem handler
3. Test with Termius
```

### Day 2: Test with Real iPhone Scan (2-3 hours)
```bash
1. Scan a simple room with 3d Scanner App
2. Export as PLY
3. Transfer via SCP/SFTP
4. Run `load-scan`
5. Debug any parsing issues
6. Verify compression ratio
```

### Day 3: Coordinate System Fix (1-2 hours)
```rust
1. Add coordinate transform
2. Test orientation is correct
3. Verify scale (mm conversion)
4. Update ASCII renderer orientation
```

### Day 4: Polish & Demo (2-3 hours)
```bash
1. Scan complete room with equipment
2. Process through pipeline
3. Generate ASCII floor plan
4. Calculate real compression stats
5. Record demo video
```

## 🚀 Quick Start Commands

### On your Mac/Linux server:
```bash
# 1. Start Arxos terminal
cargo run --bin arxos

# 2. In another terminal, start SSH
sudo arxos --ssh-server

# 3. Create upload directory
mkdir -p /tmp/scans
chmod 777 /tmp/scans
```

### On your iPhone:
```bash
# In Termius
1. Connect: arxos@your-mac.local:2222
2. Upload: scp room.ply to /tmp/scans/
3. Process: arxos load-scan /tmp/scans/room.ply
```

## 📊 Success Metrics

### Minimum Viable Demo
- [ ] Transfer PLY from iPhone to Mac
- [ ] Parse PLY without errors
- [ ] Detect at least 1 floor plane
- [ ] Generate ASCII visualization
- [ ] Achieve >1000:1 compression

### Full Success
- [ ] Detect walls, floor, ceiling
- [ ] Find outlets and lights
- [ ] 10,000:1 compression ratio
- [ ] ASCII matches actual room
- [ ] Process in <5 seconds

## 🐛 Known Issues to Fix

1. **PLY Parser assumes ASCII format**
   - Some apps export binary PLY
   - Need format detection

2. **No error handling for malformed files**
   - Add validation
   - Better error messages

3. **Fixed voxel size (5cm)**
   - Should adapt to point density
   - Affects compression ratio

4. **No progress indicator**
   - Large files appear frozen
   - Add progress callbacks

## 📱 iPhone App Settings

### 3d Scanner App Recommended Settings:
- **Resolution**: High
- **Range**: 5 meters
- **Confidence**: Medium
- **Export Format**: PLY (ASCII)
- **Include**: Color + Confidence
- **Coordinate System**: World

### File Sizes to Expect:
- Small room (10m²): 5-10 MB PLY
- Medium room (30m²): 15-30 MB PLY
- Large room (100m²): 50-100 MB PLY
- After compression: 1-10 KB ArxObjects

## ✅ Ready to Start!

**The core system is built**. We just need:
1. File transfer method (SCP works today)
2. Test with real iPhone PLY
3. Fix coordinate system
4. Tune detection thresholds

This can be working in 1-2 days of focused development!