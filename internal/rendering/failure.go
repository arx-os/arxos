package rendering

import (
	"fmt"
	"math"
	"time"

	"github.com/arx-os/arxos/internal/connections"
	"github.com/arx-os/arxos/internal/maintenance"
	"github.com/arx-os/arxos/pkg/models"
)

// FailureLayer visualizes failure propagation and risk zones
type FailureLayer struct {
	connManager    *connections.Manager
	predictor      *maintenance.Predictor
	failures       []FailureEvent
	riskZones      []RiskZone
	visible        bool
	dirty          []Region
	animFrame      int
	lastUpdate     time.Time
	simulationMode bool
}

// FailureEvent represents a simulated or predicted equipment failure
type FailureEvent struct {
	EquipmentID     string            `json:"equipment_id"`
	Position        models.Point      `json:"position"`
	FailureType     FailureType       `json:"failure_type"`
	Severity        FailureSeverity   `json:"severity"`
	StartTime       time.Time         `json:"start_time"`
	Duration        time.Duration     `json:"duration"`
	AffectedSystems []string          `json:"affected_systems"`
	PropagationPath []PropagationStep `json:"propagation_path"`
	RecoveryTime    time.Duration     `json:"recovery_time"`
	Active          bool              `json:"active"`
}

// PropagationStep represents how a failure spreads through the system
type PropagationStep struct {
	EquipmentID string        `json:"equipment_id"`
	Position    models.Point  `json:"position"`
	Delay       time.Duration `json:"delay"`
	ImpactLevel float64       `json:"impact_level"` // 0-1
	FailureMode string        `json:"failure_mode"`
	Probability float64       `json:"probability"`
}

// RiskZone represents an area with elevated failure risk
type RiskZone struct {
	Center       models.Point  `json:"center"`
	Radius       float64       `json:"radius"`
	RiskLevel    RiskLevel     `json:"risk_level"`
	FailureTypes []FailureType `json:"failure_types"`
	Equipment    []string      `json:"equipment_ids"`
	LastUpdated  time.Time     `json:"last_updated"`
}

// FailureType represents different types of failures
type FailureType string

const (
	FailureElectrical    FailureType = "electrical"
	FailureMechanical    FailureType = "mechanical"
	FailureThermal       FailureType = "thermal"
	FailureNetwork       FailureType = "network"
	FailureEnvironmental FailureType = "environmental"
	FailureCascading     FailureType = "cascading"
)

// FailureSeverity represents the impact level of a failure
type FailureSeverity string

const (
	SeverityMinor    FailureSeverity = "minor"
	SeverityModerate FailureSeverity = "moderate"
	SeverityMajor    FailureSeverity = "major"
	SeverityCritical FailureSeverity = "critical"
)

// RiskLevel represents the failure risk in a zone
type RiskLevel string

const (
	RiskLow      RiskLevel = "low"
	RiskMedium   RiskLevel = "medium"
	RiskHigh     RiskLevel = "high"
	RiskCritical RiskLevel = "critical"
)

// NewFailureLayer creates a new failure propagation visualization layer
func NewFailureLayer(connManager *connections.Manager, predictor *maintenance.Predictor) *FailureLayer {
	return &FailureLayer{
		connManager:    connManager,
		predictor:      predictor,
		failures:       []FailureEvent{},
		riskZones:      []RiskZone{},
		visible:        true,
		dirty:          []Region{},
		animFrame:      0,
		lastUpdate:     time.Now(),
		simulationMode: false,
	}
}

// Render produces the ASCII representation of failure zones and propagation
func (f *FailureLayer) Render(viewport Viewport) [][]rune {
	// Initialize render buffer
	buffer := make([][]rune, viewport.Height)
	for i := range buffer {
		buffer[i] = make([]rune, viewport.Width)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}

	if !f.visible {
		return buffer
	}

	// Render risk zones first (background)
	for _, zone := range f.riskZones {
		f.renderRiskZone(buffer, zone, viewport)
	}

	// Render active failures
	for _, failure := range f.failures {
		if failure.Active {
			f.renderFailureEvent(buffer, failure, viewport)
		}
	}

	// Render failure propagation paths
	for _, failure := range f.failures {
		if failure.Active && len(failure.PropagationPath) > 0 {
			f.renderPropagationPath(buffer, failure, viewport)
		}
	}

	return buffer
}

