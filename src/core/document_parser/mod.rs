//! Document Parser for PDF and IFC Files
//! 
//! Converts architectural documents to ASCII building models

pub mod pdf_parser;
pub mod ifc_parser;
pub mod ascii_renderer;
pub mod symbol_detector;

#[cfg(test)]
mod tests;

use crate::arxobject::ArxObject;
use std::path::Path;
use thiserror::Error;

/// Document parser errors
#[derive(Error, Debug)]
pub enum ParseError {
    #[error("Unsupported file format: {0}")]
    UnsupportedFormat(String),
    
    #[error("PDF parsing error: {0}")]
    PdfError(String),
    
    #[error("IFC parsing error: {0}")]
    IfcError(String),
    
    #[error("OCR error: {0}")]
    OcrError(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Image processing error: {0}")]
    ImageError(String),
}

/// Building plan extracted from documents
#[derive(Debug, Clone)]
pub struct BuildingPlan {
    pub name: String,
    pub floors: Vec<FloorPlan>,
    pub arxobjects: Vec<ArxObject>,
    pub metadata: BuildingMetadata,
}

/// Single floor plan
#[derive(Debug, Clone)]
pub struct FloorPlan {
    pub floor_number: i8,
    pub rooms: Vec<Room>,
    pub ascii_layout: String,
    pub equipment: Vec<Equipment>,
}

/// Room information
#[derive(Debug, Clone)]
pub struct Room {
    pub number: String,
    pub name: String,
    pub area_sqft: f32,
    pub bounds: BoundingBox,
    pub equipment_count: u32,
}

/// Equipment found in documents
#[derive(Debug, Clone)]
pub struct Equipment {
    pub equipment_type: EquipmentType,
    pub location: Point3D,
    pub room_number: Option<String>,
    pub properties: std::collections::HashMap<String, String>,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum EquipmentType {
    ElectricalOutlet,
    LightFixture,
    HvacVent,
    FireAlarm,
    SmokeDetector,
    EmergencyExit,
    Thermostat,
    Switch,
    DataPort,
    SecurityCamera,
    Sprinkler,
    Door,
    Window,
}

/// 3D point
#[derive(Debug, Clone, Copy)]
pub struct Point3D {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

/// Bounding box
#[derive(Debug, Clone, Copy)]
pub struct BoundingBox {
    pub min: Point3D,
    pub max: Point3D,
}

/// Building metadata
#[derive(Debug, Clone)]
pub struct BuildingMetadata {
    pub address: Option<String>,
    pub total_sqft: f32,
    pub year_built: Option<u16>,
    pub building_type: Option<String>,
    pub occupancy_class: Option<String>,
}

/// Main document parser interface
pub struct DocumentParser {
    pdf_parser: pdf_parser::PdfParser,
    ifc_parser: ifc_parser::IfcParser,
    renderer: ascii_renderer::AsciiRenderer,
}

impl DocumentParser {
    /// Create new document parser
    pub fn new() -> Self {
        Self {
            pdf_parser: pdf_parser::PdfParser::new(),
            ifc_parser: ifc_parser::IfcParser::new(),
            renderer: ascii_renderer::AsciiRenderer::new(),
        }
    }
    
    /// Parse any supported document type
    pub async fn parse_document(&mut self, file_path: &str) -> Result<BuildingPlan, ParseError> {
        let path = Path::new(file_path);
        let extension = path.extension()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_lowercase();
        
        match extension.as_str() {
            "pdf" => self.pdf_parser.parse(file_path).await,
            "ifc" | "ifcxml" => self.ifc_parser.parse(file_path).await,
            _ => Err(ParseError::UnsupportedFormat(extension)),
        }
    }
    
    /// Convert building plan to ArxObjects
    pub fn to_arxobjects(&self, plan: &BuildingPlan) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        
        for floor in &plan.floors {
            for equipment in &floor.equipment {
                let obj = self.equipment_to_arxobject(equipment, floor.floor_number);
                objects.push(obj);
            }
        }
        
        objects
    }
    
    /// Convert equipment to ArxObject
    fn equipment_to_arxobject(&self, equipment: &Equipment, floor: i8) -> ArxObject {
        use crate::object_types;
        
        let object_type = match equipment.equipment_type {
            EquipmentType::ElectricalOutlet => object_types::OUTLET,
            EquipmentType::LightFixture => object_types::LIGHT,
            EquipmentType::HvacVent => object_types::HVAC_VENT,
            EquipmentType::FireAlarm => object_types::FIRE_ALARM,
            EquipmentType::SmokeDetector => object_types::SMOKE_DETECTOR,
            EquipmentType::EmergencyExit => object_types::EMERGENCY_EXIT,
            EquipmentType::Thermostat => object_types::THERMOSTAT,
            _ => object_types::GENERIC,
        };
        
        ArxObject::new(
            0x0001,  // Building ID (would be assigned)
            object_type,
            (equipment.location.x * 1000.0) as i16,  // Convert to mm
            (equipment.location.y * 1000.0) as i16,
            (equipment.location.z * 1000.0) as i16,
        )
    }
    
    /// Generate ASCII representation
    pub fn generate_ascii(&self, plan: &BuildingPlan) -> String {
        self.renderer.render_building(plan)
    }
}

impl EquipmentType {
    /// Get ASCII symbol for equipment type
    pub fn to_ascii_symbol(&self) -> &'static str {
        match self {
            EquipmentType::ElectricalOutlet => "[O]",
            EquipmentType::LightFixture => "[L]",
            EquipmentType::HvacVent => "[V]",
            EquipmentType::FireAlarm => "[F]",
            EquipmentType::SmokeDetector => "[S]",
            EquipmentType::EmergencyExit => "[E]",
            EquipmentType::Thermostat => "[T]",
            EquipmentType::Switch => "[/]",
            EquipmentType::DataPort => "[D]",
            EquipmentType::SecurityCamera => "[C]",
            EquipmentType::Sprinkler => "[*]",
            EquipmentType::Door => "| |",
            EquipmentType::Window => "[-]",
        }
    }
}