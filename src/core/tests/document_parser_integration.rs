//! Integration tests for document parser with terminal

use arxos_core::document_parser::{DocumentParser, EquipmentType};
use std::fs;
use std::path::PathBuf;

/// Create a test PDF with building data
fn create_test_pdf() -> Vec<u8> {
    // Minimal valid PDF with building information
    let pdf_content = b"%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R
   /Resources << /Font << /F1 5 0 R >> >>
>>
endobj
4 0 obj
<< /Length 500 >>
stream
BT
/F1 12 Tf
50 750 Td
(BUILDING NAME: Jefferson Elementary School) Tj
0 -20 Td
(ADDRESS: 123 Main Street, Springfield) Tj
0 -30 Td
(ROOM SCHEDULE) Tj
0 -20 Td
(Room 127 - Science Lab - 800 sq ft) Tj
0 -15 Td
(Room 128 - Classroom - 600 sq ft) Tj
0 -15 Td
(Room 129 - Computer Lab - 750 sq ft) Tj
0 -30 Td
(EQUIPMENT SCHEDULE) Tj
0 -20 Td
(EO-127-01  Electrical Outlet  Room 127  120V/20A) Tj
0 -15 Td
(LF-127-01  Light Fixture  Room 127  LED 4000K) Tj
0 -15 Td
(HVAC-128-01  HVAC Vent  Room 128  Supply) Tj
0 -15 Td
(FA-129-01  Fire Alarm  Room 129  Addressable) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000229 00000 n
0000000779 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
856
%%EOF";
    pdf_content.to_vec()
}

/// Create a test IFC file
fn create_test_ifc() -> String {
    r#"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('jefferson_elementary.ifc','2024-01-15T10:00:00',(),(),'ArxOS IFC Writer','ArxOS','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCORGANIZATION($,'ArxOS',$,$,$);
#2=IFCAPPLICATION(#1,'1.0','ArxOS Terminal','ArxOS');
#3=IFCPERSON($,'User',$,$,$,$,$,$);
#4=IFCORGANIZATION($,'Organization',$,$,$);
#5=IFCPERSONANDORGANIZATION(#3,#4,$);
#6=IFCOWNERHISTORY(#5,#2,$,.ADDED.,$,#3,#2,1234567890);
#7=IFCPROJECT('project001',#6,'Jefferson Elementary','School building',$,$,$,$,#8);
#8=IFCUNITASSIGNMENT((#9,#10,#11));
#9=IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#10=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#11=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#12=IFCSITE('site001',#6,'School Site',$,$,$,$,$,$,$,$,$,$,$);
#13=IFCBUILDING('building001',#6,'Jefferson Elementary','Main Building',$,$,$,$,$,$,$,$);
#14=IFCBUILDINGSTOREY('floor1',#6,'Level 1','Ground Floor',$,$,$,$,$,$);
#15=IFCBUILDINGSTOREY('floor2',#6,'Level 2','Second Floor',$,$,$,$,$,$);
#16=IFCSPACE('space127',#6,'127','Science Lab',$,$,$,$,.ELEMENT.,$);
#17=IFCSPACE('space128',#6,'128','Classroom',$,$,$,$,.ELEMENT.,$);
#18=IFCSPACE('space129',#6,'129','Computer Lab',$,$,$,$,.ELEMENT.,$);
#19=IFCOUTLET('outlet127_1',#6,'Outlet','Electrical Outlet',$,$,$,$);
#20=IFCLIGHTFIXTURE('light127_1',#6,'Light','LED Light',$,$,$,$);
#21=IFCAIRTERMINAL('hvac128_1',#6,'Vent','HVAC Vent',$,$,$,$);
#22=IFCALARM('alarm129_1',#6,'Fire Alarm','Addressable',$,$,$,$);
#23=IFCDOOR('door127',#6,'Door','Entry Door',$,$,$,$,$,$,$);
#24=IFCWINDOW('window127',#6,'Window','Double Pane',$,$,$,$,$,$,$);
#25=IFCRELAGGREGATES('agg1',#6,$,$,#7,(#12));
#26=IFCRELAGGREGATES('agg2',#6,$,$,#12,(#13));
#27=IFCRELAGGREGATES('agg3',#6,$,$,#13,(#14,#15));
#28=IFCRELCONTAINEDINSPATIALSTRUCTURE('cont1',#6,$,$,(#16,#17),#14);
#29=IFCRELCONTAINEDINSPATIALSTRUCTURE('cont2',#6,$,$,(#18),#15);
#30=IFCRELCONTAINEDINSPATIALSTRUCTURE('cont3',#6,$,$,(#19,#20),#16);
#31=IFCRELCONTAINEDINSPATIALSTRUCTURE('cont4',#6,$,$,(#21),#17);
#32=IFCRELCONTAINEDINSPATIALSTRUCTURE('cont5',#6,$,$,(#22),#18);
ENDSEC;
END-ISO-10303-21;"#.to_string()
}

