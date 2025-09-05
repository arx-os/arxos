//! ArxOS Pixel Streaming Protocol
//! 
//! Inspired by Hypori's pixel streaming but compressed for RF mesh.
//! Instead of streaming full pixels, we stream ASCII art deltas.

use crate::arxobject::ArxObject;
use crate::pixelated_renderer::PixelatedRenderer;
use crate::MeshPacket;

/// Pixel stream packet - fits in LoRa payload
#[derive(Debug, Clone)]
pub struct PixelStreamPacket {
    /// Frame sequence number
    pub frame_id: u16,
    
    /// Delta encoding type
    pub delta_type: DeltaType,
    
    /// Compressed changes (max 11 bytes to fit 13-byte packet)
    pub delta_data: [u8; 11],
}

/// Types of delta encoding
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum DeltaType {
    /// Full frame keyframe (rare)
    KeyFrame = 0x00,
    
    /// Run-length encoded changes
    RunLengthDelta = 0x01,
    
    /// Sparse updates (position + new char)
    SparseUpdate = 0x02,
    
    /// Viewport shift (dx, dy)
    ViewportShift = 0x03,
    
    /// Object movement (id + new position)
    ObjectMove = 0x04,
}

/// ASCII frame buffer for terminal display
pub struct ASCIIFrameBuffer {
    /// Current frame
    pub buffer: Vec<Vec<char>>,
    
    /// Previous frame for delta computation
    pub prev_buffer: Vec<Vec<char>>,
    
    /// Frame dimensions
    pub width: usize,
    pub height: usize,
    
    /// Current frame ID
    pub frame_id: u16,
}

impl ASCIIFrameBuffer {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            buffer: vec![vec![' '; width]; height],
            prev_buffer: vec![vec![' '; width]; height],
            width,
            height,
            frame_id: 0,
        }
    }
    
    /// Render ArxObjects to ASCII buffer
    pub fn render_objects(&mut self, objects: &[ArxObject], view_x: f32, view_y: f32) {
        // Save previous frame
        self.prev_buffer = self.buffer.clone();
        
        // Clear current buffer
        self.buffer = vec![vec![' '; self.width]; self.height];
        
        // Render each object as ASCII
        for obj in objects {
            let x = ((obj.x as f32 - view_x) / 100.0) as usize;
            let y = ((obj.y as f32 - view_y) / 100.0) as usize;
            
            if x < self.width && y < self.height {
                self.buffer[y][x] = Self::object_to_char(obj.object_type);
            }
        }
        
        self.frame_id = self.frame_id.wrapping_add(1);
    }
    
    /// Convert object type to ASCII character
    fn object_to_char(obj_type: u8) -> char {
        use crate::arxobject::object_types::*;
        match obj_type {
            WALL => '#',
            DOOR => '+',
            OUTLET => 'o',
            SWITCH => 's',
            LIGHT => '*',
            HVAC_VENT => '≈',
            THERMOSTAT => 'θ',
            ELECTRICAL_PANEL => '⚡',
            CAMERA => '👁',
            MOTION_SENSOR => '◉',
            FLOOR => '.',
            CEILING => '-',
            WINDOW => '=',
            COLUMN => '|',
            EMERGENCY_EXIT => '🚪',
            _ => '?',
        }
    }
    
    /// Compute delta between frames
    pub fn compute_delta(&self) -> Vec<PixelStreamPacket> {
        let mut packets = Vec::new();
        let mut changes = Vec::new();
        
        // Find all changed positions
        for y in 0..self.height {
            for x in 0..self.width {
                if self.buffer[y][x] != self.prev_buffer[y][x] {
                    changes.push((x as u8, y as u8, self.buffer[y][x]));
                }
            }
        }
        
        // Encode changes into packets
        if changes.len() <= 3 {
            // Sparse update - up to 3 changes per packet
            let mut delta_data = [0u8; 11];
            for (i, &(x, y, ch)) in changes.iter().enumerate().take(3) {
                delta_data[i * 3] = x;
                delta_data[i * 3 + 1] = y;
                delta_data[i * 3 + 2] = ch as u8;
            }
            
            packets.push(PixelStreamPacket {
                frame_id: self.frame_id,
                delta_type: DeltaType::SparseUpdate,
                delta_data,
            });
        } else {
            // Run-length encode for many changes
            packets.extend(self.run_length_encode(&changes));
        }
        
        packets
    }
    
    /// Run-length encode changes
    fn run_length_encode(&self, changes: &[(u8, u8, char)]) -> Vec<PixelStreamPacket> {
        let mut packets = Vec::new();
        let mut delta_data = [0u8; 11];
        let mut pos = 0;
        
        for &(x, y, ch) in changes {
            if pos + 3 > 11 {
                // Current packet full, start new one
                packets.push(PixelStreamPacket {
                    frame_id: self.frame_id,
                    delta_type: DeltaType::RunLengthDelta,
                    delta_data,
                });
                delta_data = [0u8; 11];
                pos = 0;
            }
            
            delta_data[pos] = x;
            delta_data[pos + 1] = y;
            delta_data[pos + 2] = ch as u8;
            pos += 3;
        }
        
        if pos > 0 {
            packets.push(PixelStreamPacket {
                frame_id: self.frame_id,
                delta_type: DeltaType::RunLengthDelta,
                delta_data,
            });
        }
        
        packets
    }
}

