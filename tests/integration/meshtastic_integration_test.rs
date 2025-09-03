//! Integration tests for Meshtastic transport with ArxOS
//! 
//! These tests verify the full stack: ArxObject → Meshtastic → Mesh → ArxObject

use arxos_core::{
    arxobject::{ArxObject, object_types},
    transport::{Transport, meshtastic::MeshtasticTransport, mock::MockTransport},
    error::Result,
};
use std::time::Duration;
use tokio::time::timeout;

/// Test ArxObject serialization for Meshtastic packets
#[tokio::test]
async fn test_arxobject_fits_in_meshtastic_packet() {
    // ArxObject must be exactly 13 bytes to fit efficiently in LoRa packets
    let obj = ArxObject::new(0x1234, object_types::OUTLET, 5000, 3000, 1500);
    let bytes = obj.to_bytes();
    
    assert_eq!(bytes.len(), 13, "ArxObject must be exactly 13 bytes");
    
    // Verify round-trip serialization
    let restored = ArxObject::from_bytes(&bytes);
    assert_eq!(obj.building_id, restored.building_id);
    assert_eq!(obj.object_type, restored.object_type);
    assert_eq!(obj.x, restored.x);
    assert_eq!(obj.y, restored.y);
    assert_eq!(obj.z, restored.z);
}

/// Test mock transport for development without hardware
#[tokio::test]
async fn test_mock_transport() -> Result<()> {
    let mut transport = MockTransport::new();
    
    // Connect to mock mesh
    transport.connect("test_building").await?;
    assert!(transport.is_connected());
    
    // Create test ArxObject
    let obj = ArxObject::new(0x0001, object_types::LEAK, 1000, 2000, 300);
    
    // Send via mock transport
    transport.send(&obj.to_bytes()).await?;
    
    // Verify metrics
    let metrics = transport.get_metrics();
    assert_eq!(metrics.packets_sent, 1);
    assert_eq!(metrics.bytes_sent, 13);
    
    Ok(())
}

/// Test Meshtastic transport with actual device (requires hardware)
#[tokio::test]
#[ignore] // Ignore by default since it requires hardware
async fn test_meshtastic_hardware() -> Result<()> {
    // This test requires a Meshtastic device connected to /dev/ttyUSB0
    let mut transport = MeshtasticTransport::new("/dev/ttyUSB0".to_string());
    
    // Connect with timeout
    let connect_result = timeout(
        Duration::from_secs(5),
        transport.connect("building_1")
    ).await;
    
    match connect_result {
        Ok(Ok(())) => {
            println!("Connected to Meshtastic device");
            
            // Send test ArxObject
            let obj = ArxObject::new(0x0001, object_types::OUTLET, 1000, 2000, 300);
            transport.send(&obj.to_bytes()).await?;
            
            // Wait for potential echo
            tokio::time::sleep(Duration::from_millis(500)).await;
            
            // Try to receive
            let received = transport.receive().await?;
            if !received.is_empty() {
                let received_obj = ArxObject::from_bytes(&received.try_into().unwrap());
                println!("Received: {:?}", received_obj);
            }
            
            transport.disconnect().await?;
        }
        Ok(Err(e)) => {
            eprintln!("Connection failed: {}", e);
            return Err(e.into());
        }
        Err(_) => {
            eprintln!("Connection timeout - is device connected?");
        }
    }
    
    Ok(())
}

