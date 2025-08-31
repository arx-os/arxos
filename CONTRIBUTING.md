# Contributing to Arxos

Thank you for your interest in contributing to Arxos! This air-gapped building intelligence system has unique requirements that all contributions must follow.

## Core Principles

### 🔒 The Air-Gap Promise
**"This system never touches the web"** - All contributions must maintain complete offline operation. No internet dependencies, cloud services, or external APIs.

### 📡 RF-Only Communication
- All updates via LoRa mesh network
- No WiFi, Bluetooth, or cellular
- Ed25519 signatures for authenticity

### 🗜️ Semantic Compression
- Maintain 10,000:1 compression ratio
- 13-byte ArxObject protocol is sacred
- ASCII visualization for all data

## Development Setup

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Build everything
cargo build --release

# Run tests
cargo test
```

## Code Standards

### Language
- **Rust only** for core systems
- **Swift** for iOS LiDAR app only
- **No JavaScript/TypeScript** (no web components)

### Architecture Rules
1. **no_std compatibility** where possible
2. **Terminal-first** user interface
3. **SQL as protocol** for data exchange
4. **SSH for access** (no custom protocols)

### Code Style
- Use `cargo fmt` before committing
- Run `cargo clippy` and fix warnings
- Write tests for new features
- Document public APIs

## Testing

```bash
# Unit tests
cargo test

# Integration tests
cargo test --test '*'

# Document parser tests
./scripts/test_document_parser.sh

# Terminal client test
cargo run --bin arxos -- --help
```

## Submitting Changes

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes with clear messages
4. **Test** thoroughly (no internet required!)
5. **Push** to your fork
6. **Open** a Pull Request

## Commit Messages

Follow conventional commits:
```
feat: Add equipment symbol detection
fix: Correct ArxObject checksum calculation
docs: Update SSH terminal commands
test: Add PDF parser integration tests
refactor: Simplify mesh routing algorithm
```

## Areas Needing Contribution

### High Priority
- [ ] iOS RoomPlan integration
- [ ] Mesh routing optimization
- [ ] Hardware PCB designs
- [ ] Additional equipment symbols

### Documentation
- [ ] Hardware assembly guides
- [ ] Deployment tutorials
- [ ] API examples
- [ ] Troubleshooting guides

### Testing
- [ ] Mesh network simulations
- [ ] Load testing for 1000+ nodes
- [ ] RF interference testing
- [ ] Battery life optimization

## Prohibited Changes

❌ **Never add:**
- Internet connectivity
- Cloud services
- Web interfaces
- External dependencies requiring network
- Proprietary protocols
- Closed-source components

## Questions?

- Open an issue for bugs
- Start a discussion for features
- Read [README.md](README.md) for overview
- Check [docs/](docs/) for detailed documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

*Remember: The constraint is the innovation. Keep it offline, keep it simple, keep it secure.*