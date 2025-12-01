//! Tests for brightness ramp system in point cloud rendering
//!
//! Validates the Acerola-style 16-level ASCII rendering system.

use crate::render3d::point_cloud::*;
use crate::render3d::camera::vec3;
use crossterm::style::Color;

#[test]
fn test_brightness_ramp_lengths() {
    // Verify all ramps have correct character counts
    assert_eq!(brightness_ramps::CLASSIC.chars().count(), 9, 
        "CLASSIC ramp should have 9 characters");
    
    assert_eq!(brightness_ramps::ACEROLA_16.chars().count(), 16,
        "ACEROLA_16 ramp should have 16 characters");
    
    assert_eq!(brightness_ramps::EXTENDED_16.chars().count(), 16,
        "EXTENDED_16 ramp should have 16 characters");
    
    assert_eq!(brightness_ramps::UNICODE_16.chars().count(), 16,
        "UNICODE_16 ramp should have 16 characters");
}

#[test]
fn test_brightness_ramp_ordering() {
    // Verify ramps start with space (darkest) and end with dense character (brightest)
    assert_eq!(brightness_ramps::CLASSIC.chars().next().unwrap(), ' ',
        "CLASSIC should start with space");
    
    assert_eq!(brightness_ramps::ACEROLA_16.chars().next().unwrap(), ' ',
        "ACEROLA_16 should start with space");
    
    assert_eq!(brightness_ramps::ACEROLA_16.chars().last().unwrap(), '$',
        "ACEROLA_16 should end with '$'");
}

#[test]
fn test_get_brightness_char_bounds() {
    let ramp = brightness_ramps::ACEROLA_16;
    
    // Depth 0.0 should give first character (space)
    let ch = get_brightness_char(0.0, ramp);
    assert_eq!(ch, ' ', "Depth 0.0 should map to space (darkest)");
    
    // Depth 1.0 should give last character ($)
    let ch = get_brightness_char(1.0, ramp);
    assert_eq!(ch, '$', "Depth 1.0 should map to $ (brightest)");
}

#[test]
fn test_get_brightness_char_midrange() {
    let ramp = brightness_ramps::ACEROLA_16;
    
    // Mid-range depth should give middle character
    let ch = get_brightness_char(0.5, ramp);
    assert!(ch != ' ' && ch != '$', 
        "Mid-range depth should give middle character, got: {}", ch);
    
    // Should be around index 7-8 for 16-character ramp
    let expected_chars = ['#', '%', '@'];
    assert!(expected_chars.contains(&ch),
        "Mid-range should be around #, %, or @, got: {}", ch);
}

#[test]
fn test_get_brightness_char_progression() {
    let ramp = brightness_ramps::ACEROLA_16;
    
    // Verify smooth progression from dark to bright
    let depths = [0.0, 0.25, 0.5, 0.75, 1.0];
    let mut prev_idx = 0;
    
    for depth in depths {
        let ch = get_brightness_char(depth, ramp);
        let idx = ramp.chars().position(|c| c == ch).unwrap();
        
        // Each step should be at same or higher brightness
        assert!(idx >= prev_idx,
            "Brightness should increase with depth: {} -> {}", prev_idx, idx);
        prev_idx = idx;
    }
}

#[test]
fn test_get_brightness_char_edge_cases() {
    let ramp = brightness_ramps::ACEROLA_16;
    
    // Negative depth should clamp to 0
    let ch = get_brightness_char(-0.5, ramp);
    assert_eq!(ch, ' ', "Negative depth should clamp to space");
    
    // Depth > 1.0 should clamp to max
    let ch = get_brightness_char(2.0, ramp);
    assert_eq!(ch, '$', "Depth > 1.0 should clamp to brightest");
}

#[test]
fn test_point_cloud_renderer_default_ramp() {
    let points = vec![
        Point3DColored { 
            pos: vec3(0.0, 0.0, 0.0), 
            color: Color::White 
        },
    ];
    
    let renderer = PointCloudRenderer::new(points);
    
    // Should default to ACEROLA_16
    assert_eq!(renderer.brightness_ramp, brightness_ramps::ACEROLA_16,
        "Renderer should default to ACEROLA_16 ramp");
}

