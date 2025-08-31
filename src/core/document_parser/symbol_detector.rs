//! Symbol Detection for Architectural Drawings
//! 
//! Detects equipment symbols in floor plan images

use super::{Equipment, EquipmentType, Point3D};
use image::{DynamicImage, GrayImage, Luma};
use imageproc::template_matching::{match_template, MatchTemplateMethod};
use std::collections::HashMap;

/// Symbol detector for equipment identification
pub struct SymbolDetector {
    /// Symbol templates for each equipment type
    templates: HashMap<EquipmentType, GrayImage>,
    /// Detection threshold
    threshold: f32,
}

impl SymbolDetector {
    /// Create new symbol detector
    pub fn new() -> Self {
        Self {
            templates: Self::load_templates(),
            threshold: 0.8,  // 80% match confidence
        }
    }
    
    /// Detect all equipment symbols in image
    pub fn detect_symbols(&self, image: &DynamicImage) -> Vec<Equipment> {
        let mut equipment = Vec::new();
        let gray = image.to_luma8();
        
        // Process each template
        for (eq_type, template) in &self.templates {
            let matches = self.find_template_matches(&gray, template, *eq_type);
            equipment.extend(matches);
        }
        
        // Remove duplicates (overlapping detections)
        self.remove_duplicates(equipment)
    }
    
    /// Find all matches of a template in the image
    fn find_template_matches(
        &self,
        image: &GrayImage,
        template: &GrayImage,
        eq_type: EquipmentType,
    ) -> Vec<Equipment> {
        let mut matches = Vec::new();
        
        // Perform template matching
        let result = match_template(
            image,
            template,
            MatchTemplateMethod::CrossCorrelationNormalized,
        );
        
        // Find peaks in the result
        let (width, height) = result.dimensions();
        let template_width = template.width();
        let template_height = template.height();
        
        for y in 0..height {
            for x in 0..width {
                let score = result.get_pixel(x, y)[0];
                
                if score >= self.threshold {
                    // Check if this is a local maximum
                    if self.is_local_maximum(&result, x, y) {
                        matches.push(Equipment {
                            equipment_type: eq_type,
                            location: Point3D {
                                x: (x + template_width / 2) as f32,
                                y: (y + template_height / 2) as f32,
                                z: 0.0,
                            },
                            room_number: None,
                            properties: HashMap::new(),
                        });
                    }
                }
            }
        }
        
        matches
    }
    
    /// Check if a point is a local maximum
    fn is_local_maximum(&self, result: &image::ImageBuffer<image::Luma<f32>, Vec<f32>>, x: u32, y: u32) -> bool {
        let value = result.get_pixel(x, y)[0];
        let (width, height) = result.dimensions();
        
        // Check 3x3 neighborhood
        for dy in -1i32..=1 {
            for dx in -1i32..=1 {
                if dx == 0 && dy == 0 {
                    continue;
                }
                
                let nx = (x as i32 + dx) as u32;
                let ny = (y as i32 + dy) as u32;
                
                if nx < width && ny < height {
                    if result.get_pixel(nx, ny)[0] > value {
                        return false;
                    }
                }
            }
        }
        
        true
    }
    
    /// Remove duplicate detections
    fn remove_duplicates(&self, mut equipment: Vec<Equipment>) -> Vec<Equipment> {
        let mut filtered = Vec::new();
        
        // Sort by confidence (if available)
        equipment.sort_by(|a, b| {
            a.location.x.partial_cmp(&b.location.x).unwrap()
        });
        
        for eq in equipment {
            // Check if this equipment is too close to any already added
            let is_duplicate = filtered.iter().any(|existing: &Equipment| {
                let dx = (eq.location.x - existing.location.x).abs();
                let dy = (eq.location.y - existing.location.y).abs();
                dx < 10.0 && dy < 10.0  // Within 10 pixels
            });
            
            if !is_duplicate {
                filtered.push(eq);
            }
        }
        
        filtered
    }
    
    /// Load symbol templates
    fn load_templates() -> HashMap<EquipmentType, GrayImage> {
        let mut templates = HashMap::new();
        
        // Create simple synthetic templates for common symbols
        // In production, these would be loaded from files
        
        templates.insert(
            EquipmentType::ElectricalOutlet,
            Self::create_outlet_template(),
        );
        
        templates.insert(
            EquipmentType::LightFixture,
            Self::create_light_template(),
        );
        
        templates.insert(
            EquipmentType::Door,
            Self::create_door_template(),
        );
        
        templates
    }
    
    /// Create outlet symbol template
    fn create_outlet_template() -> GrayImage {
        // Create a simple circle with two dots (outlet symbol)
        let size = 20;
        let mut img = GrayImage::new(size, size);
        
        // Draw circle
        for y in 0..size {
            for x in 0..size {
                let dx = x as f32 - size as f32 / 2.0;
                let dy = y as f32 - size as f32 / 2.0;
                let dist = (dx * dx + dy * dy).sqrt();
                
                if (dist - size as f32 / 2.0).abs() < 1.0 {
                    img.put_pixel(x, y, Luma([0u8]));  // Black circle
                }
            }
        }
        
        // Add two dots for outlet
        img.put_pixel(size / 2 - 3, size / 2, Luma([0u8]));
        img.put_pixel(size / 2 + 3, size / 2, Luma([0u8]));
        
        img
    }
    
    /// Create light fixture template
    fn create_light_template() -> GrayImage {
        // Create a simple X or cross for light fixture
        let size = 20;
        let mut img = GrayImage::new(size, size);
        
        // Draw cross
        for i in 0..size {
            img.put_pixel(i, size / 2, Luma([0u8]));
            img.put_pixel(size / 2, i, Luma([0u8]));
        }
        
        img
    }
    
    /// Create door template
    fn create_door_template() -> GrayImage {
        // Create an arc for door swing
        let size = 30;
        let mut img = GrayImage::new(size, size);
        
        // Draw arc
        for angle in 0..90 {
            let rad = angle as f32 * std::f32::consts::PI / 180.0;
            let x = (size as f32 * rad.cos()) as u32;
            let y = (size as f32 * rad.sin()) as u32;
            
            if x < size && y < size {
                img.put_pixel(x, y, Luma([0u8]));
            }
        }
        
        img
    }
}