# BIM Daemon Architecture

## The Reality Validation Layer for Digital Twins

Arxos operates as a daemon service that continuously validates Building Information Models (BIM) against real-world conditions. Rather than replacing existing BIM tools, Arxos enhances them by maintaining bidirectional synchronization between digital models and physical reality.

### 📖 Section Contents

1. **[Architecture Overview](architecture.md)** - Daemon design and components
2. **[File Ingestion](ingestion.md)** - PDF, IFC, DWG, RVT processing
3. **[Validation Engine](validation.md)** - Reality vs model comparison
4. **[Sync Protocol](sync-protocol.md)** - Bidirectional updates
5. **[Connectors](connectors.md)** - Tool-specific integrations
6. **[Compliance](compliance.md)** - Automated code checking

## 🎯 Core Concept: Living Digital Twins

### The Problem with Traditional BIM

```rust
pub struct TraditionalBIMProblem {
    // BIM models become stale immediately after construction
    model_creation: "During design phase",
    reality_drift: "Starts on day 1 of occupancy",
    update_frequency: "Never or annually if lucky",
    validation_method: "Manual site visits",
    accuracy_after_1_year: "< 60%",
    
    // Result: Digital twins that lie
    trust_level: "Low",
    usefulness: "Historical reference only",
    maintenance_value: "Minimal",
}
```

### The Arxos Solution

```rust
pub struct ArxosBIMDaemon {
    // Continuous validation and updates
    validation_frequency: "Daily or on-change",
    update_method: "Automatic bidirectional sync",
    data_sources: vec![
        "iPhone LiDAR scans",
        "Human AR markups",
        "IoT sensor telemetry",
        "Maintenance work orders",
    ],
    accuracy_maintained: "> 95%",
    
    // Result: Digital twins that live
    trust_level: "High",
    usefulness: "Real-time decision making",
    maintenance_value: "Predictive and preventive",
}
```

## 🏗️ System Architecture

### Three-Layer Stack

```
┌─────────────────────────────────────────────────────────┐
│                    BIM TOOLS LAYER                       │
├─────────────────────────────────────────────────────────┤
│  Revit │ AutoCAD │ ArchiCAD │ Rhino │ SketchUp │ Bentley│
│    ↕        ↕         ↕         ↕        ↕         ↕    │
│  .rvt     .dwg      .pln     .3dm     .skp      .dgn   │
└────────────────────────┬─────────────────────────────────┘
                         │ File I/O
┌────────────────────────▼─────────────────────────────────┐
│                 ARXOS DAEMON LAYER                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           File Ingestion Engine                  │   │
│  │  • PDF architectural plans                       │   │
│  │  • IFC building models (ISO 16739)              │   │
│  │  • DWG/DXF AutoCAD files                        │   │
│  │  • RVT Revit projects                           │   │
│  │  • gbXML energy models                          │   │
│  └──────────────────────────────────────────────────┘   │
│                           ↓                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Semantic Understanding Engine            │   │
│  │  • Extract room boundaries and labels           │   │
│  │  • Identify building systems                    │   │
│  │  • Parse equipment schedules                    │   │
│  │  • Understand spatial relationships             │   │
│  └──────────────────────────────────────────────────┘   │
│                           ↓                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Reality Validation Engine               │   │
│  │  • Compare model to LiDAR scans                 │   │
│  │  • Validate against human markups               │   │
│  │  • Check sensor telemetry                       │   │
│  │  • Identify discrepancies                       │   │
│  └──────────────────────────────────────────────────┘   │
│                           ↓                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Bidirectional Sync Engine               │   │
│  │  • Push validated data back to BIM              │   │
│  │  • Update properties and parameters             │   │
│  │  • Add validation metadata                      │   │
│  │  • Maintain change history                      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└────────────────────────┬─────────────────────────────────┘
                         │ Reality Data
┌────────────────────────▼─────────────────────────────────┐
│                  REALITY CAPTURE LAYER                   │
├─────────────────────────────────────────────────────────┤
│  iPhone LiDAR │ AR Markups │ IoT Sensors │ Work Orders  │
└──────────────────────────────────────────────────────────┘
```

## 💡 Key Features

### 1. File Watch Service

```rust
pub struct BIMFileWatcher {
    watched_paths: Vec<PathBuf>,
    handlers: HashMap<String, Box<dyn FileHandler>>,
    
    pub async fn watch(&mut self) -> Result<(), WatchError> {
        let (tx, rx) = channel();
        
        let mut watcher = RecommendedWatcher::new(tx, Config::default())?;
        
        for path in &self.watched_paths {
            watcher.watch(path, RecursiveMode::Recursive)?;
        }
        
        while let Ok(event) = rx.recv() {
            match event {
                Event::Write(path) | Event::Create(path) => {
                    if let Some(ext) = path.extension() {
                        if let Some(handler) = self.handlers.get(ext.to_str()?) {
                            handler.process(path).await?;
                        }
                    }
                }
                _ => {}
            }
        }
        Ok(())
    }
}
```

