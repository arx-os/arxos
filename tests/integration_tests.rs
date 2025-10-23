// Integration tests for ArxOS IFC processing

#[cfg(test)]
mod ifc_tests {
    use std::fs;
    use arxos::ifc::IFCProcessor;
    
    #[test]
    fn test_ifc_processor_creation() {
        // Test that IFC processor can be created
        let _processor = IFCProcessor::new();
        // This should not panic
    }
    
    #[test]
    fn test_nonexistent_file_handling() {
        // Test error handling for non-existent files
        let processor = IFCProcessor::new();
        let result = processor.process_file("nonexistent.ifc");
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("IFC file not found"));
    }
    
    #[test]
    fn test_ifc_validation() {
        let processor = IFCProcessor::new();
        
        // Test valid IFC file
        let result = processor.validate_ifc_file("test_data/sample_building.ifc");
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), true);
        
        // Test non-existent file
        let result = processor.validate_ifc_file("nonexistent.ifc");
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("IFC file not found"));
        
        // Test file with wrong extension - create a temporary file
        let test_file = "test_file.txt";
        fs::write(test_file, "Some content").unwrap();
        
        let result = processor.validate_ifc_file(test_file);
        
        // Clean up
        fs::remove_file(test_file).unwrap();
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("File must have .ifc extension"));
    }
    
    #[test]
    fn test_invalid_ifc_format() {
        let processor = IFCProcessor::new();
        
        // Create temporary invalid IFC file
        let test_file = "invalid_test.ifc";
        std::fs::write(test_file, "INVALID IFC CONTENT").unwrap();
        
        let result = processor.validate_ifc_file(test_file);
        
        // Clean up
        std::fs::remove_file(test_file).unwrap();
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("Missing ISO-10303-21 header"));
    }
}

#[cfg(test)]
mod cli_tests {
    use std::process::Command;
    
