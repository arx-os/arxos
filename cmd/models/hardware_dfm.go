package models

// HardwareLevel represents the granularity of hardware design
type HardwareLevel string

const (
	LevelDevice    HardwareLevel = "device"     // Complete device (outlet, sensor, switch)
	LevelPCB       HardwareLevel = "pcb"        // Printed Circuit Board
	LevelComponent HardwareLevel = "component"  // Individual components (resistors, chips)
	LevelTrace     HardwareLevel = "trace"      // PCB traces and routing
	LevelSilicon   HardwareLevel = "silicon"    // Chip design level
)

// HardwareProperties for Design for Manufacturing (DfM)
type HardwareProperties struct {
	// PCB Properties
	PCBLayers           int      `json:"pcb_layers,omitempty"`           // 1, 2, 4, 6, etc.
	PCBMaterial         string   `json:"pcb_material,omitempty"`         // FR4, Rogers, Aluminum
	PCBThickness        float64  `json:"pcb_thickness_mm,omitempty"`     
	PCBDimensions       []float64 `json:"pcb_dimensions_mm,omitempty"`   // [length, width]
	CopperWeight        string   `json:"copper_weight,omitempty"`        // 1oz, 2oz
	SolderMask          string   `json:"solder_mask_color,omitempty"`    // green, black, blue
	Silkscreen          string   `json:"silkscreen_color,omitempty"`     // white, black
	SurfaceFinish       string   `json:"surface_finish,omitempty"`       // HASL, ENIG, OSP
	MinTraceWidth       float64  `json:"min_trace_width_mm,omitempty"`
	MinViaSize          float64  `json:"min_via_size_mm,omitempty"`
	MinDrillSize        float64  `json:"min_drill_size_mm,omitempty"`
	
	// Component Properties
	ComponentType       string   `json:"component_type,omitempty"`       // resistor, capacitor, IC, connector
	Package             string   `json:"package,omitempty"`              // 0603, 0805, SOIC-8, DIP-14
	Value               string   `json:"value,omitempty"`                // 10k, 100nF, etc.
	Tolerance           string   `json:"tolerance,omitempty"`            // 1%, 5%, 10%
	PowerRating         float64  `json:"power_rating_watts,omitempty"`
	VoltageRating       float64  `json:"voltage_rating,omitempty"`
	TemperatureRange    []int    `json:"temperature_range_c,omitempty"`  // [-40, 85]
	Manufacturer        string   `json:"manufacturer,omitempty"`
	ManufacturerPartNo  string   `json:"manufacturer_part_no,omitempty"`
	SupplierPartNo      string   `json:"supplier_part_no,omitempty"`
	DatasheetURL        string   `json:"datasheet_url,omitempty"`
	
	// Connector/Terminal Properties
	ConnectorType       string   `json:"connector_type,omitempty"`       // JST, Molex, Phoenix
	PinCount           int      `json:"pin_count,omitempty"`
	PinPitch           float64  `json:"pin_pitch_mm,omitempty"`         // 2.54mm, 1.27mm
	ConnectorCurrentRating float64  `json:"connector_current_rating_amps,omitempty"`
	ConnectorVoltageRating float64  `json:"connector_voltage_rating_volts,omitempty"`
	AcceptedWireGauge   []string `json:"accepted_wire_gauge_awg,omitempty"`       // Compatible wire sizes
	TerminationType    string   `json:"termination_type,omitempty"`     // screw, spring, crimp
	
	// Wire/Cable Properties
	WireType           string   `json:"wire_type,omitempty"`            // solid, stranded
	WireGauge          string   `json:"wire_gauge,omitempty"`           // 12 AWG, 14 AWG
	StrandCount        int      `json:"strand_count,omitempty"`
	InsulationType     string   `json:"insulation_type,omitempty"`      // PVC, THHN, Teflon
	InsulationColor    string   `json:"insulation_color,omitempty"`
	WireTemperatureRating  int      `json:"wire_temperature_rating_c,omitempty"`
	WireVoltageRating      int      `json:"wire_voltage_rating_volts,omitempty"`
	ConductorMaterial  string   `json:"conductor_material,omitempty"`   // copper, aluminum
	ShieldType         string   `json:"shield_type,omitempty"`          // none, foil, braid
	
	// Assembly Properties
	AssemblyMethod     string   `json:"assembly_method,omitempty"`      // SMT, THT, mixed
	ReflowProfile      string   `json:"reflow_profile,omitempty"`       // lead-free, leaded
	PickAndPlaceFile   string   `json:"pick_place_file,omitempty"`      // File path/URL
	GerberFiles        []string `json:"gerber_files,omitempty"`         // List of Gerber files
	SchematicFile      string   `json:"schematic_file,omitempty"`
	LayoutFile         string   `json:"layout_file,omitempty"`
	ThreeDModel        string   `json:"3d_model_file,omitempty"`        // STEP file
	
	// Testing/Certification
	TestPoints         []string `json:"test_points,omitempty"`          // TP1, TP2, etc.
	RequiredTests      []string `json:"required_tests,omitempty"`       // continuity, hi-pot, functional
	Certifications     []string `json:"certifications,omitempty"`       // UL, CE, FCC
	ComplianceStandards []string `json:"compliance_standards,omitempty"` // RoHS, REACH
	
	// Manufacturing
	Quantity           int      `json:"quantity,omitempty"`
	LeadTime          string   `json:"lead_time_days,omitempty"`
	CostPerUnit       float64  `json:"cost_per_unit,omitempty"`
	PreferredFab      string   `json:"preferred_fab,omitempty"`        // JLCPCB, PCBWay, etc.
	AssemblyHouse     string   `json:"assembly_house,omitempty"`
}