func (f *FailureLayer) renderRiskZone(buffer [][]rune, zone RiskZone, vp Viewport) {
	// Convert zone center to viewport coordinates
	centerX := int((zone.Center.X - vp.X) * vp.Zoom)
	centerY := int((zone.Center.Y - vp.Y) * vp.Zoom)
	radius := int(zone.Radius * vp.Zoom)

	// Get zone character based on risk level
	zoneChar := f.getRiskZoneCharacter(zone.RiskLevel)

	// Render circular zone
	for y := centerY - radius; y <= centerY+radius; y++ {
		for x := centerX - radius; x <= centerX+radius; x++ {
			// Check if point is within viewport
			if x < 0 || x >= vp.Width || y < 0 || y >= vp.Height {
				continue
			}

			// Check if point is within circle
			dx := float64(x - centerX)
			dy := float64(y - centerY)
			distance := math.Sqrt(dx*dx + dy*dy)

			if distance <= float64(radius) {
				// Use different intensities based on distance from center
				if distance <= float64(radius)*0.3 {
					buffer[y][x] = zoneChar
				} else if distance <= float64(radius)*0.7 {
					buffer[y][x] = f.getFadedZoneCharacter(zone.RiskLevel)
				} else {
					buffer[y][x] = '░' // Outer edge
				}
			}
		}
	}
}

func (f *FailureLayer) renderFailureEvent(buffer [][]rune, failure FailureEvent, vp Viewport) {
	// Convert failure position to viewport coordinates
	x := int((failure.Position.X - vp.X) * vp.Zoom)
	y := int((failure.Position.Y - vp.Y) * vp.Zoom)

	// Skip if outside viewport
	if x < 0 || x >= vp.Width || y < 0 || y >= vp.Height {
		return
	}

	// Get failure character with animation
	char := f.getFailureCharacter(failure)
	buffer[y][x] = char

	// Render failure radius based on severity
	radius := f.getFailureRadius(failure.Severity)
	if radius > 0 {
		f.renderFailureRadius(buffer, x, y, radius, failure, vp)
	}
}

func (f *FailureLayer) renderFailureRadius(buffer [][]rune, centerX, centerY, radius int, failure FailureEvent, vp Viewport) {
	radiusChar := f.getFailureRadiusCharacter(failure.FailureType)

	for dy := -radius; dy <= radius; dy++ {
		for dx := -radius; dx <= radius; dx++ {
			x := centerX + dx
			y := centerY + dy

			// Check viewport bounds
			if x < 0 || x >= vp.Width || y < 0 || y >= vp.Height {
				continue
			}

			// Check if within circle
			distance := math.Sqrt(float64(dx*dx + dy*dy))
			if distance <= float64(radius) && distance > 1 {
				// Don't overwrite existing content, only fill empty spaces
				if buffer[y][x] == ' ' || buffer[y][x] == '░' {
					buffer[y][x] = radiusChar
				}
			}
		}
	}
}

func (f *FailureLayer) renderPropagationPath(buffer [][]rune, failure FailureEvent, vp Viewport) {
	if len(failure.PropagationPath) < 2 {
		return
	}

	for i := 0; i < len(failure.PropagationPath)-1; i++ {
		from := failure.PropagationPath[i]
		to := failure.PropagationPath[i+1]

		// Convert to viewport coordinates
		x1 := int((from.Position.X - vp.X) * vp.Zoom)
		y1 := int((from.Position.Y - vp.Y) * vp.Zoom)
		x2 := int((to.Position.X - vp.X) * vp.Zoom)
		y2 := int((to.Position.Y - vp.Y) * vp.Zoom)

		// Render propagation line
		f.renderPropagationLine(buffer, x1, y1, x2, y2, to.ImpactLevel, vp)
	}
}

func (f *FailureLayer) renderPropagationLine(buffer [][]rune, x1, y1, x2, y2 int, impact float64, vp Viewport) {
	// Use Bresenham's line algorithm
	dx := abs(x2 - x1)
	dy := abs(y2 - y1)

	var xInc, yInc int
	if x1 < x2 {
		xInc = 1
	} else {
		xInc = -1
	}
	if y1 < y2 {
		yInc = 1
	} else {
		yInc = -1
	}

	error := dx - dy
	x, y := x1, y1

	// Get propagation character based on impact
	propChar := f.getPropagationCharacter(impact)

	for {
		// Check viewport bounds
		if x >= 0 && x < vp.Width && y >= 0 && y < vp.Height {
			// Only draw if space is empty or contains background
			if buffer[y][x] == ' ' || buffer[y][x] == '░' {
				buffer[y][x] = propChar
			}
		}

		if x == x2 && y == y2 {
			break
		}

		error2 := 2 * error

		if error2 > -dy {
			error -= dy
			x += xInc
		}

		if error2 < dx {
			error += dx
			y += yInc
		}
	}
}

