# Arxos Vision

**Last Updated:** October 15, 2025  
**Author:** Joel Pate  
**Purpose:** Core vision and philosophy for Arxos development

---

## The Mission (Three Words)

**Building Version Control**

---

## What Arxos Actually Is

**Arxos is a version-controlled repository for building data.**

Not a CAD application. Not a CMMS. Not a BMS. Not a project management tool.

**It's infrastructure.** Like:
- Git = Code repository
- Docker Hub = Container repository  
- npm = Package repository
- **Arxos = Building repository**

```
Arxos = Git + GitHub + PostGIS for Buildings

Git Component       →  Arxos Equivalent
--------------------------------------------
Repository          →  Building repository
Branch              →  Renovation/project branch
Commit              →  Building changes commit
Pull Request        →  Work order/contractor project
Issue               →  Equipment problem/maintenance task
Diff                →  Building changes diff
Merge               →  Approve and apply changes
```

**Plus:**
- Universal naming convention (`/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT`)
- BAS integration (import control points from Metasys, Desigo, etc.)
- Spatial intelligence (PostGIS 3D coordinates)
- Multi-interface (CLI + IFC + Mobile from one system)

Everything else (mobile apps, visualization, analytics, automation) is **built on top** of the repository, not **in** the repository.

---

## The Three Layers (Closing the Circle)

Arxos provides **three complementary interfaces** that close the loop on a building's entire lifecycle:

### 1. CLI + ASCII (Terminal Layer)
**For:** Techs, admins, scripters who live in terminals
- The "Git" experience - fast, scriptable, composable
- ASCII art for quick visualization
- Works everywhere (SSH, local, remote)
- **Status:** ~90% functional

### 2. IFC Integration (CAD/BIM Layer)
**For:** Architects, engineers, BIM managers
- Bidirectional bridge to professional design tools
- Import IFC files → populate Arxos
- Export Arxos data → IFC for architects/engineers
- **Status:** Import parsing works, entity extraction ready

### 3. React Native + AR (Field Layer)
**For:** Field techs, facility staff actually IN the building
- Scan QR codes, capture spatial anchors, take photos
- See equipment overlays in AR
- Update/create records on the spot
- **Status:** Structure complete (~40%), needs wiring

**Result:** Architect exports IFC → IT tech manages via CLI → Field tech updates via mobile → Everyone sees the same data.

---

## Core Philosophy

### 1. The Reductive Approach

Arxos works at multiple levels of sophistication. Users start where they are:

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

**Arxos doesn't prescribe workflows. It provides tools.**

### 3. User Agnostic

**"I am really agnostic to how users want to use Arxos."**

Users can:
- Integrate with their existing CMMS/CAFM
- Build custom workflows with CLI
- Use Arxos as-is for basic operations
- Script their own automation
- Export data to other tools

**Arxos just provides the repository and query interface.**

### 4. Data Portability

No vendor lock-in:
- Import from any source (IFC, CSV, manual)
- Export to any format (JSON, CSV, IFC)
- Open API for integrations
- Scriptable CLI
- Users own their data

### 5. Works Everywhere

**"Regardless of age, state, existing software"**

Arxos integrates into all buildings:
- 100-year-old buildings with no digital records ✅
- Modern facilities with full BIM models ✅
- Mixed environments with some data ✅
- Incremental data capture (start small, grow organically) ✅

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

## Competitive Positioning

### Arxos as "Cold Storage for Buildings"

**The Problem:**
- BIM 360: $1,000-10,000/year per building
- Procore: $500-2,000/year per building
- Revit Server: Expensive infrastructure + licenses
- Or data gets lost when projects end

**The Arxos Solution:**
- Store IFC files, equipment databases, scan data
- Cost: ~$0.20-0.50/month per building
- Query without expensive CAD software
- Export when needed
- Own your data forever

**Positioning:** "Stop paying thousands per year to store building data in proprietary platforms. Arxos stores building data for pennies. Query through CLI. Export to any format. Own your data forever."

