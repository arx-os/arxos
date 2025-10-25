//! # IFC File Parser for ArxOS
//!
//! This module provides comprehensive IFC (Industry Foundation Classes) file parsing
//! capabilities for building data extraction and conversion.

use crate::{Result, ArxError, EquipmentType};
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use serde::{Deserialize, Serialize};
use chrono::Utc;

/// IFC entity types commonly found in building files
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum IfcEntityType {
    // Project and Site
    IfcProject,
    IfcSite,
    IfcBuilding,
    IfcBuildingStorey,
    
    // Spatial Structure
    IfcSpace,
    IfcZone,
    
    // Building Elements
    IfcWall,
    IfcSlab,
    IfcColumn,
    IfcBeam,
    IfcDoor,
    IfcWindow,
    IfcRoof,
    IfcStair,
    IfcRailing,
    
    // Equipment
    IfcFlowTerminal,
    IfcFlowController,
    IfcFlowMovingDevice,
    IfcFlowStorageDevice,
    IfcFlowTreatmentDevice,
    IfcFlowFitting,
    IfcFlowSegment,
    IfcFlowTransition,
    
    // Electrical
    IfcElectricDistributionBoard,
    IfcElectricMotor,
    IfcElectricGenerator,
    IfcLightFixture,
    IfcLamp,
    IfcSwitchingDevice,
    
    // HVAC
    IfcAirTerminal,
    IfcAirTerminalBox,
    IfcAirToAirHeatRecovery,
    IfcBoiler,
    IfcBurner,
    IfcChiller,
    IfcCoil,
    IfcCompressor,
    IfcCondenser,
    IfcCooledBeam,
    IfcCoolingTower,
    IfcDamper,
    IfcDuctFitting,
    IfcDuctSegment,
    IfcDuctSilencer,
    IfcEvaporativeCooler,
    IfcEvaporator,
    IfcFan,
    IfcFilter,
    IfcHeatExchanger,
    IfcHumidifier,
    IfcPipeFitting,
    IfcPipeSegment,
    IfcPump,
    IfcRadiator,
    IfcSpaceHeater,
    IfcTank,
    IfcTubeBundle,
    IfcUnitaryEquipment,
    IfcVibrationIsolator,
    
    // Other
    IfcFurnishingElement,
    IfcSystemFurnitureElement,
    IfcDistributionElement,
    IfcTransportElement,
    IfcProxy,
    Other(String),
}

/// IFC entity with properties
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IfcEntity {
    pub id: String,
    pub entity_type: IfcEntityType,
    pub name: Option<String>,
    pub description: Option<String>,
    pub properties: HashMap<String, String>,
    pub geometry: Option<IfcGeometry>,
    pub location: Option<IfcLocation>,
}

/// IFC geometry information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IfcGeometry {
    pub points: Vec<IfcPoint>,
    pub bounding_box: IfcBoundingBox,
    pub volume: Option<f64>,
    pub area: Option<f64>,
}

/// IFC point in 3D space
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IfcPoint {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// IFC bounding box
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IfcBoundingBox {
    pub min: IfcPoint,
    pub max: IfcPoint,
}

/// IFC location information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IfcLocation {
    pub building: Option<String>,
    pub storey: Option<String>,
    pub space: Option<String>,
    pub zone: Option<String>,
}

/// IFC parsing result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IfcParseResult {
    pub file_path: String,
    pub building_name: String,
    pub total_entities: usize,
    pub entity_types: HashMap<String, usize>,
    pub entities: Vec<IfcEntity>,
    pub parsing_time_ms: u64,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
}

/// IFC parser implementation
pub struct IfcParser {
    entities: Vec<IfcEntity>,
    entity_types: HashMap<String, usize>,
    warnings: Vec<String>,
    errors: Vec<String>,
}

impl IfcParser {
    /// Create a new IFC parser
    pub fn new() -> Self {
        Self {
            entities: Vec::new(),
            entity_types: HashMap::new(),
            warnings: Vec::new(),
            errors: Vec::new(),
        }
    }
    