// Character selection methods

func (f *FailureLayer) getRiskZoneCharacter(level RiskLevel) rune {
	switch level {
	case RiskCritical:
		return '▓' // Dense shading
	case RiskHigh:
		return '▒' // Medium shading
	case RiskMedium:
		return '░' // Light shading
	case RiskLow:
		return '·' // Minimal shading
	default:
		return ' '
	}
}

func (f *FailureLayer) getFadedZoneCharacter(level RiskLevel) rune {
	switch level {
	case RiskCritical:
		return '▒'
	case RiskHigh:
		return '░'
	case RiskMedium:
		return '·'
	case RiskLow:
		return '‧'
	default:
		return ' '
	}
}

func (f *FailureLayer) getFailureCharacter(failure FailureEvent) rune {
	// Animate based on frame and severity
	animChars := f.getAnimationChars(failure.FailureType, failure.Severity)
	return animChars[f.animFrame%len(animChars)]
}

func (f *FailureLayer) getAnimationChars(failureType FailureType, severity FailureSeverity) []rune {
	switch failureType {
	case FailureElectrical:
		if severity == SeverityCritical {
			return []rune{'⚡', '💥', '⚡', '✦'} // Flashing electrical
		}
		return []rune{'⚡', '▪', '⚡', '▫'} // Blinking electrical

	case FailureMechanical:
		if severity == SeverityCritical {
			return []rune{'⚙', '✗', '⚙', '✗'} // Broken gear
		}
		return []rune{'⚙', '○', '⚙', '○'} // Mechanical issue

	case FailureThermal:
		if severity == SeverityCritical {
			return []rune{'🔥', '▲', '🔥', '△'} // Fire/overheating
		}
		return []rune{'♨', '▲', '♨', '△'} // Heat issue

	case FailureNetwork:
		if severity == SeverityCritical {
			return []rune{'✗', '◆', '✗', '◇'} // Network down
		}
		return []rune{'◆', '◇', '◆', '◇'} // Network issue

	case FailureEnvironmental:
		return []rune{'⚠', '△', '⚠', '▲'} // Environmental warning

	case FailureCascading:
		return []rune{'💥', '◉', '💥', '○'} // Cascading failure

	default:
		return []rune{'✗', '○', '✗', '○'} // Generic failure
	}
}

func (f *FailureLayer) getFailureRadius(severity FailureSeverity) int {
	switch severity {
	case SeverityCritical:
		return 3
	case SeverityMajor:
		return 2
	case SeverityModerate:
		return 1
	case SeverityMinor:
		return 0
	default:
		return 0
	}
}

func (f *FailureLayer) getFailureRadiusCharacter(failureType FailureType) rune {
	switch failureType {
	case FailureElectrical:
		return '·'
	case FailureThermal:
		return '▫'
	case FailureMechanical:
		return '○'
	case FailureNetwork:
		return '◦'
	default:
		return '░'
	}
}

func (f *FailureLayer) getPropagationCharacter(impact float64) rune {
	if impact > 0.8 {
		return '▬' // High impact
	} else if impact > 0.6 {
		return '▪' // Medium impact
	} else if impact > 0.3 {
		return '▫' // Low impact
	} else {
		return '·' // Minimal impact
	}
}

// Simulation and update methods

// Update advances the layer's state and animations
func (f *FailureLayer) Update(dt float64) {
	f.animFrame++
	now := time.Now()

	// Update active failures
	for i := range f.failures {
		failure := &f.failures[i]

		// Check if failure should end
		if failure.Active && now.Sub(failure.StartTime) > failure.Duration {
			failure.Active = false
			f.markDirty()
		}
	}

	// In simulation mode, periodically generate new failures
	if f.simulationMode && now.Sub(f.lastUpdate) > time.Second*10 {
		f.simulateRandomFailure()
		f.lastUpdate = now
	}

	// Update risk zones based on maintenance predictions
	if now.Sub(f.lastUpdate) > time.Minute*5 { // Update every 5 minutes
		f.updateRiskZones()
		f.lastUpdate = now
	}
}

