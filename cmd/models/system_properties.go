package models

// SystemProperties defines standard properties for each system type
// These are templates/schemas - actual values go in ArxObject.Properties map

// ElectricalProperties for electrical components
type ElectricalProperties struct {
	// Panels
	PanelType     string  `json:"panel_type,omitempty"`     // mdf, idf, sub
	Voltage       float64 `json:"voltage,omitempty"`        // 120, 208, 240, 480
	Phase         int     `json:"phase,omitempty"`          // 1 or 3
	MainBreakerAmps int   `json:"main_breaker_amps,omitempty"`
	NumberOfSpaces int    `json:"number_of_spaces,omitempty"`
	
	// Breakers
	BreakerAmps   int    `json:"breaker_amps,omitempty"`
	BreakerPoles  int    `json:"breaker_poles,omitempty"`
	CircuitNumber string `json:"circuit_number,omitempty"`
	CircuitName   string `json:"circuit_name,omitempty"`
	
	// Wiring
	WireSize     string `json:"wire_size,omitempty"`     // 12 AWG, 10 AWG, etc.
	WireType     string `json:"wire_type,omitempty"`     // THHN, NM, MC
	ConduitType  string `json:"conduit_type,omitempty"`  // EMT, rigid, PVC
	ConduitSize  string `json:"conduit_size,omitempty"`  // 1/2", 3/4", 1"
	WireLength   float64 `json:"wire_length,omitempty"`  // in feet
	
	// Devices
	DeviceType   string `json:"device_type,omitempty"`   // outlet, switch, junction
	NEMAConfig   string `json:"nema_config,omitempty"`   // 5-15R, 5-20R, L14-30R
	SwitchType   string `json:"switch_type,omitempty"`   // single_pole, 3_way, 4_way, dimmer
	
	// Load Information
	ConnectedLoad float64 `json:"connected_load,omitempty"` // in watts
	DemandFactor  float64 `json:"demand_factor,omitempty"`  // 0.0 to 1.0
	PowerFactor   float64 `json:"power_factor,omitempty"`   // 0.0 to 1.0
	
	// Equipment Details
	Make         string `json:"make,omitempty"`
	Model        string `json:"model,omitempty"`
	SerialNumber string `json:"serial_number,omitempty"`
	Rating       string `json:"rating,omitempty"`
}

// HVACProperties for HVAC components
type HVACProperties struct {
	// Capacity
	CoolingCapacityTons float64 `json:"cooling_capacity_tons,omitempty"`
	HeatingCapacityKW   float64 `json:"heating_capacity_kw,omitempty"`
	CoolingCapacityBTU  float64 `json:"cooling_capacity_btu,omitempty"`
	HeatingCapacityBTU  float64 `json:"heating_capacity_btu,omitempty"`
	
	// Airflow
	MaxCFM        float64 `json:"max_cfm,omitempty"`
	MinCFM        float64 `json:"min_cfm,omitempty"`
	DesignCFM     float64 `json:"design_cfm,omitempty"`
	
	// Equipment
	EquipmentType string  `json:"equipment_type,omitempty"` // ahu, rtu, vav, fcu
	RefrigerantType string `json:"refrigerant_type,omitempty"` // R410A, R134a
	CompressorType string  `json:"compressor_type,omitempty"` // scroll, reciprocating
	
	// Coils
	CoilType     string `json:"coil_type,omitempty"`     // cooling, heating, reheat
	CoilRows     int    `json:"coil_rows,omitempty"`
	CoilFinsPer  int    `json:"coil_fins_per_inch,omitempty"`
	
	// Fans
	FanType      string  `json:"fan_type,omitempty"`      // centrifugal, axial
	FanHP        float64 `json:"fan_hp,omitempty"`
	FanRPM       int     `json:"fan_rpm,omitempty"`
	
	// VAV Specific
	BoxType      string  `json:"box_type,omitempty"`      // single_duct, dual_duct, fan_powered
	HasReheat    bool    `json:"has_reheat,omitempty"`
	ReheatType   string  `json:"reheat_type,omitempty"`   // electric, hot_water
	
	// Filters
	FilterType   string `json:"filter_type,omitempty"`   // MERV rating
	FilterSize   string `json:"filter_size,omitempty"`   // 24x24x2
	
	// Controls
	ControlType  string `json:"control_type,omitempty"`  // pneumatic, DDC, standalone
	HasVFD       bool   `json:"has_vfd,omitempty"`
	
	// Equipment Details
	Make         string `json:"make,omitempty"`
	Model        string `json:"model,omitempty"`
	SerialNumber string `json:"serial_number,omitempty"`
}

