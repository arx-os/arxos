package physics

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arxos/arx-backend/models"
)

// FluidService handles fluid dynamics analysis integration
type FluidService struct {
	pythonServiceURL string
	httpClient       *http.Client
	cache            map[string]*models.FluidAnalysisResult
}

// FluidAnalysisRequest represents a fluid analysis request
type FluidAnalysisRequest struct {
	ID                 string                      `json:"id"`
	FlowType           string                      `json:"flow_type"`
	FluidProperties    *models.FluidProperties     `json:"fluid_properties"`
	Geometry           map[string]interface{}      `json:"geometry"`
	BoundaryConditions []*models.BoundaryCondition `json:"boundary_conditions"`
	Mesh               []*models.MeshElement       `json:"mesh"`
	SolverSettings     map[string]interface{}      `json:"solver_settings"`
	AnalysisType       string                      `json:"analysis_type"`
}

// NewFluidService creates a new fluid dynamics service
func NewFluidService(pythonServiceURL string) *FluidService {
	return &FluidService{
		pythonServiceURL: pythonServiceURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		cache: make(map[string]*models.FluidAnalysisResult),
	}
}

// AnalyzeFluidFlow performs fluid dynamics analysis
func (fs *FluidService) AnalyzeFluidFlow(request *FluidAnalysisRequest) (*models.FluidAnalysisResult, error) {
	// Check cache first
	if cached, exists := fs.cache[request.ID]; exists {
		return cached, nil
	}

	// Prepare request for Python service
	pythonRequest := map[string]interface{}{
		"id":                  request.ID,
		"flow_type":           request.FlowType,
		"fluid_properties":    request.FluidProperties,
		"geometry":            request.Geometry,
		"boundary_conditions": request.BoundaryConditions,
		"mesh":                request.Mesh,
		"solver_settings":     request.SolverSettings,
		"analysis_type":       request.AnalysisType,
	}

	// Convert to JSON
	jsonData, err := json.Marshal(pythonRequest)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Send request to Python service
	resp, err := fs.httpClient.Post(
		fs.pythonServiceURL+"/fluid-dynamics/analyze",
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to send request to Python service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Python service returned status: %d", resp.StatusCode)
	}

	// Parse response
	var result models.FluidAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Cache result
	fs.cache[request.ID] = &result

	return &result, nil
}

// AnalyzeLaminarFlow performs laminar flow analysis
func (fs *FluidService) AnalyzeLaminarFlow(request *FluidAnalysisRequest) (*models.FluidAnalysisResult, error) {
	request.FlowType = "laminar"
	return fs.AnalyzeFluidFlow(request)
}

// AnalyzeTurbulentFlow performs turbulent flow analysis
func (fs *FluidService) AnalyzeTurbulentFlow(request *FluidAnalysisRequest) (*models.FluidAnalysisResult, error) {
	request.FlowType = "turbulent"
	return fs.AnalyzeFluidFlow(request)
}

// AnalyzeTransitionalFlow performs transitional flow analysis
func (fs *FluidService) AnalyzeTransitionalFlow(request *FluidAnalysisRequest) (*models.FluidAnalysisResult, error) {
	request.FlowType = "transitional"
	return fs.AnalyzeFluidFlow(request)
}

// GetFluidProperties retrieves fluid properties
func (fs *FluidService) GetFluidProperties(fluidName string) (*models.FluidProperties, error) {
	resp, err := fs.httpClient.Get(fs.pythonServiceURL + "/fluid-dynamics/properties/" + fluidName)
	if err != nil {
		return nil, fmt.Errorf("failed to get fluid properties: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get fluid properties, status: %d", resp.StatusCode)
	}

	var properties models.FluidProperties
	if err := json.NewDecoder(resp.Body).Decode(&properties); err != nil {
		return nil, fmt.Errorf("failed to decode fluid properties: %w", err)
	}

	return &properties, nil
}

