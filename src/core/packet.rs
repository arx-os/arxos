//! Unified packet structure for slow-bleed architecture
//!
//! All packets are exactly 13 bytes for consistency across the mesh

#![cfg_attr(not(feature = "std"), no_std)]

use crate::ArxObject;

/// Universal 13-byte packet for mesh network
#[repr(C, packed)]
#[derive(Copy, Clone, Debug)]
pub struct MeshPacket {
    /// Packet type: 0x00-0x7F for live, 0x80-0xFF for detail chunks
    pub packet_type: u8,
    /// Type-specific payload (12 bytes)
    pub payload: [u8; 12],
}

impl MeshPacket {
    pub const SIZE: usize = 13;
    
    /// Create a live update packet
    pub fn live_update(object: &ArxObject) -> Self {
        let mut payload = [0u8; 12];
        
        // Pack ArxObject into payload
        payload[0..2].copy_from_slice(&object.id.to_le_bytes());
        payload[2..4].copy_from_slice(&object.x.to_le_bytes());
        payload[4..6].copy_from_slice(&object.y.to_le_bytes());
        payload[6..8].copy_from_slice(&object.z.to_le_bytes());
        payload[8..12].copy_from_slice(&object.properties);
        
        Self {
            packet_type: object.object_type & 0x7F,  // Ensure live range
            payload,
        }
    }
    
    /// Create a detail chunk packet
    pub fn detail_chunk(object_id: u16, chunk_id: u16, chunk_type: ChunkType, data: &[u8]) -> Self {
        let mut payload = [0u8; 12];
        
        payload[0..2].copy_from_slice(&object_id.to_le_bytes());
        payload[2..4].copy_from_slice(&chunk_id.to_le_bytes());
        payload[4..12].copy_from_slice(&data[..8.min(data.len())]);
        
        Self {
            packet_type: chunk_type as u8,
            payload,
        }
    }
    
    /// Check if this is a live update packet
    pub fn is_live(&self) -> bool {
        self.packet_type < 0x80
    }
    
    /// Check if this is a detail chunk packet
    pub fn is_detail(&self) -> bool {
        self.packet_type >= 0x80
    }
    
    /// Extract object ID from packet
    pub fn object_id(&self) -> u16 {
        u16::from_le_bytes([self.payload[0], self.payload[1]])
    }
}

/// Types of detail chunks in slow-bleed protocol
#[repr(u8)]
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum ChunkType {
    // Material Properties (0x80-0x8F)
    MaterialDensity = 0x80,
    MaterialThermal = 0x81,
    MaterialAcoustic = 0x82,
    MaterialStructural = 0x83,
    MaterialVisual = 0x84,
    
    // Historical Data (0x90-0x9F)
    MaintenanceHistory = 0x90,
    PerformanceHistory = 0x91,
    FailureHistory = 0x92,
    EnergyHistory = 0x93,
    
    // Relationships (0xA0-0xAF)
    ElectricalConnections = 0xA0,
    HVACConnections = 0xA1,
    PlumbingConnections = 0xA2,
    StructuralSupports = 0xA3,
    DataConnections = 0xA4,
    
    // Simulation Models (0xB0-0xBF)
    ThermalModel = 0xB0,
    AirflowModel = 0xB1,
    ElectricalModel = 0xB2,
    StructuralModel = 0xB3,
    
    // Predictive Data (0xC0-0xCF)
    FailurePrediction = 0xC0,
    MaintenanceSchedule = 0xC1,
    OptimizationParams = 0xC2,
    EnergyForecast = 0xC3,
    
    // CAD Geometry (0xD0-0xDF)
    DetailedGeometry = 0xD0,
    SurfaceProperties = 0xD1,
    Dimensions = 0xD2,
    Tolerances = 0xD3,
}

/// Detail chunk with metadata
#[derive(Clone, Debug)]
pub struct DetailChunk {
    pub object_id: u16,
    pub chunk_id: u16,
    pub chunk_type: ChunkType,
    pub data: [u8; 8],
    pub timestamp: u32,  // When received/created
}

impl DetailChunk {
    /// Create from a detail packet
    pub fn from_packet(packet: &MeshPacket, timestamp: u32) -> Option<Self> {
        if !packet.is_detail() {
            return None;
        }
        
        Some(Self {
            object_id: u16::from_le_bytes([packet.payload[0], packet.payload[1]]),
            chunk_id: u16::from_le_bytes([packet.payload[2], packet.payload[3]]),
            chunk_type: unsafe { core::mem::transmute(packet.packet_type) },
            data: packet.payload[4..12].try_into().unwrap(),
            timestamp,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_packet_size() {
        assert_eq!(core::mem::size_of::<MeshPacket>(), 13);
    }
    
    #[test]
    fn test_live_packet() {
        let obj = ArxObject::new(0x1234, 0x10, 100, 200, 300);
        let packet = MeshPacket::live_update(&obj);
        
        assert!(packet.is_live());
        assert_eq!(packet.object_id(), 0x1234);
    }
    
    #[test]
    fn test_detail_packet() {
        let packet = MeshPacket::detail_chunk(
            0x5678,
            42,
            ChunkType::MaterialDensity,
            &[1, 2, 3, 4, 5, 6, 7, 8]
        );
        
        assert!(packet.is_detail());
        assert_eq!(packet.object_id(), 0x5678);
    }
}