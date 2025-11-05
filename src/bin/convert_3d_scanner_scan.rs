//! Converter for 3D Scanner App scan data to ArxOS YAML format
//!
//! This binary extracts room boundaries and spatial data from a 3D Scanner App scan
//! and converts it to ArxOS BuildingData format for testing.
//!
//! # Usage
//!
//! ```bash
//! cargo run --bin convert_3d_scanner_scan -- ~/Downloads/scan_directory [output.yaml]
//! ```
//!
//! # Example
//!
//! ```bash
//! cargo run --bin convert_3d_scanner_scan -- ~/Downloads/2025_11_01_08_21_41 scan_output.yaml
//! ```

use clap::Parser;
use std::path::{Path, PathBuf};
use serde_json::Value;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData};
use arxos::spatial::{Point3D, BoundingBox3D};
use arxos::yaml::BuildingYamlSerializer;
use chrono::Utc;
use nalgebra::{Matrix4, Vector4};
use std::collections::HashMap;

/// Converter for 3D Scanner App scan data to ArxOS YAML format
#[derive(Parser)]
#[command(name = "convert_3d_scanner_scan")]
#[command(about = "Convert 3D Scanner App scan data to ArxOS YAML format")]
#[command(version)]
struct Args {
    /// Scan directory path (must contain info.json)
    #[arg(help = "Path to 3D Scanner App scan directory")]
    scan_dir: PathBuf,
    
    /// Output YAML file path
    #[arg(short, long, default_value = "house_scan.yaml")]
    output: PathBuf,
    
    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
    
    /// Quiet mode (minimal output)
    #[arg(short, long)]
    quiet: bool,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    
    // Validate input directory
    if !args.scan_dir.exists() {
        return Err(format!("Scan directory not found: {}", args.scan_dir.display()).into());
    }
    
    if !args.scan_dir.is_dir() {
        return Err(format!("Path is not a directory: {}", args.scan_dir.display()).into());
    }
    
    // Validate info.json exists
    let info_path = args.scan_dir.join("info.json");
    if !info_path.exists() {
        return Err(format!(
            "Missing info.json in scan directory: {}\n\nExpected file: {}",
            args.scan_dir.display(),
            info_path.display()
        ).into());
    }
    
    // Validate output path parent directory exists and is writable
    if let Some(parent) = args.output.parent() {
        if !parent.exists() {
            return Err(format!(
                "Output directory does not exist: {}\n\nPlease create the directory first or specify a different output path.",
                parent.display()
            ).into());
        }
    }
    
    if !args.quiet {
        println!("📊 Analyzing scan: {}", args.scan_dir.display());
    }
    
    // Read and parse info.json
    let info_content = std::fs::read_to_string(&info_path)
        .map_err(|e| format!("Failed to read info.json: {}\n\nPath: {}", e, info_path.display()))?;
    
    let info: Value = serde_json::from_str(&info_content)
        .map_err(|e| format!("Failed to parse info.json as JSON: {}\n\nPath: {}", e, info_path.display()))?;
    
    // Extract bounding box (OBB)
    let obb = info.get("userOBB")
        .and_then(|v| v.get("points"))
        .and_then(|v| v.as_array())
        .ok_or_else(|| format!(
            "Missing userOBB.points in info.json\n\nExpected structure: {{\"userOBB\": {{\"points\": [...]}}}}\n\nPath: {}",
            info_path.display()
        ))?;
    
    // Parse bounding box points using Point3D
    let points: Vec<Point3D> = obb.iter()
        .filter_map(|p| {
            p.as_array().and_then(|arr| {
                if arr.len() >= 3 {
                    Some(Point3D::new(
                        arr[0].as_f64().unwrap_or(0.0),
                        arr[1].as_f64().unwrap_or(0.0),
                        arr[2].as_f64().unwrap_or(0.0),
                    ))
                } else {
                    None
                }
            })
        })
        .collect();
    
