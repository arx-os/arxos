//! Meshtastic Protocol Handler for Arxos
//!
//! Handles building intelligence queries over the meshtastic mesh network.
//! Maintains air-gapped communication while providing terminal access.
#![forbid(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used, clippy::pedantic, clippy::nursery)]
#![cfg_attr(test, allow(clippy::unwrap_used, clippy::expect_used))]
#![allow(clippy::module_name_repetitions, clippy::too_many_lines, clippy::missing_errors_doc)]

use crate::arxobject::ArxObject;
use async_trait::async_trait;
use std::collections::HashMap;
use thiserror::Error;

/// Meshtastic protocol errors
#[derive(Error, Debug)]
pub enum MeshtasticProtocolError {
    #[error("Invalid packet format: {0}")]
    InvalidPacket(String),
    
    #[error("Query parsing error: {0}")]
    QueryParsingError(String),
    
    #[error("Database error: {0}")]
    DatabaseError(String),
    
    #[error("Network error: {0}")]
    NetworkError(String),
}

/// Meshtastic packet types for Arxos
#[derive(Debug, Clone, PartialEq)]
pub enum MeshtasticPacketType {
    /// Building query request
    QueryRequest = 0x10,
    /// Building query response
    QueryResponse = 0x11,
    /// ArxObject broadcast
    ArxObjectBroadcast = 0x12,
    /// Status request
    StatusRequest = 0x13,
    /// Status response
    StatusResponse = 0x14,
    /// Heartbeat
    Heartbeat = 0x15,
}

impl TryFrom<u8> for MeshtasticPacketType {
    type Error = MeshtasticProtocolError;
    
    fn try_from(value: u8) -> Result<Self, Self::Error> {
        match value {
            0x10 => Ok(MeshtasticPacketType::QueryRequest),
            0x11 => Ok(MeshtasticPacketType::QueryResponse),
            0x12 => Ok(MeshtasticPacketType::ArxObjectBroadcast),
            0x13 => Ok(MeshtasticPacketType::StatusRequest),
            0x14 => Ok(MeshtasticPacketType::StatusResponse),
            0x15 => Ok(MeshtasticPacketType::Heartbeat),
            _ => Err(MeshtasticProtocolError::InvalidPacket(
                format!("Unknown packet type: 0x{:02X}", value)
            )),
        }
    }
}

/// Meshtastic packet for Arxos
#[derive(Debug, Clone)]
pub struct MeshtasticPacket {
    pub source_id: u32,
    pub dest_id: u32,
    pub packet_type: MeshtasticPacketType,
    pub sequence: u16,
    pub payload: Vec<u8>,
}

impl MeshtasticPacket {
    /// Create a new meshtastic packet
    pub fn new(
        source_id: u32,
        dest_id: u32,
        packet_type: MeshtasticPacketType,
        sequence: u16,
        payload: Vec<u8>,
    ) -> Self {
        Self {
            source_id,
            dest_id,
            packet_type,
            sequence,
            payload,
        }
    }
    
    /// Create a building query request
    pub fn new_query_request(
        source_id: u32,
        dest_id: u32,
        query: &str,
        sequence: u16,
    ) -> Self {
        Self::new(
            source_id,
            dest_id,
            MeshtasticPacketType::QueryRequest,
            sequence,
            query.as_bytes().to_vec(),
        )
    }
    
    /// Create a building query response
    pub fn new_query_response(
        source_id: u32,
        dest_id: u32,
        response: &str,
        sequence: u16,
    ) -> Self {
        Self::new(
            source_id,
            dest_id,
            MeshtasticPacketType::QueryResponse,
            sequence,
            response.as_bytes().to_vec(),
        )
    }
    
    /// Create an ArxObject broadcast
    pub fn new_arxobject_broadcast(
        source_id: u32,
        dest_id: u32,
        arxobject: &ArxObject,
        sequence: u16,
    ) -> Self {
        let payload = arxobject.to_bytes().to_vec();
        Self::new(
            source_id,
            dest_id,
            MeshtasticPacketType::ArxObjectBroadcast,
            sequence,
            payload,
        )
    }
    
