# Arxos Documentation Index

*Last Updated: October 15, 2025*

## 🎯 Start Here - Essential Documents

**New to Arxos? Read these first:**
1. **[README.md](../README.md)** - What is Arxos?
2. **[VISION.md](../VISION.md)** - Project vision and philosophy
3. **[QUICKSTART.md](../QUICKSTART.md)** - Get running in 15 minutes
4. **[STATUS.md](STATUS.md)** - Current implementation status (~75% complete)

## 📚 Quick Navigation

### Getting Started
- [Main README](../README.md) - Project overview
- [Vision](../VISION.md) - Core philosophy and mission
- [Status](STATUS.md) - What works vs what needs work
- [Quickstart Guide](../QUICKSTART.md) - Setup in 15 minutes
- [Development Guide](DEVELOPMENT.md) - Comprehensive developer guide

### User Guides
- [Naming Convention](guides/naming-convention.md) - Universal equipment paths
- [Database Setup](guides/database-setup.md) - PostgreSQL/PostGIS setup
- [Database Migrations](guides/migrations.md) - Running and creating migrations
- [Postgres Reference](guides/postgres-reference.md) - PostgreSQL command reference

### Architecture
- [Service Architecture](architecture/SERVICE_ARCHITECTURE.md) - Core service design
- [Directory Structure](architecture/DIRECTORY_STRUCTURE.md) - Project organization
- [Unified Cache Architecture](architecture/UNIFIED_CACHE_ARCHITECTURE.md) - L1/L2/L3 caching
- [Unified Space Architecture](architecture/UNIFIED_SPACE_ARCHITECTURE.md) - Domain-agnostic spatial model
- [Offline Sync Architecture](OFFLINE_SYNC_ARCHITECTURE.md) - Conflict resolution & sync
- [CADTUI Visual Context](architecture/CADTUI_VISUAL_CONTEXT.md) - Terminal UI design
- [Coding Standards](architecture/CODING_STANDARDS.md) - Code style and conventions

### Integration Guides
- [BAS Integration](integration/BAS_INTEGRATION.md) - Building Automation Systems
- [IFC Integration](integration/IFCOPENSHELL_INTEGRATION.md) - IfcOpenShell service
- [CLI Integration](integration/CLI_INTEGRATION.md) - Command-line interface
- [Integration Flow](integration/INTEGRATION_FLOW.md) - System interconnections
- [CADTUI Workflow](integration/CADTUI_WORKFLOW_INTEGRATION.md) - TUI user flows
- [Meraki AR Navigation](integration/MERAKI_AR_NAVIGATION.md) - Augmented reality

### API Documentation
- [API Documentation](api/API_DOCUMENTATION.md) - REST API endpoints
- [OpenAPI Specifications](../api/openapi/) - Swagger/OpenAPI specs

### Testing
- [Integration Test Guide](testing/INTEGRATION_TEST_GUIDE.md) - E2E testing
- [TUI Data Integration](testing/TUI_DATA_INTEGRATION.md) - TUI test data
- [Use Case Test Progress](testing/USECASE_TEST_PROGRESS.md) - Test coverage

### Deployment
- [Deployment Guide](deployment/DEPLOYMENT_GUIDE.md) - Production deployment
- [Docker Guide](docker/README.md) - Container orchestration

### Automation
- [Intelligent Automation](automation/INTELLIGENT_AUTOMATION.md) - AI-driven workflows
- [Automation Examples](automation/AUTOMATION_EXAMPLE.md) - Practical examples

### Implementation Notes
- [Implementation Progress](implementation/IMPLEMENTATION_PROGRESS_SUMMARY.md) - **Updated: Realistic 60-65% assessment**
- **Historical Phase Docs Moved to Archive** (claimed "complete" when features had placeholders)

### Architecture Decisions
- [006: TUI Data Integration](architecture/decisions/006-tui-data-integration.md)
- [007: Version Control System](architecture/decisions/007-version-control-system.md)

## 📦 Archive

Historical session summaries and completed work are in [docs/archive/](archive/README.md).

## 🗂️ Directory Structure

