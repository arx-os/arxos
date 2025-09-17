package rendering

import (
	"math"
	
	"github.com/arx-os/arxos/internal/energy"
)

// EnergyLayer visualizes energy flow through the building
type EnergyLayer struct {
	flowSystem *energy.FlowSystem
	flowResult *energy.FlowResult
	visible    bool
	dirty      []Region
	animFrame  int
	flowType   energy.FlowType
}

// NewEnergyLayer creates a new energy flow visualization layer
func NewEnergyLayer(flowSystem *energy.FlowSystem) *EnergyLayer {
	return &EnergyLayer{
		flowSystem: flowSystem,
		visible:    true,
		dirty:      []Region{},
		animFrame:  0,
		flowType:   energy.FlowElectrical,
	}
}

// Render produces the ASCII representation of energy flow
func (e *EnergyLayer) Render(viewport Viewport) [][]rune {
	// Initialize render buffer
	buffer := make([][]rune, viewport.Height)
	for i := range buffer {
		buffer[i] = make([]rune, viewport.Width)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}
	
	if !e.visible || e.flowResult == nil {
		return buffer
	}
	
	// Render flow edges
	for edgeID, state := range e.flowResult.Edges {
		e.renderFlowEdge(buffer, edgeID, state, viewport)
	}
	
	// Render flow intensity at nodes
	for nodeID, state := range e.flowResult.Nodes {
		e.renderFlowNode(buffer, nodeID, state, viewport)
	}
	
	return buffer
}

func (e *EnergyLayer) renderFlowEdge(buffer [][]rune, edgeID string, state energy.EdgeState, vp Viewport) {
	// Parse edge ID to get from and to nodes
	// Edge ID format: "nodeA->nodeB"
	
	// For visualization, we'll show flow intensity using different characters
	_ = e.getFlowCharacter(state.Flow, state.Utilized)
	
	// In a real implementation, we'd trace the path between nodes
	// For now, we'll just mark flow intensity indicators
}

func (e *EnergyLayer) renderFlowNode(buffer [][]rune, nodeID string, state energy.NodeState, vp Viewport) {
	// This would get the actual node position from the flow system
	// For now, using placeholder logic
	
	// Render based on utilization
	_ = e.getNodeCharacter(state.Utilization)
	
	// Place character at node position (would need actual coordinates)
	// Placeholder for demonstration
}

func (e *EnergyLayer) getFlowCharacter(flow, utilization float64) rune {
	// Animated flow characters based on intensity
	if utilization > 90 {
		// Overloaded - critical
		return '‼'
	} else if utilization > 75 {
		// High flow
		switch e.animFrame % 4 {
		case 0:
			return '≫'
		case 1:
			return '>'
		case 2:
			return '≫'
		case 3:
			return '»'
		}
	} else if utilization > 50 {
		// Medium flow
		switch e.animFrame % 3 {
		case 0:
			return '→'
		case 1:
			return '⟶'
		case 2:
			return '→'
		}
	} else if utilization > 25 {
		// Low flow
		return '·'
	} else if utilization > 0 {
		// Minimal flow
		return '‧'
	}
	
	return ' '
}

func (e *EnergyLayer) getNodeCharacter(utilization float64) rune {
	switch e.flowType {
	case energy.FlowElectrical:
		if utilization > 90 {
			return '⚡' // High electrical load
		} else if utilization > 50 {
			return '◉' // Medium load
		} else if utilization > 0 {
			return '○' // Low load
		}
		return '◌' // No load
		
	case energy.FlowThermal:
		if utilization > 75 {
			return '🔥' // Hot
		} else if utilization > 50 {
			return '♨' // Warm
		} else if utilization > 25 {
			return '≈' // Cool
		}
		return '❄' // Cold
		
	case energy.FlowFluid:
		if utilization > 75 {
			return '💧' // High flow
		} else if utilization > 50 {
			return '◊' // Medium flow
		} else if utilization > 0 {
			return '·' // Low flow
		}
		return '○' // No flow
	}
	
	return '?'
}

