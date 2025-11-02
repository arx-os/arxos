# Building Documentation Generation - Concept Exploration

## The Core Idea

Just like `rustdoc` generates HTML documentation from Rust code, **ArxOS could generate HTML documentation from building data**.

**Concept:** `arx doc --building "Main Building"` generates a beautiful, navigable HTML website documenting the building.

---

## User Experience Vision

### Basic Usage

```bash
# Generate documentation for a building
arx doc --building "Main Building"

# Output: Building documentation in HTML format
# Location: ./docs/main-building/index.html
```

**Result:** User opens `index.html` and sees:
- Building overview page
- Interactive floor plans
- Equipment inventory with search
- Room layouts
- Equipment relationships
- Change history (Git integration)
- Interactive 3D visualization (embedded)

---

## What Would Be Generated?

### 1. Building Overview Page (`index.html`)

**Content:**
- Building name, ID, metadata
- Summary statistics:
  - Total floors
  - Total rooms
  - Total equipment
  - Equipment by type (HVAC: 45, Electrical: 32, etc.)
- Last updated timestamp
- Git commit history (latest 5 commits)
- Quick navigation to floors/rooms

**Design:**
- Clean, modern HTML/CSS
- Responsive (works on mobile)
- Search bar at top
- Navigation sidebar

---

### 2. Floor Plans (`floors/floor-2.html`)

**Content:**
- Floor number and name
- Wing layout diagram
- Room listing with thumbnails
- Equipment count per room
- Links to detailed room pages

**Visual:**
- ASCII/HTML floor plan diagram
- Or SVG/Canvas-based visualization
- Clickable rooms (link to room detail)

---

### 3. Room Detail Pages (`rooms/room-201.html`)

**Content:**
- Room name, type, ID
- Room dimensions and position
- Equipment list with:
  - Equipment name and type
  - Status indicators (Active/Maintenance/etc.)
  - Position coordinates
  - Properties/metadata
- Room properties
- Related rooms (adjacent, above, below)
- Change history for this room

**Visual:**
- 3D room layout diagram
- Equipment positions visualized
- Status color-coding

---

### 4. Equipment Inventory (`equipment/index.html`)

**Content:**
- Searchable/filterable equipment list
- Filters by:
  - Equipment type
  - Status
  - Floor
  - Room
- Equipment detail pages (`equipment/vav-301.html`)
- Equipment relationships (connections, dependencies)

---

### 5. Equipment Detail Pages (`equipment/vav-301.html`)

**Content:**
- Equipment name, ID, type
- Status with visual indicator
- Position in building (floor, room, coordinates)
- Properties/metadata
- Maintenance history
- Sensor data (if available)
- Related equipment
- Change history

---

### 6. Search Interface

**Features:**
- Full-text search across all building data
- Filter by type, status, floor, room
- Search results with previews
- Direct links to detail pages

---

### 7. Interactive Visualizations

**Embedded:**
- 3D building viewer (using same rendering engine)
- Interactive floor plans
- Equipment network diagrams
- Status dashboards

---

## Command Interface

### Basic Command

```bash
# Generate documentation for a building
arx doc --building "Main Building"

# Output to specific directory
arx doc --building "Main Building" --output ./building-docs

# Generate for all buildings
arx doc --all

# Generate with specific format/theme
arx doc --building "Main Building" --theme dark
arx doc --building "Main Building" --format minimal
```

### Advanced Options

```bash
# Include Git history
arx doc --building "Main Building" --include-history

# Include sensor data
arx doc --building "Main Building" --include-sensors

# Include AR scan data
arx doc --building "Main Building" --include-ar-scans

# Embed interactive visualizations
arx doc --building "Main Building" --interactive

# Generate PDF version
arx doc --building "Main Building" --pdf

# Serve locally (like `cargo doc --open`)
arx doc --building "Main Building" --serve
```

---

## Technical Implementation

### Architecture

