# Minimal Building Documentation - Implementation Plan

## Core Principle: Maximum Simplicity

**Goal:** Generate HTML documentation using only:
- Standard Rust (`std::fs`, `std::fmt`)
- Existing rendering functions (reuse what we have)
- Simple string formatting (`format!()`)
- Zero external dependencies

---

## Simplest Possible Implementation

### Phase 1: Basic HTML Generation (MVP)

**Single File Approach:** Generate one HTML file per building

```bash
arx doc --building "Main Building"
# Generates: ./docs/main-building.html
```

**What's Inside:**
- Single HTML file with embedded CSS
- Building overview
- Floor listing
- Room listing  
- Equipment listing
- Reuse existing ASCII render output (embedded as `<pre>`)

**Implementation:**
- One function: `generate_building_docs()`
- Simple HTML template using `format!()` macros
- Embed ASCII output from existing renderer
- Write single file

---

## Implementation Structure

### Module Structure (Minimal)

```
src/docs/
└── mod.rs         # Single file with everything
```

**That's it.** No submodules, no templates, no complexity.

### Function Signature

```rust
// crates/arxui/crates/arxui/src/docs/mod.rs
pub fn generate_building_docs(
    building_name: &str,
    output_path: Option<&str>
) -> Result<(), Box<dyn std::error::Error>> {
    // 1. Load building data (reuse existing)
    // 2. Generate HTML string
    // 3. Write to file
    // Done.
}
```

---

## HTML Generation (Simple String Formatting)

### Template Approach: Just `format!()`

```rust
fn generate_html(building_data: &BuildingData) -> String {
    format!(r#"
<!DOCTYPE html>
<html>
<head>
    <title>{name} - Building Documentation</title>
    <style>
        body {{ font-family: monospace; margin: 40px; }}
        h1 {{ color: #333; }}
        .building-info {{ background: #f5f5f5; padding: 20px; }}
        .floor {{ margin: 20px 0; }}
        pre {{ background: #f9f9f9; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>{name}</h1>
    <div class="building-info">
        <p><strong>Floors:</strong> {floor_count}</p>
        <p><strong>Rooms:</strong> {room_count}</p>
        <p><strong>Equipment:</strong> {equipment_count}</p>
    </div>
    
    <h2>Floors</h2>
    {floors_html}
    
    <h2>Rooms</h2>
    {rooms_html}
    
    <h2>Equipment</h2>
    {equipment_html}
    
    <h2>Building Visualization</h2>
    <pre>{ascii_render}</pre>
</body>
</html>
"#,
        name = building_data.building.name,
        floor_count = building_data.floors.len(),
        room_count = total_rooms(&building_data),
        equipment_count = total_equipment(&building_data),
        floors_html = generate_floors_html(&building_data),
        rooms_html = generate_rooms_html(&building_data),
        equipment_html = generate_equipment_html(&building_data),
        ascii_render = generate_ascii_render(building_data),
    )
}
```

**That's it.** No template engine, no external dependencies.

---

## Reusing Existing Code

### 1. Load Building Data

```rust
use crate::utils::loading::load_building_data;

let building_data = load_building_data(building_name)?;
```

### 2. Reuse ASCII Rendering

```rust
// Reuse existing renderer
use crate::render::BuildingRenderer;

let renderer = BuildingRenderer::new(building_data.clone());
let ascii_output = renderer.render_floor_plan_to_string(floor)?;
```

### 3. Generate HTML Sections

```rust
fn generate_floors_html(data: &BuildingData) -> String {
    data.floors.iter()
        .map(|floor| format!(
            "<div class=\"floor\"><h3>Floor {}</h3><p>Rooms: {}</p></div>",
            floor.level,
            floor.rooms.len()
        ))
        .collect::<Vec<_>>()
        .join("\n")
}
```

---

## Command Implementation

### Add to CLI

```rust
// src/cli/mod.rs
#[derive(Subcommand)]
pub enum Commands {
    // ... existing commands ...
    
    /// Generate HTML documentation for a building
    Doc {
        /// Building name
        #[arg(long)]
        building: String,
        /// Output file path (default: ./docs/{building}.html)
        #[arg(long)]
        output: Option<String>,
    },
}
```

### Command Handler

```rust
// crates/arxui/crates/arxui/src/commands/mod.rs
Commands::Doc { building, output } => {
    docs::generate_building_docs(&building, output.as_deref())
},
```

### Handler Implementation

```rust
// crates/arxui/crates/arxui/src/commands/doc.rs (or crates/arxui/crates/arxui/src/docs/mod.rs)
pub fn handle_doc(building: String, output: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    let output_path = output.unwrap_or_else(|| {
        format!("./docs/{}.html", building.to_lowercase().replace(" ", "-"))
    });
    
    // Ensure output directory exists
    if let Some(parent) = std::path::Path::new(&output_path).parent() {
        std::fs::create_dir_all(parent)?;
    }
    
    generate_building_docs(&building, Some(&output_path))
}
```