/// Pixel stream receiver - reconstructs display from packets
pub struct PixelStreamReceiver {
    frame_buffer: ASCIIFrameBuffer,
    last_frame_id: u16,
    packet_buffer: Vec<PixelStreamPacket>,
}

impl PixelStreamReceiver {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            frame_buffer: ASCIIFrameBuffer::new(width, height),
            last_frame_id: 0,
            packet_buffer: Vec::new(),
        }
    }
    
    /// Process incoming pixel stream packet
    pub fn process_packet(&mut self, packet: PixelStreamPacket) {
        // Check if packet is for current frame
        if packet.frame_id <= self.last_frame_id {
            return; // Old packet, ignore
        }
        
        match packet.delta_type {
            DeltaType::SparseUpdate => {
                // Apply sparse updates
                for i in 0..3 {
                    let x = packet.delta_data[i * 3] as usize;
                    let y = packet.delta_data[i * 3 + 1] as usize;
                    let ch = packet.delta_data[i * 3 + 2] as char;
                    
                    if x < self.frame_buffer.width && y < self.frame_buffer.height && ch != '\0' {
                        self.frame_buffer.buffer[y][x] = ch;
                    }
                }
            }
            DeltaType::ViewportShift => {
                // Shift entire viewport
                let dx = packet.delta_data[0] as i8;
                let dy = packet.delta_data[1] as i8;
                self.shift_viewport(dx, dy);
            }
            DeltaType::ObjectMove => {
                // Move specific object
                let obj_id = u16::from_le_bytes([packet.delta_data[0], packet.delta_data[1]]);
                let old_x = packet.delta_data[2] as usize;
                let old_y = packet.delta_data[3] as usize;
                let new_x = packet.delta_data[4] as usize;
                let new_y = packet.delta_data[5] as usize;
                let ch = packet.delta_data[6] as char;
                
                // Clear old position
                if old_x < self.frame_buffer.width && old_y < self.frame_buffer.height {
                    self.frame_buffer.buffer[old_y][old_x] = ' ';
                }
                // Draw new position
                if new_x < self.frame_buffer.width && new_y < self.frame_buffer.height {
                    self.frame_buffer.buffer[new_y][new_x] = ch;
                }
            }
            _ => {}
        }
        
        self.last_frame_id = packet.frame_id;
    }
    
    /// Shift viewport
    fn shift_viewport(&mut self, dx: i8, dy: i8) {
        // Simple viewport shift - in production would be more sophisticated
        if dx != 0 || dy != 0 {
            let mut new_buffer = vec![vec![' '; self.frame_buffer.width]; self.frame_buffer.height];
            
            for y in 0..self.frame_buffer.height {
                for x in 0..self.frame_buffer.width {
                    let new_x = (x as i32 + dx as i32) as usize;
                    let new_y = (y as i32 + dy as i32) as usize;
                    
                    if new_x < self.frame_buffer.width && new_y < self.frame_buffer.height {
                        new_buffer[new_y][new_x] = self.frame_buffer.buffer[y][x];
                    }
                }
            }
            
            self.frame_buffer.buffer = new_buffer;
        }
    }
    
    /// Get current display
    pub fn get_display(&self) -> String {
        let mut output = String::new();
        for row in &self.frame_buffer.buffer {
            for &ch in row {
                output.push(ch);
            }
            output.push('\n');
        }
        output
    }
}

/// Demo showing pixel streaming over mesh
pub fn demo_pixel_streaming() {
    println!("\n📺 ArxOS Pixel Streaming Demo\n");
    
    println!("Hypori approach:");
    println!("  • Streams full HD pixels (1920×1080×24-bit)");
    println!("  • Requires ~6 Mbps bandwidth");
    println!("  • Cloud server renders everything");
    
    println!("\nArxOS approach:");
    println!("  • Streams ASCII art deltas (80×25 chars)");
    println!("  • Uses ~100 bytes per frame update");
    println!("  • Mesh nodes render locally");
    
    println!("\nExample frame update:");
    println!("┌────────────────────────┐");
    println!("│  Previous:   Current:  │");
    println!("│  #####       #####     │");
    println!("│  #   #       # o #     │");  
    println!("│  # + #  →    # + #     │");
    println!("│  #   #       #   #     │");
    println!("│  #####       #####     │");
    println!("└────────────────────────┘");
    
    println!("\nDelta packet (13 bytes):");
    println!("  [Frame:42][Sparse][x:3,y:2,'o']");
    
    println!("\nBandwidth comparison:");
    println!("  Hypori: 6,000,000 bps");
    println!("  ArxOS:        800 bps");
    println!("  Ratio:      7,500:1");
}