```
arx doc command
    ↓
Load building data (YAML/Git)
    ↓
Transform to documentation model
    ↓
Generate HTML templates
    ↓
Write to output directory
    ↓
Optional: Start local server
```

### Components Needed

1. **Documentation Generator** (`src/docs/generator.rs`)
   - Reads building data
   - Transforms to documentation structure
   - Generates HTML files

2. **Template System** (`templates/`)
   - HTML templates (mustache/handlebars-like)
   - CSS stylesheets
   - JavaScript for interactivity

3. **Asset Generation** (`src/docs/assets.rs`)
   - Generates floor plan diagrams
   - Creates equipment network graphs
   - Generates status indicators

4. **Static Server** (`src/docs/server.rs`)
   - Optional local server (like `cargo doc --open`)
   - Serves generated HTML files

### Template Structure

```
templates/
├── building.html          # Building overview
├── floor.html             # Floor detail page
├── room.html              # Room detail page
├── equipment.html         # Equipment detail page
├── equipment-list.html    # Equipment inventory
├── search.html            # Search interface
├── styles.css             # Styling
└── scripts.js             # Interactivity
```

### Data Model for Docs

```rust
pub struct BuildingDocumentation {
    pub building: Building,
    pub floors: Vec<FloorDoc>,
    pub rooms: Vec<RoomDoc>,
    pub equipment: Vec<EquipmentDoc>,
    pub metadata: DocumentationMetadata,
}

pub struct FloorDoc {
    pub floor: Floor,
    pub rooms: Vec<RoomDoc>,
    pub floor_plan: FloorPlan,
}

pub struct RoomDoc {
    pub room: Room,
    pub equipment: Vec<EquipmentDoc>,
    pub room_layout: RoomLayout,
    pub related_rooms: Vec<String>,
}

pub struct EquipmentDoc {
    pub equipment: Equipment,
    pub location_path: String,  // "Floor 2 / Wing A / Room 201"
    pub status_indicator: StatusIndicator,
    pub related_equipment: Vec<String>,
}
```

---

## Use Cases

### 1. Facility Management

**Scenario:** Facility manager needs to share building information with contractors

```bash
# Generate comprehensive building docs
arx doc --building "Main Building" --include-history --output ./share-docs

# Share the folder
# Contractors open index.html and see everything
```

**Benefits:**
- Self-contained HTML (no server needed)
- Works offline
- Professional presentation
- Searchable and navigable

---

### 2. Maintenance Reports

**Scenario:** Generate documentation showing only equipment needing maintenance

```bash
# Filter documentation by status
arx doc --building "Main Building" --filter-status "Maintenance" --output ./maintenance-report
```

**Result:** HTML page showing only equipment in maintenance, with locations and details.

---

### 3. Building Handoff

**Scenario:** Hand off building documentation to new facility manager

```bash
# Generate complete documentation with history
arx doc --building "Main Building" --include-history --include-sensors --output ./handoff-docs
```

**Result:** Complete building documentation package in HTML format.

---

### 4. Client Presentations

**Scenario:** Present building status to stakeholders

```bash
# Generate presentation-ready docs
arx doc --building "Main Building" --theme professional --interactive --output ./presentation
```

**Result:** Beautiful, interactive HTML presentation.

---

### 5. Compliance Documentation

**Scenario:** Generate documentation for regulatory compliance

```bash
# Generate with all details
arx doc --building "Main Building" --include-history --include-sensors --format detailed --output ./compliance-docs
```

**Result:** Comprehensive documentation package.

---

## Design Considerations

### 1. Self-Contained

**Principle:** Generated HTML should work without a server
- All CSS/JS embedded or in same directory
- No external dependencies
- Works from file:// protocol

**Implementation:**
- Bundle CSS/JS in docs directory
- Use relative paths
- Self-contained HTML files

---

### 2. Responsive Design

**Principle:** Works on desktop, tablet, mobile
- Responsive CSS
- Mobile-friendly navigation
- Touch-friendly interactions

---

### 3. Searchable