### 2. Universal Model Representation

```rust
// Internal representation that can map to any BIM format
pub struct UniversalBuildingModel {
    pub metadata: BuildingMetadata,
    pub spatial_structure: SpatialHierarchy,
    pub components: Vec<BuildingComponent>,
    pub systems: Vec<BuildingSystem>,
    pub relationships: Vec<Relationship>,
    pub validation_history: Vec<ValidationRecord>,
}

pub struct BuildingComponent {
    pub id: Uuid,
    pub component_type: ComponentType,  // Wall, Door, Window, Equipment
    pub geometry: Geometry,             // 3D representation
    pub properties: HashMap<String, Value>,
    pub reality_validation: Option<ValidationResult>,
    pub last_verified: Option<DateTime<Utc>>,
}

pub struct ValidationResult {
    pub status: ValidationStatus,       // Matches, Modified, Missing, New
    pub confidence: f32,                // 0.0 to 1.0
    pub discrepancies: Vec<Discrepancy>,
    pub evidence_source: EvidenceSource, // LiDAR, Human, Sensor
    pub validated_at: DateTime<Utc>,
    pub validated_by: String,
}
```

### 3. Format-Specific Connectors

```rust
pub trait BIMConnector: Send + Sync {
    /// Import BIM file to universal model
    fn import(&self, path: &Path) -> Result<UniversalBuildingModel>;
    
    /// Export universal model back to BIM format
    fn export(&self, model: &UniversalBuildingModel, path: &Path) -> Result<()>;
    
    /// Update specific properties in BIM file
    fn update_properties(&self, path: &Path, updates: Vec<PropertyUpdate>) -> Result<()>;
    
    /// Add validation metadata to BIM
    fn add_validation(&self, path: &Path, validation: ValidationReport) -> Result<()>;
    
    /// Extract change history
    fn get_changes(&self, path: &Path, since: DateTime<Utc>) -> Result<Vec<Change>>;
}
```

## 📊 Ingestion Pipeline

### PDF Processing

```rust
pub struct PdfIngestion {
    pub fn process_architectural_pdf(&self, pdf: &[u8]) -> Result<BuildingPlan> {
        // 1. Extract pages
        let pages = extract_pages(pdf)?;
        
        // 2. Identify drawing types
        let floor_plans = pages.iter()
            .filter(|p| is_floor_plan(p))
            .collect::<Vec<_>>();
            
        let elevations = pages.iter()
            .filter(|p| is_elevation(p))
            .collect::<Vec<_>>();
            
        // 3. Process floor plans
        let mut rooms = Vec::new();
        for plan in floor_plans {
            // OCR room numbers and labels
            let text_elements = ocr_text(plan)?;
            
            // Detect walls, doors, windows
            let geometry = detect_architectural_elements(plan)?;
            
            // Correlate text with geometry
            rooms.extend(correlate_rooms(text_elements, geometry)?);
        }
        
        // 4. Extract metadata from title block
        let metadata = extract_title_block_info(&pages[0])?;
        
        // 5. Parse room schedule if present
        let room_schedule = extract_room_schedule(pdf)?;
        
        Ok(BuildingPlan {
            metadata,
            rooms,
            room_schedule,
            coordinate_system: establish_coordinates(&floor_plans[0])?,
        })
    }
}
```

### IFC Integration

