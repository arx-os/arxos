# Developer Quick Start Guide

## From Zero to Building Intelligence in 30 Minutes

This guide gets you up and running with Arxos development. You'll build a working system that can compress point clouds, create AR markups, and query building intelligence.

## Prerequisites

```bash
# Required tools
- Rust 1.75+ (rustup.rs)
- Node.js 18+ (for WASM tools)
- SQLite 3.40+ (for spatial queries)
- iOS: Xcode 15+ with iOS 17 SDK
- Android: Android Studio with API 33+

# Optional but recommended
- Visual Studio Code with rust-analyzer
- TablePlus or DB Browser for SQLite
- Postman for API testing
```

## 1. Environment Setup (5 minutes)

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Install Rust if needed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Add WASM target
rustup target add wasm32-unknown-unknown

# Install wasm-pack for WASM builds
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

# Install dependencies
cargo build --all
```

### Project Structure

```
arxos/
├── crates/
│   ├── arxos-core/        # Core compression and ArxObject logic
│   ├── arxos-wasm/        # WASM bindings
│   ├── arxos-server/      # REST API server
│   └── arxos-cli/         # Terminal client
├── mobile/
│   ├── ios/               # iOS AR app
│   └── android/           # Android AR app
├── web/
│   └── demo/              # Web demo app
└── docs/                  # You are here!
```

## 2. Build Core Library (5 minutes)

### Build and Test Rust Core

```bash
# Build core library
cd crates/arxos-core
cargo build --release

# Run tests
cargo test

# Expected output:
# test compression::tests::test_point_cloud_compression ... ok
# test arxobject::tests::test_arxobject_creation ... ok
# test spatial::tests::test_nearby_query ... ok
# test result: ok. 42 passed; 0 failed
```

### Try the Compression Algorithm

```rust
// crates/arxos-core/examples/compress.rs
use arxos_core::{compress_point_cloud, CompressionOptions};

fn main() {
    // Load sample point cloud
    let points = load_sample_points(); // 1 million points
    
    // Compress with semantic understanding
    let compressed = compress_point_cloud(&points, CompressionOptions {
        target_ratio: 10000.0,
        preserve_detail: false,
        semantic_hints: vec!["wall", "door", "outlet"],
    }).unwrap();
    
    println!("Compression achieved:");
    println!("  Input: {} points ({} MB)", 
             points.len(), 
             points.len() * 12 / 1_000_000);
    println!("  Output: {} bytes", compressed.size());
    println!("  Ratio: {:.0}:1", compressed.compression_ratio);
}

// Run it:
// cargo run --example compress
// Output:
// Compression achieved:
//   Input: 1000000 points (12 MB)
//   Output: 1200 bytes
//   Ratio: 10000:1
```

## 3. Build WASM Module (5 minutes)

### Compile to WASM

```bash
# Build WASM module
cd crates/arxos-wasm
wasm-pack build --target web --out-dir pkg

# Check output
ls -lh pkg/
# arxos_wasm_bg.wasm (3.2 MB)
# arxos_wasm.js (15 KB)
# arxos_wasm.d.ts (8 KB)
```

### Test in Browser

```html
<!-- web/demo/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Arxos WASM Demo</title>
</head>
<body>
    <h1>Arxos Compression Demo</h1>
    <button id="compress">Compress Point Cloud</button>
    <div id="result"></div>
    
    <script type="module">
        import init, { compress_point_cloud } from './pkg/arxos_wasm.js';
        
        async function run() {
            await init();
            
            document.getElementById('compress').onclick = async () => {
                // Generate random point cloud
                const points = new Float32Array(3000); // 1000 3D points
                for (let i = 0; i < points.length; i++) {
                    points[i] = Math.random() * 10;
                }
                
                // Compress
                const result = compress_point_cloud(points);
                
                // Display results
                document.getElementById('result').innerHTML = `
                    <p>Input: ${points.length / 3} points</p>
                    <p>Output: ${result.size} bytes</p>
                    <p>Ratio: ${result.ratio}:1</p>
                `;
            };
        }
        
        run();
    </script>
</body>
</html>
```

```bash
# Serve the demo
cd web/demo
python3 -m http.server 8000

# Open http://localhost:8000
```

## 4. Set Up Database (5 minutes)

### Create SQLite Database

```bash
# Create database with spatial support
cd data
sqlite3 arxos.db < ../sql/schema.sql

