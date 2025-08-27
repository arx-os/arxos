package models

import (
	"fmt"
	"strings"
)

// SystemRelationship defines how systems interconnect
type SystemRelationship struct {
	FromID       string                 `json:"from_id"`
	ToID         string                 `json:"to_id"`
	Type         string                 `json:"type"`         // powers, controls, feeds, monitors, serves
	Properties   map[string]interface{} `json:"properties"`   // voltage, amperage, flow_rate, bandwidth
	Bidirectional bool                  `json:"bidirectional"`
	Critical     bool                   `json:"critical"`     // Is this a critical dependency?
}

// Standard relationship types across all systems
const (
	// Electrical relationships
	RelPowers           = "powers"            // Electrical circuit powers equipment
	RelFeedsFrom        = "feeds_from"        // Equipment fed from panel/circuit
	RelBackupPower      = "backup_power"      // UPS/generator backup
	
	// Control relationships  
	RelControls         = "controls"          // BAS/controller controls equipment
	RelControlledBy     = "controlled_by"     // Equipment controlled by system
	RelMonitors         = "monitors"          // Sensor monitors equipment/space
	RelMonitoredBy      = "monitored_by"      // Equipment monitored by sensor
	
	// Physical relationships
	RelServes           = "serves"            // HVAC serves space, pump serves loop
	RelServedBy         = "served_by"         // Space served by HVAC
	RelConnectsTo       = "connects_to"       // Physical connection (pipe, duct, wire)
	RelContains         = "contains"          // Panel contains breakers, room contains equipment
	
	// Data relationships
	RelCommunicatesWith = "communicates_with" // Network/data connection
	RelReportsTo        = "reports_to"        // Device reports to system
)

// CrossSystemConnection represents a connection between different systems
type CrossSystemConnection struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	
	// Source system
	SourceSystem string                 `json:"source_system"` // electrical, hvac, plumbing
	SourceID     string                 `json:"source_id"`     // Full ArxObject ID
	SourceType   string                 `json:"source_type"`   // breaker, valve, damper
	
	// Target system
	TargetSystem string                 `json:"target_system"`
	TargetID     string                 `json:"target_id"`
	TargetType   string                 `json:"target_type"`
	
	// Connection details
	ConnectionType string               `json:"connection_type"` // power, control, data, fluid
	Properties     map[string]interface{} `json:"properties"`
	
	// Operational data
	Status       string                 `json:"status"`        // active, inactive, fault
	LoadInfo     *LoadInformation       `json:"load_info,omitempty"`
}

// LoadInformation for electrical connections
type LoadInformation struct {
	Voltage      float64 `json:"voltage"`       // Operating voltage
	Current      float64 `json:"current_amps"`  // Current draw
	Power        float64 `json:"power_watts"`   // Power consumption
	PowerFactor  float64 `json:"power_factor"`  // For AC loads
	Phase        string  `json:"phase"`         // single, three
}

// Real-world Examples of Cross-System Connections

// Example 1: HVAC Unit powered by Electrical
var HVACPowerConnection = CrossSystemConnection{
	Name:         "AHU-1 Power Feed",
	Description:  "Air Handler Unit 1 electrical connection",
	SourceSystem: "electrical",
	SourceID:     "hq/electrical/panel/mdf/breaker/24/circuit/hvac/ahu_1",
	SourceType:   "circuit",
	TargetSystem: "hvac",
	TargetID:     "hq/hvac/ahu/1",
	TargetType:   "air_handler",
	ConnectionType: "power",
	Properties: map[string]interface{}{
		"voltage":        208,
		"phase":          "three",
		"breaker_amps":   30,
		"wire_size":      "10_awg",
		"disconnect":     "hq/electrical/disconnect/ahu_1",
		"lockout_tagout": true,
	},
	LoadInfo: &LoadInformation{
		Voltage:     208,
		Current:     22.5,
		Power:       8100,
		PowerFactor: 0.85,
		Phase:       "three",
	},
}

// Example 2: Network Switch in IDF powered by outlet
var NetworkPowerConnection = CrossSystemConnection{
	Name:         "IDF Switch Power",
	Description:  "Network switch power connection",
	SourceSystem: "electrical",
	SourceID:     "hq/electrical/panel/idf_1/breaker/5/circuit/outlet/rack_1",
	SourceType:   "outlet",
	TargetSystem: "network",
	TargetID:     "hq/network/switch/core_sw_1",
	TargetType:   "switch",
	ConnectionType: "power",
	Properties: map[string]interface{}{
		"outlet_type":    "nema_5_20r",
		"ups_protected":  true,
		"ups_id":         "hq/electrical/ups/idf_1",
		"redundant_feed": "hq/electrical/panel/idf_1/breaker/6/circuit/outlet/rack_1_b",
	},
	LoadInfo: &LoadInformation{
		Voltage: 120,
		Current: 2.5,
		Power:   300,
	},
}

