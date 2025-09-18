// Package energy implements energy flow modeling for building systems
package energy

import (
	"fmt"
	"math"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/connections"
	"github.com/arx-os/arxos/pkg/models"
)

// FlowType represents different types of energy flow
type FlowType string

const (
	FlowElectrical FlowType = "electrical"
	FlowThermal    FlowType = "thermal"
	FlowFluid      FlowType = "fluid"
	FlowData       FlowType = "data"
)

// FlowSystem models energy flow through building systems
type FlowSystem struct {
	nodes       map[string]*FlowNode
	edges       map[string]*FlowEdge
	connManager *connections.Manager
	flowType    FlowType
}

// FlowNode represents a point in the energy network
type FlowNode struct {
	ID         string
	Equipment  *models.Equipment
	Potential  float64 // Voltage for electrical, Temperature for thermal, Pressure for fluid
	Flow       float64 // Current for electrical, Heat flux for thermal, Flow rate for fluid
	Capacity   float64 // Maximum flow capacity
	Resistance float64 // Resistance to flow
	IsSource   bool    // True for generators/sources
	IsSink     bool    // True for loads/sinks
	X, Y       float64 // Position for visualization
}

// FlowEdge represents a connection between nodes
type FlowEdge struct {
	ID         string
	FromNode   string
	ToNode     string
	Flow       float64 // Current flow through edge
	Capacity   float64 // Maximum flow capacity
	Resistance float64 // Resistance of connection
	Length     float64 // Physical length (affects resistance)
	Active     bool    // Whether flow is currently active
}

// NewFlowSystem creates a new energy flow system
func NewFlowSystem(flowType FlowType, connManager *connections.Manager) *FlowSystem {
	return &FlowSystem{
		nodes:       make(map[string]*FlowNode),
		edges:       make(map[string]*FlowEdge),
		connManager: connManager,
		flowType:    flowType,
	}
}

// AddNode adds a flow node to the system
func (fs *FlowSystem) AddNode(equipment *models.Equipment, isSource, isSink bool) error {
	if _, exists := fs.nodes[equipment.ID]; exists {
		return fmt.Errorf("node %s already exists", equipment.ID)
	}

	node := &FlowNode{
		ID:        equipment.ID,
		Equipment: equipment,
		IsSource:  isSource,
		IsSink:    isSink,
		X:         equipment.Location.X,
		Y:         equipment.Location.Y,
	}

	// Set default values based on equipment type and flow type
	fs.setNodeDefaults(node)

	fs.nodes[equipment.ID] = node
	logger.Debug("Added flow node: %s (source=%v, sink=%v)", equipment.ID, isSource, isSink)
	return nil
}

// AddEdge adds a flow edge between nodes
func (fs *FlowSystem) AddEdge(fromID, toID string, capacity, resistance float64) error {
	if _, exists := fs.nodes[fromID]; !exists {
		return fmt.Errorf("source node %s not found", fromID)
	}
	if _, exists := fs.nodes[toID]; !exists {
		return fmt.Errorf("target node %s not found", toID)
	}

	edgeID := fmt.Sprintf("%s->%s", fromID, toID)
	edge := &FlowEdge{
		ID:         edgeID,
		FromNode:   fromID,
		ToNode:     toID,
		Capacity:   capacity,
		Resistance: resistance,
		Active:     true,
	}

	// Calculate length from node positions
	from := fs.nodes[fromID]
	to := fs.nodes[toID]
	edge.Length = fs.calculateDistance(from, to)

	fs.edges[edgeID] = edge
	logger.Debug("Added flow edge: %s (cap=%.2f, res=%.2f)", edgeID, capacity, resistance)
	return nil
}