# Verify tables
sqlite3 arxos.db ".tables"
# arxobjects  arxobjects_spatial  buildings  users  contributions
```

### Insert Test Data

```sql
-- Insert test building
INSERT INTO buildings (id, name, address, building_type)
VALUES ('jefferson-elem', 'Jefferson Elementary', '123 School St', 'school');

-- Insert test objects
INSERT INTO arxobjects (
    building_id, object_type, floor_number,
    position_x, position_y, position_z,
    properties, created_by
) VALUES 
    ('jefferson-elem', 'outlet', 1, 5000, 3000, 300,
     '{"circuit": "A-12", "voltage": 120}', 'user-123'),
    ('jefferson-elem', 'door', 1, 2000, 0, 0,
     '{"type": "emergency_exit"}', 'user-123');

-- Test spatial query
SELECT * FROM arxobjects
WHERE building_id = 'jefferson-elem'
  AND position_x BETWEEN 4000 AND 6000;
```

## 5. Run Development Server (5 minutes)

### Start REST API Server

```bash
# Run server
cd crates/arxos-server
cargo run --release

# Server starts on http://localhost:3000
# 
# [2024-01-20 10:15:23] Arxos Server v1.0.0
# [2024-01-20 10:15:23] Database: data/arxos.db
# [2024-01-20 10:15:23] Listening on http://0.0.0.0:3000
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:3000/health
# {"status": "healthy", "version": "1.0.0"}

# Create ArxObject
curl -X POST http://localhost:3000/api/v1/arxobjects \
  -H "Content-Type: application/json" \
  -d '{
    "buildingId": "jefferson-elem",
    "objectType": "outlet",
    "position": {"x": 5420, "y": 3180, "z": 300},
    "properties": {"circuit": "A-12", "voltage": 120}
  }'
# {"id": "...", "biltEarned": 20}

# Query nearby objects
curl "http://localhost:3000/api/v1/buildings/jefferson-elem/nearby?x=5000&y=3000&z=300&radius=5"
# {"objects": [...], "count": 3}
```

## 6. Build iOS AR App (10 minutes)

### Set Up iOS Project

```bash
cd mobile/ios
open ArxosAR.xcodeproj

# In Xcode:
# 1. Select your development team
# 2. Connect iPhone with LiDAR (iPhone 12 Pro or newer)
# 3. Build and run (Cmd+R)
```

### Key iOS Integration Points

```swift
// ViewController.swift - Key integration
class ARViewController: UIViewController {
    // WASM engine for compression
    let arxosEngine = ArxosWASMEngine()
    
    // AR session for LiDAR
    let arSession = ARSession()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Initialize WASM
        arxosEngine.initialize()
        
