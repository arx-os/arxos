//! Protocol Translator
//!
//! Translates between ArxOS and Meshtastic protocols

use anyhow::Result;
use log::debug;
use prost::Message;

use arxos_core::ArxObject;

/// Protocol translator between ArxOS and Meshtastic
pub struct ProtocolTranslator {
    // Add any state needed for protocol translation
}

impl ProtocolTranslator {
    /// Create new protocol translator
    pub fn new() -> Self {
        Self {}
    }

    /// Encode ArxObject to Meshtastic message format
    pub fn encode_arxobject(&self, arxobject: ArxObject) -> Result<Vec<u8>> {
        debug!("Encoding ArxObject to Meshtastic format");

        // Convert ArxObject to bytes
        let arxobject_bytes = arxobject.to_bytes();

        // Create Meshtastic message wrapper
        let meshtastic_message = MeshtasticMessage {
            id: 0, // Will be set by Meshtastic
            payload: arxobject_bytes,
            from: 0, // Will be set by Meshtastic
            to: 0,   // Broadcast
            channel: "arxos".to_string(),
            want_ack: false,
            hop_limit: 3,
            want_response: false,
        };

        // Encode as protobuf
        let mut buf = Vec::new();
        meshtastic_message.encode(&mut buf)?;

        debug!("Encoded {} bytes for Meshtastic", buf.len());
        Ok(buf)
    }

    /// Decode Meshtastic message to ArxObject
    pub fn decode_arxobject(&self, data: &[u8]) -> Result<ArxObject> {
        debug!("Decoding Meshtastic message to ArxObject");

        // Decode Meshtastic message
        let meshtastic_message = MeshtasticMessage::decode(data)?;

        // Extract ArxObject bytes
        let arxobject_bytes = meshtastic_message.payload;

        // Convert bytes to ArxObject
        let arxobject = ArxObject::from_bytes(&arxobject_bytes)?;

        debug!("Decoded ArxObject: {:?}", arxobject);
        Ok(arxobject)
    }

    /// Validate Meshtastic message
    pub fn validate_message(&self, data: &[u8]) -> bool {
        // Basic validation - check if it's a valid protobuf message
        MeshtasticMessage::decode(data).is_ok()
    }

    /// Get message type from Meshtastic data
    pub fn get_message_type(&self, data: &[u8]) -> Result<MessageType> {
        let message = MeshtasticMessage::decode(data)?;
        
        // Check if this is an ArxOS message
        if message.channel == "arxos" {
            Ok(MessageType::ArxOS)
        } else {
            Ok(MessageType::Standard)
        }
    }
}

/// Meshtastic message structure
#[derive(Clone, PartialEq, Message)]
pub struct MeshtasticMessage {
    #[prost(uint32, tag = "1")]
    pub id: u32,
    #[prost(bytes, tag = "2")]
    pub payload: Vec<u8>,
    #[prost(fixed32, tag = "3")]
    pub from: u32,
    #[prost(fixed32, tag = "4")]
    pub to: u32,
    #[prost(string, tag = "5")]
    pub channel: String,
    #[prost(bool, tag = "6")]
    pub want_ack: bool,
    #[prost(uint32, tag = "7")]
    pub hop_limit: u32,
    #[prost(bool, tag = "8")]
    pub want_response: bool,
}

/// Message type enumeration
#[derive(Debug, Clone, PartialEq)]
pub enum MessageType {
    ArxOS,
    Standard,
}

impl Default for ProtocolTranslator {
    fn default() -> Self {
        Self::new()
    }
}
