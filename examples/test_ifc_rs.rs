// Standalone test for ifc_rs integration
// Run with: cargo run --example test_ifc_rs

use std::str::FromStr;

fn main() {
    println!("🧪 Testing ifc_rs parsing with ArxOS sample files\n");
    
    // Test 1: Parse sample_building.ifc
    println!("1. Testing sample_building.ifc...");
    match ifc_rs::IFC::from_file("test_data/sample_building.ifc") {
        Ok(ifc) => {
            println!("   ✅ Successfully parsed!");
            println!("   📄 Schema: {:?}", ifc.header.schema);
            println!("   📄 Version: {:?}", ifc.header.version);
        }
        Err(e) => {
            println!("   ❌ Failed to parse: {}", e);
        }
    }
    
    println!("\n2. Testing Building-Architecture.ifc...");
    match ifc_rs::IFC::from_file("test_data/Building-Architecture.ifc") {
        Ok(ifc) => {
            println!("   ✅ Successfully parsed!");
            println!("   📄 Schema: {:?}", ifc.header.schema);
        }
        Err(e) => {
            println!("   ⚠️  Could not parse: {}", e);
            println!("      (This may be expected if file uses unsupported IFC features)");
        }
    }
    
    println!("\n3. Testing Building-Hvac.ifc...");
    match ifc_rs::IFC::from_file("test_data/Building-Hvac.ifc") {
        Ok(ifc) => {
            println!("   ✅ Successfully parsed!");
            println!("   📄 Schema: {:?}", ifc.header.schema);
        }
        Err(e) => {
            println!("   ⚠️  Could not parse: {}", e);
            println!("      (This may be expected if file uses unsupported IFC features)");
        }
    }
    
    println!("\n4. Testing string parsing (WASM compatibility)...");
    let content = std::fs::read_to_string("test_data/sample_building.ifc")
        .expect("Should be able to read file");
    match ifc_rs::IFC::from_str(&content) {
        Ok(ifc) => {
            println!("   ✅ Successfully parsed from string!");
            println!("   📄 Schema: {:?}", ifc.header.schema);
        }
        Err(e) => {
            println!("   ❌ Failed: {}", e);
        }
    }
    
    println!("\n🎉 ifc_rs integration testing complete!");
    println!("\n✨ Next steps:");
    println!("   1. Create IFCRsConverter to map ifc_rs types to ArxOS IFCEntity");
    println!("   2. Wire up BimParser to use ifc_rs");
    println!("   3. Test end-to-end with HierarchyBuilder");
}