        // Configure AR for LiDAR
        let config = ARWorldTrackingConfiguration()
        config.sceneReconstruction = .mesh
        arSession.run(config)
    }
    
    // Handle tap for markup
    @IBAction func handleTap(_ gesture: UITapGestureRecognizer) {
        let location = gesture.location(in: arView)
        
        // Get 3D position
        if let position = hitTest(at: location) {
            // Show marking interface
            showMarkupMenu(at: position)
        }
    }
    
    // Process LiDAR scan
    func processPointCloud(_ pointCloud: ARPointCloud) {
        // Compress using WASM
        let compressed = arxosEngine.compress(pointCloud)
        
        print("Compressed \(pointCloud.count) points to \(compressed.size) bytes")
        print("Ratio: \(compressed.ratio):1")
        
        // Store in database
        database.insert(compressed)
    }
}
```

## 7. Complete Working Example

### Full Compression + Markup + Query Flow

```rust
// examples/full_flow.rs
use arxos::{
    compress_point_cloud,
    create_ar_markup,
    store_arxobject,
    query_nearby,
    calculate_bilt,
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Initialize database
    let db = Connection::open("arxos.db")?;
    
    // 2. Simulate LiDAR scan
    println!("Simulating LiDAR scan...");
    let point_cloud = generate_room_scan(); // 500K points
    
    // 3. Compress to ArxObject
    println!("Compressing point cloud...");
    let compressed = compress_point_cloud(&point_cloud, Default::default())?;
    println!("  Achieved {:.0}:1 compression", compressed.ratio);
    
    // 4. Store structure
    store_arxobject(&db, &compressed)?;
    println!("  Stored room structure");
    
    // 5. Simulate AR markup
    println!("\nSimulating AR markups...");
    let markups = vec![
        create_ar_markup(
            Position3D::new(5000, 3000, 300),
            ObjectType::Outlet,
            properties!{
                "circuit" => "A-12",
                "voltage" => 120,
                "amperage" => 15
            },
            &user
        )?,
        create_ar_markup(
            Position3D::new(2000, 0, 0),
            ObjectType::Door,
            properties!{
                "type" => "emergency_exit",
                "width" => 36
            },
            &user
        )?,
    ];
    
    // 6. Calculate BILT rewards
    for markup in &markups {
        let bilt = calculate_bilt(markup);
        println!("  {} at {:?}: {} BILT", 
                 markup.object_type, 
                 markup.position,
                 bilt);
        store_arxobject(&db, &markup.to_arxobject())?;
    }
    
    // 7. Query spatial data
    println!("\nQuerying nearby objects...");
    let nearby = query_nearby(
        &db,
        Position3D::new(5000, 3000, 300),
        5.0 // 5 meter radius
    )?;
    
    for obj in nearby {
        println!("  Found: {} at {:.1}m distance",
                 obj.object_type,
                 obj.distance_from(Position3D::new(5000, 3000, 300)));
    }
    
    // 8. Generate compliance report
    println!("\nGenerating compliance report...");
    let report = generate_fire_safety_report(&db, "jefferson-elem")?;
    println!("  Fire extinguishers: {}", report.extinguisher_count);
    println!("  Emergency exits: {}", report.exit_count);
    println!("  Compliance status: {}", report.status);
    
    Ok(())
}
```

## 8. Development Workflow

### Recommended Development Process

```bash
# 1. Make changes to core library
cd crates/arxos-core
# Edit src/compression.rs

# 2. Test locally
cargo test
cargo run --example compress

# 3. Build WASM if needed
cd ../arxos-wasm
wasm-pack build

# 4. Test in browser
cd ../../web/demo
python3 -m http.server

# 5. Test on device
cd ../../mobile/ios
xcodebuild -scheme ArxosAR -destination 'platform=iOS' build
```

### Hot Reload Development

```bash
# Terminal 1: Watch Rust changes
cargo watch -x test -x build

# Terminal 2: Watch WASM changes
cargo watch -s "wasm-pack build --target web"

# Terminal 3: Serve web demo
npx live-server web/demo

# Terminal 4: Database queries
sqlite3 arxos.db
```

## 9. Common Issues and Solutions

### Issue: WASM module too large
```bash
# Solution: Optimize for size
wasm-pack build --release -- --features wee_alloc
wasm-opt -Os -o optimized.wasm arxos_wasm_bg.wasm
```

### Issue: Spatial queries slow
```sql
-- Solution: Ensure R-tree index exists
CREATE INDEX IF NOT EXISTS idx_spatial 
ON arxobjects_spatial(min_x, max_x, min_y, max_y, min_z, max_z);

-- Analyze query plan
EXPLAIN QUERY PLAN
SELECT * FROM arxobjects WHERE ...;
```

### Issue: iOS app crashes on device
```swift
// Solution: Check memory usage
class MemoryManager {
    static func checkMemory() {
        let memoryUsage = getMemoryUsage()
        if memoryUsage > 100_000_000 { // 100MB
            // Reduce point cloud density
            pointCloud.downsample(factor: 2)
        }
    }
}
```

## 10. Next Steps

### Essential Reading
1. [Bidirectional Architecture](../01-vision/README.md)
2. [ArxObject Compression](../02-arxobject/README.md)
3. [API Reference](../09-api-reference/README.md)

### Sample Projects
- `examples/school-mapping/` - Complete school mapping app
- `examples/fire-safety/` - Compliance reporting system
- `examples/maintenance/` - Predictive maintenance dashboard

### Join the Community
- Discord: [discord.gg/arxos](https://discord.gg/arxos)
- GitHub Discussions: [github.com/arxos/arxos/discussions](https://github.com/arxos/arxos/discussions)
- Weekly Dev Calls: Thursdays 2pm EST

---

*From zero to building intelligence in 30 minutes. Welcome to Arxos!*