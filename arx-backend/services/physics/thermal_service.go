package physics

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arxos/arx-backend/models"
)

// ThermalService handles thermal analysis integration
type ThermalService struct {
	pythonServiceURL string
	httpClient       *http.Client
	cache            map[string]*models.ThermalAnalysisResult
}

// ThermalAnalysisRequest represents a thermal analysis request
type ThermalAnalysisRequest struct {
	ID                 string                             `json:"id"`
	AnalysisType       string                             `json:"analysis_type"`
	HeatTransferTypes  []string                           `json:"heat_transfer_types"`
	Materials          map[string]*models.ThermalMaterial `json:"materials"`
	Geometry           map[string]interface{}             `json:"geometry"`
	BoundaryConditions []*models.ThermalBoundaryCondition `json:"boundary_conditions"`
	HeatSources        []*models.HeatSource               `json:"heat_sources"`
	Mesh               []map[string]interface{}           `json:"mesh"`
	SolverSettings     map[string]interface{}             `json:"solver_settings"`
	InitialConditions  map[string]float64                 `json:"initial_conditions"`
}

// NewThermalService creates a new thermal analysis service
func NewThermalService(pythonServiceURL string) *ThermalService {
	return &ThermalService{
		pythonServiceURL: pythonServiceURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		cache: make(map[string]*models.ThermalAnalysisResult),
	}
}

