# ArxOS Development Phases

## Overview
ArxOS development follows a phased approach, starting with a simple PDF markup tool and evolving into a comprehensive building intelligence platform. Each phase delivers standalone value while building toward the complete vision.

## Phase 1: PDF Terminal Tool (MVP)
**Timeline: Months 1-2**  
**Goal: Make existing PDF floor plans interactive through terminal interface**  
**Status: Planning**

### Core Features
- [ ] PDF Import & Parsing
  - Extract text elements and coordinates
  - Identify room labels and equipment markers
  - Generate coordinate mapping for ASCII rendering

- [ ] ASCII Map Generation
  - Convert PDF layout to ASCII art
  - Preserve spatial relationships
  - Simple symbols for equipment types

- [ ] Terminal Navigation
  - Basic commands: `cd`, `ls`, `pwd`, `look`
  - Navigate between rooms/areas
  - View equipment in current location

- [ ] Markup Operations
  - `mark <item> --status <status>` - Mark equipment status
  - `annotate <item> "<note>"` - Add text notes
  - `tag <item> --type <type>` - Classify equipment
  - Status types: `normal`, `needs-repair`, `failed`

- [ ] PDF Export
  - Export ASCII map back to PDF with markup layer
  - Preserve original PDF as base layer
  - Add colored annotations for status
  - Include text notes as PDF comments

- [ ] Basic Version Control
  - Simple Git integration
  - Track who changed what and when
  - `commit` and `log` commands

### Technical Implementation
- **Language**: Go
- **PDF Library**: pdfcpu or UniDoc
- **ASCII Rendering**: Custom renderer
- **Storage**: Plain text files + Git
- **No database required**

### Example Workflow
```bash
# Import PDF floor plan
arx import floor2.pdf

# View ASCII rendering
arx map
Floor 2 - Electrical Layout
════════════════════════════
┌──────────┬──────────┬─────┐
│ Room 2A  │ Room 2B  │ Mech│
│  ● ● ●   │  ● ● ○   │  ⚡ │
└──────────┴──────────┴─────┘
  ● Normal  ○ Failed  ⚡ Panel

# Navigate and mark issues
arx cd room_2B
arx mark outlet_3 --status failed
arx annotate outlet_3 "Ground fault detected 1/15"

# Export updated PDF
arx export floor2_marked.pdf

# Save changes
arx commit -m "Marked failed outlet in room 2B"
```

### Success Criteria
- Import and render a PDF floor plan in terminal
- Mark at least 3 equipment status changes
- Export PDF with visible markup
- Complete workflow in under 5 minutes

### Dependencies & Risks
- **Dependencies**: PDF parsing library for Go
- **Risks**: 
  - PDF complexity and format variations
  - Text extraction accuracy
  - Coordinate system mapping

### Adjustments & Notes
*Space for documenting changes as development progresses*

---

## Phase 2: Building Intelligence Layer
**Timeline: Months 3-5**  
**Goal: Add structured data, queries, and system connections**  
**Status: Future**

### Planned Features
- [ ] Object Model
  - Equipment types and properties
  - Hierarchical building structure
  - System connections (electrical, plumbing, HVAC)

- [ ] SQLite Database
  - Index all objects for fast queries
  - Spatial indexing for proximity searches
  - Full-text search on annotations

- [ ] Query Interface
  - SQL-like SELECT statements
  - Filter by type, status, location
  - Aggregation queries for reporting

- [ ] Connection Tracing
  - `trace <object> upstream/downstream`
  - Circuit mapping
  - Dependency tracking

- [ ] IFC Import Support
  - Parse IFC building models
  - Extract equipment and spaces
  - Maintain relationship to PDF plans

- [ ] Sync Daemon
  - Watch folder for PDF/IFC updates
  - Auto-import changes
  - Track modifications

- [ ] Branch Workflows
  - Create branches for change sets
  - Diff and merge functionality
  - Pull request workflow for reviews

### Technical Additions
- **Database**: SQLite with JSON support
- **IFC Parser**: IfcOpenShell Go bindings or custom
- **File Watching**: fsnotify
- **Storage**: JSON files + SQLite index + Git

### Example New Commands
```bash
# Query for issues
arx query "SELECT * FROM objects WHERE status = 'failed'"

# Trace electrical path
arx trace outlet_2B upstream
  → circuit_15
    → panel_2B
      → main_panel

# Create branch for work
arx branch maintenance/electrical-repairs
arx update outlet_2B --status normal
arx commit -m "Repaired outlet 2B"
arx push
```

### Success Criteria
- Import IFC file and correlate with PDF
- Execute complex queries across building
- Trace connections through systems
- Manage branched workflows