// PlumbingProperties for plumbing components
type PlumbingProperties struct {
	// Pipes
	PipeType     string  `json:"pipe_type,omitempty"`     // copper, PVC, PEX, cast_iron
	PipeSize     string  `json:"pipe_size,omitempty"`     // 1/2", 3/4", 1", 2"
	PipeSchedule string  `json:"pipe_schedule,omitempty"` // 40, 80
	
	// Valves
	ValveType    string  `json:"valve_type,omitempty"`    // ball, gate, globe, check
	ValveSize    string  `json:"valve_size,omitempty"`    // matches pipe size
	NormallyOpen bool    `json:"normally_open,omitempty"`
	
	// Flow
	FlowRateGPM  float64 `json:"flow_rate_gpm,omitempty"`
	PressurePSI  float64 `json:"pressure_psi,omitempty"`
	Temperature  float64 `json:"temperature_f,omitempty"`
	
	// Fixtures
	FixtureType  string  `json:"fixture_type,omitempty"`  // sink, toilet, urinal
	FixtureUnits float64 `json:"fixture_units,omitempty"` // DFU or WFU
	FlowRate     float64 `json:"flow_rate,omitempty"`     // GPM or GPF
	
	// Water Heaters
	HeaterType   string  `json:"heater_type,omitempty"`   // tank, tankless
	CapacityGal  float64 `json:"capacity_gal,omitempty"`
	RecoveryRate float64 `json:"recovery_rate,omitempty"` // GPH
	InputBTU     float64 `json:"input_btu,omitempty"`
	
	// Pumps
	PumpType     string  `json:"pump_type,omitempty"`     // centrifugal, positive_displacement
	PumpHP       float64 `json:"pump_hp,omitempty"`
	HeadFeet     float64 `json:"head_feet,omitempty"`
	
	// Equipment Details
	Make         string `json:"make,omitempty"`
	Model        string `json:"model,omitempty"`
	SerialNumber string `json:"serial_number,omitempty"`
}

// FireSafetyProperties for fire alarm and sprinkler systems
type FireSafetyProperties struct {
	// Fire Alarm
	DeviceType      string `json:"device_type,omitempty"`      // smoke, heat, pull, horn_strobe
	DetectorType    string `json:"detector_type,omitempty"`    // photoelectric, ionization
	CoverageArea    float64 `json:"coverage_area_sqft,omitempty"`
	SoundLevel      int    `json:"sound_level_db,omitempty"`
	
	// Sprinkler
	HeadType        string `json:"head_type,omitempty"`        // pendant, upright, sidewall
	Temperature     int    `json:"temperature_rating,omitempty"` // 135, 155, 175, 200
	KFactor         float64 `json:"k_factor,omitempty"`
	CoveragePattern string `json:"coverage_pattern,omitempty"` // standard, extended
	
	// Zones
	ZoneNumber      string `json:"zone_number,omitempty"`
	ZoneType        string `json:"zone_type,omitempty"`        // wet, dry, preaction
	
	// Equipment Details
	Make         string `json:"make,omitempty"`
	Model        string `json:"model,omitempty"`
	SerialNumber string `json:"serial_number,omitempty"`
}