```rust
pub struct IfcConnector {
    pub fn import_ifc(&self, file_path: &Path) -> Result<UniversalBuildingModel> {
        let ifc = ifc_rs::open(file_path)?;
        
        // Extract spatial structure
        let project = ifc.get_project()?;
        let sites = ifc.get_sites()?;
        let buildings = ifc.get_buildings()?;
        let storeys = ifc.get_building_storeys()?;
        let spaces = ifc.get_spaces()?;
        
        // Extract building elements
        let walls = ifc.get_all::<IfcWall>()?;
        let doors = ifc.get_all::<IfcDoor>()?;
        let windows = ifc.get_all::<IfcWindow>()?;
        let equipment = ifc.get_all::<IfcBuildingElementProxy>()?;
        
        // Convert to universal model
        let model = UniversalBuildingModel {
            metadata: extract_project_metadata(&project),
            spatial_structure: build_spatial_hierarchy(&buildings, &storeys, &spaces),
            components: convert_elements_to_components(walls, doors, windows, equipment),
            systems: extract_building_systems(&ifc),
            relationships: extract_relationships(&ifc),
            validation_history: Vec::new(),
        };
        
        Ok(model)
    }
    
    pub fn export_validation_to_ifc(&self, 
        ifc_path: &Path, 
        validation: &ValidationReport
    ) -> Result<()> {
        let mut ifc = ifc_rs::open(ifc_path)?;
        
        // Add property set for Arxos validation
        let property_set = IfcPropertySet {
            name: "ArxosValidation".to_string(),
            properties: vec![
                IfcProperty::Text("LastValidated", validation.timestamp.to_rfc3339()),
                IfcProperty::Real("AccuracyScore", validation.accuracy_score),
                IfcProperty::Integer("DiscrepancyCount", validation.discrepancies.len()),
                IfcProperty::Text("ValidationSource", validation.source.to_string()),
            ],
        };
        
        // Attach to relevant elements
        for discrepancy in &validation.discrepancies {
            if let Some(element) = ifc.get_by_id(&discrepancy.element_id) {
                element.add_property_set(property_set.clone());
                
                // Add specific issue as comment
                element.add_comment(&discrepancy.description);
            }
        }
        
        ifc.save()?;
        Ok(())
    }
}
```

## 🔄 Bidirectional Sync

### Reality → BIM Updates

```rust
pub struct RealityToBIMSync {
    pub fn sync_reality_to_bim(&self, 
        bim_model: &mut UniversalBuildingModel,
        reality_data: &RealityCapture
    ) -> SyncReport {
        let mut report = SyncReport::new();
        
        // 1. Match reality objects to BIM components
        let matches = self.match_components(bim_model, reality_data);
        
        // 2. Process each match
        for (bim_component, reality_object) in matches {
            match self.compare(bim_component, reality_object) {
                Comparison::Matches => {
                    // Update validation timestamp
                    bim_component.last_verified = Some(Utc::now());
                    bim_component.reality_validation = Some(ValidationResult {
                        status: ValidationStatus::Verified,
                        confidence: 0.95,
                        discrepancies: vec![],
                        evidence_source: reality_object.source,
                        validated_at: Utc::now(),
                        validated_by: reality_object.captured_by,
                    });
                }
                
                Comparison::Modified(changes) => {
                    // Record discrepancies
                    report.modifications.push(Modification {
                        component_id: bim_component.id,
                        changes,
                        suggested_action: self.suggest_action(&changes),
                    });
                }
                
                Comparison::Missing => {
                    // Component in BIM but not in reality
                    report.missing_components.push(bim_component.id);
                }
            }
        }
        
        // 3. Handle new reality objects not in BIM
        for reality_object in reality_data.unmatched_objects() {
            report.new_in_reality.push(NewComponent {
                detected_type: reality_object.object_type,
                location: reality_object.position,
                properties: reality_object.properties,
                confidence: reality_object.detection_confidence,
            });
        }
        
        report
    }
}
```

### BIM → Reality Notifications

```rust
pub struct BIMToRealitySync {
    pub fn detect_bim_changes(&self, 
        old_model: &UniversalBuildingModel,
        new_model: &UniversalBuildingModel
    ) -> Vec<ChangeNotification> {
        let mut notifications = Vec::new();
        
        // Detect structural changes
        let structural_changes = diff_components(&old_model.components, &new_model.components);
        
        for change in structural_changes {
            match change {
                Change::Added(component) => {
                    notifications.push(ChangeNotification {
                        change_type: ChangeType::NewComponent,
                        description: format!("New {} added at {}", 
                            component.component_type, 
                            component.geometry.centroid()),
                        requires_validation: true,
                        assigned_to: self.assign_validator(&component),
                    });
                }
                
                Change::Removed(component) => {
                    notifications.push(ChangeNotification {
                        change_type: ChangeType::ComponentRemoved,
                        description: format!("{} removed", component.id),
                        requires_validation: true,
                        assigned_to: "facility_manager",
                    });
                }
                
                Change::Modified(old, new) => {
                    let changes = describe_modifications(old, new);
                    notifications.push(ChangeNotification {
                        change_type: ChangeType::ComponentModified,
                        description: changes,
                        requires_validation: true,
                        assigned_to: self.assign_validator(&new),
                    });
                }
            }
        }
        
        notifications
    }
}
```

## 🎮 User Workflows

### Architect Workflow

