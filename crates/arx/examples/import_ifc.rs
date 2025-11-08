use arx::ifc::IFCProcessor;
use std::env;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let file_path = env::args()
        .nth(1)
        .expect("Usage: cargo run --example import_ifc <path-to-ifc>");

    let processor = IFCProcessor::new();
    let (building, floors) = processor.extract_hierarchy(&file_path)?;

    println!("Imported building: {}", building.name);
    println!("Floors parsed: {}", floors.len());

    Ok(())
}
