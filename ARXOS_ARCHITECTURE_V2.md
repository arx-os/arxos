# ArxOS v2: Architecture, Design & Implementation Plan

**Project:** ArxOS - Git for Buildings  
**Version:** 2.0 (Complete Rewrite)  
**Language:** Rust  
**Philosophy:** Free, Open Source, Terminal-First  
**Date:** December 2024  
**Author:** Joel (Founder)  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Vision & Philosophy](#vision--philosophy)
3. [Core Architecture](#core-architecture)
4. [Data Model & Storage](#data-model--storage)
5. [Terminal Visualization System](#terminal-visualization-system)
6. [Git Integration Strategy](#git-integration-strategy)
7. [IFC Processing Pipeline](#ifc-processing-pipeline)
8. [Spatial Data Management](#spatial-data-management)
9. [GitHub Actions Ecosystem](#github-actions-ecosystem)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Technical Specifications](#technical-specifications)
12. [Success Metrics](#success-metrics)

---

## Executive Summary

### The Problem
Building management is stuck in the stone age:
- Static PDFs that become outdated immediately
- Siloed systems that don't communicate
- Manual processes for everything
- No version control for building changes
- Complex, expensive software that nobody uses

### The Solution
**ArxOS: Git for Buildings** - A free, open-source tool that brings version control to building management:

- **Universal Path System**: Every piece of equipment gets a unique address (`/B1/3/301/HVAC/VAV-301`)
- **Git-Based Workflow**: Familiar pull requests, issues, and collaboration
- **Terminal Visualization**: ASCII/Unicode building plans that update in real-time
- **IFC Import**: Industry-standard building data import
- **Zero Infrastructure**: Runs on GitHub Actions, no servers needed

### Key Innovation
**Terminal BIM (Building Information Model)** - The first building management system designed for the terminal, making it:
- Fast (no GUI overhead)
- Universal (works anywhere)
- Scriptable (automation-friendly)
- Version controlled (stored as text in Git)

---

## Vision & Philosophy

### Core Principles

**1. Free for the World**
- Open source, no licensing fees
- Available to every building on Earth
- Community-driven development

**2. Terminal-First Design**
- ASCII/Unicode visualization
- Command-line interface
- No complex GUI dependencies

**3. Git-Native Workflow**
- Familiar to developers
- Built-in collaboration
- Complete audit trail

**4. Zero Infrastructure**
- No servers to maintain
- No databases to backup
- Runs on GitHub Actions

**5. Hardware Integration Ready**
- ESP32/RP2040 sensor support
- Open source hardware designs
- Edge-to-cloud architecture

### The "Git for Buildings" Analogy

| Git (Code) | ArxOS (Buildings) |
|------------|-------------------|
| Files | Equipment |
| Commits | Changes |
| Branches | Projects |
| Pull Requests | Work Orders |
| Issues | Problems |
| Repository | Building |
| GitHub | Building Management Platform |

---

## Core Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Terminal CLI  │  GitHub Actions  │  GitHub Web Interface  │
│  (Rust)        │  (Docker)        │  (GitHub)              │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Core Engine Layer                        │
├─────────────────────────────────────────────────────────────┤
│  IFC Parser  │  Spatial Engine  │  Git Client  │  Renderer │
│  (Rust)      │  (Rust)         │  (Rust)      │  (Rust)   │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Git Repository  │  YAML Files  │  Spatial Data  │  Assets │
│  (GitHub/GitLab) │  (Text)      │  (Coordinates) │  (Files)│
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

**1. Core Engine (Rust)**
- IFC file processing
- Spatial data management
- Git operations
- Terminal rendering

**2. GitHub Actions (Docker)**
- Automated workflows
- CI/CD integration
- Scheduled reports
- Event-driven processing

**3. Data Storage (Git)**
- YAML files for equipment data
- Git history for version control
- GitHub for collaboration
- No database required

**4. User Interfaces**
- Terminal CLI (primary)
- GitHub web interface (secondary)
- GitHub mobile app (tertiary)

---

## Data Model & Storage

### Universal Path System

**Format:** `/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT`

**Examples:**
```
/B1/3/301/HVAC/VAV-301          # VAV unit in room 301, floor 3
/EMPIRE-STATE/ROOF/MER-NORTH/HVAC/AHU-01  # Air handler on roof
/CAMPUS-WEST/1/101/LIGHTS/ZONE-A          # Lighting zone
```

**Path Rules:**
- Building: Alphanumeric, uppercase, hyphens allowed
- Floor: Number or name (ROOF, BASEMENT, etc.)
- Room: Room number or name
- System: HVAC, ELECTRICAL, PLUMBING, LIGHTS, SAFETY, etc.
- Equipment: Equipment identifier

### YAML Data Format

**Equipment File:** `equipment/B1/3/301/HVAC/VAV-301.yml`

```yaml
apiVersion: arxos.io/v1
kind: Equipment
metadata:
  name: VAV-301
  path: /B1/3/301/HVAC/VAV-301
  id: eq_vav_301_abc123
  labels:
    system: hvac
    type: vav
    criticality: medium
    building: B1
    floor: "3"
    room: "301"

spec:
  # Configuration (editable via PR)
  manufacturer: Trane
  model: VAV-500
  serial_number: TRN-2020-12345
  install_date: 2020-03-15
  
  capacity:
    cfm: 1000
    heating_btuh: 15000
  
  setpoints:
    temperature: 72
    humidity: 50
  
  schedule: weekday-9to5
  
  # Spatial data (from IFC/AR, read-only in YAML)
  position:
    x: 10.5
    y: 8.2
    z: 2.7
    coordinate_system: "building_local"
  
  bounding_box:
    min: {x: 9.5, y: 7.2, z: 1.7}
    max: {x: 11.5, y: 9.2, z: 3.7}
  
  ar_anchors:
    - id: "anchor_abc123"
      position: {x: 10.5, y: 8.2, z: 2.7}
      confidence: 0.95
      source: "lidar_scan"
      timestamp: "2024-12-01T10:30:00Z"

status:
  # Current state (synced from sensors, read-only)
  operational_state: running
  health: healthy
  current_values:
    temperature: 71.8
    humidity: 48
    damper_position: 45
  last_updated: 2024-12-01T10:30:00Z
  
  alarms:
    - type: "high_temperature"
      message: "Temperature above setpoint"
      severity: "warning"
      timestamp: "2024-12-01T09:15:00Z"

maintenance:
  schedule: quarterly
  last_pm: 2024-09-15
  next_pm: 2024-12-15
  vendor: ACME HVAC
  notes: "Filter replacement needed"

_arxos:
  # Sync metadata
  postgis_id: eq_abc123
  git_commit: a3f2b1c
  last_synced: 2024-12-01T10:30:00Z
```

**Building File:** `building.yml`

```yaml
apiVersion: arxos.io/v1
kind: Building
metadata:
  name: "Empire State Building"
  id: "bldg_empire-state"
  path: /EMPIRE-STATE
  createdAt: "2024-01-01T00:00:00Z"
  updatedAt: "2024-12-01T10:30:00Z"

spec:
  address: "350 5th Ave, New York, NY 10118"
  coordinates:
    latitude: 40.7484
    longitude: -73.9857
    elevation: 10.0
    coordinate_system: "WGS84"
  
  dimensions:
    width: 100.0
    height: 50.0
    depth: 200.0
    units: "meters"
  
  floors:
    - level: 1
      name: "Ground Floor"
      height: 4.0
    - level: 2
      name: "Second Floor"
      height: 3.5
    - level: 3
      name: "Third Floor"
      height: 3.5

status:
  phase: Active
  occupancy: 85
  last_updated: 2024-12-01T10:30:00Z
```

### File Organization

**Repository Structure:**
```
building-repo/
├── building.yml                    # Building metadata
├── floors/                         # Floor configurations
│   ├── B1/
│   │   ├── 1.yml
│   │   ├── 2.yml
│   │   └── 3.yml
├── rooms/                          # Room configurations
│   ├── B1/
│   │   ├── 1/
│   │   │   ├── 101.yml
│   │   │   ├── 102.yml
│   │   │   └── 103.yml
├── equipment/                      # Equipment configurations
│   ├── B1/
│   │   ├── 1/
│   │   │   ├── 101/
│   │   │   │   ├── HVAC/
│   │   │   │   │   ├── VAV-101.yml
│   │   │   │   │   └── RTU-101.yml
│   │   │   │   ├── ELECTRICAL/
│   │   │   │   │   ├── Panel-101.yml
│   │   │   │   │   └── Outlet-101.yml
│   │   │   │   └── PLUMBING/
│   │   │   │       ├── Toilet-101.yml
│   │   │   │       └── Sink-101.yml
├── .github/                        # GitHub Actions workflows
│   └── workflows/
│       ├── ifc-import.yml          # Process IFC files
│       ├── spatial-validator.yml   # Validate spatial data
│       ├── building-reporter.yml  # Generate reports
│       └── equipment-monitor.yml  # Monitor equipment status
├── reports/                        # Generated reports
│   ├── energy/
│   ├── maintenance/
│   └── spatial/
└── README.md                       # Building documentation
```

---

## Terminal Visualization System

### ASCII/Unicode Building Plans

**Core Concept:** Render 3D building data as 2D ASCII art in the terminal

**Example Output:**
```bash
$ arx render --building B1 --floor 3

Building B1 - Floor 3 (Third Floor)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌─────────────┐              ┌──────────────┐          │
│  │  Room 301    │              │  Room 302    │          │
│  │  Conference  │              │  Office      │          │
│  │              │              │              │          │
│  │  🌡️  VAV-301 │              │  🌡️  VAV-302  │          │
│  │  71.8°F ✅   │              │  70.5°F ✅   │          │
│  │  [10.5,8.2]  │              │  [25.3,8.1]  │          │
│  └─────────────┘              └──────────────┘          │
│                                                             │
│  ┌──────────────────────────────┐                       │
│  │  Room 303 - Open Office      │                       │
│  │                               │                       │
│  │  🌡️  VAV-303   🌡️  VAV-304   │                       │
│  │  72.1°F ✅    71.5°F ✅      │                       │
│  └──────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘

Equipment Status: ✅ 4 healthy | ⚠️ 0 warnings | ❌ 0 critical
Last Updated: 2 seconds ago
Data Source: Git repository (github.com/company/building)
```

### Rendering Engine Architecture

**Rust Implementation:**

```rust
use crossterm::{execute, style, terminal};
use std::io::{self, Write};

pub struct BuildingRenderer {
    equipment: Vec<Equipment>,
    building: Building,
}

impl BuildingRenderer {
    pub fn new(equipment: Vec<Equipment>, building: Building) -> Self {
        Self { equipment, building }
    }
    
    pub fn render_floor(&self, floor: i32) -> Result<(), Box<dyn std::error::Error>> {
        let floor_equipment: Vec<_> = self.equipment
            .iter()
            .filter(|eq| eq.floor == floor)
            .collect();
        
        if floor_equipment.is_empty() {
            println!("No equipment found on floor {}", floor);
            return Ok(());
        }
        
        // Calculate floor bounds
        let bounds = self.calculate_floor_bounds(&floor_equipment);
        
        // Render header
        self.render_header(floor)?;
        
        // Render ASCII floor plan
        self.render_ascii_floor_plan(&floor_equipment, bounds)?;
        
        // Render equipment status
        self.render_equipment_status(&floor_equipment)?;
        
        // Render footer
        self.render_footer()?;
        
        Ok(())
    }
    
    fn render_header(&self, floor: i32) -> Result<(), Box<dyn std::error::Error>> {
        let floor_name = self.get_floor_name(floor);
        println!("Building {} - Floor {} ({})", self.building.name, floor, floor_name);
        Ok(())
    }
    
    fn render_ascii_floor_plan(
        &self, 
        equipment: &[&Equipment], 
        bounds: (f64, f64, f64, f64)
    ) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;
        let width = ((max_x - min_x) * 2.0) as usize + 1;  // Scale for terminal
        let height = ((max_y - min_y) * 2.0) as usize + 1;
        
        // Create ASCII grid
        let mut grid = vec![vec![' '; width]; height];
        
        // Draw room boundaries
        self.draw_room_boundaries(&mut grid, equipment, bounds)?;
        
        // Place equipment
        self.place_equipment(&mut grid, equipment, bounds)?;
        
        // Render grid
        for row in grid {
            println!("{}", row.iter().collect::<String>());
        }
        
        Ok(())
    }
    
    fn place_equipment(
        &self, 
        grid: &mut Vec<Vec<char>>, 
        equipment: &[&Equipment], 
        bounds: (f64, f64, f64, f64)
    ) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;
        
        for eq in equipment {
            let x = ((eq.position.x - min_x) / (max_x - min_x) * (grid[0].len() - 1) as f64) as usize;
            let y = ((eq.position.y - min_y) / (max_y - min_y) * (grid.len() - 1) as f64) as usize;
            
            let symbol = self.get_equipment_symbol(eq);
            grid[y][x] = symbol;
        }
        
        Ok(())
    }
    
    fn get_equipment_symbol(&self, equipment: &Equipment) -> char {
        match equipment.equipment_type.as_str() {
            "HVAC" => '🌡️',
            "ELECTRICAL" => '⚡',
            "PLUMBING" => '🚰',
            "LIGHTS" => '💡',
            "SAFETY" => '🚨',
            "DOORS" => '🚪',
            "WINDOWS" => '🪟',
            "ELEVATOR" => '🛗',
            "STAIRS" => '🪜',
            "GENERATOR" => '🔋',
            "PUMP" => '💧',
            "VALVE" => '🔧',
            _ => '📦',
        }
    }
    
    fn render_equipment_status(&self, equipment: &[&Equipment]) -> Result<(), Box<dyn std::error::Error>> {
        println!("\nEquipment Status:");
        
        for eq in equipment {
            let status_icon = self.get_status_symbol(&eq.status);
            println!("  {} {} {} - {}°F", 
                status_icon, 
                eq.name, 
                eq.path, 
                eq.current_temperature
            );
        }
        
        Ok(())
    }
    
    fn get_status_symbol(&self, status: &str) -> &str {
        match status {
            "healthy" => "✅",
            "warning" => "⚠️",
            "critical" => "❌",
            "offline" => "⏸️",
            "maintenance" => "🔧",
            _ => "❓",
        }
    }
    
    fn render_footer(&self) -> Result<(), Box<dyn std::error::Error>> {
        let healthy = self.equipment.iter().filter(|eq| eq.status == "healthy").count();
        let warnings = self.equipment.iter().filter(|eq| eq.status == "warning").count();
        let critical = self.equipment.iter().filter(|eq| eq.status == "critical").count();
        
        println!("\nEquipment Status: ✅ {} healthy | ⚠️ {} warnings | ❌ {} critical", 
            healthy, warnings, critical);
        println!("Last Updated: {}", chrono::Utc::now().format("%H:%M:%S"));
        println!("Data Source: Git repository (github.com/company/building)");
        
        Ok(())
    }
}
```

### Interactive Features

**1. Navigation**
```bash
$ arx explore --building B1
Building B1 - Floor 3
Use arrow keys to navigate, 'q' to quit

┌─────────────────────────────────┐
│  ┌──────┐      ┌──────┐         │
│  │ 301  │      │ 302  │         │
│  │ 🌡️    │      │ 🌡️    │         │
│  │71.8°F│      │70.5°F│         │
│  └──────┘      └──────┘         │
└─────────────────────────────────┘

> Room 301 selected
  Equipment: VAV-301, LIGHTS-301
  Status: ✅ Healthy
  Press 'Enter' to view details
```

**2. Real-time Updates**
```bash
$ arx watch --building B1 --floor 3
Watching for changes... (Press Ctrl+C to stop)

Building B1 - Floor 3
┌─────────────────────────────────┐
│  ┌──────┐      ┌──────┐         │
│  │ 301  │      │ 302  │         │
│  │ 🌡️    │      │ 🌡️    │         │
│  │71.8°F│      │70.5°F│         │
│  └──────┘      └──────┘         │
└─────────────────────────────────┘

[10:30:15] VAV-301 temperature updated: 71.8°F → 72.1°F
[10:30:45] VAV-302 setpoint changed: 70.5°F → 69.0°F
```

**3. 3D Building View**
```bash
$ arx render --building B1 --3d
Building B1 - 3D View (Top-Down)

Floor 3:
┌─────────────────────────────────┐
│  ┌──────┐      ┌──────┐         │
│  │ 301  │      │ 302  │         │
│  │ 🌡️    │      │ 🌡️    │         │
│  └──────┘      └──────┘         │
└─────────────────────────────────┘

Floor 2:
┌─────────────────────────────────┐
│  ┌──────┐      ┌──────┐         │
│  │ 201  │      │ 202  │         │
│  │ 🌡️    │      │ 🌡️    │         │
│  └──────┘      └──────┘         │
└─────────────────────────────────┘

Floor 1:
┌─────────────────────────────────┐
│  ┌──────┐      ┌──────┐         │
│  │ 101  │      │ 102  │         │
│  │ 🌡️    │      │ 🌡️    │         │
│  └──────┘      └──────┘         │
└─────────────────────────────────┘
```

---

## Git Integration Strategy

### Git-First Architecture

**Core Principle:** Git is the primary data store, not a secondary sync target

**Benefits:**
- Complete version history
- Built-in collaboration
- No database complexity
- Universal access
- Zero infrastructure costs

### Git Operations

**1. Repository Structure**
```
building-repo/
├── .git/
├── building.yml
├── equipment/
├── floors/
├── rooms/
├── .github/workflows/
└── README.md
```

**2. Git Workflow**
```bash
# Import IFC file
arx import building.ifc --repo github.com/company/building

# View changes
git status
git diff

# Commit changes
git add equipment/
git commit -m "Import building equipment from IFC"

# Push to remote
git push origin main

# Create pull request
gh pr create --title "Building Equipment Import"
```

**3. Branch Strategy**
- `main`: Production-ready building data
- `feature/*`: Planned changes and improvements
- `emergency/*`: Emergency fixes and immediate actions
- `realtime/*`: Ephemeral sensor data and real-time updates

### Git Provider Support

**Supported Providers:**
- GitHub (primary)
- GitLab
- Bitbucket
- Self-hosted Git
- Local Git

**Rust Implementation:**
```rust
use git2::Repository;
use reqwest::Client;

pub enum GitProvider {
    GitHub,
    GitLab,
    Bitbucket,
    Local,
    Custom(String),
}

pub struct GitClient {
    provider: GitProvider,
    repository: Repository,
    client: Option<Client>,
}

impl GitClient {
    pub fn new(repo_url: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let provider = Self::detect_provider(repo_url);
        let repository = Repository::clone(repo_url, "./temp-repo")?;
        
        Ok(Self {
            provider,
            repository,
            client: Some(Client::new()),
        })
    }
    
    pub fn write_file(&self, path: &str, content: &str) -> Result<(), Box<dyn std::error::Error>> {
        let file_path = Path::new(&self.repository.path()).join(path);
        std::fs::write(file_path, content)?;
        Ok(())
    }
    
    pub fn commit(&self, message: &str) -> Result<(), Box<dyn std::error::Error>> {
        let mut index = self.repository.index()?;
        index.add_all(["*"], git2::IndexAddOption::DEFAULT, None)?;
        index.write()?;
        
        let tree_id = index.write_tree()?;
        let tree = self.repository.find_tree(tree_id)?;
        
        let signature = git2::Signature::now("ArxOS", "arxos@example.com")?;
        let head = self.repository.head()?;
        let parent = self.repository.find_commit(head.target().unwrap())?;
        
        self.repository.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &[&parent],
        )?;
        
        Ok(())
    }
    
    pub fn push(&self) -> Result<(), Box<dyn std::error::Error>> {
        let mut remote = self.repository.find_remote("origin")?;
        remote.push(&["refs/heads/main:refs/heads/main"], None)?;
        Ok(())
    }
}
```

---

## IFC Processing Pipeline

### IFC File Processing

**Input:** IFC file (Industry Foundation Classes)
**Output:** YAML equipment files
**Process:** Parse → Extract → Transform → Store

**Rust Implementation:**
```rust
use ifc_rs::IfcFile;
use serde_yaml;

pub struct IFCProcessor {
    file: IfcFile,
}

impl IFCProcessor {
    pub fn new(file_path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let file = IfcFile::load(file_path)?;
        Ok(Self { file })
    }
    
    pub fn process_to_yaml(&self) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
        let mut equipment = Vec::new();
        
        // Extract building elements
        for entity in self.file.entities() {
            if let Some(spatial_data) = entity.spatial_location() {
                let eq = Equipment {
                    path: self.generate_path(&entity),
                    name: entity.name().unwrap_or("Unknown").to_string(),
                    equipment_type: self.map_ifc_type(entity.type_name()),
                    position: spatial_data.position,
                    bounding_box: spatial_data.bounding_box,
                    properties: entity.properties(),
                };
                equipment.push(eq);
            }
        }
        
        Ok(equipment)
    }
    
    fn generate_path(&self, entity: &IfcEntity) -> String {
        // Generate universal path from IFC entity
        let building = "B1"; // Extract from IFC
        let floor = self.extract_floor(entity);
        let room = self.extract_room(entity);
        let system = self.map_system(entity.type_name());
        let equipment = entity.name().unwrap_or("UNKNOWN");
        
        format!("/{}/{}/{}/{}/{}", building, floor, room, system, equipment)
    }
    
    fn map_ifc_type(&self, ifc_type: &str) -> String {
        match ifc_type {
            "IfcSpace" => "ROOM".to_string(),
            "IfcBuildingElement" => "EQUIPMENT".to_string(),
            "IfcFlowTerminal" => "HVAC".to_string(),
            "IfcElectricalElement" => "ELECTRICAL".to_string(),
            "IfcPlumbingFixture" => "PLUMBING".to_string(),
            _ => "UNKNOWN".to_string(),
        }
    }
}
```

### Spatial Data Extraction

**Coordinate Systems:**
- IFC coordinates → Building local coordinates
- Support for multiple coordinate systems
- Automatic transformation

**Rust Implementation:**
```rust
use proj::Proj;

pub struct CoordinateTransformer {
    proj: Proj,
}

impl CoordinateTransformer {
    pub fn new(from_crs: &str, to_crs: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let proj = Proj::new_known_crs(from_crs, to_crs, None)?;
        Ok(Self { proj })
    }
    
    pub fn transform_point(&self, point: (f64, f64, f64)) -> Result<(f64, f64, f64), Box<dyn std::error::Error>> {
        let (x, y) = self.proj.convert((point.0, point.1))?;
        Ok((x, y, point.2)) // Z coordinate unchanged
    }
    
    pub fn transform_bounding_box(&self, bbox: BoundingBox) -> Result<BoundingBox, Box<dyn std::error::Error>> {
        let min = self.transform_point((bbox.min_x, bbox.min_y, bbox.min_z))?;
        let max = self.transform_point((bbox.max_x, bbox.max_y, bbox.max_z))?;
        
        Ok(BoundingBox {
            min_x: min.0,
            min_y: min.1,
            min_z: min.2,
            max_x: max.0,
            max_y: max.1,
            max_z: max.2,
        })
    }
}
```

---

## Spatial Data Management

### Coordinate Systems

**Supported Systems:**
- WGS84 (GPS coordinates)
- UTM (Universal Transverse Mercator)
- Building local coordinates
- Custom coordinate systems

**Rust Implementation:**
```rust
use geo::{Point, Polygon, LineString};
use nalgebra::{Vector3, Point3, Matrix4};

pub struct SpatialEngine {
    coordinate_systems: HashMap<String, CoordinateSystem>,
}

impl SpatialEngine {
    pub fn new() -> Self {
        let mut systems = HashMap::new();
        
        // Add standard coordinate systems
        systems.insert("WGS84".to_string(), CoordinateSystem::wgs84());
        systems.insert("UTM".to_string(), CoordinateSystem::utm());
        systems.insert("building_local".to_string(), CoordinateSystem::building_local());
        
        Self {
            coordinate_systems: systems,
        }
    }
    
    pub fn transform_coordinates(
        &self,
        point: Point3<f64>,
        from_crs: &str,
        to_crs: &str
    ) -> Result<Point3<f64>, Box<dyn std::error::Error>> {
        let from_system = self.coordinate_systems.get(from_crs)
            .ok_or("Unknown coordinate system")?;
        let to_system = self.coordinate_systems.get(to_crs)
            .ok_or("Unknown coordinate system")?;
        
        // Transform coordinates
        let transformed = from_system.transform_to(to_system, point)?;
        Ok(transformed)
    }
    
    pub fn calculate_distance(&self, p1: Point3<f64>, p2: Point3<f64>) -> f64 {
        let dx = p2.x - p1.x;
        let dy = p2.y - p1.y;
        let dz = p2.z - p1.z;
        
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
    
    pub fn find_equipment_within_radius(
        &self,
        center: Point3<f64>,
        radius: f64,
        equipment: &[Equipment]
    ) -> Vec<&Equipment> {
        equipment.iter()
            .filter(|eq| self.calculate_distance(center, eq.position) <= radius)
            .collect()
    }
}
```

### Spatial Indexing

**R-Tree Implementation:**
```rust
use rstar::{RTree, AABB};

pub struct SpatialIndex {
    rtree: RTree<Equipment>,
}

impl SpatialIndex {
    pub fn new(equipment: Vec<Equipment>) -> Self {
        let rtree = RTree::bulk_load(equipment);
        Self { rtree }
    }
    
    pub fn find_within_radius(&self, center: Point3<f64>, radius: f64) -> Vec<&Equipment> {
        let search_box = AABB::from_corners(
            Point3::new(center.x - radius, center.y - radius, center.z - radius),
            Point3::new(center.x + radius, center.y + radius, center.z + radius)
        );
        
        self.rtree.locate_within_aabb(&search_box)
            .filter(|eq| self.calculate_distance(center, eq.position) <= radius)
            .collect()
    }
    
    pub fn find_within_bounding_box(&self, bbox: AABB<f64>) -> Vec<&Equipment> {
        self.rtree.locate_within_aabb(&bbox).collect()
    }
}
```

---

## GitHub Actions Ecosystem

### Core Actions

**1. IFC Processor Action**
```yaml
# arxos/ifc-processor@v1
name: Process IFC Building Data
description: 'Convert IFC files to YAML equipment data'
inputs:
  ifc-file:
    description: 'Path to IFC file'
    required: true
  output-path:
    description: 'Output directory for YAML files'
    required: false
    default: 'equipment/'
runs:
  using: 'composite'
  steps:
    - name: Process IFC
      run: |
        arx import ${{ inputs.ifc-file }} --output ${{ inputs.output-path }}
        git add ${{ inputs.output-path }}
        git commit -m "Processed IFC: ${{ inputs.ifc-file }}"
        git push
```

**2. Spatial Validator Action**
```yaml
# arxos/spatial-validator@v1
name: Validate Building Spatial Data
description: 'Validate spatial coordinates and equipment placement'
inputs:
  building-path:
    description: 'Path to building data'
    required: false
    default: 'equipment/'
runs:
  using: 'composite'
  steps:
    - name: Validate Spatial Data
      run: |
        arx validate --spatial --path ${{ inputs.building-path }}
        arx check --coordinates --path ${{ inputs.building-path }}
        arx verify --paths --path ${{ inputs.building-path }}
```

**3. Building Reporter Action**
```yaml
# arxos/building-reporter@v1
name: Generate Building Reports
description: 'Generate building status and energy reports'
inputs:
  report-type:
    description: 'Type of report to generate'
    required: false
    default: 'status'
runs:
  using: 'composite'
  steps:
    - name: Generate Reports
      run: |
        arx report --type ${{ inputs.report-type }} --output reports/
        git add reports/
        git commit -m "Generated ${{ inputs.report-type }} report"
        git push
```

**4. Equipment Monitor Action**
```yaml
# arxos/equipment-monitor@v1
name: Monitor Equipment Status
description: 'Monitor equipment health and generate alerts'
inputs:
  alert-threshold:
    description: 'Alert threshold for equipment issues'
    required: false
    default: 'warning'
runs:
  using: 'composite'
  steps:
    - name: Monitor Equipment
      run: |
        arx monitor --threshold ${{ inputs.alert-threshold }}
        if [ $? -ne 0 ]; then
          gh issue create --title "Equipment Alert" --body "Equipment issues detected"
        fi
```

### Workflow Examples

**1. IFC Import Workflow**
```yaml
# .github/workflows/ifc-import.yml
name: Import IFC Building Data
on:
  push:
    paths: ['*.ifc']
jobs:
  import:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: arxos/ifc-processor@v1
        with:
          ifc-file: ${{ github.event.head_commit.modified }}
      - uses: arxos/spatial-validator@v1
      - uses: arxos/building-reporter@v1
        with:
          report-type: 'import-summary'
```

**2. Equipment Monitoring Workflow**
```yaml
# .github/workflows/equipment-monitor.yml
name: Equipment Monitoring
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: arxos/equipment-monitor@v1
        with:
          alert-threshold: 'warning'
      - uses: arxos/building-reporter@v1
        with:
          report-type: 'status'
```

**3. Building Report Workflow**
```yaml
# .github/workflows/building-report.yml
name: Weekly Building Report
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: arxos/building-reporter@v1
        with:
          report-type: 'weekly'
      - name: Create Issue
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Weekly Building Status Report',
              body: `# Building Status Report
              
              ## Equipment Status
              \`\`\`
              ${fs.readFileSync('reports/weekly-status.txt', 'utf8')}
              \`\`\`
              
              ## Energy Report
              \`\`\`
              ${fs.readFileSync('reports/energy-report.txt', 'utf8')}
              \`\`\`
              `
            });
```

---

## Implementation Roadmap

### Phase 1: Core Engine (4 weeks)

**Week 1: Project Setup**
- [ ] Initialize Rust project
- [ ] Set up project structure
- [ ] Configure dependencies
- [ ] Set up CI/CD pipeline

**Week 2: IFC Processing**
- [ ] Implement IFC parser
- [ ] Extract spatial data
- [ ] Generate universal paths
- [ ] Create YAML output

**Week 3: Git Integration**
- [ ] Implement Git client
- [ ] Support multiple providers
- [ ] File operations
- [ ] Commit and push

**Week 4: Terminal Rendering**
- [ ] ASCII floor plan renderer
- [ ] Equipment status display
- [ ] Interactive navigation
- [ ] 3D building view

### Phase 2: GitHub Actions (2 weeks)

**Week 5: Core Actions**
- [ ] IFC processor action
- [ ] Spatial validator action
- [ ] Building reporter action
- [ ] Equipment monitor action

**Week 6: Workflow Examples**
- [ ] IFC import workflow
- [ ] Equipment monitoring workflow
- [ ] Building report workflow
- [ ] Documentation

### Phase 3: Advanced Features (4 weeks)

**Week 7: Spatial Engine**
- [ ] Coordinate transformations
- [ ] Spatial indexing
- [ ] Distance calculations
- [ ] Bounding box queries

**Week 8: Interactive Features**
- [ ] Real-time updates
- [ ] Interactive navigation
- [ ] Equipment details
- [ ] Search functionality

**Week 9: Reporting System**
- [ ] Energy reports
- [ ] Maintenance reports
- [ ] Equipment status
- [ ] Custom reports

**Week 10: Testing & Polish**
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance optimization
- [ ] Documentation

### Phase 4: Community & Launch (2 weeks)

**Week 11: Community Building**
- [ ] GitHub Discussions
- [ ] Example repositories
- [ ] Tutorial videos
- [ ] Documentation site

**Week 12: Launch**
- [ ] Publish to GitHub Marketplace
- [ ] Create example workflows
- [ ] Launch announcement
- [ ] Community outreach

---

## Technical Specifications

### Rust Dependencies

**Core Dependencies:**
```toml
[dependencies]
# CLI framework
clap = { version = "4.0", features = ["derive"] }

# Terminal rendering
crossterm = "0.27"
ratatui = "0.24"

# Git operations
git2 = "0.18"
reqwest = { version = "0.11", features = ["json"] }

# Spatial data
geo = "0.25"
proj = "0.28"
nalgebra = "0.32"
rstar = "0.10"

# IFC processing
ifc-rs = "0.1"  # Custom crate needed

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_yaml = "0.9"
serde_json = "1.0"

# Error handling
anyhow = "1.0"
thiserror = "1.0"

# Async runtime
tokio = { version = "1.0", features = ["full"] }

# HTTP client
reqwest = { version = "0.11", features = ["json"] }

# Date/time
chrono = { version = "0.4", features = ["serde"] }

# File system
walkdir = "2.3"
glob = "0.3"
```

**Development Dependencies:**
```toml
[dev-dependencies]
# Testing
criterion = "0.5"
proptest = "1.0"

# Documentation
mdbook = "0.4"
```

### Performance Requirements

**IFC Processing:**
- Process 1000+ equipment items in <5 seconds
- Memory usage <100MB for typical buildings
- Support files up to 100MB

**Terminal Rendering:**
- Render floor plans in <100ms
- Support buildings with 1000+ equipment items
- Real-time updates <50ms

**Git Operations:**
- Commit operations <1 second
- Push operations <10 seconds
- Support repositories with 10,000+ files

### Platform Support

**Operating Systems:**
- Linux (primary)
- macOS
- Windows

**Terminal Support:**
- All modern terminals
- Unicode support required
- Color support recommended

**Git Providers:**
- GitHub
- GitLab
- Bitbucket
- Self-hosted Git
- Local Git

---

## Success Metrics

### Technical Metrics

**Performance:**
- IFC processing: <5 seconds for 1000 equipment items
- Terminal rendering: <100ms for floor plans
- Git operations: <1 second for commits

**Reliability:**
- 99.9% uptime for GitHub Actions
- <1% error rate for IFC processing
- Zero data loss

**Usability:**
- <5 minutes to import first building
- <1 minute to render building view
- <30 seconds to make equipment changes

### Community Metrics

**Adoption:**
- 100+ GitHub repositories using ArxOS
- 1000+ IFC files processed
- 50+ contributors

**Engagement:**
- 1000+ GitHub stars
- 100+ GitHub Discussions
- 50+ example repositories

**Impact:**
- Buildings using version control
- Reduced equipment downtime
- Improved maintenance efficiency

---

## Conclusion

ArxOS v2 represents a complete reimagining of building management software. By embracing the "Git for Buildings" philosophy and focusing on terminal-first design, we create a tool that is:

- **Free**: Available to every building on Earth
- **Simple**: Terminal interface, no complex GUI
- **Powerful**: Full spatial data management
- **Collaborative**: Built-in Git workflow
- **Extensible**: GitHub Actions ecosystem

The combination of Rust's performance, Git's collaboration model, and terminal visualization creates something genuinely unique in the building management space.

This architecture document provides the blueprint for building ArxOS v2. The implementation roadmap ensures we can deliver a working system in 12 weeks, with community building and launch in the final phase.

The future of building management is version-controlled, terminal-based, and free for everyone. ArxOS v2 makes that future possible.

---

**Document Version:** 2.0  
**Last Updated:** December 2024  
**Status:** Ready for Implementation  
**Next Step:** Begin Phase 1 development