// Update advances the energy flow animation
func (e *EnergyLayer) Update(dt float64) {
	e.animFrame++
	
	// Re-run simulation periodically (every 30 frames = 1 second at 30 FPS)
	if e.animFrame%30 == 0 {
		if result, err := e.flowSystem.Simulate(); err == nil {
			e.flowResult = result
			e.markDirty()
		}
	}
}

func (e *EnergyLayer) markDirty() {
	// Mark entire viewport as dirty for now
	// Could optimize to only mark areas with flow changes
	e.dirty = []Region{{0, 0, 1000, 1000}}
}

// SetVisible controls layer visibility
func (e *EnergyLayer) SetVisible(visible bool) {
	e.visible = visible
}

// IsVisible returns current visibility state
func (e *EnergyLayer) IsVisible() bool {
	return e.visible
}

// GetZ returns the z-index for layering
func (e *EnergyLayer) GetZ() int {
	return LayerEnergy
}

// GetName returns the layer name
func (e *EnergyLayer) GetName() string {
	return "energy"
}

// SetDirty marks regions that need re-rendering
func (e *EnergyLayer) SetDirty(regions []Region) {
	e.dirty = regions
}

// SetFlowType changes the type of flow being visualized
func (e *EnergyLayer) SetFlowType(flowType energy.FlowType) {
	e.flowType = flowType
	e.markDirty()
}

// RunSimulation triggers a new flow simulation
func (e *EnergyLayer) RunSimulation() error {
	result, err := e.flowSystem.Simulate()
	if err != nil {
		return err
	}
	
	e.flowResult = result
	e.markDirty()
	return nil
}

// GetEfficiency returns the current system efficiency
func (e *EnergyLayer) GetEfficiency() float64 {
	if e.flowResult != nil {
		return e.flowResult.Efficiency
	}
	return 0
}

// GetTotalFlow returns the total flow in the system
func (e *EnergyLayer) GetTotalFlow() float64 {
	if e.flowResult != nil {
		return e.flowResult.TotalFlow
	}
	return 0
}

// GetTotalLoss returns the total energy loss in the system
func (e *EnergyLayer) GetTotalLoss() float64 {
	if e.flowResult != nil {
		return e.flowResult.TotalLoss
	}
	return 0
}

// RenderFlowPath renders an animated flow path between two points
func (e *EnergyLayer) RenderFlowPath(buffer [][]rune, points []energy.FlowPoint, vp Viewport) {
	for i, point := range points {
		// Convert world coordinates to viewport
		x := int((point.X - vp.X) * vp.Zoom)
		y := int((point.Y - vp.Y) * vp.Zoom)
		
		// Skip if outside viewport
		if x < 0 || x >= vp.Width || y < 0 || y >= vp.Height {
			continue
		}
		
		// Choose character based on flow direction and animation frame
		char := e.getDirectionalFlowChar(point.Direction, point.Intensity, i)
		buffer[y][x] = char
	}
}

func (e *EnergyLayer) getDirectionalFlowChar(direction, intensity float64, offset int) rune {
	// Convert angle to 8 directions
	angle := direction + math.Pi/8 // Offset for proper quadrant
	if angle < 0 {
		angle += 2 * math.Pi
	}
	
	octant := int(angle / (math.Pi / 4)) % 8
	
	// Animated based on frame and offset
	animOffset := (e.animFrame + offset) % 3
	
	// High intensity flow
	if intensity > 0.7 {
		switch octant {
		case 0, 4: // East/West
			if animOffset == 0 {
				return '═'
			}
			return '─'
		case 2, 6: // North/South
			if animOffset == 0 {
				return '║'
			}
			return '│'
		case 1: // Northeast
			return '╗'
		case 3: // Northwest
			return '╔'
		case 5: // Southwest
			return '╚'
		case 7: // Southeast
			return '╝'
		}
	}
	
	// Low intensity flow
	switch octant {
	case 0: // East
		return '→'
	case 1: // Northeast
		return '↗'
	case 2: // North
		return '↑'
	case 3: // Northwest
		return '↖'
	case 4: // West
		return '←'
	case 5: // Southwest
		return '↙'
	case 6: // South
		return '↓'
	case 7: // Southeast
		return '↘'
	}
	
	return '·'
}