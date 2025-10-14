# ArxOS Vision Document

**Date:** October 13, 2025
**Author:** Joel Pate
**Purpose:** Core vision and philosophy for ArxOS development

---

## The Mission (Three Words)

**Building Version Control**

---

## What ArxOS Actually Is

**ArxOS is a version-controlled repository for building data.**

Not a CAD application. Not a CMMS. Not a BMS. Not a project management tool.

**It's infrastructure.** Like:
- Git = Code repository
- Docker Hub = Container repository
- npm = Package repository
- **ArxOS = Building repository**

Everything else (mobile apps, visualization, analytics, automation) is **built on top** of the repository, not **in** the repository.

---

## Core Philosophy

### 1. The Reductive Approach

ArxOS works at multiple levels of sophistication. Users start where they are:

**Level 0: The Spreadsheet Replacement**
- A list of rooms
- A list of equipment
- Basic queries: "Show me all equipment in Room 301"
- No spatial data, no floor plans
- Just addresses and records

**Level 1: Add Spatial When Needed**
- Scan QR codes with mobile app
- Save equipment locations manually
- Build spatial relationships incrementally
- Only for things that matter

**Level 2: Import the Full Model (If It Exists)**
- Import IFC file from architect
- Entire building model with spatial relationships
- But most buildings don't have this

**Key Insight:** Most real-world facility management is **Lego pieces** (modular, flexible, grows organically), not **puzzle pieces** (fixed, rigid, complete).

### 2. CLI-First Philosophy

**The CLI is the composability layer.**

Users build their own workflows:

```bash
# DIY CMMS
arx query /B1/*/HVAC/* --filter "last_service > 90days" \
  | while read equipment; do
      curl -X POST their-cmms.com/api/work-orders -d "$equipment"
    done

# Integration with existing tools
arx get /B1/2/IDF-2A/NETWORK/SW-01 --json \
  | jq '.manufacturer, .model, .serial' \
  | curl -X POST servicenow.com/api/assets -d @-

# Custom reporting
arx query /B1/*/ENERGY/* --format csv \
  | python analyze_energy.py \
  | mail -s "Monthly Energy Report" boss@school.edu
```

**ArxOS doesn't prescribe workflows. It provides tools.**

### 3. User Agnostic

**"I am really agnostic to how users want to use Arxos."**

Users can:
- Integrate with their existing CMMS/CAFM
- Build custom workflows with CLI
- Use ArxOS as-is for basic operations
- Script their own automation
- Export data to other tools

**ArxOS just provides the repository and query interface.**

### 4. Data Portability

No vendor lock-in:
- Import from any source (IFC, CSV, manual)
- Export to any format (JSON, CSV, IFC)
- Open API for integrations
- Scriptable CLI
- Users own their data

---

## Competitive Positioning

### ArxOS as "Cold Storage for Buildings"

**The Problem:**
- BIM 360: $1,000-10,000/year per building
- Procore: $500-2,000/year per building
- Revit Server: Expensive infrastructure + licenses
- Or data gets lost when projects end

**The ArxOS Solution:**
- Store IFC files, equipment databases, scan data
- Cost: ~$0.20-0.50/month per building
- Query without expensive CAD software
- Export when needed
- Own your data forever

**Positioning:** "Stop paying thousands per year to store building data in proprietary platforms. ArxOS stores building data for pennies. Query through CLI. Export to any format. Own your data forever."

### Cost Advantages

**Traditional Approach (Expensive):**
- Raw LiDAR: 200-500 MB per room
- Entire building: 20-100 GB
- Storage cost: $40-100/month for 20 buildings
- Requires GPU/heavy compute to view

**ArxOS Approach (Cheap):**
- Simplified/compressed geometry
- 50-200 KB per room (1000x smaller)
- Storage cost: $10-50/year for entire district
- Terminal-based viewing (no GPU needed)

**For 100-building organization:**
- Traditional BIM platform: $50,000-500,000/year
- ArxOS: $500-5,000/year
- **1000x cheaper**

### The Git Parallel

**Git's mission:** Version control for code

**Users built on top:**
- GitHub (collaboration)
- GitLab (DevOps)
- Bitbucket (enterprise)
- Countless CI/CD tools

**Git didn't try to be all of those. It just did version control well.**

---

**ArxOS mission:** Version control for buildings

**Users will build on top:**
- CMMS integrations
- Analytics dashboards
- Mobile apps
- Custom workflows
- IoT integrations

**ArxOS doesn't try to be all of those. It just does version control well.**

---

## Core Product Features

### The Repository Does:

1. **Store building entities**
   - Buildings, floors, rooms, equipment
   - Metadata, properties, relationships
   - Spatial data (when available)

2. **Universal addressing system**
   - Every component has a path: `/B1/3/301/HVAC/VAV-301`
   - Human-readable, hierarchical
   - Works for all building systems

3. **Version control**
   - Commits (what changed)
   - Branches (parallel changes)
   - History (track over time)
   - Diffs (compare versions)

4. **Query interface**
   - By path: `arx get /B1/3/*/HVAC/*`
   - By type: `arx query --type switch`
   - By location: `arx query --room 301`
   - By system: `arx query --system HVAC`

