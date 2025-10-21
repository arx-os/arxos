package spatial

import (
	"fmt"
	"math"
	"strings"
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// SpatialValidator provides validation for spatial operations and data
type SpatialValidator struct {
	// Configuration for validation rules
	maxDistance   float64       // Maximum allowed distance in mm
	minConfidence float64       // Minimum confidence threshold
	maxAge        time.Duration // Maximum age for spatial data
}

// NewSpatialValidator creates a new spatial validator with default settings
func NewSpatialValidator() *SpatialValidator {
	return &SpatialValidator{
		maxDistance:   10000.0,        // 10 meters in mm
		minConfidence: 0.5,            // 50% confidence minimum
		maxAge:        24 * time.Hour, // 24 hours max age
	}
}

// WithMaxDistance sets the maximum allowed distance
func (sv *SpatialValidator) WithMaxDistance(distance float64) *SpatialValidator {
	sv.maxDistance = distance
	return sv
}

// WithMinConfidence sets the minimum confidence threshold
func (sv *SpatialValidator) WithMinConfidence(confidence float64) *SpatialValidator {
	sv.minConfidence = confidence
	return sv
}

// WithMaxAge sets the maximum age for spatial data
func (sv *SpatialValidator) WithMaxAge(age time.Duration) *SpatialValidator {
	sv.maxAge = age
	return sv
}

// ValidateSpatialLocation validates a spatial location
func (sv *SpatialValidator) ValidateSpatialLocation(location *SpatialLocation) error {
	if location == nil {
		return fmt.Errorf("spatial location cannot be nil")
	}

	// Check if coordinates are valid numbers
	if math.IsNaN(location.X) || math.IsNaN(location.Y) || math.IsNaN(location.Z) {
		return fmt.Errorf("spatial location coordinates cannot be NaN")
	}

	if math.IsInf(location.X, 0) || math.IsInf(location.Y, 0) || math.IsInf(location.Z, 0) {
		return fmt.Errorf("spatial location coordinates cannot be infinite")
	}

	// Check if coordinates are within reasonable range
	maxCoord := 1000000.0 // 1km in mm
	if math.Abs(location.X) > maxCoord || math.Abs(location.Y) > maxCoord || math.Abs(location.Z) > maxCoord {
		return fmt.Errorf("spatial location coordinates exceed maximum range")
	}

	return nil
}

// ValidateQuaternion validates a quaternion rotation
func (sv *SpatialValidator) ValidateQuaternion(quat *Quaternion) error {
	if quat == nil {
		return fmt.Errorf("quaternion cannot be nil")
	}

	// Check if quaternion components are valid numbers
	if math.IsNaN(quat.W) || math.IsNaN(quat.X) || math.IsNaN(quat.Y) || math.IsNaN(quat.Z) {
		return fmt.Errorf("quaternion components cannot be NaN")
	}

	if math.IsInf(quat.W, 0) || math.IsInf(quat.X, 0) || math.IsInf(quat.Y, 0) || math.IsInf(quat.Z, 0) {
		return fmt.Errorf("quaternion components cannot be infinite")
	}

	// Check if quaternion is normalized (magnitude should be approximately 1)
	magnitude := math.Sqrt(quat.W*quat.W + quat.X*quat.X + quat.Y*quat.Y + quat.Z*quat.Z)
	if math.Abs(magnitude-1.0) > 0.001 {
		return fmt.Errorf("quaternion is not normalized (magnitude: %f)", magnitude)
	}

	return nil
}

// ValidateSpatialAnchor validates a spatial anchor
func (sv *SpatialValidator) ValidateSpatialAnchor(anchor *SpatialAnchor) error {
	if anchor == nil {
		return fmt.Errorf("spatial anchor cannot be nil")
	}

	// Validate ID
	if strings.TrimSpace(anchor.ID) == "" {
		return fmt.Errorf("spatial anchor ID cannot be empty")
	}

	// Validate position
	if err := sv.ValidateSpatialLocation(anchor.Position); err != nil {
		return fmt.Errorf("spatial anchor position validation failed: %w", err)
	}

	// Validate rotation
	if err := sv.ValidateQuaternion(anchor.Rotation); err != nil {
		return fmt.Errorf("spatial anchor rotation validation failed: %w", err)
	}

	// Validate confidence
	if anchor.Confidence < 0 || anchor.Confidence > 1 {
		return fmt.Errorf("spatial anchor confidence must be between 0 and 1")
	}

	if anchor.Confidence < sv.minConfidence {
		return fmt.Errorf("spatial anchor confidence %f is below minimum threshold %f",
			anchor.Confidence, sv.minConfidence)
	}

	// Validate required fields
	if strings.TrimSpace(anchor.BuildingID) == "" {
		return fmt.Errorf("spatial anchor building ID cannot be empty")
	}

	// Validate age
	if time.Since(anchor.Timestamp) > sv.maxAge {
		return fmt.Errorf("spatial anchor is too old (age: %v)", time.Since(anchor.Timestamp))
	}

	// Validate platform
	if strings.TrimSpace(anchor.Platform) != "" {
		validPlatforms := []string{"ARKit", "ARCore", "WebXR", "Manual"}
		if !containsString(validPlatforms, anchor.Platform) {
			return fmt.Errorf("invalid AR platform: %s", anchor.Platform)
		}
	}

	// Validate stability
	if anchor.Stability < 0 || anchor.Stability > 1 {
		return fmt.Errorf("spatial anchor stability must be between 0 and 1")
	}

	// Validate range
	if anchor.Range <= 0 {
		return fmt.Errorf("spatial anchor range must be positive")
	}

	return nil
}

// ValidateARNavigationPath validates a navigation path
func (sv *SpatialValidator) ValidateARNavigationPath(path *ARNavigationPath) error {
	if path == nil {
		return fmt.Errorf("AR navigation path cannot be nil")
	}

	// Validate ID
	if strings.TrimSpace(path.ID) == "" {
		return fmt.Errorf("AR navigation path ID cannot be empty")
	}

	// Validate waypoints
	for i, waypoint := range path.Waypoints {
		if err := sv.ValidateSpatialLocation(waypoint); err != nil {
			return fmt.Errorf("waypoint %d validation failed: %w", i, err)
		}
	}

	// Validate path distance
	if path.Distance < 0 {
		return fmt.Errorf("AR navigation path distance cannot be negative")
	}

	if path.Distance > sv.maxDistance {
		return fmt.Errorf("AR navigation path distance %f exceeds maximum %f",
			path.Distance, sv.maxDistance)
	}

	// Validate estimated time
	if path.EstimatedTime < 0 {
		return fmt.Errorf("AR navigation path estimated time cannot be negative")
	}

	// Validate difficulty
	validDifficulties := []string{"easy", "medium", "hard"}
	if !containsString(validDifficulties, path.Difficulty) {
		return fmt.Errorf("invalid difficulty level: %s", path.Difficulty)
	}

	// Validate instructions
	for i, instruction := range path.ARInstructions {
		if err := sv.ValidateARInstruction(&instruction); err != nil {
			return fmt.Errorf("instruction %d validation failed: %w", i, err)
		}
	}

	return nil
}

// ValidateARInstruction validates an AR instruction
func (sv *SpatialValidator) ValidateARInstruction(instruction *ARInstruction) error {
	if instruction == nil {
		return fmt.Errorf("AR instruction cannot be nil")
	}

	// Validate ID
	if strings.TrimSpace(instruction.ID) == "" {
		return fmt.Errorf("AR instruction ID cannot be empty")
	}

	// Validate type
	validTypes := []string{"move", "turn", "stop", "wait", "start", "arrival"}
	if !containsString(validTypes, instruction.Type) {
		return fmt.Errorf("invalid instruction type: %s", instruction.Type)
	}

	// Validate position
	if instruction.Position != nil {
		if err := sv.ValidateSpatialLocation(instruction.Position); err != nil {
			return fmt.Errorf("AR instruction position validation failed: %w", err)
		}
	}

	// Validate duration
	if instruction.EstimatedDuration < 0 {
		return fmt.Errorf("AR instruction estimated duration cannot be negative")
	}

	// Validate priority
	validPriorities := []string{"low", "medium", "high", "urgent"}
	if !containsString(validPriorities, instruction.Priority) {
		return fmt.Errorf("invalid instruction priority: %s", instruction.Priority)
	}

	// Validate visualization
	if err := sv.ValidateARVisualization(&instruction.ARVisualization); err != nil {
		return fmt.Errorf("AR instruction visualization validation failed: %w", err)
	}

	return nil
}

// ValidateARVisualization validates an AR visualization
func (sv *SpatialValidator) ValidateARVisualization(vis *ARVisualization) error {
	if vis == nil {
		return fmt.Errorf("AR visualization cannot be nil")
	}

	// Validate type
	validTypes := []string{"arrow", "circle", "plane", "object", "text", "icon"}
	if !containsString(validTypes, vis.Type) {
		return fmt.Errorf("invalid visualization type: %s", vis.Type)
	}

	// Validate color (basic hex color validation)
	if vis.Color != "" && !isValidHexColor(vis.Color) {
		return fmt.Errorf("invalid visualization color format: %s", vis.Color)
	}

	// Validate size
	if vis.Size <= 0 {
		return fmt.Errorf("visualization size must be positive")
	}

	if vis.Size > 10.0 {
		return fmt.Errorf("visualization size %f exceeds maximum 10.0", vis.Size)
	}

	// Validate opacity
	if vis.Opacity < 0 || vis.Opacity > 1 {
		return fmt.Errorf("visualization opacity must be between 0 and 1")
	}

	// Validate intensity
	if vis.Intensity < 0 || vis.Intensity > 1 {
		return fmt.Errorf("visualization intensity must be between 0 and 1")
	}

	// Validate animation
	if vis.Animation != "" {
		validAnimations := []string{"none", "pulse", "rotate", "fade", "bounce", "shake"}
		if !containsString(validAnimations, vis.Animation) {
			return fmt.Errorf("invalid visualization animation: %s", vis.Animation)
		}
	}

	return nil
}

// ValidateARSessionMetrics validates AR session metrics
func (sv *SpatialValidator) ValidateARSessionMetrics(metrics *ARSessionMetrics) error {
	if metrics == nil {
		return fmt.Errorf("AR session metrics cannot be nil")
	}

	// Validate session ID
	if strings.TrimSpace(metrics.SessionID) == "" {
		return fmt.Errorf("AR session metrics session ID cannot be empty")
	}

	// Validate time range
	if metrics.EndTime.Before(metrics.StartTime) {
		return fmt.Errorf("AR session end time cannot be before start time")
	}

	// Validate duration
	if math.Abs(metrics.Duration-metrics.EndTime.Sub(metrics.StartTime).Seconds()) > 1.0 {
		return fmt.Errorf("AR session duration mismatch with time range")
	}

	// Validate counts (non-negative)
	counts := map[string]int{
		"anchors detected":            metrics.AnchorsDetected,
		"anchors created":             metrics.AnchorsCreated,
		"anchors updated":             metrics.AnchorsUpdated,
		"anchors removed":             metrics.AnchorsRemoved,
		"equipment overlays rendered": metrics.EquipmentOverlaysRendered,
		"navigation paths calculated": metrics.NavigationPathsCalculated,
		"errors encountered":          metrics.ErrorsEncountered,
	}

	for name, count := range counts {
		if count < 0 {
			return fmt.Errorf("AR session metrics %s cannot be negative", name)
		}
	}

	// Validate performance metrics
	if metrics.AverageFrameRate < 0 {
		return fmt.Errorf("AR session average frame rate cannot be negative")
	}

	if metrics.AverageTrackingQuality < 0 || metrics.AverageTrackingQuality > 1 {
		return fmt.Errorf("AR session tracking quality must be between 0 and 1")
	}

	if metrics.BatteryUsage < 0 || metrics.BatteryUsage > 100 {
		return fmt.Errorf("AR session battery usage must be between 0 and 100 percent")
	}

	if metrics.MemoryUsage < 0 {
		return fmt.Errorf("AR session memory usage cannot be negative")
	}

	// Validate thermal state
	if metrics.ThermalState != "" {
		validStates := []string{"normal", "slight", "intermediate", "critical"}
		if !containsString(validStates, metrics.ThermalState) {
			return fmt.Errorf("invalid AR session thermal state: %s", metrics.ThermalState)
		}
	}

	return nil
}

// ValidateDistance validates the distance between two spatial references
func (sv *SpatialValidator) ValidateDistance(from, to *SpatialLocation, expectedDistance float64) error {
	if from == nil || to == nil {
		return fmt.Errorf("cannot validate distance with nil locations")
	}

	actualDistance := calculateDistance(from, to)
	distanceDiff := math.Abs(actualDistance - expectedDistance)

	// Allow 5% tolerance
	tolerance := expectedDistance * 0.05
	if distanceDiff > tolerance {
		return fmt.Errorf("distance validation failed: expected %f, actual %f (diff: %f, tolerance: %f)",
			expectedDistance, actualDistance, distanceDiff, tolerance)
	}

	return nil
}

// ValidateWithinBounds validates that a spatial location is within specified bounds
func (sv *SpatialValidator) ValidateWithinBounds(location *SpatialLocation, bounds models.BoundingBox) error {
	if location == nil {
		return fmt.Errorf("cannot validate bounds with nil location")
	}

	point := location.ToPoint3D()
	if !bounds.Contains(point) {
		return fmt.Errorf("spatial location %s is outside bounds (min: %v, max: %v)",
			location.String(), bounds.Min, bounds.Max)
	}

	return nil
}

// Helper functions

// containsString checks if a slice contains a string
func containsString(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// isValidHexColor validates hex color format (#RRGGBB or #RGB)
func isValidHexColor(color string) bool {
	if color == "" {
		return false
	}

	if color[0] != '#' {
		return false
	}

	if len(color) == 4 || len(color) == 7 {
		for _, char := range color[1:] {
			if !((char >= '0' && char <= '9') ||
				(char >= 'A' && char <= 'F') ||
				(char >= 'a' && char <= 'f')) {
				return false
			}
		}
		return true
	}

	return false
}

// calculateDistance calculates the Euclidean distance between two spatial locations
func calculateDistance(from, to *SpatialLocation) float64 {
	dx := from.X - to.X
	dy := from.Y - to.Y
	dz := from.Z - to.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// SpatialLocation utility methods

// String returns a string representation of SpatialLocation
func (sl *SpatialLocation) String() string {
	if sl == nil {
		return "nil"
	}
	return fmt.Sprintf("(%.3f, %.3f, %.3f)", sl.X, sl.Y, sl.Z)
}

// DistanceTo calculates distance to another spatial location
func (sl *SpatialLocation) DistanceTo(other *SpatialLocation) float64 {
	if sl == nil || other == nil {
		return -1
	}
	return calculateDistance(sl, other)
}

// IsValid checks if the spatial location has valid coordinates
func (sl *SpatialLocation) IsValid() bool {
	if sl == nil {
		return false
	}

	return !math.IsNaN(sl.X) && !math.IsNaN(sl.Y) && !math.IsNaN(sl.Z) &&
		!math.IsInf(sl.X, 0) && !math.IsInf(sl.Y, 0) && !math.IsInf(sl.Z, 0)
}
