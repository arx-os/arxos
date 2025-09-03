//! PixaTool-Inspired Pixelated ASCII Renderer for ArxOS
//! 
//! Transforms LiDAR point clouds into aesthetic pixel art visualizations
//! that look like the industrial/architectural pixel art aesthetic.
//! Each pixel represents spatial density of ArxObjects.

use crate::arxobject::ArxObject;
use std::collections::HashMap;

/// ASCII palette inspired by the industrial pixel art aesthetic
/// Darker to lighter based on object density
const DENSITY_PALETTE: [char; 16] = [
    ' ',  // Empty space
    '.',  // Trace amounts
    ':',  // Sparse
    '-',  // Light density
    '=',  // Low density
    '+',  // Low-medium
    '*',  // Medium
    'o',  // Medium-high
    'O',  // High density
    '#',  // Very high
    '█',  // Solid
    '▓',  // Dense solid
    '▒',  // Super dense
    '░',  // Extremely dense
    '▀',  // Maximum density
    '■',  // Overflow/special
];

/// Edge detection characters for architectural features
const EDGE_CHARS: EdgePalette = EdgePalette {
    horizontal: '─',
    vertical: '│',
    corner_tl: '┌',
    corner_tr: '┐',
    corner_bl: '└',
    corner_br: '┘',
    cross: '┼',
    t_down: '┬',
    t_up: '┴',
    t_right: '├',
    t_left: '┤',
};

#[derive(Clone, Copy)]
struct EdgePalette {
    horizontal: char,
    vertical: char,
    corner_tl: char,
    corner_tr: char,
    corner_bl: char,
    corner_br: char,
    cross: char,
    t_down: char,
    t_up: char,
    t_right: char,
    t_left: char,
}

/// Pixelation settings to match the aesthetic
#[derive(Debug, Clone)]
pub struct PixelationConfig {
    /// Size of each pixel block in millimeters
    pub pixel_size_mm: u32,
    /// View width in pixels
    pub width_pixels: usize,
    /// View height in pixels  
    pub height_pixels: usize,
    /// Depth layers for pseudo-3D effect
    pub depth_layers: usize,
    /// Enable edge detection for architectural lines
    pub edge_detection: bool,
    /// Contrast adjustment (0.5 - 2.0)
    pub contrast: f32,
    /// Brightness adjustment (-1.0 to 1.0)
    pub brightness: f32,
    /// Dithering for smoother gradients
    pub dithering: bool,
}

impl Default for PixelationConfig {
    fn default() -> Self {
        Self {
            pixel_size_mm: 200,      // 20cm blocks
            width_pixels: 120,       // Terminal width
            height_pixels: 40,       // Terminal height
            depth_layers: 4,         // 4 depth planes
            edge_detection: true,
            contrast: 1.2,          // Slight contrast boost
            brightness: 0.1,        // Slight brightness boost
            dithering: true,
        }
    }
}

/// Main pixelated renderer
pub struct PixelatedRenderer {
    config: PixelationConfig,
    /// 3D voxel grid: [x][y][z] -> density
    voxel_grid: Vec<Vec<Vec<f32>>>,
    /// Edge map for architectural features
    edge_map: Vec<Vec<bool>>,
    /// Final rendered frame
    frame_buffer: Vec<Vec<char>>,
}

impl PixelatedRenderer {
    pub fn new(config: PixelationConfig) -> Self {
        let voxel_grid = vec![
            vec![vec![0.0; config.depth_layers]; config.height_pixels]; 
            config.width_pixels
        ];
        
        let edge_map = vec![vec![false; config.height_pixels]; config.width_pixels];
        let frame_buffer = vec![vec![' '; config.width_pixels]; config.height_pixels];
        
        Self {
            config,
            voxel_grid,
            edge_map,
            frame_buffer,
        }
    }
    
    /// Process ArxObjects into voxel grid
    pub fn process_arxobjects(&mut self, objects: &[ArxObject], view_center: (u16, u16, u16)) {
        // Clear voxel grid
        for x in 0..self.config.width_pixels {
            for y in 0..self.config.height_pixels {
                for z in 0..self.config.depth_layers {
                    self.voxel_grid[x][y][z] = 0.0;
                }
            }
        }
        
        // Map ArxObjects to voxels
        for obj in objects {
            // Calculate pixel position relative to view center
            let px = ((obj.x as i32 - view_center.0 as i32) / self.config.pixel_size_mm as i32)
                + (self.config.width_pixels as i32 / 2);
            let py = ((obj.y as i32 - view_center.1 as i32) / self.config.pixel_size_mm as i32)
                + (self.config.height_pixels as i32 / 2);
            let pz = ((obj.z as i32 - view_center.2 as i32) / 1000) // Convert to meters for depth
                .clamp(0, self.config.depth_layers as i32 - 1) as usize;
            
            // Skip if outside view
            if px < 0 || px >= self.config.width_pixels as i32 ||
               py < 0 || py >= self.config.height_pixels as i32 {
                continue;
            }
            
            let px = px as usize;
            let py = py as usize;
            
            // Accumulate density with depth falloff
            let depth_factor = 1.0 / (1.0 + pz as f32 * 0.3);
            self.voxel_grid[px][py][pz] += depth_factor;
            
            // Mark edges based on object type
            if self.is_structural_object(obj.object_type) {
                self.edge_map[px][py] = true;
            }
        }
        
        // Apply image processing
        if self.config.edge_detection {
            self.detect_edges();
        }
        
        self.apply_contrast_brightness();
        
        if self.config.dithering {
            self.apply_dithering();
        }
    }
    