```
docs/
├── DOCUMENTATION_INDEX.md          ← You are here
├── STATUS.md                       Current project status
├── DEVELOPMENT.md                  Comprehensive dev guide
├── OFFLINE_SYNC_ARCHITECTURE.md    Offline sync design
│
├── guides/                         ⭐ User Guides (NEW)
│   ├── naming-convention.md        Universal equipment paths
│   ├── database-setup.md           PostgreSQL/PostGIS setup
│   ├── migrations.md               Database migrations
│   └── postgres-reference.md       PostgreSQL command reference
│
├── api/                            API documentation
│   └── API_DOCUMENTATION.md
│
├── architecture/                   Core architecture
│   ├── SERVICE_ARCHITECTURE.md
│   ├── DIRECTORY_STRUCTURE.md
│   ├── UNIFIED_CACHE_ARCHITECTURE.md
│   ├── UNIFIED_SPACE_ARCHITECTURE.md
│   ├── CADTUI_VISUAL_CONTEXT.md
│   ├── CODING_STANDARDS.md
│   └── decisions/
│       ├── 006-tui-data-integration.md
│       └── 007-version-control-system.md
│
├── automation/                     Automation guides
│   ├── INTELLIGENT_AUTOMATION.md
│   └── AUTOMATION_EXAMPLE.md
│
├── deployment/                     Deployment
│   └── DEPLOYMENT_GUIDE.md
│
├── docker/                         Container docs
│   └── README.md
│
├── implementation/                 Implementation notes
│   └── IMPLEMENTATION_PROGRESS_SUMMARY.md
│
├── integration/                    Integration guides
│   ├── BAS_INTEGRATION.md
│   ├── CADTUI_WORKFLOW_INTEGRATION.md
│   ├── CLI_INTEGRATION.md
│   ├── IFCOPENSHELL_INTEGRATION.md
│   ├── INTEGRATION_FLOW.md
│   ├── MERAKI_AR_NAVIGATION.md
│   └── README.md
│
├── testing/                        Testing guides
│   ├── INTEGRATION_TEST_GUIDE.md
│   ├── TUI_DATA_INTEGRATION.md
│   └── USECASE_TEST_PROGRESS.md
│
└── archive/                        ⭐ Historical documents (67+ files)
    ├── README.md                   Categorized index
    └── [Superseded docs with dates]
```

## 🆕 Latest Updates

**October 15, 2025 - Documentation Consolidation:**
- ✅ **Consolidated 113 docs** into organized structure
- ✅ **Created [STATUS.md](STATUS.md)** - Single source of truth for project status
- ✅ **Created [VISION.md](../VISION.md)** - Unified vision document
- ✅ **Created [guides/](guides/)** directory with 4 comprehensive guides
- ✅ **Archived 20+ superseded docs** with dated filenames
- ✅ **Updated navigation** - Clear paths to all information
- ✅ **Preserved history** - All original content in archive

**October 12, 2025 - Documentation Refactor:**
- ✅ Created honest project status assessment (60-70% → 75% complete)
- ✅ Implemented universal naming convention
- ✅ Added 17 new HTTP API endpoints (BAS, PR, Issues)
- ✅ Wired BAS CLI commands to real data

**Earlier (Historical):**
- ✅ Implemented equipment topology system with graph relationships
- ✅ Created comprehensive database schema (107 tables, 33 migrations)
- ✅ Built Git-like version control for buildings

## 🔍 Finding Information

- **New to Arxos?** Start with [README](../README.md) → [VISION](../VISION.md) → [QUICKSTART](../QUICKSTART.md)
- **Want to develop?** See [DEVELOPMENT.md](DEVELOPMENT.md) for comprehensive developer guide
- **Checking feature status?** See [STATUS.md](STATUS.md) for what works vs what needs work
- **Setting up dev environment?** See [Database Setup](guides/database-setup.md)
- **Understanding the architecture?** Read [Service Architecture](architecture/SERVICE_ARCHITECTURE.md)
- **Learning naming convention?** See [Naming Convention](guides/naming-convention.md)
- **Integrating a system?** Check [integration/](integration/)
- **Looking for API docs?** See [API Documentation](api/API_DOCUMENTATION.md)
- **Need historical context?** Browse [archive/](archive/)

## 📝 Contributing to Documentation

When adding documentation:

1. **Active Guides** → `/docs/` (operational, frequently referenced)
2. **Architecture** → `/docs/architecture/` (design decisions, patterns)
3. **Integration** → `/docs/integration/` (how systems connect)
4. **Session Summaries** → `/docs/archive/` (historical work logs)
5. **User-facing** → Project root (README, QUICKSTART)

## 🔗 External Resources

- [IfcOpenShell Documentation](http://ifcopenshell.org/)
- [PostGIS Manual](https://postgis.net/documentation/)
- [Bubbletea TUI Framework](https://github.com/charmbracelet/bubbletea)
- [React Native Docs](https://reactnative.dev/)

---

*For questions or documentation improvements, see [CONTRIBUTING](../CONTRIBUTING.md)*

