package models

import (
	"time"
)

// FluidAnalysisRequest represents a fluid analysis request
type FluidAnalysisRequest struct {
	ID                 string                 `json:"id"`
	Type               string                 `json:"type"` // laminar, turbulent, compressible
	Geometry           map[string]interface{} `json:"geometry"`
	BoundaryConditions map[string]interface{} `json:"boundary_conditions"`
	FluidProperties    map[string]interface{} `json:"fluid_properties"`
	MeshSettings       map[string]interface{} `json:"mesh_settings"`
	SolverSettings     map[string]interface{} `json:"solver_settings"`
	CreatedAt          time.Time              `json:"created_at"`
}

// FluidAnalysisResult represents the result of fluid analysis
type FluidAnalysisResult struct {
	ID             string      `json:"id"`
	Status         string      `json:"status"`
	FlowRate       float64     `json:"flow_rate"`
	PressureDrop   float64     `json:"pressure_drop"`
	Velocity       float64     `json:"velocity"`
	ReynoldsNumber float64     `json:"reynolds_number"`
	PressureField  []float64   `json:"pressure_field"`
	VelocityField  []float64   `json:"velocity_field"`
	Streamlines    [][]float64 `json:"streamlines"`
	AnalysisTime   float64     `json:"analysis_time"`
	Error          string      `json:"error,omitempty"`
	CreatedAt      time.Time   `json:"created_at"`
	CompletedAt    *time.Time  `json:"completed_at"`
}

// ThermalAnalysisRequest represents a thermal analysis request
type ThermalAnalysisRequest struct {
	ID                 string                   `json:"id"`
	Type               string                   `json:"type"` // conduction, convection, radiation
	Geometry           map[string]interface{}   `json:"geometry"`
	MaterialProperties map[string]interface{}   `json:"material_properties"`
	BoundaryConditions map[string]interface{}   `json:"boundary_conditions"`
	HeatSources        []map[string]interface{} `json:"heat_sources"`
	MeshSettings       map[string]interface{}   `json:"mesh_settings"`
	SolverSettings     map[string]interface{}   `json:"solver_settings"`
	CreatedAt          time.Time                `json:"created_at"`
}

// ThermalAnalysisResult represents the result of thermal analysis
type ThermalAnalysisResult struct {
	ID                  string      `json:"id"`
	Status              string      `json:"status"`
	Temperature         float64     `json:"temperature"`
	HeatTransfer        float64     `json:"heat_transfer"`
	ThermalConductivity float64     `json:"thermal_conductivity"`
	TemperatureField    []float64   `json:"temperature_field"`
	HeatFluxField       []float64   `json:"heat_flux_field"`
	ThermalGradients    [][]float64 `json:"thermal_gradients"`
	AnalysisTime        float64     `json:"analysis_time"`
	Error               string      `json:"error,omitempty"`
	CreatedAt           time.Time   `json:"created_at"`
	CompletedAt         *time.Time  `json:"completed_at"`
}

// ElectricalAnalysisRequest represents an electrical analysis request
type ElectricalAnalysisRequest struct {
	ID             string                   `json:"id"`
	Type           string                   `json:"type"` // dc, ac, transient
	Circuit        map[string]interface{}   `json:"circuit"`
	Components     []map[string]interface{} `json:"components"`
	Sources        []map[string]interface{} `json:"sources"`
	Loads          []map[string]interface{} `json:"loads"`
	SolverSettings map[string]interface{}   `json:"solver_settings"`
	CreatedAt      time.Time                `json:"created_at"`
}

// ElectricalAnalysisResult represents the result of electrical analysis
type ElectricalAnalysisResult struct {
	ID           string     `json:"id"`
	Status       string     `json:"status"`
	Voltage      float64    `json:"voltage"`
	Current      float64    `json:"current"`
	Power        float64    `json:"power"`
	Resistance   float64    `json:"resistance"`
	VoltageField []float64  `json:"voltage_field"`
	CurrentField []float64  `json:"current_field"`
	PowerField   []float64  `json:"power_field"`
	AnalysisTime float64    `json:"analysis_time"`
	Error        string     `json:"error,omitempty"`
	CreatedAt    time.Time  `json:"created_at"`
	CompletedAt  *time.Time `json:"completed_at"`
}

