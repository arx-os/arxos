package analytics

import (
	"fmt"
	"math"
	"math/rand"
	"strings"
	
	"github.com/joelpate/arxos/internal/connections"
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/internal/particles"
	"github.com/joelpate/arxos/pkg/models"
)

// FailurePropagation simulates and visualizes cascading failures
type FailurePropagation struct {
	connections   *connections.Manager
	particleSystem *particles.System
	failureMap    map[string]*FailureNode
	propagationSpeed float64
}

// FailureNode represents a node in the failure graph
type FailureNode struct {
	Equipment       *models.Equipment
	FailureProbability float64
	FailureTime        float64
	IsFailed           bool
	CascadeFrom        string
	AffectedSystems    []string
}

// NewFailurePropagation creates a new failure propagation analyzer
func NewFailurePropagation(connMgr *connections.Manager) *FailurePropagation {
	return &FailurePropagation{
		connections:      connMgr,
		particleSystem:   particles.NewSystem(80, 30),
		failureMap:       make(map[string]*FailureNode),
		propagationSpeed: 1.0,
	}
}

// SimulateFailure simulates a failure starting from a specific equipment
func (fp *FailurePropagation) SimulateFailure(startEquipmentID string, duration float64) (*FailureReport, error) {
	logger.Info("Starting failure simulation from: %s", startEquipmentID)
	
	// Initialize failure map
	fp.initializeFailureMap()
	
	// Mark initial failure
	if node, exists := fp.failureMap[startEquipmentID]; exists {
		node.IsFailed = true
		node.FailureTime = 0
		node.FailureProbability = 1.0
	} else {
		return nil, fmt.Errorf("equipment %s not found", startEquipmentID)
	}
	
	// Simulate propagation over time
	timeStep := 0.1
	currentTime := 0.0
	
	report := &FailureReport{
		InitialFailure: startEquipmentID,
		Timeline:       []FailureEvent{},
		TotalAffected:  1,
	}
	
	// Add initial failure event
	report.Timeline = append(report.Timeline, FailureEvent{
		Time:        0,
		EquipmentID: startEquipmentID,
		Type:        "Initial Failure",
		Probability: 1.0,
	})
	
	for currentTime < duration {
		newFailures := fp.propagateStep(currentTime)
		
		for _, failure := range newFailures {
			report.Timeline = append(report.Timeline, failure)
			report.TotalAffected++
		}
		
		currentTime += timeStep
	}
	
	// Generate impact analysis
	report.ImpactAnalysis = fp.analyzeImpact()
	
	// Generate visualization
	report.Visualization = fp.visualizeFailure()
	
	logger.Info("Failure simulation complete: %d equipment affected", report.TotalAffected)
	
	return report, nil
}

// propagateStep simulates one time step of failure propagation
func (fp *FailurePropagation) propagateStep(currentTime float64) []FailureEvent {
	newFailures := []FailureEvent{}
	
	// Check each failed equipment for downstream effects
	for id, node := range fp.failureMap {
		if !node.IsFailed {
			continue
		}
		
		// Get downstream connections
		downstream := fp.connections.GetDownstream(id)
		
		for _, connectedID := range downstream {
			connectedNode, exists := fp.failureMap[connectedID]
			if !exists || connectedNode.IsFailed {
				continue
			}
			
			// Calculate failure probability based on connection type and distance
			failProb := fp.calculateFailureProbability(node, connectedNode, currentTime)
			
			// Random failure check
			if rand.Float64() < failProb {
				connectedNode.IsFailed = true
				connectedNode.FailureTime = currentTime
				connectedNode.FailureProbability = failProb
				connectedNode.CascadeFrom = id
				
				newFailures = append(newFailures, FailureEvent{
					Time:        currentTime,
					EquipmentID: connectedID,
					Type:        "Cascading Failure",
					Probability: failProb,
					CausedBy:    id,
				})
			}
		}
	}
	
	return newFailures
}

// calculateFailureProbability calculates the probability of cascade failure
func (fp *FailurePropagation) calculateFailureProbability(source, target *FailureNode, timeSinceFailure float64) float64 {
	baseProbability := 0.0
	
	// Connection type affects probability
	connType := fp.connections.GetConnectionType(source.Equipment.ID, target.Equipment.ID)
	switch connType {
	case "power":
		baseProbability = 0.8 // High probability for power failures
	case "data":
		baseProbability = 0.3 // Lower for data connections
	case "control":
		baseProbability = 0.6 // Medium for control systems
	case "hvac":
		baseProbability = 0.4
	case "plumbing":
		baseProbability = 0.2
	default:
		baseProbability = 0.1
	}
	
	// Equipment type resilience
	resilience := fp.getEquipmentResilience(target.Equipment.Type)
	baseProbability *= (1.0 - resilience)
	
	// Time decay - failures become less likely over time
	timeDecay := math.Exp(-timeSinceFailure / 10.0)
	baseProbability *= timeDecay
	
	// Distance factor (if equipment has locations)
	if source.Equipment.Location.X != 0 && target.Equipment.Location.X != 0 {
		distance := fp.calculateDistance(source.Equipment.Location, target.Equipment.Location)
		distanceFactor := math.Exp(-distance / 20.0)
		baseProbability *= distanceFactor
	}
	
	return math.Min(baseProbability, 1.0)
}