    if points.len() != 8 {
        return Err(format!(
            "Expected 8 OBB points, got {}\n\nPlease ensure the scan data is complete and valid.\n\nPath: {}",
            points.len(),
            info_path.display()
        ).into());
    }
    
    // Calculate min/max bounds using BoundingBox3D
    let bounding_box = BoundingBox3D::from_points(&points)
        .ok_or_else(|| "Failed to calculate bounding box from OBB points".to_string())?;
    
    let min_x = bounding_box.min.x;
    let max_x = bounding_box.max.x;
    let min_y = bounding_box.min.y;
    let max_y = bounding_box.max.y;
    let min_z = bounding_box.min.z;
    let max_z = bounding_box.max.z;
    
    let width = max_x - min_x;
    let depth = max_z - min_z;
    let height = max_y - min_y;
    
    if !args.quiet {
        println!("📐 Bounding Box:");
        println!("   X: {:.2} to {:.2} (width: {:.2}m)", min_x, max_x, width);
        println!("   Y: {:.2} to {:.2} (height: {:.2}m)", min_y, max_y, height);
        println!("   Z: {:.2} to {:.2} (depth: {:.2}m)", min_z, max_z, depth);
        println!("   Volume: {:.2} m³", width * depth * height);
    }
    
    // Get scan metadata
    let title = info.get("title")
        .and_then(|v| v.as_str())
        .unwrap_or("House Scan")
        .to_string();
    let device = info.get("device")
        .and_then(|v| v.as_str())
        .unwrap_or("Unknown")
        .to_string();
    
    if !args.quiet {
        println!("📱 Device: {}", device);
        println!("🏠 Title: {}", title);
    }
    
