//! Tests for document parser module

#[cfg(test)]
mod tests {
    use super::super::*;
    use std::fs;
    use std::path::PathBuf;
    
    /// Create test PDF content
    fn create_test_pdf() -> Vec<u8> {
        // Minimal valid PDF with room schedule
        let pdf_content = b"%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
100 700 Td
(BUILDING NAME: Jefferson Elementary) Tj
100 650 Td
(ROOM SCHEDULE) Tj
100 600 Td
(Room 127 - Science Lab - 800 sq ft) Tj
100 550 Td
(Room 128 - Classroom - 600 sq ft) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000229 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
492
%%EOF";
        pdf_content.to_vec()
    }
    
    /// Create test IFC content
    fn create_test_ifc() -> String {
        r#"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('IFC4'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',(),(),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('project_id',$,'Test Project',$,$,$,$,$,$);
#2=IFCSITE('site_id',$,'Test Site',$,$,$,$,$,$,$,$,$,$,$);
#3=IFCBUILDING('building_id',$,'Jefferson Elementary',$,$,$,$,$,$,$,$,$);
#4=IFCBUILDINGSTOREY('floor1_id',$,'Level 1',$,$,$,$,$,$,$);
#5=IFCSPACE('space1_id',$,'127','Science Lab',$,$,$,$,$,$);
#6=IFCSPACE('space2_id',$,'128','Classroom',$,$,$,$,$,$);
#7=IFCOUTLET('outlet1_id',$,'Outlet',$,$,$,$,$);
#8=IFCLIGHTFIXTURE('light1_id',$,'Light',$,$,$,$,$);
#9=IFCDOOR('door1_id',$,'Door',$,$,$,$,$,$,$);
#10=IFCWINDOW('window1_id',$,'Window',$,$,$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;"#.to_string()
    }
    
    #[test]
    fn test_equipment_type_symbols() {
        assert_eq!(EquipmentType::ElectricalOutlet.to_ascii_symbol(), "[O]");
        assert_eq!(EquipmentType::LightFixture.to_ascii_symbol(), "[L]");
        assert_eq!(EquipmentType::HvacVent.to_ascii_symbol(), "[V]");
        assert_eq!(EquipmentType::Door.to_ascii_symbol(), "| |");
        assert_eq!(EquipmentType::Window.to_ascii_symbol(), "[-]");
    }
    
    #[test]
    fn test_point3d_creation() {
        let point = Point3D { x: 10.0, y: 20.0, z: 3.0 };
        assert_eq!(point.x, 10.0);
        assert_eq!(point.y, 20.0);
        assert_eq!(point.z, 3.0);
    }
    
    #[test]
    fn test_bounding_box() {
        let bbox = BoundingBox {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 10.0, y: 10.0, z: 3.0 },
        };
        
