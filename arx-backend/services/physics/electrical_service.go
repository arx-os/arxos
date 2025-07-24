package physics

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"time"

	"github.com/arxos/arx-backend/models"
)

// ElectricalService handles electrical simulation integration
type ElectricalService struct {
	pythonServiceURL string
	httpClient       *http.Client
	cache            map[string]*models.ElectricalAnalysisResult
}

// ElectricalAnalysisRequest represents an electrical analysis request
type ElectricalAnalysisRequest struct {
	ID                 string                                `json:"id"`
	CircuitType        string                                `json:"circuit_type"`
	AnalysisType       string                                `json:"analysis_type"`
	Components         []*models.ElectricalComponent         `json:"components"`
	Materials          map[string]*models.ElectricalMaterial `json:"materials"`
	BoundaryConditions []*models.ElectricalBoundaryCondition `json:"boundary_conditions"`
	Mesh               []map[string]interface{}              `json:"mesh"`
	SolverSettings     map[string]interface{}                `json:"solver_settings"`
	FrequencyRange     *models.FrequencyRange                `json:"frequency_range,omitempty"`
}

// NewElectricalService creates a new electrical simulation service
func NewElectricalService(pythonServiceURL string) *ElectricalService {
	return &ElectricalService{
		pythonServiceURL: pythonServiceURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		cache: make(map[string]*models.ElectricalAnalysisResult),
	}
}

