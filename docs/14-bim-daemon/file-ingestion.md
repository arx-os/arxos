# File Ingestion Specifications

## Processing Building Data from Multiple Formats

Arxos ingests building information from various file formats, extracting spatial structure, metadata, and semantic information to bootstrap building intelligence.

## Supported Formats

### 1. PDF - Architectural Drawings

```rust
pub struct PdfProcessor {
    supported_types: vec![
        "Floor plans",
        "Elevations", 
        "Sections",
        "Room schedules",
        "Equipment schedules",
        "Electrical plans",
        "Mechanical plans",
        "Plumbing plans",
        "Fire safety plans",
    ],
    
    extraction_capabilities: vec![
        "OCR text extraction",
        "Vector graphics parsing",
        "Raster image processing",
        "Table detection",
        "Symbol recognition",
        "Dimension extraction",
        "Layer separation",
    ],
}
```

#### PDF Processing Pipeline

```rust
pub fn process_pdf(pdf_bytes: &[u8]) -> Result<BuildingIntelligence> {
    // 1. Page Classification
    let pages = pdf::extract_pages(pdf_bytes)?;
    let classified = pages.iter().map(|page| {
        ClassifiedPage {
            page_number: page.number,
            drawing_type: classify_drawing_type(page),
            scale: extract_scale(page),
            title_block: extract_title_block(page),
        }
    }).collect();
    
    // 2. Floor Plan Processing
    let floor_plans = classified.iter()
        .filter(|p| p.drawing_type == DrawingType::FloorPlan)
        .map(|p| process_floor_plan(p))
        .collect::<Result<Vec<_>>>()?;
    
    // 3. Room Extraction
    let rooms = floor_plans.iter()
        .flat_map(|plan| extract_rooms(plan))
        .collect::<Vec<_>>();
    
    // 4. Text Extraction and Correlation
    let text_elements = extract_all_text(&pages)?;
    let room_labels = correlate_text_to_rooms(&text_elements, &rooms)?;
    
    // 5. Schedule Parsing
    let schedules = extract_schedules(&pages)?;
    let room_schedule = schedules.get("room_schedule");
    let door_schedule = schedules.get("door_schedule");
    let equipment_schedule = schedules.get("equipment_schedule");
    
    // 6. System Extraction
    let electrical = extract_electrical_system(&classified)?;
    let mechanical = extract_mechanical_system(&classified)?;
    let plumbing = extract_plumbing_system(&classified)?;
    
    Ok(BuildingIntelligence {
        structure: BuildingStructure {
            floors: floor_plans,
            rooms: enrich_rooms_with_schedules(rooms, room_schedule),
        },
        systems: BuildingSystems {
            electrical,
            mechanical,
            plumbing,
        },
        metadata: extract_project_metadata(&pages[0]),
    })
}
```

#### OCR and Text Extraction

```rust
pub struct TextExtractor {
    pub fn extract_room_numbers(&self, image: &DynamicImage) -> Vec<RoomLabel> {
        // Use Tesseract or cloud OCR
        let ocr_result = tesseract::ocr(image, "eng")?;
        
        // Parse room number patterns
        let room_pattern = Regex::new(r"(?i)(room|rm)?\s*([A-Z]?\d{2,4}[A-Z]?)")?;
        
        ocr_result.lines()
            .filter_map(|line| {
                if let Some(captures) = room_pattern.captures(line.text) {
                    Some(RoomLabel {
                        number: captures[2].to_string(),
                        position: line.bounding_box.center(),
                        confidence: line.confidence,
                    })
                } else {
                    None
                }
            })
            .collect()
    }
    
    pub fn extract_dimensions(&self, drawing: &Drawing) -> Vec<Dimension> {
        // Look for dimension lines and text
        let dim_pattern = Regex::new(r"(\d+)['\"]?\s*-\s*(\d+)['\"]?")?;
        
        drawing.text_elements.iter()
            .filter_map(|text| {
                if let Some(captures) = dim_pattern.captures(&text.content) {
                    Some(Dimension {
                        feet: captures[1].parse().ok()?,
                        inches: captures[2].parse().ok()?,
                        position: text.position,
                    })
                } else {
                    None
                }
            })
            .collect()
    }
}
```

### 2. IFC - Industry Foundation Classes

