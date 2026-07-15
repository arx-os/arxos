//! Integration tests for local caching tier metrics and Discovery HUD managers.

#[cfg(feature = "web")]
mod web_tests {
    use arxos::core::{Anchor, Position, MapRef, RelativePose, PoseType};
    use arxos::core::domain::ArxAddress;
    use arxos::core::spatial::Point3D;
    use arxos::web::cache::{WarmCache, BinaryAssetCache, SyncQueue};
    use arxos::web::cache::warm::BuildingSyncEnvelope;
    use arxos::web::cache::warming::PredictiveWarming;
    use arxos::web::discovery::{DiscoveryManager, HudOverlay, HudTask, TaskResolver, LocationContext};

    #[test]
    fn test_warm_cache_metrics_and_eviction() {
        let mut warm_cache = WarmCache::new();
        assert_eq!(warm_cache.hits, 0);
        assert_eq!(warm_cache.misses, 0);

        let addr = ArxAddress::from_path("/building/hq/floor-1").unwrap();
        
        // Miss check
        assert!(warm_cache.get_subtree(&addr).is_none());
        assert_eq!(warm_cache.misses, 1);

        // Populate and Hit check
        let envelope = BuildingSyncEnvelope {
            base_address: addr.clone(),
            anchors: vec![],
            payload: "Room geometry envelope".to_string(),
            fetched_at_timestamp: 1000,
        };
        warm_cache.insert_subtree(envelope);

        assert!(warm_cache.get_subtree(&addr).is_some());
        assert_eq!(warm_cache.hits, 1);
    }

    #[test]
    fn test_binary_asset_cache_retries_and_latency() {
        let mut binary_cache = BinaryAssetCache::new();
        assert_eq!(binary_cache.hits, 0);
        assert_eq!(binary_cache.misses, 0);

        let map_ref = MapRef::Ipfs {
            cid: "bafybeic7n6x4h5z2g".to_string(),
        };

        // Hydrating assets for the first time should cause a miss, run retries, and measure latency
        let data = binary_cache.load_asset(&map_ref).unwrap();
        assert!(data.len() > 0);
        assert_eq!(binary_cache.misses, 1);
        assert_eq!(binary_cache.hits, 0);
        assert!(binary_cache.last_latency_ms >= 0);

        // Next fetch is a hit
        let hit_data = binary_cache.load_asset(&map_ref).unwrap();
        assert_eq!(hit_data, data);
        assert_eq!(binary_cache.hits, 1);
    }

    #[test]
    fn test_discovery_radius_filtering_and_provisional_status() {
        let mut warm_cache = WarmCache::new();
        let mut manager = DiscoveryManager::new();
        let warmer = PredictiveWarming;

        let floor_addr = ArxAddress::from_path("/building/hq/floor-1").unwrap();
        let anchor1 = Anchor::new(
            "ahu-01".to_string(),
            Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() },
            0.9,
        );
        let anchor2 = Anchor::new(
            "ahu-02".to_string(),
            Position { x: 25.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() },
            0.85,
        );

        let envelope = BuildingSyncEnvelope {
            base_address: floor_addr.clone(),
            anchors: vec![anchor1, anchor2],
            payload: "floor scan payload".to_string(),
            fetched_at_timestamp: 1000,
        };
        warm_cache.insert_subtree(envelope);

        // Position worker at origin (0.0, 0.0, 0.0)
        let location = LocationContext {
            current_address: floor_addr,
            coordinates: Point3D::new(0.0, 0.0, 0.0),
            confidence: 1.0,
        };
        manager.update_position(location, &mut warm_cache, &warmer);

        // With default radius 10.0, only anchor1 and the pre-warmed lobby anchor are visible (distance < 10m)
        let visible = manager.get_visible_anchors(&warm_cache);
        assert_eq!(visible.len(), 2);
        assert!(visible.iter().any(|a| a.name == "ahu-01"));
        assert!(visible.iter().any(|a| a.name == "ahu-lobby-recalibrated"));

        // Verify provisional status detection (starts with /building)
        assert!(manager.is_provisional());
    }

    #[test]
    fn test_hud_compilation_and_task_resolver() {
        let mut sync_queue = SyncQueue::new();

        // 1. Create a low-saturation anchor (<0.8 saturation) and a dangling RelativePose target
        let mut anchor = Anchor::new(
            "ahu-01".to_string(),
            Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() },
            0.5,
        ); // low confidence
        let broken_pose = RelativePose {
            target_id: "dangling".to_string(),
            pose_type: PoseType::AnchorToAnchor,
            x: 1.0, y: 0.0, z: 0.0,
            roll: 0.0, pitch: 0.0, yaw: 0.0,
        };
        anchor.relative_poses.push(broken_pose);

        let tasks = HudOverlay::compile_tasks(&[anchor.clone()]);
        assert_eq!(tasks.len(), 2); // 1 LowSaturation, 1 DanglingPose task

        let mut has_low_sat = false;
        let mut has_dangling = false;
        for task in tasks {
            match task {
                HudTask::LowSaturation(s) => {
                    assert_eq!(s.anchor.name, "ahu-01");
                    assert_eq!(s.bounty_multiplier, 1.50);
                    has_low_sat = true;
                }
                HudTask::DanglingPose(d) => {
                    assert_eq!(d.source_id, anchor.id);
                    assert_eq!(d.bounty_multiplier, 1.10);
                    has_dangling = true;
                }
            }
        }
        assert!(has_low_sat);
        assert!(has_dangling);

        // 2. Resolve the low-saturation task
        TaskResolver::recalibrate_anchor(
            "ahu-01",
            Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() },
            0.95,
            &mut sync_queue,
        );
        assert_eq!(sync_queue.queue.len(), 1);
    }

    #[test]
    fn test_ar_overlay_label_projection() {
        use arxos::web::overlay::label::LabelProjector;

        let worker_pos = Position {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "local".to_string(),
        };

        // Anchor is directly in front of the worker (X positive)
        let anchor = Anchor::new(
            "Panel-A1".to_string(),
            Position { x: 3.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() },
            0.9,
        );

        // Worker heading is 0.0 degrees (pointing directly along X positive)
        let labels = LabelProjector::project_labels(&[anchor], &worker_pos, 0.0, None);
        assert_eq!(labels.len(), 1);
        
        let label = &labels[0];
        assert_eq!(label.title, "Panel-A1");
        assert!((label.x_percent - 50.0).abs() < 1e-5); // Centered horizontally (50%)
        assert_eq!(label.distance_m, 3.0);
    }
}