    #[test]
    fn test_render_command_with_real_data() {
        // Test that render command works with real YAML data
        let output = Command::new("cargo")
            .args(&["run", "--", "render", "--building", "Floor-1", "--floor", "0"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should contain real building data
        assert!(stdout.contains("Building Floor-1"));
        assert!(stdout.contains("Floor 0"));
        assert!(stdout.contains("VAV-301"));
        assert!(stdout.contains("HVAC"));
        assert!(stdout.contains("Data Source: YAML building data"));
    }
    
    #[test]
    fn test_validate_command_yaml_files() {
        // Test that validate command works with YAML files
        let output = Command::new("cargo")
            .args(&["run", "--", "validate"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should find and validate YAML files
        assert!(stdout.contains("Validating current directory"));
        assert!(stdout.contains("Found 2 YAML file(s) to validate"));
        assert!(stdout.contains("validation passed"));
    }
    
    #[test]
    fn test_validate_command_ifc_file() {
        // Test that validate command works with IFC files
        let output = Command::new("cargo")
            .args(&["run", "--", "validate", "--path", "test_data/sample_building.ifc"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should validate IFC file successfully
        assert!(stdout.contains("Validating data at: test_data/sample_building.ifc"));
        assert!(stdout.contains("IFC file validation passed"));
    }
    
    #[test]
    fn test_validate_command_error_handling() {
        // Test error handling for non-existent files
        let output = Command::new("cargo")
            .args(&["run", "--", "validate", "--path", "nonexistent.ifc"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show proper error message
        assert!(stdout.contains("Validating data at: nonexistent.ifc"));
        assert!(stdout.contains("IFC file validation failed"));
        assert!(stdout.contains("IFC file not found"));
    }
    
    #[test]
    fn test_status_command_basic() {
        // Test that status command works in a Git repository
        let output = Command::new("cargo")
            .args(&["run", "--", "status"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show repository status
        assert!(stdout.contains("ArxOS Repository Status"));
        assert!(stdout.contains("Branch:"));
        assert!(stdout.contains("Last commit:"));
        assert!(stdout.contains("Working Directory Status:"));
    }
    
    #[test]
    fn test_status_command_verbose() {
        // Test that status command works with verbose flag
        let output = Command::new("cargo")
            .args(&["run", "--", "status", "--verbose"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show detailed information
        assert!(stdout.contains("ArxOS Repository Status"));
        assert!(stdout.contains("Recent Commits:"));
        assert!(stdout.contains("Working Directory Status:"));
    }
    
    #[test]
    fn test_status_command_outside_repo() {
        // Test status command outside a Git repository
        // Create a temporary directory without Git
        let temp_dir = tempfile::tempdir().unwrap();
        let temp_path = temp_dir.path();
        
        // Use the compiled binary directly
        let binary_path = std::env::current_dir()
            .unwrap()
            .join("target/debug/arxos");
        
        // Ensure binary exists
        if !binary_path.exists() {
            // Build the binary first
            let build_output = Command::new("cargo")
                .args(&["build"])
                .output()
                .expect("Failed to build binary");
            
            if !build_output.status.success() {
                panic!("Failed to build binary: {}", String::from_utf8_lossy(&build_output.stderr));
            }
        }
        
        let output = Command::new(&binary_path)
            .args(&["status"])
            .current_dir(temp_path)
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show appropriate error message
        assert!(stdout.contains("Not in a Git repository"));
        assert!(stdout.contains("Run 'arx import <file.ifc>' to initialize"));
        
        // temp_dir will be automatically cleaned up when it goes out of scope
    }
    
    #[test]
    fn test_diff_command_basic() {
        // Test that diff command works in a Git repository
        let output = Command::new("cargo")
            .args(&["run", "--", "diff"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show diff information
        assert!(stdout.contains("ArxOS Diff"));
        assert!(stdout.contains("Commit:"));
        assert!(stdout.contains("files changed"));
    }
    
    #[test]
    fn test_diff_command_stat() {
        // Test that diff command works with stat flag
        let output = Command::new("cargo")
            .args(&["run", "--", "diff", "--stat"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show statistics
        assert!(stdout.contains("ArxOS Diff"));
        assert!(stdout.contains("Diff Statistics:"));
        assert!(stdout.contains("Files changed:"));
        assert!(stdout.contains("Insertions:"));
        assert!(stdout.contains("Deletions:"));
    }
    
    #[test]
    fn test_diff_command_outside_repo() {
        // Test diff command outside a Git repository
        let temp_dir = tempfile::tempdir().unwrap();
        let temp_path = temp_dir.path();
        
        let binary_path = std::env::current_dir()
            .unwrap()
            .join("target/debug/arxos");
        
        // Ensure binary exists
        if !binary_path.exists() {
            // Build the binary first
            let build_output = Command::new("cargo")
                .args(&["build"])
                .output()
                .expect("Failed to build binary");
            
            if !build_output.status.success() {
                panic!("Failed to build binary: {}", String::from_utf8_lossy(&build_output.stderr));
            }
        }
        
        let output = Command::new(&binary_path)
            .args(&["diff"])
            .current_dir(temp_path)
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show appropriate error message
        assert!(stdout.contains("Not in a Git repository"));
        assert!(stdout.contains("Run 'arx import <file.ifc>' to initialize"));
        
        // temp_dir will be automatically cleaned up when it goes out of scope
    }
    
    #[test]
    fn test_history_command_basic() {
        // Test that history command works in a Git repository
        let output = Command::new("cargo")
            .args(&["run", "--", "history"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show history information
        assert!(stdout.contains("ArxOS History"));
        assert!(stdout.contains("Recent Commits"));
        assert!(stdout.contains("showing 10"));
    }
    
    #[test]
    fn test_history_command_verbose() {
        // Test that history command works with verbose flag
        let output = Command::new("cargo")
            .args(&["run", "--", "history", "--verbose", "--limit", "3"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show detailed information
        assert!(stdout.contains("ArxOS History"));
        assert!(stdout.contains("Commit #"));
        assert!(stdout.contains("Hash:"));
        assert!(stdout.contains("Author:"));
        assert!(stdout.contains("Date:"));
        assert!(stdout.contains("Message:"));
    }
    
    #[test]
    fn test_history_command_limit() {
        // Test that history command respects limit
        let output = Command::new("cargo")
            .args(&["run", "--", "history", "--limit", "5"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show limited number of commits
        assert!(stdout.contains("ArxOS History"));
        assert!(stdout.contains("showing 5"));
    }
    
    #[test]
    fn test_history_command_outside_repo() {
        // Test history command outside a Git repository
        let temp_dir = tempfile::tempdir().unwrap();
        let temp_path = temp_dir.path();
        
        let binary_path = std::env::current_dir()
            .unwrap()
            .join("target/debug/arxos");
        
        // Ensure binary exists
        if !binary_path.exists() {
            // Build the binary first
            let build_output = Command::new("cargo")
                .args(&["build"])
                .output()
                .expect("Failed to build binary");
            
            if !build_output.status.success() {
                panic!("Failed to build binary: {}", String::from_utf8_lossy(&build_output.stderr));
            }
        }
        
        let output = Command::new(&binary_path)
            .args(&["history"])
            .current_dir(temp_path)
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show appropriate error message
        assert!(stdout.contains("Not in a Git repository"));
        assert!(stdout.contains("Run 'arx import <file.ifc>' to initialize"));
        
        // temp_dir will be automatically cleaned up when it goes out of scope
    }
}

#[cfg(test)]
mod spatial_tests {
    use arxos::{SpatialEntity, BoundingBox3D, Point3D};
    
    #[test]
    fn test_spatial_entity_creation() {
        let entity = SpatialEntity {
            id: "test-123".to_string(),
            name: "Test Equipment".to_string(),
            entity_type: "HVAC".to_string(),
            position: Point3D::new(10.5, 8.2, 2.7),
            bounding_box: BoundingBox3D::new(
                Point3D::new(9.5, 7.2, 1.7),
                Point3D::new(11.5, 9.2, 3.7),
            ),
            coordinate_system: None,
        };
        
        assert_eq!(entity.id, "test-123");
        assert_eq!(entity.name, "Test Equipment");
        assert_eq!(entity.position.x, 10.5);
        assert_eq!(entity.position.y, 8.2);
        assert_eq!(entity.position.z, 2.7);
    }
}

#[cfg(test)]
mod live_monitoring_tests {
    use super::*;

    // Mock structures for live monitoring testing
    #[derive(Debug, Clone)]
    struct MockLiveMonitorState {
        current_building: Option<String>,
        current_floor: Option<i32>,
        current_room: Option<String>,
        sensors_only: bool,
        alerts_only: bool,
        refresh_interval: u64,
        last_refresh: std::time::Instant,
        selected_index: usize,
        view_mode: MockMonitorViewMode,
        show_help: bool,
        show_logs: bool,
        show_filters: bool,
        sensor_data: Vec<MockSensorReading>,
        alerts: Vec<MockAlert>,
        logs: Vec<MockLogEntry>,
    }

    #[derive(Debug, Clone)]
    enum MockMonitorViewMode {
        Overview,
        Sensors,
        Alerts,
        Logs,
        System,
        Filters,
    }

    #[derive(Debug, Clone)]
    struct MockSensorReading {
        id: String,
        name: String,
        sensor_type: String,
        value: f64,
        unit: String,
        location: String,
        status: String,
    }

    #[derive(Debug, Clone)]
    struct MockAlert {
        id: String,
        severity: MockAlertSeverity,
        title: String,
        description: String,
        location: String,
        acknowledged: bool,
    }

    #[derive(Debug, Clone)]
    enum MockAlertSeverity {
        Info,
        Warning,
        Error,
        Critical,
    }

    #[derive(Debug, Clone)]
    struct MockLogEntry {
        timestamp: String,
        level: MockLogLevel,
        source: String,
        message: String,
    }

    #[derive(Debug, Clone)]
    enum MockLogLevel {
        Debug,
        Info,
        Warning,
        Error,
    }

    impl MockLiveMonitorState {
        fn new() -> Self {
            Self {
                current_building: None,
                current_floor: None,
                current_room: None,
                sensors_only: false,
                alerts_only: false,
                refresh_interval: 5,
                last_refresh: std::time::Instant::now(),
                selected_index: 0,
                view_mode: MockMonitorViewMode::Overview,
                show_help: false,
                show_logs: false,
                show_filters: false,
                sensor_data: Vec::new(),
                alerts: Vec::new(),
                logs: Vec::new(),
            }
        }

        fn load_sample_data(&mut self) {
            self.sensor_data = vec![
                MockSensorReading {
                    id: "temp_001".to_string(),
                    name: "Temperature Sensor".to_string(),
                    sensor_type: "DHT22".to_string(),
                    value: 22.5,
                    unit: "°C".to_string(),
                    location: "Room 301".to_string(),
                    status: "Normal".to_string(),
                },
                MockSensorReading {
                    id: "humidity_001".to_string(),
                    name: "Humidity Sensor".to_string(),
                    sensor_type: "DHT22".to_string(),
                    value: 45.2,
                    unit: "%".to_string(),
                    location: "Room 301".to_string(),
                    status: "Normal".to_string(),
                },
            ];

            self.alerts = vec![
                MockAlert {
                    id: "alert_001".to_string(),
                    severity: MockAlertSeverity::Warning,
                    title: "High Temperature Detected".to_string(),
                    description: "Temperature exceeded threshold".to_string(),
                    location: "Room 301".to_string(),
                    acknowledged: false,
                },
            ];

            self.logs = vec![
                MockLogEntry {
                    timestamp: "2024-01-01T12:00:00Z".to_string(),
                    level: MockLogLevel::Info,
                    source: "SensorProcessor".to_string(),
                    message: "Processing sensor data".to_string(),
                },
            ];
        }

        fn navigate_up(&mut self) {
            if self.selected_index > 0 {
                self.selected_index -= 1;
            }
        }

        fn navigate_down(&mut self) {
            let max_items = match self.view_mode {
                MockMonitorViewMode::Overview => 5,
                MockMonitorViewMode::Sensors => self.sensor_data.len(),
                MockMonitorViewMode::Alerts => self.alerts.len(),
                MockMonitorViewMode::Logs => self.logs.len(),
                MockMonitorViewMode::System => 7,
                MockMonitorViewMode::Filters => 6,
            };
            if self.selected_index < max_items.saturating_sub(1) {
                self.selected_index += 1;
            }
        }

        fn toggle_help(&mut self) {
            self.show_help = !self.show_help;
        }

        fn toggle_log_view(&mut self) {
            self.show_logs = !self.show_logs;
            if self.show_logs {
                self.view_mode = MockMonitorViewMode::Logs;
            } else {
                self.view_mode = MockMonitorViewMode::Overview;
            }
        }

        fn toggle_filter(&mut self) {
            self.show_filters = !self.show_filters;
            if self.show_filters {
                self.view_mode = MockMonitorViewMode::Filters;
            } else {
                self.view_mode = MockMonitorViewMode::Overview;
            }
        }

        fn toggle_alerts_only(&mut self) {
            self.alerts_only = !self.alerts_only;
            if self.alerts_only {
                self.view_mode = MockMonitorViewMode::Alerts;
            }
        }

        fn toggle_sensors_only(&mut self) {
            self.sensors_only = !self.sensors_only;
            if self.sensors_only {
                self.view_mode = MockMonitorViewMode::Sensors;
            }
        }

        fn should_refresh(&self) -> bool {
            self.last_refresh.elapsed().as_secs() >= self.refresh_interval
        }
    }

    #[test]
    fn test_live_monitor_state_creation() {
        let state = MockLiveMonitorState::new();
        assert_eq!(state.refresh_interval, 5);
        assert_eq!(state.selected_index, 0);
        assert!(!state.show_help);
        assert!(!state.show_logs);
        assert!(!state.show_filters);
        assert!(!state.sensors_only);
        assert!(!state.alerts_only);
    }

    #[test]
    fn test_sample_data_loading() {
        let mut state = MockLiveMonitorState::new();
        state.load_sample_data();
        
        assert_eq!(state.sensor_data.len(), 2);
        assert_eq!(state.alerts.len(), 1);
        assert_eq!(state.logs.len(), 1);
        
        assert_eq!(state.sensor_data[0].name, "Temperature Sensor");
        assert_eq!(state.sensor_data[0].value, 22.5);
        assert_eq!(state.alerts[0].title, "High Temperature Detected");
    }

    #[test]
    fn test_navigation_up() {
        let mut state = MockLiveMonitorState::new();
        state.selected_index = 1;
        state.navigate_up();
        assert_eq!(state.selected_index, 0);
        
        state.navigate_up(); // Should not go below 0
        assert_eq!(state.selected_index, 0);
    }

    #[test]
    fn test_navigation_down() {
        let mut state = MockLiveMonitorState::new();
        state.load_sample_data();
        state.view_mode = MockMonitorViewMode::Sensors;
        
        state.navigate_down();
        assert_eq!(state.selected_index, 1);
        
        state.navigate_down(); // Should not exceed bounds
        assert_eq!(state.selected_index, 1);
    }

    #[test]
    fn test_help_toggle() {
        let mut state = MockLiveMonitorState::new();
        assert!(!state.show_help);
        
        state.toggle_help();
        assert!(state.show_help);
        
        state.toggle_help();
        assert!(!state.show_help);
    }

    #[test]
    fn test_log_view_toggle() {
        let mut state = MockLiveMonitorState::new();
        assert!(!state.show_logs);
        
        state.toggle_log_view();
        assert!(state.show_logs);
        assert!(matches!(state.view_mode, MockMonitorViewMode::Logs));
        
        state.toggle_log_view();
        assert!(!state.show_logs);
        assert!(matches!(state.view_mode, MockMonitorViewMode::Overview));
    }

    #[test]
    fn test_filter_toggle() {
        let mut state = MockLiveMonitorState::new();
        assert!(!state.show_filters);
        
        state.toggle_filter();
        assert!(state.show_filters);
        assert!(matches!(state.view_mode, MockMonitorViewMode::Filters));
        
        state.toggle_filter();
        assert!(!state.show_filters);
        assert!(matches!(state.view_mode, MockMonitorViewMode::Overview));
    }

    #[test]
    fn test_alerts_only_toggle() {
        let mut state = MockLiveMonitorState::new();
        assert!(!state.alerts_only);
        
        state.toggle_alerts_only();
        assert!(state.alerts_only);
        assert!(matches!(state.view_mode, MockMonitorViewMode::Alerts));
        
        state.toggle_alerts_only();
        assert!(!state.alerts_only);
    }

    #[test]
    fn test_sensors_only_toggle() {
        let mut state = MockLiveMonitorState::new();
        assert!(!state.sensors_only);
        
        state.toggle_sensors_only();
        assert!(state.sensors_only);
        assert!(matches!(state.view_mode, MockMonitorViewMode::Sensors));
        
        state.toggle_sensors_only();
        assert!(!state.sensors_only);
    }

    #[test]
    fn test_refresh_timing() {
        let mut state = MockLiveMonitorState::new();
        state.refresh_interval = 1; // 1 second
        
        // Should not refresh immediately
        assert!(!state.should_refresh());
        
        // Wait a bit and test again
        std::thread::sleep(std::time::Duration::from_millis(100));
        assert!(!state.should_refresh());
    }

    #[test]
    fn test_sensor_data_structure() {
        let sensor = MockSensorReading {
            id: "test_001".to_string(),
            name: "Test Sensor".to_string(),
            sensor_type: "DHT22".to_string(),
            value: 25.0,
            unit: "°C".to_string(),
            location: "Test Room".to_string(),
            status: "Normal".to_string(),
        };
        
        assert_eq!(sensor.id, "test_001");
        assert_eq!(sensor.value, 25.0);
        assert_eq!(sensor.unit, "°C");
    }

    #[test]
    fn test_alert_data_structure() {
        let alert = MockAlert {
            id: "alert_001".to_string(),
            severity: MockAlertSeverity::Warning,
            title: "Test Alert".to_string(),
            description: "Test description".to_string(),
            location: "Test Location".to_string(),
            acknowledged: false,
        };
        
        assert_eq!(alert.id, "alert_001");
        assert!(!alert.acknowledged);
        assert!(matches!(alert.severity, MockAlertSeverity::Warning));
    }

    #[test]
    fn test_log_data_structure() {
        let log = MockLogEntry {
            timestamp: "2024-01-01T12:00:00Z".to_string(),
            level: MockLogLevel::Info,
            source: "TestSource".to_string(),
            message: "Test message".to_string(),
        };
        
        assert_eq!(log.source, "TestSource");
        assert!(matches!(log.level, MockLogLevel::Info));
    }

    #[test]
    fn test_view_mode_transitions() {
        let mut state = MockLiveMonitorState::new();
        state.load_sample_data();
        
        // Test transitioning to sensors view
        state.toggle_sensors_only();
        assert!(matches!(state.view_mode, MockMonitorViewMode::Sensors));
        
        // Test transitioning to alerts view
        state.toggle_alerts_only();
        assert!(matches!(state.view_mode, MockMonitorViewMode::Alerts));
        
        // Test transitioning to logs view
        state.toggle_log_view();
        assert!(matches!(state.view_mode, MockMonitorViewMode::Logs));
    }
}

#[cfg(test)]
mod interactive_explorer_tests {
    use std::time::Duration;
    
    // Mock the explorer state for testing
    #[derive(Debug, Clone)]
    enum ViewMode {
        Buildings,
        Floors,
        Rooms,
        Equipment,
    }
    
    #[derive(Debug, Clone)]
    struct RoomInfo {
        id: String,
        name: String,
        room_type: String,
        floor: i32,
        wing: String,
        equipment_count: usize,
        status: String,
    }
    
    #[derive(Debug, Clone)]
    struct EquipmentInfo {
        id: String,
        name: String,
        equipment_type: String,
        room_id: String,
        status: String,
        position: String,
        last_updated: String,
    }
    
    #[derive(Debug)]
    struct MockBuildingExplorerState {
        current_building: Option<String>,
        current_floor: Option<i32>,
        current_room: Option<String>,
        auto_refresh: bool,
        refresh_interval: u64,
        last_refresh: std::time::Instant,
        
        selected_index: usize,
        view_mode: ViewMode,
        show_help: bool,
        
        buildings: Vec<String>,
        floors: Vec<i32>,
        rooms: Vec<RoomInfo>,
        equipment: Vec<EquipmentInfo>,
    }
    
    impl MockBuildingExplorerState {
        fn new(
            building: Option<String>,
            floor: Option<i32>,
            room: Option<String>,
            auto_refresh: bool,
            refresh_interval: u64,
        ) -> Self {
            Self {
                current_building: building,
                current_floor: floor,
                current_room: room,
                auto_refresh,
                refresh_interval,
                last_refresh: std::time::Instant::now(),
                selected_index: 0,
                view_mode: ViewMode::Buildings,
                show_help: false,
                buildings: Vec::new(),
                floors: Vec::new(),
                rooms: Vec::new(),
                equipment: Vec::new(),
            }
        }
        
        fn load_sample_data(&mut self) {
            self.buildings = vec![
                "B1 - Main Building".to_string(),
                "B2 - Annex Building".to_string(),
                "B3 - Gymnasium".to_string(),
            ];
            
            if self.current_building.is_some() {
                self.floors = vec![1, 2, 3];
            }
            
            if let Some(floor) = self.current_floor {
                self.rooms = vec![
                    RoomInfo {
                        id: "room_001".to_string(),
                        name: "Classroom 101".to_string(),
                        room_type: "classroom".to_string(),
                        floor,
                        wing: "North".to_string(),
                        equipment_count: 5,
                        status: "active".to_string(),
                    },
                    RoomInfo {
                        id: "room_002".to_string(),
                        name: "Classroom 102".to_string(),
                        room_type: "classroom".to_string(),
                        floor,
                        wing: "North".to_string(),
                        equipment_count: 3,
                        status: "active".to_string(),
                    },
                ];
            }
            
            if let Some(ref room_id) = self.current_room {
                self.equipment = vec![
                    EquipmentInfo {
                        id: "eq_001".to_string(),
                        name: "HVAC Unit".to_string(),
                        equipment_type: "hvac".to_string(),
                        room_id: room_id.clone(),
                        status: "operational".to_string(),
                        position: "(10.5, 5.2, 2.1)".to_string(),
                        last_updated: "2024-12-01T10:30:00Z".to_string(),
                    },
                ];
            }
        }
        
        fn navigate_up(&mut self) {
            match self.view_mode {
                ViewMode::Buildings => {
                    if self.selected_index > 0 {
                        self.selected_index -= 1;
                    }
                }
                ViewMode::Floors => {
                    if self.selected_index > 0 {
                        self.selected_index -= 1;
                    }
                }
                ViewMode::Rooms => {
                    if self.selected_index > 0 {
                        self.selected_index -= 1;
                    }
                }
                ViewMode::Equipment => {
                    if self.selected_index > 0 {
                        self.selected_index -= 1;
                    }
                }
            }
        }
        
        fn navigate_down(&mut self) {
            match self.view_mode {
                ViewMode::Buildings => {
                    if self.selected_index < self.buildings.len().saturating_sub(1) {
                        self.selected_index += 1;
                    }
                }
                ViewMode::Floors => {
                    if self.selected_index < self.floors.len().saturating_sub(1) {
                        self.selected_index += 1;
                    }
                }
                ViewMode::Rooms => {
                    if self.selected_index < self.rooms.len().saturating_sub(1) {
                        self.selected_index += 1;
                    }
                }
                ViewMode::Equipment => {
                    if self.selected_index < self.equipment.len().saturating_sub(1) {
                        self.selected_index += 1;
                    }
                }
            }
        }
        
        fn navigate_left(&mut self) {
            match self.view_mode {
                ViewMode::Buildings => {}
                ViewMode::Floors => {
                    self.view_mode = ViewMode::Buildings;
                    self.selected_index = 0;
                }
                ViewMode::Rooms => {
                    self.view_mode = ViewMode::Floors;
                    self.selected_index = 0;
                }
                ViewMode::Equipment => {
                    self.view_mode = ViewMode::Rooms;
                    self.selected_index = 0;
                }
            }
        }
        
        fn navigate_right(&mut self) {
            match self.view_mode {
                ViewMode::Buildings => {
                    if !self.buildings.is_empty() {
                        self.current_building = Some(self.buildings[self.selected_index].clone());
                        self.view_mode = ViewMode::Floors;
                        self.selected_index = 0;
                    }
                }
                ViewMode::Floors => {
                    if !self.floors.is_empty() {
                        self.current_floor = Some(self.floors[self.selected_index]);
                        self.view_mode = ViewMode::Rooms;
                        self.selected_index = 0;
                    }
                }
                ViewMode::Rooms => {
                    if !self.rooms.is_empty() {
                        self.current_room = Some(self.rooms[self.selected_index].id.clone());
                        self.view_mode = ViewMode::Equipment;
                        self.selected_index = 0;
                    }
                }
                ViewMode::Equipment => {}
            }
        }
        
        fn should_auto_refresh(&self) -> bool {
            self.auto_refresh && 
            self.last_refresh.elapsed() >= Duration::from_secs(self.refresh_interval)
        }
        
        fn toggle_help(&mut self) {
            self.show_help = !self.show_help;
        }
    }
    
    #[test]
    fn test_explorer_state_creation() {
        let state = MockBuildingExplorerState::new(
            Some("B1".to_string()),
            Some(1),
            Some("room_001".to_string()),
            true,
            5,
        );
        
        assert_eq!(state.current_building, Some("B1".to_string()));
        assert_eq!(state.current_floor, Some(1));
        assert_eq!(state.current_room, Some("room_001".to_string()));
        assert_eq!(state.auto_refresh, true);
        assert_eq!(state.refresh_interval, 5);
        assert_eq!(state.selected_index, 0);
        assert_eq!(state.show_help, false);
    }
    
    #[test]
    fn test_sample_data_loading() {
        let mut state = MockBuildingExplorerState::new(
            Some("B1".to_string()),
            Some(1),
            Some("room_001".to_string()),
            false,
            5,
        );
        
        state.load_sample_data();
        
        assert_eq!(state.buildings.len(), 3);
        assert_eq!(state.buildings[0], "B1 - Main Building");
        assert_eq!(state.floors.len(), 3);
        assert_eq!(state.floors[0], 1);
        assert_eq!(state.rooms.len(), 2);
        assert_eq!(state.rooms[0].name, "Classroom 101");
        assert_eq!(state.equipment.len(), 1);
        assert_eq!(state.equipment[0].name, "HVAC Unit");
    }
    
    #[test]
    fn test_navigation_up() {
        let mut state = MockBuildingExplorerState::new(None, None, None, false, 5);
        state.load_sample_data();
        
        // Start at index 0
        assert_eq!(state.selected_index, 0);
        
        // Navigate up should not change index when at 0
        state.navigate_up();
        assert_eq!(state.selected_index, 0);
        
        // Move down first
        state.navigate_down();
        assert_eq!(state.selected_index, 1);
        
        // Now navigate up should work
        state.navigate_up();
        assert_eq!(state.selected_index, 0);
    }
    
    #[test]
    fn test_navigation_down() {
        let mut state = MockBuildingExplorerState::new(None, None, None, false, 5);
        state.load_sample_data();
        
        // Start at index 0
        assert_eq!(state.selected_index, 0);
        
        // Navigate down should work
        state.navigate_down();
        assert_eq!(state.selected_index, 1);
        
        state.navigate_down();
        assert_eq!(state.selected_index, 2);
        
        // At the end, should not go further
        state.navigate_down();
        assert_eq!(state.selected_index, 2);
    }
    
    #[test]
    fn test_navigation_right() {
        let mut state = MockBuildingExplorerState::new(None, None, None, false, 5);
        state.load_sample_data();
        
        // Start in Buildings view
        assert_eq!(state.selected_index, 0);
        
        // Navigate right should select building and move to floors
        state.navigate_right();
        assert_eq!(state.current_building, Some("B1 - Main Building".to_string()));
        assert_eq!(state.selected_index, 0);
        
        // Load floors data for the selected building
        state.load_sample_data();
        
        // Navigate right again should select floor and move to rooms
        state.navigate_right();
        assert_eq!(state.current_floor, Some(1));
        assert_eq!(state.selected_index, 0);
        
        // Load rooms data for the selected floor
        state.load_sample_data();
        
        // Navigate right again should select room and move to equipment
        state.navigate_right();
        assert_eq!(state.current_room, Some("room_001".to_string()));
        assert_eq!(state.selected_index, 0);
    }
    
    #[test]
    fn test_navigation_left() {
        let mut state = MockBuildingExplorerState::new(
            Some("B1".to_string()),
            Some(1),
            Some("room_001".to_string()),
            false,
            5,
        );
        state.load_sample_data();
        
        // Start in Equipment view
        state.view_mode = ViewMode::Equipment;
        
        // Navigate left should go back to rooms
        state.navigate_left();
        assert_eq!(state.selected_index, 0);
        
        // Navigate left again should go back to floors
        state.navigate_left();
        assert_eq!(state.selected_index, 0);
        
        // Navigate left again should go back to buildings
        state.navigate_left();
        assert_eq!(state.selected_index, 0);
        
        // Navigate left from buildings should not change
        state.navigate_left();
        assert_eq!(state.selected_index, 0);
    }
    
    #[test]
    fn test_auto_refresh_logic() {
        let mut state = MockBuildingExplorerState::new(None, None, None, true, 1);
        
        // Should not auto-refresh immediately
        assert_eq!(state.should_auto_refresh(), false);
        
        // Wait for refresh interval
        std::thread::sleep(Duration::from_millis(1100));
        
        // Should auto-refresh now
        assert_eq!(state.should_auto_refresh(), true);
    }
    
    #[test]
    fn test_help_toggle() {
        let mut state = MockBuildingExplorerState::new(None, None, None, false, 5);
        
        // Start with help off
        assert_eq!(state.show_help, false);
        
        // Toggle help on
        state.toggle_help();
        assert_eq!(state.show_help, true);
        
        // Toggle help off
        state.toggle_help();
        assert_eq!(state.show_help, false);
    }
    
    #[test]
    fn test_room_info_structure() {
        let room = RoomInfo {
            id: "room_001".to_string(),
            name: "Classroom 101".to_string(),
            room_type: "classroom".to_string(),
            floor: 1,
            wing: "North".to_string(),
            equipment_count: 5,
            status: "active".to_string(),
        };
        
        assert_eq!(room.id, "room_001");
        assert_eq!(room.name, "Classroom 101");
        assert_eq!(room.room_type, "classroom");
        assert_eq!(room.floor, 1);
        assert_eq!(room.wing, "North");
        assert_eq!(room.equipment_count, 5);
        assert_eq!(room.status, "active");
    }
    
    #[test]
    fn test_equipment_info_structure() {
        let equipment = EquipmentInfo {
            id: "eq_001".to_string(),
            name: "HVAC Unit".to_string(),
            equipment_type: "hvac".to_string(),
            room_id: "room_001".to_string(),
            status: "operational".to_string(),
            position: "(10.5, 5.2, 2.1)".to_string(),
            last_updated: "2024-12-01T10:30:00Z".to_string(),
        };
        
        assert_eq!(equipment.id, "eq_001");
        assert_eq!(equipment.name, "HVAC Unit");
        assert_eq!(equipment.equipment_type, "hvac");
        assert_eq!(equipment.room_id, "room_001");
        assert_eq!(equipment.status, "operational");
        assert_eq!(equipment.position, "(10.5, 5.2, 2.1)");
        assert_eq!(equipment.last_updated, "2024-12-01T10:30:00Z");
    }
    
    #[test]
    fn test_view_mode_transitions() {
        let mut state = MockBuildingExplorerState::new(None, None, None, false, 5);
        state.load_sample_data();
        
        // Start in Buildings view
        assert!(matches!(state.view_mode, ViewMode::Buildings));
        
        // Navigate right to floors
        state.navigate_right();
        assert!(matches!(state.view_mode, ViewMode::Floors));
        
        // Load floors data and navigate right to rooms
        state.load_sample_data();
        state.navigate_right();
        assert!(matches!(state.view_mode, ViewMode::Rooms));
        
        // Load rooms data and navigate right to equipment
        state.load_sample_data();
        state.navigate_right();
        assert!(matches!(state.view_mode, ViewMode::Equipment));
        
        // Navigate left back to rooms
        state.navigate_left();
        assert!(matches!(state.view_mode, ViewMode::Rooms));
        
        // Navigate left back to floors
        state.navigate_left();
        assert!(matches!(state.view_mode, ViewMode::Floors));
        
        // Navigate left back to buildings
        state.navigate_left();
        assert!(matches!(state.view_mode, ViewMode::Buildings));
    }
}