    /// Serialize packet to bytes
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::new();
        
        // Header: source_id (4 bytes) + dest_id (4 bytes) + type (1 byte) + sequence (2 bytes)
        bytes.extend_from_slice(&self.source_id.to_le_bytes());
        bytes.extend_from_slice(&self.dest_id.to_le_bytes());
        bytes.push(self.packet_type.clone() as u8);
        bytes.extend_from_slice(&self.sequence.to_le_bytes());
        
        // Payload length (2 bytes)
        bytes.extend_from_slice(&(self.payload.len() as u16).to_le_bytes());
        
        // Payload
        bytes.extend_from_slice(&self.payload);
        
        bytes
    }
    
    /// Deserialize packet from bytes
    pub fn from_bytes(data: &[u8]) -> Result<Self, MeshtasticProtocolError> {
        if data.len() < 13 {
            return Err(MeshtasticProtocolError::InvalidPacket(
                "Packet too short".to_string()
            ));
        }
        
        let mut offset = 0;
        
        // Parse header
        let source_id = u32::from_le_bytes([
            data[offset], data[offset + 1], data[offset + 2], data[offset + 3]
        ]);
        offset += 4;
        
        let dest_id = u32::from_le_bytes([
            data[offset], data[offset + 1], data[offset + 2], data[offset + 3]
        ]);
        offset += 4;
        
        let packet_type = MeshtasticPacketType::try_from(data[offset])?;
        offset += 1;
        
        let sequence = u16::from_le_bytes([data[offset], data[offset + 1]]);
        offset += 2;
        
        let payload_len = u16::from_le_bytes([data[offset], data[offset + 1]]) as usize;
        offset += 2;
        
        if data.len() < offset + payload_len {
            return Err(MeshtasticProtocolError::InvalidPacket(
                "Payload length mismatch".to_string()
            ));
        }
        
        let payload = data[offset..offset + payload_len].to_vec();
        
        Ok(Self {
            source_id,
            dest_id,
            packet_type,
            sequence,
            payload,
        })
    }
}

/// Building query types
#[derive(Debug, Clone, PartialEq)]
pub enum BuildingQuery {
    /// Query by room number
    RoomQuery { room: String },
    /// Query by object type
    TypeQuery { object_type: u8 },
    /// Query by building ID
    BuildingQuery { building_id: u16 },
    /// Query by status
    StatusQuery { status: String },
    /// Complex query with multiple criteria
    ComplexQuery { criteria: HashMap<String, String> },
}

impl BuildingQuery {
    /// Parse query from string
    pub fn parse(query: &str) -> Result<Self, MeshtasticProtocolError> {
        let query = query.trim();
        
        // Simple room query: "room:127"
        if let Some(room) = query.strip_prefix("room:") {
            return Ok(BuildingQuery::RoomQuery {
                room: room.to_string(),
            });
        }
        
        // Type query: "type:outlet"
        if let Some(type_str) = query.strip_prefix("type:") {
            let object_type = match type_str {
                "outlet" => 0x10,
                "light" => 0x20,
                "sensor" => 0x30,
                "hvac" => 0x40,
                "door" => 0x50,
                "window" => 0x60,
                _ => return Err(MeshtasticProtocolError::QueryParsingError(
                    format!("Unknown object type: {}", type_str)
                )),
            };
            return Ok(BuildingQuery::TypeQuery { object_type });
        }
        
        // Building query: "building:0x0001"
        if let Some(building_str) = query.strip_prefix("building:") {
            let building_id = if let Some(hex_str) = building_str.strip_prefix("0x") {
                u16::from_str_radix(hex_str, 16)
                    .map_err(|_| MeshtasticProtocolError::QueryParsingError(
                        "Invalid building ID format".to_string()
                    ))?
            } else {
                building_str.parse()
                    .map_err(|_| MeshtasticProtocolError::QueryParsingError(
                        "Invalid building ID format".to_string()
                    ))?
            };
            return Ok(BuildingQuery::BuildingQuery { building_id });
        }
        
        // Status query: "status:faulty"
        if let Some(status) = query.strip_prefix("status:") {
            return Ok(BuildingQuery::StatusQuery {
                status: status.to_string(),
            });
        }
        
        // Complex query parsing (basic implementation)
        if query.contains(':') {
            let mut criteria = HashMap::new();
            for part in query.split_whitespace() {
                if let Some((key, value)) = part.split_once(':') {
                    criteria.insert(key.to_string(), value.to_string());
                }
            }
            return Ok(BuildingQuery::ComplexQuery { criteria });
        }
        
        Err(MeshtasticProtocolError::QueryParsingError(
            format!("Unable to parse query: {}", query)
        ))
    }
}