// PhysicsAnalysis represents a general physics analysis
type PhysicsAnalysis struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"` // structural, fluid, thermal, electrical
	SubType      string                 `json:"sub_type"`
	Status       string                 `json:"status"`
	Request      map[string]interface{} `json:"request"`
	Result       map[string]interface{} `json:"result"`
	AnalysisTime float64                `json:"analysis_time"`
	Error        string                 `json:"error,omitempty"`
	CreatedAt    time.Time              `json:"created_at"`
	CompletedAt  *time.Time             `json:"completed_at"`
}

// PhysicsMaterial represents a physics material
type PhysicsMaterial struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"` // structural, fluid, thermal, electrical
	Category    string                 `json:"category"`
	Properties  map[string]interface{} `json:"properties"`
	Units       map[string]string      `json:"units"`
	Description string                 `json:"description"`
	Source      string                 `json:"source"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// PhysicsGeometry represents a physics geometry
type PhysicsGeometry struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`   // 2d, 3d
	Format      string                 `json:"format"` // stl, step, iges, etc.
	Data        map[string]interface{} `json:"data"`
	BoundingBox []float64              `json:"bounding_box"`
	Volume      float64                `json:"volume"`
	SurfaceArea float64                `json:"surface_area"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// PhysicsMesh represents a physics mesh
type PhysicsMesh struct {
	ID           string                 `json:"id"`
	GeometryID   string                 `json:"geometry_id"`
	Type         string                 `json:"type"` // tetrahedral, hexahedral, mixed
	ElementType  string                 `json:"element_type"`
	NodeCount    int                    `json:"node_count"`
	ElementCount int                    `json:"element_count"`
	Quality      float64                `json:"quality"`
	Settings     map[string]interface{} `json:"settings"`
	Data         map[string]interface{} `json:"data"`
	CreatedAt    time.Time              `json:"created_at"`
}

// PhysicsBoundaryCondition represents a physics boundary condition
type PhysicsBoundaryCondition struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	PhysicsType string                 `json:"physics_type"`
	Geometry    string                 `json:"geometry"`
	Value       map[string]interface{} `json:"value"`
	Units       map[string]string      `json:"units"`
	Description string                 `json:"description"`
	CreatedAt   time.Time              `json:"created_at"`
}

// PhysicsSolver represents a physics solver configuration
type PhysicsSolver struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	PhysicsType string                 `json:"physics_type"`
	Method      string                 `json:"method"`
	Settings    map[string]interface{} `json:"settings"`
	Convergence map[string]interface{} `json:"convergence"`
	Performance map[string]interface{} `json:"performance"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// PhysicsResult represents a physics analysis result
type PhysicsResult struct {
	ID            string                 `json:"id"`
	AnalysisID    string                 `json:"analysis_id"`
	Type          string                 `json:"type"`
	Status        string                 `json:"status"`
	Data          map[string]interface{} `json:"data"`
	Visualization map[string]interface{} `json:"visualization"`
	Statistics    map[string]interface{} `json:"statistics"`
	Error         string                 `json:"error,omitempty"`
	CreatedAt     time.Time              `json:"created_at"`
	CompletedAt   *time.Time             `json:"completed_at"`
}

// PhysicsStatistics represents physics analysis statistics
type PhysicsStatistics struct {
	ID            string                 `json:"id"`
	Period        string                 `json:"period"`
	Date          time.Time              `json:"date"`
	Type          string                 `json:"type"`
	TotalAnalyses int                    `json:"total_analyses"`
	Successful    int                    `json:"successful"`
	Failed        int                    `json:"failed"`
	AverageTime   float64                `json:"average_time"`
	SuccessRate   float64                `json:"success_rate"`
	ResourceUsage map[string]interface{} `json:"resource_usage"`
	CreatedAt     time.Time              `json:"created_at"`
}