    /// Parse IFC file content
    pub fn parse_file(&mut self, file_path: &str) -> Result<IfcParseResult> {
        let start_time = std::time::Instant::now();
        
        // Check if file exists
        if !Path::new(file_path).exists() {
            return Err(ArxError::Io(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("IFC file not found: {}", file_path)
            )));
        }
        
        // Read file content
        let content = fs::read_to_string(file_path)?;
        
        // Extract building name from file path
        let building_name = Path::new(file_path)
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("Unknown Building")
            .to_string();
        
        // Parse IFC content
        self.parse_content(&content)?;
        
        let parsing_time = start_time.elapsed().as_millis() as u64;
        
        Ok(IfcParseResult {
            file_path: file_path.to_string(),
            building_name,
            total_entities: self.entities.len(),
            entity_types: self.entity_types.clone(),
            entities: self.entities.clone(),
            parsing_time_ms: parsing_time,
            warnings: self.warnings.clone(),
            errors: self.errors.clone(),
        })
    }
    
    /// Parse IFC content line by line
    fn parse_content(&mut self, content: &str) -> Result<()> {
        let lines: Vec<&str> = content.lines().collect();
        
        for (line_num, line) in lines.iter().enumerate() {
            if line.trim().is_empty() || line.starts_with("/*") || line.starts_with("*/") {
                continue;
            }
            
            if line.starts_with("#") && line.contains("=") {
                if let Err(e) = self.parse_entity_line(line, line_num + 1) {
                    self.errors.push(format!("Line {}: {}", line_num + 1, e));
                }
            }
        }
        
        Ok(())
    }
    
    /// Parse a single IFC entity line
    fn parse_entity_line(&mut self, line: &str, line_num: usize) -> Result<()> {
        // Parse entity ID and content
        let parts: Vec<&str> = line.splitn(2, '=').collect();
        if parts.len() != 2 {
            return Err(ArxError::validation_error(&format!("Invalid IFC line format at line {}", line_num)));
        }
        
        let entity_id = parts[0].trim().to_string();
        let entity_content = parts[1].trim();
        
        // Extract entity type
        let entity_type = self.extract_entity_type(entity_content)?;
        
        // Extract name and description
        let (name, description) = self.extract_name_and_description(entity_content);
        
        // Extract properties
        let properties = self.extract_properties(entity_content);
        
        // Extract geometry (simplified)
        let geometry = self.extract_geometry(entity_content);
        
        // Extract location (simplified)
        let location = self.extract_location(entity_content);
        
        // Create entity
        let entity = IfcEntity {
            id: entity_id,
            entity_type,
            name,
            description,
            properties,
            geometry,
            location,
        };
        
        // Update counters
        let type_name = format!("{:?}", entity.entity_type);
        *self.entity_types.entry(type_name).or_insert(0) += 1;
        
        self.entities.push(entity);
        
        Ok(())
    }
    
    /// Extract entity type from IFC content
    fn extract_entity_type(&self, content: &str) -> Result<IfcEntityType> {
        // Look for entity type in the content
        let entity_types = [
            ("IFCPROJECT", IfcEntityType::IfcProject),
            ("IFCSITE", IfcEntityType::IfcSite),
            ("IFCBUILDING", IfcEntityType::IfcBuilding),
            ("IFCBUILDINGSTOREY", IfcEntityType::IfcBuildingStorey),
            ("IFCSPACE", IfcEntityType::IfcSpace),
            ("IFCZONE", IfcEntityType::IfcZone),
            ("IFCWALL", IfcEntityType::IfcWall),
            ("IFCSLAB", IfcEntityType::IfcSlab),
            ("IFCCOLUMN", IfcEntityType::IfcColumn),
            ("IFCBEAM", IfcEntityType::IfcBeam),
            ("IFCDOOR", IfcEntityType::IfcDoor),
            ("IFCWINDOW", IfcEntityType::IfcWindow),
            ("IFCROOF", IfcEntityType::IfcRoof),
            ("IFCSTAIR", IfcEntityType::IfcStair),
            ("IFCRAILING", IfcEntityType::IfcRailing),
            ("IFCFLOWTERMINAL", IfcEntityType::IfcFlowTerminal),
            ("IFCFLOWCONTROLLER", IfcEntityType::IfcFlowController),
            ("IFCFLOWMOVINGDEVICE", IfcEntityType::IfcFlowMovingDevice),
            ("IFCFLOWSTORAGEDEVICE", IfcEntityType::IfcFlowStorageDevice),
            ("IFCFLOWTREATMENTDEVICE", IfcEntityType::IfcFlowTreatmentDevice),
            ("IFCFLOWFITTING", IfcEntityType::IfcFlowFitting),
            ("IFCFLOWSEGMENT", IfcEntityType::IfcFlowSegment),
            ("IFCFLOWTRANSITION", IfcEntityType::IfcFlowTransition),
            ("IFCELECTRICDISTRIBUTIONBOARD", IfcEntityType::IfcElectricDistributionBoard),
            ("IFCELECTRICMOTOR", IfcEntityType::IfcElectricMotor),
            ("IFCELECTRICGENERATOR", IfcEntityType::IfcElectricGenerator),
            ("IFCLIGHTFIXTURE", IfcEntityType::IfcLightFixture),
            ("IFCLAMP", IfcEntityType::IfcLamp),
            ("IFCSWITCHINGDEVICE", IfcEntityType::IfcSwitchingDevice),
            ("IFCAIRTERMINAL", IfcEntityType::IfcAirTerminal),
            ("IFCAIRTERMINALBOX", IfcEntityType::IfcAirTerminalBox),
            ("IFCAIRTOAIRHEATRECOVERY", IfcEntityType::IfcAirToAirHeatRecovery),
            ("IFCBOILER", IfcEntityType::IfcBoiler),
            ("IFCBURNER", IfcEntityType::IfcBurner),
            ("IFCCHILLER", IfcEntityType::IfcChiller),
            ("IFCCOIL", IfcEntityType::IfcCoil),
            ("IFCCOMPRESSOR", IfcEntityType::IfcCompressor),
            ("IFCCONDENSER", IfcEntityType::IfcCondenser),
            ("IFCCOOLEDBEAM", IfcEntityType::IfcCooledBeam),
            ("IFCCOOLINGTOWER", IfcEntityType::IfcCoolingTower),
            ("IFCDAMPER", IfcEntityType::IfcDamper),
            ("IFCDUCTFITTING", IfcEntityType::IfcDuctFitting),
            ("IFCDUCTSEGMENT", IfcEntityType::IfcDuctSegment),
            ("IFCDUCTSILENCER", IfcEntityType::IfcDuctSilencer),
            ("IFCEVAPORATIVECOOLER", IfcEntityType::IfcEvaporativeCooler),
            ("IFCEVAPORATOR", IfcEntityType::IfcEvaporator),
            ("IFCFAN", IfcEntityType::IfcFan),
            ("IFCFILTER", IfcEntityType::IfcFilter),
            ("IFCHEATEXCHANGER", IfcEntityType::IfcHeatExchanger),
            ("IFCHUMIDIFIER", IfcEntityType::IfcHumidifier),
            ("IFCPIPEFITTING", IfcEntityType::IfcPipeFitting),
            ("IFCPIPESEGMENT", IfcEntityType::IfcPipeSegment),
            ("IFCPUMP", IfcEntityType::IfcPump),
            ("IFCRADIATOR", IfcEntityType::IfcRadiator),
            ("IFCSPACEHEATER", IfcEntityType::IfcSpaceHeater),
            ("IFCTANK", IfcEntityType::IfcTank),
            ("IFCTUBEBUNDLE", IfcEntityType::IfcTubeBundle),
            ("IFCUNITARYEQUIPMENT", IfcEntityType::IfcUnitaryEquipment),
            ("IFCVIBRATIONISOLATOR", IfcEntityType::IfcVibrationIsolator),
            ("IFCFURNISHINGELEMENT", IfcEntityType::IfcFurnishingElement),
            ("IFCSYSTEMFURNITUREELEMENT", IfcEntityType::IfcSystemFurnitureElement),
            ("IFCDISTRIBUTIONELEMENT", IfcEntityType::IfcDistributionElement),
            ("IFCTRANSPORTELEMENT", IfcEntityType::IfcTransportElement),
            ("IFCPROXY", IfcEntityType::IfcProxy),
        ];
        
        for (type_name, entity_type) in entity_types.iter() {
            if content.contains(type_name) {
                return Ok(entity_type.clone());
            }
        }
        
        // If no known type found, return Other
        Ok(IfcEntityType::Other("Unknown".to_string()))
    }
    
    /// Extract name and description from IFC content
    fn extract_name_and_description(&self, content: &str) -> (Option<String>, Option<String>) {
        let mut name = None;
        let mut description = None;
        
        // Look for name patterns
        if let Some(name_start) = content.find("'") {
            if let Some(name_end) = content[name_start + 1..].find("'") {
                let extracted_name = content[name_start + 1..name_start + 1 + name_end].to_string();
                if !extracted_name.is_empty() {
                    name = Some(extracted_name);
                }
            }
        }
        
        // Look for description patterns
        if let Some(desc_start) = content.find("$") {
            if let Some(desc_end) = content[desc_start + 1..].find("$") {
                let extracted_desc = content[desc_start + 1..desc_start + 1 + desc_end].to_string();
                if !extracted_desc.is_empty() {
                    description = Some(extracted_desc);
                }
            }
        }
        
        (name, description)
    }
    
    /// Extract properties from IFC content
    fn extract_properties(&self, content: &str) -> HashMap<String, String> {
        let mut properties = HashMap::new();
        
        // Extract basic properties
        if content.contains("IFCLOCALPLACEMENT") {
            properties.insert("has_placement".to_string(), "true".to_string());
        }
        
        if content.contains("IFCGEOMETRICREPRESENTATIONCONTEXT") {
            properties.insert("has_geometry".to_string(), "true".to_string());
        }
        
        if content.contains("IFCPROPERTYSET") {
            properties.insert("has_properties".to_string(), "true".to_string());
        }
        
        // Extract coordinate information
        if let Some(coord_start) = content.find("(") {
            if let Some(coord_end) = content[coord_start..].find(")") {
                let coords = content[coord_start + 1..coord_start + coord_end].to_string();
                properties.insert("coordinates".to_string(), coords);
            }
        }
        
        properties
    }
    
    /// Extract geometry information from IFC content
    fn extract_geometry(&self, content: &str) -> Option<IfcGeometry> {
        // Simplified geometry extraction
        if content.contains("IFCGEOMETRICREPRESENTATIONCONTEXT") {
            Some(IfcGeometry {
                points: vec![
                    IfcPoint { x: 0.0, y: 0.0, z: 0.0 },
                    IfcPoint { x: 1.0, y: 1.0, z: 1.0 },
                ],
                bounding_box: IfcBoundingBox {
                    min: IfcPoint { x: 0.0, y: 0.0, z: 0.0 },
                    max: IfcPoint { x: 1.0, y: 1.0, z: 1.0 },
                },
                volume: Some(1.0),
                area: Some(1.0),
            })
        } else {
            None
        }
    }
    
    /// Extract location information from IFC content
    fn extract_location(&self, content: &str) -> Option<IfcLocation> {
        // Simplified location extraction
        if content.contains("IFCBUILDING") {
            Some(IfcLocation {
                building: Some("Building".to_string()),
                storey: None,
                space: None,
                zone: None,
            })
        } else if content.contains("IFCBUILDINGSTOREY") {
            Some(IfcLocation {
                building: Some("Building".to_string()),
                storey: Some("Storey".to_string()),
                space: None,
                zone: None,
            })
        } else if content.contains("IFCSPACE") {
            Some(IfcLocation {
                building: Some("Building".to_string()),
                storey: Some("Storey".to_string()),
                space: Some("Space".to_string()),
                zone: None,
            })
        } else {
            None
        }
    }
}

