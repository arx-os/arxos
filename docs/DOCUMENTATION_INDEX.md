# ArxOS Documentation Index

**Last Updated:** November 2025  
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
- **[TODO_REMAINING.md](./development/TODO_REMAINING.md)** - Pending development tasks
- **[render/](./development/render/)** - Rendering system documentation
  - [2D_FLOOR_PLANS.md](./development/render/2D_FLOOR_PLANS.md) - 2D ASCII rendering
- **[codebase-reviews/](./development/codebase-reviews/)** - In-depth module reviews and architecture analysis
- **[improvement-summaries/](./development/improvement-summaries/)** - Summaries of completed improvements

### [Mobile](./mobile/)

iOS and Android development documentation.

- **[MOBILE_FFI_INTEGRATION.md](./mobile/MOBILE_FFI_INTEGRATION.md)** - Complete FFI guide
- **[MOBILE_GAME_INTEGRATION.md](./mobile/MOBILE_GAME_INTEGRATION.md)** - Game system mobile integration
- **[IOS_FFI_STATUS.md](./mobile/IOS_FFI_STATUS.md)** - Current iOS integration status
- **[ANDROID.md](./mobile/ANDROID.md)** - Android setup and build guide
- **[MOBILE_CI_CD.md](./mobile/MOBILE_CI_CD.md)** - GitHub Actions workflows
- **[MOBILE_SIGNUP_WORKFLOW.md](./mobile/MOBILE_SIGNUP_WORKFLOW.md)** - Auth system design

### [Augmented Reality](./ar/)

AR and LiDAR integration documentation.

- **[AR_SCAN_INTEGRATION.md](./ar/AR_SCAN_INTEGRATION.md)** - AR/ARKit and ARCore integration
- **[AR_TERMINAL_DESIGN.md](./ar/AR_TERMINAL_DESIGN.md)** - Hybrid AR+Terminal UI design
- **[AR_LOOP_ROADMAP.md](./ar/AR_LOOP_ROADMAP.md)** - Roadmap to close AR loop
- **[SCAN_DATA_TESTING.md](./ar/SCAN_DATA_TESTING.md)** - Scan data testing

### [Features](./features/)

Specific feature documentation.

- **[GAME_SYSTEM.md](./features/GAME_SYSTEM.md)** - Gamified PR review and planning system
- **[CONSTRAINTS.md](./features/CONSTRAINTS.md)** - Constraint validation system
- **[IFC_COMPATIBILITY.md](./features/IFC_COMPATIBILITY.md)** - IFC round-trip compatibility
- **[IFC_PROCESSING.md](./features/IFC_PROCESSING.md)** - IFC file import and conversion
- **[HARDWARE_INTEGRATION.md](./features/HARDWARE_INTEGRATION.md)** - IoT sensor integration
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

## 🔄 Migration & Updates

- **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - Upgrading between ArxOS versions
- **[CHANGELOG_NOVEMBER_2025.md](./CHANGELOG_NOVEMBER_2025.md)** - November 2025 updates (Game System)

---

## 📖 Documentation Archive

Historical and outdated documentation preserved in the [`archive/`](./archive/) directory:
- Previous implementations and plans
- Legacy mobile build guides
- Old architecture decisions
- Historical code reviews

---

## 🎯 Quick Reference

**New to ArxOS?** → Start with [User Guide](./core/USER_GUIDE.md)  
**Contributing?** → See [Developer Onboarding](./development/DEVELOPER_ONBOARDING.md)  
**Security?** → Review [Security Guide](./development/SECURITY.md)  
**Adding features?** → See [Architecture](./core/ARCHITECTURE.md)  
**Building mobile apps?** → See [Mobile FFI](./mobile/MOBILE_FFI_INTEGRATION.md)  
**Deploying at scale?** → See [Enterprise Deployment](./business/ENTERPRISE_DEPLOYMENT.md)  
**Need performance tips?** → See [Performance Guide](./development/PERFORMANCE_GUIDE.md)  
**Looking for API details?** → See [API Reference](./core/API_REFERENCE.md)  
**Gamified building management?** → See [Game System](./features/GAME_SYSTEM.md)  
**Reviewing contractor PRs?** → See [Game System](./features/GAME_SYSTEM.md) → PR Review Mode

---

## 🆕 Recent Updates (November 2025)

- ✨ **Gamified PR Review & Planning System** - Interactive game-based building management
- 📱 **Mobile Game Integration** - Mobile FFI functions for PR review and planning
- 📚 **Learning Mode** - Educational scenarios from historical PRs
- ✅ **IFC Round-Trip Compatibility** - Complete metadata preservation for game operations
- 🪙 **Economy Layer Integration** - Polygon contracts, CLI staking commands, and mobile FFI endpoints for ARXO rewards
