package particles

import (
	"fmt"
	"strings"

	"github.com/arx-os/arxos/pkg/models"
)

// BuildingEffects provides particle effects for building systems
type BuildingEffects struct {
	system *System
	room   *models.Room
}

// NewBuildingEffects creates effects for a room
func NewBuildingEffects(room *models.Room) *BuildingEffects {
	width := int(room.Bounds.MaxX - room.Bounds.MinX)
	height := int(room.Bounds.MaxY - room.Bounds.MinY)

	// Ensure minimum size for visualization
	if width < 40 {
		width = 40
	}
	if height < 20 {
		height = 20
	}

	return &BuildingEffects{
		system: NewSystem(width, height),
		room:   room,
	}
}

// SimulateHVAC shows airflow through a room
func (be *BuildingEffects) SimulateHVAC() string {
	s := be.system

	// Configure for airflow
	s.Gravity = -0.01 // Slight upward drift
	s.Wind = 0.3      // Rightward flow
	s.Friction = 0.99 // Low friction for smooth flow

	// Spawn air particles from left vents
	ventY := float64(s.Height) / 3
	s.EmitFromLine(0, ventY, 0, ventY+3, TypeAir, 5)

	// Add circulation force in center
	s.AddForce(float64(s.Width)/2, float64(s.Height)/2, 10, 0.1, -0.1)

	// Update physics
	s.Update()

	// Render to string
	return be.renderWithFrame("HVAC Airflow Simulation")
}

// SimulateElectrical shows electrical flow
func (be *BuildingEffects) SimulateElectrical(fromX, fromY, toX, toY float64) string {
	s := be.system

	// Configure for electrical flow
	s.Gravity = 0     // No gravity for electricity
	s.Wind = 0        // No wind
	s.Friction = 0.95 // Some resistance

	// Create electrical path
	s.EmitFromLine(fromX, fromY, toX, toY, TypeElectric, 3)

	// Update physics
	s.Update()

	return be.renderWithFrame("Electrical Flow")
}

// SimulateWaterLeak shows water leak from a point
func (be *BuildingEffects) SimulateWaterLeak(x, y float64) string {
	s := be.system

	// Configure for water
	s.Gravity = 0.5   // Strong gravity
	s.Wind = 0.05     // Slight drift
	s.Friction = 0.98 // Water friction

	// Spawn water particles
	s.Spawn(x, y, TypeWater, 10)

	// Update physics
	s.Update()

	return be.renderWithFrame("Water Leak Detected!")
}

// SimulateOccupancy shows people movement patterns
func (be *BuildingEffects) SimulateOccupancy(paths [][]float64) string {
	s := be.system

	// Configure for people movement
	s.Gravity = 0    // People don't fall
	s.Wind = 0       // No wind affects people
	s.Friction = 0.9 // High friction for controlled movement

	// Spawn people along paths
	for _, path := range paths {
		if len(path) >= 4 {
			s.EmitFromLine(path[0], path[1], path[2], path[3], TypePeople, 1)
		}
	}

	// Update physics
	s.Update()

	return be.renderWithFrame("Occupancy Flow Pattern")
}

// renderWithFrame renders the particle system with a room frame
func (be *BuildingEffects) renderWithFrame(title string) string {
	grid := be.system.Render()

	var output strings.Builder

	// Title
	output.WriteString(fmt.Sprintf("\n%s - %s\n", be.room.Name, title))
	output.WriteString(strings.Repeat("═", be.system.Width+2))
	output.WriteString("\n")

	// Top border
	output.WriteRune('┌')
	output.WriteString(strings.Repeat("─", be.system.Width))
	output.WriteRune('┐')
	output.WriteString("\n")

	// Render grid with side borders
	for _, row := range grid {
		output.WriteRune('│')
		for _, char := range row {
			output.WriteRune(char)
		}
		output.WriteRune('│')
		output.WriteString("\n")
	}

	// Bottom border
	output.WriteRune('└')
	output.WriteString(strings.Repeat("─", be.system.Width))
	output.WriteRune('┘')
	output.WriteString("\n")

	// Legend
	output.WriteString("\nLegend: ")
	output.WriteString("· Air  ○ Water  ± Electric  ° Heat  ● People\n")
	output.WriteString(fmt.Sprintf("Active Particles: %d\n", len(be.system.Particles)))

	return output.String()
}

// AnimateEffect runs a continuous animation (would need terminal control)
func (be *BuildingEffects) AnimateEffect(effectType string, frames int) []string {
	results := make([]string, frames)

	for i := 0; i < frames; i++ {
		switch effectType {
		case "hvac":
			// Continuous airflow
			ventY := float64(be.system.Height) / 3
			be.system.EmitFromLine(0, ventY, 0, ventY+3, TypeAir, 5)
			be.system.Update()
			results[i] = be.renderWithFrame("HVAC Airflow")

		case "leak":
			// Continuous water leak
			be.system.Spawn(float64(be.system.Width)/2, 5, TypeWater, 3)
			be.system.Update()
			results[i] = be.renderWithFrame("Water Leak Active")

		case "heat":
			// Heat distribution
			be.system.Spawn(float64(be.system.Width)/2, float64(be.system.Height)-2, TypeHeat, 2)
			be.system.Update()
			results[i] = be.renderWithFrame("Heat Distribution")

		default:
			be.system.Update()
			results[i] = be.renderWithFrame("Particle Simulation")
		}
	}

	return results
}