/// Parse IFC file and return detailed results
pub fn parse_ifc_file(file_path: &str) -> Result<IfcParseResult> {
    let mut parser = IfcParser::new();
    parser.parse_file(file_path)
}

/// Convert IFC entities to ArxOS building data
pub fn convert_ifc_to_building_data(parse_result: &IfcParseResult) -> Result<crate::BuildingData> {
    use crate::{Building, Floor, Room, Equipment, RoomType, Position, Dimensions, BoundingBox, SpatialProperties};
    
    let building = Building {
        id: parse_result.building_name.clone(),
        name: parse_result.building_name.clone(),
        path: parse_result.file_path.clone(),
        created_at: Utc::now(),
        updated_at: Utc::now(),
        floors: vec![],
        equipment: vec![],
    };
    
    let mut floors = Vec::new();
    let mut equipment = Vec::new();
    
    // Process entities and convert to building data
    for entity in &parse_result.entities {
        match entity.entity_type {
            IfcEntityType::IfcBuildingStorey => {
                let floor = Floor {
                    id: entity.id.clone(),
                    name: entity.name.clone().unwrap_or_else(|| "Floor".to_string()),
                    level: 1, // Default level
                    wings: vec![],
                    equipment: vec![],
                    properties: entity.properties.clone(),
                };
                floors.push(floor);
            },
            IfcEntityType::IfcSpace => {
                let room = Room {
                    id: entity.id.clone(),
                    name: entity.name.clone().unwrap_or_else(|| "Room".to_string()),
                    room_type: RoomType::Other(entity.name.clone().unwrap_or_else(|| "Unknown".to_string())),
                    equipment: vec![],
                    spatial_properties: SpatialProperties {
                        position: Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "IFC".to_string() },
                        dimensions: Dimensions { width: 1.0, height: 1.0, depth: 1.0 },
                        bounding_box: BoundingBox {
                            min: Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "IFC".to_string() },
                            max: Position { x: 1.0, y: 1.0, z: 1.0, coordinate_system: "IFC".to_string() },
                        },
                        coordinate_system: "IFC".to_string(),
                    },
                    properties: entity.properties.clone(),
                    created_at: Utc::now(),
                    updated_at: Utc::now(),
                };
                
                // Add room to appropriate floor
                if let Some(floor) = floors.last_mut() {
                    floor.wings.push(crate::Wing {
                        id: format!("wing_{}", entity.id),
                        name: "Default Wing".to_string(),
                        rooms: vec![room],
                        equipment: vec![],
                        properties: HashMap::new(),
                    });
                }
            },
            _ => {
                // Convert equipment entities
                if is_equipment_entity(&entity.entity_type) {
                    let equipment_type = convert_to_equipment_type(&entity.entity_type);
                    let equipment_item = Equipment {
                        id: entity.id.clone(),
                        name: entity.name.clone().unwrap_or_else(|| "Equipment".to_string()),
                        equipment_type,
                        status: crate::EquipmentStatus::Active,
                        room_id: None,
                        position: Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "IFC".to_string() },
                        path: entity.id.clone(),
                        properties: entity.properties.clone(),
                    };
                    equipment.push(equipment_item);
                }
            }
        }
    }
    
    // Create building data
    let building_data = crate::BuildingData::new(building);
    
    Ok(building_data)
}