// getEquipmentResilience returns resilience factor for equipment type
func (fp *FailurePropagation) getEquipmentResilience(equipType string) float64 {
	resilience := map[string]float64{
		"panel":        0.7, // Panels are resilient
		"mdf":          0.8, // Main distribution frames are very resilient
		"ups":          0.9, // UPS systems are highly resilient
		"outlet":       0.1, // Outlets have low resilience
		"switch":       0.3,
		"access_point": 0.2,
		"server":       0.4,
	}
	
	if r, exists := resilience[equipType]; exists {
		return r
	}
	return 0.3 // Default resilience
}

// visualizeFailure creates ASCII visualization of failure propagation
func (fp *FailurePropagation) visualizeFailure() string {
	var viz strings.Builder
	
	viz.WriteString("\nFailure Propagation Visualization\n")
	viz.WriteString("==================================\n\n")
	
	// Create particle simulation of failure spread
	fp.particleSystem.Clear()
	
	// Add failure particles
	for _, node := range fp.failureMap {
		if !node.IsFailed {
			continue
		}
		
		// Spawn failure particles at equipment location
		x := node.Equipment.Location.X
		y := node.Equipment.Location.Y
		
		// Scale to particle system coordinates
		x = x * 2
		y = y * 2
		
		// Spawn different particles based on failure time
		particleType := particles.TypeSmoke
		if node.FailureTime == 0 {
			particleType = particles.TypeHeat // Initial failure
		} else if node.FailureTime < 5 {
			particleType = particles.TypeElectric // Early cascade
		}
		
		// Spawn 5 particles at once
		fp.particleSystem.Spawn(x, y, particleType, 5)
		
		// Add connection particles showing propagation paths
		if node.CascadeFrom != "" {
			if source, exists := fp.failureMap[node.CascadeFrom]; exists {
				fp.drawPropagationPath(source.Equipment.Location, node.Equipment.Location)
			}
		}
	}
	
	// Update particle system for animation effect
	for i := 0; i < 10; i++ {
		fp.particleSystem.Update()
	}
	
	// Render particle visualization
	rendered := fp.particleSystem.Render()
	for _, row := range rendered {
		viz.WriteString(string(row))
		viz.WriteString("\n")
	}
	viz.WriteString("\n")
	
	// Add legend
	viz.WriteString("Legend:\n")
	viz.WriteString("  🔥 Initial Failure\n")
	viz.WriteString("  ⚡ Electrical Cascade\n")
	viz.WriteString("  💨 System Failure\n")
	viz.WriteString("  · · Propagation Path\n\n")
	
	// Add timeline visualization
	viz.WriteString("Failure Timeline:\n")
	viz.WriteString("─────────────────\n")
	
	// Group failures by time
	timeGroups := make(map[int][]string)
	for id, node := range fp.failureMap {
		if node.IsFailed {
			timeGroup := int(node.FailureTime)
			timeGroups[timeGroup] = append(timeGroups[timeGroup], id)
		}
	}
	
	// Display timeline
	for t := 0; t <= 10; t++ {
		if failures, exists := timeGroups[t]; exists {
			viz.WriteString(fmt.Sprintf("T+%02d: ", t))
			for i, id := range failures {
				if i > 0 {
					viz.WriteString(", ")
				}
				viz.WriteString(id)
			}
			viz.WriteString("\n")
		}
	}
	
	return viz.String()
}

// drawPropagationPath draws particle path between two points
func (fp *FailurePropagation) drawPropagationPath(from, to models.Point) {
	steps := 10
	for i := 0; i <= steps; i++ {
		t := float64(i) / float64(steps)
		x := from.X + (to.X-from.X)*t
		y := from.Y + (to.Y-from.Y)*t
		
		// Add small particle at each step
		fp.particleSystem.Spawn(x*2, y*2, particles.TypeAir, 1)
	}
}

// analyzeImpact analyzes the impact of the failure cascade
func (fp *FailurePropagation) analyzeImpact() ImpactAnalysis {
	analysis := ImpactAnalysis{
		AffectedByType:     make(map[string]int),
		AffectedBySeverity: make(map[string]int),
		CriticalPaths:      []CriticalPath{},
		EstimatedDowntime:  0,
		EstimatedCost:      0,
	}
	
	// Count affected equipment by type
	for _, node := range fp.failureMap {
		if node.IsFailed {
			analysis.AffectedByType[node.Equipment.Type]++
			
			// Categorize by severity
			if node.FailureTime == 0 {
				analysis.AffectedBySeverity["Critical"]++
			} else if node.FailureTime < 5 {
				analysis.AffectedBySeverity["High"]++
			} else if node.FailureTime < 10 {
				analysis.AffectedBySeverity["Medium"]++
			} else {
				analysis.AffectedBySeverity["Low"]++
			}
			
			// Estimate downtime and cost
			analysis.EstimatedDowntime += fp.estimateDowntime(node.Equipment.Type)
			analysis.EstimatedCost += fp.estimateCost(node.Equipment.Type)
		}
	}
	
	// Identify critical paths
	analysis.CriticalPaths = fp.findCriticalPaths()
	
	return analysis
}