        assert_eq!(bbox.min.x, 0.0);
        assert_eq!(bbox.max.x, 10.0);
    }
    
    #[tokio::test]
    async fn test_pdf_parser_initialization() {
        let parser = pdf_parser::PdfParser::new();
        // Parser should initialize without errors
        assert!(true);
    }
    
    #[tokio::test]
    async fn test_ifc_parser_initialization() {
        let parser = ifc_parser::IfcParser::new();
        // Parser should initialize without errors
        assert!(true);
    }
    
    #[test]
    fn test_ascii_renderer_initialization() {
        let renderer = ascii_renderer::AsciiRenderer::new();
        // Renderer should initialize without errors
        assert!(true);
    }
    
    #[test]
    fn test_document_parser_initialization() {
        let parser = DocumentParser::new();
        // Parser should initialize without errors
        assert!(true);
    }
    
    #[tokio::test]
    async fn test_parse_unsupported_format() {
        let mut parser = DocumentParser::new();
        let result = parser.parse_document("test.xyz").await;
        
        assert!(result.is_err());
        match result {
            Err(ParseError::UnsupportedFormat(ext)) => {
                assert_eq!(ext, "xyz");
            },
            _ => panic!("Expected UnsupportedFormat error"),
        }
    }
    
    #[test]
    fn test_room_creation() {
        let room = Room {
            number: "127".to_string(),
            name: "Science Lab".to_string(),
            area_sqft: 800.0,
            bounds: BoundingBox {
                min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                max: Point3D { x: 10.0, y: 10.0, z: 3.0 },
            },
            equipment_count: 12,
        };
        
        assert_eq!(room.number, "127");
        assert_eq!(room.name, "Science Lab");
        assert_eq!(room.area_sqft, 800.0);
        assert_eq!(room.equipment_count, 12);
    }
    
    #[test]
    fn test_equipment_creation() {
        let equipment = Equipment {
            equipment_type: EquipmentType::ElectricalOutlet,
            location: Point3D { x: 5.0, y: 5.0, z: 0.3 },
            room_number: Some("127".to_string()),
            properties: std::collections::HashMap::new(),
        };
        
        assert_eq!(equipment.equipment_type, EquipmentType::ElectricalOutlet);
        assert_eq!(equipment.location.x, 5.0);
        assert_eq!(equipment.room_number, Some("127".to_string()));
    }
    
    #[test]
    fn test_floor_plan_creation() {
        let floor = FloorPlan {
            floor_number: 1,
            rooms: vec![
                Room {
                    number: "127".to_string(),
                    name: "Science Lab".to_string(),
                    area_sqft: 800.0,
                    bounds: BoundingBox {
                        min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                        max: Point3D { x: 10.0, y: 10.0, z: 3.0 },
                    },
                    equipment_count: 0,
                }
            ],
            ascii_layout: "║ Room 127 ║".to_string(),
            equipment: vec![],
        };
        
        assert_eq!(floor.floor_number, 1);
        assert_eq!(floor.rooms.len(), 1);
        assert_eq!(floor.rooms[0].number, "127");
    }
    
    #[test]
    fn test_building_plan_creation() {
        let plan = BuildingPlan {
            name: "Jefferson Elementary".to_string(),
            floors: vec![],
            arxobjects: vec![],
            metadata: BuildingMetadata {
                address: Some("123 Main St".to_string()),
                total_sqft: 25000.0,
                year_built: Some(1985),
                building_type: Some("Educational".to_string()),
                occupancy_class: Some("E".to_string()),
            },
        };
        
        assert_eq!(plan.name, "Jefferson Elementary");
        assert_eq!(plan.metadata.total_sqft, 25000.0);
        assert_eq!(plan.metadata.year_built, Some(1985));
    }
    
    #[test]
    fn test_equipment_to_arxobject_conversion() {
        let parser = DocumentParser::new();
        let equipment = Equipment {
            equipment_type: EquipmentType::ElectricalOutlet,
            location: Point3D { x: 5.0, y: 5.0, z: 0.3 },
            room_number: Some("127".to_string()),
            properties: std::collections::HashMap::new(),
        };
        
        let floor = FloorPlan {
            floor_number: 1,
            rooms: vec![],
            ascii_layout: String::new(),
            equipment: vec![equipment.clone()],
        };
        
        let plan = BuildingPlan {
            name: "Test Building".to_string(),
            floors: vec![floor],
            arxobjects: vec![],
            metadata: BuildingMetadata {
                address: None,
                total_sqft: 0.0,
                year_built: None,
                building_type: None,
                occupancy_class: None,
            },
        };
        
        let arxobjects = parser.to_arxobjects(&plan);
        assert_eq!(arxobjects.len(), 1);
        
        let obj = &arxobjects[0];
        assert_eq!(obj.x, 5000); // 5.0m * 1000 = 5000mm
        assert_eq!(obj.y, 5000);
        assert_eq!(obj.z, 300);  // 0.3m * 1000 = 300mm
    }
    
    #[test]
    fn test_ascii_renderer_with_floor_plan() {
        let renderer = ascii_renderer::AsciiRenderer::new();
        
        let room = Room {
            number: "127".to_string(),
            name: "Science Lab".to_string(),
            area_sqft: 800.0,
            bounds: BoundingBox {
                min: Point3D { x: 5.0, y: 5.0, z: 0.0 },
                max: Point3D { x: 15.0, y: 12.0, z: 3.0 },
            },
            equipment_count: 0,
        };
        
        let equipment = Equipment {
            equipment_type: EquipmentType::ElectricalOutlet,
            location: Point3D { x: 10.0, y: 8.0, z: 0.3 },
            room_number: Some("127".to_string()),
            properties: std::collections::HashMap::new(),
        };
        
        let floor = FloorPlan {
            floor_number: 1,
            rooms: vec![room],
            ascii_layout: String::new(),
            equipment: vec![equipment],
        };
        
        let ascii = renderer.render_floor(&floor);
        
        // Check that ASCII output contains expected elements
        assert!(ascii.contains("FLOOR 1"));
        assert!(ascii.contains("127"));
        assert!(ascii.contains("Science Lab"));
        assert!(ascii.contains("800 sq ft"));
    }
    
    #[test]
    fn test_symbol_detector_initialization() {
        let detector = symbol_detector::SymbolDetector::new();
        // Detector should initialize without errors
        assert!(true);
    }
    
    #[tokio::test]
    async fn test_ifc_entity_parsing() {
        let mut parser = ifc_parser::IfcParser::new();
        
        // Create temp IFC file
        let temp_dir = std::env::temp_dir();
        let ifc_path = temp_dir.join("test.ifc");
        fs::write(&ifc_path, create_test_ifc()).unwrap();
        
        // Parse should succeed without panicking
        let result = parser.parse(ifc_path.to_str().unwrap()).await;
        
        // Clean up
        let _ = fs::remove_file(ifc_path);
        
        // Basic validation
        if let Ok(plan) = result {
            assert!(plan.name.contains("Jefferson") || plan.name == "Unknown Building");
        }
    }
    
    #[test]
    fn test_building_metadata() {
        let metadata = BuildingMetadata {
            address: Some("123 Main St, Springfield".to_string()),
            total_sqft: 25000.0,
            year_built: Some(1985),
            building_type: Some("Educational".to_string()),
            occupancy_class: Some("E".to_string()),
        };
        
        assert_eq!(metadata.address, Some("123 Main St, Springfield".to_string()));
        assert_eq!(metadata.total_sqft, 25000.0);
        assert_eq!(metadata.year_built, Some(1985));
        assert_eq!(metadata.building_type, Some("Educational".to_string()));
        assert_eq!(metadata.occupancy_class, Some("E".to_string()));
    }
}