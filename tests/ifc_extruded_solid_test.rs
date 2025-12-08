// Standalone test for IFC ExtrudedAreaSolid bounding box computation
// This test reproduces the issue without requiring full cargo test linking

use nalgebra::Vector3;

#[test]
fn test_extruded_solid_bounding_box_manual() {
    // Profile points: 4x3 rectangle at Z=0
    let profile_points = vec![
        Vector3::new(0.0_f64, 0.0_f64, 0.0_f64),
        Vector3::new(4.0_f64, 0.0_f64, 0.0_f64),
        Vector3::new(4.0_f64, 3.0_f64, 0.0_f64),
        Vector3::new(0.0_f64, 3.0_f64, 0.0_f64),
    ];

    // Extrusion: 3.0 units in Z direction
    let extrusion_direction = Vector3::new(0.0_f64, 0.0_f64, 1.0_f64);
    let extrusion_depth = 3.0_f64;
    let extrusion_vector = extrusion_direction * extrusion_depth;

    // Generate all points (base + extruded)
    let mut all_points = Vec::new();
    for point in &profile_points {
        all_points.push(*point);
        all_points.push(point + extrusion_vector);
    }

    // Compute bounding box
    let mut min = all_points[0];
    let mut max = all_points[0];

    for point in all_points.iter().skip(1) {
        min.x = min.x.min(point.x);
        min.y = min.y.min(point.y);
        min.z = min.z.min(point.z);

        max.x = max.x.max(point.x);
        max.y = max.y.max(point.y);
        max.z = max.z.max(point.z);
    }

    // Verify expected bounding box
    println!("Min: ({}, {}, {})", min.x, min.y, min.z);
    println!("Max: ({}, {}, {})", max.x, max.y, max.z);

    assert!((min.x - 0.0).abs() < 1e-6, "min.x should be 0.0, got {}", min.x);
    assert!((min.y - 0.0).abs() < 1e-6, "min.y should be 0.0, got {}", min.y);
    assert!((min.z - 0.0).abs() < 1e-6, "min.z should be 0.0, got {}", min.z);
    assert!((max.x - 4.0).abs() < 1e-6, "max.x should be 4.0, got {}", max.x);
    assert!((max.y - 3.0).abs() < 1e-6, "max.y should be 3.0, got {}", max.y);
    assert!((max.z - 3.0).abs() < 1e-6, "max.z should be 3.0, got {}", max.z);

    println!("✅ Manual test passed: Bounding box is correct!");
}
