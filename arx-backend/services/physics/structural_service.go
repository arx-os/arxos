package physics

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// StructuralService handles structural analysis integration
type StructuralService struct {
	pythonServiceURL string
	client           *http.Client
	cache            map[string]*StructuralAnalysisResult
}

// StructuralAnalysisRequest represents a structural analysis request
type StructuralAnalysisRequest struct {
	ElementID    string                   `json:"element_id"`
	AnalysisType string                   `json:"analysis_type"`
	Elements     []StructuralElement      `json:"elements"`
	Loads        []Load                   `json:"loads"`
	Materials    map[string]MaterialProps `json:"materials"`
	Options      AnalysisOptions          `json:"options"`
}

// StructuralElement represents a structural element
type StructuralElement struct {
	ID       string                 `json:"id"`
	Type     string                 `json:"type"`
	Material string                 `json:"material"`
	Geometry map[string]interface{} `json:"geometry"`
	Nodes    [][]float64            `json:"nodes"`
	Supports []Support              `json:"supports"`
}

// Load represents a structural load
type Load struct {
	ID        string    `json:"id"`
	Type      string    `json:"type"`
	Magnitude float64   `json:"magnitude"`
	Direction []float64 `json:"direction"`
	Location  []float64 `json:"location"`
	Duration  float64   `json:"duration"`
}

// MaterialProps represents material properties
type MaterialProps struct {
	Name             string  `json:"name"`
	Type             string  `json:"type"`
	ElasticModulus   float64 `json:"elastic_modulus"`
	PoissonRatio     float64 `json:"poisson_ratio"`
	YieldStrength    float64 `json:"yield_strength"`
	UltimateStrength float64 `json:"ultimate_strength"`
	Density          float64 `json:"density"`
	ThermalExpansion float64 `json:"thermal_expansion"`
	FatigueStrength  float64 `json:"fatigue_strength"`
}

// Support represents a structural support
type Support struct {
	Node       int    `json:"node"`
	Type       string `json:"type"`
	Restraints []bool `json:"restraints"`
}

// AnalysisOptions represents analysis options
type AnalysisOptions struct {
	MaxIterations int     `json:"max_iterations"`
	Tolerance     float64 `json:"tolerance"`
	TimeStep      float64 `json:"time_step"`
	MaxTime       float64 `json:"max_time"`
}