// SimulateFailure creates a simulated failure event
func (f *FailureLayer) SimulateFailure(equipmentID string, position models.Point, failureType FailureType, severity FailureSeverity) {
	failure := FailureEvent{
		EquipmentID: equipmentID,
		Position:    position,
		FailureType: failureType,
		Severity:    severity,
		StartTime:   time.Now(),
		Duration:    f.getFailureDuration(severity),
		Active:      true,
	}

	// Calculate propagation path
	failure.PropagationPath = f.calculatePropagationPath(equipmentID, failureType)
	failure.AffectedSystems = f.getAffectedSystems(equipmentID)

	f.failures = append(f.failures, failure)
	f.markDirty()
}

func (f *FailureLayer) simulateRandomFailure() {
	// Generate a random failure for demonstration
	failureTypes := []FailureType{
		FailureElectrical, FailureMechanical, FailureThermal, FailureNetwork,
	}
	severities := []FailureSeverity{
		SeverityMinor, SeverityModerate, SeverityMajor,
	}

	// Random position
	position := models.Point{
		X: float64(f.animFrame%50 + 10),
		Y: float64(f.animFrame%30 + 5),
	}

	failureType := failureTypes[f.animFrame%len(failureTypes)]
	severity := severities[f.animFrame%len(severities)]

	f.SimulateFailure(
		fmt.Sprintf("sim_%d", f.animFrame),
		position,
		failureType,
		severity,
	)
}

func (f *FailureLayer) calculatePropagationPath(equipmentID string, failureType FailureType) []PropagationStep {
	// Use connections manager to find propagation path
	downstream := f.connManager.GetDownstream(equipmentID)

	var path []PropagationStep
	for i, nextID := range downstream {
		if i >= 5 { // Limit propagation depth
			break
		}

		step := PropagationStep{
			EquipmentID: nextID,
			Position:    models.Point{X: float64(i * 5), Y: float64(i * 3)}, // Simplified
			Delay:       time.Duration(i+1) * time.Second,
			ImpactLevel: math.Max(0.1, 1.0-float64(i)*0.2), // Decreasing impact
			FailureMode: string(failureType),
			Probability: math.Max(0.1, 0.9-float64(i)*0.15), // Decreasing probability
		}
		path = append(path, step)
	}

	return path
}

func (f *FailureLayer) getAffectedSystems(equipmentID string) []string {
	// Simplified - in real implementation would analyze system dependencies
	return []string{"electrical", "hvac"} // Example affected systems
}

func (f *FailureLayer) getFailureDuration(severity FailureSeverity) time.Duration {
	switch severity {
	case SeverityCritical:
		return time.Hour * 4 // 4 hours
	case SeverityMajor:
		return time.Hour * 2 // 2 hours
	case SeverityModerate:
		return time.Hour * 1 // 1 hour
	case SeverityMinor:
		return time.Minute * 30 // 30 minutes
	default:
		return time.Hour * 1
	}
}

func (f *FailureLayer) updateRiskZones() {
	// This would integrate with the maintenance predictor to create risk zones
	// For now, create some example zones
	f.riskZones = []RiskZone{
		{
			Center:       models.Point{X: 20, Y: 15},
			Radius:       5.0,
			RiskLevel:    RiskHigh,
			FailureTypes: []FailureType{FailureElectrical},
			LastUpdated:  time.Now(),
		},
	}
}

// Layer interface implementation

// SetVisible controls layer visibility
func (f *FailureLayer) SetVisible(visible bool) {
	f.visible = visible
}

// IsVisible returns current visibility state
func (f *FailureLayer) IsVisible() bool {
	return f.visible
}

// GetZ returns the z-index for layering
func (f *FailureLayer) GetZ() int {
	return LayerFailure
}

// GetName returns the layer name
func (f *FailureLayer) GetName() string {
	return "failure"
}

// SetDirty marks regions that need re-rendering
func (f *FailureLayer) SetDirty(regions []Region) {
	f.dirty = regions
}

func (f *FailureLayer) markDirty() {
	// Mark entire viewport as dirty
	f.dirty = []Region{{0, 0, 1000, 1000}}
}

// Control methods

// SetSimulationMode enables/disables automatic failure simulation
func (f *FailureLayer) SetSimulationMode(enabled bool) {
	f.simulationMode = enabled
}

// ClearFailures removes all failure events
func (f *FailureLayer) ClearFailures() {
	f.failures = []FailureEvent{}
	f.markDirty()
}

// GetActiveFailures returns currently active failure events
func (f *FailureLayer) GetActiveFailures() []FailureEvent {
	var active []FailureEvent
	for _, failure := range f.failures {
		if failure.Active {
			active = append(active, failure)
		}
	}
	return active
}

// Utility function - using abs from connections.go
