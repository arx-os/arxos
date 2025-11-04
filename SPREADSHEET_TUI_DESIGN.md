# Spreadsheet TUI Design Document

**Created:** January 2025  
**Status:** Design Phase  
**Target:** Excel-parity spreadsheet interface for ArxOS building data

---

## Table of Contents

1. [Overview](#overview)
2. [Goals and Objectives](#goals-and-objectives)
3. [Architecture](#architecture)
4. [Module Structure](#module-structure)
5. [Data Sources](#data-sources)
6. [UI/UX Design](#uiux-design)
7. [Rendering Implementation](#rendering-implementation)
8. [Editing Workflow](#editing-workflow)
9. [Integration Points](#integration-points)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [Performance Considerations](#performance-considerations)
12. [Testing Strategy](#testing-strategy)
13. [Implementation Phases](#implementation-phases)
14. [Future Enhancements](#future-enhancements)

---

## Overview

The Spreadsheet TUI provides an Excel-like interface for viewing and editing building data in the terminal. It enables building management professionals to work with tabular data (equipment, rooms, sensors) using familiar spreadsheet conventions while maintaining ArxOS's Git-based version control and terminal-first philosophy.

### Key Features

- **Grid-based interface** with cells, rows, and columns
- **Keyboard navigation** (arrow keys, Home/End, Page Up/Down)
- **Cell editing** (inline editing with Enter, cancel with Esc)
- **Data validation** (type checking, enum validation, constraint enforcement)
- **Git integration** (auto-stage changes, optional commits)
- **Import/Export** (CSV, Excel via existing export system)
- **Filtering and sorting** (column-based filtering, multi-column sorting)
- **Search** (find and navigate to cells matching search terms)

---

## Goals and Objectives

### Primary Goals

1. **Familiar Interface**: Provide Excel-like experience for non-technical users
2. **Bulk Editing**: Enable efficient editing of multiple records
3. **Data Integrity**: Maintain data validation and type safety
4. **Version Control**: Seamlessly integrate with Git workflow
5. **Performance**: Handle large datasets (1000+ rows) efficiently

### Success Criteria

- Users can edit equipment/room data as easily as in Excel
- Changes are automatically version-controlled via Git
- Data validation prevents invalid entries
- Interface is responsive with 1000+ rows
- Import/export works with existing CSV/Excel workflows

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Command Layer                     │
│                  arx -sheet <source>                     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Spreadsheet Handler                         │
│         (src/commands/spreadsheet.rs)                    │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            Spreadsheet UI Module                         │
│           (src/ui/spreadsheet/)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Grid    │ │  Editor  │ │  Render  │ │  Data    │   │
│  │  State   │ │  Logic   │ │  Engine  │ │  Source  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            Data Source Abstraction                       │
│  EquipmentDataSource │ RoomDataSource │ SensorDataSource │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            Core Data Layer                               │
│  Equipment │ Room │ Building │ Persistence │ Git         │
└──────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **CLI Command Layer**: Parse `arx -sheet` command and route to handler
2. **Spreadsheet Handler**: Initialize spreadsheet with data source
3. **Spreadsheet UI Module**: Core spreadsheet logic, state, and rendering
4. **Data Source Abstraction**: Convert core data types to grid format
5. **Core Data Layer**: Existing ArxOS data structures and persistence

---

## Module Structure

### Directory Layout

```
src/
├── commands/
│   └── spreadsheet.rs          # Command handler
└── ui/
    └── spreadsheet/
        ├── mod.rs              # Module exports
        ├── types.rs            # Core types (Cell, Grid, Column, etc.)
        ├── grid.rs             # Grid state management
        ├── render.rs           # Rendering logic
        ├── editor.rs           # Cell editing
        ├── navigation.rs       # Keyboard navigation
        ├── validation.rs       # Data validation
        ├── data_source.rs      # Data source trait and implementations
        ├── import.rs           # CSV/Excel import
        ├── export.rs           # CSV/Excel export
        └── filter_sort.rs      # Filtering and sorting
```

### Module Dependencies

```
spreadsheet/
├── types (foundation)
├── grid (depends on: types)
├── render (depends on: types, grid)
├── editor (depends on: types, grid, validation)
├── navigation (depends on: types, grid)
├── validation (depends on: types)
├── data_source (depends on: types, core::)
├── import (depends on: types, grid, data_source)
├── export (depends on: types, grid, ui::export)
└── filter_sort (depends on: types, grid)
```

---

## Data Sources

### SpreadsheetDataSource Trait

```rust
/// Trait for data sources that provide spreadsheet data
pub trait SpreadsheetDataSource: Send + Sync {
    /// Get the column definitions for this data source
    fn columns(&self) -> Vec<ColumnDefinition>;
    
    /// Get the number of rows
    fn row_count(&self) -> usize;
    
    /// Get cell value at (row, col)
    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn std::error::Error>>;
    
    /// Set cell value at (row, col)
    fn set_cell(&mut self, row: usize, col: usize, value: CellValue) -> Result<(), Box<dyn std::error::Error>>;
    
    /// Add a new row
    fn add_row(&mut self) -> Result<usize, Box<dyn std::error::Error>>;
    
    /// Delete a row
    fn delete_row(&mut self, row: usize) -> Result<(), Box<dyn std::error::Error>>;
    
    /// Get row data as Equipment/Room/etc. (for persistence)
    fn get_row_data(&self, row: usize) -> Result<Box<dyn std::any::Any>, Box<dyn std::error::Error>>;
    
    /// Save changes to building.yaml and Git
    fn save(&mut self, commit: bool) -> Result<(), Box<dyn std::error::Error>>;
    
    /// Reload from building.yaml
    fn reload(&mut self) -> Result<(), Box<dyn std::error::Error>>;
}
```

### ColumnDefinition

```rust
pub struct ColumnDefinition {
    pub id: String,              // Column identifier (e.g., "equipment.name")
    pub label: String,           // Display label (e.g., "Name")
    pub data_type: CellType,     // Data type (Text, Number, Enum, Date, etc.)
    pub editable: bool,           // Whether cells in this column can be edited
    pub width: Option<u16>,      // Preferred column width (None = auto)
    pub validation: Option<ValidationRule>, // Validation rules
    pub enum_values: Option<Vec<String>>,   // For enum types
}
```

### CellType

```rust
pub enum CellType {
    Text,           // String
    Number,         // f64
    Integer,        // i64
    Boolean,        // bool
    Enum(Vec<String>), // Enum with possible values
    Date,           // DateTime
    UUID,           // UUID string
    Reference,      // Reference to another entity (e.g., room_id)
}
```

### Implementations

#### EquipmentDataSource

```rust
pub struct EquipmentDataSource {
    equipment: Vec<Equipment>,
    building_name: String,
    columns: Vec<ColumnDefinition>,
    modified: HashSet<usize>, // Track modified rows
}

impl SpreadsheetDataSource for EquipmentDataSource {
    fn columns(&self) -> Vec<ColumnDefinition> {
        vec![
            ColumnDefinition {
                id: "equipment.id".to_string(),
                label: "ID".to_string(),
                data_type: CellType::UUID,
                editable: false, // Read-only
                width: Some(36),
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "equipment.name".to_string(),
                label: "Name".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: Some(30),
                validation: Some(ValidationRule::Required),
                enum_values: None,
            },
            ColumnDefinition {
                id: "equipment.type".to_string(),
                label: "Type".to_string(),
                data_type: CellType::Enum(vec!["HVAC".to_string(), "Electrical".to_string(), ...]),
                editable: true,
                width: Some(15),
                validation: None,
                enum_values: Some(vec!["HVAC".to_string(), "Electrical".to_string(), ...]),
            },
            ColumnDefinition {
                id: "equipment.status".to_string(),
                label: "Status".to_string(),
                data_type: CellType::Enum(vec!["Active".to_string(), "Inactive".to_string(), ...]),
                editable: true,
                width: Some(12),
                validation: None,
                enum_values: Some(vec!["Active".to_string(), "Inactive".to_string(), ...]),
            },
            // ... more columns
        ]
    }
    
    // ... implementation methods
}
```

#### RoomDataSource

Similar structure to EquipmentDataSource, with columns for:
- ID, Name, Type, Area, Volume, Floor, Equipment Count, Properties

#### SensorDataSource

For time-series sensor data:
- Sensor ID, Timestamp, Value, Status, Equipment ID, Room ID

---

## UI/UX Design

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Spreadsheet: Equipment List                    [?] Help [Ctrl+S] Save│
├──────────┬──────────┬──────────┬──────────┬──────────┬───────────────┤
│ ID       │ Name     │ Type     │ Status   │ Room     │ Position      │
├──────────┼──────────┼──────────┼──────────┼──────────┼───────────────┤
│ uuid-123 │ AC Unit  │ HVAC     │ Active   │ Room-101 │ (10,20,5)    │
│ uuid-456 │ Light    │ Electric │ Active   │ Room-102 │ (15,25,6)    │
│ uuid-789 │ Heater   │ HVAC     │[Active]  │ Room-103 │ (20,30,5)    │
│          │          │          │          │          │               │
│          │ [Cursor] │          │          │          │               │
└──────────┴──────────┴──────────┴──────────┴──────────┴───────────────┘
│ Row 3/45  │ Column: Status │ Press Enter to edit │ Filter: [       ] │
└───────────────────────────────────────────────────────────────────────┘
```

### Visual Elements

1. **Fixed Header Row**: Column names, always visible
2. **Fixed ID Column**: First column (ID), always visible when scrolling horizontally
3. **Grid Lines**: Border between cells (using Ratatui's Block borders)
4. **Selection Highlight**: Inverted colors for selected cell
5. **Edit Mode**: Different styling (underline, cursor position)
6. **Modified Indicator**: Asterisk (*) or color change for modified cells
7. **Status Bar**: Row/column info, edit mode, filter status

### Color Scheme

- **Default**: Theme text color
- **Selected Cell**: Theme accent color background
- **Header Row**: Theme secondary color, bold
- **Modified Cell**: Yellow/orange foreground
- **Error Cell**: Red foreground
- **Read-only Column**: Muted/gray foreground

---

## Rendering Implementation

### Grid Rendering

```rust
pub fn render_spreadsheet(
    frame: &mut Frame,
    area: Rect,
    grid: &Grid,
    theme: &Theme,
) {
    // Split area into header, body, and footer
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(10),    // Grid body
            Constraint::Length(1),  // Status bar
        ])
        .split(area);
    
    // Render header
    render_header(frame, layout[0], grid, theme);
    
    // Render grid body with virtual scrolling
    render_grid_body(frame, layout[1], grid, theme);
    
    // Render status bar
    render_status_bar(frame, layout[2], grid, theme);
}
```

### Virtual Scrolling

Only render visible rows to handle large datasets:

```rust
fn render_grid_body(frame: &mut Frame, area: Rect, grid: &Grid, theme: &Theme) {
    let visible_rows = area.height.saturating_sub(1); // -1 for header
    let start_row = grid.scroll_offset;
    let end_row = (start_row + visible_rows as usize).min(grid.row_count());
    
    // Render visible rows only
    for (idx, row_idx) in (start_row..end_row).enumerate() {
        let row_area = Rect {
            x: area.x,
            y: area.y + idx as u16 + 1,
            width: area.width,
            height: 1,
        };
        render_row(frame, row_area, grid, row_idx, theme);
    }
}
```

### Column Width Management

```rust
pub struct ColumnWidthManager {
    columns: Vec<ColumnWidth>,
    total_width: u16,
    available_width: u16,
}

impl ColumnWidthManager {
    /// Calculate optimal column widths
    fn calculate_widths(&mut self, grid: &Grid) {
        // 1. Use preferred widths where specified
        // 2. Distribute remaining space proportionally
        // 3. Ensure minimum width (e.g., 8 chars)
        // 4. Handle horizontal scrolling if needed
    }
    
    /// Get visible columns based on scroll position
    fn visible_columns(&self, scroll_x: usize) -> Vec<usize> {
        // Return column indices that are visible
    }
}
```

---

## Editing Workflow

### Cell Editing States

```rust
pub enum EditState {
    Navigation,    // Normal navigation mode
    Editing,       // Cell is being edited
    Validating,    // Validating input
    Error,         // Validation error
}
```

### Editing Flow

1. **Enter Edit Mode**: User presses Enter on a cell
2. **Input Mode**: User types new value
3. **Validation**: On Enter or Tab, validate input
4. **Apply or Reject**: If valid, apply; if invalid, show error and stay in edit mode
5. **Mark Modified**: Track modified cells for Git staging

### Inline Editor

```rust
pub struct CellEditor {
    original_value: String,
    current_value: String,
    cursor_position: usize,
    column: ColumnDefinition,
}

impl CellEditor {
    fn handle_key(&mut self, key: KeyEvent) -> EditorAction {
        match key.code {
            KeyCode::Char(c) => {
                self.insert_char(c);
                EditorAction::Continue
            }
            KeyCode::Backspace => {
                self.delete_char();
                EditorAction::Continue
            }
            KeyCode::Enter => {
                EditorAction::ValidateAndApply
            }
            KeyCode::Esc => {
                EditorAction::Cancel
            }
            // ... other keys
        }
    }
}
```

### Data Validation

```rust
pub enum ValidationRule {
    Required,                    // Must not be empty
    MinLength(usize),            // Minimum string length
    MaxLength(usize),            // Maximum string length
    MinValue(f64),               // Minimum numeric value
    MaxValue(f64),               // Maximum numeric value
    Pattern(String),             // Regex pattern
    EnumValue(Vec<String>),      // Must be one of these values
    UUID,                        // Must be valid UUID
    Reference(String),           // Must reference valid entity
}

pub fn validate_cell(
    value: &str,
    column: &ColumnDefinition,
) -> Result<CellValue, ValidationError> {
    // Apply validation rules based on column definition
    // Return validated CellValue or ValidationError
}
```

---

## Integration Points

### Git Integration

```rust
impl SpreadsheetDataSource {
    fn save(&mut self, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
        // 1. Convert modified rows back to Equipment/Room objects
        // 2. Update building.yaml via PersistenceManager
        // 3. Stage changes via GitManager
        // 4. If commit=true, commit changes
    }
}
```

### Export Integration

Reuse existing export system for CSV export:

```rust
pub fn export_to_csv(
    grid: &Grid,
    data_source: &dyn SpreadsheetDataSource,
    path: PathBuf,
) -> Result<(), Box<dyn std::error::Error>> {
    // Use existing CSV export functionality
    // Or extend ui::export to support CSV
}
```

### Import Integration

```rust
pub fn import_from_csv(
    path: PathBuf,
    data_source: &mut dyn SpreadsheetDataSource,
) -> Result<(), Box<dyn std::error::Error>> {
    // Parse CSV file
    // Validate rows
    // Add/update rows in data source
    // Return summary of imported rows
}
```

### Command Palette Integration

Add spreadsheet command to command palette:

```rust
CommandEntry {
    name: "spreadsheet".to_string(),
    full_command: "arx -sheet equipment".to_string(),
    description: "Open equipment spreadsheet".to_string(),
    category: CommandCategory::Equipment,
    shortcut: Some("Ctrl+S"),
}
```

---

## Keyboard Shortcuts

### Navigation

| Key | Action |
|-----|--------|
| `Arrow Keys` | Move selection (Up/Down/Left/Right) |
| `Home` | Move to first column in row |
| `End` | Move to last column in row |
| `Ctrl+Home` | Move to first cell (0,0) |
| `Ctrl+End` | Move to last cell |
| `Page Up` | Scroll up one page |
| `Page Down` | Scroll down one page |
| `Tab` | Move to next cell (right) |
| `Shift+Tab` | Move to previous cell (left) |

### Editing

| Key | Action |
|-----|--------|
| `Enter` | Enter edit mode / Apply edit |
| `Esc` | Cancel edit |
| `F2` | Enter edit mode |
| `Delete` | Clear cell (when not editing) |
| `Ctrl+Z` | Undo last change |
| `Ctrl+Y` | Redo last change |

### Operations

| Key | Action |
|-----|--------|
| `Ctrl+S` | Save changes (stage to Git) |
| `Ctrl+Shift+S` | Save and commit |
| `Ctrl+O` | Open/Import CSV |
| `Ctrl+E` | Export to CSV |
| `Ctrl+F` | Find/Search |
| `Ctrl+G` | Go to row/column |
| `Ctrl+A` | Select all cells |
| `Ctrl+C` | Copy selected cells |
| `Ctrl+V` | Paste cells |
| `Ctrl+X` | Cut selected cells |
| `Delete` | Delete selected rows |
| `Insert` | Insert new row |

### Help

| Key | Action |
|-----|--------|
| `?` or `F1` | Show help overlay |
| `Esc` | Close help / Cancel operation |

---

## Performance Considerations

### Virtual Scrolling

- Only render visible rows (viewport-based rendering)
- Calculate scroll position based on row height
- Cache rendered row strings where possible

### Large Dataset Handling

- Lazy loading for 1000+ rows
- Batch updates (don't save on every cell change)
- Debounced saves (wait 500ms after last edit before auto-save)

### Memory Management

- Use references where possible (avoid cloning large datasets)
- Release memory when switching data sources
- Limit undo/redo history (e.g., last 50 operations)

### Rendering Optimization

- Only re-render changed cells
- Use efficient string building for cell content
- Cache column width calculations

### Data Source Optimization

- Load data in chunks if needed
- Use indices for fast lookups
- Track only modified rows (not entire dataset)

---

## Testing Strategy

### Unit Tests

**types.rs**
- Cell value parsing and validation
- Column definition creation
- Cell type conversions

**grid.rs**
- Grid state management
- Selection navigation
- Scroll position calculation

**editor.rs**
- Cell editing logic
- Input validation
- Undo/redo functionality

**validation.rs**
- All validation rules
- Error message generation
- Type conversion

**data_source.rs**
- EquipmentDataSource operations
- RoomDataSource operations
- Data conversion to/from core types

**import.rs**
- CSV parsing
- Data validation on import
- Error handling

**export.rs**
- CSV generation
- Format preservation

### Integration Tests

**test_spreadsheet_equipment_workflow()**
- Open spreadsheet with equipment data
- Edit multiple cells
- Save changes
- Verify Git staging

**test_spreadsheet_import_export()**
- Export to CSV
- Import from CSV
- Verify data integrity

**test_spreadsheet_large_dataset()**
- Open spreadsheet with 1000+ rows
- Navigate efficiently
- Edit cells
- Verify performance

**test_spreadsheet_validation()**
- Enter invalid data
- Verify error messages
- Verify invalid cells are highlighted

### Test File Structure

```
tests/
├── commands/
│   └── spreadsheet_tests.rs
└── ui/
    └── spreadsheet/
        ├── types_tests.rs
        ├── grid_tests.rs
        ├── editor_tests.rs
        ├── validation_tests.rs
        ├── data_source_tests.rs
        ├── import_tests.rs
        └── export_tests.rs
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal**: Basic grid rendering and navigation

- [ ] Create module structure
- [ ] Implement core types (Cell, Grid, Column)
- [ ] Implement basic grid rendering
- [ ] Implement keyboard navigation
- [ ] Create EquipmentDataSource skeleton
- [ ] Basic CLI command (`arx -sheet equipment`)

**Deliverable**: Grid that displays equipment data with keyboard navigation

### Phase 2: Editing (Week 2)

**Goal**: Cell editing functionality

- [ ] Implement cell editor
- [ ] Implement inline editing UI
- [ ] Implement data validation
- [ ] Implement undo/redo
- [ ] Track modified cells

**Deliverable**: Users can edit cells with validation

### Phase 3: Data Persistence (Week 3)

**Goal**: Save changes to building.yaml and Git

- [ ] Implement save functionality
- [ ] Integrate with PersistenceManager
- [ ] Integrate with GitManager
- [ ] Auto-stage on save
- [ ] Optional commit on save

**Deliverable**: Changes are saved and version-controlled

### Phase 4: Import/Export (Week 4)

**Goal**: CSV import and export

- [ ] Implement CSV export
- [ ] Implement CSV import
- [ ] Data validation on import
- [ ] Error handling for malformed CSV
- [ ] Integration with existing export system

**Deliverable**: Users can import/export CSV files

### Phase 5: Advanced Features (Week 5)

**Goal**: Filtering, sorting, and polish

- [ ] Implement column filtering
- [ ] Implement multi-column sorting
- [ ] Implement search/find
- [ ] Implement copy/paste
- [ ] Add RoomDataSource
- [ ] Add SensorDataSource
- [ ] Performance optimization

**Deliverable**: Full-featured spreadsheet with all data sources

### Phase 6: Testing and Documentation (Week 6)

**Goal**: Comprehensive testing and documentation

- [ ] Write unit tests for all modules
- [ ] Write integration tests
- [ ] Performance testing
- [ ] User documentation
- [ ] Code documentation

**Deliverable**: Fully tested and documented feature

---

## Future Enhancements

### Potential Features

1. **Formulas**: Basic formula support (SUM, AVG, COUNT, etc.)
2. **Multi-sheet**: Support multiple sheets (tabs) for different data sources
3. **Cell formatting**: Number formatting, date formatting
4. **Conditional formatting**: Color cells based on values
5. **Column resizing**: User-adjustable column widths
6. **Row grouping**: Group rows by column value
7. **Pivot tables**: Basic pivot table functionality
8. **Excel import**: Direct .xlsx file import (via `calamine` crate)
9. **Cell comments**: Add comments to cells
10. **Collaboration**: Real-time collaboration (future)

---

## Technical Decisions

### Why Ratatui?

- Already integrated in ArxOS
- Efficient rendering
- Good terminal compatibility
- Active development

### Why Trait-Based Data Sources?

- Flexible: Easy to add new data sources
- Testable: Can mock data sources for testing
- Extensible: Users could create custom data sources

### Why Virtual Scrolling?

- Performance: Handle 1000+ rows efficiently
- Memory: Only render visible cells
- User experience: Smooth navigation

### Why Git Integration?

- Consistency: Matches ArxOS philosophy
- Version control: All changes are tracked
- Collaboration: Multiple users can work on same data

---

## Dependencies

### New Dependencies

```toml
[dependencies]
# CSV parsing and generation
csv = "1.3"
# Excel file support (optional, for future)
# calamine = "0.24"

# For advanced date/time parsing (if needed)
# chrono = "0.4" (already in use)
```

### Existing Dependencies Used

- `ratatui` - UI rendering
- `crossterm` - Terminal input/output
- `serde` - Serialization
- `serde_yaml` - YAML handling
- Git operations (via existing `src/git/manager.rs`)

---

## CLI Command Design

### Command Syntax

```bash
# Open equipment spreadsheet
arx -sheet equipment [--building <name>] [--filter <filter>]

# Open room spreadsheet
arx -sheet rooms [--building <name>] [--filter <filter>]

# Open sensor data spreadsheet
arx -sheet sensors [--building <name>] [--filter <filter>]

# Open custom spreadsheet (from CSV)
arx -sheet csv --file <path.csv>
```

### Options

```bash
--building <name>     # Specify building name (default: current directory)
--filter <filter>     # Pre-filter data (e.g., "status=Active")
--commit              # Auto-commit on save (default: stage only)
--no-git              # Disable Git integration (for read-only)
```

### Examples

```bash
# Edit equipment for current building
arx -sheet equipment

# Edit equipment for specific building
arx -sheet equipment --building "Main Building"

# Edit only active equipment
arx -sheet equipment --filter "status=Active"

# Import CSV and edit
arx -sheet csv --file equipment_import.csv
```

---

## Error Handling

### Error Types

```rust
pub enum SpreadsheetError {
    InvalidCellValue { row: usize, col: usize, value: String, reason: String },
    ValidationFailed { row: usize, col: usize, rule: ValidationRule },
    SaveFailed { reason: String },
    GitOperationFailed { reason: String },
    ImportFailed { line: usize, reason: String },
    ExportFailed { reason: String },
    DataSourceError { reason: String },
}
```

### Error Display

- Show error in status bar
- Highlight invalid cells in red
- Show error message in help overlay
- Log errors for debugging

---

## Accessibility Considerations

### Keyboard-Only Navigation

- All operations accessible via keyboard
- No mouse dependency (but mouse support can be added)

### Screen Reader Support

- Clear status messages
- Descriptive cell labels
- Keyboard shortcuts documented

### Color Contrast

- Use theme colors that meet WCAG standards
- Don't rely solely on color for information
- Provide symbols/icons as backup

---

## Conclusion

The Spreadsheet TUI feature will provide building management professionals with a familiar, efficient interface for editing building data while maintaining ArxOS's terminal-first, Git-integrated philosophy. The modular design allows for incremental implementation and future enhancements.

**Ready for implementation!** 🚀

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Author**: ArxOS Development Team