// GetSolverConfig retrieves solver configuration
func (fs *FluidService) GetSolverConfig(solverName string) (map[string]interface{}, error) {
	resp, err := fs.httpClient.Get(fs.pythonServiceURL + "/fluid-dynamics/solver/" + solverName)
	if err != nil {
		return nil, fmt.Errorf("failed to get solver config: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get solver config, status: %d", resp.StatusCode)
	}

	var config map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&config); err != nil {
		return nil, fmt.Errorf("failed to decode solver config: %w", err)
	}

	return config, nil
}

// CalculateReynoldsNumber calculates Reynolds number
func (fs *FluidService) CalculateReynoldsNumber(velocity, characteristicLength, density, viscosity float64) float64 {
	return (density * velocity * characteristicLength) / viscosity
}

// CalculateFlowRate calculates flow rate from velocity field
func (fs *FluidService) CalculateFlowRate(velocityField []models.Vector3D) float64 {
	if len(velocityField) == 0 {
		return 0.0
	}

	totalVelocity := 0.0
	for _, velocity := range velocityField {
		magnitude := velocity.Magnitude()
		totalVelocity += magnitude
	}

	return totalVelocity / float64(len(velocityField))
}

// CalculatePressureDrop calculates pressure drop
func (fs *FluidService) CalculatePressureDrop(pressureField []float64) float64 {
	if len(pressureField) < 2 {
		return 0.0
	}

	maxPressure := pressureField[0]
	minPressure := pressureField[0]

	for _, pressure := range pressureField {
		if pressure > maxPressure {
			maxPressure = pressure
		}
		if pressure < minPressure {
			minPressure = pressure
		}
	}

	return maxPressure - minPressure
}

// ValidateFluidAnalysisRequest validates fluid analysis request
func (fs *FluidService) ValidateFluidAnalysisRequest(request *FluidAnalysisRequest) error {
	if request.ID == "" {
		return fmt.Errorf("request ID is required")
	}

	if request.FluidProperties == nil {
		return fmt.Errorf("fluid properties are required")
	}

	if len(request.BoundaryConditions) == 0 {
		return fmt.Errorf("at least one boundary condition is required")
	}

	if len(request.Mesh) == 0 {
		return fmt.Errorf("mesh is required")
	}

	// Validate boundary conditions
	hasInlet := false
	hasOutlet := false

	for _, bc := range request.BoundaryConditions {
		switch bc.Type {
		case "inlet":
			hasInlet = true
		case "outlet":
			hasOutlet = true
		}
	}

	if !hasInlet {
		return fmt.Errorf("at least one inlet boundary condition is required")
	}

	if !hasOutlet {
		return fmt.Errorf("at least one outlet boundary condition is required")
	}

	return nil
}

// GetAnalysisHistory retrieves analysis history
func (fs *FluidService) GetAnalysisHistory(limit int) ([]*models.FluidAnalysisResult, error) {
	resp, err := fs.httpClient.Get(fmt.Sprintf("%s/fluid-dynamics/history?limit=%d", fs.pythonServiceURL, limit))
	if err != nil {
		return nil, fmt.Errorf("failed to get analysis history: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get analysis history, status: %d", resp.StatusCode)
	}

	var history []*models.FluidAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&history); err != nil {
		return nil, fmt.Errorf("failed to decode analysis history: %w", err)
	}

	return history, nil
}

// GetAnalysisStatistics retrieves analysis statistics
func (fs *FluidService) GetAnalysisStatistics() (*models.FluidAnalysisStatistics, error) {
	resp, err := fs.httpClient.Get(fs.pythonServiceURL + "/fluid-dynamics/statistics")
	if err != nil {
		return nil, fmt.Errorf("failed to get analysis statistics: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get analysis statistics, status: %d", resp.StatusCode)
	}

	var stats models.FluidAnalysisStatistics
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode analysis statistics: %w", err)
	}

	return &stats, nil
}

// ClearCache clears the analysis cache
func (fs *FluidService) ClearCache() {
	fs.cache = make(map[string]*models.FluidAnalysisResult)
}

// GetCacheSize returns the current cache size
func (fs *FluidService) GetCacheSize() int {
	return len(fs.cache)
}
