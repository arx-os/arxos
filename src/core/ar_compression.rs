//! AR to ArxObject Compression Algorithm
//! 
//! Converts high-resolution AR drawings and LiDAR scans into compressed
//! 13-byte ArxObjects that can be transmitted over low-bandwidth radio networks
//! and procedurally reconstructed on the receiving end.

use crate::arxobject::{ArxObject, object_types};

/// AR path drawing types that can be compressed
#[derive(Debug, Clone, Copy)]
pub enum ARPathType {
    /// Electrical conduit routing
    ElectricalConduit = 0x80,
    /// HVAC ductwork path
    HVACDuct = 0x81,
    /// Plumbing pipe route
    PlumbingPipe = 0x82,
    /// Network cable path
    NetworkCable = 0x83,
    /// Fire suppression line
    FireSuppression = 0x84,
    /// Emergency egress route
    EmergencyExit = 0x85,
    /// Maintenance access path
    MaintenanceAccess = 0x86,
}

/// AR drawing primitive that gets compressed
#[derive(Debug, Clone)]
pub struct ARDrawingPrimitive {
    /// Type of path being drawn
    pub path_type: ARPathType,
    /// Start position in millimeters (from LiDAR)
    pub start: (f32, f32, f32),
    /// End position in millimeters
    pub end: (f32, f32, f32),
    /// Obstacle being avoided (if any)
    pub obstacle_id: Option<u16>,
    /// Bend radius for curved sections
    pub bend_radius: Option<f32>,
    /// Annotation flags
    pub annotations: AnnotationFlags,
}

/// Annotation flags that fit in 1 byte
#[derive(Debug, Clone, Copy)]
pub struct AnnotationFlags {
    /// Critical safety issue
    pub safety_critical: bool,
    /// Code violation
    pub code_violation: bool,
    /// Requires supervisor approval
    pub needs_approval: bool,
    /// Temporary routing
    pub temporary: bool,
    /// Cost impact
    pub cost_impact: bool,
    /// Schedule impact  
    pub schedule_impact: bool,
    /// Material change
    pub material_change: bool,
    /// Tool requirement change
    pub tool_change: bool,
}

impl AnnotationFlags {
    /// Pack into single byte
    pub fn to_byte(&self) -> u8 {
        let mut byte = 0u8;
        if self.safety_critical { byte |= 0x80; }
        if self.code_violation { byte |= 0x40; }
        if self.needs_approval { byte |= 0x20; }
        if self.temporary { byte |= 0x10; }
        if self.cost_impact { byte |= 0x08; }
        if self.schedule_impact { byte |= 0x04; }
        if self.material_change { byte |= 0x02; }
        if self.tool_change { byte |= 0x01; }
        byte
    }
    
    /// Unpack from byte
    pub fn from_byte(byte: u8) -> Self {
        Self {
            safety_critical: byte & 0x80 != 0,
            code_violation: byte & 0x40 != 0,
            needs_approval: byte & 0x20 != 0,
            temporary: byte & 0x10 != 0,
            cost_impact: byte & 0x08 != 0,
            schedule_impact: byte & 0x04 != 0,
            material_change: byte & 0x02 != 0,
            tool_change: byte & 0x01 != 0,
        }
    }
}

/// Compressor for AR drawings to ArxObjects
pub struct ARCompressor {
    /// Building context for relative positioning
    building_id: u16,
    /// Current sequence number for multi-packet paths
    sequence: u8,
    /// Spatial resolution (mm per unit)
    resolution: f32,
}

impl ARCompressor {
    pub fn new(building_id: u16) -> Self {
        Self {
            building_id,
            sequence: 0,
            resolution: 10.0, // 1cm resolution default
        }
    }
    
    /// Compress AR drawing primitive into ArxObject(s)
    pub fn compress_drawing(&mut self, drawing: &ARDrawingPrimitive) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        
        // Calculate compressed positions (16-bit millimeters -> centimeters)
        let start_x = (drawing.start.0 / self.resolution) as u16;
        let start_y = (drawing.start.1 / self.resolution) as u16;
        let start_z = (drawing.start.2 / self.resolution) as u16;
        
        // Calculate delta to end (more efficient than absolute)
        let delta_x = ((drawing.end.0 - drawing.start.0) / self.resolution) as i16;
        let delta_y = ((drawing.end.1 - drawing.start.1) / self.resolution) as i16;
        let delta_z = ((drawing.end.2 - drawing.start.2) / self.resolution) as i16;
        