**Principle:** Full-text search across all content
- Client-side search (no server needed)
- JavaScript-based search
- Filter by type/status/floor/room

---

### 4. Interactive Visualizations

**Principle:** Embedded visualizations where useful
- Floor plan diagrams
- Equipment network graphs
- Status dashboards
- Interactive 3D viewer (optional)

**Implementation:**
- SVG for diagrams
- Canvas for complex visuals
- Embedded iframe for 3D (if interactive mode enabled)

---

### 5. Git Integration

**Principle:** Show change history
- Latest commits
- Change logs
- Diff views (optional)
- Version timeline

**Implementation:**
- Query Git history via `git log`
- Parse commit messages
- Display as timeline/changelog

---

### 6. Themes

**Principle:** Multiple visual themes
- Default (light)
- Dark mode
- Professional (corporate)
- Minimal (print-friendly)

**Implementation:**
- CSS theme files
- Theme selector in HTML
- Command-line theme selection

---

## Comparison to rustdoc

| Feature | rustdoc | ArxOS Building Docs |
|---------|---------|---------------------|
| **Source** | Rust code comments | Building data (YAML/Git) |
| **Output** | HTML API docs | HTML building docs |
| **Navigation** | Module/type hierarchy | Building/floor/room hierarchy |
| **Search** | Function/type search | Equipment/room search |
| **Examples** | Code examples | Equipment locations/status |
| **Interactive** | Type links, search | Floor plans, 3D views |
| **Hosting** | docs.rs or GitHub Pages | Self-contained HTML |

**Key Insight:** Same concept, different domain!

---

## Implementation Phases

### Phase 1: Basic HTML Generation

**Goal:** Generate simple HTML pages for building/floor/room/equipment

**Tasks:**
- Create `arx doc` command
- Basic HTML templates
- Generate building overview
- Generate floor/room/equipment pages
- Simple CSS styling

**Output:** Static HTML files that work offline

---

### Phase 2: Enhanced Features

**Goal:** Add search, filtering, navigation

**Tasks:**
- Client-side search (JavaScript)
- Filter by type/status
- Navigation sidebar
- Better styling
- Responsive design

---

### Phase 3: Visualizations

**Goal:** Add diagrams and visual elements

**Tasks:**
- Floor plan diagrams (ASCII or SVG)
- Room layout diagrams
- Equipment network graphs
- Status dashboards
- Visual navigation

---

### Phase 4: Advanced Features

**Goal:** Git history, interactivity, themes

**Tasks:**
- Git history integration
- Interactive 3D viewer
- Multiple themes
- PDF export (optional)
- Local server mode

---

## Technical Challenges

### 1. Diagram Generation

**Challenge:** Generate floor plans and room layouts

**Solutions:**
- ASCII art (simple, works everywhere)
- SVG generation (better visuals)
- Canvas-based rendering (most flexible)
- Reuse existing rendering engine

---

### 2. Large Buildings

**Challenge:** Performance with thousands of rooms/equipment

**Solutions:**
- Lazy loading (load pages on demand)
- Pagination (equipment list paginated)
- Static generation (pre-compute everything)
- Index pages (summary, detail on demand)

---

### 3. Interactivity

**Challenge:** Interactive features without server

**Solutions:**
- Client-side JavaScript
- Embedded visualizations (SVG/Canvas)
- Pre-rendered static assets
- Optional: Local server for true interactivity

---

### 4. Git Integration

**Challenge:** Including Git history in static docs

**Solutions:**
- Pre-compute commit history
- Embed commit log in HTML
- Link to Git repository (if accessible)
- Optional: Generate on-demand with local server

---

## Example Output Structure