// StructuralAnalysisResult represents the result of structural analysis
type StructuralAnalysisResult struct {
	ElementID       string                 `json:"element_id"`
	AnalysisType    string                 `json:"analysis_type"`
	Displacements   [][]float64            `json:"displacements"`
	Stresses        [][]float64            `json:"stresses"`
	Strains         [][]float64            `json:"strains"`
	Forces          [][]float64            `json:"forces"`
	SafetyFactor    float64                `json:"safety_factor"`
	MaxDisplacement float64                `json:"max_displacement"`
	MaxStress       float64                `json:"max_stress"`
	MaxStrain       float64                `json:"max_strain"`
	BucklingLoad    *float64               `json:"buckling_load,omitempty"`
	FatigueLife     *float64               `json:"fatigue_life,omitempty"`
	AnalysisTime    float64                `json:"analysis_time"`
	Status          string                 `json:"status"`
	Error           string                 `json:"error,omitempty"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// NewStructuralService creates a new structural analysis service
func NewStructuralService(pythonServiceURL string) *StructuralService {
	return &StructuralService{
		pythonServiceURL: pythonServiceURL,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		cache: make(map[string]*StructuralAnalysisResult),
	}
}

// AnalyzeStructure performs structural analysis
func (ss *StructuralService) AnalyzeStructure(request *StructuralAnalysisRequest) (*StructuralAnalysisResult, error) {
	startTime := time.Now()

	// Check cache first
	cacheKey := ss.generateCacheKey(request)
	if cached, exists := ss.cache[cacheKey]; exists {
		return cached, nil
	}

	// Validate request
	if err := ss.validateRequest(request); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Call Python service
	result, err := ss.callPythonService(request)
	if err != nil {
		return nil, fmt.Errorf("Python service call failed: %w", err)
	}

	// Calculate analysis time
	result.AnalysisTime = time.Since(startTime).Seconds()

	// Cache result
	ss.cache[cacheKey] = result

	return result, nil
}

// AnalyzeBeam performs beam analysis
func (ss *StructuralService) AnalyzeBeam(beamID string, length, width, height float64, material string, loads []Load) (*StructuralAnalysisResult, error) {
	request := &StructuralAnalysisRequest{
		ElementID:    beamID,
		AnalysisType: "static",
		Elements: []StructuralElement{
			{
				ID:       beamID,
				Type:     "beam",
				Material: material,
				Geometry: map[string]interface{}{
					"length": length,
					"width":  width,
					"height": height,
				},
				Nodes: [][]float64{
					{0, 0, 0},
					{length, 0, 0},
				},
				Supports: []Support{
					{Node: 0, Type: "fixed", Restraints: []bool{true, true, true, true, true, true}},
					{Node: 1, Type: "pinned", Restraints: []bool{true, true, true, false, false, false}},
				},
			},
		},
		Loads: loads,
		Options: AnalysisOptions{
			MaxIterations: 1000,
			Tolerance:     1e-6,
		},
	}

	return ss.AnalyzeStructure(request)
}

// AnalyzeColumn performs column analysis
func (ss *StructuralService) AnalyzeColumn(columnID string, length, width, height float64, material string, axialLoad float64) (*StructuralAnalysisResult, error) {
	request := &StructuralAnalysisRequest{
		ElementID:    columnID,
		AnalysisType: "buckling",
		Elements: []StructuralElement{
			{
				ID:       columnID,
				Type:     "column",
				Material: material,
				Geometry: map[string]interface{}{
					"length": length,
					"width":  width,
					"height": height,
				},
				Nodes: [][]float64{
					{0, 0, 0},
					{0, 0, length},
				},
				Supports: []Support{
					{Node: 0, Type: "fixed", Restraints: []bool{true, true, true, true, true, true}},
					{Node: 1, Type: "pinned", Restraints: []bool{true, true, true, false, false, false}},
				},
			},
		},
		Loads: []Load{
			{
				ID:        "axial_load",
				Type:      "dead",
				Magnitude: axialLoad,
				Direction: []float64{0, 0, -1},
				Location:  []float64{0, 0, length},
				Duration:  0,
			},
		},
		Options: AnalysisOptions{
			MaxIterations: 1000,
			Tolerance:     1e-6,
		},
	}

	return ss.AnalyzeStructure(request)
}

// AnalyzePlate performs plate analysis
func (ss *StructuralService) AnalyzePlate(plateID string, length, width, thickness float64, material string, loads []Load) (*StructuralAnalysisResult, error) {
	request := &StructuralAnalysisRequest{
		ElementID:    plateID,
		AnalysisType: "static",
		Elements: []StructuralElement{
			{
				ID:       plateID,
				Type:     "plate",
				Material: material,
				Geometry: map[string]interface{}{
					"length":    length,
					"width":     width,
					"thickness": thickness,
				},
				Nodes: [][]float64{
					{0, 0, 0},
					{length, 0, 0},
					{length, width, 0},
					{0, width, 0},
				},
				Supports: []Support{
					{Node: 0, Type: "fixed", Restraints: []bool{true, true, true, true, true, true}},
				},
			},
		},
		Loads: loads,
		Options: AnalysisOptions{
			MaxIterations: 1000,
			Tolerance:     1e-6,
		},
	}

	return ss.AnalyzeStructure(request)
}

// AnalyzeFatigue performs fatigue analysis
func (ss *StructuralService) AnalyzeFatigue(elementID string, element StructuralElement, loadHistory []Load) (*StructuralAnalysisResult, error) {
	request := &StructuralAnalysisRequest{
		ElementID:    elementID,
		AnalysisType: "fatigue",
		Elements:     []StructuralElement{element},
		Loads:        loadHistory,
		Options: AnalysisOptions{
			MaxIterations: 1000,
			Tolerance:     1e-6,
		},
	}

	return ss.AnalyzeStructure(request)
}

// AnalyzeDynamic performs dynamic analysis
func (ss *StructuralService) AnalyzeDynamic(elementID string, element StructuralElement, loads []Load, timeStep, maxTime float64) (*StructuralAnalysisResult, error) {
	request := &StructuralAnalysisRequest{
		ElementID:    elementID,
		AnalysisType: "dynamic",
		Elements:     []StructuralElement{element},
		Loads:        loads,
		Options: AnalysisOptions{
			MaxIterations: 1000,
			Tolerance:     1e-6,
			TimeStep:      timeStep,
			MaxTime:       maxTime,
		},
	}

	return ss.AnalyzeStructure(request)
}

// GetAnalysisHistory returns analysis history for an element
func (ss *StructuralService) GetAnalysisHistory(elementID string) ([]*StructuralAnalysisResult, error) {
	// This would typically query the database
	// For now, return mock data
	return []*StructuralAnalysisResult{
		{
			ElementID:       elementID,
			AnalysisType:    "static",
			SafetyFactor:    2.5,
			MaxDisplacement: 0.005,
			MaxStress:       150.0,
			AnalysisTime:    1.2,
			Status:          "completed",
		},
		{
			ElementID:    elementID,
			AnalysisType: "buckling",
			SafetyFactor: 3.2,
			BucklingLoad: &[]float64{50000.0}[0],
			AnalysisTime: 2.1,
			Status:       "completed",
		},
	}, nil
}

// GetMaterialProperties returns material properties
func (ss *StructuralService) GetMaterialProperties(materialName string) (*MaterialProps, error) {
	// This would typically query the database
	// For now, return mock data
	materials := map[string]*MaterialProps{
		"A36_Steel": {
			Name:             "A36 Steel",
			Type:             "steel",
			ElasticModulus:   200000,
			PoissonRatio:     0.3,
			YieldStrength:    250,
			UltimateStrength: 400,
			Density:          7850,
			ThermalExpansion: 12e-6,
			FatigueStrength:  150,
		},
		"Concrete_C30": {
			Name:             "C30 Concrete",
			Type:             "concrete",
			ElasticModulus:   30000,
			PoissonRatio:     0.2,
			YieldStrength:    30,
			UltimateStrength: 40,
			Density:          2400,
			ThermalExpansion: 10e-6,
			FatigueStrength:  15,
		},
	}

	if material, exists := materials[materialName]; exists {
		return material, nil
	}

	return nil, fmt.Errorf("material %s not found", materialName)
}

// Helper methods

func (ss *StructuralService) validateRequest(request *StructuralAnalysisRequest) error {
	if request.ElementID == "" {
		return fmt.Errorf("element ID is required")
	}

	if len(request.Elements) == 0 {
		return fmt.Errorf("at least one element is required")
	}

	if request.AnalysisType == "" {
		return fmt.Errorf("analysis type is required")
	}

	// Validate analysis type
	validTypes := []string{"static", "dynamic", "buckling", "fatigue", "deflection"}
	valid := false
	for _, t := range validTypes {
		if request.AnalysisType == t {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid analysis type: %s", request.AnalysisType)
	}

	return nil
}

func (ss *StructuralService) callPythonService(request *StructuralAnalysisRequest) (*StructuralAnalysisResult, error) {
	// Serialize request
	requestJSON, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequest("POST", ss.pythonServiceURL+"/analyze", bytes.NewBuffer(requestJSON))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	// Send request
	resp, err := ss.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Python service returned status %d", resp.StatusCode)
	}

	// Parse response
	var result StructuralAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

func (ss *StructuralService) generateCacheKey(request *StructuralAnalysisRequest) string {
	// Create a simple cache key based on element ID and analysis type
	return fmt.Sprintf("%s_%s", request.ElementID, request.AnalysisType)
}

// ClearCache clears the analysis cache
func (ss *StructuralService) ClearCache() {
	ss.cache = make(map[string]*StructuralAnalysisResult)
}

// GetCacheSize returns the current cache size
func (ss *StructuralService) GetCacheSize() int {
	return len(ss.cache)
}

// GetCacheStats returns cache statistics
func (ss *StructuralService) GetCacheStats() map[string]interface{} {
	return map[string]interface{}{
		"size":         len(ss.cache),
		"hit_rate":     0.75,    // Mock hit rate
		"memory_usage": "2.5MB", // Mock memory usage
	}
}
