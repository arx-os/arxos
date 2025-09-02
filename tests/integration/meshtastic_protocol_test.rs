//! Integration tests for Meshtastic Protocol

use arxos_core::meshtastic_protocol::{
    MeshtasticPacket, MeshtasticPacketType, BuildingQuery, MockMeshtasticHandler
};
use arxos_core::arxobject::{ArxObject, object_types};

#[test]
fn test_meshtastic_packet_serialization() {
    let packet = MeshtasticPacket::new_query_request(0x0001, 0x0002, "room:127", 1);
    
    // Serialize to bytes
    let bytes = packet.to_bytes();
    
    // Deserialize back
    let restored = MeshtasticPacket::from_bytes(&bytes).unwrap();
    
    assert_eq!(packet.source_id, restored.source_id);
    assert_eq!(packet.dest_id, restored.dest_id);
    assert_eq!(packet.packet_type, restored.packet_type);
    assert_eq!(packet.sequence, restored.sequence);
    assert_eq!(packet.payload, restored.payload);
}

#[test]
fn test_building_query_parsing() {
    // Test room query
    let query = BuildingQuery::parse("room:127").unwrap();
    match query {
        BuildingQuery::RoomQuery { room } => assert_eq!(room, "127"),
        _ => panic!("Wrong query type"),
    }
    
    // Test type query
    let query = BuildingQuery::parse("type:outlet").unwrap();
    match query {
        BuildingQuery::TypeQuery { object_type } => assert_eq!(object_type, 0x10),
        _ => panic!("Wrong query type"),
    }
    
    // Test building query
    let query = BuildingQuery::parse("building:0x0001").unwrap();
    match query {
        BuildingQuery::BuildingQuery { building_id } => assert_eq!(building_id, 0x0001),
        _ => panic!("Wrong query type"),
    }
    
    // Test status query
    let query = BuildingQuery::parse("status:faulty").unwrap();
    match query {
        BuildingQuery::StatusQuery { status } => assert_eq!(status, "faulty"),
        _ => panic!("Wrong query type"),
    }
}

#[tokio::test]
async fn test_meshtastic_handler() {
    let mut handler = MockMeshtasticHandler::new(0x0001);
    
    // Add some test objects
    let obj1 = ArxObject::new(0x0001, object_types::OUTLET, 1000, 2000, 1500);
    let obj2 = ArxObject::new(0x0001, object_types::LIGHT, 2000, 3000, 2500);
    let obj3 = ArxObject::new(0x0002, object_types::OUTLET, 3000, 4000, 3500);
    
    handler.add_arxobject(obj1);
    handler.add_arxobject(obj2);
    handler.add_arxobject(obj3);
    
    // Test type query
    let query = BuildingQuery::parse("type:outlet").unwrap();
    let response = handler.process_query(query).await.unwrap();
    assert!(response.contains("Found 2 objects"));
    
    // Test building query
    let query = BuildingQuery::parse("building:0x0001").unwrap();
    let response = handler.process_query(query).await.unwrap();
    assert!(response.contains("Found 2 objects"));
    
    // Test status
    let status = handler.get_status().await.unwrap();
    assert!(status.contains("Node ID: 0x0001"));
    assert!(status.contains("Objects: 3"));
}

#[tokio::test]
async fn test_meshtastic_packet_handling() {
    let mut handler = MockMeshtasticHandler::new(0x0001);
    
    // Test query request packet
    let query_packet = MeshtasticPacket::new_query_request(0x0002, 0x0001, "type:light", 1);
    let response = handler.handle_packet(query_packet).await.unwrap();
    
    assert!(response.is_some());
    let response_packet = response.unwrap();
    assert_eq!(response_packet.packet_type, MeshtasticPacketType::QueryResponse);
    assert_eq!(response_packet.source_id, 0x0001);
    assert_eq!(response_packet.dest_id, 0x0002);
    
    // Test status request packet
    let status_packet = MeshtasticPacket::new(
        0x0002, 0x0001, MeshtasticPacketType::StatusRequest, 2, vec![]
    );
    let response = handler.handle_packet(status_packet).await.unwrap();
    
    assert!(response.is_some());
    let response_packet = response.unwrap();
    assert_eq!(response_packet.packet_type, MeshtasticPacketType::StatusResponse);
}

#[test]
fn test_arxobject_broadcast_packet() {
    let arxobject = ArxObject::new(0x0001, object_types::SENSOR, 1000, 2000, 1500);
    let packet = MeshtasticPacket::new_arxobject_broadcast(0x0001, 0xFFFF, &arxobject, 1);
    
    assert_eq!(packet.packet_type, MeshtasticPacketType::ArxObjectBroadcast);
    assert_eq!(packet.source_id, 0x0001);
    assert_eq!(packet.dest_id, 0xFFFF); // Broadcast
    assert_eq!(packet.payload.len(), 13); // ArxObject size
    
    // Verify payload is the ArxObject bytes
    let restored_object = ArxObject::from_bytes(&packet.payload[..13].try_into().unwrap());
    assert_eq!(arxobject.id, restored_object.id);
    assert_eq!(arxobject.object_type, restored_object.object_type);
}

#[test]
fn test_packet_type_enum() {
    // Test all packet types
    assert_eq!(MeshtasticPacketType::QueryRequest as u8, 0x10);
    assert_eq!(MeshtasticPacketType::QueryResponse as u8, 0x11);
    assert_eq!(MeshtasticPacketType::ArxObjectBroadcast as u8, 0x12);
    assert_eq!(MeshtasticPacketType::StatusRequest as u8, 0x13);
    assert_eq!(MeshtasticPacketType::StatusResponse as u8, 0x14);
    assert_eq!(MeshtasticPacketType::Heartbeat as u8, 0x15);
    
    // Test conversion from u8
    assert_eq!(MeshtasticPacketType::try_from(0x10).unwrap(), MeshtasticPacketType::QueryRequest);
    assert_eq!(MeshtasticPacketType::try_from(0x11).unwrap(), MeshtasticPacketType::QueryResponse);
    assert_eq!(MeshtasticPacketType::try_from(0x12).unwrap(), MeshtasticPacketType::ArxObjectBroadcast);
    assert_eq!(MeshtasticPacketType::try_from(0x13).unwrap(), MeshtasticPacketType::StatusRequest);
    assert_eq!(MeshtasticPacketType::try_from(0x14).unwrap(), MeshtasticPacketType::StatusResponse);
    assert_eq!(MeshtasticPacketType::try_from(0x15).unwrap(), MeshtasticPacketType::Heartbeat);
    
    // Test invalid packet type
    assert!(MeshtasticPacketType::try_from(0x99).is_err());
}
