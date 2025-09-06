//! Complete Pipeline: LiDAR → PLY → ArxObjects → Aesthetic ASCII Art
//! 
//! This module implements the full vision for ArxOS:
//! Taking raw LiDAR scans and transforming them into beautiful,
//! functional pixel art visualizations that look like industrial art.

use crate::arxobject::{ArxObject, object_types};
use crate::ply_parser::{PlyParser, Point3D};
use crate::point_cloud_processor::{PointCloudProcessor, ProcessingConfig};
use crate::pixelated_renderer::{PixelatedRenderer, PixelationConfig};
use crate::error::{ArxError, Result};
use std::path::Path;

/// Configuration for aesthetic compression
pub struct AestheticConfig {
    /// Target aesthetic style
    pub style: AestheticStyle,
    /// Compression aggressiveness (0.0 - 1.0)
    pub compression_level: f32,
    /// Enable smart object detection
    pub smart_detection: bool,
    /// Preserve architectural lines
    pub preserve_edges: bool,
}

/// Different aesthetic styles inspired by pixel art
#[derive(Debug, Clone, Copy)]
pub enum AestheticStyle {
    /// High contrast industrial (like the reference image)
    IndustrialPixel,
    /// Smooth gradients, atmospheric
    Atmospheric,
    /// Sharp, geometric, brutalist
    Brutalist,
    /// Soft, retro game aesthetic
    RetroGame,
    /// Matrix-style digital rain
    CyberMatrix,
}

impl Default for AestheticConfig {
    fn default() -> Self {
        Self {
            style: AestheticStyle::IndustrialPixel,
            compression_level: 0.7,
            smart_detection: true,
            preserve_edges: true,
        }
    }
}

/// Main pipeline orchestrator
pub struct AestheticPipeline {
    aesthetic_config: AestheticConfig,
    processor_config: ProcessingConfig,
    pixelation_config: PixelationConfig,
}

impl AestheticPipeline {
    pub fn new(aesthetic_config: AestheticConfig) -> Self {
        // Configure processing based on aesthetic style
        let (processor_config, pixelation_config) = match aesthetic_config.style {
            AestheticStyle::IndustrialPixel => {
                (
                    ProcessingConfig {
                        voxel_size_mm: 150.0,  // 15cm voxels
                        min_points_per_voxel: 5,
                        cluster_distance_mm: 300.0,
                        detect_objects: true,
                        merge_similar: true,
                        floor_height_mm: 100.0,
                        ceiling_height_mm: 2400.0,
                    },
                    PixelationConfig {
                        pixel_size_mm: 200,  // 20cm blocks
                        width_pixels: 120,
                        height_pixels: 40,
                        depth_layers: 4,
                        edge_detection: true,
                        contrast: 1.3,
                        brightness: 0.1,
                        dithering: true,
                    }
                )
            },
            AestheticStyle::Atmospheric => {
                (
                    ProcessingConfig {
                        voxel_size_mm: 200.0,
                        min_points_per_voxel: 3,
                        cluster_distance_mm: 500.0,
                        detect_objects: true,
                        merge_similar: true,
                        floor_height_mm: 100.0,
                        ceiling_height_mm: 2400.0,
                    },
                    PixelationConfig {
                        pixel_size_mm: 300,
                        width_pixels: 100,
                        height_pixels: 35,
                        depth_layers: 6,
                        edge_detection: false,
                        contrast: 0.8,
                        brightness: -0.1,
                        dithering: true,
                    }
                )
            },
            AestheticStyle::Brutalist => {
                (
                    ProcessingConfig {
                        voxel_size_mm: 250.0,
                        min_points_per_voxel: 10,
                        cluster_distance_mm: 200.0,
                        detect_objects: true,
                        merge_similar: false,  // Keep sharp edges
                        floor_height_mm: 100.0,
                        ceiling_height_mm: 2400.0,
                    },
                    PixelationConfig {
                        pixel_size_mm: 400,
                        width_pixels: 80,
                        height_pixels: 30,
                        depth_layers: 3,
                        edge_detection: true,
                        contrast: 2.0,
                        brightness: 0.0,
                        dithering: false,
                    }
                )
            },
            AestheticStyle::RetroGame => {
                (
                    ProcessingConfig {
                        voxel_size_mm: 100.0,
                        min_points_per_voxel: 2,
                        cluster_distance_mm: 250.0,
                        detect_objects: true,
                        merge_similar: true,
                        floor_height_mm: 100.0,
                        ceiling_height_mm: 2400.0,
                    },
                    PixelationConfig {
                        pixel_size_mm: 150,
                        width_pixels: 160,
                        height_pixels: 48,
                        depth_layers: 2,
                        edge_detection: false,
                        contrast: 1.5,
                        brightness: 0.2,
                        dithering: false,
                    }
                )
            },
            AestheticStyle::CyberMatrix => {
                (
                    ProcessingConfig {
                        voxel_size_mm: 50.0,
                        min_points_per_voxel: 1,
                        cluster_distance_mm: 100.0,
                        detect_objects: false,  // Keep raw data feel
                        merge_similar: false,
                        floor_height_mm: 100.0,
                        ceiling_height_mm: 2400.0,
                    },
                    PixelationConfig {
                        pixel_size_mm: 100,
                        width_pixels: 200,
                        height_pixels: 50,
                        depth_layers: 8,
                        edge_detection: true,
                        contrast: 1.8,
                        brightness: -0.2,
                        dithering: true,
                    }
                )
            },
        };
        
        Self {
            aesthetic_config,
            processor_config,
            pixelation_config,
        }
    }
    
