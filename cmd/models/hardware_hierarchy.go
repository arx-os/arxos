package models

import (
	"fmt"
	"strings"
)

// HardwareHierarchy extends ArxObject IDs into hardware level
// This enables full traceability from building → system → device → PCB → component → pin

// Example Hardware Hierarchies:

// Smart Outlet Example:
// building_id/electrical/outlet/f1_r101_north_1                    (Device level)
// building_id/electrical/outlet/f1_r101_north_1/hardware/pcb/main  (PCB level)
// building_id/electrical/outlet/f1_r101_north_1/hardware/pcb/main/component/u1 (Component)
// building_id/electrical/outlet/f1_r101_north_1/hardware/pcb/main/component/u1/pin/1 (Pin)
// building_id/electrical/outlet/f1_r101_north_1/hardware/pcb/main/trace/power_5v (Trace)
// building_id/electrical/outlet/f1_r101_north_1/hardware/wire/line (Line wire)
// building_id/electrical/outlet/f1_r101_north_1/hardware/wire/neutral (Neutral wire)
// building_id/electrical/outlet/f1_r101_north_1/hardware/wire/ground (Ground wire)

// Electrical Panel Breaker Example:
// building_id/electrical/panel/mdf/breaker/12                      (Breaker device)
// building_id/electrical/panel/mdf/breaker/12/hardware/contact/main (Physical contact)
// building_id/electrical/panel/mdf/breaker/12/hardware/trip/magnetic (Trip mechanism)
// building_id/electrical/panel/mdf/breaker/12/hardware/trip/thermal
// building_id/electrical/panel/mdf/breaker/12/hardware/terminal/line
// building_id/electrical/panel/mdf/breaker/12/hardware/terminal/load

// Sensor Example:
// building_id/sensor/temp_f1_r101                                  (Sensor device)
// building_id/sensor/temp_f1_r101/hardware/pcb/sensor_board       (PCB)
// building_id/sensor/temp_f1_r101/hardware/pcb/sensor_board/component/u1 (MCU)
// building_id/sensor/temp_f1_r101/hardware/pcb/sensor_board/component/u2 (Temp sensor IC)
// building_id/sensor/temp_f1_r101/hardware/pcb/sensor_board/component/j1 (Connector)
// building_id/sensor/temp_f1_r101/hardware/pcb/sensor_board/antenna/chip (Antenna)
// building_id/sensor/temp_f1_r101/hardware/enclosure/main         (Physical enclosure)
// building_id/sensor/temp_f1_r101/hardware/battery/cr2032         (Battery)

// HVAC Controller Example:
// building_id/hvac/controller/ahu_1                               (Controller device)
// building_id/hvac/controller/ahu_1/hardware/pcb/controller       (Controller PCB)
// building_id/hvac/controller/ahu_1/hardware/pcb/io_board        (I/O expansion PCB)
// building_id/hvac/controller/ahu_1/hardware/terminal_block/inputs
// building_id/hvac/controller/ahu_1/hardware/terminal_block/outputs
// building_id/hvac/controller/ahu_1/hardware/din_rail/mounting

// HardwareIDBuilder extends IDBuilder for hardware components
type HardwareIDBuilder struct {
	*IDBuilder
}

// NewHardwareIDBuilder creates a hardware ID builder from device ID
func NewHardwareIDBuilder(deviceID string) *HardwareIDBuilder {
	return &HardwareIDBuilder{
		IDBuilder: &IDBuilder{
			parts: strings.Split(deviceID, "/"),
		},
	}
}

// Hardware adds the hardware namespace
func (b *HardwareIDBuilder) Hardware() *HardwareIDBuilder {
	b.Add("hardware")
	return b
}

// PCB adds a PCB level
func (b *HardwareIDBuilder) PCB(boardName string) *HardwareIDBuilder {
	b.Add("pcb").Add(boardName)
	return b
}

// Component adds a component
func (b *HardwareIDBuilder) Component(designator string) *HardwareIDBuilder {
	b.Add("component").Add(strings.ToLower(designator))
	return b
}

// Pin adds a pin
func (b *HardwareIDBuilder) Pin(pinNumber string) *HardwareIDBuilder {
	b.Add("pin").Add(pinNumber)
	return b
}

// Trace adds a trace
func (b *HardwareIDBuilder) Trace(netName string) *HardwareIDBuilder {
	b.Add("trace").Add(strings.ToLower(strings.ReplaceAll(netName, " ", "_")))
	return b
}

// Wire adds a wire
func (b *HardwareIDBuilder) Wire(wireType string) *HardwareIDBuilder {
	b.Add("wire").Add(wireType)
	return b
}

// Terminal adds a terminal
func (b *HardwareIDBuilder) Terminal(terminalName string) *HardwareIDBuilder {
	b.Add("terminal").Add(terminalName)
	return b
}