#[tokio::test]
async fn test_pdf_parsing() {
    // Create temp directory
    let temp_dir = std::env::temp_dir();
    let pdf_path = temp_dir.join("test_building.pdf");
    
    // Write test PDF
    fs::write(&pdf_path, create_test_pdf()).unwrap();
    
    // Parse PDF
    let mut parser = DocumentParser::new();
    let result = parser.parse_document(pdf_path.to_str().unwrap()).await;
    
    // Clean up
    fs::remove_file(pdf_path).ok();
    
    // Verify parsing succeeded
    assert!(result.is_ok(), "PDF parsing should succeed");
    
    let plan = result.unwrap();
    assert!(plan.name.contains("Jefferson"));
    
    // Should have extracted rooms from text
    let total_rooms: usize = plan.floors.iter().map(|f| f.rooms.len()).sum();
    assert!(total_rooms > 0, "Should have extracted rooms");
}

#[tokio::test]
async fn test_ifc_parsing() {
    // Create temp directory
    let temp_dir = std::env::temp_dir();
    let ifc_path = temp_dir.join("test_building.ifc");
    
    // Write test IFC
    fs::write(&ifc_path, create_test_ifc()).unwrap();
    
    // Parse IFC
    let mut parser = DocumentParser::new();
    let result = parser.parse_document(ifc_path.to_str().unwrap()).await;
    
    // Clean up
    fs::remove_file(ifc_path).ok();
    
    // Verify parsing succeeded
    assert!(result.is_ok(), "IFC parsing should succeed");
    
    let plan = result.unwrap();
    assert!(plan.name.contains("Jefferson") || plan.name == "Unknown Building");
}

#[test]
fn test_arxobject_conversion() {
    let parser = DocumentParser::new();
    
    // Create a test building plan
    use arxos_core::document_parser::{
        BuildingPlan, FloorPlan, Equipment, Point3D, BuildingMetadata
    };
    use std::collections::HashMap;
    
    let equipment = vec![
        Equipment {
            equipment_type: EquipmentType::ElectricalOutlet,
            location: Point3D { x: 5.0, y: 3.0, z: 0.3 },
            room_number: Some("127".to_string()),
            properties: HashMap::new(),
        },
        Equipment {
            equipment_type: EquipmentType::LightFixture,
            location: Point3D { x: 10.0, y: 5.0, z: 2.8 },
            room_number: Some("127".to_string()),
            properties: HashMap::new(),
        },
    ];
    
    let floor = FloorPlan {
        floor_number: 1,
        rooms: vec![],
        ascii_layout: String::new(),
        equipment,
    };
    
    let plan = BuildingPlan {
        name: "Test Building".to_string(),
        floors: vec![floor],
        arxobjects: vec![],
        metadata: BuildingMetadata {
            address: None,
            total_sqft: 10000.0,
            year_built: Some(2020),
            building_type: Some("Educational".to_string()),
            occupancy_class: Some("E".to_string()),
        },
    };
    
    // Convert to ArxObjects
    let arxobjects = parser.to_arxobjects(&plan);
    
    // Verify conversion
    assert_eq!(arxobjects.len(), 2, "Should have 2 ArxObjects");
    
    // Check first object (outlet)
    let outlet = &arxobjects[0];
    assert_eq!(outlet.x, 5000); // 5.0m * 1000
    assert_eq!(outlet.y, 3000); // 3.0m * 1000
    assert_eq!(outlet.z, 300);  // 0.3m * 1000
    
    // Check second object (light)
    let light = &arxobjects[1];
    assert_eq!(light.x, 10000); // 10.0m * 1000
    assert_eq!(light.y, 5000);  // 5.0m * 1000
    assert_eq!(light.z, 2800);  // 2.8m * 1000
}