// AnalyzeThermalBehavior performs thermal analysis
func (ts *ThermalService) AnalyzeThermalBehavior(request *ThermalAnalysisRequest) (*models.ThermalAnalysisResult, error) {
	// Check cache first
	if cached, exists := ts.cache[request.ID]; exists {
		return cached, nil
	}

	// Prepare request for Python service
	pythonRequest := map[string]interface{}{
		"id":                  request.ID,
		"analysis_type":       request.AnalysisType,
		"heat_transfer_types": request.HeatTransferTypes,
		"materials":           request.Materials,
		"geometry":            request.Geometry,
		"boundary_conditions": request.BoundaryConditions,
		"heat_sources":        request.HeatSources,
		"mesh":                request.Mesh,
		"solver_settings":     request.SolverSettings,
		"initial_conditions":  request.InitialConditions,
	}

	// Convert to JSON
	jsonData, err := json.Marshal(pythonRequest)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Send request to Python service
	resp, err := ts.httpClient.Post(
		ts.pythonServiceURL+"/thermal-analysis/analyze",
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
	var result models.ThermalAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Cache result
	ts.cache[request.ID] = &result

	return &result, nil
}

// AnalyzeConduction performs conduction heat transfer analysis
func (ts *ThermalService) AnalyzeConduction(request *ThermalAnalysisRequest) (*models.ThermalAnalysisResult, error) {
	request.HeatTransferTypes = []string{"conduction"}
	return ts.AnalyzeThermalBehavior(request)
}

// AnalyzeConvection performs convection heat transfer analysis
func (ts *ThermalService) AnalyzeConvection(request *ThermalAnalysisRequest) (*models.ThermalAnalysisResult, error) {
	request.HeatTransferTypes = []string{"convection"}
	return ts.AnalyzeThermalBehavior(request)
}

// AnalyzeRadiation performs radiation heat transfer analysis
func (ts *ThermalService) AnalyzeRadiation(request *ThermalAnalysisRequest) (*models.ThermalAnalysisResult, error) {
	request.HeatTransferTypes = []string{"radiation"}
	return ts.AnalyzeThermalBehavior(request)
}

// AnalyzeCombinedHeatTransfer performs combined heat transfer analysis
func (ts *ThermalService) AnalyzeCombinedHeatTransfer(request *ThermalAnalysisRequest) (*models.ThermalAnalysisResult, error) {
	request.HeatTransferTypes = []string{"conduction", "convection", "radiation"}
	return ts.AnalyzeThermalBehavior(request)
}

// GetMaterialProperties retrieves thermal material properties
func (ts *ThermalService) GetMaterialProperties(materialName string) (*models.ThermalMaterial, error) {
	resp, err := ts.httpClient.Get(ts.pythonServiceURL + "/thermal-analysis/materials/" + materialName)
	if err != nil {
		return nil, fmt.Errorf("failed to get material properties: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get material properties, status: %d", resp.StatusCode)
	}

	var material models.ThermalMaterial
	if err := json.NewDecoder(resp.Body).Decode(&material); err != nil {
		return nil, fmt.Errorf("failed to decode material properties: %w", err)
	}

	return &material, nil
}

// GetSolverConfig retrieves solver configuration
func (ts *ThermalService) GetSolverConfig(solverName string) (map[string]interface{}, error) {
	resp, err := ts.httpClient.Get(ts.pythonServiceURL + "/thermal-analysis/solver/" + solverName)
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

// CalculateHeatTransferRate calculates heat transfer rate
func (ts *ThermalService) CalculateHeatTransferRate(heatFluxField []models.Vector3D, area float64) float64 {
	if len(heatFluxField) == 0 {
		return 0.0
	}

	totalHeatFlux := 0.0
	for _, heatFlux := range heatFluxField {
		magnitude := heatFlux.Magnitude()
		totalHeatFlux += magnitude
	}

	averageHeatFlux := totalHeatFlux / float64(len(heatFluxField))
	return averageHeatFlux * area
}

// CalculateThermalEfficiency calculates thermal efficiency
func (ts *ThermalService) CalculateThermalEfficiency(inputPower, outputPower float64) float64 {
	if inputPower <= 0 {
		return 0.0
	}
	return (outputPower / inputPower) * 100.0
}

// CalculateThermalStress calculates thermal stress
func (ts *ThermalService) CalculateThermalStress(temperature, referenceTemp, thermalExpansion, youngsModulus float64) float64 {
	deltaT := temperature - referenceTemp
	thermalStrain := thermalExpansion * deltaT
	return youngsModulus * thermalStrain
}

// ValidateThermalAnalysisRequest validates thermal analysis request
func (ts *ThermalService) ValidateThermalAnalysisRequest(request *ThermalAnalysisRequest) error {
	if request.ID == "" {
		return fmt.Errorf("request ID is required")
	}

	if len(request.Materials) == 0 {
		return fmt.Errorf("at least one material is required")
	}

	if len(request.BoundaryConditions) == 0 {
		return fmt.Errorf("at least one boundary condition is required")
	}

	if len(request.Mesh) == 0 {
		return fmt.Errorf("mesh is required")
	}

	if len(request.HeatTransferTypes) == 0 {
		return fmt.Errorf("at least one heat transfer type is required")
	}

	// Validate heat transfer types
	validTypes := map[string]bool{
		"conduction": true,
		"convection": true,
		"radiation":  true,
		"combined":   true,
	}

	for _, heatTransferType := range request.HeatTransferTypes {
		if !validTypes[heatTransferType] {
			return fmt.Errorf("invalid heat transfer type: %s", heatTransferType)
		}
	}

	return nil
}

// GetAnalysisHistory retrieves analysis history
func (ts *ThermalService) GetAnalysisHistory(limit int) ([]*models.ThermalAnalysisResult, error) {
	resp, err := ts.httpClient.Get(fmt.Sprintf("%s/thermal-analysis/history?limit=%d", ts.pythonServiceURL, limit))
	if err != nil {
		return nil, fmt.Errorf("failed to get analysis history: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get analysis history, status: %d", resp.StatusCode)
	}

	var history []*models.ThermalAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&history); err != nil {
		return nil, fmt.Errorf("failed to decode analysis history: %w", err)
	}

	return history, nil
}

// GetAnalysisStatistics retrieves analysis statistics
func (ts *ThermalService) GetAnalysisStatistics() (*models.ThermalAnalysisStatistics, error) {
	resp, err := ts.httpClient.Get(ts.pythonServiceURL + "/thermal-analysis/statistics")
	if err != nil {
		return nil, fmt.Errorf("failed to get analysis statistics: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get analysis statistics, status: %d", resp.StatusCode)
	}

	var stats models.ThermalAnalysisStatistics
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode analysis statistics: %w", err)
	}

	return &stats, nil
}

// ClearCache clears the analysis cache
func (ts *ThermalService) ClearCache() {
	ts.cache = make(map[string]*models.ThermalAnalysisResult)
}

// GetCacheSize returns the current cache size
func (ts *ThermalService) GetCacheSize() int {
	return len(ts.cache)
}