// BASProperties for building automation components
type BASProperties struct {
	// Controllers
	ControllerType  string `json:"controller_type,omitempty"`  // main, floor, equipment
	Protocol        string `json:"protocol,omitempty"`        // BACnet, Modbus, LON
	IPAddress       string `json:"ip_address,omitempty"`
	MACAddress      string `json:"mac_address,omitempty"`
	
	// Sensors
	SensorType      string  `json:"sensor_type,omitempty"`      // temp, humidity, CO2, occupancy
	Range           string  `json:"range,omitempty"`
	Accuracy        float64 `json:"accuracy,omitempty"`
	Units           string  `json:"units,omitempty"`
	
	// Actuators
	ActuatorType    string  `json:"actuator_type,omitempty"`    // valve, damper
	TravelTime      int     `json:"travel_time_seconds,omitempty"`
	FailPosition    string  `json:"fail_position,omitempty"`    // open, closed, last
	
	// Points
	PointType       string  `json:"point_type,omitempty"`       // AI, AO, DI, DO, AV, BV
	PointAddress    string  `json:"point_address,omitempty"`
	
	// Equipment Details
	Make         string `json:"make,omitempty"`
	Model        string `json:"model,omitempty"`
	SerialNumber string `json:"serial_number,omitempty"`
	Firmware     string `json:"firmware_version,omitempty"`
}

// PropertySchema defines expected properties for validation
type PropertySchema struct {
	Required []string               `json:"required"`
	Optional []string               `json:"optional"`
	Types    map[string]string      `json:"types"`    // property name -> type
	Ranges   map[string]interface{} `json:"ranges"`   // property name -> valid range
	Values   map[string][]string    `json:"values"`   // property name -> valid values
}

// SystemSchemas defines property schemas for each system/component combination
var SystemSchemas = map[string]map[string]PropertySchema{
	"electrical": {
		"breaker": {
			Required: []string{"breaker_amps", "breaker_poles", "circuit_number"},
			Optional: []string{"circuit_name", "make", "model"},
			Types: map[string]string{
				"breaker_amps":  "int",
				"breaker_poles": "int",
				"circuit_number": "string",
			},
			Ranges: map[string]interface{}{
				"breaker_amps": []int{15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150, 200},
				"breaker_poles": []int{1, 2, 3},
			},
		},
		"outlet": {
			Required: []string{"device_type", "nema_config"},
			Optional: []string{"voltage", "phase"},
			Types: map[string]string{
				"device_type": "string",
				"nema_config": "string",
			},
			Values: map[string][]string{
				"device_type": {"receptacle", "gfci", "afci", "switch", "dimmer"},
				"nema_config": {"5-15R", "5-20R", "6-15R", "6-20R", "L14-30R"},
			},
		},
	},
	"hvac": {
		"vav": {
			Required: []string{"max_cfm", "min_cfm"},
			Optional: []string{"has_reheat", "reheat_type", "box_type"},
			Types: map[string]string{
				"max_cfm": "float",
				"min_cfm": "float",
				"has_reheat": "bool",
				"reheat_type": "string",
			},
			Values: map[string][]string{
				"reheat_type": {"electric", "hot_water", "none"},
				"box_type": {"single_duct", "dual_duct", "fan_powered"},
			},
		},
		"ahu": {
			Required: []string{"max_cfm", "equipment_type"},
			Optional: []string{"cooling_capacity_tons", "heating_capacity_kw"},
			Types: map[string]string{
				"max_cfm": "float",
				"cooling_capacity_tons": "float",
				"heating_capacity_kw": "float",
			},
		},
	},
	"plumbing": {
		"valve": {
			Required: []string{"valve_type", "valve_size"},
			Optional: []string{"normally_open", "make", "model"},
			Types: map[string]string{
				"valve_type": "string",
				"valve_size": "string",
				"normally_open": "bool",
			},
			Values: map[string][]string{
				"valve_type": {"ball", "gate", "globe", "check", "butterfly"},
				"valve_size": {"1/2\"", "3/4\"", "1\"", "1-1/4\"", "1-1/2\"", "2\"", "3\"", "4\""},
			},
		},
	},
}

// GetPropertySchema returns the property schema for a system/component type
func GetPropertySchema(system, componentType string) *PropertySchema {
	if systemSchemas, ok := SystemSchemas[system]; ok {
		if schema, ok := systemSchemas[componentType]; ok {
			return &schema
		}
	}
	return nil
}