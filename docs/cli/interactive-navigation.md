# Interactive Navigation Guide

This guide covers **interactive navigation** in the Arxos CLI, enabling you to explore buildings as filesystems with infinite fractal zoom capabilities across all 6 visualization layers.

---

## 🎯 **Overview**

Interactive navigation in Arxos transforms building exploration into an intuitive, terminal-based experience. The CLI provides **interactive modes** that make navigating complex building hierarchies as natural as browsing a file system, with the added power of **infinite fractal zoom** and **6-layer visualization**.

### **Revolutionary Features**

- **Interactive Mode**: Enter interactive sessions for building exploration
- **Infinite Zoom Navigation**: Seamlessly zoom between 11 scale levels
- **6-Layer Visualization**: Switch between SVG-BIM, AR overlay, ASCII art, and CLI views
- **Real-time Updates**: Live building data and status updates
- **Contextual Help**: Intelligent help based on current location and zoom level
- **Command History**: Persistent command history across sessions
- **Tab Completion**: Intelligent path and command completion
- **Interactive Menus**: Navigate complex hierarchies with menu interfaces

---

## 🚀 **Getting Started with Interactive Mode**

### **Entering Interactive Mode**

```bash
# Start interactive mode for current building
arx interactive

# Start interactive mode for specific building
arx interactive building:main

# Start interactive mode with specific zoom level
arx interactive --zoom floor

# Start interactive mode with ASCII rendering
arx interactive --ascii

# Start interactive mode with SVG BIM view
arx interactive --svg

# Start interactive mode with AR overlay
arx interactive --ar
```

### **Interactive Mode Prompt**

When you enter interactive mode, you'll see a context-aware prompt:

```bash
🏗️  Arxos Interactive Mode
📍  Current Location: building:main/floor:1/room:101
🔬  Zoom Level: room (1 char = 0.01m)
🎨  View Mode: ASCII + SVG-BIM
📊  Status: 12 objects, 3 systems active

arx> 
```

The prompt shows:
- **Current Location**: Your position in the building filesystem
- **Zoom Level**: Current zoom level with scale information
- **View Mode**: Active visualization layers
- **Status**: Object count and system status

---

## 🔬 **Infinite Zoom Navigation**

### **Zoom Level Commands**

Interactive mode provides seamless zoom navigation across all 11 scale levels:

```bash
# Zoom to campus level (1 char = 100m)
arx> zoom campus

# Zoom to site level (1 char = 10m)
arx> zoom site

# Zoom to building level (1 char = 1m)
arx> zoom building

# Zoom to floor level (1 char = 0.1m)
arx> zoom floor

# Zoom to room level (1 char = 0.01m)
arx> zoom room

# Zoom to furniture level (1 char = 0.001m)
arx> zoom furniture

# Zoom to equipment level (1 char = 0.0001m)
arx> zoom equipment

# Zoom to component level (1 char = 0.00001m)
arx> zoom component

# Zoom to detail level (1 char = 0.000001m)
arx> zoom detail

# Zoom to submicron level (1 char = 0.0000001m)
arx> zoom submicron

# Zoom to nanoscopic level (1 char = 0.00000001m)
arx> zoom nanoscopic
```

### **Zoom with Options**

```bash
# Zoom with smooth transition
arx> zoom building --smooth

# Zoom with specific duration
arx> zoom room --duration 2.5

# Zoom with ASCII rendering
arx> zoom floor --ascii

# Zoom with SVG BIM view
arx> zoom building --svg

# Zoom with AR overlay
arx> zoom room --ar

# Zoom with information display
arx> zoom campus --info

# Zoom with performance metrics
arx> zoom building --performance
```

### **Zoom Status and Information**

```bash
# Check current zoom level
arx> zoom status

# Show zoom information
arx> zoom info

# List available zoom levels
arx> zoom levels

# Show zoom history
arx> zoom history

# Reset zoom to default
arx> zoom reset

# Zoom to previous level
arx> zoom back

# Zoom to next level
arx> zoom forward
```

---

## 🎨 **6-Layer Visualization Switching**

Interactive mode allows you to switch between all 6 visualization layers:

### **View Mode Commands**

```bash
# Switch to ASCII art view
arx> view ascii

# Switch to SVG BIM view
arx> view svg

# Switch to 3D Three.js view
arx> view three

# Switch to AR overlay view
arx> view ar

# Switch to CLI data view
arx> view cli

# Switch to AQL query view
arx> view aql

# Show current view mode
arx> view status

# List available view modes
arx> view modes

# Toggle between view modes
arx> view toggle

# Split view (multiple layers)
arx> view split ascii+svg

# Custom view combination
arx> view custom "ascii+svg+ar"
```