```typescript
class ArchitectWorkflow {
    // Morning: Open project in Revit
    openProject("school_renovation.rvt");
    
    // Make design changes
    moveWall("Cafeteria.North", 2.0);
    addDoor("Emergency Exit", "East Wall");
    
    // Save normally - Arxos daemon detects change
    save();
    
    // Later: See validation results in Revit
    // Arxos has added comments and properties:
    // - "Wall move validated - no conflicts"
    // - "New door location has electrical panel - suggest moving 3ft south"
    
    // Architect adjusts based on reality feedback
    moveDoor("Emergency Exit", {x: original.x, y: original.y - 3});
}
```

### Facility Manager Workflow

```typescript
class FacilityManagerWorkflow {
    // Dashboard shows all BIM files and reality status
    viewDashboard() {
        return {
            buildings: [
                {
                    name: "Main Campus",
                    bim_file: "campus_master.ifc",
                    last_reality_check: "2 hours ago",
                    discrepancies: 3,
                    compliance_status: "Review needed"
                }
            ]
        };
    }
    
    // Click to see discrepancies
    viewDiscrepancies("Main Campus") {
        return [
            "Room 127: New equipment detected not in BIM",
            "Corridor B: Emergency exit blocked (violation)",
            "HVAC Zone 2: Actual capacity differs from model"
        ];
    }
    
    // Approve reality updates to flow back to BIM
    approveUpdate("Room 127", "Add new equipment to model");
}
```

### Field Worker Workflow

```typescript
class FieldWorkerWorkflow {
    // Get notification of BIM changes
    notification: "Cafeteria redesign needs field validation";
    
    // Open AR app showing both BIM design and current reality
    openARView("Cafeteria");
    
    // See overlay of proposed changes
    viewProposedChanges() {
        showAROverlay({
            current_wall: "Red outline",
            proposed_wall: "Green outline",
            new_door: "Yellow highlight"
        });
    }
    
    // Validate feasibility
    markValidation({
        wall_move: "Feasible",
        door_location: "Conflict with electrical panel",
        suggestion: "Move door 3ft south"
    });
    
    // Validation flows back to architect's Revit
}
```

## 📊 Compliance Automation

```rust
pub struct ComplianceValidator {
    pub fn validate_against_code(&self, 
        model: &UniversalBuildingModel,
        reality: &RealityCapture,
        code: BuildingCode
    ) -> ComplianceReport {
        let mut violations = Vec::new();
        
        // Check egress requirements
        for space in &model.spatial_structure.spaces {
            let exits = self.find_exits(space, model);
            let occupancy = self.calculate_occupancy(space);
            
            if exits.len() < code.required_exits(occupancy) {
                violations.push(Violation {
                    code_section: "IBC 1005.1",
                    description: format!("Insufficient exits for occupancy of {}", occupancy),
                    location: space.name.clone(),
                    severity: Severity::Critical,
                });
            }
            
            // Verify exits are actually accessible in reality
            for exit in exits {
                if let Some(reality_exit) = reality.find_component(exit.id) {
                    if reality_exit.is_blocked() {
                        violations.push(Violation {
                            code_section: "IBC 1003.6",
                            description: "Exit path blocked",
                            location: exit.location.to_string(),
                            severity: Severity::Critical,
                        });
                    }
                }
            }
        }
        
        // Check ADA compliance
        // Check fire ratings
        // Check structural modifications
        
        ComplianceReport {
            violations,
            checked_at: Utc::now(),
            code_version: code.version,
            pass: violations.is_empty(),
        }
    }
}
```

## 🔧 Configuration

```yaml
# arxos-daemon.yaml
daemon:
  mode: continuous  # or on-demand
  
watch_directories:
  - /shared/BIM/active_projects
  - /facilities/as-builts
  
file_handlers:
  pdf:
    enabled: true
    extract_text: true
    extract_geometry: true
    
  ifc:
    enabled: true
    version: IFC4
    validate_schema: true
    
  dwg:
    enabled: true
    autocad_version: 2022
    
  rvt:
    enabled: true
    revit_version: 2024
    
validation:
  auto_validate: true
  validation_interval: daily
  confidence_threshold: 0.85
  
sync:
  bidirectional: true
  update_bim: true
  require_approval: false  # Set true for manual review
  
notifications:
  email:
    - facility.manager@school.edu
  teams:
    webhook: https://...
  in_app: true
```

## 🎯 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| BIM accuracy vs reality | >95% | Validation reports |
| Time to detect changes | <1 hour | File watcher logs |
| Sync success rate | >99% | Sync reports |
| Compliance violations caught | 100% | Compliance reports |
| User adoption | >80% | Active users |

---

*"Making BIM models live and breathe with reality"*