    /// Detect edges for architectural features
    fn detect_edges(&mut self) {
        let mut new_edges = vec![vec![false; self.config.height_pixels]; self.config.width_pixels];
        
        for x in 1..self.config.width_pixels - 1 {
            for y in 1..self.config.height_pixels - 1 {
                let center = self.get_voxel_density(x, y);
                
                // Sobel edge detection
                let gx = self.get_voxel_density(x + 1, y) - self.get_voxel_density(x - 1, y);
                let gy = self.get_voxel_density(x, y + 1) - self.get_voxel_density(x, y - 1);
                
                let edge_strength = (gx * gx + gy * gy).sqrt();
                
                // Mark strong edges
                if edge_strength > 0.5 {
                    new_edges[x][y] = true;
                }
            }
        }
        
        self.edge_map = new_edges;
    }
    
    /// Get combined density across all depth layers
    fn get_voxel_density(&self, x: usize, y: usize) -> f32 {
        if x >= self.config.width_pixels || y >= self.config.height_pixels {
            return 0.0;
        }
        
        let mut total = 0.0;
        for z in 0..self.config.depth_layers {
            total += self.voxel_grid[x][y][z];
        }
        total
    }
    
    /// Apply contrast and brightness adjustments
    fn apply_contrast_brightness(&mut self) {
        for x in 0..self.config.width_pixels {
            for y in 0..self.config.height_pixels {
                for z in 0..self.config.depth_layers {
                    let mut val = self.voxel_grid[x][y][z];
                    
                    // Apply contrast
                    val = ((val - 0.5) * self.config.contrast) + 0.5;
                    
                    // Apply brightness
                    val += self.config.brightness;
                    
                    // Clamp
                    self.voxel_grid[x][y][z] = val.clamp(0.0, 1.0);
                }
            }
        }
    }
    
    /// Apply Floyd-Steinberg dithering for smoother gradients
    fn apply_dithering(&mut self) {
        for y in 0..self.config.height_pixels - 1 {
            for x in 1..self.config.width_pixels - 1 {
                let old_val = self.get_voxel_density(x, y);
                let new_val = (old_val * 15.0).round() / 15.0;
                let error = old_val - new_val;
                
                // Distribute error to neighbors
                if x + 1 < self.config.width_pixels {
                    self.voxel_grid[x + 1][y][0] += error * 7.0 / 16.0;
                }
                if x > 0 && y + 1 < self.config.height_pixels {
                    self.voxel_grid[x - 1][y + 1][0] += error * 3.0 / 16.0;
                }
                if y + 1 < self.config.height_pixels {
                    self.voxel_grid[x][y + 1][0] += error * 5.0 / 16.0;
                }
                if x + 1 < self.config.width_pixels && y + 1 < self.config.height_pixels {
                    self.voxel_grid[x + 1][y + 1][0] += error * 1.0 / 16.0;
                }
            }
        }
    }
    
    /// Check if object type is structural (walls, floors, etc)
    fn is_structural_object(&self, object_type: u8) -> bool {
        use crate::arxobject::object_types::*;
        matches!(object_type, WALL | FLOOR | CEILING | DOOR | WINDOW | COLUMN)
    }
    
    /// Render the final ASCII frame
    pub fn render(&mut self) -> String {
        let mut output = String::new();
        
        // Add top border
        output.push('╔');
        for _ in 0..self.config.width_pixels {
            output.push('═');
        }
        output.push_str("╗\n");
        
        // Render each line
        for y in 0..self.config.height_pixels {
            output.push('║');
            
            for x in 0..self.config.width_pixels {
                let char = if self.edge_map[x][y] && self.config.edge_detection {
                    self.get_edge_char(x, y)
                } else {
                    self.get_density_char(x, y)
                };
                
                output.push(char);
            }
            
            output.push_str("║\n");
        }
        
        // Add bottom border
        output.push('╚');
        for _ in 0..self.config.width_pixels {
            output.push('═');
        }
        output.push_str("╝\n");
        
        output
    }
    
    /// Get appropriate edge character based on neighboring edges
    fn get_edge_char(&self, x: usize, y: usize) -> char {
        let has_left = x > 0 && self.edge_map[x - 1][y];
        let has_right = x < self.config.width_pixels - 1 && self.edge_map[x + 1][y];
        let has_top = y > 0 && self.edge_map[x][y - 1];
        let has_bottom = y < self.config.height_pixels - 1 && self.edge_map[x][y + 1];
        
        match (has_left, has_right, has_top, has_bottom) {
            (true, true, false, false) => EDGE_CHARS.horizontal,
            (false, false, true, true) => EDGE_CHARS.vertical,
            (false, true, false, true) => EDGE_CHARS.corner_tl,
            (true, false, false, true) => EDGE_CHARS.corner_tr,
            (false, true, true, false) => EDGE_CHARS.corner_bl,
            (true, false, true, false) => EDGE_CHARS.corner_br,
            (true, true, true, true) => EDGE_CHARS.cross,
            (true, true, false, true) => EDGE_CHARS.t_down,
            (true, true, true, false) => EDGE_CHARS.t_up,
            (false, true, true, true) => EDGE_CHARS.t_right,
            (true, false, true, true) => EDGE_CHARS.t_left,
            _ => self.get_density_char(x, y),
        }
    }
    