### **View Mode Examples**

```bash
# ASCII Art View (Terminal-based)
arx> view ascii
🎨  ASCII Art View Active
🔬  Zoom Level: room (1 char = 0.01m)

┌─────────────────────────────────────────┐
│                                         │
│              ROOM 101                   │
│                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  │
│  │ W1  │  │ W2  │  │ W3  │  │ W4  │  │
│  └─────┘  └─────┘  └─────┘  └─────┘  │
│                                         │
└─────────────────────────────────────────┘

# SVG BIM View (Browser-based)
arx> view svg
🎨  SVG BIM View Active
🔬  Zoom Level: room (1 char = 0.01m)
🌐  Opening SVG BIM in browser...

# 3D Three.js View (Browser-based)
arx> view three
🎨  3D Three.js View Active
🔬  Zoom Level: room (1 char = 0.01m)
🌐  Opening 3D viewer in browser...

# AR Overlay View (Mobile AR)
arx> view ar
🎨  AR Overlay View Active
🔬  Zoom Level: room (1 char = 0.01m)
📱  AR mode activated on mobile device...
```

---

## 🗂️ **Filesystem Navigation**

### **Basic Navigation Commands**

```bash
# Show current location
arx> pwd

# Change directory
arx> cd floor:2

# List contents
arx> ls

# List with tree structure
arx> ls --tree

# List with ASCII rendering
arx> ls --ascii

# List with SVG BIM view
arx> ls --svg

# List with properties
arx> ls --properties

# List with status
arx> ls --status

# Show tree structure
arx> tree

# Show tree with limited depth
arx> tree --depth 2

# Show tree with specific types
arx> tree --types floor,room
```

### **Advanced Navigation**

```bash
# Navigate to parent
arx> cd ..

# Navigate to root
arx> cd /

# Navigate to specific path
arx> cd building:main/floor:1/room:101

# Navigate to campus level
arx> cd campus:main

# Navigate to systems
arx> cd systems:electrical

# Navigate to specific component
arx> cd systems:electrical/panel:main

# Navigate to micro level
arx> cd micro:chip_level

# Navigate to previous location
arx> cd -

# Navigate to bookmark
arx> cd @bookmark:office
```

### **Navigation with Context**

```bash
# Navigate and show context
arx> cd floor:2 --context

# Navigate with zoom adjustment
arx> cd room:201 --zoom room

# Navigate with view change
arx> cd systems:electrical --view ascii

# Navigate with information display
arx> cd panel:main --info

# Navigate with status check
arx> cd room:101 --status

# Navigate with validation
arx> cd wall:north --validate

# Navigate with search
arx> cd --search "outlet"
```

---

## 🔍 **Search and Discovery**

### **Search Commands**

```bash
# Search for objects
arx> find outlet

# Search by type
arx> find --type electrical

# Search by system
arx> find --system hvac

# Search by property
arx> find --property "voltage=480V"

# Search by status
arx> find --status active

# Search by location
arx> find --location "floor:1"

# Search with regex
arx> find --regex "panel.*"

# Search with wildcards
arx> find "panel*"

# Search with multiple criteria
arx> find --type outlet --system electrical --status active

# Search with results limit
arx> find outlet --limit 10

# Search with sorting
arx> find outlet --sort name

# Search with output format
arx> find outlet --format json
```

### **Advanced Search**

```bash
# Search with spatial constraints
arx> find --near "room:101" --radius 10m

# Search with temporal constraints
arx> find --modified "2024-01-01" --modified-before "2024-12-31"

# Search with confidence scoring
arx> find --confidence 0.8

# Search with relationship constraints
arx> find --connected-to "panel:main"

# Search with performance constraints
arx> find --performance ">90%"

# Search with energy constraints
arx> find --energy "<100W"

# Search with maintenance constraints
arx> find --maintenance-due "7d"

# Search with compliance constraints
arx> find --compliance "fire-safety"
```

---

## 📊 **ArxObject Management**

### **Inspection Commands**

```bash
# Show object details
arx> inspect outlet:1

# Show object with full details
arx> inspect outlet:1 --full

# Show object properties
arx> inspect outlet:1 --properties

# Show object relationships
arx> inspect outlet:1 --relationships

# Show object history
arx> inspect outlet:1 --history

# Show object performance
arx> inspect outlet:1 --performance

# Show object validation
arx> inspect outlet:1 --validation

# Show object compliance
arx> inspect outlet:1 --compliance

# Show object maintenance
arx> inspect outlet:1 --maintenance

# Show object energy usage
arx> inspect outlet:1 --energy
```