---

## Complete Minimal Implementation

### File: `crates/arxui/crates/arxui/src/docs/mod.rs`

```rust
//! Building documentation generation
//!
//! Generates simple HTML documentation from building data.

use crate::utils::loading::load_building_data;
use crate::render::BuildingRenderer;

/// Generate HTML documentation for a building
pub fn generate_building_docs(
    building_name: &str,
    output_path: Option<&str>
) -> Result<(), Box<dyn std::error::Error>> {
    // Load building data
    let building_data = load_building_data(building_name)?;
    
    // Generate HTML
    let html = generate_html(&building_data)?;
    
    // Determine output path
    let output = output_path.unwrap_or_else(|| {
        let filename = building_name.to_lowercase().replace(" ", "-");
        &format!("./docs/{}.html", filename)
    });
    
    // Ensure directory exists
    if let Some(parent) = std::path::Path::new(output).parent() {
        std::fs::create_dir_all(parent)?;
    }
    
    // Write file
    std::fs::write(output, html)?;
    
    println!("✅ Documentation generated: {}", output);
    Ok(())
}

fn generate_html(data: &BuildingData) -> Result<String, Box<dyn std::error::Error>> {
    // Count totals
    let room_count: usize = data.floors.iter().map(|f| f.rooms.len()).sum();
    let equipment_count: usize = data.floors.iter()
        .flat_map(|f| &f.rooms)
        .map(|r| r.equipment.len())
        .sum();
    
    // Generate sections
    let floors_html = generate_floors_section(data);
    let rooms_html = generate_rooms_section(data);
    let equipment_html = generate_equipment_section(data);
    
    // Generate ASCII render (reuse existing renderer)
    let ascii_render = generate_ascii_render(data)?;
    
    Ok(format!(r#"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Building Documentation</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        <h1>{name}</h1>
        
        <div class="summary">
            <h2>Building Summary</h2>
            <ul>
                <li><strong>Floors:</strong> {floor_count}</li>
                <li><strong>Rooms:</strong> {room_count}</li>
                <li><strong>Equipment:</strong> {equipment_count}</li>
                <li><strong>Last Updated:</strong> {updated_at}</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Floors</h2>
            {floors_html}
        </div>
        
        <div class="section">
            <h2>Rooms</h2>
            {rooms_html}
        </div>
        
        <div class="section">
            <h2>Equipment</h2>
            {equipment_html}
        </div>
        
        <div class="section">
            <h2>Building Visualization</h2>
            <pre class="ascii-render">{ascii_render}</pre>
        </div>
    </div>
</body>
</html>
"#,
        name = html_escape(&data.building.name),
        floor_count = data.floors.len(),
        room_count = room_count,
        equipment_count = equipment_count,
        updated_at = data.building.updated_at.format("%Y-%m-%d %H:%M:%S UTC"),
        floors_html = floors_html,
        rooms_html = rooms_html,
        equipment_html = equipment_html,
        ascii_render = html_escape(&ascii_render),
        css = get_css(),
    ))
}

fn generate_floors_section(data: &BuildingData) -> String {
    data.floors.iter()
        .map(|floor| {
            let room_count: usize = floor.rooms.iter().map(|r| r.equipment.len()).sum();
            format!(
                r#"<div class="floor-item">
                    <h3>Floor {level}</h3>
                    <p>Rooms: {rooms}, Equipment: {equipment}</p>
                </div>"#,
                level = floor.level,
                rooms = floor.rooms.len(),
                equipment = room_count,
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn generate_rooms_section(data: &BuildingData) -> String {
    data.floors.iter()
        .flat_map(|floor| {
            floor.rooms.iter().map(move |room| {
                format!(
                    r#"<div class="room-item">
                        <h4>{name} (Floor {floor})</h4>
                        <p>Type: {type}, Equipment: {count}</p>
                    </div>"#,
                    name = html_escape(&room.name),
                    floor = floor.level,
                    type = format!("{:?}", room.room_type),
                    count = room.equipment.len(),
                )
            })
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn generate_equipment_section(data: &BuildingData) -> String {
    data.floors.iter()
        .flat_map(|floor| {
            floor.rooms.iter().flat_map(move |room| {
                room.equipment.iter().map(move |eq| {
                    format!(
                        r#"<div class="equipment-item">
                            <h4>{name}</h4>
                            <p>Type: {type}, Status: {status}, Location: Floor {floor}, Room {room}</p>
                        </div>"#,
                        name = html_escape(&eq.name),
                        type = format!("{:?}", eq.equipment_type),
                        status = format!("{:?}", eq.status),
                        floor = floor.level,
                        room = html_escape(&room.name),
                    )
                })
            })
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn generate_ascii_render(data: &BuildingData) -> Result<String, Box<dyn std::error::Error>> {
    // Reuse existing renderer
    let renderer = BuildingRenderer::new(data.clone());
    
    // Collect ASCII output for all floors
    let mut output = String::new();
    for floor_data in renderer.floors() {
        output.push_str(&format!("Floor {}:\n", floor_data.level));
        // Capture render output to string instead of println
        // (Would need to modify renderer or capture stdout)
        // For now, simple placeholder
        output.push_str("[ASCII rendering would go here]\n\n");
    }
    
    Ok(output)
}

fn html_escape(text: &str) -> String {
    text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#x27;")
}

fn get_css() -> &'static str {
    r#"
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        .summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .summary ul {
            list-style: none;
            padding: 0;
        }
        .summary li {
            padding: 5px 0;
        }
        .section {
            margin: 30px 0;
        }
        .floor-item, .room-item, .equipment-item {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            border-radius: 3px;
        }
        .ascii-render {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
        }
    "#
}
```