// Simulate runs the energy flow simulation
func (fs *FlowSystem) Simulate() (*FlowResult, error) {
	result := &FlowResult{
		Nodes:      make(map[string]NodeState),
		Edges:      make(map[string]EdgeState),
		TotalFlow:  0,
		TotalLoss:  0,
		Efficiency: 0,
	}

	switch fs.flowType {
	case FlowElectrical:
		fs.simulateElectrical(result)
	case FlowThermal:
		fs.simulateThermal(result)
	case FlowFluid:
		fs.simulateFluid(result)
	default:
		return nil, fmt.Errorf("unsupported flow type: %s", fs.flowType)
	}

	// Calculate efficiency
	if result.TotalFlow > 0 {
		result.Efficiency = (result.TotalFlow - result.TotalLoss) / result.TotalFlow * 100
	}

	return result, nil
}

// simulateElectrical implements electrical power flow using Kirchhoff's laws
func (fs *FlowSystem) simulateElectrical(result *FlowResult) {
	// Simplified DC power flow calculation
	// In real implementation, would use Newton-Raphson or similar for AC

	// Find all sources and sinks
	sources := []*FlowNode{}
	sinks := []*FlowNode{}
	for _, node := range fs.nodes {
		if node.IsSource {
			sources = append(sources, node)
			node.Potential = 120.0 // Standard voltage for sources
		}
		if node.IsSink {
			sinks = append(sinks, node)
		}
	}

	// Simple voltage divider network simulation
	for _, edge := range fs.edges {
		from := fs.nodes[edge.FromNode]
		to := fs.nodes[edge.ToNode]

		if from.IsSource && to.IsSink {
			// Direct source to sink connection
			voltageDrop := edge.Resistance * edge.Flow
			current := (from.Potential - voltageDrop) / edge.Resistance

			// Apply Ohm's law: V = I * R
			if current > edge.Capacity {
				current = edge.Capacity // Limit to capacity
			}

			edge.Flow = current
			powerLoss := current * current * edge.Resistance // I²R losses

			// Update result
			result.Edges[edge.ID] = EdgeState{
				Flow:     current,
				Loss:     powerLoss,
				Utilized: (current / edge.Capacity) * 100,
			}

			result.TotalFlow += current * from.Potential // Power = V * I
			result.TotalLoss += powerLoss
		}
	}

	// Update node states
	for _, node := range fs.nodes {
		state := NodeState{
			Potential:   node.Potential,
			Flow:        node.Flow,
			Utilization: 0,
		}

		if node.Capacity > 0 {
			state.Utilization = (node.Flow / node.Capacity) * 100
		}

		result.Nodes[node.ID] = state
	}
}

// simulateThermal implements heat flow simulation
func (fs *FlowSystem) simulateThermal(result *FlowResult) {
	// Simplified heat transfer using thermal resistance network

	// Set source temperatures (e.g., HVAC units)
	for _, node := range fs.nodes {
		if node.IsSource {
			node.Potential = 72.0 // Target temperature in Fahrenheit
		}
	}

	// Heat flow calculation: Q = ΔT / R
	for _, edge := range fs.edges {
		from := fs.nodes[edge.FromNode]
		to := fs.nodes[edge.ToNode]

		tempDiff := from.Potential - to.Potential
		heatFlow := tempDiff / edge.Resistance

		if math.Abs(heatFlow) > edge.Capacity {
			if heatFlow > 0 {
				heatFlow = edge.Capacity
			} else {
				heatFlow = -edge.Capacity
			}
		}

		edge.Flow = heatFlow

		// Update result
		result.Edges[edge.ID] = EdgeState{
			Flow:     heatFlow,
			Loss:     math.Abs(heatFlow) * 0.1, // 10% heat loss assumption
			Utilized: (math.Abs(heatFlow) / edge.Capacity) * 100,
		}

		result.TotalFlow += math.Abs(heatFlow)
		result.TotalLoss += math.Abs(heatFlow) * 0.1
	}
}