    /// Process PLY file through complete pipeline
    pub async fn process_ply_file(&self, ply_path: &Path) -> Result<String> {
        println!("🎨 Aesthetic Pipeline Starting...");
        println!("  Style: {:?}", self.aesthetic_config.style);
        
        // Step 1: Parse PLY file
        println!("📁 Loading PLY file...");
        let mut parser = PlyParser::new();
        parser.parse_file(ply_path)?;
        let points = parser.points();
        println!("  ✓ Loaded {} points", points.len());
        
        // Show statistics
        let stats = parser.statistics();
        println!("  ✓ Bounds: ({:.1}, {:.1}, {:.1}) to ({:.1}, {:.1}, {:.1})",
            stats.min_bounds.x, stats.min_bounds.y, stats.min_bounds.z,
            stats.max_bounds.x, stats.max_bounds.y, stats.max_bounds.z);
        
        // Step 2: Process point cloud to ArxObjects  
        println!("🔄 Converting to ArxObjects...");
        let mut processor = PointCloudProcessor::new(self.processor_config.clone());
        let mut arxobjects = processor.process(points, 42)?; // Building ID 42
        println!("  ✓ Generated {} ArxObjects", arxobjects.len());
        
        // Step 3: Apply aesthetic compression
        if self.aesthetic_config.compression_level > 0.0 {
            println!("🗜️ Applying aesthetic compression...");
            arxobjects = self.apply_aesthetic_compression(arxobjects);
            println!("  ✓ Compressed to {} objects", arxobjects.len());
        }
        
        // Step 4: Smart object detection (if enabled)
        if self.aesthetic_config.smart_detection {
            println!("🔍 Detecting architectural features...");
            self.detect_and_enhance_features(&mut arxobjects);
            println!("  ✓ Enhanced architectural elements");
        }
        
        // Step 5: Render to ASCII art
        println!("🎨 Rendering aesthetic ASCII art...");
        let mut renderer = PixelatedRenderer::new(self.pixelation_config.clone());
        
        // Calculate view center (center of mass of objects)
        let center = self.calculate_center(&arxobjects);
        renderer.process_arxobjects(&arxobjects, center);
        
        let output = renderer.render();
        
        // Add metadata header
        let stats = renderer.get_stats();
        let header = self.generate_header(&stats, arxobjects.len());
        
        Ok(format!("{}\n{}", header, output))
    }
    
