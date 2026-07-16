//! Integration tests for ownership claim verification, live splits, and owner staging reviews.

#[cfg(feature = "agent")]
mod agent_tests {
    use serial_test::serial;
    use arxos::agent::claim::{
        ClaimListener, ClaimEvent, GitReconstructor, GraceWindowManager,
        RewardReleaser, ClaimState
    };
    use tempfile::tempdir;

    #[test]
    fn test_claim_listener_and_rewards_simulation() {
        let mut listener = ClaimListener::new();
        let event = ClaimEvent {
            building_uuid: "building-123".to_string(),
            owner_address: "0x1234567890abcdef".to_string(),
            merkle_root: [0u8; 32],
            git_repo_url: "https://github.com/arx-os/arxos-test.git".to_string(),
        };

        listener.inject_simulated_event(event);
        let events = listener.poll_events();
        assert_eq!(events.len(), 1);
        assert_eq!(events[0].building_uuid, "building-123");

        // Reward split validation in dry-run mode
        let releaser = RewardReleaser::new(false);
        let receipt = releaser.release_escrowed_axd("building-123", "0x1234567890abcdef", 1000.0).unwrap();
        assert!(receipt.contains("[DRY-RUN]"));
        assert!(receipt.contains("Workers: 700.00"));
        assert!(receipt.contains("Owner (0x1234567890abcdef): 100.00"));
        assert!(receipt.contains("Maintainers: 200.00"));
    }

    #[test]
    #[serial]
    fn test_claim_listener_and_rewards_live() {
        // Safe check without private keys env
        let releaser = RewardReleaser::new(true);
        let err = releaser.release_escrowed_axd("building-123", "0x1234567890abcdef", 1000.0).unwrap_err();
        assert!(err.contains("On-chain signing failed"));

        // Set simulated mock keys env
        std::env::set_var("PHASE_RPC_URL", "https://mock.phase.network");
        std::env::set_var("PHASE_PRIVATE_KEY", "MOCK_SECRET_KEY");

        let releaser_live = RewardReleaser::new(true);
        let receipt = releaser_live.release_escrowed_axd("building-123", "0x1234567890abcdef", 1000.0).unwrap();
        assert!(receipt.contains("On-chain transfer SUCCESS"));
        assert!(receipt.contains("Tx Hash:"));
        assert!(receipt.contains("Owner (0x1234567890abcdef): 100.00"));

        std::env::remove_var("PHASE_RPC_URL");
        std::env::remove_var("PHASE_PRIVATE_KEY");
    }

    #[test]
    fn test_git_reconstructor_promotion() {
        let reconstructor = GitReconstructor::new();
        let temp_dir = tempdir().unwrap();
        let repo_path = temp_dir.path().to_str().unwrap();

        let root = [0u8; 32];
        let payload = reconstructor.fetch_and_verify_payload("building-123", &root).unwrap();
        
        reconstructor.reconstruct_history(repo_path, &payload).unwrap();

        let yaml_content = std::fs::read_to_string(temp_dir.path().join("building.yaml")).unwrap();
        assert!(yaml_content.contains("address: /main/hq"));
    }

    #[test]
    fn test_owner_staging_review_queue() {
        let grace_manager = GraceWindowManager::new();
        let temp_dir = tempdir().unwrap();
        let repo_path = temp_dir.path().to_str().unwrap();
        let building_id = "building-123";

        let mock_provisional_contrib = r#"
building:
  id: "test-building-id"
  name: "Claimed HQ"
  path: "/building/hq"
  address: "/building/hq"
  created_at: 2026-01-01T00:00:00Z
  updated_at: 2026-01-01T00:00:00Z
  floors: []
  coordinate_systems: []
equipment: []
"#;

        // 1. Write mock building.yaml to start with
        std::fs::write(temp_dir.path().join("building.yaml"), mock_provisional_contrib).unwrap();

        // 2. Queue a pending contribution
        let idx = grace_manager.add_pending_contribution(repo_path, mock_provisional_contrib).unwrap();
        assert_eq!(idx, 0);

        let list = grace_manager.list_pending_contributions(repo_path).unwrap();
        assert_eq!(list.len(), 1);
        assert_eq!(list[0].0, 0);

        // 3. Register active grace window claim
        let mut gm = grace_manager;
        gm.register_active_claim(building_id.to_string(), 14);

        // 4. Approve and assert on-chain splits
        let (state, receipt) = gm.review_pending_contribution(
            repo_path,
            building_id,
            0,
            true, // Approve
            "0x1234567890abcdef",
            false, // Simulation mode
        ).unwrap();

        assert_eq!(state, ClaimState::RewardsReleased);
        assert!(receipt.contains("Workers: 350.00")); // 70% of 500.0 Completeness Bounty

        // Confirm building.yaml has been promoted
        let promoted_yaml = std::fs::read_to_string(temp_dir.path().join("building.yaml")).unwrap();
        assert!(promoted_yaml.contains("address: /main/hq"));
    }

