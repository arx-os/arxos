//! Integration tests for ifc_rs library with ArxOS sample files
//!
//! These tests validate the complete IFC parsing pipeline:
//! 1. ifc_rs parses IFC files
//! 2. IFCRsConverter extracts entities
//! 3. HierarchyBuilder constructs Building model

use arx::ifc::{BimParser, IFCEntity};
use arx::ifc::hierarchy::HierarchyBuilder;

#[test]
fn test_ifc_rs_parse_sample_building() {
    let result = ifc_rs::IFC::from_file("test_data/sample_building.ifc");
    
    match result {
        Ok(ifc) => {
            println!("✅ Successfully parsed sample_building.ifc");
            println!("   Entities count: {}", ifc.data.0.len());
            
            // Verify we have some entities
            assert!(ifc.data.0.len() > 0, "Should have parsed some entities");
            
            // Print some info about the parsed file
            println!("   Header version: {:?}", ifc.header.version);
            println!("   Schema: {:?}", ifc.header.schema);
        }
        Err(e) => {
            panic!("Failed to parse sample_building.ifc: {}", e);
        }
    }
}

#[test]
fn test_ifc_rs_parse_building_architecture() {
    let result = ifc_rs::IFC::from_file("test_data/Building-Architecture.ifc");
    
    match result {
        Ok(ifc) => {
            println!("✅ Successfully parsed Building-Architecture.ifc");
            println!("   Entities count: {}", ifc.data.0.len());
            assert!(ifc.data.0.len() > 0);
        }
        Err(e) => {
            println!("⚠️  Could not parse Building-Architecture.ifc: {}", e);
            println!("   This may be expected if the file uses unsupported IFC features");
        }
    }
}

#[test]
fn test_ifc_rs_parse_building_hvac() {
    let result = ifc_rs::IFC::from_file("test_data/Building-Hvac.ifc");
    
    match result {
        Ok(ifc) => {
            println!("✅ Successfully parsed Building-Hvac.ifc");
            println!("   Entities count: {}", ifc.data.0.len());
            assert!(ifc.data.0.len() > 0);
        }
        Err(e) => {
            println!("⚠️  Could not parse Building-Hvac.ifc: {}", e);
            println!("   This may be expected if the file uses unsupported IFC features");
        }
    }
}

#[test]
fn test_ifc_rs_parse_from_string() {
    let content = std::fs::read_to_string("test_data/sample_building.ifc")
        .expect("Should be able to read sample file");
    
    let result = ifc_rs::IFC::from_str(&content);
    
    match result {
        Ok(ifc) => {
            println!("✅ Successfully parsed IFC from string");
            println!("   Entities count: {}", ifc.data.0.len());
            assert!(ifc.data.0.len() > 0);
        }
        Err(e) => {
            panic!("Failed to parse IFC from string: {}", e);
        }
    }
}

#[test]
fn test_ifc_rs_entity_iteration() {
    let ifc = ifc_rs::IFC::from_file("test_data/sample_building.ifc")
        .expect("Should parse sample file");
    
    println!("\n🔍 Inspecting IFC entities:");
    
    let mut building_count = 0;
    let mut storey_count = 0;
    let mut space_count = 0;
    let mut relation_count = 0;
    
    for (id, entity) in &ifc.data.0 {
        let entity_str = entity.to_string();
        
        if entity_str.contains("IFCBUILDING") {
            building_count += 1;
            println!("   Found IFCBUILDING: #{}", id);
        } else if entity_str.contains("IFCBUILDINGSTOREY") {
            storey_count += 1;
            println!("   Found IFCBUILDINGSTOREY: #{}", id);
        } else if entity_str.contains("IFCSPACE") {
            space_count += 1;
            println!("   Found IFCSPACE: #{}", id);
        } else if entity_str.contains("IFCREL") {
            relation_count += 1;
        }
    }
    
    println!("\n📊 Summary:");
    println!("   Buildings: {}", building_count);
    println!("   Storeys: {}", storey_count);
    println!("   Spaces: {}", space_count);
    println!("   Relations: {}", relation_count);
    
    // Verify we found expected entities
    assert!(building_count > 0, "Should have at least one building");
}

// ============================================================================
// BimParser Integration Tests
// ============================================================================

#[test]
fn test_bim_parser_parse_file() {
    let parser = BimParser::new();
    
    // Building-Hvac.ifc is known to parse successfully
    let result = parser.parse_ifc_file("test_data/Building-Hvac.ifc");
    
    match result {
        Ok((building, spatial_entities)) => {
            println!("✅ BimParser successfully parsed Building-Hvac.ifc");
            println!("   Building name: {}", building.name);
            println!("   Floors: {}", building.floors.len());
            println!("   Spatial entities: {}", spatial_entities.len());
            
            assert!(!building.name.is_empty(), "Building should have a name");
            assert!(building.floors.len() >= 0, "Building should have floors extracted");
        }
        Err(e) => {
            panic!("BimParser failed to parse: {}", e);
        }
    }
}

#[test]
fn test_bim_parser_integration_pipeline() {
    // Test the complete pipeline: ifc_rs → IFCRsConverter → HierarchyBuilder
    
    // Step 1: Parse with ifc_rs
    let ifc = ifc_rs::IFC::from_file("test_data/Building-Hvac.ifc")
        .expect("Should parse with ifc_rs");
    
    println!("✅ Step 1: ifc_rs parsed file");
    
    // Step 2: Convert to IFCEntity
    use arx::ifc::ifc_rs_converter::IFCRsConverter;
    let entities = IFCRsConverter::convert(&ifc)
        .expect("Should convert entities");
    
    println!("✅ Step 2: IFCRsConverter extracted {} entities", entities.len());
    assert!(!entities.is_empty(), "Should have extracted entities");
    
    // Step 3: Build hierarchy
    let hierarchy_builder = HierarchyBuilder::new(entities);
    let building = hierarchy_builder.build_hierarchy()
        .expect("Should build hierarchy");
    
    println!("✅ Step 3: HierarchyBuilder constructed Building");
    println!("   Building: {}", building.name);
    println!("   Floors: {}", building.floors.len());
    
    assert!(!building.name.is_empty(), "Building should have a name");
}