### Dependencies & Risks
- **Dependencies**: IFC parsing library, SQLite
- **Risks**:
  - IFC format complexity
  - Performance with large buildings
  - Sync conflict resolution

### Adjustments & Notes
*Space for documenting changes as development progresses*

#### Potential Tools to Evaluate
- **jq integration**: Since we're using JSON for object storage, consider supporting jq-style queries as an alternative or supplement to SQL. Could allow: `arx export --json | jq '.objects[] | select(.status=="failed")'` or native support like `arx query --jq '.objects[] | select(.type=="outlet")'`. Evaluate during Phase 2 implementation to see if it's simpler than SQL parsing and whether facilities teams would benefit from standard Unix tool compatibility.

---

## Phase 3: Field Operations Platform
**Timeline: Months 6-8**  
**Goal: Mobile AR interface and real-time collaboration**  
**Status: Future**

### Planned Features
- [ ] Mobile AR Application
  - iOS/Android native apps
  - Camera overlay with equipment identification
  - Offline mode with sync

- [ ] Real-time Collaboration
  - Multiple users editing simultaneously
  - Conflict resolution
  - Live status updates

- [ ] Advanced Visualization
  - 3D ASCII isometric views
  - Multi-floor navigation
  - System overlay views (electrical, plumbing, etc.)

- [ ] Spatial Features
  - Proximity searches
  - Path finding
  - Area calculations

- [ ] Media Attachments
  - Photos of equipment
  - Voice notes
  - Video documentation

- [ ] Integration APIs
  - REST API for external systems
  - Webhook notifications
  - CMMS/EAM integration

### Technical Additions
- **Mobile**: Swift/ARKit, Kotlin/ARCore
- **Backend API**: Go REST server
- **Real-time**: WebSockets or SSE
- **Media Storage**: Local filesystem with Git LFS

### Adjustments & Notes
*Space for documenting changes as development progresses*

---

## Phase 4: Enterprise Features
**Timeline: Months 9-12**  
**Goal: Enterprise scalability and integration**  
**Status: Concept**

### Potential Features
- [ ] Multi-building Portfolio Support
- [ ] Advanced BIM/CAD Integration (Revit, AutoCAD)
- [ ] IoT Sensor Integration
- [ ] Predictive Maintenance ML
- [ ] Compliance Reporting
- [ ] SSO/LDAP Authentication
- [ ] Cloud Deployment Options

### Adjustments & Notes
*Space for documenting changes as development progresses*

---

## Development Principles

### For All Phases
1. **User-First**: Each phase must deliver immediate value
2. **Simple Core**: Keep the core tool simple and fast
3. **Offline-First**: Always work without internet
4. **Git-Native**: Version control built-in, not bolted on
5. **Terminal-Centric**: CLI is the primary interface

### Phase Gate Criteria
Before moving to the next phase:
1. Current phase features are stable
2. Real users have tested and provided feedback
3. Performance meets requirements
4. Documentation is complete
5. Tests cover critical paths

---

## Tracking Development

### Phase 1 Milestones
- [ ] Week 1-2: PDF parsing and ASCII rendering prototype
- [ ] Week 3-4: Basic terminal navigation working
- [ ] Week 5-6: Markup and annotation features
- [ ] Week 7-8: PDF export with markups
- [ ] Week 9-10: Git integration and version control
- [ ] Week 11-12: Testing, documentation, and polish

### Metrics to Track
- PDF import success rate
- Time to complete common workflows
- User feedback scores
- Number of equipment items tracked
- Export quality satisfaction

### Known Issues & Blockers
*Document issues as they arise*

### Design Decisions Log
*Document key decisions and rationale*

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| | | | |

### User Feedback
*Capture feedback from testing*

### Technical Debt
*Track shortcuts taken for later resolution*

---

## Next Actions

### Immediate (Phase 1 Start)
1. Research Go PDF libraries (pdfcpu vs UniDoc vs others)
2. Create prototype PDF parser
3. Design ASCII rendering algorithm
4. Implement basic terminal navigation
5. Test with real floor plan PDFs

### Questions to Resolve
- What PDF library best handles floor plans?
- How to handle different PDF coordinate systems?
- What ASCII symbols for different equipment types?
- How to preserve PDF layers on export?
- What metadata to track in Git commits?

---

## Notes

This document is living and should be updated regularly as development progresses. Each phase can be adjusted based on user feedback and technical discoveries.

Key files to maintain:
- `PHASES.md` - This document
- `ARCHITECTURE.md` - Overall system design
- `CHANGELOG.md` - Version history
- `TODO.md` - Current sprint tasks