// Example 3: BAS Controller with power and network
var BASControllerConnections = []CrossSystemConnection{
	{
		Name:         "BAS Controller Power",
		SourceSystem: "electrical",
		SourceID:     "hq/electrical/panel/bas/breaker/1/circuit/outlet/controller_1",
		TargetSystem: "bas",
		TargetID:     "hq/bas/controller/main",
		ConnectionType: "power",
	},
	{
		Name:         "BAS Controller Network",
		SourceSystem: "network",
		SourceID:     "hq/network/switch/bas_sw_1/port/12",
		TargetSystem: "bas",
		TargetID:     "hq/bas/controller/main",
		ConnectionType: "data",
		Properties: map[string]interface{}{
			"protocol":  "bacnet_ip",
			"vlan":      "bas_control",
			"bandwidth": "1gbps",
		},
	},
	{
		Name:         "BAS Controls AHU",
		SourceSystem: "bas",
		SourceID:     "hq/bas/controller/main",
		TargetSystem: "hvac",
		TargetID:     "hq/hvac/ahu/1",
		ConnectionType: "control",
		Properties: map[string]interface{}{
			"control_points": []string{"start_stop", "temp_setpoint", "fan_speed"},
			"protocol":       "modbus",
		},
	},
}

// Example 4: Security Camera with PoE
var SecurityCameraConnection = CrossSystemConnection{
	Name:         "Security Camera PoE",
	Description:  "Camera powered over ethernet",
	SourceSystem: "network",
	SourceID:     "hq/network/switch/poe_sw_1/port/8",
	SourceType:   "poe_port",
	TargetSystem: "security",
	TargetID:     "hq/security/camera/entrance_1",
	TargetType:   "ip_camera",
	ConnectionType: "power_and_data",
	Properties: map[string]interface{}{
		"poe_standard": "802.3at",
		"power_watts":  25,
		"data_rate":    "100mbps",
		"vlan":         "security",
	},
}

// SystemDependencyMap tracks critical dependencies
type SystemDependencyMap struct {
	SystemID      string                    `json:"system_id"`
	Dependencies  []SystemDependency        `json:"dependencies"`
	Provides      []string                  `json:"provides"`     // What this system provides
	RequiredFor   []string                  `json:"required_for"` // What systems need this
}

type SystemDependency struct {
	DependsOn    string  `json:"depends_on"`    // System ID
	Type         string  `json:"type"`          // power, control, data
	Criticality  string  `json:"criticality"`   // critical, important, nice-to-have
	FailoverPath string  `json:"failover_path"` // Backup/redundant path
}

// GetSystemDependencies returns all dependencies for a system
func GetSystemDependencies(systemID string) *SystemDependencyMap {
	// This would query the actual dependency graph
	// For demonstration, return example for HVAC
	
	if strings.Contains(systemID, "hvac") {
		return &SystemDependencyMap{
			SystemID: systemID,
			Dependencies: []SystemDependency{
				{
					DependsOn:   "electrical/panel/mdf/breaker/24",
					Type:        "power",
					Criticality: "critical",
					FailoverPath: "electrical/generator/emergency",
				},
				{
					DependsOn:   "bas/controller/main",
					Type:        "control",
					Criticality: "important",
					FailoverPath: "local_controls",
				},
				{
					DependsOn:   "plumbing/chilled_water/supply",
					Type:        "thermal",
					Criticality: "critical",
				},
			},
			Provides: []string{
				"conditioned_air",
				"ventilation",
				"humidity_control",
			},
			RequiredFor: []string{
				"occupant_comfort",
				"equipment_cooling",
				"air_quality",
			},
		}
	}
	
	return nil
}

// PowerDistributionTree shows electrical hierarchy with connected systems
type PowerDistributionTree struct {
	NodeID       string                    `json:"node_id"`
	NodeType     string                    `json:"node_type"` // transformer, panel, breaker, circuit
	Voltage      float64                   `json:"voltage"`
	TotalLoad    float64                   `json:"total_load_amps"`
	Capacity     float64                   `json:"capacity_amps"`
	Children     []*PowerDistributionTree  `json:"children"`
	ConnectedSystems []ConnectedSystem     `json:"connected_systems"`
}

type ConnectedSystem struct {
	SystemType   string  `json:"system_type"`   // hvac, network, lighting
	SystemID     string  `json:"system_id"`
	DeviceName   string  `json:"device_name"`
	LoadAmps     float64 `json:"load_amps"`
	Critical     bool    `json:"critical"`
}

