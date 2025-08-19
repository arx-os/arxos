package arxobject

// ObjectType represents the type of ArxObject element
type ObjectType string

// Architectural Elements
const (
	// Structural
	TypeWall           ObjectType = "wall"
	TypeColumn         ObjectType = "column"
	TypeBeam           ObjectType = "beam"
	TypeSlab           ObjectType = "slab"
	TypeFoundation     ObjectType = "foundation"
	TypeLoadBearing    ObjectType = "load_bearing"
	
	// Openings
	TypeDoor           ObjectType = "door"
	TypeDoorSingle     ObjectType = "door_single"
	TypeDoorDouble     ObjectType = "door_double"
	TypeDoorSliding    ObjectType = "door_sliding"
	TypeDoorBifold     ObjectType = "door_bifold"
	TypeDoorRevolving  ObjectType = "door_revolving"
	TypeDoorOverhead   ObjectType = "door_overhead"
	TypeDoorFire       ObjectType = "door_fire"
	
	// Windows
	TypeWindow         ObjectType = "window"
	TypeWindowFixed    ObjectType = "window_fixed"
	TypeWindowCasement ObjectType = "window_casement"
	TypeWindowSliding  ObjectType = "window_sliding"
	TypeWindowAwning   ObjectType = "window_awning"
	TypeSkylight       ObjectType = "skylight"
	TypeCurtainWall    ObjectType = "curtain_wall"
	
	// Spaces
	TypeRoom           ObjectType = "room"
	TypeCorridor       ObjectType = "corridor"
	TypeStairwell      ObjectType = "stairwell"
	TypeElevatorShaft  ObjectType = "elevator_shaft"
	TypeAtrium         ObjectType = "atrium"
	TypeVoid           ObjectType = "void"
	
	// Vertical Circulation
	TypeStairs         ObjectType = "stairs"
	TypeStairsUp       ObjectType = "stairs_up"
	TypeStairsDown     ObjectType = "stairs_down"
	TypeEscalator      ObjectType = "escalator"
	TypeRamp           ObjectType = "ramp"
	TypeLadder         ObjectType = "ladder"
	TypeElevator       ObjectType = "elevator"
	TypeLift           ObjectType = "lift"
	
	// Roofing
	TypeRoof           ObjectType = "roof"
	TypeRoofSlope      ObjectType = "roof_slope"
	TypeGutter         ObjectType = "gutter"
	TypeDownspout      ObjectType = "downspout"
	TypeParapet        ObjectType = "parapet"
)

// MEP - Mechanical
const (
	// HVAC Equipment
	TypeAHU            ObjectType = "ahu"              // Air Handling Unit
	TypeVAV            ObjectType = "vav"              // Variable Air Volume
	TypeFCU            ObjectType = "fcu"              // Fan Coil Unit
	TypeChiller        ObjectType = "chiller"
	TypeBoiler         ObjectType = "boiler"
	TypeCoolingTower   ObjectType = "cooling_tower"
	TypeHeatPump       ObjectType = "heat_pump"
	TypeFurnace        ObjectType = "furnace"
	TypeExhaustFan     ObjectType = "exhaust_fan"
	TypeSupplyFan      ObjectType = "supply_fan"
	
	// HVAC Distribution
	TypeDuct           ObjectType = "duct"
	TypeDuctSupply     ObjectType = "duct_supply"
	TypeDuctReturn     ObjectType = "duct_return"
	TypeDuctExhaust    ObjectType = "duct_exhaust"
	TypeDiffuser       ObjectType = "diffuser"
	TypeGrille         ObjectType = "grille"
	TypeRegister       ObjectType = "register"
	TypeDamper         ObjectType = "damper"
	TypeFireDamper     ObjectType = "fire_damper"
	TypeSmokeDetector  ObjectType = "smoke_detector"
	TypeThermostat     ObjectType = "thermostat"
	TypeHumidistat     ObjectType = "humidistat"
	TypeSensor         ObjectType = "sensor"
	TypeTemperatureSensor ObjectType = "temperature_sensor"
	TypePressureSensor ObjectType = "pressure_sensor"
	TypeFlowSensor     ObjectType = "flow_sensor"
)