```rust
pub struct IfcProcessor {
    supported_versions: vec!["IFC2x3", "IFC4", "IFC4.1", "IFC4.2"],
    
    extracted_elements: vec![
        "IfcProject",
        "IfcSite", 
        "IfcBuilding",
        "IfcBuildingStorey",
        "IfcSpace",
        "IfcWall",
        "IfcDoor",
        "IfcWindow",
        "IfcSlab",
        "IfcRoof",
        "IfcColumn",
        "IfcBeam",
        "IfcStair",
        "IfcBuildingElementProxy", // Generic equipment
        "IfcFurnishingElement",
        "IfcDistributionElement",  // MEP equipment
    ],
}
```

#### IFC Processing Pipeline

```rust
pub fn process_ifc(file_path: &Path) -> Result<UniversalBuildingModel> {
    let ifc = IfcDocument::open(file_path)?;
    
    // 1. Extract Project Structure
    let project = ifc.project()?;
    let units = extract_units(&project)?;
    let north = extract_true_north(&project)?;
    
    // 2. Spatial Hierarchy
    let sites = ifc.instances_of::<IfcSite>()?;
    let buildings = ifc.instances_of::<IfcBuilding>()?;
    let storeys = ifc.instances_of::<IfcBuildingStorey>()?;
    let spaces = ifc.instances_of::<IfcSpace>()?;
    
    // 3. Building Elements
    let elements = extract_building_elements(&ifc)?;
    
    // 4. Properties and Quantities
    let property_sets = extract_property_sets(&ifc)?;
    let quantities = extract_quantities(&ifc)?;
    
    // 5. Relationships
    let spatial_containment = extract_spatial_containment(&ifc)?;
    let element_connections = extract_connections(&ifc)?;
    
    // 6. Systems and Zones
    let systems = extract_building_systems(&ifc)?;
    let zones = extract_zones(&ifc)?;
    
    // Convert to universal model
    Ok(UniversalBuildingModel {
        metadata: BuildingMetadata {
            name: project.name,
            address: extract_address(&sites[0]),
            units,
            north_direction: north,
        },
        spatial_structure: build_hierarchy(buildings, storeys, spaces),
        components: convert_ifc_to_components(elements, property_sets),
        systems: convert_ifc_systems(systems),
        zones: convert_ifc_zones(zones),
        relationships: merge_relationships(spatial_containment, element_connections),
    })
}

// Property extraction
pub fn extract_properties(element: &IfcElement) -> HashMap<String, Value> {
    let mut properties = HashMap::new();
    
    // Direct attributes
    properties.insert("Name", element.name.into());
    properties.insert("Description", element.description.into());
    properties.insert("ObjectType", element.object_type.into());
    
    // Property sets
    for pset in element.property_sets() {
        for property in pset.properties() {
            match property {
                IfcProperty::SingleValue(name, value) => {
                    properties.insert(name, convert_ifc_value(value));
                }
                IfcProperty::EnumeratedValue(name, value) => {
                    properties.insert(name, value.to_string().into());
                }
                IfcProperty::BoundedValue(name, lower, upper) => {
                    properties.insert(format!("{}_min", name), lower.into());
                    properties.insert(format!("{}_max", name), upper.into());
                }
                _ => {}
            }
        }
    }
    
    // Quantities
    for qset in element.quantity_sets() {
        for quantity in qset.quantities() {
            match quantity {
                IfcQuantity::Length(name, value) => {
                    properties.insert(name, value.into());
                }
                IfcQuantity::Area(name, value) => {
                    properties.insert(name, value.into());
                }
                IfcQuantity::Volume(name, value) => {
                    properties.insert(name, value.into());
                }
                _ => {}
            }
        }
    }
    
    properties
}
```

### 3. DWG/DXF - AutoCAD

```rust
pub struct DwgProcessor {
    supported_versions: vec![
        "AutoCAD 2018",
        "AutoCAD 2021", 
        "AutoCAD 2024",
    ],
    
    layer_conventions: LayerConventions {
        architectural: vec!["A-WALL", "A-DOOR", "A-GLAZ"],
        electrical: vec!["E-POWR", "E-LITE", "E-FIRE"],
        mechanical: vec!["M-HVAC", "M-DUCT", "M-PIPE"],
        plumbing: vec!["P-FIXT", "P-PIPE", "P-EQUIP"],
    },
}
```

#### DWG Processing Pipeline

