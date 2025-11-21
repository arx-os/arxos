# ArxOS Documentation Index

**Last Updated:** 2025-11-11  
**Project:** ArxOS - Git for Buildings

---

## 🚀 Quick Start

- **[User Guide](./core/USER_GUIDE.md)** - Complete guide to using ArxOS CLI and features
- **[Architecture](./core/ARCHITECTURE.md)** - System architecture and design patterns  
- **[Developer Onboarding](./development/DEVELOPER_ONBOARDING.md)** - Setup guide for new developers

---

## 📚 Documentation by Category

### [Core Documentation](./core/)

Essential documentation for understanding and using ArxOS.

- **[USER_GUIDE.md](./core/USER_GUIDE.md)** - Complete guide to using ArxOS CLI and features
- **[ARCHITECTURE.md](./core/ARCHITECTURE.md)** - System architecture and design patterns
- **[CODEBASE_OVERVIEW.md](./core/CODEBASE_OVERVIEW.md)** - Technical reference and module breakdown
- **[CONFIGURATION.md](./core/CONFIGURATION.md)** - Configuration guide and options
- **[API_REFERENCE.md](./core/API_REFERENCE.md)** - Complete API documentation

### [Development](./development/)

Documentation for contributing to ArxOS development.

- **[DEVELOPER_ONBOARDING.md](./development/DEVELOPER_ONBOARDING.md)** - Setup and contribution guide
- **[ERROR_HANDLING_GUIDE.md](./development/ERROR_HANDLING_GUIDE.md)** - Error handling patterns
- **[SECURITY.md](./development/SECURITY.md)** - Security practices and scanning
- **[PERFORMANCE_GUIDE.md](./development/PERFORMANCE_GUIDE.md)** - Optimization strategies
- **[BENCHMARKS.md](./development/BENCHMARKS.md)** - Performance benchmark data
- **[RUSTDOC_GUIDE.md](./development/RUSTDOC_GUIDE.md)** - Documentation generation guide
- **[K8S_GUIDE.md](./development/K8S_GUIDE.md)** - Running ArxOS workloads on Kubernetes
- **[improvement-summaries/](./development/improvement-summaries/)** - Summaries of completed improvements

### [Mobile (Archived)](./mobile/)
- **[STATUS.md](./mobile/STATUS.md)** – Current state and archive retrieval instructions
- Legacy references (FFI guide, iOS/Android build docs, CI/CD, signup workflow) are preserved for historical purposes only.

### [Web](./web/)

Progressive Web App documentation.

- **[PWA Documentation](../pwa/)** - See pwa/README.md and pwa/docs/ for PWA development

### [Augmented Reality](./ar/)

AR and LiDAR integration documentation.

- **[AR_SCAN_INTEGRATION.md](./ar/AR_SCAN_INTEGRATION.md)** - AR/ARKit and ARCore integration
- **[AR_TERMINAL_DESIGN.md](./ar/AR_TERMINAL_DESIGN.md)** - Hybrid AR+Terminal UI design
- **[SCAN_DATA_TESTING.md](./ar/SCAN_DATA_TESTING.md)** - Scan data testing

### [Features](./features/)

Specific feature documentation.

- **[GAME_SYSTEM.md](./features/GAME_SYSTEM.md)** - Gamified PR review and planning system
- **[CONSTRAINTS.md](./features/CONSTRAINTS.md)** - Constraint validation system
- **[IFC_COMPATIBILITY.md](./features/IFC_COMPATIBILITY.md)** - IFC round-trip compatibility
- **[IFC_PROCESSING.md](./features/IFC_PROCESSING.md)** - IFC file import and conversion
- **[BUILDING_DOCS.md](./features/BUILDING_DOCS.md)** - Automatic documentation generation

### [Business](./business/)

Business and enterprise features.

- **[REWARD_SYSTEM.md](./business/REWARD_SYSTEM.md)** - DePIN rewards and licensing
- **[PAYMENT_TRACKING.md](./business/PAYMENT_TRACKING.md)** - Payment processing
- **[ENTERPRISE_DEPLOYMENT.md](./business/ENTERPRISE_DEPLOYMENT.md)** - Deploying at scale

### [Economy](./economy/)

On-chain incentives, staking, and revenue infrastructure.

- **[README.md](./economy/README.md)** - Polygon contracts, Rust services, CLI/FFI, and ops runbooks

### [Ideas](./ideas/)

Future feature exploration and brainstorming.

- **[DAILY_MOVEMENT_REPLAY.md](./ideas/DAILY_MOVEMENT_REPLAY.md)** - Movement tracking and ASCII replay

---

## 📦 Examples & Reference

### [Examples](../examples/)

Example building data files and usage patterns.

- **[Examples Index](../examples/README.md)** - Main examples directory
- **[Building Examples](../examples/buildings/)** - Building data examples
  - [Complete Office Building](../examples/buildings/building.yaml) - Full example with equipment
  - [Minimal Building](../examples/buildings/minimal-building.yaml) - Minimal valid structure
  - [Multi-Floor Building](../examples/buildings/multi-floor-building.yaml) - Multi-story example

---

## 📖 Documentation Archive

Historical and outdated documentation preserved in the [`archive/`](./archive/) directory:
- Previous implementations and plans
- Legacy mobile build guides
- Old architecture decisions
- Historical code reviews (codebase-reviews/)
- Phase completion documents (PHASE_1_COMPLETE.md, etc.)
- V1.0 release documentation

---

## 🎯 Quick Reference

**New to ArxOS?** → Start with [User Guide](./core/USER_GUIDE.md)  
**Contributing?** → See [Developer Onboarding](./development/DEVELOPER_ONBOARDING.md)  
**Security?** → Review [Security Guide](./development/SECURITY.md)  
**Adding features?** → See [Architecture](./core/ARCHITECTURE.md)  
**Need the old mobile clients?** → See [Mobile Status & Archive](./mobile/STATUS.md)  
**Building the PWA?** → See [Web Development](./web/DEVELOPMENT.md)  
**Deploying at scale?** → See [Enterprise Deployment](./business/ENTERPRISE_DEPLOYMENT.md)  
**Need performance tips?** → See [Performance Guide](./development/PERFORMANCE_GUIDE.md)  
**Looking for API details?** → See [API Reference](./core/API_REFERENCE.md)  
**Gamified building management?** → See [Game System](./features/GAME_SYSTEM.md)  
**Reviewing contractor PRs?** → See [Game System](./features/GAME_SYSTEM.md) → PR Review Mode

---

## 🆕 Recent Updates (November 2025)

- 🌐 **WASM PWA First** - Native shells archived; the PWA + desktop agent are the supported surfaces
- 🔁 **Rustdoc Overhaul** - Upstream Rust/WASM docs are now modularized under `docs/rustdoc/`
- 🪙 **Economy Layer Integration** - Polygon contracts, CLI staking commands, and rewards workflows
- 🎮 **Gamified PR Review & Planning System** - Interactive game-based building management