// MEP - Electrical
const (
	// Power Distribution
	TypePanel          ObjectType = "panel"
	TypePanelMain      ObjectType = "panel_main"
	TypePanelSub       ObjectType = "panel_sub"
	TypeTransformer    ObjectType = "transformer"
	TypeGenerator      ObjectType = "generator"
	TypeUPS            ObjectType = "ups"
	TypeSwitchgear     ObjectType = "switchgear"
	TypeMCC            ObjectType = "mcc"              // Motor Control Center
	
	// Outlets & Devices
	TypeOutlet         ObjectType = "outlet"
	TypeOutletDuplex   ObjectType = "outlet_duplex"
	TypeOutlet220V     ObjectType = "outlet_220v"
	TypeOutletFloor    ObjectType = "outlet_floor"
	TypeOutletGFCI     ObjectType = "outlet_gfci"
	TypeSwitch         ObjectType = "switch"
	TypeSwitch3Way     ObjectType = "switch_3way"
	TypeDimmer         ObjectType = "dimmer"
	TypeJunctionBox    ObjectType = "junction_box"
	
	// Lighting
	TypeLight          ObjectType = "light"
	TypeLightCeiling   ObjectType = "light_ceiling"
	TypeLightRecessed  ObjectType = "light_recessed"
	TypeLightPendant   ObjectType = "light_pendant"
	TypeLightWall      ObjectType = "light_wall"
	TypeLightTrack     ObjectType = "light_track"
	TypeLightEmergency ObjectType = "light_emergency"
	TypeLightExit      ObjectType = "light_exit"
	TypeLightExterior  ObjectType = "light_exterior"
	
	// Low Voltage
	TypeDataOutlet     ObjectType = "data_outlet"
	TypePhoneOutlet    ObjectType = "phone_outlet"
	TypeTVOutlet       ObjectType = "tv_outlet"
	TypeCamera         ObjectType = "camera"
	TypeAccessControl  ObjectType = "access_control"
	TypeIntercom       ObjectType = "intercom"
	TypeSpeaker        ObjectType = "speaker"
	
	// Cable Management
	TypeConduit        ObjectType = "conduit"
	TypeCableTray      ObjectType = "cable_tray"
	TypeWireway        ObjectType = "wireway"
)

// MEP - Plumbing
const (
	// Fixtures
	TypeToilet         ObjectType = "toilet"
	TypeUrinal         ObjectType = "urinal"
	TypeSink           ObjectType = "sink"
	TypeLavatory       ObjectType = "lavatory"
	TypeShower         ObjectType = "shower"
	TypeBathtub        ObjectType = "bathtub"
	TypeDrinkingFountain ObjectType = "drinking_fountain"
	TypeFloorDrain     ObjectType = "floor_drain"
	TypeRoofDrain      ObjectType = "roof_drain"
	TypeCleanout       ObjectType = "cleanout"
	TypeHoseBibb       ObjectType = "hose_bibb"
	
	// Equipment
	TypeWaterHeater    ObjectType = "water_heater"
	TypeBoosterPump    ObjectType = "booster_pump"
	TypeExpansionTank  ObjectType = "expansion_tank"
	TypeBackflowPreventer ObjectType = "backflow_preventer"
	TypeGreaseInterceptor ObjectType = "grease_interceptor"
	TypeSumpPump       ObjectType = "sump_pump"
	TypeEjectorPump    ObjectType = "ejector_pump"
	
	// Piping
	TypePipe           ObjectType = "pipe"
	TypePipeColdWater  ObjectType = "pipe_cold_water"
	TypePipeHotWater   ObjectType = "pipe_hot_water"
	TypePipeWaste      ObjectType = "pipe_waste"
	TypePipeVent       ObjectType = "pipe_vent"
	TypePipeStorm      ObjectType = "pipe_storm"
	TypePipeGas        ObjectType = "pipe_gas"
	TypePipeSteam      ObjectType = "pipe_steam"
	TypePipeCondensate ObjectType = "pipe_condensate"
	
	// Valves
	TypeValve          ObjectType = "valve"
	TypeValveGate      ObjectType = "valve_gate"
	TypeValveBall      ObjectType = "valve_ball"
	TypeValveGlobe     ObjectType = "valve_globe"
	TypeValveCheck     ObjectType = "valve_check"
	TypeValvePRV       ObjectType = "valve_prv"        // Pressure Reducing
	TypeValveRelief    ObjectType = "valve_relief"
	TypeValveControl   ObjectType = "valve_control"
)