// HardwareComponent represents a single component in a hardware design
type HardwareComponent struct {
	ArxObjectV2
	
	// Component-specific
	Designator        string   `json:"designator"`        // R1, C1, U1, etc.
	SchematicSymbol   string   `json:"schematic_symbol"`
	FootprintName     string   `json:"footprint_name"`
	Position          PCBPosition `json:"pcb_position"`
	Rotation          float64  `json:"rotation_degrees"`
	Side              string   `json:"side"`              // top, bottom
	
	// Electrical connections
	Pins              []PinConnection `json:"pins"`
	Nets              []string        `json:"nets"`          // Connected net names
}

// PCBPosition represents position on a PCB
type PCBPosition struct {
	X     float64 `json:"x_mm"`
	Y     float64 `json:"y_mm"`
	Layer string  `json:"layer"` // top, bottom
}

// PinConnection represents a component pin connection
type PinConnection struct {
	PinNumber   string  `json:"pin_number"`
	PinName     string  `json:"pin_name"`
	NetName     string  `json:"net_name"`
	ElectricalType string `json:"electrical_type"` // input, output, power, ground, passive
}

// PCBTrace represents a trace on a PCB
type PCBTrace struct {
	NetName      string      `json:"net_name"`
	Width        float64     `json:"width_mm"`
	Layer        string      `json:"layer"`
	StartPoint   PCBPosition `json:"start_point"`
	EndPoint     PCBPosition `json:"end_point"`
	Vias         []PCBVia    `json:"vias,omitempty"`
	Length       float64     `json:"length_mm"`
	Impedance    float64     `json:"impedance_ohms,omitempty"`
}

// PCBVia represents a via on a PCB
type PCBVia struct {
	Position     PCBPosition `json:"position"`
	Diameter     float64     `json:"diameter_mm"`
	DrillSize    float64     `json:"drill_size_mm"`
	Type         string      `json:"type"` // through, blind, buried
	StartLayer   string      `json:"start_layer"`
	EndLayer     string      `json:"end_layer"`
}

// WireHarness represents a collection of wires bundled together
type WireHarness struct {
	ArxObjectV2
	
	// Harness properties
	HarnessID    string       `json:"harness_id"`
	Wires        []WireRun    `json:"wires"`
	Connectors   []Connector  `json:"connectors"`
	TotalLength  float64      `json:"total_length_mm"`
	BundleDiameter float64    `json:"bundle_diameter_mm"`
	Weight       float64      `json:"weight_grams"`
	
	// Routing
	RoutePath    []RoutePoint `json:"route_path"`
	BendRadius   float64      `json:"min_bend_radius_mm"`
	Supports     []string     `json:"support_points"` // ArxObject IDs of support points
}