        // First ArxObject: Start point + path type
        objects.push(ArxObject {
            building_id: self.building_id,
            object_type: drawing.path_type as u8,
            x: start_x,
            y: start_y,
            z: start_z,
            properties: [
                self.sequence,                    // Sequence number
                drawing.annotations.to_byte(),     // Annotation flags
                (delta_x >> 8) as u8,             // High byte of X delta
                (delta_x & 0xFF) as u8,           // Low byte of X delta
            ],
        });
        
        // Second ArxObject: End point + deltas
        if delta_y != 0 || delta_z != 0 || drawing.obstacle_id.is_some() {
            self.sequence += 1;
            
            let obstacle_bytes = drawing.obstacle_id
                .map(|id| id.to_le_bytes())
                .unwrap_or([0xFF, 0xFF]); // 0xFFFF = no obstacle
            
            objects.push(ArxObject {
                building_id: self.building_id,
                object_type: 0xA0, // PATH_SEGMENT marker
                x: (delta_y.abs() as u16),
                y: (delta_z.abs() as u16),
                z: 0, // Unused in segment
                properties: [
                    self.sequence,
                    ((delta_y < 0) as u8) << 7 | ((delta_z < 0) as u8) << 6,
                    obstacle_bytes[0],
                    obstacle_bytes[1],
                ],
            });
        }
        
        // Third ArxObject: Complex curves (if needed)
        if let Some(radius) = drawing.bend_radius {
            self.sequence += 1;
            
            let radius_cm = (radius / 10.0) as u16;
            
            objects.push(ArxObject {
                building_id: self.building_id,
                object_type: 0xA1, // PATH_CURVE marker
                x: radius_cm,
                y: 0, // Curve start angle
                z: 0, // Curve end angle
                properties: [
                    self.sequence,
                    0, // Curve direction
                    0, // Reserved
                    0, // Reserved
                ],
            });
        }
        
        self.sequence += 1;
        objects
    }
    
    /// Compress a complex multi-segment path
    pub fn compress_path(&mut self, segments: &[ARDrawingPrimitive]) -> Vec<ArxObject> {
        let mut all_objects = Vec::new();
        
        // Reset sequence for new path
        self.sequence = 0;
        
        // Add path header
        all_objects.push(ArxObject {
            building_id: self.building_id,
            object_type: 0xA2, // PATH_HEADER
            x: segments.len() as u16,
            y: 0,
            z: 0,
            properties: [
                0, // Path ID
                segments[0].path_type as u8,
                0, // Total length high byte (calculated)
                0, // Total length low byte
            ],
        });
        
        // Compress each segment
        for segment in segments {
            all_objects.extend(self.compress_drawing(segment));
        }
        
        // Add path terminator
        all_objects.push(ArxObject {
            building_id: self.building_id,
            object_type: 0xA3, // PATH_END
            x: 0,
            y: 0,
            z: 0,
            properties: [self.sequence, 0, 0, 0],
        });
        
        all_objects
    }
}

/// Decompressor for reconstructing AR drawings from ArxObjects
pub struct ARDecompressor {
    /// Current path being reconstructed
    current_path: Vec<ARDrawingPrimitive>,
    /// Expected sequence number
    expected_sequence: u8,
    /// Spatial resolution
    resolution: f32,
}

impl ARDecompressor {
    pub fn new() -> Self {
        Self {
            current_path: Vec::new(),
            expected_sequence: 0,
            resolution: 10.0,
        }
    }
    