// HardwareTraceability provides full path from building to component pin
type HardwareTraceability struct {
	BuildingID   string   `json:"building_id"`
	System       string   `json:"system"`        // electrical, hvac, etc.
	DevicePath   string   `json:"device_path"`   // Path to device
	DeviceID     string   `json:"device_id"`     // Full device ArxObject ID
	HardwarePath []string `json:"hardware_path"` // Path within hardware
	PinSignal    string   `json:"pin_signal,omitempty"`
	NetName      string   `json:"net_name,omitempty"`
	WirePath     []string `json:"wire_path,omitempty"` // Physical wire routing
}

// GetHardwareTraceability returns full traceability for a hardware component
func GetHardwareTraceability(componentID string) (*HardwareTraceability, error) {
	parts := strings.Split(componentID, "/")
	
	// Find where hardware starts
	hwIndex := -1
	for i, part := range parts {
		if part == "hardware" {
			hwIndex = i
			break
		}
	}
	
	if hwIndex == -1 {
		return nil, fmt.Errorf("not a hardware component ID")
	}
	
	trace := &HardwareTraceability{
		BuildingID:   parts[0],
		DevicePath:   strings.Join(parts[:hwIndex], "/"),
		DeviceID:     strings.Join(parts[:hwIndex], "/"),
		HardwarePath: parts[hwIndex:],
	}
	
	// Extract system from device path
	if len(parts) > 1 {
		trace.System = parts[1]
	}
	
	return trace, nil
}

// WireTraceability tracks a wire from source to destination
type WireTraceability struct {
	WireID       string   `json:"wire_id"`
	StartDevice  string   `json:"start_device"`  // Device ArxObject ID
	StartPin     string   `json:"start_pin"`     // Pin or terminal
	EndDevice    string   `json:"end_device"`    
	EndPin       string   `json:"end_pin"`
	PathDevices  []string `json:"path_devices"`  // Intermediate junction boxes, etc.
	WireType     string   `json:"wire_type"`     // hot, neutral, ground, signal
	Gauge        string   `json:"gauge"`
	Color        string   `json:"color"`
	Length       float64  `json:"length_meters"`
	InConduit    string   `json:"in_conduit,omitempty"`    // Conduit ArxObject ID
	InHarness    string   `json:"in_harness,omitempty"`    // Harness ArxObject ID
}

// CircuitPath tracks complete electrical path including hardware
type CircuitPath struct {
	CircuitID    string              `json:"circuit_id"`
	BreakerID    string              `json:"breaker_id"`
	Voltage      float64             `json:"voltage"`
	Current      float64             `json:"current_amps"`
	
	// Path from breaker to device
	PathSegments []CircuitSegment    `json:"path_segments"`
	
	// All devices on circuit
	Devices      []string            `json:"devices"`
	
	// Wire details
	Wires        []WireTraceability  `json:"wires"`
}

// CircuitSegment represents one segment of a circuit path
type CircuitSegment struct {
	FromDevice   string  `json:"from_device"`
	ToDevice     string  `json:"to_device"`
	WireGauge    string  `json:"wire_gauge"`
	WireLength   float64 `json:"wire_length_meters"`
	VoltDrop     float64 `json:"voltage_drop"`
	InConduit    string  `json:"in_conduit,omitempty"`
}

// ManufacturingBOM generates Bill of Materials for hardware
type ManufacturingBOM struct {
	ProjectID    string         `json:"project_id"`
	DeviceID     string         `json:"device_id"`
	Revision     string         `json:"revision"`
	Date         string         `json:"date"`
	
	// PCB Components
	Components   []BOMLine      `json:"components"`
	
	// Mechanical parts
	Mechanical   []BOMLine      `json:"mechanical"`
	
	// Wires and cables
	Wiring       []BOMLine      `json:"wiring"`
	
	// Assembly materials
	Assembly     []BOMLine      `json:"assembly"`
	
	// Totals
	TotalParts   int            `json:"total_parts"`
	TotalCost    float64        `json:"total_cost"`
	LeadTime     int            `json:"lead_time_days"`
}

// BOMLine represents one line in a BOM
type BOMLine struct {
	LineNo       int      `json:"line_no"`
	Designators  []string `json:"designators"`      // R1,R2,R3
	Quantity     int      `json:"quantity"`
	Description  string   `json:"description"`
	Value        string   `json:"value,omitempty"`
	Package      string   `json:"package,omitempty"`
	Manufacturer string   `json:"manufacturer,omitempty"`
	MfgPartNo    string   `json:"mfg_part_no,omitempty"`
	Supplier     string   `json:"supplier,omitempty"`
	SupPartNo    string   `json:"sup_part_no,omitempty"`
	UnitCost     float64  `json:"unit_cost"`
	ExtCost      float64  `json:"ext_cost"`
	LeadTime     int      `json:"lead_time_days,omitempty"`
	Notes        string   `json:"notes,omitempty"`
}