    // Count frames
    let frame_count = std::fs::read_dir(&args.scan_dir)?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let file_name = entry.file_name();
            let name = file_name.to_string_lossy();
            if name.starts_with("frame_") && name.ends_with(".json") {
                Some(())
            } else {
                None
            }
        })
        .count();
    
    if !args.quiet {
        println!("📷 Frames: {}", frame_count);
    }
    
    // Try to read roomplan/room.json for actual floor plan geometry
    let roomplan_path = args.scan_dir.join("roomplan").join("room.json");
    let mut floor_polygon: Option<Vec<Point3D>> = None;
    let mut walls_count = 0;
    let mut doors_count = 0;
    let mut windows_count = 0;
    let mut walls_data: Option<String> = None;
    
    if roomplan_path.exists() {
        if !args.quiet {
            println!("📐 Found floor plan data: roomplan/room.json");
        }
        match std::fs::read_to_string(&roomplan_path) {
            Ok(room_content) => {
                if let Ok(room_data) = serde_json::from_str::<Value>(&room_content) {
                    // Extract floor polygon
                    if let Some(floors) = room_data.get("floors").and_then(|v| v.as_array()) {
                        if let Some(floor) = floors.first() {
                            if let Some(corners) = floor.get("polygonCorners").and_then(|v| v.as_array()) {
                                let polygon: Vec<Point3D> = corners.iter()
                                    .filter_map(|p| {
                                        p.as_array().and_then(|arr| {
                                            if arr.len() >= 3 {
                                                Some(Point3D::new(
                                                    arr[0].as_f64().unwrap_or(0.0),
                                                    arr[1].as_f64().unwrap_or(0.0),
                                                    arr[2].as_f64().unwrap_or(0.0),
                                                ))
                                            } else {
                                                None
                                            }
                                        })
                                    })
                                    .collect();
                                
                                if !polygon.is_empty() {
                                    if !args.quiet {
                                        println!("   ✓ Floor polygon: {} corners", polygon.len());
                                    }
                                    floor_polygon = Some(polygon);
                                }
                            }
                        }
                    }
                    
                    // Count structural elements
                    walls_count = room_data.get("walls")
                        .and_then(|v| v.as_array())
                        .map(|a| a.len())
                        .unwrap_or(0);
                    doors_count = room_data.get("doors")
                        .and_then(|v| v.as_array())
                        .map(|a| a.len())
                        .unwrap_or(0);
                    windows_count = room_data.get("windows")
                        .and_then(|v| v.as_array())
                        .map(|a| a.len())
                        .unwrap_or(0);
                    
                    if !args.quiet {
                        println!("   ✓ Walls: {}", walls_count);
                        println!("   ✓ Doors: {}", doors_count);
                        println!("   ✓ Windows: {}", windows_count);
                    }
                    
                    // Extract wall line segments using nalgebra
                    let mut wall_segments: Vec<String> = Vec::new();
                    if let Some(walls) = room_data.get("walls").and_then(|v| v.as_array()) {
                        for wall in walls.iter().take(100) { // Limit to prevent huge strings
                            if let (Some(dims), Some(transform)) = (
                                wall.get("dimensions").and_then(|v| v.as_array()),
                                wall.get("transform").and_then(|v| v.as_array())
                            ) {
                                if dims.len() >= 2 && transform.len() >= 16 {
                                    let length = dims[0].as_f64().unwrap_or(0.0);
                                    
                                    // Extract transform matrix elements (row-major 4x4)
                                    let m: Vec<f64> = transform.iter()
                                        .take(16)
                                        .filter_map(|v| v.as_f64())
                                        .collect();
                                    
                                    if m.len() == 16 && length > 0.0 {
                                        // Build nalgebra Matrix4 from row-major array
                                        let transform_matrix = Matrix4::new(
                                            m[0], m[1], m[2], m[3],
                                            m[4], m[5], m[6], m[7],
                                            m[8], m[9], m[10], m[11],
                                            m[12], m[13], m[14], m[15],
                                        );
                                        
                                        // Wall extends along local X axis from -length/2 to +length/2
                                        let local_start = Vector4::new(-length / 2.0, 0.0, 0.0, 1.0);
                                        let local_end = Vector4::new(length / 2.0, 0.0, 0.0, 1.0);
                                        
                                        // Transform to world space using matrix multiplication
                                        let world_start = transform_matrix * local_start;
                                        let world_end = transform_matrix * local_end;
                                        
                                        wall_segments.push(format!("{},{},{},{}", 
                                            world_start.x, world_start.y, 
                                            world_end.x, world_end.y));
                                    }
                                }
                            }
                        }
                    }
                    
                    if !wall_segments.is_empty() && !args.quiet {
                        println!("   ✓ Extracted {} wall segments", wall_segments.len());
                    }
                    
                    walls_data = Some(wall_segments.join("|"));
                }
            }
            Err(e) => {
                if args.verbose {
                    eprintln!("⚠️  Could not read room.json: {}", e);
                }
            }
        }
    }
    
    // Generate ArxOS BuildingData structure using library types
    let building_data = generate_building_data(
        &title,
        &device,
        bounding_box,
        width, depth, height,
        frame_count,
        &args.scan_dir,
        floor_polygon.as_ref(),
        walls_count,
        doors_count,
        windows_count,
        walls_data.as_deref(),
    )?;
    
    // Serialize to YAML using library serializer
    let serializer = BuildingYamlSerializer::new();
    let yaml = serializer.to_yaml(&building_data)?;
    
    // Write output
    std::fs::write(&args.output, yaml)
        .map_err(|e| format!("Failed to write output file: {}\n\nPath: {}\n\nError: {}", 
            e, args.output.display(), e))?;
    
    if !args.quiet {
        println!("✅ Generated: {}", args.output.display());
        println!("");
        println!("💡 Next steps:");
        println!("   1. Review the generated YAML file");
        println!("   2. Test with: arx doc --building \"{}\"", title);
        println!("   3. Import to test: arx import {}", args.output.display());
    }
    
    Ok(())
}