### Cost Advantages

**Traditional Approach (Expensive):**
- Raw LiDAR: 200-500 MB per room
- Entire building: 20-100 GB
- Storage cost: $40-100/month for 20 buildings
- Requires GPU/heavy compute to view

**Arxos Approach (Cheap):**
- Simplified/compressed geometry
- 50-200 KB per room (1000x smaller)
- Storage cost: $10-50/year for entire district
- Terminal-based viewing (no GPU needed)

**For 100-building organization:**
- Traditional BIM platform: $50,000-500,000/year
- Arxos: $500-5,000/year
- **95-99% cheaper**

### The Git Parallel

**Git's mission:** Version control for code

**Users built on top:**
- GitHub (collaboration)
- GitLab (DevOps)
- Bitbucket (enterprise)
- Countless CI/CD tools

**Git didn't try to be all of those. It just did version control well.**

---

**Arxos mission:** Version control for buildings

**Users will build on top:**
- CMMS integrations
- Analytics dashboards
- Mobile apps
- Custom workflows
- IoT integrations

**Arxos doesn't try to be all of those. It just does version control well.**

---

## Target Users & Use Cases

### Use Case 1: School IT Tech (Primary User - Joel)

**Current State:**
- Manages IT equipment across 20+ school buildings
- Digs through PDFs and spreadsheets
- No single source of truth
- Changes aren't tracked

**With Arxos:**
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

**With Arxos:**
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

**With Arxos:**
```bash
# Archive project data
arx import building-design.ifc

# Query years later without CAD software
arx query /B1/*/ELEC/PANEL-*

# Export when needed
arx export B1 --format json
```

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

**Priority:** Phase 4-5 (After Core Works)

This is a "nice-to-have" feature that demonstrates innovation, but core repository functionality comes first.

---

## What "Version 1.0" Means

**Arxos v1.0 = When users can:**

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

## The Competitive Moat

**It's not features. It's the data model + CLI.**

Once users:
- Write scripts using `arx` commands
- Build integrations on the API
- Store building data in Arxos format
- Use paths as addressing system

**They're locked in.** Not by vendor lock-in, but by **ecosystem lock-in**.

Just like Git: You could switch to Mercurial, but why? Everything works with Git.

---

## Marketing & Positioning

### The Elevator Pitch

**"Arxos is version control for buildings. Track what changed, when, and why. Query equipment by path. Import from any source. Export to any format. Build your own workflows on top."**

### Target Market Messages

**For IT Techs:**
> "Stop digging through PDFs. Every piece of equipment has an address. Query it like you query files."

**For Facility Managers:**
> "Track building changes like code changes. Know what changed, when, and why."

**For Building Owners:**
> "Your building data shouldn't be locked in expensive proprietary systems. Own it."

**For Architects:**
> "Don't lose project data when the project ends. Archive it in Arxos for pennies."

### Pricing Strategy (Future)

**Free Tier:**
- Up to 5 buildings
- Core functionality
- CLI + API access
- Self-hosted

**Pro Tier ($10-50/month):**
- 20-100 buildings
- Cloud sync
- Mobile app
- Priority support

**Enterprise ($500+/month):**
- Unlimited buildings
- Custom integrations
- Dedicated support
- SLA guarantees

**vs. Competitors:**
- BIM 360: $1,000-10,000/year per building
- Procore: $500-2,000/year per building
- **Arxos: 95% cheaper**

---

## Strategic Considerations

### Primary Customer Decision

**Who to build for first?**

**Option A: IT Techs (Recommended)**
- You are the customer → immediate validation
- Clear pain points you live daily
- Wedge: IT asset management → expand to other systems

**Option B: Facility Managers**
- Larger market, budget authority
- Needs CMMS features
- Slower to reach, longer sales cycles

**Option C: Building Owners/Architects**
- High willingness to pay
- BIM archive use case
- Episodic need (only during/after construction)