#[test]
fn test_point_cloud_renderer_custom_ramp() {
    let points = vec![
        Point3DColored { 
            pos: vec3(0.0, 0.0, 0.0), 
            color: Color::White 
        },
    ];
    
    // Test builder pattern with different ramps
    let renderer = PointCloudRenderer::new(points.clone())
        .with_brightness_ramp(brightness_ramps::CLASSIC);
    assert_eq!(renderer.brightness_ramp, brightness_ramps::CLASSIC,
        "Should accept CLASSIC ramp");
    
    let renderer = PointCloudRenderer::new(points.clone())
        .with_brightness_ramp(brightness_ramps::UNICODE_16);
    assert_eq!(renderer.brightness_ramp, brightness_ramps::UNICODE_16,
        "Should accept UNICODE_16 ramp");
    
    let renderer = PointCloudRenderer::new(points)
        .with_brightness_ramp(brightness_ramps::EXTENDED_16);
    assert_eq!(renderer.brightness_ramp, brightness_ramps::EXTENDED_16,
        "Should accept EXTENDED_16 ramp");
}

#[test]
fn test_brightness_char_distribution() {
    let ramp = brightness_ramps::ACEROLA_16;
    let num_samples = 100;
    
    // Sample across full depth range
    for i in 0..num_samples {
        let depth = i as f32 / (num_samples - 1) as f32;
        let ch = get_brightness_char(depth, ramp);
        
        // Every character should be from the ramp
        assert!(ramp.contains(ch),
            "Character '{}' at depth {} should be in ramp", ch, depth);
    }
}

#[test]
fn test_acerola_16_specific_characters() {
    // Verify the exact Acerola character set
    let expected = " .:-=+*#%@MWBQ&$";
    assert_eq!(brightness_ramps::ACEROLA_16, expected,
        "ACEROLA_16 should match exact character sequence");
    
    // Verify key characters at specific positions
    let chars: Vec<char> = brightness_ramps::ACEROLA_16.chars().collect();
    assert_eq!(chars[0], ' ', "Position 0 should be space");
    assert_eq!(chars[8], '%', "Position 8 should be %");
    assert_eq!(chars[15], '$', "Position 15 should be $");
}

#[test]
fn test_lod_threshold() {
    // Small point cloud should not use LOD
    let small_points: Vec<Point3DColored> = (0..5000)
        .map(|i| Point3DColored {
            pos: vec3(i as f32, 0.0, 0.0),
            color: Color::White,
        })
        .collect();
    
    let renderer = PointCloudRenderer::new(small_points);
    assert!(renderer.grid.is_none(), 
        "Point clouds < 10,000 should not use LOD grid");
    
    // Large point cloud should use LOD
    let large_points: Vec<Point3DColored> = (0..15000)
        .map(|i| Point3DColored {
            pos: vec3(i as f32, 0.0, 0.0),
            color: Color::White,
        })
        .collect();
    
    let renderer = PointCloudRenderer::new(large_points);
    assert!(renderer.grid.is_some(),
        "Point clouds > 10,000 should use LOD grid");
}

#[test]
fn test_brightness_ramp_no_duplicates() {
    // Each ramp should have unique characters for best visual distinction
    for (name, ramp) in [
        ("CLASSIC", brightness_ramps::CLASSIC),
        ("ACEROLA_16", brightness_ramps::ACEROLA_16),
        ("EXTENDED_16", brightness_ramps::EXTENDED_16),
        ("UNICODE_16", brightness_ramps::UNICODE_16),
    ] {
        let chars: Vec<char> = ramp.chars().collect();
        let unique_chars: std::collections::HashSet<char> = chars.iter().copied().collect();
        
        assert_eq!(chars.len(), unique_chars.len(),
            "{} ramp should have no duplicate characters", name);
    }
}
