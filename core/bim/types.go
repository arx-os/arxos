package bim

// Column represents a structural column
type Column struct {
	ID       string
	Location Point3D
	Height   float64
	Width    float64
	Depth    float64
	Material string
}

// Slab represents a floor slab
type Slab struct {
	ID        string
	Thickness float64
	Polygon   []Point3D
	Material  string
}

// WallConnection represents a connection between walls
type WallConnection struct {
	WallID     string
	ConnectedTo string
	Type       string
	Angle      float64
}

// HostedObject represents an object hosted on a wall
type HostedObject struct {
	ID       string
	Type     string
	Position float64
	Height   float64
}

// Opening represents an opening in a wall
type Opening struct {
	ID     string
	Type   string
	Width  float64
	Height float64
	Sill   float64
}

// InsulationSpec represents insulation specifications
type InsulationSpec struct {
	Type      string
	Thickness float64
	RValue    float64
}

// RenderStyle represents rendering style for visualization
type RenderStyle struct {
	Color       string
	LineWeight  float64
	FillPattern string
	Transparent bool
}

// Constraint represents geometric constraints
type Constraint struct {
	Type   string
	Target string
	Value  float64
}

// Door represents a door object
type Door struct {
	ID          string
	Position    Point3D
	Width       float64
	Height      float64
	Type        string
	SwingAngle  float64
	Material    string
	HostWall    *Wall
}

// Window represents a window object
type Window struct {
	ID       string
	Width    float64
	Height   float64
	Type     string
	Glazing  string
	Frame    string
}

// Corridor represents a corridor/hallway
type Corridor struct {
	ID        string
	Name      string
	Width     float64
	Length    float64
	Polygon   []Point3D
}

// Outlet represents an electrical outlet
type Outlet struct {
	ID       string
	Type     string
	Position Point3D
	Height   float64
	HostWall *Wall
	Voltage  int
	Amperage int
}

// ElectricalOutlet is an alias for Outlet
type ElectricalOutlet = Outlet

// LightFixture represents a lighting fixture
type LightFixture struct {
	ID       string
	Type     string
	Position Point3D
	Wattage  int
	Lumens   int
}

// HVACTerminal represents an HVAC terminal unit
type HVACTerminal struct {
	ID       string
	Type     string
	Position Point3D
	Capacity float64
	Zone     string
}

// PlumbingFixture represents a plumbing fixture
type PlumbingFixture struct {
	ID       string
	Type     string
	Position Point3D
	FlowRate float64
}

// ElectricalPanel represents an electrical panel
type ElectricalPanel struct {
	ID         string
	Location   Point3D
	Voltage    int
	Amperage   int
	NumCircuits int
}

// Circuit represents an electrical circuit
type Circuit struct {
	ID       string
	PanelID  string
	Number   int
	Amperage int
	Voltage  int
	Outlets  []string
}

// Switch represents an electrical switch
type Switch struct {
	ID       string
	Type     string
	Position Point3D
	Controls []string
}

// Conduit represents electrical conduit
type Conduit struct {
	ID       string
	Diameter float64
	Path     []Point3D
	Material string
}

// CableTray represents a cable tray
type CableTray struct {
	ID       string
	Width    float64
	Height   float64
	Path     []Point3D
	Material string
}

// LoadCalculation represents electrical load calculations
type LoadCalculation struct {
	TotalLoad      float64
	DiversityFactor float64
	DemandFactor   float64
	PeakDemand     float64
}

// AirHandler represents an air handling unit
type AirHandler struct {
	ID       string
	Location Point3D
	Capacity float64
	Type     string
}

// VAVBox represents a variable air volume box
type VAVBox struct {
	ID       string
	Location Point3D
	MinFlow  float64
	MaxFlow  float64
}

// Diffuser represents an air diffuser
type Diffuser struct {
	ID       string
	Location Point3D
	Size     string
	CFM      float64
}

// ReturnGrille represents a return air grille
type ReturnGrille struct {
	ID       string
	Location Point3D
	Size     string
}

// Duct represents HVAC ductwork
type Duct struct {
	ID       string
	Path     []Point3D
	Width    float64
	Height   float64
	Material string
}

// RefrigerantPipe represents refrigerant piping
type RefrigerantPipe struct {
	ID       string
	Path     []Point3D
	Diameter float64
	Type     string
}

// AirflowCalculation represents airflow calculations
type AirflowCalculation struct {
	TotalCFM       float64
	StaticPressure float64
	VelocityFPM    float64
}

// SystemsModel represents all building systems
type SystemsModel struct {
	ElectricalSystems []ElectricalSystem
	HVACSystems       []HVACSystem
	PlumbingSystems   []PlumbingSystem
}

// SpatialIndex represents spatial indexing for fast queries
type SpatialIndex struct {
	Grid map[string][]string // Grid-based spatial index
}

// PlumbingSystem represents a plumbing system
type PlumbingSystem struct {
	ID          string
	Name        string
	Type        string
	Fixtures    []PlumbingFixture
	SupplyPipes []Pipe
	DrainPipes  []Pipe
}

// Pipe represents a plumbing pipe
type Pipe struct {
	ID       string
	Path     []Point3D
	Diameter float64
	Material string
	Type     string // supply, drain, vent
}

