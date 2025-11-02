//! Converter for 3D Scanner App scan data to ArxOS YAML format
//!
//! This script extracts room boundaries and spatial data from a 3D Scanner App scan
//! and converts it to ArxOS BuildingData format for testing.

use std::path::Path;
use serde_json::Value;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <scan_directory> [output_file.yaml]", args[0]);
        eprintln!("Example: {} ~/Downloads/2025_11_01_08_21_41", args[0]);
        std::process::exit(1);
    }

    let scan_dir = Path::new(&args[1]);
    let output_file = args.get(2).map(|s| s.as_str()).unwrap_or("house_scan.yaml");

    println!("📊 Analyzing scan: {}", scan_dir.display());

    // Read info.json
    let info_path = scan_dir.join("info.json");
    let info_content = std::fs::read_to_string(&info_path)
        .map_err(|e| format!("Failed to read info.json: {}", e))?;
    let info: Value = serde_json::from_str(&info_content)
        .map_err(|e| format!("Failed to parse info.json: {}", e))?;

    // Extract bounding box (OBB)
    let obb = info.get("userOBB")
        .and_then(|v| v.get("points"))
        .and_then(|v| v.as_array())
        .ok_or("Missing userOBB.points in info.json")?;

    // Parse bounding box points
    let points: Vec<[f64; 3]> = obb.iter()
        .filter_map(|p| {
            p.as_array().and_then(|arr| {
                if arr.len() == 3 {
                    Some([
                        arr[0].as_f64().unwrap_or(0.0),
                        arr[1].as_f64().unwrap_or(0.0),
                        arr[2].as_f64().unwrap_or(0.0),
                    ])
                } else {
                    None
                }
            })
        })
        .collect();

    if points.len() != 8 {
        return Err(format!("Expected 8 OBB points, got {}", points.len()).into());
    }

    // Calculate min/max bounds
    let min_x = points.iter().map(|p| p[0]).fold(f64::INFINITY, f64::min);
    let max_x = points.iter().map(|p| p[0]).fold(f64::NEG_INFINITY, f64::max);
    let min_y = points.iter().map(|p| p[1]).fold(f64::INFINITY, f64::min);
    let max_y = points.iter().map(|p| p[1]).fold(f64::NEG_INFINITY, f64::max);
    let min_z = points.iter().map(|p| p[2]).fold(f64::INFINITY, f64::min);
    let max_z = points.iter().map(|p| p[2]).fold(f64::NEG_INFINITY, f64::max);

    let width = max_x - min_x;
    let depth = max_z - min_z;
    let height = max_y - min_y;

    println!("📐 Bounding Box:");
    println!("   X: {:.2} to {:.2} (width: {:.2}m)", min_x, max_x, width);
    println!("   Y: {:.2} to {:.2} (height: {:.2}m)", min_y, max_y, height);
    println!("   Z: {:.2} to {:.2} (depth: {:.2}m)", min_z, max_z, depth);
    println!("   Volume: {:.2} m³", width * depth * height);

    // Get scan metadata
    let title = info.get("title")
        .and_then(|v| v.as_str())
        .unwrap_or("House Scan")
        .to_string();
    let device = info.get("device")
        .and_then(|v| v.as_str())
        .unwrap_or("Unknown")
        .to_string();

    println!("📱 Device: {}", device);
    println!("🏠 Title: {}", title);

    // Count frames
    let frame_count = std::fs::read_dir(scan_dir)?
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

    println!("📷 Frames: {}", frame_count);

    // Try to read roomplan/room.json for actual floor plan geometry
    let roomplan_path = scan_dir.join("roomplan").join("room.json");
    let mut floor_polygon: Option<Vec<[f64; 3]>> = None;
    let mut walls_count = 0;
    let mut doors_count = 0;
    let mut windows_count = 0;
    let mut walls_data: Option<String> = None;

    if roomplan_path.exists() {
        println!("📐 Found floor plan data: roomplan/room.json");
        match std::fs::read_to_string(&roomplan_path) {
            Ok(room_content) => {
                if let Ok(room_data) = serde_json::from_str::<Value>(&room_content) {
                    // Extract floor polygon
                    if let Some(floors) = room_data.get("floors").and_then(|v| v.as_array()) {
                        if let Some(floor) = floors.first() {
                            if let Some(corners) = floor.get("polygonCorners").and_then(|v| v.as_array()) {
                                let polygon: Vec<[f64; 3]> = corners.iter()
                                    .filter_map(|p| {
                                        p.as_array().and_then(|arr| {
                                            if arr.len() >= 3 {
                                                Some([
                                                    arr[0].as_f64().unwrap_or(0.0),
                                                    arr[1].as_f64().unwrap_or(0.0),
                                                    arr[2].as_f64().unwrap_or(0.0),
                                                ])
                                            } else {
                                                None
                                            }
                                        })
                                    })
                                    .collect();
                                
                                if !polygon.is_empty() {
                                    let polygon_len = polygon.len();
                                    floor_polygon = Some(polygon);
                                    println!("   ✓ Floor polygon: {} corners", polygon_len);
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
                    
                    println!("   ✓ Walls: {}", walls_count);
                    println!("   ✓ Doors: {}", doors_count);
                    println!("   ✓ Windows: {}", windows_count);
                    
                    // Extract wall line segments
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
                                        // Wall extends along local X axis from -length/2 to +length/2
                                        // Local space: wall center at origin, extends along X
                                        let local_start = [-length / 2.0, 0.0, 0.0, 1.0];
                                        let local_end = [length / 2.0, 0.0, 0.0, 1.0];
                                        
                                        // Transform to world space using matrix multiplication
                                        // Matrix is row-major 4x4: 
                                        // [m00 m01 m02 m03]  Translation in row 4 (indices 12,13,14)
                                        // [m10 m11 m12 m13]
                                        // [m20 m21 m22 m23]
                                        // [tx  ty  tz  1  ]
                                        let transform_point = |p: [f64; 4]| -> (f64, f64, f64) {
                                            // Multiply point by matrix (row-major)
                                            let x = p[0]*m[0] + p[1]*m[1] + p[2]*m[2] + p[3]*m[12];
                                            let y = p[0]*m[4] + p[1]*m[5] + p[2]*m[6] + p[3]*m[13];
                                            let z = p[0]*m[8] + p[1]*m[9] + p[2]*m[10] + p[3]*m[14];
                                            (x, y, z)
                                        };
                                        
                                        let (x1, y1, _z1) = transform_point(local_start);
                                        let (x2, y2, _z2) = transform_point(local_end);
                                        
                                        wall_segments.push(format!("{},{},{},{}", x1, y1, x2, y2));
                                    }
                                }
                            }
                        }
                    }
                    
                    if !wall_segments.is_empty() {
                        println!("   ✓ Extracted {} wall segments", wall_segments.len());
                    }
                    
                    walls_data = Some(wall_segments.join("|"));
                }
            }
            Err(e) => {
                println!("⚠️  Could not read room.json: {}", e);
            }
        }
    }

    // Generate ArxOS YAML structure
    let building_yaml = generate_building_yaml(
        &title,
        &device,
        min_x, max_x, min_y, max_y, min_z, max_z,
        width, depth, height,
        frame_count,
        scan_dir,
        floor_polygon.as_ref(),
        walls_count,
        doors_count,
        windows_count,
        walls_data.as_deref(),
    )?;

    // Write output
    std::fs::write(output_file, building_yaml)?;
    println!("✅ Generated: {}", output_file);
    println!("");
    println!("💡 Next steps:");
    println!("   1. Review the generated YAML file");
    println!("   2. Test with: arx doc --building \"{}\"", title);
    println!("   3. Import to test: arx import house_scan.yaml");

    Ok(())
}