    /// Process received ArxObject and reconstruct drawing
    pub fn process_object(&mut self, obj: &ArxObject) -> Option<Vec<ARDrawingPrimitive>> {
        match obj.object_type {
            // Path type objects (0x80-0x86)
            0x80..=0x86 => {
                // Start of new path segment
                let path_type = match obj.object_type {
                    0x80 => ARPathType::ElectricalConduit,
                    0x81 => ARPathType::HVACDuct,
                    0x82 => ARPathType::PlumbingPipe,
                    0x83 => ARPathType::NetworkCable,
                    0x84 => ARPathType::FireSuppression,
                    0x85 => ARPathType::EmergencyExit,
                    0x86 => ARPathType::MaintenanceAccess,
                    _ => return None,
                };
                
                let start_x = obj.x as f32 * self.resolution;
                let start_y = obj.y as f32 * self.resolution;
                let start_z = obj.z as f32 * self.resolution;
                
                // Extract delta from properties
                let delta_x = i16::from_le_bytes([obj.properties[3], obj.properties[2]]);
                
                let primitive = ARDrawingPrimitive {
                    path_type,
                    start: (start_x, start_y, start_z),
                    end: (
                        start_x + (delta_x as f32 * self.resolution),
                        start_y, // Will be updated by next packet
                        start_z, // Will be updated by next packet
                    ),
                    obstacle_id: None,
                    bend_radius: None,
                    annotations: AnnotationFlags::from_byte(obj.properties[1]),
                };
                
                self.current_path.push(primitive);
                self.expected_sequence = obj.properties[0] + 1;
                None
            }
            
            // Path segment continuation
            0xA0 => {
                if let Some(last) = self.current_path.last_mut() {
                    // Update end position with Y and Z deltas
                    let delta_y = obj.x as i16 * if obj.properties[1] & 0x80 != 0 { -1 } else { 1 };
                    let delta_z = obj.y as i16 * if obj.properties[1] & 0x40 != 0 { -1 } else { 1 };
                    
                    last.end.1 = last.start.1 + (delta_y as f32 * self.resolution);
                    last.end.2 = last.start.2 + (delta_z as f32 * self.resolution);
                    
                    // Extract obstacle ID
                    let obstacle_id = u16::from_le_bytes([obj.properties[2], obj.properties[3]]);
                    if obstacle_id != 0xFFFF {
                        last.obstacle_id = Some(obstacle_id);
                    }
                }
                None
            }
            
            // Path curve
            0xA1 => {
                if let Some(last) = self.current_path.last_mut() {
                    last.bend_radius = Some(obj.x as f32 * 10.0); // Convert back to mm
                }
                None
            }
            
            // Path end - return completed path
            0xA3 => {
                let path = self.current_path.clone();
                self.current_path.clear();
                self.expected_sequence = 0;
                Some(path)
            }
            
            _ => None,
        }
    }
    
    /// Generate procedural interpolation between points
    pub fn interpolate_path(&self, primitives: &[ARDrawingPrimitive]) -> Vec<(f32, f32, f32)> {
        let mut points = Vec::new();
        
        for primitive in primitives {
            // Simple linear interpolation for now
            let steps = 20;
            for i in 0..=steps {
                let t = i as f32 / steps as f32;
                points.push((
                    primitive.start.0 + (primitive.end.0 - primitive.start.0) * t,
                    primitive.start.1 + (primitive.end.1 - primitive.start.1) * t,
                    primitive.start.2 + (primitive.end.2 - primitive.start.2) * t,
                ));
            }
        }
        
        points
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_ar_compression_round_trip() {
        let mut compressor = ARCompressor::new(0x0042);
        let mut decompressor = ARDecompressor::new();
        
        // Create test AR drawing
        let drawing = ARDrawingPrimitive {
            path_type: ARPathType::ElectricalConduit,
            start: (1000.0, 2000.0, 2800.0),
            end: (3000.0, 2000.0, 2800.0),
            obstacle_id: Some(0x1234),
            bend_radius: Some(500.0),
            annotations: AnnotationFlags {
                safety_critical: true,
                needs_approval: true,
                ..Default::default()
            },
        };
        
        // Compress to ArxObjects
        let objects = compressor.compress_drawing(&drawing);
        assert!(objects.len() <= 3); // Should fit in 3 packets or less
        
        // Calculate total bytes
        let total_bytes = objects.len() * 13;
        assert!(total_bytes <= 39); // 3 packets max
        
        // Decompress
        for obj in &objects {
            decompressor.process_object(obj);
        }
    }
    
    #[test]
    fn test_annotation_flags() {
        let flags = AnnotationFlags {
            safety_critical: true,
            code_violation: false,
            needs_approval: true,
            temporary: false,
            cost_impact: true,
            schedule_impact: false,
            material_change: false,
            tool_change: true,
        };
        
        let byte = flags.to_byte();
        assert_eq!(byte, 0xA9); // 10101001
        
        let restored = AnnotationFlags::from_byte(byte);
        assert_eq!(restored.safety_critical, flags.safety_critical);
        assert_eq!(restored.needs_approval, flags.needs_approval);
        assert_eq!(restored.cost_impact, flags.cost_impact);
        assert_eq!(restored.tool_change, flags.tool_change);
    }
}

impl Default for AnnotationFlags {
    fn default() -> Self {
        Self {
            safety_critical: false,
            code_violation: false,
            needs_approval: false,
            temporary: false,
            cost_impact: false,
            schedule_impact: false,
            material_change: false,
            tool_change: false,
        }
    }
}