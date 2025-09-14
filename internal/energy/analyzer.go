package energy

import (
	"math"
	"time"

	"github.com/joelpate/arxos/pkg/models"
)

// Analyzer performs energy flow analysis on buildings
type Analyzer struct {
	// Energy flow patterns
	flowPatterns map[string]*FlowPattern
}

// FlowPattern represents energy flow through equipment
type FlowPattern struct {
	EquipmentID string
	InputPower  float64
	OutputPower float64
	Efficiency  float64
	Timestamp   time.Time
}

// NewAnalyzer creates a new energy analyzer
func NewAnalyzer() *Analyzer {
	return &Analyzer{
		flowPatterns: make(map[string]*FlowPattern),
	}
}

// AnalyzeEquipment analyzes energy flow for a piece of equipment
func (a *Analyzer) AnalyzeEquipment(eq *models.Equipment) *FlowPattern {
	// Simple energy analysis based on equipment type
	pattern := &FlowPattern{
		EquipmentID: eq.ID,
		Timestamp:   time.Now(),
	}

	switch eq.Type {
	case "HVAC.RTU":
		pattern.InputPower = 5000 // Watts
		pattern.OutputPower = 4500
		pattern.Efficiency = 0.9
	case "Electrical.Panel":
		pattern.InputPower = 10000
		pattern.OutputPower = 9800
		pattern.Efficiency = 0.98
	case "outlet":
		pattern.InputPower = 1500
		pattern.OutputPower = 1450
		pattern.Efficiency = 0.97
	default:
		pattern.InputPower = 1000
		pattern.OutputPower = 950
		pattern.Efficiency = 0.95
	}

	// Degrade efficiency based on equipment status
	if eq.Status == models.StatusDegraded {
		pattern.Efficiency *= 0.8
		pattern.OutputPower = pattern.InputPower * pattern.Efficiency
	} else if eq.Status == models.StatusFailed {
		pattern.Efficiency = 0
		pattern.OutputPower = 0
	}

	a.flowPatterns[eq.ID] = pattern
	return pattern
}

// GetTotalEnergyFlow calculates total energy flow for all analyzed equipment
func (a *Analyzer) GetTotalEnergyFlow() float64 {
	total := 0.0
	for _, pattern := range a.flowPatterns {
		total += pattern.InputPower
	}
	return total
}

// GetAverageEfficiency calculates average efficiency across all equipment
func (a *Analyzer) GetAverageEfficiency() float64 {
	if len(a.flowPatterns) == 0 {
		return 0
	}

	totalEfficiency := 0.0
	for _, pattern := range a.flowPatterns {
		totalEfficiency += pattern.Efficiency
	}
	return totalEfficiency / float64(len(a.flowPatterns))
}

// PredictEnergyUsage predicts future energy usage based on patterns
func (a *Analyzer) PredictEnergyUsage(hours int) float64 {
	currentFlow := a.GetTotalEnergyFlow()
	// Simple linear prediction with some variance
	variance := math.Sin(float64(hours)/24*math.Pi) * 0.2
	return currentFlow * float64(hours) * (1 + variance)
}

// Reset clears all analyzed patterns
func (a *Analyzer) Reset() {
	a.flowPatterns = make(map[string]*FlowPattern)
}