5. **Import/Export**
   - Import: IFC, CSV, JSON, manual entry
   - Export: JSON, CSV, IFC, custom formats
   - Bidirectional data flow

### The Repository Doesn't Do:

- ❌ CAD editing (export to CAD tools instead)
- ❌ Work order management (integrate with CMMS instead)
- ❌ Real-time BMS control (integrate with BAS instead)
- ❌ Project management (integrate with PM tools instead)
- ❌ Prescribe workflows (users script their own)

---

## Future Vision: ASCII Terminal Visualization

### The Idea

Convert LiDAR point clouds to ASCII art for terminal-based 3D visualization.

### Why This Matters

**Cost Optimization:**
- Process point cloud on-device (iPhone)
- Downsample to 5,000-10,000 key points
- Send 100 KB payload to server (vs 200 MB full scan)
- Store lightweight geometry forever
- Render in terminal (no GPU needed)

**Unique Differentiator:**
- SSH access to building data
- Low bandwidth visualization
- Works over crappy connections
- Scriptable/automatable
- No other building system has this

### Practical Implementation

```bash
# Scan room with iPhone LiDAR
$ arx scan import room-301.ply

# View in terminal
$ arx view 3d --room 301
[ASCII 3D point cloud]
[WASD to navigate, mouse to rotate]

# Simple floor plan
$ arx view floor --floor 2
┌─────────────────────────────────┐
│  201    202    IDF-2A    203   │
│  [AP]   [S]    [SW][PR]  [S]   │
└─────────────────────────────────┘
```

### Priority: Phase 4-5 (After Core Works)

This is a "nice-to-have" feature that demonstrates innovation, but core repository functionality comes first.

---

## What "Version 1.0" Means

**ArxOS v1.0 = When users can:**

1. ✅ Store building data (import IFC, CSV, or manual entry)
2. ✅ Query efficiently (`arx query`, `arx get`, path patterns)
3. ✅ Track changes (`arx commit`, `arx log`, `arx diff`)
4. ✅ Export data (`arx export --format json/csv`)
5. ✅ Script workflows (pipe CLI commands, use API)

**That's it. That's v1.0.**

Everything else is:
- Interface improvements
- Additional import formats
- Performance optimizations
- Documentation/examples
- Community integrations

---

## Target Users & Use Cases

### Use Case 1: School IT Tech (Primary User - Joel)

**Current State:**
- Manages IT equipment across 20+ school buildings
- Digs through PDFs and spreadsheets
- No single source of truth
- Changes aren't tracked

**With ArxOS:**
```bash
# Find equipment
arx get /B1/2/IDF-2A/NETWORK/SW-01

# List all switches in building
arx query /B1/*/NETWORK/SW-*

# Track changes
arx log /B1/2/IDF-2A/NETWORK/SW-01

# Import BAS data
arx bas import metasys_points.csv --building B1
```

### Use Case 2: Facility Manager

**Current State:**
- HVAC, electrical, plumbing spread across multiple systems
- No version control for building changes
- Hard to know what equipment exists where

**With ArxOS:**
```bash
# All HVAC equipment on floor 3
arx query /B1/3/*/HVAC/*

# Equipment due for maintenance
arx query --filter "last_service > 90days"

# Track building changes
arx log --since "2024-01-01"
```

### Use Case 3: Building Owner/Architect

**Current State:**
- IFC files lost after project ends
- Pay expensive fees to store in BIM platforms
- Can't query data without CAD software

**With ArxOS:**
```bash
# Archive project data
arx import building-design.ifc

# Query years later without CAD software
arx query /B1/*/ELEC/PANEL-*

# Export when needed
arx export B1 --format json
```

---

## Success Metrics

### Technical Success

- ✅ Compiles without errors
- ✅ 60%+ test coverage
- ✅ All CLI commands work with real data
- ✅ API covers core use cases
- ✅ Import/export works for common formats
- ✅ Query performance < 100ms for typical building

### Product Success

- ✅ Can manage a building without IFC file
- ✅ Can import IFC and query equipment
- ✅ Can track changes over time
- ✅ Can export data to other tools
- ✅ Can script custom workflows

### Business Success

- ✅ Joel uses it daily at work
- ✅ Coworkers find it useful
- ✅ Saves time vs current workflow
- ✅ Solves real problems
- ✅ Others want to use it

---

## Current State Assessment

**Overall Completion: ~70%**

### What Works ✅

- Core infrastructure (database, auth, domain models)
- BAS CSV import (fully functional, 100% test coverage)
- Git-like version control (branches, commits, PRs)
- Equipment CRUD and topology
- CLI commands (~86% functional)
- HTTP API core endpoints (~48 endpoints)
- IFC parsing and entity extraction logic
- Universal naming convention (path system)

### What Needs Work ⚠️

- Path-based queries (database ready, needs repository methods)
- Some CLI wiring (mostly done, minor gaps)
- Test coverage (~15%, needs improvement)
- Mobile app integration (40% done)

### What's Missing ❌