**Option D: Multi-Sided (All)**
- Maximum market
- Risk: diffused focus

### Core Value Proposition

**What's the #1 hook?**

1. **"Git for Buildings"** - Version control (unique, defensible)
2. **"Universal Naming"** - Every equipment gets an address (scriptability)
3. **"BIM Cold Storage"** - 1000x cheaper storage (cost advantage)
4. **"BAS Integration"** - Auto-import from any BAS (solves real pain)
5. **"Open Platform"** - Universal repository (ecosystem play)

**Recommendation:** Lead with universal naming + BAS integration. Both are unique and solve immediate pain.

---

## Success Metrics

### Technical Success

- ✅ Compiles without errors
- ⚠️ 15% test coverage (target: 60%+)
- ✅ All CLI commands work with real data
- ✅ API covers core use cases
- ⚠️ Import/export works (IFC pending service update)
- ⚠️ Query performance (untested at scale)

### Product Success

- ⚠️ Can manage building without IFC file (yes, manually)
- ⚠️ Can import IFC and query equipment (pending)
- ✅ Can track changes over time
- ✅ Can export data to other tools
- ✅ Can script custom workflows

### Business Success (To Be Validated)

- ⏳ Joel uses it daily at work
- ⏳ Coworkers find it useful
- ⏳ Saves time vs current workflow
- ⏳ Solves real problems
- ⏳ Others want to use it

---

## Key Decisions & Constraints

### Technical Decisions

- **Language:** Pure Go (no Python in core, except IFC service)
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

## Lessons Learned

### What Joel Discovered

1. **Arxos is simpler than originally thought**
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

Arxos is version-controlled storage for building data. Import IFC files, BAS exports, or add equipment manually. Every component gets a path. Query by location, type, or system. Track changes over time like Git. Export to any format. Build your own workflows with CLI and API. No vendor lock-in. Own your data. Start simple, add complexity as needed. It's infrastructure, not an application. Everything else is built on top.

---

## Next Steps

### Immediate (Next 4-6 Weeks)

1. **Complete path-based queries** (8-12 hours)
   - Add `FindByPath()` to repositories
   - Wire CLI commands
   - Test with wildcard patterns

2. **IFC service enhancement** (6-8 hours Python)
   - Return detailed entities (not just counts)
   - Enable full building model creation

3. **Integration testing** (20-30 hours)
   - End-to-end workflows
   - Import → query → export
   - Version control workflows

4. **Real-world validation** (Ongoing)
   - Deploy at workplace
   - Document actual workflows
   - Gather feedback from daily use

### Deferred (Post-MVP)

- Mobile app polish (30-40 hours)
- ASCII 3D visualization (future)
- Advanced analytics (future)
- Workflow automation (future)
- Multi-user collaboration features (WebSockets)

---

## The Opportunity

**If this works:**
- Category-creating product (Git for Buildings)
- Massive cost advantage (95% cheaper)
- Solves real problems (validated by Joel's experience)
- Defensible (network effects, ecosystem lock-in)
- Scalable (software + hardware ecosystem)

**If it doesn't:**
- Architectural skills proven
- Technical capability demonstrated
- Consulting credentials established
- Asset for acquisition/licensing
- Learning experience

**Either way, the work has value.**

---

**The hard part (architecture, data model, domain understanding) is done.**

**Now: Make it fully functional, deploy it, use it, validate it.**

**Mission: Building Version Control**

---

## Historical Documents

This vision document consolidates and supersedes:
- [ARXOS_VISION.md](docs/archive/arxos-vision-oct-2025.md) - Original vision document
- [VISION_DISCUSSION_PREP.md](docs/archive/vision-discussion-prep-oct-2025.md) - Strategic planning document

See [Archive](docs/archive/) for historical versions and development notes.

---

*This document represents the core vision for Arxos as of October 15, 2025. It serves as the north star for all development decisions.*