// Example Power Distribution showing cross-system connections
var ExamplePowerTree = &PowerDistributionTree{
	NodeID:   "hq/electrical/panel/mdf",
	NodeType: "panel",
	Voltage:  208,
	Capacity: 400,
	TotalLoad: 287,
	Children: []*PowerDistributionTree{
		{
			NodeID:    "hq/electrical/panel/mdf/breaker/1",
			NodeType:  "breaker",
			Voltage:   208,
			Capacity:  20,
			TotalLoad: 15,
			ConnectedSystems: []ConnectedSystem{
				{
					SystemType: "lighting",
					SystemID:   "hq/lighting/circuit/f1_north",
					DeviceName: "Floor 1 North Lighting",
					LoadAmps:   15,
				},
			},
		},
		{
			NodeID:    "hq/electrical/panel/mdf/breaker/12",
			NodeType:  "breaker",
			Voltage:   120,
			Capacity:  15,
			TotalLoad: 8,
			ConnectedSystems: []ConnectedSystem{
				{
					SystemType: "electrical",
					SystemID:   "hq/electrical/outlet/f1_r101_north_1",
					DeviceName: "Smart Outlet",
					LoadAmps:   1.5,
				},
				{
					SystemType: "hardware",
					SystemID:   "hq/hardware/device/sensor_node_1",
					DeviceName: "IoT Sensor Node",
					LoadAmps:   0.1,
				},
			},
		},
		{
			NodeID:    "hq/electrical/panel/mdf/breaker/24",
			NodeType:  "breaker",
			Voltage:   208,
			Capacity:  30,
			TotalLoad: 22.5,
			ConnectedSystems: []ConnectedSystem{
				{
					SystemType: "hvac",
					SystemID:   "hq/hvac/ahu/1",
					DeviceName: "Air Handler Unit 1",
					LoadAmps:   22.5,
					Critical:   true,
				},
			},
		},
		{
			NodeID:    "hq/electrical/panel/mdf/breaker/30",
			NodeType:  "breaker", 
			Voltage:   120,
			Capacity:  20,
			TotalLoad: 12,
			ConnectedSystems: []ConnectedSystem{
				{
					SystemType: "network",
					SystemID:   "hq/network/rack/mdf_1",
					DeviceName: "Network Rack MDF",
					LoadAmps:   10,
					Critical:   true,
				},
				{
					SystemType: "security",
					SystemID:   "hq/security/panel/main",
					DeviceName: "Security Panel",
					LoadAmps:   2,
					Critical:   true,
				},
			},
		},
	},
}

// ValidateCrossSystemConnection ensures connection is valid
func ValidateCrossSystemConnection(conn *CrossSystemConnection) error {
	// Check electrical connections have proper load info
	if conn.ConnectionType == "power" && conn.LoadInfo == nil {
		return fmt.Errorf("power connection missing load information")
	}
	
	// Verify voltage compatibility
	if conn.ConnectionType == "power" && conn.LoadInfo != nil {
		sourceVoltage, _ := conn.Properties["voltage"].(float64)
		if sourceVoltage > 0 && conn.LoadInfo.Voltage != sourceVoltage {
			return fmt.Errorf("voltage mismatch: source=%v, load=%v", 
				sourceVoltage, conn.LoadInfo.Voltage)
		}
	}
	
	// Check data connections have protocol info
	if conn.ConnectionType == "data" {
		if _, ok := conn.Properties["protocol"]; !ok {
			return fmt.Errorf("data connection missing protocol information")
		}
	}
	
	return nil
}

// FindPowerSource traces back to find electrical source for any equipment
func FindPowerSource(equipmentID string) (*PowerPath, error) {
	// This would traverse the relationship graph to find power source
	// Returns the complete electrical path from equipment to panel/transformer
	
	path := &PowerPath{
		EquipmentID: equipmentID,
		PowerChain: []PowerNode{
			{ID: "hq/electrical/outlet/f1_r101_north_1", Type: "outlet", Voltage: 120},
			{ID: "hq/electrical/panel/mdf/breaker/12/circuit/outlet/1", Type: "circuit", Voltage: 120},
			{ID: "hq/electrical/panel/mdf/breaker/12", Type: "breaker", Voltage: 120, Amperage: 15},
			{ID: "hq/electrical/panel/mdf", Type: "panel", Voltage: 208},
			{ID: "hq/electrical/transformer/main", Type: "transformer", Voltage: 480},
		},
	}
	
	return path, nil
}

type PowerPath struct {
	EquipmentID string      `json:"equipment_id"`
	PowerChain  []PowerNode `json:"power_chain"` // From equipment to source
	TotalLength float64     `json:"total_wire_length_meters"`
	VoltageDrop float64     `json:"voltage_drop_percent"`
}

type PowerNode struct {
	ID       string  `json:"id"`
	Type     string  `json:"type"`
	Voltage  float64 `json:"voltage"`
	Amperage float64 `json:"amperage,omitempty"`
}