    #[test]
    #[serial]
    fn test_private_key_loader_and_hardening() {
        use arxos::agent::claim::rewards::{
            PrivateKeyLoader, EnvironmentKeyLoader, FileKeyLoader, HybridKeyLoader,
            DistributorConfig
        };
        use tempfile::tempdir;
        use std::fs;

        // 1. Test EnvironmentKeyLoader
        std::env::set_var("PHASE_PRIVATE_KEY", "ENV_SECRET");
        std::env::set_var("PHASE_RPC_URL", "https://env.rpc");
        let env_loader = EnvironmentKeyLoader;
        assert_eq!(env_loader.load_private_key().unwrap(), "ENV_SECRET");
        assert_eq!(env_loader.load_rpc_url().unwrap(), "https://env.rpc");

        // 2. Test FileKeyLoader
        let temp_dir = tempdir().unwrap();
        let config_path = temp_dir.path().join("payout.json");
        let config_content = r#"{
            "private_key": "FILE_SECRET",
            "rpc_url": "https://file.rpc"
        }"#;
        fs::write(&config_path, config_content).unwrap();

        let file_loader = FileKeyLoader {
            filepath: config_path.to_str().unwrap().to_string(),
        };
        assert_eq!(file_loader.load_private_key().unwrap(), "FILE_SECRET");
        assert_eq!(file_loader.load_rpc_url().unwrap(), "https://file.rpc");

        // Clean env variables
        std::env::remove_var("PHASE_PRIVATE_KEY");
        std::env::remove_var("PHASE_RPC_URL");

        // 3. Test HybridKeyLoader prioritizes env over file
        let hybrid_loader = HybridKeyLoader {
            env_loader: EnvironmentKeyLoader,
            file_loader: FileKeyLoader {
                filepath: config_path.to_str().unwrap().to_string(),
            },
        };

        // File only (env is unset)
        assert_eq!(hybrid_loader.load_private_key().unwrap(), "FILE_SECRET");
        assert_eq!(hybrid_loader.load_rpc_url().unwrap(), "https://file.rpc");

        // Env set
        std::env::set_var("PHASE_PRIVATE_KEY", "ENV_PRIORITY");
        std::env::set_var("PHASE_RPC_URL", "https://env.priority");
        assert_eq!(hybrid_loader.load_private_key().unwrap(), "ENV_PRIORITY");
        assert_eq!(hybrid_loader.load_rpc_url().unwrap(), "https://env.priority");