### **ArxObject Operations**

```bash
# Validate object
arx> arxobject validate outlet:1

# Relate objects
arx> arxobject relate outlet:1 --to "circuit:1"

# Show object lifecycle
arx> arxobject lifecycle outlet:1

# Search objects
arx> arxobject search "voltage=120V"

# Show object statistics
arx> arxobject stats outlet:1

# Export object data
arx> arxobject export outlet:1 --format json

# Show object connections
arx> arxobject connections outlet:1

# Show object dependencies
arx> arxobject dependencies outlet:1

# Show object impact analysis
arx> arxobject impact outlet:1
```

---

## 🔌 **Real-time Monitoring**

### **Monitoring Commands**

```bash
# Start monitoring
arx> monitor start

# Stop monitoring
arx> monitor stop

# Show monitoring status
arx> monitor status

# Monitor specific object
arx> monitor outlet:1

# Monitor specific system
arx> monitor systems:electrical

# Monitor with alerts
arx> monitor --alerts

# Monitor with metrics
arx> monitor --metrics

# Monitor with performance
arx> monitor --performance

# Monitor with energy
arx> monitor --energy

# Monitor with maintenance
arx> monitor --maintenance

# Monitor with compliance
arx> monitor --compliance
```

### **Real-time Updates**

```bash
# Watch for changes
arx> watch

# Watch specific path
arx> watch floor:1

# Watch with filters
arx> watch --type outlet

# Watch with notifications
arx> watch --notify

# Watch with logging
arx> watch --log

# Watch with metrics
arx> watch --metrics

# Watch with alerts
arx> watch --alerts

# Watch with performance
arx> watch --performance
```

---

## 🎯 **Interactive Menus**

### **Menu Navigation**

```bash
# Show main menu
arx> menu

# Show navigation menu
arx> menu navigation

# Show zoom menu
arx> menu zoom

# Show view menu
arx> menu view

# Show search menu
arx> menu search

# Show monitoring menu
arx> menu monitoring

# Show help menu
arx> menu help

# Show settings menu
arx> menu settings

# Show bookmarks menu
arx> menu bookmarks

# Show history menu
arx> menu history
```

### **Menu Examples**

```bash
# Main Menu
arx> menu
🏗️  Arxos Interactive Menu
─────────────────────────────
1. Navigation
2. Zoom Control
3. View Modes
4. Search & Discovery
5. Monitoring
6. ArxObject Management
7. Settings
8. Help
9. Exit

Select option (1-9): 

# Zoom Menu
arx> menu zoom
🔬  Zoom Control Menu
─────────────────────
1. Campus (1 char = 100m)
2. Site (1 char = 10m)
3. Building (1 char = 1m)
4. Floor (1 char = 0.1m)
5. Room (1 char = 0.01m)
6. Furniture (1 char = 0.001m)
7. Equipment (1 char = 0.0001m)
8. Component (1 char = 0.00001m)
9. Detail (1 char = 0.000001m)
10. Submicron (1 char = 0.0000001m)
11. Nanoscopic (1 char = 0.00000001m)
12. Back to Main Menu

Select zoom level (1-12):
```

---

## 🛠️ **Interactive Features**

### **Tab Completion**

Interactive mode provides intelligent tab completion:

```bash
# Path completion
arx> cd fl<TAB>          # Completes to floor:1
arx> cd systems:el<TAB>  # Completes to systems:electrical

# Command completion
arx> zo<TAB>             # Completes to zoom
arx> vi<TAB>             # Completes to view

# Option completion
arx> zoom --<TAB>        # Shows available options
arx> ls --<TAB>          # Shows available options

# Object completion
arx> inspect out<TAB>    # Completes to outlet:1
arx> monitor pan<TAB>    # Completes to panel:main
```

### **Command History**

```bash
# Show command history
arx> history

# Show recent commands
arx> history --recent 10

# Search command history
arx> history --search "zoom"

# Execute command from history
arx> !10                 # Execute command #10

# Execute last command
arx> !!

# Execute last command with substitution
arx> !:s/zoom/room/     # Substitute 'zoom' with 'room' in last command

# Show command with line numbers
arx> history --numbers

# Clear command history
arx> history --clear
```

### **Contextual Help**