    /// Apply aesthetic-aware compression
    fn apply_aesthetic_compression(&self, objects: Vec<ArxObject>) -> Vec<ArxObject> {
        let target_count = (objects.len() as f32 * (1.0 - self.aesthetic_config.compression_level)) as usize;
        
        // Sort by visual importance
        let mut scored_objects: Vec<(f32, ArxObject)> = objects.iter()
            .map(|obj| (self.calculate_visual_importance(obj), *obj))
            .collect();
        
        scored_objects.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
        
        // Keep most important objects
        scored_objects.into_iter()
            .take(target_count.max(100)) // Keep at least 100 objects
            .map(|(_, obj)| obj)
            .collect()
    }
    
    /// Calculate visual importance of an object
    fn calculate_visual_importance(&self, obj: &ArxObject) -> f32 {
        let mut score = 1.0;
        
        // Structural elements are most important
        if matches!(obj.object_type, 
            object_types::WALL | 
            object_types::FLOOR | 
            object_types::CEILING |
            object_types::DOOR |
            object_types::WINDOW) {
            score *= 10.0;
        }
        
        // Equipment is important
        if matches!(obj.object_type,
            object_types::ELECTRICAL_PANEL |
            object_types::HVAC_VENT |
            object_types::EMERGENCY_EXIT) {
            score *= 5.0;
        }
        
        // Objects at eye level are more important
        let eye_level = 1500; // 1.5m
        let distance_from_eye = ((obj.z as i32 - eye_level).abs() as f32) / 1000.0;
        score *= 1.0 / (1.0 + distance_from_eye);
        
        // Edge objects are important for defining space
        if self.aesthetic_config.preserve_edges {
            // Simple heuristic: objects at regular intervals might be edges
            if obj.x % 1000 < 100 || obj.y % 1000 < 100 {
                score *= 2.0;
            }
        }
        
        score
    }
    
    /// Detect and enhance architectural features
    fn detect_and_enhance_features(&self, objects: &mut Vec<ArxObject>) {
        // Group objects by height layers
        let mut layers: std::collections::HashMap<u16, Vec<usize>> = std::collections::HashMap::new();
        
        for (idx, obj) in objects.iter().enumerate() {
            let layer = obj.z / 100; // 10cm layers
            layers.entry(layer).or_insert_with(Vec::new).push(idx);
        }
        
        // Detect floor plane (lowest dense layer)
        if let Some((floor_z, indices)) = layers.iter()
            .filter(|(_, indices)| indices.len() > 50)
            .min_by_key(|(z, _)| **z) {
            
            for &idx in indices {
                objects[idx].object_type = object_types::FLOOR;
            }
        }
        
        // Detect ceiling (highest dense layer)
        if let Some((ceiling_z, indices)) = layers.iter()
            .filter(|(_, indices)| indices.len() > 50)
            .max_by_key(|(z, _)| **z) {
            
            for &idx in indices {
                objects[idx].object_type = object_types::CEILING;
            }
        }
        
        // Detect walls (vertical clusters)
        // This is simplified - real implementation would use more sophisticated clustering
        for obj in objects.iter_mut() {
            if obj.z > 500 && obj.z < 2500 { // Between floor and ceiling
                // Check if at edge positions
                if obj.x < 500 || obj.x > 9500 || obj.y < 500 || obj.y > 9500 {
                    obj.object_type = object_types::WALL;
                }
            }
        }
    }
    
    /// Calculate center of mass for view
    fn calculate_center(&self, objects: &[ArxObject]) -> (u16, u16, u16) {
        if objects.is_empty() {
            return (5000, 5000, 1500);
        }
        
        let sum_x: u64 = objects.iter().map(|o| o.x as u64).sum();
        let sum_y: u64 = objects.iter().map(|o| o.y as u64).sum();
        let sum_z: u64 = objects.iter().map(|o| o.z as u64).sum();
        
        let count = objects.len() as u64;
        
        (
            (sum_x / count) as u16,
            (sum_y / count) as u16,
            (sum_z / count) as u16,
        )
    }
    