// PhysicsJob represents a physics analysis job
type PhysicsJob struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Status      string                 `json:"status"`
	Priority    int                    `json:"priority"`
	Request     map[string]interface{} `json:"request"`
	Result      map[string]interface{} `json:"result"`
	Progress    float64                `json:"progress"`
	Error       string                 `json:"error,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	StartedAt   *time.Time             `json:"started_at"`
	CompletedAt *time.Time             `json:"completed_at"`
}

// PhysicsQueue represents a physics analysis queue
type PhysicsQueue struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Status      string                 `json:"status"`
	Capacity    int                    `json:"capacity"`
	CurrentLoad int                    `json:"current_load"`
	Jobs        []PhysicsJob           `json:"jobs"`
	Settings    map[string]interface{} `json:"settings"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// PhysicsResource represents a physics computing resource
type PhysicsResource struct {
	ID             string                 `json:"id"`
	Name           string                 `json:"name"`
	Type           string                 `json:"type"` // cpu, gpu, cluster
	Status         string                 `json:"status"`
	Specifications map[string]interface{} `json:"specifications"`
	Utilization    map[string]interface{} `json:"utilization"`
	Performance    map[string]interface{} `json:"performance"`
	CreatedAt      time.Time              `json:"created_at"`
	UpdatedAt      time.Time              `json:"updated_at"`
}

// PhysicsConfiguration represents physics system configuration
type PhysicsConfiguration struct {
	ID          string    `json:"id"`
	Key         string    `json:"key"`
	Value       string    `json:"value"`
	Category    string    `json:"category"`
	Description string    `json:"description"`
	Enabled     bool      `json:"enabled"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// PhysicsValidation represents physics validation results
type PhysicsValidation struct {
	ID         string            `json:"id"`
	AnalysisID string            `json:"analysis_id"`
	Type       string            `json:"type"`
	Status     string            `json:"status"`
	Checks     []ValidationCheck `json:"checks"`
	Warnings   []string          `json:"warnings"`
	Errors     []string          `json:"errors"`
	CreatedAt  time.Time         `json:"created_at"`
}

// ValidationCheck represents a validation check
type ValidationCheck struct {
	Name      string      `json:"name"`
	Type      string      `json:"type"`
	Status    string      `json:"status"`
	Value     interface{} `json:"value"`
	Expected  interface{} `json:"expected"`
	Tolerance float64     `json:"tolerance"`
	Message   string      `json:"message"`
}

// Physics constants

const (
	// Analysis types
	PhysicsTypeStructural = "structural"
	PhysicsTypeFluid      = "fluid"
	PhysicsTypeThermal    = "thermal"
	PhysicsTypeElectrical = "electrical"

	// Analysis subtypes
	PhysicsSubTypeStatic     = "static"
	PhysicsSubTypeDynamic    = "dynamic"
	PhysicsSubTypeBuckling   = "buckling"
	PhysicsSubTypeFatigue    = "fatigue"
	PhysicsSubTypeDeflection = "deflection"

	// Fluid analysis types
	FluidTypeLaminar      = "laminar"
	FluidTypeTurbulent    = "turbulent"
	FluidTypeCompressible = "compressible"

	// Thermal analysis types
	ThermalTypeConduction = "conduction"
	ThermalTypeConvection = "convection"
	ThermalTypeRadiation  = "radiation"

	// Electrical analysis types
	ElectricalTypeDC        = "dc"
	ElectricalTypeAC        = "ac"
	ElectricalTypeTransient = "transient"

	// Job status
	JobStatusPending   = "pending"
	JobStatusRunning   = "running"
	JobStatusCompleted = "completed"
	JobStatusFailed    = "failed"
	JobStatusCancelled = "cancelled"

	// Queue status
	QueueStatusActive  = "active"
	QueueStatusPaused  = "paused"
	QueueStatusStopped = "stopped"

	// Resource status
	ResourceStatusAvailable = "available"
	ResourceStatusBusy      = "busy"
	ResourceStatusOffline   = "offline"
	ResourceStatusError     = "error"

	// Validation status
	ValidationStatusPassed  = "passed"
	ValidationStatusWarning = "warning"
	ValidationStatusFailed  = "failed"
)
