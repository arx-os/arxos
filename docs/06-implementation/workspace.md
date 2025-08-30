# Cargo Workspace Setup

## Organizing the Rust Monorepo

### Workspace Structure

```toml
# Root Cargo.toml
[workspace]
members = [
    "arxos-core",
    "arxos-embedded",
    "arxos-terminal",
    "arxos-mobile",
]

[workspace.package]
version = "0.1.0"
authors = ["Arxos Community"]
edition = "2021"
license = "MIT OR Apache-2.0"

[workspace.dependencies]
heapless = "0.7"
postcard = "1.0"
log = "0.4"
```

### Shared Dependencies

```toml
# arxos-core/Cargo.toml
[package]
name = "arxos-core"
version.workspace = true

[dependencies]
heapless = { workspace = true }
postcard = { workspace = true }

[features]
default = ["std"]
std = []
no_std = []
```

### Cross-Platform Building

```bash
# Install targets
rustup target add wasm32-unknown-unknown  # Web
rustup target add aarch64-apple-ios       # iOS
rustup target add riscv32imc-unknown-none-elf  # ESP32

# Build everything
cargo build --workspace --release
```

---

→ Next: [Embedded Development](embedded.md)