// AnalyzeElectricalCircuit performs electrical circuit analysis
func (es *ElectricalService) AnalyzeElectricalCircuit(request *ElectricalAnalysisRequest) (*models.ElectricalAnalysisResult, error) {
	// Check cache first
	if cached, exists := es.cache[request.ID]; exists {
		return cached, nil
	}

	// Prepare request for Python service
	pythonRequest := map[string]interface{}{
		"id":                  request.ID,
		"circuit_type":        request.CircuitType,
		"analysis_type":       request.AnalysisType,
		"components":          request.Components,
		"materials":           request.Materials,
		"boundary_conditions": request.BoundaryConditions,
		"mesh":                request.Mesh,
		"solver_settings":     request.SolverSettings,
		"frequency_range":     request.FrequencyRange,
	}

	// Convert to JSON
	jsonData, err := json.Marshal(pythonRequest)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Send request to Python service
	resp, err := es.httpClient.Post(
		es.pythonServiceURL+"/electrical-simulation/analyze",
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
	var result models.ElectricalAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Cache result
	es.cache[request.ID] = &result

	return &result, nil
}

// AnalyzeSteadyState performs steady-state electrical analysis
func (es *ElectricalService) AnalyzeSteadyState(request *ElectricalAnalysisRequest) (*models.ElectricalAnalysisResult, error) {
	request.AnalysisType = "steady_state"
	return es.AnalyzeElectricalCircuit(request)
}

// AnalyzeTransient performs transient electrical analysis
func (es *ElectricalService) AnalyzeTransient(request *ElectricalAnalysisRequest) (*models.ElectricalAnalysisResult, error) {
	request.AnalysisType = "transient"
	return es.AnalyzeElectricalCircuit(request)
}

// AnalyzeFrequencyDomain performs frequency domain analysis
func (es *ElectricalService) AnalyzeFrequencyDomain(request *ElectricalAnalysisRequest) (*models.ElectricalAnalysisResult, error) {
	request.AnalysisType = "frequency_domain"
	return es.AnalyzeElectricalCircuit(request)
}

// AnalyzeFault performs fault analysis
func (es *ElectricalService) AnalyzeFault(request *ElectricalAnalysisRequest) (*models.ElectricalAnalysisResult, error) {
	request.AnalysisType = "fault_analysis"
	return es.AnalyzeElectricalCircuit(request)
}

// GetMaterialProperties retrieves electrical material properties
func (es *ElectricalService) GetMaterialProperties(materialName string) (*models.ElectricalMaterial, error) {
	resp, err := es.httpClient.Get(es.pythonServiceURL + "/electrical-simulation/materials/" + materialName)
	if err != nil {
		return nil, fmt.Errorf("failed to get material properties: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get material properties, status: %d", resp.StatusCode)
	}

	var material models.ElectricalMaterial
	if err := json.NewDecoder(resp.Body).Decode(&material); err != nil {
		return nil, fmt.Errorf("failed to decode material properties: %w", err)
	}

	return &material, nil
}

// GetSolverConfig retrieves solver configuration
func (es *ElectricalService) GetSolverConfig(solverName string) (map[string]interface{}, error) {
	resp, err := es.httpClient.Get(es.pythonServiceURL + "/electrical-simulation/solver/" + solverName)
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

// CalculatePower calculates electrical power
func (es *ElectricalService) CalculatePower(voltage, current float64) float64 {
	return voltage * current
}

// CalculatePowerLoss calculates power loss
func (es *ElectricalService) CalculatePowerLoss(current, resistance float64) float64 {
	return current * current * resistance
}

// CalculateEfficiency calculates electrical efficiency
func (es *ElectricalService) CalculateEfficiency(inputPower, outputPower float64) float64 {
	if inputPower <= 0 {
		return 0.0
	}
	return (outputPower / inputPower) * 100.0
}

// CalculateImpedance calculates electrical impedance
func (es *ElectricalService) CalculateImpedance(resistance, reactance float64) float64 {
	return math.Sqrt(resistance*resistance + reactance*reactance)
}

// CalculateVoltageDrop calculates voltage drop
func (es *ElectricalService) CalculateVoltageDrop(current, resistance float64) float64 {
	return current * resistance
}

// ValidateElectricalAnalysisRequest validates electrical analysis request
func (es *ElectricalService) ValidateElectricalAnalysisRequest(request *ElectricalAnalysisRequest) error {
	if request.ID == "" {
		return fmt.Errorf("request ID is required")
	}

	if len(request.Components) == 0 {
		return fmt.Errorf("at least one component is required")
	}

	if len(request.BoundaryConditions) == 0 {
		return fmt.Errorf("at least one boundary condition is required")
	}

	if len(request.Mesh) == 0 {
		return fmt.Errorf("mesh is required")
	}

	// Validate circuit type
	validCircuitTypes := map[string]bool{
		"dc":           true,
		"ac":           true,
		"three_phase":  true,
		"single_phase": true,
	}

	if !validCircuitTypes[request.CircuitType] {
		return fmt.Errorf("invalid circuit type: %s", request.CircuitType)
	}

	// Validate analysis type
	validAnalysisTypes := map[string]bool{
		"steady_state":     true,
		"transient":        true,
		"frequency_domain": true,
		"fault_analysis":   true,
	}

	if !validAnalysisTypes[request.AnalysisType] {
		return fmt.Errorf("invalid analysis type: %s", request.AnalysisType)
	}

	return nil
}

// GetAnalysisHistory retrieves analysis history
func (es *ElectricalService) GetAnalysisHistory(limit int) ([]*models.ElectricalAnalysisResult, error) {
	resp, err := es.httpClient.Get(fmt.Sprintf("%s/electrical-simulation/history?limit=%d", es.pythonServiceURL, limit))
	if err != nil {
		return nil, fmt.Errorf("failed to get analysis history: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get analysis history, status: %d", resp.StatusCode)
	}

	var history []*models.ElectricalAnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&history); err != nil {
		return nil, fmt.Errorf("failed to decode analysis history: %w", err)
	}

	return history, nil
}

// GetAnalysisStatistics retrieves analysis statistics
func (es *ElectricalService) GetAnalysisStatistics() (*models.ElectricalAnalysisStatistics, error) {
	resp, err := es.httpClient.Get(es.pythonServiceURL + "/electrical-simulation/statistics")
	if err != nil {
		return nil, fmt.Errorf("failed to get analysis statistics: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get analysis statistics, status: %d", resp.StatusCode)
	}

	var stats models.ElectricalAnalysisStatistics
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode analysis statistics: %w", err)
	}

	return &stats, nil
}

// ClearCache clears the analysis cache
func (es *ElectricalService) ClearCache() {
	es.cache = make(map[string]*models.ElectricalAnalysisResult)
}

// GetCacheSize returns the current cache size
func (es *ElectricalService) GetCacheSize() int {
	return len(es.cache)
}