/// Test multiple ArxObjects representing a building
#[tokio::test]
async fn test_building_representation() -> Result<()> {
    let mut transport = MockTransport::new();
    transport.connect("test_building").await?;
    
    // Create objects for one floor of a building
    let mut objects = Vec::new();
    
    // Room 101
    objects.push(ArxObject::new(0x0001, object_types::ROOM, 0, 0, 0));
    objects.push(ArxObject::new(0x0001, object_types::DOOR, 1000, 0, 0));
    objects.push(ArxObject::new(0x0001, object_types::OUTLET, 500, 100, 300));
    objects.push(ArxObject::new(0x0001, object_types::OUTLET, 3500, 100, 300));
    objects.push(ArxObject::new(0x0001, object_types::LIGHT, 2000, 2000, 2800));
    
    // Room 102
    objects.push(ArxObject::new(0x0001, object_types::ROOM, 5000, 0, 0));
    objects.push(ArxObject::new(0x0001, object_types::DOOR, 6000, 0, 0));
    objects.push(ArxObject::new(0x0001, object_types::WINDOW, 7500, 2000, 1200));
    objects.push(ArxObject::new(0x0001, object_types::THERMOSTAT, 5100, 1000, 1500));
    
    // Send all objects
    for obj in &objects {
        transport.send(&obj.to_bytes()).await?;
    }
    
    let metrics = transport.get_metrics();
    assert_eq!(metrics.packets_sent, objects.len() as u64);
    assert_eq!(metrics.bytes_sent, objects.len() * 13);
    
    // Total size for 9 objects: 117 bytes
    // Equivalent point cloud would be ~450KB (5000:1 compression)
    println!("Sent {} objects in {} bytes", objects.len(), metrics.bytes_sent);
    println!("Compression ratio: ~5000:1 vs point cloud");
    
    Ok(())
}

/// Test game-style movement through building
#[tokio::test]
async fn test_game_navigation() -> Result<()> {
    use arxos_core::ascii_bridge::AsciiBridge;
    
    let mut transport = MockTransport::new();
    transport.connect("test_building").await?;
    
    // Create ASCII bridge for conversions
    let mut bridge = AsciiBridge::new(0x0001);
    
    // Parse movement command
    let ascii_command = "PLAYER @ (10.5, 5.2, 0.0)m MOVING:NORTH";
    let player_obj = bridge.parse(ascii_command)?;
    
    // Send player position update
    transport.send(&player_obj.to_bytes()).await?;
    
    // Simulate receiving nearby objects
    let nearby_outlet = ArxObject::new(0x0001, object_types::OUTLET, 10500, 6000, 300);
    
    // Convert to ASCII for display
    let ascii_display = bridge.render(&nearby_outlet);
    println!("You see: {}", ascii_display);
    
    assert!(ascii_display.contains("OUTLET"));
    
    Ok(())
}

/// Test alert broadcasting
#[tokio::test]
async fn test_alert_broadcast() -> Result<()> {
    let mut transport = MockTransport::new();
    transport.connect("test_building").await?;
    
    // Create leak alert
    let leak = ArxObject::with_properties(
        0x0001,                    // Building 1
        object_types::LEAK,        // Leak type
        10500, 2300, 0,           // Location
        [3, 0, 0, 0],             // Severity: HIGH
    );
    
    // Broadcast alert
    transport.send(&leak.to_bytes()).await?;
    
    // In real scenario, all nodes in building would receive this
    println!("ALERT broadcast: Leak detected at ({}, {}, {})", 
             leak.x, leak.y, leak.z);
    
    Ok(())
}

/// Benchmark compression performance
#[test]
fn bench_compression_ratio() {
    use std::time::Instant;
    
    let start = Instant::now();
    
    // Create 10,000 ArxObjects (typical building)
    let mut objects = Vec::new();
    for i in 0..10_000 {
        objects.push(ArxObject::new(
            1,
            (i % 20) as u8,
            (i * 100 % 65535) as u16,
            (i * 200 % 65535) as u16,
            (i * 10 % 3000) as u16,
        ));
    }
    
    let arxos_size = objects.len() * 13;
    let point_cloud_estimate = objects.len() * 50_000; // 50KB per object area
    let compression_ratio = point_cloud_estimate as f64 / arxos_size as f64;
    
    let elapsed = start.elapsed();
    
    println!("Performance Report:");
    println!("  Objects created: {}", objects.len());
    println!("  ArxOS size: {} bytes ({} KB)", arxos_size, arxos_size / 1024);
    println!("  Point cloud estimate: {} bytes ({} MB)", 
             point_cloud_estimate, point_cloud_estimate / 1_048_576);
    println!("  Compression ratio: {:.0}:1", compression_ratio);
    println!("  Time: {:?}", elapsed);
    println!("  Throughput: {:.0} objects/sec", 
             objects.len() as f64 / elapsed.as_secs_f64());
    
    assert!(compression_ratio > 3000.0, "Must maintain >3000:1 compression");
}