# Arxos Data Architecture: Where Data Lives

> Note: This document describes storage topology. For protocol and object formats, see the canonicals in `../technical`.

## Overview
Arxos uses a **distributed, hierarchical data storage** model that mirrors real-world building infrastructure.

```
┌─────────────────────────────────────────────────────────┐
│                OFFLINE BACKUP MEDIA (Optional)          │
│          (e.g., encrypted external storage)             │
└─────────────────────────────────────────────────────────┘
                            ↑
                     Periodic Sync
                            ↑
┌─────────────────────────────────────────────────────────┐
│                  DISTRICT SERVERS                        │
│            (County School District Office)               │
│         Location: /var/lib/arxos/district.db            │
│              Size: ~10-100 GB per district              │
└─────────────────────────────────────────────────────────┘
                            ↑
                     RF Mesh Network
                            ↑
┌─────────────────────────────────────────────────────────┐
│                  BUILDING NODES                          │
│              (Each School Building)                      │
│         Location: /var/lib/arxos/building.db            │
│               Size: ~100 MB per building                │
└─────────────────────────────────────────────────────────┘
                            ↑
                      Local Network
                            ↑
┌─────────────────────────────────────────────────────────┐
│                    EDGE DEVICES                          │
│            (Raspberry Pi in Closets)                     │
│          Location: /home/pi/arxos/cache.db              │
│                Size: ~10 MB per zone                    │
└─────────────────────────────────────────────────────────┘
```

## Physical Data Locations

### 1. **Building Primary Database** (Main Source of Truth)
```
Path: /var/lib/arxos/building.db
Size: ~100 MB (compressed ArxObjects)
Host: Building server (closet/office)
```

**Contains:**
- All ArxObjects for the building (walls, outlets, equipment)
- Scan history and metadata
- Maintenance logs
- Spatial indices for fast queries

**Example for your scan:**
```sql
-- Your 436,556 point scan becomes ~5,000 ArxObjects
-- Stored in: /var/lib/arxos/building.db
-- Table: arxobjects
-- Size: 5,000 × 13 bytes = 65 KB (from 33 MB PLY file!)
```

### 2. **Edge Node Caches** (Distributed Throughout Building)
```
Path: /home/pi/arxos/zone_cache.db
Size: ~1-10 MB per node
Host: Raspberry Pi Zero W ($15 devices)
```

**Located:**
- Electrical closets
- Mechanical rooms  
- Network cabinets
- Every 2-3 classrooms

**Contains:**
- Local zone ArxObjects only
- Recent queries cache
- Temporary sensor data
- Mesh routing tables

### 3. **Field Device Memory** (Transient)
```
Path: In-memory only
Size: ~100 KB
Host: Phones, tablets, radios
```

**Contains:**
- Current view ArxObjects
- Active query results
- Temporary AR annotations

### 4. **District Aggregation** (School District Level)
```
Path: /var/lib/arxos/district.db
Size: ~10-100 GB (all schools)
Host: District IT center
```

**Contains:**
- Aggregated building summaries
- District-wide patterns
- Shared equipment models
- Maintenance vendor data

## Data Flow Example

When you scan and query your building:

```bash
# 1. SCAN IMPORT (On building server)
$ arxos import /Downloads/Untitled_Scan_18_44_21.ply
→ Writes to: /var/lib/arxos/building.db
→ 436,556 points → 5,000 ArxObjects (65 KB)

# 2. EDGE SYNC (Automatic)
[Every 5 minutes]
Building server → Edge nodes
/var/lib/arxos/building.db → /home/pi/arxos/zone_cache.db
Only relevant zone data synced (1-2 MB)

# 3. FIELD QUERY (Technician's phone)
Tech: "What's in room 127?"
→ Query hits nearest edge node (RF mesh)
→ Edge node checks: /home/pi/arxos/zone_cache.db
→ Returns: 8 ArxObjects (104 bytes)
→ Transit time: ~200ms

# 4. BACKUP (Offline Optional)
Building → District → Offline media (optional)
/var/lib/arxos/building.db → encrypted external drive / secure vault
Incremental backup: ~5 MB/night
```

## Why This Architecture?

### **Resilience**
- Building operates even if internet dies
- Edge nodes work even if server dies
- Mesh works even if power dies (battery backup)

### **Performance**  
- Queries answered from nearest cache
- No network round-trips for basic operations
- Sub-second response times

### **Cost**
- No external service fees for normal operations
- Commodity hardware (Raspberry Pi)
- Existing school infrastructure

### **Privacy**
- Building data stays in building
- No vendor lock-in
- School owns their data

## Storage Requirements

### Per Building (e.g., a school)
- **Initial scan**: 100 MB SQLite database
- **Annual growth**: ~50 MB (updates/maintenance)
- **5-year total**: ~350 MB

### Per District (100 schools)
- **Initial**: 10 GB aggregated
- **Annual growth**: 5 GB
- **5-year total**: 35 GB

### Compare to Traditional BIM/CAD:
- **Revit model**: 500 MB - 2 GB per building
- **Point cloud**: 1-50 GB per building
- **Arxos**: 100 MB per building (10-500× smaller!)

## Configuration Files

### Building Node
```toml
# /etc/arxos/building.toml
[database]
path = "/var/lib/arxos/building.db"
max_size = "1GB"
vacuum_schedule = "weekly"

[sync]
edge_nodes = ["pi-room-101", "pi-room-201"]
district_server = "district.arxos.local"
sync_interval = 300  # 5 minutes
```

### Edge Node
```toml
# /home/pi/.arxos/config.toml
[cache]
path = "/home/pi/arxos/zone_cache.db"
max_size = "50MB"
zone_id = "building-42-zone-3"

[upstream]
building_server = "192.168.1.100"
fallback = "mesh-only"
```

## Actual Deployment

For your use case (K-12 schools):

1. **Building Server**: Old desktop PC in IT closet
   - OS: Ubuntu Server
   - Storage: 256 GB SSD (enough for 1000+ buildings!)
   - Database: `/var/lib/arxos/building.db`

2. **Edge Nodes**: Raspberry Pi Zero W
   - Location: Every 2-3 classrooms
   - Storage: 16 GB SD card
   - Cache: `/home/pi/arxos/zone_cache.db`

3. **Backup**: District NAS
   - Nightly incremental backups
   - 30-day retention
   - Optional offline backup media rotation

The data literally lives **inside the building it describes** - making Arxos a true nervous system for infrastructure!