// estimateDowntime estimates downtime hours for equipment type
func (fp *FailurePropagation) estimateDowntime(equipType string) float64 {
	downtime := map[string]float64{
		"panel":        24.0,
		"mdf":          48.0,
		"server":       12.0,
		"switch":       8.0,
		"outlet":       2.0,
		"access_point": 4.0,
	}
	
	if d, exists := downtime[equipType]; exists {
		return d
	}
	return 4.0
}

// estimateCost estimates repair cost for equipment type
func (fp *FailurePropagation) estimateCost(equipType string) float64 {
	cost := map[string]float64{
		"panel":        5000.0,
		"mdf":          15000.0,
		"server":       8000.0,
		"switch":       2000.0,
		"outlet":       150.0,
		"access_point": 500.0,
	}
	
	if c, exists := cost[equipType]; exists {
		return c
	}
	return 1000.0
}

// findCriticalPaths identifies critical failure paths
func (fp *FailurePropagation) findCriticalPaths() []CriticalPath {
	paths := []CriticalPath{}
	
	// Find chains of failures
	for id, node := range fp.failureMap {
		if !node.IsFailed || node.CascadeFrom == "" {
			continue
		}
		
		// Trace back to origin
		path := []string{id}
		current := node.CascadeFrom
		
		for current != "" {
			path = append([]string{current}, path...)
			if parent, exists := fp.failureMap[current]; exists {
				current = parent.CascadeFrom
			} else {
				break
			}
		}
		
		if len(path) > 2 {
			paths = append(paths, CriticalPath{
				Path:   path,
				Length: len(path),
				Risk:   node.FailureProbability,
			})
		}
	}
	
	return paths
}

// initializeFailureMap sets up the failure tracking map
func (fp *FailurePropagation) initializeFailureMap() {
	// This would be populated from actual equipment data
	// For now, using sample data
	fp.failureMap = make(map[string]*FailureNode)
}

// calculateDistance calculates distance between two points
func (fp *FailurePropagation) calculateDistance(p1, p2 models.Point) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	return math.Sqrt(dx*dx + dy*dy)
}

// AnalyzeSystemResilience analyzes overall system resilience
func (fp *FailurePropagation) AnalyzeSystemResilience() *ResilienceReport {
	report := &ResilienceReport{
		OverallScore:     0,
		Vulnerabilities:  []Vulnerability{},
		Recommendations:  []string{},
		RedundancyMap:    make(map[string]int),
	}
	
	// Analyze redundancy
	for id := range fp.failureMap {
		upstream := fp.connections.GetUpstream(id)
		report.RedundancyMap[id] = len(upstream)
		
		if len(upstream) < 2 {
			report.Vulnerabilities = append(report.Vulnerabilities, Vulnerability{
				EquipmentID: id,
				Type:        "Single Point of Failure",
				Severity:    "High",
				Description: fmt.Sprintf("Equipment %s has only %d upstream connection(s)", id, len(upstream)),
			})
		}
	}
	
	// Calculate overall resilience score
	totalEquipment := len(fp.failureMap)
	redundantEquipment := 0
	for _, redundancy := range report.RedundancyMap {
		if redundancy >= 2 {
			redundantEquipment++
		}
	}
	
	if totalEquipment > 0 {
		report.OverallScore = float64(redundantEquipment) / float64(totalEquipment)
	}
	
	// Generate recommendations
	if report.OverallScore < 0.5 {
		report.Recommendations = append(report.Recommendations, 
			"Critical: System has low redundancy. Consider adding backup power sources.")
	}
	
	if len(report.Vulnerabilities) > 5 {
		report.Recommendations = append(report.Recommendations,
			"Multiple single points of failure detected. Implement redundant connections.")
	}
	
	return report
}

// Data structures

type FailureReport struct {
	InitialFailure string
	Timeline       []FailureEvent
	TotalAffected  int
	ImpactAnalysis ImpactAnalysis
	Visualization  string
}

type FailureEvent struct {
	Time        float64
	EquipmentID string
	Type        string
	Probability float64
	CausedBy    string
}

type ImpactAnalysis struct {
	AffectedByType     map[string]int
	AffectedBySeverity map[string]int
	CriticalPaths      []CriticalPath
	EstimatedDowntime  float64
	EstimatedCost      float64
}

type CriticalPath struct {
	Path   []string
	Length int
	Risk   float64
}

type ResilienceReport struct {
	OverallScore    float64
	Vulnerabilities []Vulnerability
	Recommendations []string
	RedundancyMap   map[string]int
}

type Vulnerability struct {
	EquipmentID string
	Type        string
	Severity    string
	Description string
}