/// Trait for handling meshtastic protocol operations
#[async_trait]
pub trait MeshtasticProtocolHandler {
    /// Handle incoming meshtastic packet
    async fn handle_packet(&mut self, packet: MeshtasticPacket) -> Result<Option<MeshtasticPacket>, MeshtasticProtocolError>;
    
    /// Process building query
    async fn process_query(&mut self, query: BuildingQuery) -> Result<String, MeshtasticProtocolError>;
    
    /// Get node status
    async fn get_status(&self) -> Result<String, MeshtasticProtocolError>;
    
    /// Broadcast ArxObject
    async fn broadcast_arxobject(&mut self, arxobject: &ArxObject) -> Result<(), MeshtasticProtocolError>;
}

/// Mock implementation for testing
pub struct MockMeshtasticHandler {
    pub arxobjects: Vec<ArxObject>,
    pub node_id: u32,
}

impl MockMeshtasticHandler {
    pub fn new(node_id: u32) -> Self {
        Self {
            arxobjects: Vec::new(),
            node_id,
        }
    }
    
    pub fn add_arxobject(&mut self, arxobject: ArxObject) {
        self.arxobjects.push(arxobject);
    }
}

#[async_trait]
impl MeshtasticProtocolHandler for MockMeshtasticHandler {
    async fn handle_packet(&mut self, packet: MeshtasticPacket) -> Result<Option<MeshtasticPacket>, MeshtasticProtocolError> {
        match packet.packet_type {
            MeshtasticPacketType::QueryRequest => {
                let query_str = String::from_utf8(packet.payload)
                    .map_err(|_| MeshtasticProtocolError::InvalidPacket("Invalid UTF-8 in query".to_string()))?;
                
                let query = BuildingQuery::parse(&query_str)?;
                let response = self.process_query(query).await?;
                
                Ok(Some(MeshtasticPacket::new_query_response(
                    self.node_id,
                    packet.source_id,
                    &response,
                    packet.sequence,
                )))
            }
            MeshtasticPacketType::StatusRequest => {
                let status = self.get_status().await?;
                Ok(Some(MeshtasticPacket::new(
                    self.node_id,
                    packet.source_id,
                    MeshtasticPacketType::StatusResponse,
                    packet.sequence,
                    status.into_bytes(),
                )))
            }
            MeshtasticPacketType::ArxObjectBroadcast => {
                if packet.payload.len() == 13 {
                    let mut buf = [0u8; 13];
                    buf.copy_from_slice(&packet.payload[..13]);
                    let arxobject = ArxObject::from_bytes(&buf);
                    self.arxobjects.push(arxobject);
                }
                Ok(None) // No response needed for broadcasts
            }
            _ => Ok(None),
        }
    }
    