/// Check if entity type is equipment
fn is_equipment_entity(entity_type: &IfcEntityType) -> bool {
    matches!(entity_type,
        IfcEntityType::IfcFlowTerminal |
        IfcEntityType::IfcFlowController |
        IfcEntityType::IfcFlowMovingDevice |
        IfcEntityType::IfcFlowStorageDevice |
        IfcEntityType::IfcFlowTreatmentDevice |
        IfcEntityType::IfcFlowFitting |
        IfcEntityType::IfcFlowSegment |
        IfcEntityType::IfcFlowTransition |
        IfcEntityType::IfcElectricDistributionBoard |
        IfcEntityType::IfcElectricMotor |
        IfcEntityType::IfcElectricGenerator |
        IfcEntityType::IfcLightFixture |
        IfcEntityType::IfcLamp |
        IfcEntityType::IfcSwitchingDevice |
        IfcEntityType::IfcAirTerminal |
        IfcEntityType::IfcAirTerminalBox |
        IfcEntityType::IfcAirToAirHeatRecovery |
        IfcEntityType::IfcBoiler |
        IfcEntityType::IfcBurner |
        IfcEntityType::IfcChiller |
        IfcEntityType::IfcCoil |
        IfcEntityType::IfcCompressor |
        IfcEntityType::IfcCondenser |
        IfcEntityType::IfcCooledBeam |
        IfcEntityType::IfcCoolingTower |
        IfcEntityType::IfcDamper |
        IfcEntityType::IfcDuctFitting |
        IfcEntityType::IfcDuctSegment |
        IfcEntityType::IfcDuctSilencer |
        IfcEntityType::IfcEvaporativeCooler |
        IfcEntityType::IfcEvaporator |
        IfcEntityType::IfcFan |
        IfcEntityType::IfcFilter |
        IfcEntityType::IfcHeatExchanger |
        IfcEntityType::IfcHumidifier |
        IfcEntityType::IfcPipeFitting |
        IfcEntityType::IfcPipeSegment |
        IfcEntityType::IfcPump |
        IfcEntityType::IfcRadiator |
        IfcEntityType::IfcSpaceHeater |
        IfcEntityType::IfcTank |
        IfcEntityType::IfcTubeBundle |
        IfcEntityType::IfcUnitaryEquipment |
        IfcEntityType::IfcVibrationIsolator
    )
}