    /// Generate header with metadata
    fn generate_header(&self, stats: &crate::pixelated_renderer::RenderStats, object_count: usize) -> String {
        let style_icon = match self.aesthetic_config.style {
            AestheticStyle::IndustrialPixel => "⚙️",
            AestheticStyle::Atmospheric => "🌫️",
            AestheticStyle::Brutalist => "🏢",
            AestheticStyle::RetroGame => "🕹️",
            AestheticStyle::CyberMatrix => "💻",
        };
        
        format!(
            "╔════════════════════════════════════════════════════════════╗\n\
             ║ {} ArxOS Aesthetic Render - {:?} Style\n\
             ║ Objects: {} | Pixels: {} | Density: {:.1}%\n\
             ║ Compression: {:.0}:1 | Edge Detection: {}\n\
             ╚════════════════════════════════════════════════════════════╝",
            style_icon,
            self.aesthetic_config.style,
            object_count,
            stats.occupied_pixels,
            (stats.occupied_pixels as f32 / stats.total_pixels as f32) * 100.0,
            50000000 / (object_count * 13), // Approximate compression from original point cloud
            if self.pixelation_config.edge_detection { "ON" } else { "OFF" }
        )
    }
}

// ProcessingConfig and PixelationConfig now have proper Clone derives in their modules

/// Quick demo function
pub async fn demo_complete_pipeline() {
    println!("\n🎨 ArxOS Complete Aesthetic Pipeline Demo\n");
    println!("Vision: LiDAR → PLY → ArxObjects → Beautiful ASCII Art\n");
    
    // Simulate the pipeline with generated data
    let config = AestheticConfig {
        style: AestheticStyle::IndustrialPixel,
        compression_level: 0.7,
        smart_detection: true,
        preserve_edges: true,
    };
    
    let pipeline = AestheticPipeline::new(config);
    
    // Create sample ArxObjects (simulating PLY processing)
    let mut objects = Vec::new();
    
    // Generate a room with industrial equipment
    for x in 0..40 {
        for y in 0..40 {
            // Floor
            objects.push(ArxObject::new(42, object_types::FLOOR, x * 250, y * 250, 0));
            
            // Ceiling
            objects.push(ArxObject::new(42, object_types::CEILING, x * 250, y * 250, 3000));
        }
    }
    
    // Walls
    for i in 0..40 {
        objects.push(ArxObject::new(42, object_types::WALL, 0, i * 250, 1500));
        objects.push(ArxObject::new(42, object_types::WALL, 9750, i * 250, 1500));
        objects.push(ArxObject::new(42, object_types::WALL, i * 250, 0, 1500));
        objects.push(ArxObject::new(42, object_types::WALL, i * 250, 9750, 1500));
    }
    
    // Industrial equipment cluster
    for x in 15..25 {
        for y in 15..25 {
            for z in 0..5 {
                objects.push(ArxObject::new(
                    42, 
                    object_types::HVAC_VENT,
                    x * 250, 
                    y * 250, 
                    z * 300 + 500
                ));
            }
        }
    }
    
    // Apply compression
    println!("Original objects: {}", objects.len());
    let compressed = pipeline.apply_aesthetic_compression(objects);
    println!("After aesthetic compression: {}", compressed.len());
    
    // Render
    let mut renderer = PixelatedRenderer::new(pipeline.pixelation_config);
    renderer.process_arxobjects(&compressed, (5000, 5000, 1500));
    
    let output = renderer.render();
    println!("\n{}", output);
    
    println!("\n✨ This is the ArxOS vision:");
    println!("  • Beautiful industrial pixel art aesthetic");
    println!("  • Extreme compression (1000:1 or better)");
    println!("  • Functional for maintenance/inspection");
    println!("  • Works over low-bandwidth RF networks");
    println!("  • Makes buildings feel alive and playable");
}