fn generate_building_yaml(
    name: &str,
    device: &str,
    min_x: f64, max_x: f64,
    min_y: f64, max_y: f64,
    min_z: f64, max_z: f64,
    width: f64, depth: f64, height: f64,
    frame_count: usize,
    scan_dir: &Path,
    floor_polygon: Option<&Vec<[f64; 3]>>,
    walls_count: usize,
    doors_count: usize,
    windows_count: usize,
    walls_data: Option<&str>,
) -> Result<String, Box<dyn std::error::Error>> {
    use chrono::Utc;

    let now = Utc::now();

    // Create a single floor with the scanned space as one large room
    let room_name = if name.contains("Scan") || name.contains("scan") {
        "Main Floor"
    } else {
        "Scanned Space"
    };

    let building_yaml = format!(r#"building:
  id: scan-{timestamp}
  name: {name}
  description: "3D Scanner App scan from {device}. {frame_count} frames captured in floor plan mode."
  created_at: {created_at}
  updated_at: {updated_at}
  version: "1.0.0"
  global_bounding_box:
    min:
      x: {min_x}
      y: {min_y}
      z: {min_z}
    max:
      x: {max_x}
      y: {max_y}
      z: {max_z}

metadata:
  source_file: "{scan_dir}"
  parser_version: "1.0.0"
  total_entities: 1
  spatial_entities: 1
  coordinate_system: "World"
  units: "meters"
  tags:
    - "3d-scanner-app"
    - "floor-plan-mode"
    - "mobile-scan"

floors:
  - id: floor-ground
    name: "Ground Floor"
    level: 0
    elevation: {floor_elevation}
    rooms:
      - id: room-main
        name: "{room_name}"
        room_type: "Residential"
        area: {area}
        volume: {volume}
        position:
          x: {center_x}
          y: {floor_elevation}
          z: {center_z}
        bounding_box:
          min:
            x: {min_x}
            y: {min_y}
            z: {min_z}
          max:
            x: {max_x}
            y: {max_y}
            z: {max_z}
        equipment: []
        properties:
          scan_source: "3D Scanner App"
          device: "{device}"
          frame_count: "{frame_count}"
          scan_mode: "floor-plan"
          width_meters: "{width}"
          depth_meters: "{depth}"
          height_meters: "{height}"
          walls_detected: "{walls_count}"
          doors_detected: "{doors_count}"
          windows_detected: "{windows_count}"
          floor_polygon_points: "{floor_polygon_count}"
          floor_polygon: "{floor_polygon_data}"
          walls_data: "{walls_data}"
    equipment: []
    bounding_box:
      min:
        x: {min_x}
        y: {min_y}
        z: {min_z}
      max:
        x: {max_x}
        y: {max_y}
        z: {max_z}

coordinate_systems: []
"#,
        timestamp = now.timestamp(),
        name = name,
        device = device,
        frame_count = frame_count,
        created_at = now.to_rfc3339(),
        updated_at = now.to_rfc3339(),
        scan_dir = scan_dir.display(),
        min_x = min_x,
        min_y = min_y,
        min_z = min_z,
        max_x = max_x,
        max_y = max_y,
        max_z = max_z,
        center_x = (min_x + max_x) / 2.0,
        center_z = (min_z + max_z) / 2.0,
        floor_elevation = min_y,
        area = width * depth,
        volume = width * depth * height,
        room_name = room_name,
        width = width,
        depth = depth,
        height = height,
        walls_count = walls_count,
        doors_count = doors_count,
        windows_count = windows_count,
        floor_polygon_count = floor_polygon.map(|p| p.len()).unwrap_or(0),
        floor_polygon_data = floor_polygon.map(|poly| {
            poly.iter()
                .map(|p| format!("{},{},{}", p[0], p[1], p[2]))
                .collect::<Vec<_>>()
                .join(";")
        }).unwrap_or_else(|| String::new()),
        walls_data = walls_data.unwrap_or_default(),
    );

    Ok(building_yaml)
}

