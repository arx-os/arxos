# Arxos Documentation

## Universal Spatial Intelligence Through Semantic Compression

Arxos transforms every iPhone into a building intelligence scanner. Using **Rust, WebAssembly, and SQL**, we compress 50MB point clouds into 5KB semantic objects, achieving 10,000:1 compression while preserving queryable building intelligence.

## 📚 Documentation Structure

### [01. Vision & Problem](01-vision/)
**The Paradigm Shift: From Graphics to Information**
- Why spatial intelligence requires semantic compression
- How iPhone LiDAR democratizes building scanning
- The 10,000:1 compression breakthrough

### [02. ArxObject Specification](02-arxobject/)
**Semantic Compression at Scale**
- ArxObject data model and compression algorithms
- From point clouds to queryable intelligence
- ASCII rendering for universal access

### [03. Technical Architecture](03-architecture/)
**The Three-Technology Stack**
- **Rust**: Memory-safe processing engine
- **WASM**: Universal deployment target
- **SQL**: Spatial queries and synchronization
- Why 3 technologies beat 50 frameworks

### [04. SQL Database](04-sql-database/)
**Spatial Intelligence Through SQL**
- PostGIS/SQLite spatial indexing
- SQL replication as mesh protocol
- Building compliance queries

### [05. WASM Deployment](05-wasm-deployment/)
**Write Once, Run Everywhere**
- iOS via WebView + WASM
- Web browsers with native WASM
- Embedded systems via WASI
- Single binary for all platforms

### [06. Mesh Network](06-mesh-network/)
**Distributed Intelligence**
- SQL replication for synchronization
- LoRa for air-gapped environments
- Epidemic propagation patterns

### [07. Terminal Interface](07-terminal-interface/)
**ASCII as Information Density**
- Terminal-first design philosophy
- Progressive detail rendering
- Command-line spatial queries

### [08. iOS Integration](08-ios-integration/)
**LiDAR to Intelligence Pipeline**
- RoomPlan API integration
- Swift ↔ WASM bridge
- 20-second scan-to-query workflow

### [09. Implementation Guide](09-implementation/)
**Building Arxos**
- Development environment setup
- Core components walkthrough
- Testing and validation

### [10. Roadmap](10-roadmap/)
**From Concept to Reality**
- 12-week single-developer plan
- Milestone-based development
- Deployment strategies

## 🚀 Quick Start

```bash
# Build the WASM module
cargo build --target wasm32-unknown-unknown

# Run terminal interface
cargo run --bin arxos-cli

# Start web interface
cd web && python3 -m http.server

# Deploy to iOS
./scripts/deploy-ios.sh
```

## 💡 Core Innovation

### The Compression Breakthrough

```
Traditional: 50MB point cloud → 45min transfer → Special viewer
Arxos:       50MB → 5KB ArxObject → 30sec transfer → Any terminal
```

### The Stack Simplification

| Aspect | Traditional | Arxos |
|--------|------------|-------|
| **Languages** | Swift, Kotlin, JavaScript, Python, C++ | Rust |
| **Frameworks** | 50+ platform-specific | WASM + SQL |
| **Codebases** | 1 per platform | 1 universal |
| **Binary Size** | 50-200MB | 2-5MB WASM |
| **Dev Time** | 12-18 months | 3-6 months |
| **Team Size** | 5-10 engineers | 1 developer |

## 🎯 Key Concepts

### Semantic Compression
Point clouds contain geometric redundancy. ArxObjects preserve semantic meaning while discarding redundant geometry, achieving 10,000:1 compression.

### Universal Deployment
One Rust codebase compiles to WASM, running on iOS, Android, Web, Desktop, and Embedded systems without platform-specific code.

### SQL as Protocol
Database replication becomes the mesh synchronization protocol, eliminating custom networking code.

## 📖 Reading Paths

### For Building Owners
1. [Vision Overview](01-vision/)
2. [ROI Analysis](01-vision/economics.md)
3. [Case Studies](10-roadmap/case-studies.md)

### For Developers
1. [Technical Architecture](03-architecture/)
2. [ArxObject Specification](02-arxobject/)
3. [Implementation Guide](09-implementation/)

### For Hardware Engineers
1. [Mesh Network Design](06-mesh-network/)
2. [LoRa Integration](06-mesh-network/lora.md)
3. [Embedded Deployment](05-wasm-deployment/embedded.md)

## 🔧 Development Status

- ✅ ArxObject specification complete
- ✅ Core compression algorithms
- ✅ Terminal rendering system
- 🚧 WASM compilation pipeline
- 🚧 iOS LiDAR integration
- 📅 SQL database layer
- 📅 Mesh synchronization

## 📞 Contact & Contributing

- **GitHub**: [github.com/arxos/arxos](https://github.com/arxos/arxos)
- **Discord**: [discord.gg/arxos](https://discord.gg/arxos)
- **Email**: team@arxos.io

---

*"The constraint is the innovation. Three technologies, universal deployment, infinite scale."*