```rust
pub fn process_dwg(file_path: &Path) -> Result<CadDrawing> {
    let dwg = DwgDocument::open(file_path)?;
    
    // 1. Extract Layers
    let layers = dwg.layers()
        .map(|layer| {
            Layer {
                name: layer.name.clone(),
                color: layer.color,
                line_type: layer.line_type.clone(),
                entities: extract_layer_entities(&dwg, &layer),
            }
        })
        .collect::<Vec<_>>();
    
    // 2. Process Architectural Elements
    let walls = extract_walls(&layers)?;
    let doors = extract_doors(&layers)?;
    let windows = extract_windows(&layers)?;
    let rooms = extract_room_polylines(&layers)?;
    
    // 3. Extract Text and Annotations
    let text_entities = dwg.entities()
        .filter_map(|e| match e {
            Entity::Text(t) => Some(TextAnnotation {
                content: t.text_string.clone(),
                position: Point2D::new(t.insertion_point.x, t.insertion_point.y),
                height: t.height,
                rotation: t.rotation,
            }),
            Entity::MText(mt) => Some(TextAnnotation {
                content: mt.text.clone(),
                position: Point2D::new(mt.insertion_point.x, mt.insertion_point.y),
                height: mt.height,
                rotation: mt.rotation,
            }),
            _ => None,
        })
        .collect::<Vec<_>>();
    
    // 4. Extract Blocks (reusable symbols)
    let blocks = extract_block_references(&dwg)?;
    let equipment = identify_equipment_blocks(&blocks)?;
    
    // 5. Extract Dimensions
    let dimensions = extract_dimensions(&dwg)?;
    
    // 6. Build spatial model
    Ok(CadDrawing {
        units: extract_units(&dwg),
        layers,
        walls,
        doors,
        windows,
        rooms: correlate_rooms_with_labels(rooms, text_entities),
        equipment,
        dimensions,
        coordinate_system: extract_coordinate_system(&dwg),
    })
}

// Symbol recognition for equipment
pub fn identify_equipment_blocks(blocks: &[BlockReference]) -> Vec<Equipment> {
    blocks.iter()
        .filter_map(|block| {
            match block.name.to_uppercase().as_str() {
                name if name.contains("OUTLET") => Some(Equipment {
                    equipment_type: EquipmentType::ElectricalOutlet,
                    position: block.insertion_point,
                    rotation: block.rotation,
                    attributes: block.attributes.clone(),
                }),
                name if name.contains("SWITCH") => Some(Equipment {
                    equipment_type: EquipmentType::LightSwitch,
                    position: block.insertion_point,
                    rotation: block.rotation,
                    attributes: block.attributes.clone(),
                }),
                name if name.contains("HVAC") | name.contains("VAV") => Some(Equipment {
                    equipment_type: EquipmentType::HvacUnit,
                    position: block.insertion_point,
                    rotation: block.rotation,
                    attributes: block.attributes.clone(),
                }),
                _ => None,
            }
        })
        .collect()
}
```

### 4. Revit Integration

```rust
pub struct RevitProcessor {
    api_version: "2024",
    
    extracted_categories: vec![
        "Walls",
        "Doors",
        "Windows",
        "Rooms",
        "Floors",
        "Ceilings",
        "Roofs",
        "Stairs",
        "Furniture",
        "Mechanical Equipment",
        "Electrical Equipment",
        "Plumbing Fixtures",
    ],
}
```

#### Revit Processing via IFC Export

```rust
pub fn process_revit(rvt_path: &Path) -> Result<UniversalBuildingModel> {
    // Option 1: Use Revit API (requires Revit installation)
    if revit_api_available() {
        return process_via_revit_api(rvt_path);
    }
    
    // Option 2: Export to IFC and process
    let ifc_path = export_revit_to_ifc(rvt_path)?;
    let model = process_ifc(&ifc_path)?;
    
    // Preserve Revit-specific metadata
    let revit_metadata = extract_revit_metadata(rvt_path)?;
    model.metadata.merge(revit_metadata);
    
    Ok(model)
}

// Direct Revit API access (when available)
#[cfg(windows)]
pub fn process_via_revit_api(rvt_path: &Path) -> Result<UniversalBuildingModel> {
    use revit_api::*;
    
    let app = Application::launch()?;
    let doc = app.open_document(rvt_path)?;
    
    // Extract elements
    let collector = FilteredElementCollector::new(&doc);
    
    let walls = collector
        .of_class(WallType)
        .where_element_is_not_element_type()
        .to_elements();
        
    let rooms = collector
        .of_category(BuiltInCategory::Rooms)
        .to_elements();
    
    // Convert to universal model
    // ...
    
    Ok(model)
}
```