    /// Get character based on voxel density
    fn get_density_char(&self, x: usize, y: usize) -> char {
        let density = self.get_voxel_density(x, y);
        let index = ((density * 15.0).round() as usize).min(15);
        DENSITY_PALETTE[index]
    }
    
    /// Generate statistics about the current view
    pub fn get_stats(&self) -> RenderStats {
        let mut total_objects = 0;
        let mut max_density = 0.0f32;
        
        for x in 0..self.config.width_pixels {
            for y in 0..self.config.height_pixels {
                let density = self.get_voxel_density(x, y);
                if density > 0.0 {
                    total_objects += 1;
                    max_density = max_density.max(density);
                }
            }
        }
        
        RenderStats {
            total_pixels: self.config.width_pixels * self.config.height_pixels,
            occupied_pixels: total_objects,
            max_density,
            edge_pixels: self.edge_map.iter()
                .flat_map(|row| row.iter())
                .filter(|&&e| e)
                .count(),
        }
    }
}

/// Rendering statistics
pub struct RenderStats {
    pub total_pixels: usize,
    pub occupied_pixels: usize,
    pub max_density: f32,
    pub edge_pixels: usize,
}

/// Demo function showing the aesthetic
pub fn demo_aesthetic() {
    println!("\n╔════════════════════════════════════════════════════════════╗");
    println!("║  ArxOS Pixelated Aesthetic Renderer                         ║");
    println!("║  Inspired by Industrial Pixel Art                           ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");
    
    // Create sample ArxObjects representing a room with equipment
    let mut objects = Vec::new();
    
    // Floor
    for x in 0..20 {
        for y in 0..20 {
            objects.push(ArxObject::new(
                42, // building
                crate::arxobject::object_types::FLOOR,
                x * 500, y * 500, 0,
            ));
        }
    }
    
    // Walls
    for x in 0..20 {
        objects.push(ArxObject::new(
            42,
            crate::arxobject::object_types::WALL,
            x * 500, 0, 1500,
        ));
        objects.push(ArxObject::new(
            42,
            crate::arxobject::object_types::WALL,
            x * 500, 9500, 1500,
        ));
    }
    
    // Equipment cluster (like HVAC unit)
    for x in 5..8 {
        for y in 5..8 {
            for z in 0..3 {
                objects.push(ArxObject::new(
                    42,
                    crate::arxobject::object_types::HVAC_VENT,
                    x * 500, y * 500, z * 500,
                ));
            }
        }
    }
    
    // Create renderer with aesthetic config
    let config = PixelationConfig {
        pixel_size_mm: 250,  // Quarter meter blocks
        width_pixels: 80,
        height_pixels: 30,
        depth_layers: 4,
        edge_detection: true,
        contrast: 1.3,
        brightness: 0.0,
        dithering: true,
    };
    
    let mut renderer = PixelatedRenderer::new(config);
    
    // Process and render
    renderer.process_arxobjects(&objects, (5000, 5000, 1000));
    let output = renderer.render();
    
    println!("{}", output);
    
    let stats = renderer.get_stats();
    println!("\n📊 Render Statistics:");
    println!("  Total pixels: {}", stats.total_pixels);
    println!("  Occupied: {} ({:.1}%)", 
        stats.occupied_pixels, 
        stats.occupied_pixels as f32 / stats.total_pixels as f32 * 100.0);
    println!("  Edge pixels: {}", stats.edge_pixels);
    println!("  Max density: {:.2}", stats.max_density);
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_pixelation_basic() {
        let config = PixelationConfig::default();
        let mut renderer = PixelatedRenderer::new(config);
        
        let objects = vec![
            ArxObject::new(42, 0x10, 1000, 1000, 1000),
            ArxObject::new(42, 0x20, 2000, 2000, 1000),
        ];
        
        renderer.process_arxobjects(&objects, (1500, 1500, 1000));
        let output = renderer.render();
        
        assert!(output.contains('║'));
        assert!(output.contains('═'));
    }
    
    #[test]
    fn test_density_mapping() {
        let config = PixelationConfig {
            width_pixels: 10,
            height_pixels: 10,
            ..Default::default()
        };
        
        let mut renderer = PixelatedRenderer::new(config);
        
        // Single object should create visible density
        let objects = vec![
            ArxObject::new(42, 0x10, 5000, 5000, 1000),
        ];
        
        renderer.process_arxobjects(&objects, (5000, 5000, 1000));
        let density = renderer.get_voxel_density(5, 5);
        assert!(density > 0.0);
    }
}