    async fn process_query(&mut self, query: BuildingQuery) -> Result<String, MeshtasticProtocolError> {
        let mut results = Vec::new();
        
        match query {
            BuildingQuery::RoomQuery { room } => {
                results.push(format!("Query: room:{}", room));
                results.push(format!("Found {} objects in room {}", 
                    self.arxobjects.len(), room));
            }
            BuildingQuery::TypeQuery { object_type } => {
                let count = self.arxobjects.iter()
                    .filter(|obj| obj.object_type == object_type)
                    .count();
                results.push(format!("Query: type:0x{:02X}", object_type));
                results.push(format!("Found {} objects of type 0x{:02X}", count, object_type));
            }
            BuildingQuery::BuildingQuery { building_id } => {
                let count = self.arxobjects.iter()
                    .filter(|obj| obj.building_id == building_id)
                    .count();
                results.push(format!("Query: building:0x{:04X}", building_id));
                results.push(format!("Found {} objects in building 0x{:04X}", count, building_id));
            }
            BuildingQuery::StatusQuery { status } => {
                results.push(format!("Query: status:{}", status));
                results.push(format!("Found {} objects with status '{}'", 
                    self.arxobjects.len(), status));
            }
            BuildingQuery::ComplexQuery { criteria } => {
                results.push("Complex query:".to_string());
                for (key, value) in criteria {
                    results.push(format!("  {}: {}", key, value));
                }
                results.push(format!("Found {} matching objects", self.arxobjects.len()));
            }
        }
        
        Ok(results.join("\n"))
    }
    
    async fn get_status(&self) -> Result<String, MeshtasticProtocolError> {
        Ok(format!(
            "Node ID: 0x{:04X}\nObjects: {}\nStatus: OK",
            self.node_id, self.arxobjects.len()
        ))
    }
    
    async fn broadcast_arxobject(&mut self, arxobject: &ArxObject) -> Result<(), MeshtasticProtocolError> {
        self.arxobjects.push(*arxobject);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::arxobject::object_types;

    #[test]
    fn test_meshtastic_packet_creation() {
        let packet = MeshtasticPacket::new_query_request(0x0001, 0x0002, "room:127", 1);
        
        assert_eq!(packet.source_id, 0x0001);
        assert_eq!(packet.dest_id, 0x0002);
        assert_eq!(packet.packet_type, MeshtasticPacketType::QueryRequest);
        assert_eq!(packet.sequence, 1);
        assert_eq!(packet.payload, b"room:127");
    }

    #[test]
    fn test_meshtastic_packet_serialization() {
        let packet = MeshtasticPacket::new_query_request(0x0001, 0x0002, "test", 1);
        let bytes = packet.to_bytes();
        let restored = MeshtasticPacket::from_bytes(&bytes).unwrap();
        
        assert_eq!(packet.source_id, restored.source_id);
        assert_eq!(packet.dest_id, restored.dest_id);
        assert_eq!(packet.packet_type, restored.packet_type);
        assert_eq!(packet.sequence, restored.sequence);
        assert_eq!(packet.payload, restored.payload);
    }

    #[test]
    fn test_building_query_parsing() {
        let query = BuildingQuery::parse("room:127").unwrap();
        match query {
            BuildingQuery::RoomQuery { room } => assert_eq!(room, "127"),
            _ => panic!("Wrong query type"),
        }
        
        let query = BuildingQuery::parse("type:outlet").unwrap();
        match query {
            BuildingQuery::TypeQuery { object_type } => assert_eq!(object_type, 0x10),
            _ => panic!("Wrong query type"),
        }
        
        let query = BuildingQuery::parse("building:0x0001").unwrap();
        match query {
            BuildingQuery::BuildingQuery { building_id } => assert_eq!(building_id, 0x0001),
            _ => panic!("Wrong query type"),
        }
    }

    #[tokio::test]
    async fn test_mock_handler() {
        let mut handler = MockMeshtasticHandler::new(0x0001);
        
        // Add some test objects
        let obj1 = ArxObject::new(0x0001, object_types::OUTLET, 1000, 2000, 1500);
        let obj2 = ArxObject::new(0x0001, object_types::LIGHT, 2000, 3000, 2500);
        handler.add_arxobject(obj1);
        handler.add_arxobject(obj2);
        
        // Test query
        let query = BuildingQuery::parse("type:outlet").unwrap();
        let response = handler.process_query(query).await.unwrap();
        assert!(response.contains("Found 1 objects"));
        
        // Test status
        let status = handler.get_status().await.unwrap();
        assert!(status.contains("Node ID: 0x0001"));
        assert!(status.contains("Objects: 2"));
    }
}