```
building-docs/
├── index.html                    # Building overview
├── styles.css                    # Styling
├── scripts.js                    # Interactivity
├── floors/
│   ├── index.html               # Floor list
│   ├── floor-1.html             # Floor 1 detail
│   ├── floor-2.html             # Floor 2 detail
│   └── ...
├── rooms/
│   ├── index.html               # Room list
│   ├── room-201.html            # Room 201 detail
│   ├── room-202.html            # Room 202 detail
│   └── ...
├── equipment/
│   ├── index.html               # Equipment inventory
│   ├── vav-301.html             # VAV-301 detail
│   ├── camera-101.html         # Camera-101 detail
│   └── ...
├── search.html                   # Search interface
├── history.html                  # Git history (if enabled)
└── assets/
    ├── floor-plans/
    ├── room-layouts/
    └── diagrams/
```

---

## Command Syntax Design

```bash
# Basic
arx doc --building "Main Building"

# Advanced
arx doc \
  --building "Main Building" \
  --output ./docs \
  --theme dark \
  --include-history \
  --include-sensors \
  --interactive \
  --serve

# Options
--building, -b      Building name (required)
--output, -o        Output directory (default: ./docs)
--theme             Theme: default, dark, professional, minimal
--include-history   Include Git commit history
--include-sensors   Include sensor data
--include-ar-scans  Include AR scan data
--interactive       Enable interactive visualizations
--serve             Start local web server
--port               Server port (default: 8080)
--pdf               Also generate PDF version
--format            Format: html, pdf, both
--filter-status     Filter by equipment status
--filter-type       Filter by equipment type
--filter-floor      Filter by floor number
```

---

## Inspiration from rustdoc

### What Makes rustdoc Great

1. **Self-contained**: Generated docs work offline
2. **Searchable**: Built-in search functionality
3. **Navigable**: Clear navigation structure
4. **Examples**: Shows usage examples
5. **Cross-references**: Links between related items
6. **Always in sync**: Generated from source

### Applying to Building Docs

1. **Self-contained**: HTML files work offline ✅
2. **Searchable**: JavaScript search ✅
3. **Navigable**: Building → Floor → Room → Equipment ✅
4. **Examples**: Equipment locations, room layouts ✅
5. **Cross-references**: Links between rooms/equipment ✅
6. **Always in sync**: Generated from current building data ✅

---

## Next Steps / Questions

### Implementation Questions

1. **Template System**: Use a Rust templating crate (like `askama`, `handlebars-rust`) or generate HTML directly?
2. **Diagram Generation**: ASCII art, SVG, or Canvas?
3. **JavaScript**: How much interactivity? Vanilla JS or embedded library?
4. **Server**: Include local server or just static HTML?
5. **PDF Export**: Include PDF generation or just HTML?

### Immediate Actions

1. ✅ **Note for later**: Create GitHub Actions workflow for rustdoc
2. **Explore**: Building documentation generation concept
3. **Design**: Command interface and output format
4. **Prototype**: Basic HTML generation to validate concept

---

## Thoughts / Brain Dump

### Why This Makes Sense

- **Consistency**: Same philosophy as rustdoc - generate docs from data
- **Git-native**: Documentation is a view on Git-managed data
- **Portable**: Self-contained HTML can be shared, archived
- **Professional**: Makes building data presentation-ready
- **Discoverable**: Searchable, navigable, like rustdoc

### Potential Extensions

1. **API Integration**: Generate docs that link to API endpoints
2. **Live Data**: Optional server mode for real-time updates
3. **Export Formats**: PDF, Markdown, JSON
4. **Templates**: User-customizable templates
5. **Plugins**: Extensible system for custom visualizations

### User Feedback Loop

Users could:
- Generate docs to share with stakeholders
- Archive building state at specific points
- Create compliance documentation
- Generate maintenance reports
- Create building handoff packages

---

## Summary

**The Concept:** Apply rustdoc's philosophy to building data - generate beautiful, navigable HTML documentation from building information.

**The Command:** `arx doc --building "Name"` generates self-contained HTML documentation.

**The Value:** 
- Share building information easily
- Create professional documentation
- Archive building states
- Compliance and reporting
- Building handoff

**The Implementation:** Template-based HTML generation with optional interactive features.

**Status:** 🧠 Concept exploration - needs validation and prototyping