// Fire Protection
const (
	// Detection
	TypeSmokeAlarm     ObjectType = "smoke_alarm"
	TypeHeatDetector   ObjectType = "heat_detector"
	TypePullStation    ObjectType = "pull_station"
	TypeFirePanel      ObjectType = "fire_panel"
	TypeAnnunciator    ObjectType = "annunciator"
	
	// Suppression
	TypeSprinkler      ObjectType = "sprinkler"
	TypeSprinklerHead  ObjectType = "sprinkler_head"
	TypeFirePump       ObjectType = "fire_pump"
	TypeStandpipe      ObjectType = "standpipe"
	TypeFireHoseCabinet ObjectType = "fire_hose_cabinet"
	TypeFireExtinguisher ObjectType = "fire_extinguisher"
	TypeSiamese        ObjectType = "siamese_connection"
	
	// Notification
	TypeHorn           ObjectType = "horn"
	TypeStrobe         ObjectType = "strobe"
	TypeHornStrobe     ObjectType = "horn_strobe"
	TypeSpeakerFire    ObjectType = "speaker_fire"
)

// Furniture & Equipment
const (
	// Office
	TypeDesk           ObjectType = "desk"
	TypeChair          ObjectType = "chair"
	TypeTable          ObjectType = "table"
	TypeTableConference ObjectType = "table_conference"
	TypeCabinet        ObjectType = "cabinet"
	TypeShelf          ObjectType = "shelf"
	TypeWorkstation    ObjectType = "workstation"
	
	// Kitchen
	TypeRefrigerator   ObjectType = "refrigerator"
	TypeDishwasher     ObjectType = "dishwasher"
	TypeRange          ObjectType = "range"
	TypeOven           ObjectType = "oven"
	TypeMicrowave      ObjectType = "microwave"
	TypeCounter        ObjectType = "counter"
	
	// Specialty
	TypeBed            ObjectType = "bed"
	TypeCouch          ObjectType = "couch"
	TypeBench          ObjectType = "bench"
	TypeRack           ObjectType = "rack"
	TypeLocker         ObjectType = "locker"
	TypeVendingMachine ObjectType = "vending_machine"
)

// Site & Landscape
const (
	TypeParking        ObjectType = "parking"
	TypeDriveway       ObjectType = "driveway"
	TypeSidewalk       ObjectType = "sidewalk"
	TypeCurb           ObjectType = "curb"
	TypeRetainingWall  ObjectType = "retaining_wall"
	TypeFence          ObjectType = "fence"
	TypeGate           ObjectType = "gate"
	TypeBollard        ObjectType = "bollard"
	TypeTree           ObjectType = "tree"
	TypePlanter        ObjectType = "planter"
	TypePavement       ObjectType = "pavement"
	TypeLandscape      ObjectType = "landscape"
	TypeCatchBasin     ObjectType = "catch_basin"
	TypeManhole        ObjectType = "manhole"
	TypeUtilityPole    ObjectType = "utility_pole"
	TypeLightPole      ObjectType = "light_pole"
	TypeSign           ObjectType = "sign"
)

// Annotations & References
const (
	TypeDimension      ObjectType = "dimension"
	TypeText           ObjectType = "text"
	TypeLabel          ObjectType = "label"
	TypeCallout        ObjectType = "callout"
	TypeSection        ObjectType = "section"
	TypeElevation      ObjectType = "elevation"
	TypeDetail         ObjectType = "detail"
	TypeGrid           ObjectType = "grid"
	TypeNorth          ObjectType = "north"
	TypeScale          ObjectType = "scale"
	TypeTitle          ObjectType = "title"
	TypeRevision       ObjectType = "revision"
	TypeKeynote        ObjectType = "keynote"
	TypeSchedule       ObjectType = "schedule"
	TypeLegend         ObjectType = "legend"
)

