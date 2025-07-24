package models

import (
	"time"
)

// StructuralElement represents a structural element in the system
type StructuralElement struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"` // beam, column, plate, shell
	Material    string                 `json:"material"`
	Geometry    map[string]interface{} `json:"geometry"`
	Nodes       [][]float64            `json:"nodes"`
	Supports    []Support              `json:"supports"`
	Loads       []Load                 `json:"loads"`
	Properties  ElementProperties      `json:"properties"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// Support represents a structural support condition
type Support struct {
	Node       int      `json:"node"`
	Type       string   `json:"type"` // fixed, pinned, roller, etc.
	Restraints []bool   `json:"restraints"` // [x, y, z, rx, ry, rz]
	Stiffness  []float64 `json:"stiffness,omitempty"`
}

// Load represents a structural load
type Load struct {
	ID        string    `json:"id"`
	Type      string    `json:"type"` // dead, live, wind, seismic, etc.
	Magnitude float64   `json:"magnitude"`
	Direction []float64 `json:"direction"` // unit vector [x, y, z]
	Location  []float64 `json:"location"`  // coordinates [x, y, z]
	Duration  float64   `json:"duration"`  // seconds (0 for static loads)
	Function  string    `json:"function,omitempty"` // time function for dynamic loads
}

// ElementProperties contains physical properties of structural elements
type ElementProperties struct {
	CrossSection CrossSection `json:"cross_section"`
	Material     Material     `json:"material"`
	Mass         float64      `json:"mass"`
	Inertia      []float64    `json:"inertia"` // [Ix, Iy, Iz]
}

// CrossSection represents cross-sectional properties
type CrossSection struct {
	Type       string  `json:"type"` // rectangular, circular, I-beam, etc.
	Area       float64 `json:"area"`
	Height     float64 `json:"height"`
	Width      float64 `json:"width"`
	Thickness  float64 `json:"thickness,omitempty"`
	Ix         float64 `json:"ix"` // moment of inertia about x-axis
	Iy         float64 `json:"iy"` // moment of inertia about y-axis
	Iz         float64 `json:"iz"` // polar moment of inertia
	SectionModulusX float64 `json:"section_modulus_x"`
	SectionModulusY float64 `json:"section_modulus_y"`
}

// Material represents material properties
type Material struct {
	Name             string  `json:"name"`
	Type             string  `json:"type"`
	ElasticModulus   float64 `json:"elastic_modulus"`   // E in MPa
	PoissonRatio     float64 `json:"poisson_ratio"`     // ν
	YieldStrength    float64 `json:"yield_strength"`    // σy in MPa
	UltimateStrength float64 `json:"ultimate_strength"` // σu in MPa
	Density          float64 `json:"density"`           // ρ in kg/m³
	ThermalExpansion float64 `json:"thermal_expansion"` // α in 1/°C
	FatigueStrength  float64 `json:"fatigue_strength"`  // σf in MPa
	FractureToughness float64 `json:"fracture_toughness"` // KIC in MPa·√m
}

// AnalysisRequest represents a structural analysis request
type AnalysisRequest struct {
	ID           string                `json:"id"`
	Elements     []StructuralElement   `json:"elements"`
	AnalysisType string                `json:"analysis_type"` // static, dynamic, buckling, fatigue
	LoadCombination string             `json:"load_combination"`
	Options      AnalysisOptions       `json:"options"`
	RequestedBy  string                `json:"requested_by"`
	Priority     int                   `json:"priority"`
	CreatedAt    time.Time             `json:"created_at"`
}

// AnalysisOptions contains analysis configuration options
type AnalysisOptions struct {
	MaxIterations int     `json:"max_iterations"`
	Tolerance     float64 `json:"tolerance"`
	TimeStep      float64 `json:"time_step"`
	MaxTime       float64 `json:"max_time"`
	SolverType    string  `json:"solver_type"` // direct, iterative
	ElementType   string  `json:"element_type"` // beam, shell, solid
	IntegrationOrder int  `json:"integration_order"`
	Nonlinear    bool    `json:"nonlinear"`
	LargeDeformation bool `json:"large_deformation"`
}

// AnalysisResult represents the result of structural analysis
type AnalysisResult struct {
	ID              string                 `json:"id"`
	RequestID       string                 `json:"request_id"`
	ElementID       string                 `json:"element_id"`
	AnalysisType    string                 `json:"analysis_type"`
	Status          string                 `json:"status"` // completed, failed, in_progress
	Displacements   [][]float64            `json:"displacements"`
	Stresses        [][]float64            `json:"stresses"`
	Strains         [][]float64            `json:"strains"`
	Forces          [][]float64            `json:"forces"`
	Reactions       [][]float64            `json:"reactions"`
	SafetyFactor    float64                `json:"safety_factor"`
	MaxDisplacement float64                `json:"max_displacement"`
	MaxStress       float64                `json:"max_stress"`
	MaxStrain       float64                `json:"max_strain"`
	BucklingLoad    *float64               `json:"buckling_load,omitempty"`
	FatigueLife     *float64               `json:"fatigue_life,omitempty"`
	AnalysisTime    float64                `json:"analysis_time"`
	Error           string                 `json:"error,omitempty"`
	Metadata        map[string]interface{} `json:"metadata"`
	CreatedAt       time.Time              `json:"created_at"`
}

// LoadCombination represents a combination of loads
type LoadCombination struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Type        string            `json:"type"` // ultimate, service
	Loads       []LoadFactor      `json:"loads"`
	Description string            `json:"description"`
	CreatedAt   time.Time         `json:"created_at"`
}

// LoadFactor represents a load with its factor
type LoadFactor struct {
	LoadID string  `json:"load_id"`
	Factor float64 `json:"factor"`
}

// StructuralModel represents a complete structural model
type StructuralModel struct {
	ID          string                `json:"id"`
	Name        string                `json:"name"`
	Description string                `json:"description"`
	Elements    []StructuralElement   `json:"elements"`
	Materials   map[string]Material   `json:"materials"`
	LoadCases   []LoadCase            `json:"load_cases"`
	LoadCombinations []LoadCombination `json:"load_combinations"`
	CreatedAt   time.Time             `json:"created_at"`
	UpdatedAt   time.Time             `json:"updated_at"`
}

// LoadCase represents a load case
type LoadCase struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Type        string    `json:"type"`
	Loads       []Load    `json:"loads"`
	Description string    `json:"description"`
	CreatedAt   time.Time `json:"created_at"`
}

// AnalysisHistory represents analysis history for an element
type AnalysisHistory struct {
	ElementID string           `json:"element_id"`
	Results   []AnalysisResult `json:"results"`
	Summary   AnalysisSummary  `json:"summary"`
}

// AnalysisSummary provides a summary of analysis results
type AnalysisSummary struct {
	TotalAnalyses    int     `json:"total_analyses"`
	SuccessfulAnalyses int   `json:"successful_analyses"`
	AverageSafetyFactor float64 `json:"average_safety_factor"`
	MinSafetyFactor   float64 `json:"min_safety_factor"`
	MaxSafetyFactor   float64 `json:"max_safety_factor"`
	LastAnalysisDate  time.Time `json:"last_analysis_date"`
}

// StructuralValidation represents validation results
type StructuralValidation struct {
	ElementID    string   `json:"element_id"`
	Valid        bool     `json:"valid"`
	Errors       []string `json:"errors"`
	Warnings     []string `json:"warnings"`
	ValidatedAt  time.Time `json:"validated_at"`
}

// MaterialLibrary represents a library of materials
type MaterialLibrary struct {
	ID        string              `json:"id"`
	Name      string              `json:"name"`
	Materials map[string]Material `json:"materials"`
	CreatedAt time.Time           `json:"created_at"`
	UpdatedAt time.Time           `json:"updated_at"`
}

// CrossSectionLibrary represents a library of cross sections
type CrossSectionLibrary struct {
	ID            string                    `json:"id"`
	Name          string                    `json:"name"`
	CrossSections map[string]CrossSection   `json:"cross_sections"`
	CreatedAt     time.Time                 `json:"created_at"`
	UpdatedAt     time.Time                 `json:"updated_at"`
}

// AnalysisTemplate represents a reusable analysis template
type AnalysisTemplate struct {
	ID          string          `json:"id"`
	Name        string          `json:"name"`
	Description string          `json:"description"`
	Options     AnalysisOptions `json:"options"`
	LoadCombinations []string   `json:"load_combinations"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
}

// StructuralReport represents a comprehensive structural analysis report
type StructuralReport struct {
	ID              string                `json:"id"`
	ModelID         string                `json:"model_id"`
	AnalysisResults []AnalysisResult      `json:"analysis_results"`
	Summary         ReportSummary         `json:"summary"`
	Recommendations []string              `json:"recommendations"`
	GeneratedAt     time.Time             `json:"generated_at"`
}

// ReportSummary provides a summary of the structural report
type ReportSummary struct {
	TotalElements     int     `json:"total_elements"`
	AnalyzedElements  int     `json:"analyzed_elements"`
	CriticalElements  int     `json:"critical_elements"`
	AverageSafetyFactor float64 `json:"average_safety_factor"`
	MinSafetyFactor   float64 `json:"min_safety_factor"`
	MaxSafetyFactor   float64 `json:"max_safety_factor"`
	OverallStatus     string  `json:"overall_status"`
} 