---

## What This Achieves

### Minimal Dependencies
- ✅ Zero external crates
- ✅ Only uses `std::fs`, `std::fmt`
- ✅ Reuses existing code (`load_building_data`, `BuildingRenderer`)

### Simple Output
- ✅ Single HTML file
- ✅ Embedded CSS
- ✅ Self-contained (works offline)
- ✅ No JavaScript needed (initially)

### Easy to Extend
- ✅ Add more sections easily (just more `format!()` calls)
- ✅ Enhance CSS incrementally
- ✅ Add JavaScript later if needed

---

## Progressive Enhancement Path

### Version 1: Static Single File (This Plan)
- One HTML file
- Embedded CSS
- Basic listing of floors/rooms/equipment
- ASCII render embedded as `<pre>`

### Version 2: Simple Multi-File (Later)
- Separate HTML files per floor/room
- Simple navigation between pages
- Still no JavaScript

### Version 3: Add Interactivity (Future)
- Client-side search (vanilla JavaScript)
- Filter by type/status
- Simple theme toggle

### Version 4: Enhanced Visualizations (Future)
- SVG floor plans
- Interactive 3D viewer
- Status dashboards

---

## Implementation Steps

### Step 1: Create Module

```rust
// src/lib.rs or crates/arxui/crates/arxui/src/docs/mod.rs
pub mod docs;
```

### Step 2: Add Command

```rust
// src/cli/mod.rs
Commands::Doc { building, output } => {
    docs::generate_building_docs(&building, output.as_deref())
}
```

### Step 3: Implement Core Function

```rust
// crates/arxui/crates/arxui/src/docs/mod.rs
// Implement generate_building_docs() as shown above
```

### Step 4: Test

```bash
arx doc --building "Main Building"
open docs/main-building.html
```

**That's it!** 4 steps, minimal code, maximum simplicity.

---

## Benefits of Minimal Approach

1. **Fast to implement** - Few hours, not days
2. **Easy to understand** - No complex abstractions
3. **Easy to maintain** - All in one place
4. **Easy to extend** - Just add more format!() calls
5. **No dependencies** - Works everywhere
6. **Self-contained** - Single file is portable

---

## What's Missing (Can Add Later)

- ❌ Multi-page navigation (single file is fine for small buildings)
- ❌ Search functionality (Ctrl+F works fine)
- ❌ Interactive visualizations (ASCII render is sufficient)
- ❌ Themes (one simple theme is enough)
- ❌ PDF export (HTML is sufficient)

**Key Insight:** Start with the absolute minimum, add features only when needed.

---

## Example Output (What User Gets)

```
docs/
└── main-building.html    # Single file, open in any browser
```

**File contains:**
- Building summary
- Floor listing
- Room listing with details
- Equipment listing with details
- ASCII building visualization

**User experience:**
1. Run `arx doc --building "Main Building"`
2. Open `docs/main-building.html` in browser
3. Browse building information
4. Share the file with others

**That's it.** No servers, no build steps, no complexity.

---

## Next Steps

1. ✅ Create `crates/arxui/crates/arxui/src/docs/mod.rs` with minimal implementation
2. ✅ Add `Doc` command to CLI
3. ✅ Test with real building data
4. ✅ Iterate based on usage

**Estimated Time:** 2-4 hours for MVP

---

## Summary

**The Minimalist Approach:**
- Single function
- Single HTML file output
- String formatting (`format!()`)
- Reuse existing renderers
- Zero external dependencies
- Embedded CSS
- Self-contained

**Result:**
- Fast implementation
- Easy maintenance
- Works everywhere
- Portable and shareable

This is the simplest possible implementation that still provides real value.

