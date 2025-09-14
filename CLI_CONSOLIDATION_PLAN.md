# CLI Consolidation Plan

## Current State
- **arxos** (NEW): Unified CLI with clean architecture
- **arx-legacy**: Feature-complete with 22 commands (misnomer - it's actually the main tool)
- **bim**: Clean Building-as-Code focused tool
- **arxd**: Daemon (keep separate)
- **arxos-server**: API server (keep separate)

## Consolidation Strategy

### Phase 1: Immediate (Done)
- ✅ Created unified `arxos` CLI structure
- ✅ Implemented core commands (import, export, simulate, query, sync)

### Phase 2: Migration
1. Port best features from `arx-legacy` to `arxos`:
   - Enhanced PDF import
   - IFC support
   - 3D rendering
   - Advanced queries

2. Keep `bim` as lightweight alternative for text-only workflows

### Phase 3: Cleanup
- Rename `arx-legacy` → `arx-v1` (acknowledge it's not legacy)
- Deprecate `arx-v1` once `arxos` has feature parity
- Maintain `bim` for Building-as-Code purists

## Final Architecture
```
arxos         # Main unified CLI
arxos-server  # REST API
arxd          # File watcher daemon
bim           # Lightweight text-focused tool (optional)
```