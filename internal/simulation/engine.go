package simulation

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/energy"
	"github.com/arx-os/arxos/internal/maintenance"
	"github.com/arx-os/arxos/internal/particles"
	"github.com/arx-os/arxos/pkg/models"
)

// Engine orchestrates all simulation types
type Engine struct {
	particleSystem *particles.System
	energyAnalyzer *energy.Analyzer
	maintPredictor *maintenance.Predictor
}

// NewEngine creates a new simulation engine
func NewEngine() *Engine {
	return &Engine{
		particleSystem: particles.NewSystem(100, 50), // Default size
		energyAnalyzer: energy.NewAnalyzer(),
		maintPredictor: nil, // Will be set when needed with database
	}
}

// Results contains all simulation outputs
type Results struct {
	Timestamp          time.Time
	BuildingID         string
	TotalEnergyFlow    float64
	AverageEfficiency  float64
	CriticalIssues     []Issue
	Recommendations    []string
	EquipmentAnalysis  map[string]*EquipmentSimulation
}

// EquipmentSimulation contains simulation data for a single equipment
type EquipmentSimulation struct {
	EquipmentID        string
	EnergyFlow         float64
	ParticleLoad       float64
	NextMaintenance    time.Time
	FailureProbability float64
	EfficiencyScore    float64
}

// Issue represents a critical finding from simulations
type Issue struct {
	Severity    string
	Equipment   string
	Description string
	Impact      string
}

// Analyze runs all simulations on a building
func (e *Engine) Analyze(building *models.FloorPlan) (*Results, error) {
	logger.Info("Starting comprehensive simulation for building %s", building.ID)

	results := &Results{
		Timestamp:         time.Now(),
		BuildingID:        building.ID,
		EquipmentAnalysis: make(map[string]*EquipmentSimulation),
		CriticalIssues:    []Issue{},
		Recommendations:   []string{},
	}

	// Run particle simulation
	if err := e.runParticleSimulation(building, results); err != nil {
		logger.Warn("Particle simulation failed: %v", err)
	}

	// Run energy flow analysis
	if err := e.runEnergyAnalysis(building, results); err != nil {
		logger.Warn("Energy analysis failed: %v", err)
	}

	// Run predictive maintenance
	if err := e.runMaintenancePrediction(building, results); err != nil {
		logger.Warn("Maintenance prediction failed: %v", err)
	}

	// Analyze combined results
	e.analyzeResults(results)

	logger.Info("Simulation complete: %d issues found, efficiency: %.2f%%",
		len(results.CriticalIssues), results.AverageEfficiency*100)

	return results, nil
}

func (e *Engine) runParticleSimulation(building *models.FloorPlan, results *Results) error {
	logger.Debug("Running particle simulation...")

	// Initialize particle system with building layout
	e.particleSystem.Initialize(len(building.Equipment))

	// Run simulation steps
	for i := 0; i < 100; i++ {
		e.particleSystem.Step(0.1)
	}

	// Extract particle loads for each equipment
	for i, eq := range building.Equipment {
		load := e.particleSystem.GetLoadAt(i)

		if sim, ok := results.EquipmentAnalysis[eq.ID]; ok {
			sim.ParticleLoad = load
		} else {
			results.EquipmentAnalysis[eq.ID] = &EquipmentSimulation{
				EquipmentID:  eq.ID,
				ParticleLoad: load,
			}
		}

		// Flag high particle loads
		if load > 0.8 {
			results.CriticalIssues = append(results.CriticalIssues, Issue{
				Severity:    "HIGH",
				Equipment:   eq.ID,
				Description: fmt.Sprintf("High particle load detected: %.2f", load),
				Impact:      "Potential airflow blockage or filter replacement needed",
			})
		}
	}

	return nil
}

func (e *Engine) runEnergyAnalysis(building *models.FloorPlan, results *Results) error {
	logger.Debug("Running energy flow analysis...")

	// Analyze energy flow through equipment
	e.energyAnalyzer.Reset()
	for _, eq := range building.Equipment {
		pattern := e.energyAnalyzer.AnalyzeEquipment(eq)

		if sim, ok := results.EquipmentAnalysis[eq.ID]; ok {
			sim.EnergyFlow = pattern.InputPower
			sim.EfficiencyScore = pattern.Efficiency
		} else {
			results.EquipmentAnalysis[eq.ID] = &EquipmentSimulation{
				EquipmentID:     eq.ID,
				EnergyFlow:      pattern.InputPower,
				EfficiencyScore: pattern.Efficiency,
			}
		}

		// Flag abnormal energy consumption
		if pattern.InputPower > 100000 { // 100kW threshold in watts
			results.CriticalIssues = append(results.CriticalIssues, Issue{
				Severity:    "MEDIUM",
				Equipment:   eq.ID,
				Description: fmt.Sprintf("High energy consumption: %.2f kW", pattern.InputPower/1000),
				Impact:      "Increased operating costs",
			})
		}
	}

	results.TotalEnergyFlow = e.energyAnalyzer.GetTotalEnergyFlow()
	results.AverageEfficiency = e.energyAnalyzer.GetAverageEfficiency()

	return nil
}