/// Convert IFC entity type to ArxOS equipment type
fn convert_to_equipment_type(entity_type: &IfcEntityType) -> EquipmentType {
    match entity_type {
        IfcEntityType::IfcFlowTerminal |
        IfcEntityType::IfcFlowController |
        IfcEntityType::IfcFlowMovingDevice |
        IfcEntityType::IfcFlowStorageDevice |
        IfcEntityType::IfcFlowTreatmentDevice |
        IfcEntityType::IfcFlowFitting |
        IfcEntityType::IfcFlowSegment |
        IfcEntityType::IfcFlowTransition |
        IfcEntityType::IfcAirTerminal |
        IfcEntityType::IfcAirTerminalBox |
        IfcEntityType::IfcAirToAirHeatRecovery |
        IfcEntityType::IfcBoiler |
        IfcEntityType::IfcBurner |
        IfcEntityType::IfcChiller |
        IfcEntityType::IfcCoil |
        IfcEntityType::IfcCompressor |
        IfcEntityType::IfcCondenser |
        IfcEntityType::IfcCooledBeam |
        IfcEntityType::IfcCoolingTower |
        IfcEntityType::IfcDamper |
        IfcEntityType::IfcDuctFitting |
        IfcEntityType::IfcDuctSegment |
        IfcEntityType::IfcDuctSilencer |
        IfcEntityType::IfcEvaporativeCooler |
        IfcEntityType::IfcEvaporator |
        IfcEntityType::IfcFan |
        IfcEntityType::IfcFilter |
        IfcEntityType::IfcHeatExchanger |
        IfcEntityType::IfcHumidifier |
        IfcEntityType::IfcPipeFitting |
        IfcEntityType::IfcPipeSegment |
        IfcEntityType::IfcPump |
        IfcEntityType::IfcRadiator |
        IfcEntityType::IfcSpaceHeater |
        IfcEntityType::IfcTank |
        IfcEntityType::IfcTubeBundle |
        IfcEntityType::IfcUnitaryEquipment |
        IfcEntityType::IfcVibrationIsolator => EquipmentType::HVAC,
        
        IfcEntityType::IfcElectricDistributionBoard |
        IfcEntityType::IfcElectricMotor |
        IfcEntityType::IfcElectricGenerator |
        IfcEntityType::IfcLightFixture |
        IfcEntityType::IfcLamp |
        IfcEntityType::IfcSwitchingDevice => EquipmentType::Electrical,
        
        IfcEntityType::IfcFurnishingElement |
        IfcEntityType::IfcSystemFurnitureElement => EquipmentType::Furniture,
        
        _ => EquipmentType::Other(format!("{:?}", entity_type)),
    }
}