fn generate_building_data(
    name: &str,
    device: &str,
    bounding_box: BoundingBox3D,
    width: f64,
    depth: f64,
    height: f64,
    frame_count: usize,
    scan_dir: &Path,
    floor_polygon: Option<&Vec<Point3D>>,
    walls_count: usize,
    doors_count: usize,
    windows_count: usize,
    walls_data: Option<&str>,
) -> Result<BuildingData, Box<dyn std::error::Error>> {
    let now = Utc::now();
    
    // Create a single floor with the scanned space as one large room
    let room_name = if name.contains("Scan") || name.contains("scan") {
        "Main Floor"
    } else {
        "Scanned Space"
    };
    
    // Build room properties
    let mut room_properties = HashMap::new();
    room_properties.insert("scan_source".to_string(), "3D Scanner App".to_string());
    room_properties.insert("device".to_string(), device.to_string());
    room_properties.insert("frame_count".to_string(), frame_count.to_string());
    room_properties.insert("scan_mode".to_string(), "floor-plan".to_string());
    room_properties.insert("width_meters".to_string(), format!("{:.2}", width));
    room_properties.insert("depth_meters".to_string(), format!("{:.2}", depth));
    room_properties.insert("height_meters".to_string(), format!("{:.2}", height));
    room_properties.insert("walls_detected".to_string(), walls_count.to_string());
    room_properties.insert("doors_detected".to_string(), doors_count.to_string());
    room_properties.insert("windows_detected".to_string(), windows_count.to_string());
    room_properties.insert("floor_polygon_points".to_string(), 
        floor_polygon.map(|p| p.len()).unwrap_or(0).to_string());
    
    // Add floor polygon data if available
    if let Some(polygon) = floor_polygon {
        let polygon_str = polygon.iter()
            .map(|p| format!("{},{},{}", p.x, p.y, p.z))
            .collect::<Vec<_>>()
            .join(";");
        room_properties.insert("floor_polygon".to_string(), polygon_str);
    }
    
    // Add walls data if available
    if let Some(walls) = walls_data {
        room_properties.insert("walls_data".to_string(), walls.to_string());
    }
    
    // Calculate room center and elevation
    let center_x = (bounding_box.min.x + bounding_box.max.x) / 2.0;
    let center_z = (bounding_box.min.z + bounding_box.max.z) / 2.0;
    let floor_elevation = bounding_box.min.y;
    
    // Create room data
    let room = RoomData {
        id: "room-main".to_string(),
        name: room_name.to_string(),
        room_type: "Residential".to_string(),
        area: Some(width * depth),
        volume: Some(width * depth * height),
        position: Point3D::new(center_x, floor_elevation, center_z),
        bounding_box: bounding_box.clone(),
        equipment: vec![],
        properties: room_properties,
    };
    
    // Create floor data
    let floor = FloorData {
        id: "floor-ground".to_string(),
        name: "Ground Floor".to_string(),
        level: 0,
        elevation: floor_elevation,
        wings: vec![],
        rooms: vec![room],
        equipment: vec![],
        bounding_box: Some(bounding_box.clone()),
    };
    
    // Create building info
    let building_info = BuildingInfo {
        id: format!("scan-{}", now.timestamp()),
        name: name.to_string(),
        description: Some(format!("3D Scanner App scan from {}. {} frames captured in floor plan mode.", device, frame_count)),
        created_at: now,
        updated_at: now,
        version: "1.0.0".to_string(),
        global_bounding_box: Some(bounding_box),
    };
    
    // Create metadata
    let metadata = BuildingMetadata {
        source_file: Some(scan_dir.display().to_string()),
        parser_version: "1.0.0".to_string(),
        total_entities: 1,
        spatial_entities: 1,
        coordinate_system: "World".to_string(),
        units: "meters".to_string(),
        tags: vec!["3d-scanner-app".to_string(), "floor-plan-mode".to_string(), "mobile-scan".to_string()],
    };
    
    // Create building data
    let building_data = BuildingData {
        building: building_info,
        metadata,
        floors: vec![floor],
        coordinate_systems: vec![],
    };
    
    Ok(building_data)
}