// simulateFluid implements fluid flow simulation
func (fs *FlowSystem) simulateFluid(result *FlowResult) {
	// Simplified fluid flow using Bernoulli's equation

	// Set source pressures (e.g., pumps)
	for _, node := range fs.nodes {
		if node.IsSource {
			node.Potential = 50.0 // PSI
		}
	}

	// Flow rate: Q = ΔP / R (simplified)
	for _, edge := range fs.edges {
		from := fs.nodes[edge.FromNode]
		to := fs.nodes[edge.ToNode]

		pressureDiff := from.Potential - to.Potential
		flowRate := pressureDiff / edge.Resistance

		if flowRate > edge.Capacity {
			flowRate = edge.Capacity
		}

		edge.Flow = flowRate
		frictionLoss := flowRate * edge.Resistance * 0.05 // Friction losses

		// Update result
		result.Edges[edge.ID] = EdgeState{
			Flow:     flowRate,
			Loss:     frictionLoss,
			Utilized: (flowRate / edge.Capacity) * 100,
		}

		result.TotalFlow += flowRate
		result.TotalLoss += frictionLoss
	}
}

// setNodeDefaults sets default values based on equipment type
func (fs *FlowSystem) setNodeDefaults(node *FlowNode) {
	switch fs.flowType {
	case FlowElectrical:
		switch node.Equipment.Type {
		case "panel":
			node.Capacity = 200.0  // Amps
			node.Resistance = 0.01 // Ohms
		case "outlet":
			node.Capacity = 20.0
			node.Resistance = 0.1
		case "breaker":
			node.Capacity = 30.0
			node.Resistance = 0.05
		default:
			node.Capacity = 10.0
			node.Resistance = 1.0
		}

	case FlowThermal:
		switch node.Equipment.Type {
		case "hvac":
			node.Capacity = 50000.0 // BTU/hr
			node.Resistance = 0.1
		case "vent":
			node.Capacity = 500.0
			node.Resistance = 1.0
		default:
			node.Capacity = 100.0
			node.Resistance = 5.0
		}

	case FlowFluid:
		switch node.Equipment.Type {
		case "pump":
			node.Capacity = 100.0 // GPM
			node.Resistance = 0.1
		case "valve":
			node.Capacity = 50.0
			node.Resistance = 0.5
		default:
			node.Capacity = 10.0
			node.Resistance = 1.0
		}
	}
}

// calculateDistance calculates distance between two nodes
func (fs *FlowSystem) calculateDistance(from, to *FlowNode) float64 {
	dx := to.X - from.X
	dy := to.Y - from.Y
	return math.Sqrt(dx*dx + dy*dy)
}

// GetFlowPath returns the flow intensity along a path
func (fs *FlowSystem) GetFlowPath(fromID, toID string) ([]FlowPoint, error) {
	path, err := fs.connManager.FindPath(fromID, toID)
	if err != nil {
		return nil, err
	}

	points := make([]FlowPoint, 0, len(path))
	for i := 0; i < len(path)-1; i++ {
		edgeID := fmt.Sprintf("%s->%s", path[i], path[i+1])
		if edge, exists := fs.edges[edgeID]; exists {
			node := fs.nodes[path[i]]
			points = append(points, FlowPoint{
				X:         node.X,
				Y:         node.Y,
				Intensity: edge.Flow,
				Direction: fs.getFlowDirection(node, fs.nodes[path[i+1]]),
			})
		}
	}

	return points, nil
}

// getFlowDirection calculates flow direction between nodes
func (fs *FlowSystem) getFlowDirection(from, to *FlowNode) float64 {
	return math.Atan2(to.Y-from.Y, to.X-from.X)
}

// FlowResult contains simulation results
type FlowResult struct {
	Nodes      map[string]NodeState
	Edges      map[string]EdgeState
	TotalFlow  float64
	TotalLoss  float64
	Efficiency float64
}

// NodeState represents the state of a node after simulation
type NodeState struct {
	Potential   float64 // Voltage/Temperature/Pressure
	Flow        float64 // Current/Heat/Flow through node
	Utilization float64 // Percentage of capacity used
}

// EdgeState represents the state of an edge after simulation
type EdgeState struct {
	Flow     float64 // Flow through edge
	Loss     float64 // Energy loss in edge
	Utilized float64 // Percentage of capacity used
}

// FlowPoint represents a point in a flow path for visualization
type FlowPoint struct {
	X, Y      float64
	Intensity float64
	Direction float64 // Angle in radians
}