- Comprehensive testing
- Some API endpoints (optional for MVP)
- Documentation polish
- Real-world usage validation

---

## The Path Forward

### Immediate Priorities (Next 4-6 Weeks)

**Focus: Make the repository fully functional**

1. **Complete path-based queries** (3-4 hours)
   - Add `FindByPath()` to repositories
   - Wire CLI commands
   - Test with wildcard patterns

2. **Finish CLI wiring** (2-3 hours)
   - Any remaining placeholder commands
   - Error handling improvements
   - Help text polish

3. **Integration testing** (8-12 hours)
   - End-to-end workflows
   - Import → query → export
   - Version control workflows

4. **Real-world validation** (Ongoing)
   - Use at workplace
   - Document actual workflows
   - Fix bugs discovered in real use

### Deferred (Post-MVP)

- Mobile app polish
- ASCII 3D visualization
- Advanced analytics
- Workflow automation
- Multi-user collaboration features

---

## Key Decisions & Constraints

### Technical Decisions

- **Language:** Pure Go/Rust (no Python in core)
- **Database:** PostgreSQL + PostGIS (spatial support)
- **Architecture:** Clean Architecture (domain-driven)
- **API:** REST (simple, universal)
- **CLI:** Cobra (standard Go CLI framework)

### Design Constraints

- **Accuracy:** Visual reference quality, not engineering precision
- **Storage:** Optimize for cost (simplified geometry)
- **Interface:** CLI-first, GUI optional
- **Integration:** Open API, no lock-in
- **Complexity:** Start simple, add as needed

### Philosophical Constraints

- **User freedom:** Don't prescribe workflows
- **Data ownership:** Users own their data
- **Portability:** Import/export everything
- **Simplicity:** Do one thing well (version control)
- **Agnosticism:** Support multiple use cases

---

## The Competitive Moat

**It's not features. It's the data model + CLI.**

Once users:
- Write scripts using `arx` commands
- Build integrations on the API
- Store building data in ArxOS format
- Use paths as addressing system

**They're locked in.** Not by vendor lock-in, but by **ecosystem lock-in**.

Just like Git: You could switch to Mercurial, but why? Everything works with Git.

---

## Marketing & Positioning

### The Elevator Pitch

**"ArxOS is version control for buildings. Track what changed, when, and why. Query equipment by path. Import from any source. Export to any format. Build your own workflows on top."**

### Target Market Messages

**For IT Techs:**
> "Stop digging through PDFs. Every piece of equipment has an address. Query it like you query files."

**For Facility Managers:**
> "Track building changes like code changes. Know what changed, when, and why."

**For Building Owners:**
> "Your building data shouldn't be locked in expensive proprietary systems. Own it."

**For Architects:**
> "Don't lose project data when the project ends. Archive it in ArxOS for pennies."

### Pricing Strategy (Future)

**Free Tier:**
- Up to 5 buildings
- Core functionality
- CLI + API access

**Pro Tier ($10-50/month):**
- 20-100 buildings
- Priority support
- Advanced features

**Enterprise ($500+/month):**
- Unlimited buildings
- Custom integrations
- Dedicated support

**vs. Competitors:**
- BIM 360: $1,000-10,000/year per building
- Procore: $500-2,000/year per building
- **ArxOS: 95% cheaper**

---

## Lessons Learned

### What Joel Discovered

1. **ArxOS is simpler than originally thought**
   - It's a repository, not an operating system
   - Core product is focused and achievable
   - Complexity comes from applications built on top

2. **You don't need IFC to start**
   - Manual entry works fine
   - Build organically as you discover equipment
   - Import structured data when available

3. **CLI is the killer feature**
   - Enables user-created workflows
   - Scriptability = composability
   - Power users will love this

4. **Cost optimization is a strategy**
   - ASCII visualization isn't just cool, it's economical
   - Simplified geometry = 1000x cost reduction
   - "Good enough" beats "perfect but expensive"

5. **Mission clarity matters**
   - "Building Version Control" - three words
   - Everything else is secondary
   - Focus wins

---

## The Vision in One Paragraph

ArxOS is version-controlled storage for building data. Import IFC files, BAS exports, or add equipment manually. Every component gets a path. Query by location, type, or system. Track changes over time like Git. Export to any format. Build your own workflows with CLI and API. No vendor lock-in. Own your data. Start simple, add complexity as needed. It's infrastructure, not an application. Everything else is built on top.

---

## Next Steps

1. **Finish wiring** (the remaining 30%)
   - Complete path queries
   - Test end-to-end
   - Fix bugs

2. **Deploy to one building** (real validation)
   - Use at workplace
   - Document actual workflows
   - Gather feedback

3. **Iterate based on reality** (true product-market fit)
   - What actually gets used?
   - What's missing?
   - What's unnecessary?

4. **Then expand** (after core proves valuable)
   - Mobile app polish
   - ASCII visualization
   - Community features

---

**The hard part (architecture, data model, domain understanding) is done.**

**Now: Make it fully functional, deploy it, use it.**

**Mission: Building Version Control**

---

*This document represents the core vision for ArxOS as articulated on October 13, 2025. It should serve as the north star for all development decisions.*

