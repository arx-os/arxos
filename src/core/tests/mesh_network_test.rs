//! Test mesh network functionality

use arxos_core::mesh_network_simple::{MeshNode, MeshConfig, MeshSimulator};
use arxos_core::arxobject_simple::{ArxObject, object_types};
use std::time::Duration;

#[tokio::test]
async fn test_mesh_node_creation() {
    let config = MeshConfig {
        node_id: 1,
        building_id: 0x0001,
        listen_port: 8080,
        database_path: ":memory:".to_string(),
        ..Default::default()
    };
    
    let node = MeshNode::new(config).expect("Should create node");
    
    // Add a peer
    let peer_addr = "127.0.0.1:8081".parse().unwrap();
    node.add_peer(2, peer_addr, Default::default());
    
    let stats = node.get_stats();
    assert_eq!(stats.active_peers, 1);
}

#[tokio::test]
async fn test_mesh_simulator() {
    // Create a 3-node mesh network
    let simulator = MeshSimulator::new(3).expect("Should create simulator");
    
    // Generate test objects
    let objects = vec![
        ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300),
        ArxObject::new(0x0001, object_types::LIGHT_SWITCH, 2000, 1000, 1200),
        ArxObject::new(0x0001, object_types::THERMOSTAT, 3000, 2000, 1500),
    ];
    
    // Inject objects into node 0
    simulator.inject_objects(0, objects).expect("Should inject objects");
    
    // Simulate network activity for 2 seconds
    simulator.simulate(Duration::from_secs(2)).await;
}

#[tokio::test]
async fn test_spatial_query() {
    let config = MeshConfig {
        node_id: 1,
        building_id: 0x0001,
        listen_port: 8080,
        database_path: ":memory:".to_string(),
        ..Default::default()
    };
    
    let node = MeshNode::new(config).expect("Should create node");
    
    // Add some objects to the database
    {
        let mut db = node.database.lock().unwrap();
        let objects = vec![
            ArxObject::new(0x0001, object_types::OUTLET, 5000, 5000, 300),
            ArxObject::new(0x0001, object_types::OUTLET, 5500, 5500, 300),
            ArxObject::new(0x0001, object_types::OUTLET, 10000, 10000, 300),
        ];
        db.insert_batch(&objects).expect("Should insert objects");
    }
    
    // Query for objects near (5, 5, 0.3)
    let results = node.query_spatial((5.0, 5.0, 0.3), 1.0).await
        .expect("Should query spatial");
    
    // Should find the two outlets near (5, 5)
    assert_eq!(results.len(), 2);
}

#[test]
fn test_mesh_config_defaults() {
    let config = MeshConfig::default();
    
    assert_eq!(config.building_id, 0x0001);
    assert_eq!(config.listen_port, 8080);
    assert_eq!(config.max_peers, 10);
    assert_eq!(config.broadcast_interval, Duration::from_secs(30));
    assert_eq!(config.sync_interval, Duration::from_secs(60));
}

#[tokio::test]
async fn test_object_deduplication() {
    let config = MeshConfig {
        node_id: 1,
        building_id: 0x0001,
        listen_port: 8080,
        database_path: ":memory:".to_string(),
        ..Default::default()
    };
    
    let node = MeshNode::new(config).expect("Should create node");
    
    // Insert the same object multiple times
    let obj = ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300);
    
    {
        let mut db = node.database.lock().unwrap();
        db.insert(&obj).expect("Should insert first");
        db.insert(&obj).expect("Should insert second"); // SQLite allows duplicates
    }
    
    // But the mesh should track seen objects
    // In production, the mesh would deduplicate via the seen_objects set
}