// WireRun represents a single wire in a run
type WireRun struct {
	WireID       string       `json:"wire_id"`
	FromPin      string       `json:"from_pin"`      // Component:Pin format
	ToPin        string       `json:"to_pin"`
	Color        string       `json:"color"`
	Gauge        string       `json:"gauge"`
	Length       float64      `json:"length_mm"`
	Signal       string       `json:"signal_name,omitempty"`
}

// Connector represents a hardware connector
type Connector struct {
	ConnectorID  string       `json:"connector_id"`
	Type         string       `json:"type"`
	Position     string       `json:"position"`      // ArxObject ID where mounted
	Orientation  string       `json:"orientation"`   // Direction facing
	PinMap       map[string]string `json:"pin_map"` // Pin number -> signal name
}

// RoutePoint represents a point in a wire routing path
type RoutePoint struct {
	X            float64 `json:"x"`
	Y            float64 `json:"y"`
	Z            float64 `json:"z"`
	FixtureType  string  `json:"fixture_type,omitempty"` // tie, clip, conduit
}

// CircuitBoard represents a complete PCB assembly
type CircuitBoard struct {
	ArxObjectV2
	
	// Board info
	BoardName    string     `json:"board_name"`
	Revision     string     `json:"revision"`
	BoardType    string     `json:"board_type"` // controller, power, sensor, interface
	
	// Design files
	SchematicURL string     `json:"schematic_url"`
	LayoutURL    string     `json:"layout_url"`
	GerberURL    string     `json:"gerber_url"`
	BOMUrl       string     `json:"bom_url"`
	
	// Components
	Components   []HardwareComponent `json:"components"`
	Traces       []PCBTrace         `json:"traces,omitempty"`
	
	// Power
	PowerNets    []PowerNet         `json:"power_nets"`
	GroundPlanes []GroundPlane      `json:"ground_planes"`
	
	// Interfaces
	Connectors   []Connector        `json:"connectors"`
	TestPoints   []TestPoint        `json:"test_points"`
}

// PowerNet represents a power distribution network on PCB
type PowerNet struct {
	NetName      string  `json:"net_name"`      // +5V, +3.3V, +12V
	Voltage      float64 `json:"voltage"`
	CurrentMax   float64 `json:"current_max_amps"`
	TraceWidth   float64 `json:"trace_width_mm"`
	PlaneLayer   string  `json:"plane_layer,omitempty"`
}

// GroundPlane represents a ground plane on PCB
type GroundPlane struct {
	Layer        string    `json:"layer"`
	NetName      string    `json:"net_name"` // GND, AGND, DGND
	Area         float64   `json:"area_mm2"`
	Cutouts      []PCBArea `json:"cutouts,omitempty"`
}

// PCBArea represents an area on PCB
type PCBArea struct {
	X1 float64 `json:"x1_mm"`
	Y1 float64 `json:"y1_mm"`
	X2 float64 `json:"x2_mm"`
	Y2 float64 `json:"y2_mm"`
}

// TestPoint represents a test point on PCB
type TestPoint struct {
	Designator   string      `json:"designator"` // TP1, TP2
	NetName      string      `json:"net_name"`
	Position     PCBPosition `json:"position"`
	Diameter     float64     `json:"diameter_mm"`
	Purpose      string      `json:"purpose"`
}

// HardwareNamespace extends the ArxObject naming for hardware
// Example paths:
// building_id/electrical/panel/mdf/breaker/1/hardware/pcb/main
// building_id/electrical/panel/mdf/breaker/1/hardware/pcb/main/component/r1
// building_id/electrical/outlet/f1_r101_1/hardware/pcb/control
// building_id/electrical/outlet/f1_r101_1/hardware/wire_harness/main
// building_id/hvac/controller/ahu_1/hardware/pcb/controller
// building_id/sensor/temp_f1_r101/hardware/pcb/sensor_board