## Coordinate System Alignment

```rust
pub struct CoordinateAlignment {
    /// Align imported model with reality capture
    pub fn align_to_reality(
        imported_model: &ImportedModel,
        reality_scan: &RealityScan
    ) -> AlignmentTransform {
        // 1. Find common reference points
        let reference_points = find_reference_points(imported_model, reality_scan);
        
        // 2. Calculate transformation matrix
        let transform = calculate_best_fit_transform(&reference_points)?;
        
        // 3. Validate alignment quality
        let alignment_error = calculate_alignment_error(&transform, &reference_points);
        
        if alignment_error > ACCEPTABLE_ERROR {
            // Try alternative alignment strategies
            transform = try_alternative_alignment(imported_model, reality_scan)?;
        }
        
        AlignmentTransform {
            translation: transform.translation,
            rotation: transform.rotation,
            scale: transform.scale,
            confidence: 1.0 - (alignment_error / MAX_ERROR),
        }
    }
    
    /// Find matching features between model and scan
    fn find_reference_points(
        model: &ImportedModel,
        scan: &RealityScan
    ) -> Vec<ReferencePointPair> {
        let mut pairs = Vec::new();
        
        // Match corners
        for model_corner in model.detect_corners() {
            if let Some(scan_corner) = scan.find_nearest_corner(&model_corner, MAX_DISTANCE) {
                pairs.push(ReferencePointPair {
                    model_point: model_corner,
                    scan_point: scan_corner,
                    confidence: calculate_match_confidence(&model_corner, &scan_corner),
                });
            }
        }
        
        // Match doors
        for model_door in model.doors() {
            if let Some(scan_door) = scan.find_matching_door(&model_door) {
                pairs.push(ReferencePointPair {
                    model_point: model_door.center(),
                    scan_point: scan_door.center(),
                    confidence: 0.9,
                });
            }
        }
        
        pairs
    }
}
```

## Validation After Import

```rust
pub struct ImportValidation {
    /// Validate imported model against expectations
    pub fn validate_import(imported: &ImportedModel) -> ValidationReport {
        let mut issues = Vec::new();
        
        // Check for required elements
        if imported.rooms.is_empty() {
            issues.push(ValidationIssue {
                severity: Severity::Error,
                message: "No rooms detected in import".to_string(),
            });
        }
        
        // Check coordinate system
        if !imported.has_valid_coordinates() {
            issues.push(ValidationIssue {
                severity: Severity::Warning,
                message: "Coordinate system may need manual alignment".to_string(),
            });
        }
        
        // Check scale
        let avg_room_size = calculate_average_room_size(&imported.rooms);
        if avg_room_size < 10.0 || avg_room_size > 1000.0 {
            issues.push(ValidationIssue {
                severity: Severity::Warning,
                message: format!("Unusual room sizes detected: {}sqm average", avg_room_size),
            });
        }
        
        // Check for orphaned elements
        let orphaned = find_orphaned_elements(imported);
        if !orphaned.is_empty() {
            issues.push(ValidationIssue {
                severity: Severity::Info,
                message: format!("{} elements not assigned to rooms", orphaned.len()),
            });
        }
        
        ValidationReport {
            success: issues.iter().all(|i| i.severity != Severity::Error),
            issues,
            statistics: ImportStatistics {
                rooms_imported: imported.rooms.len(),
                walls_imported: imported.walls.len(),
                equipment_imported: imported.equipment.len(),
                systems_detected: imported.systems.len(),
            },
        }
    }
}
```

## Incremental Updates

```rust
pub struct IncrementalIngestion {
    /// Process only changes since last import
    pub fn process_incremental(
        file_path: &Path,
        last_import: DateTime<Utc>
    ) -> Result<IncrementalUpdate> {
        let file_modified = fs::metadata(file_path)?.modified()?;
        
        if file_modified <= last_import {
            return Ok(IncrementalUpdate::NoChanges);
        }
        
        // Load previous state
        let previous = load_previous_import(file_path)?;
        
        // Process current file
        let current = process_file(file_path)?;
        
        // Calculate differences
        let changes = diff_models(&previous, &current);
        
        Ok(IncrementalUpdate::Changes(changes))
    }
}
```

---

*"Turning static files into living building intelligence"*