#[test]
fn test_ascii_generation() {
    use arxos_core::document_parser::{
        DocumentParser, BuildingPlan, FloorPlan, Room, Point3D, 
        BoundingBox, BuildingMetadata
    };
    
    let parser = DocumentParser::new();
    
    let room = Room {
        number: "127".to_string(),
        name: "Science Lab".to_string(),
        area_sqft: 800.0,
        bounds: BoundingBox {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 10.0, y: 8.0, z: 3.0 },
        },
        equipment_count: 5,
    };
    
    let floor = FloorPlan {
        floor_number: 1,
        rooms: vec![room],
        ascii_layout: "Test layout".to_string(),
        equipment: vec![],
    };
    
    let plan = BuildingPlan {
        name: "Jefferson Elementary".to_string(),
        floors: vec![floor],
        arxobjects: vec![],
        metadata: BuildingMetadata {
            address: Some("123 Main St".to_string()),
            total_sqft: 25000.0,
            year_built: Some(1985),
            building_type: Some("Educational".to_string()),
            occupancy_class: Some("E".to_string()),
        },
    };
    
    // Generate ASCII
    let ascii = parser.generate_ascii(&plan);
    
    // Verify ASCII contains expected elements
    assert!(ascii.contains("JEFFERSON ELEMENTARY"));
    assert!(ascii.contains("FLOOR 1"));
    assert!(ascii.contains("127"));
    assert!(ascii.contains("Science Lab"));
    assert!(ascii.contains("800 sq ft"));
    assert!(ascii.contains("BUILDING SUMMARY"));
}

#[tokio::test]
async fn test_command_processor() {
    use arxos_terminal::commands::CommandProcessor;
    
    let mut processor = CommandProcessor::new();
    
    // Test help command processing
    let result = processor.process("help").await;
    assert!(!result.success); // help is not handled by processor
    
    // Test load-plan with missing file
    let result = processor.process("load-plan nonexistent.pdf").await;
    assert!(!result.success);
    assert!(result.output[0].contains("not found"));
    
    // Test list-floors without loaded plan
    let result = processor.process("list-floors").await;
    assert!(!result.success);
    assert!(result.output[0].contains("No building plan loaded"));
}

#[test]
fn test_equipment_symbols() {
    use arxos_core::document_parser::EquipmentType;
    
    // Test all equipment types have symbols
    let types = vec![
        EquipmentType::ElectricalOutlet,
        EquipmentType::LightFixture,
        EquipmentType::HvacVent,
        EquipmentType::FireAlarm,
        EquipmentType::SmokeDetector,
        EquipmentType::EmergencyExit,
        EquipmentType::Thermostat,
        EquipmentType::Switch,
        EquipmentType::DataPort,
        EquipmentType::SecurityCamera,
        EquipmentType::Sprinkler,
        EquipmentType::Door,
        EquipmentType::Window,
    ];
    
    for eq_type in types {
        let symbol = eq_type.to_ascii_symbol();
        assert!(!symbol.is_empty(), "{:?} should have a symbol", eq_type);
        assert!(symbol.len() <= 3, "{:?} symbol should be 3 chars or less", eq_type);
    }
}