// StandardCircuits provides common circuit designs
var StandardCircuits = map[string]CircuitTemplate{
	"outlet_gfci": {
		Name: "GFCI Outlet Circuit",
		Components: []ComponentTemplate{
			{Designator: "U1", Type: "IC", Value: "RV4141", Package: "SOIC-8", Description: "GFCI Controller"},
			{Designator: "T1", Type: "transformer", Value: "1:1000", Package: "CUSTOM", Description: "Current Sense"},
			{Designator: "K1", Type: "relay", Value: "30A", Package: "CUSTOM", Description: "Trip Relay"},
			{Designator: "R1", Type: "resistor", Value: "10k", Package: "0805"},
			{Designator: "C1", Type: "capacitor", Value: "100nF", Package: "0805"},
		},
	},
	"smart_switch": {
		Name: "Smart Light Switch",
		Components: []ComponentTemplate{
			{Designator: "U1", Type: "IC", Value: "ESP32", Package: "QFN-48", Description: "WiFi Controller"},
			{Designator: "U2", Type: "IC", Value: "ACS712", Package: "SOIC-8", Description: "Current Sensor"},
			{Designator: "Q1", Type: "triac", Value: "BT136", Package: "TO-220"},
			{Designator: "U3", Type: "IC", Value: "HLK-PM01", Package: "MODULE", Description: "AC-DC Power"},
		},
	},
	"sensor_node": {
		Name: "Wireless Sensor Node",
		Components: []ComponentTemplate{
			{Designator: "U1", Type: "IC", Value: "STM32L0", Package: "QFN-32", Description: "MCU"},
			{Designator: "U2", Type: "IC", Value: "BME280", Package: "LGA-8", Description: "Temp/Humidity"},
			{Designator: "U3", Type: "IC", Value: "nRF24L01", Package: "MODULE", Description: "Radio"},
			{Designator: "U4", Type: "IC", Value: "MCP1700", Package: "SOT-23", Description: "LDO"},
		},
	},
}

// ComponentTemplate for standard components
type ComponentTemplate struct {
	Designator  string
	Type        string
	Value       string
	Package     string
	Description string
}

// CircuitTemplate for standard circuit blocks
type CircuitTemplate struct {
	Name       string
	Components []ComponentTemplate
}

// DFMRules defines manufacturing constraints
type DFMRules struct {
	// PCB Rules
	MinTraceWidth      float64 `json:"min_trace_width_mm"`
	MinTraceSpacing    float64 `json:"min_trace_spacing_mm"`
	MinViaSize         float64 `json:"min_via_size_mm"`
	MinViaDrill        float64 `json:"min_via_drill_mm"`
	MinAnnularRing     float64 `json:"min_annular_ring_mm"`
	MinSilkscreenWidth float64 `json:"min_silkscreen_width_mm"`
	MinPadSize         float64 `json:"min_pad_size_mm"`
	MinHoleDiameter    float64 `json:"min_hole_diameter_mm"`
	
	// Assembly Rules
	MinComponentSpacing float64 `json:"min_component_spacing_mm"`
	MinCourtyardSpace  float64 `json:"min_courtyard_space_mm"`
	AllowBottomSMT     bool    `json:"allow_bottom_smt"`
	
	// Wire Rules
	MinBendRadius      float64 `json:"min_bend_radius_factor"` // Multiple of wire diameter
	MaxWireLength      float64 `json:"max_wire_length_mm"`
	MinWireGauge       string  `json:"min_wire_gauge"`
	
	// Compliance
	RequireRoHS        bool    `json:"require_rohs"`
	RequireUL          bool    `json:"require_ul"`
	RequireCE          bool    `json:"require_ce"`
}

// GetDFMRules returns manufacturing rules for a given fab/standard
func GetDFMRules(standard string) DFMRules {
	// Common fab house rules
	standards := map[string]DFMRules{
		"jlcpcb_standard": {
			MinTraceWidth:     0.127,  // 5 mil
			MinTraceSpacing:   0.127,
			MinViaSize:        0.5,
			MinViaDrill:        0.3,
			MinAnnularRing:    0.1,
			MinSilkscreenWidth: 0.15,
			MinPadSize:        0.25,
			MinHoleDiameter:   0.3,
			MinComponentSpacing: 0.2,
			MinCourtyardSpace: 0.5,
			AllowBottomSMT:    true,
			RequireRoHS:       true,
		},
		"ul_electrical": {
			MinWireGauge:      "14 AWG",
			MinBendRadius:     5.0,
			MaxWireLength:     3000, // 3 meters
			RequireUL:         true,
		},
	}
	
	if rules, ok := standards[standard]; ok {
		return rules
	}
	
	// Return default rules
	return standards["jlcpcb_standard"]
}