func (e *Engine) runMaintenancePrediction(building *models.FloorPlan, results *Results) error {
	logger.Debug("Running predictive maintenance analysis...")

	if e.maintPredictor == nil {
		// Use simple heuristics if predictor not available
		for _, eq := range building.Equipment {
			// Simple maintenance prediction based on status
			nextMaint := time.Now().Add(30 * 24 * time.Hour) // 30 days default
			failProb := 0.1 // 10% base probability

			if eq.Status == models.StatusDegraded {
				nextMaint = time.Now().Add(7 * 24 * time.Hour) // 7 days if degraded
				failProb = 0.4
			} else if eq.Status == models.StatusFailed {
				nextMaint = time.Now() // Immediate
				failProb = 1.0
			}

			if sim, ok := results.EquipmentAnalysis[eq.ID]; ok {
				sim.NextMaintenance = nextMaint
				sim.FailureProbability = failProb
			} else {
				results.EquipmentAnalysis[eq.ID] = &EquipmentSimulation{
					EquipmentID:        eq.ID,
					NextMaintenance:    nextMaint,
					FailureProbability: failProb,
				}
			}
		}
		return nil
	}

	for _, eq := range building.Equipment {
		// Use predictor if available
		health, err := e.maintPredictor.AnalyzeEquipmentHealth(context.Background(), eq.ID)
		if err != nil {
			// Fallback to simple heuristics
			nextDate := time.Now().Add(30 * 24 * time.Hour)
			health = &maintenance.EquipmentHealth{
				NextScheduledDate:  &nextDate,
				FailureProbability: 0.1,
			}
		}

		nextMaint := time.Now().Add(30 * 24 * time.Hour) // Default
		if health.NextScheduledDate != nil {
			nextMaint = *health.NextScheduledDate
		}
		failProb := health.FailureProbability

		if sim, ok := results.EquipmentAnalysis[eq.ID]; ok {
			sim.NextMaintenance = nextMaint
			sim.FailureProbability = failProb
		} else {
			results.EquipmentAnalysis[eq.ID] = &EquipmentSimulation{
				EquipmentID:        eq.ID,
				NextMaintenance:    nextMaint,
				FailureProbability: failProb,
			}
		}

		// Flag high failure risk
		if failProb > 0.3 {
			results.CriticalIssues = append(results.CriticalIssues, Issue{
				Severity:    "CRITICAL",
				Equipment:   eq.ID,
				Description: fmt.Sprintf("High failure risk: %.1f%%", failProb*100),
				Impact:      "Potential equipment failure within 30 days",
			})

			results.Recommendations = append(results.Recommendations,
				fmt.Sprintf("Schedule immediate maintenance for %s", eq.ID))
		}
	}

	return nil
}

func (e *Engine) analyzeResults(results *Results) {
	// Calculate overall efficiency
	totalEfficiency := 0.0
	count := 0

	for _, sim := range results.EquipmentAnalysis {
		// Simple efficiency calculation based on energy and particle load
		efficiency := 1.0 - (sim.ParticleLoad * 0.3) - (sim.FailureProbability * 0.5)
		if sim.EnergyFlow > 0 {
			efficiency *= (50.0 / sim.EnergyFlow) // Normalize by expected consumption
		}

		sim.EfficiencyScore = efficiency
		totalEfficiency += efficiency
		count++
	}

	if count > 0 {
		results.AverageEfficiency = totalEfficiency / float64(count)
	}

	// Add general recommendations
	if results.AverageEfficiency < 0.7 {
		results.Recommendations = append(results.Recommendations,
			"Overall building efficiency is below optimal. Consider comprehensive maintenance review.")
	}

	if len(results.CriticalIssues) > 5 {
		results.Recommendations = append(results.Recommendations,
			"Multiple critical issues detected. Prioritize maintenance for high-risk equipment.")
	}
}