// System represents the building system
type System string

const (
	SystemStructural   System = "structural"
	SystemElectrical   System = "electrical"
	SystemHVAC         System = "hvac"
	SystemPlumbing     System = "plumbing"
	SystemFire         System = "fire"
	SystemData         System = "data"
	SystemSecurity     System = "security"
	SystemFurniture    System = "furniture"
	SystemEquipment    System = "equipment"
	SystemSite         System = "site"
	SystemAnnotation   System = "annotation"
	SystemArchitectural System = "architectural"
	SystemMechanical   System = "mechanical"
	SystemTelecom      System = "telecom"
	SystemAudio        System = "audio"
	SystemLighting     System = "lighting"
	SystemControls     System = "controls"
	SystemEnvelope     System = "envelope"
	SystemInterior     System = "interior"
	SystemExterior     System = "exterior"
)

// RenderProperties contains properties for visual rendering
type RenderProperties struct {
	// Basic shape properties
	Shape        string  `json:"shape"`         // rect, circle, arc, line, polygon, path
	FillColor    string  `json:"fill_color"`    // Hex color or "none"
	StrokeColor  string  `json:"stroke_color"`  // Hex color
	StrokeWidth  float32 `json:"stroke_width"`  // Line thickness
	StrokeDash   []int   `json:"stroke_dash"`   // Dash pattern [on, off]
	Opacity      float32 `json:"opacity"`       // 0.0 to 1.0
	
	// Advanced properties
	Pattern      string  `json:"pattern"`       // Hatch pattern name
	Symbol       string  `json:"symbol"`        // Symbol identifier
	Text         string  `json:"text"`          // Display text/label
	Icon         string  `json:"icon"`          // Icon resource path
	Rotation     float32 `json:"rotation"`      // Rotation in degrees
	Mirror       bool    `json:"mirror"`        // Mirror horizontally
	
	// 3D properties (for future)
	Height       float32 `json:"height"`        // Extrusion height
	Elevation    float32 `json:"elevation"`     // Base elevation
	IsVisible3D  bool    `json:"is_visible_3d"` // Show in 3D view
}

// GetDefaultRenderProperties returns default rendering properties for each type
func GetDefaultRenderProperties(objType ObjectType, system System) RenderProperties {
	// This will be implemented in the renderer
	// Returns appropriate visual properties for each object type
	return RenderProperties{
		Shape:       "rect",
		StrokeColor: "#666666",
		StrokeWidth: 1.0,
		Opacity:     1.0,
	}
}

// TypeCategory groups object types into broader categories
type TypeCategory string

const (
	CategoryStructural   TypeCategory = "structural"
	CategoryArchitectural TypeCategory = "architectural"
	CategoryMechanical   TypeCategory = "mechanical"
	CategoryElectrical   TypeCategory = "electrical"
	CategoryPlumbing     TypeCategory = "plumbing"
	CategoryFire         TypeCategory = "fire"
	CategoryFurniture    TypeCategory = "furniture"
	CategorySite         TypeCategory = "site"
	CategoryAnnotation   TypeCategory = "annotation"
)

// GetTypeCategory returns the category for an object type
func GetTypeCategory(objType ObjectType) TypeCategory {
	// Implementation would map types to categories
	// This is a simplified version
	switch objType {
	case TypeWall, TypeColumn, TypeBeam, TypeSlab:
		return CategoryStructural
	case TypeDoor, TypeWindow, TypeRoom, TypeStairs:
		return CategoryArchitectural
	case TypeAHU, TypeDuct, TypeDiffuser:
		return CategoryMechanical
	case TypePanel, TypeOutlet, TypeLight:
		return CategoryElectrical
	case TypePipe, TypeValve, TypeToilet:
		return CategoryPlumbing
	case TypeSprinkler, TypeFirePanel:
		return CategoryFire
	case TypeDesk, TypeChair:
		return CategoryFurniture
	case TypeParking, TypeTree:
		return CategorySite
	case TypeDimension, TypeText:
		return CategoryAnnotation
	default:
		return CategoryArchitectural
	}
}