        std::env::remove_var("PHASE_PRIVATE_KEY");
        std::env::remove_var("PHASE_RPC_URL");
    }

    #[test]
    fn test_agent_http_endpoints() {
        use axum::{
            http::StatusCode,
            response::IntoResponse,
        };
        use tempfile::tempdir;
        use std::fs;
        use std::sync::{Arc, Mutex};
        use arxos::agent::{
            auth::TokenState,
            dispatcher::AgentState,
        };

        let temp_dir = tempdir().unwrap();
        let repo_path = temp_dir.path().to_str().unwrap();

        // Write a mock building.yaml
        let mock_yaml = r#"
building:
  id: "building-123"
  name: "Mock Twin"
  path: "/building/hq"
  address: "/building/hq"
  created_at: 2026-01-01T00:00:00Z
  updated_at: 2026-01-01T00:00:00Z
  floors: []
  coordinate_systems: []
equipment: []
"#;
        fs::write(temp_dir.path().join("building.yaml"), mock_yaml).unwrap();

        // Queue a pending contribution
        let grace_manager = GraceWindowManager::new();
        let idx = grace_manager.add_pending_contribution(repo_path, mock_yaml).unwrap();
        assert_eq!(idx, 0);

        // Setup AgentState
        let token_state = TokenState::new("secret-token".to_string(), vec![]);
        let agent_state = Arc::new(AgentState {
            repo_root: temp_dir.path().to_path_buf(),
            token: Arc::new(Mutex::new(token_state)),
            metrics: Arc::new(arxos::agent::observability::AgentMetrics::new()),
            reload_handle: None,
        });

        tokio::runtime::Runtime::new().unwrap().block_on(async {
            // 1. Test UNAUTHORIZED staging request
            let headers = axum::http::HeaderMap::new();
            let query = axum::extract::Query(arxos::agent::server::AuthParams { token: None });
            let state = axum::extract::State(agent_state.clone());
            let res = arxos::agent::server::http_claims_staging(headers, query, state).await;
            let response = res.into_response();
            assert_eq!(response.status(), StatusCode::UNAUTHORIZED);

            // 2. Test AUTHORIZED staging request
            let headers = axum::http::HeaderMap::new();
            let query = axum::extract::Query(arxos::agent::server::AuthParams { token: Some("secret-token".to_string()) });
            let state = axum::extract::State(agent_state.clone());
            let res = arxos::agent::server::http_claims_staging(headers, query, state).await;
            let response = res.into_response();
            assert_eq!(response.status(), StatusCode::OK);

            // 3. Test AUTHORIZED approve request
            let headers = axum::http::HeaderMap::new();
            let query = axum::extract::Query(arxos::agent::server::AuthParams { token: Some("secret-token".to_string()) });
            let path = axum::extract::Path(0usize);
            let state = axum::extract::State(agent_state.clone());
            let body = axum::Json(arxos::agent::server::HttpClaimReviewRequest {
                owner_address: "0x1234567890abcdef".to_string(),
                live: Some(false),
            });
            let res = arxos::agent::server::http_claim_approve(headers, query, path, state, body).await;
            let response = res.into_response();
            assert_eq!(response.status(), StatusCode::OK);
        });
    }

    #[test]
    fn test_agent_observability_endpoints() {
        use axum::{
            http::StatusCode,
            response::IntoResponse,
        };
        use tempfile::tempdir;
        use std::sync::{Arc, Mutex};
        use arxos::agent::{
            auth::TokenState,
            dispatcher::AgentState,
        };

        let temp_dir = tempdir().unwrap();

        // Setup AgentState with metrics
        let token_state = TokenState::new("secret-token".to_string(), vec![]);
        let metrics = Arc::new(arxos::agent::observability::AgentMetrics::new());
        
        // Record some mock metrics
        metrics.record_claim_processed(true, 500.0); // 1 approved with 500 AXD
        metrics.record_claim_processed(false, 0.0); // 1 rejected
        metrics.record_error();

        let agent_state = Arc::new(AgentState {
            repo_root: temp_dir.path().to_path_buf(),
            token: Arc::new(Mutex::new(token_state)),
            metrics: metrics.clone(),
            reload_handle: None,
        });

        tokio::runtime::Runtime::new().unwrap().block_on(async {
            // 1. Test status endpoint unauthorized
            let headers = axum::http::HeaderMap::new();
            let query = axum::extract::Query(arxos::agent::server::AuthParams { token: None });
            let state = axum::extract::State(agent_state.clone());
            let res = arxos::agent::server::http_agent_status(headers, query, state).await;
            assert_eq!(res.into_response().status(), StatusCode::UNAUTHORIZED);

            // 2. Test status endpoint authorized
            let headers = axum::http::HeaderMap::new();
            let query = axum::extract::Query(arxos::agent::server::AuthParams { token: Some("secret-token".to_string()) });
            let state = axum::extract::State(agent_state.clone());
            let res = arxos::agent::server::http_agent_status(headers, query, state).await;
            let response = res.into_response();
            assert_eq!(response.status(), StatusCode::OK);

            // 3. Test claims status endpoint
            let headers = axum::http::HeaderMap::new();
            let query = axum::extract::Query(arxos::agent::server::AuthParams { token: Some("secret-token".to_string()) });
            let state = axum::extract::State(agent_state.clone());
            let res = arxos::agent::server::http_claims_status(headers, query, state).await;
            let response = res.into_response();
            assert_eq!(response.status(), StatusCode::OK);

            let body_bytes = axum::body::to_bytes(response.into_body(), 10000).await.unwrap();
            let val: serde_json::Value = serde_json::from_slice(&body_bytes).unwrap();
            assert_eq!(val.get("claims_processed").unwrap().as_u64().unwrap(), 2);
            assert_eq!(val.get("claims_approved").unwrap().as_u64().unwrap(), 1);
            assert_eq!(val.get("claims_rejected").unwrap().as_u64().unwrap(), 1);
            assert_eq!(val.get("rewards_distributed_axd").unwrap().as_f64().unwrap(), 500.0);

            // 4. Test metrics endpoint
            let headers = axum::http::HeaderMap::new();
            let query = axum::extract::Query(arxos::agent::server::AuthParams { token: Some("secret-token".to_string()) });
            let state = axum::extract::State(agent_state.clone());
            let res = arxos::agent::server::http_prometheus_metrics(headers, query, state).await;
            let response = res.into_response();
            assert_eq!(response.status(), StatusCode::OK);

            let body_bytes = axum::body::to_bytes(response.into_body(), 10000).await.unwrap();
            let metrics_text = String::from_utf8(body_bytes.to_vec()).unwrap();
            assert!(metrics_text.contains("arx_agent_claims_processed_total 2"));
            assert!(metrics_text.contains("arx_agent_claims_approved_total 1"));
            assert!(metrics_text.contains("arx_agent_claims_rejected_total 1"));
            assert!(metrics_text.contains("arx_agent_rewards_distributed_axd_total 500.00"));
            assert!(metrics_text.contains("arx_agent_errors_total 2"));
        });
    }

    #[test]
    fn test_log_redactor_and_sensitive() {
        use arxos::agent::observability::{redact_secrets, Sensitive};

        // Redactor
        let raw = "Some error with private key MOCK_SECRET_KEY and secret key 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
        let redacted = redact_secrets(raw);
        assert!(!redacted.contains("MOCK_SECRET_KEY"));
        assert!(!redacted.contains("0123456789abcdef"));
        assert!(redacted.contains("[REDACTED]"));

        // Sensitive
        let sensitive = Sensitive("super-secret");
        let display = format!("{}", sensitive);
        let debug = format!("{:?}", sensitive);
        assert_eq!(display, "[REDACTED]");
        assert_eq!(debug, "[REDACTED]");
    }
}
