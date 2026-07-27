# arxos-core

Rust core library for Arxos (Phase 0 foundation).

## Responsibilities

- Content-addressed **objects** (header + typed body)
- **Canonical CBOR** serialization + **BLAKE3** CIDs
- **Root** repository state with ed25519 author signatures
- Local **CAS** object store (Git-style fan-out)
- Optional **UniFFI** bindings for Swift

## Features

| Feature | Description |
|---------|-------------|
| *(default)* | Core library only |
| `uniffi` | Generate UniFFI scaffolding for mobile |

## Quick test

```bash
cargo test -p arxos-core
```