// GenerateBOM creates a BOM from hardware components
func GenerateBOM(deviceID string, components []*HardwareComponent) *ManufacturingBOM {
	bom := &ManufacturingBOM{
		DeviceID:   deviceID,
		Date:       "2024-08-26",
		Components: []BOMLine{},
	}
	
	// Group components by value and package
	groups := make(map[string]*BOMLine)
	
	for _, comp := range components {
		// Create key from type, value, package
		key := fmt.Sprintf("%s_%s_%s", 
			comp.Properties["component_type"],
			comp.Properties["value"],
			comp.Properties["package"])
		
		if line, exists := groups[key]; exists {
			line.Designators = append(line.Designators, comp.Properties["designator"].(string))
			line.Quantity++
		} else {
			groups[key] = &BOMLine{
				Designators: []string{comp.Properties["designator"].(string)},
				Quantity:    1,
				Description: comp.Properties["component_type"].(string),
				Value:       comp.Properties["value"].(string),
				Package:     comp.Properties["package"].(string),
			}
		}
	}
	
	// Convert to BOM lines
	lineNo := 1
	for _, line := range groups {
		line.LineNo = lineNo
		bom.Components = append(bom.Components, *line)
		bom.TotalParts += line.Quantity
		lineNo++
	}
	
	return bom
}

// HardwareTestPoint defines test points for hardware validation
type HardwareTestPoint struct {
	TestID       string   `json:"test_id"`
	DeviceID     string   `json:"device_id"`
	TestType     string   `json:"test_type"`      // continuity, voltage, current, signal
	TestPoint    string   `json:"test_point"`     // Component:Pin or TP1
	ExpectedValue string  `json:"expected_value"`
	Tolerance    string   `json:"tolerance"`
	Units        string   `json:"units"`
	Required     bool     `json:"required"`
}

// Example test points for a smart outlet
var SmartOutletTestPoints = []HardwareTestPoint{
	{
		TestID:       "line_voltage",
		TestType:     "voltage",
		TestPoint:    "J1:1", // Line input
		ExpectedValue: "120",
		Tolerance:    "±10%",
		Units:        "VAC",
		Required:     true,
	},
	{
		TestID:       "5v_rail",
		TestType:     "voltage", 
		TestPoint:    "TP1",
		ExpectedValue: "5.0",
		Tolerance:    "±5%",
		Units:        "VDC",
		Required:     true,
	},
	{
		TestID:       "mcu_clock",
		TestType:     "signal",
		TestPoint:    "U1:9", // MCU clock pin
		ExpectedValue: "16MHz",
		Tolerance:    "±1%",
		Units:        "Hz",
		Required:     true,
	},
	{
		TestID:       "gfci_test",
		TestType:     "functional",
		TestPoint:    "TEST_BUTTON",
		ExpectedValue: "TRIP",
		Required:     true,
	},
}

// OpenHardwareLibrary provides templates for open-source hardware
type OpenHardwareLibrary struct {
	DeviceType   string                 `json:"device_type"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	License      string                 `json:"license"`      // MIT, GPL, CERN OHL
	Repository   string                 `json:"repository"`   // GitHub URL
	Schematic    string                 `json:"schematic_url"`
	PCBLayout    string                 `json:"pcb_layout_url"`
	BOM          *ManufacturingBOM      `json:"bom"`
	TestPoints   []HardwareTestPoint    `json:"test_points"`
	Firmware     string                 `json:"firmware_url,omitempty"`
	Documentation string                `json:"docs_url"`
}

// Community hardware designs for the Open Hardware Revolution
var OpenHardwareDesigns = map[string]OpenHardwareLibrary{
	"arxos_smart_outlet": {
		DeviceType:  "outlet",
		Name:        "ArxOS Smart Outlet v1.0",
		Description: "WiFi-enabled outlet with power monitoring and GFCI",
		License:     "CERN-OHL-S-2.0",
		Repository:  "github.com/arxos/hardware/smart-outlet",
	},
	"arxos_sensor_node": {
		DeviceType:  "sensor",
		Name:        "ArxOS Universal Sensor Node",
		Description: "Battery-powered wireless sensor with multiple inputs",
		License:     "MIT",
		Repository:  "github.com/arxos/hardware/sensor-node",
	},
	"arxos_breaker_monitor": {
		DeviceType:  "breaker_addon",
		Name:        "ArxOS Breaker Monitor Clip-On",
		Description: "Non-invasive current monitoring for standard breakers",
		License:     "CERN-OHL-W-2.0",
		Repository:  "github.com/arxos/hardware/breaker-monitor",
	},
}