```bash
# Show help for current context
arx> help

# Show help for specific command
arx> help zoom

# Show help for current location
arx> help --location

# Show help for current zoom level
arx> help --zoom

# Show help for current view mode
arx> help --view

# Show help with examples
arx> help --examples

# Show help with tutorials
arx> help --tutorials

# Show help with best practices
arx> help --best-practices
```

---

## ⚙️ **Settings and Configuration**

### **Settings Commands**

```bash
# Show current settings
arx> settings

# Show specific setting
arx> settings prompt

# Change setting
arx> settings prompt "🏗️ {location} [{zoom}] > "

# Reset setting to default
arx> settings prompt --reset

# Show available settings
arx> settings --list

# Export settings
arx> settings --export

# Import settings
arx> settings --import settings.yml

# Show setting help
arx> settings --help
```

### **Configuration Examples**

```bash
# Custom prompt format
arx> settings prompt "🏗️ {building}/{floor}/{room} [{zoom}] > "

# Custom zoom levels
arx> settings zoom.levels.custom "ultra-macro:0.000000001"

# Custom view modes
arx> settings view.custom "ascii+svg+ar"

# Custom search defaults
arx> settings search.default.limit 20

# Custom monitoring intervals
arx> settings monitor.interval 5s

# Custom ASCII rendering
arx> settings ascii.charset "extended"

# Custom SVG BIM settings
arx> settings svg.coordinate-system "world"
```

---

## 🔖 **Bookmarks and Shortcuts**

### **Bookmark Commands**

```bash
# Create bookmark
arx> bookmark add office "building:main/floor:2/room:201"

# List bookmarks
arx> bookmark list

# Navigate to bookmark
arx> cd @office

# Show bookmark details
arx> bookmark show office

# Edit bookmark
arx> bookmark edit office "building:main/floor:2/room:201"

# Delete bookmark
arx> bookmark delete office

# Export bookmarks
arx> bookmark export

# Import bookmarks
arx> bookmark import bookmarks.yml

# Search bookmarks
arx> bookmark search "office"
```

### **Shortcut Commands**

```bash
# Create shortcut
arx> shortcut add "el" "cd systems:electrical"

# List shortcuts
arx> shortcut list

# Execute shortcut
arx> el

# Show shortcut details
arx> shortcut show "el"

# Edit shortcut
arx> shortcut edit "el" "cd systems:electrical --view ascii"

# Delete shortcut
arx> shortcut delete "el"

# Export shortcuts
arx> shortcut export

# Import shortcuts
arx> shortcut import shortcuts.yml
```

---

## 🚪 **Exiting Interactive Mode**

### **Exit Commands**

```bash
# Exit interactive mode
arx> exit

# Exit with confirmation
arx> exit --confirm

# Exit and save session
arx> exit --save

# Exit and export session
arx> exit --export session.yml

# Exit and clear history
arx> exit --clear-history

# Exit and reset settings
arx> exit --reset

# Exit with status
arx> exit --status

# Force exit
arx> exit --force

# Show exit options
arx> exit --help
```

### **Session Management**

```bash
# Save current session
arx> session save

# Load saved session
arx> session load office

# List saved sessions
arx> session list

# Show session details
arx> session show office

# Delete saved session
arx> session delete office

# Export session
arx> session export office

# Import session
arx> session import session.yml

# Clear all sessions
arx> session clear
```

---

## 🔗 **Related Documentation**

- **Vision**: [Platform Vision](../../vision.md)
- **Architecture**: [Current Architecture](../current-architecture.md)
- **File Tree**: [File Tree Structure](file-tree.md)
- **Commands**: [CLI Commands Reference](commands.md)
- **ASCII-BIM**: [ASCII-BIM Engine](../architecture/ascii-bim.md)
- **ArxObjects**: [ArxObject System](../architecture/arxobjects.md)

---

## 🆘 **Getting Help**

- **Interactive Issues**: Test with [Enhanced Zoom Demo](../frontend/demo-enhanced-zoom.html)
- **Navigation Questions**: Review [File Tree Structure](file-tree.md)
- **Command Help**: Check [CLI Commands Reference](commands.md)
- **Architecture Questions**: Review [Current Architecture](../current-architecture.md)

Interactive navigation in Arxos transforms building exploration into an intuitive, powerful experience. With **infinite fractal zoom**, **6-layer visualization**, and **intelligent assistance**, you can navigate buildings as naturally as browsing a file system, while accessing the full power of the revolutionary Arxos platform.

**Happy navigating! 🏗️✨**