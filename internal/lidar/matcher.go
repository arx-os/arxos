package lidar

import (
	"math"
	"sort"

	"github.com/arx-os/arxos/internal/spatial"
)

// EquipmentMatcher matches detected objects to known equipment
type EquipmentMatcher struct {
	thresholds MatchThresholds
}

// NewEquipmentMatcher creates a new equipment matcher
func NewEquipmentMatcher(thresholds MatchThresholds) *EquipmentMatcher {
	return &EquipmentMatcher{
		thresholds: thresholds,
	}
}

// NewDefaultMatcher creates a matcher with default thresholds
func NewDefaultMatcher() *EquipmentMatcher {
	return &EquipmentMatcher{
		thresholds: DefaultMatchThresholds(),
	}
}

// KnownEquipment represents equipment from the BIM model
type KnownEquipment struct {
	ID          string
	Type        string
	Position    spatial.Point3D
	Dimensions  Dimensions
	BoundingBox spatial.BoundingBox
	Attributes  map[string]interface{}
	Confidence  spatial.ConfidenceLevel
}

// MatchDetectedObjects matches detected objects to known equipment
func (m *EquipmentMatcher) MatchDetectedObjects(
	detectedObjects []*DetectedObject,
	knownEquipment []KnownEquipment,
) ([]*EquipmentMatch, error) {

	matches := make([]*EquipmentMatch, 0)

	// Track which equipment has been matched
	matchedEquipment := make(map[string]bool)

	// Sort detected objects by confidence (highest first)
	sort.Slice(detectedObjects, func(i, j int) bool {
		return detectedObjects[i].Confidence > detectedObjects[j].Confidence
	})

	for _, detected := range detectedObjects {
		bestMatch := m.findBestMatch(detected, knownEquipment, matchedEquipment)
		if bestMatch != nil && bestMatch.MatchScore >= m.thresholds.MinConfidence {
			matches = append(matches, bestMatch)
			matchedEquipment[bestMatch.EquipmentID] = true
		}
	}

	return matches, nil
}

// findBestMatch finds the best equipment match for a detected object
func (m *EquipmentMatcher) findBestMatch(
	detected *DetectedObject,
	knownEquipment []KnownEquipment,
	matchedEquipment map[string]bool,
) *EquipmentMatch {

	var bestMatch *EquipmentMatch
	bestScore := 0.0

	for _, equipment := range knownEquipment {
		// Skip already matched equipment
		if matchedEquipment[equipment.ID] {
			continue
		}

		// Calculate match scores
		shapeScore := m.calculateShapeScore(detected, equipment)
		sizeScore := m.calculateSizeScore(detected, equipment)
		locationScore := m.calculateLocationScore(detected, equipment)

		// Calculate weighted overall score
		overallScore := shapeScore*0.3 + sizeScore*0.3 + locationScore*0.4

		if overallScore > bestScore {
			bestScore = overallScore
			bestMatch = &EquipmentMatch{
				DetectedObject: detected,
				EquipmentID:    equipment.ID,
				EquipmentType:  equipment.Type,
				MatchScore:     overallScore,
				ShapeScore:     shapeScore,
				SizeScore:      sizeScore,
				LocationScore:  locationScore,
				Confidence:     m.calculateMatchConfidence(overallScore),
			}
		}
	}

	return bestMatch
}

// calculateShapeScore calculates shape similarity score
func (m *EquipmentMatcher) calculateShapeScore(
	detected *DetectedObject,
	equipment KnownEquipment,
) float64 {

	// Compare object class if available
	if detected.ObjectClass == equipment.Type {
		return 1.0
	}

	// Compare shape features
	features := detected.Features

	// Check if detected shape matches expected shape for equipment type
	expectedShape := m.getExpectedShape(equipment.Type)
	if features.Shape == expectedShape {
		return 0.9
	}

	// Calculate aspect ratio similarity
	detectedAspect := features.Dimensions.Length / features.Dimensions.Width
	equipmentAspect := equipment.Dimensions.Length / equipment.Dimensions.Width

	aspectDiff := math.Abs(detectedAspect-equipmentAspect) / math.Max(detectedAspect, equipmentAspect)
	aspectScore := 1.0 - math.Min(aspectDiff, 1.0)

	// Combine scores
	return aspectScore * m.thresholds.ShapeSimilarity
}

// calculateSizeScore calculates size similarity score
func (m *EquipmentMatcher) calculateSizeScore(
	detected *DetectedObject,
	equipment KnownEquipment,
) float64 {

	detectedDims := detected.Features.Dimensions
	equipmentDims := equipment.Dimensions

	// Calculate dimensional differences
	lengthDiff := math.Abs(detectedDims.Length-equipmentDims.Length) / equipmentDims.Length
	widthDiff := math.Abs(detectedDims.Width-equipmentDims.Width) / equipmentDims.Width
	heightDiff := math.Abs(detectedDims.Height-equipmentDims.Height) / equipmentDims.Height

	// Average dimensional difference
	avgDiff := (lengthDiff + widthDiff + heightDiff) / 3.0

	// Check if within acceptable deviation
	if avgDiff > m.thresholds.SizeDeviation {
		return 0.0
	}

	// Calculate score based on deviation
	score := 1.0 - (avgDiff / m.thresholds.SizeDeviation)

	// Also consider volume similarity
	detectedVolume := detected.Features.Volume
	equipmentVolume := equipmentDims.Length * equipmentDims.Width * equipmentDims.Height
	volumeDiff := math.Abs(detectedVolume-equipmentVolume) / equipmentVolume
	volumeScore := 1.0 - math.Min(volumeDiff/m.thresholds.SizeDeviation, 1.0)

	// Weighted average of dimensional and volume scores
	return score*0.7 + volumeScore*0.3
}

// calculateLocationScore calculates location proximity score
func (m *EquipmentMatcher) calculateLocationScore(
	detected *DetectedObject,
	equipment KnownEquipment,
) float64 {

	// Calculate distance between centroids
	distance := detected.Centroid.DistanceTo(equipment.Position)

	// Check if within acceptable radius
	if distance > m.thresholds.LocationRadius {
		return 0.0
	}

	// Calculate score based on distance
	score := 1.0 - (distance / m.thresholds.LocationRadius)

	// Consider height difference more strictly (equipment shouldn't move floors)
	heightDiff := math.Abs(detected.Centroid.Z - equipment.Position.Z)
	if heightDiff > 0.5 { // More than 50cm height difference
		score *= 0.5
	}

	return score
}

// calculateMatchConfidence converts match score to confidence level
func (m *EquipmentMatcher) calculateMatchConfidence(score float64) spatial.ConfidenceLevel {
	if score >= 0.9 {
		return spatial.ConfidenceHigh
	} else if score >= 0.7 {
		return spatial.ConfidenceMedium
	} else if score >= 0.5 {
		return spatial.ConfidenceLow
	}
	return spatial.ConfidenceEstimated
}

// getExpectedShape returns expected shape for equipment type
func (m *EquipmentMatcher) getExpectedShape(equipmentType string) string {
	shapeMap := map[string]string{
		"hvac_unit":      "irregular",
		"pipe":           "linear",
		"duct":           "linear",
		"column":         "linear",
		"wall":           "planar",
		"tank":           "spherical",
		"pump":           "irregular",
		"electrical_box": "irregular",
	}

	if shape, ok := shapeMap[equipmentType]; ok {
		return shape
	}
	return "irregular"
}

// MatchWithContext matches objects using additional context
func (m *EquipmentMatcher) MatchWithContext(
	detected *DetectedObject,
	equipment KnownEquipment,
	context MatchContext,
) *EquipmentMatch {

	// Basic matching
	shapeScore := m.calculateShapeScore(detected, equipment)
	sizeScore := m.calculateSizeScore(detected, equipment)
	locationScore := m.calculateLocationScore(detected, equipment)

	// Apply context modifiers
	if context.FloorLevel != "" {
		// Boost score if on expected floor
		if m.isOnFloor(detected.Centroid, context.FloorLevel) {
			locationScore *= 1.2
		}
	}

	if context.RoomID != "" {
		// Boost score if in expected room
		if m.isInRoom(detected.Centroid, context.RoomID) {
			locationScore *= 1.3
		}
	}

	if context.SystemType != "" {
		// Check if equipment type matches system
		if m.belongsToSystem(equipment.Type, context.SystemType) {
			shapeScore *= 1.1
		}
	}

	// Calculate final score
	overallScore := math.Min(shapeScore*0.3+sizeScore*0.3+locationScore*0.4, 1.0)

	return &EquipmentMatch{
		DetectedObject: detected,
		EquipmentID:    equipment.ID,
		EquipmentType:  equipment.Type,
		MatchScore:     overallScore,
		ShapeScore:     shapeScore,
		SizeScore:      sizeScore,
		LocationScore:  locationScore,
		Confidence:     m.calculateMatchConfidence(overallScore),
	}
}

// MatchContext provides additional context for matching
type MatchContext struct {
	FloorLevel      string
	RoomID          string
	SystemType      string // e.g., "hvac", "plumbing", "electrical"
	NearbyEquipment []string
}

// Helper methods for context matching

func (m *EquipmentMatcher) isOnFloor(position spatial.Point3D, floor string) bool {
	// Simple floor detection based on Z coordinate
	// Assumes 3m floor height
	floorNum := 0
	if floor == "1" {
		floorNum = 1
	} else if floor == "2" {
		floorNum = 2
	}
	// Add more floor parsing as needed

	expectedZ := float64(floorNum) * 3.0
	return math.Abs(position.Z-expectedZ) < 1.5 // Within 1.5m of expected floor height
}

func (m *EquipmentMatcher) isInRoom(position spatial.Point3D, roomID string) bool {
	// Simplified room containment check
	// Real implementation would check against room boundaries
	return true // Placeholder
}

func (m *EquipmentMatcher) belongsToSystem(equipmentType, systemType string) bool {
	systemMap := map[string][]string{
		"hvac":       {"hvac_unit", "duct", "diffuser", "vav_box"},
		"plumbing":   {"pipe", "valve", "pump", "tank"},
		"electrical": {"electrical_box", "conduit", "transformer"},
		"structural": {"column", "beam", "wall"},
	}

	if types, ok := systemMap[systemType]; ok {
		for _, t := range types {
			if t == equipmentType {
				return true
			}
		}
	}
	return false
}

// FindUnmatchedObjects identifies detected objects without matches
func (m *EquipmentMatcher) FindUnmatchedObjects(
	detectedObjects []*DetectedObject,
	matches []*EquipmentMatch,
) []*DetectedObject {

	matchedObjects := make(map[string]bool)
	for _, match := range matches {
		matchedObjects[match.DetectedObject.ID] = true
	}

	unmatched := make([]*DetectedObject, 0)
	for _, obj := range detectedObjects {
		if !matchedObjects[obj.ID] {
			unmatched = append(unmatched, obj)
		}
	}

	return unmatched
}

// FindMissingEquipment identifies equipment not found in scan
func (m *EquipmentMatcher) FindMissingEquipment(
	knownEquipment []KnownEquipment,
	matches []*EquipmentMatch,
) []KnownEquipment {

	matchedEquipment := make(map[string]bool)
	for _, match := range matches {
		matchedEquipment[match.EquipmentID] = true
	}

	missing := make([]KnownEquipment, 0)
	for _, equipment := range knownEquipment {
		if !matchedEquipment[equipment.ID] {
			missing = append(missing, equipment)
		}
	}

	return missing
}

// GenerateMatchReport creates a summary of matching results
func (m *EquipmentMatcher) GenerateMatchReport(
	detectedObjects []*DetectedObject,
	knownEquipment []KnownEquipment,
	matches []*EquipmentMatch,
) MatchReport {

	unmatched := m.FindUnmatchedObjects(detectedObjects, matches)
	missing := m.FindMissingEquipment(knownEquipment, matches)

	// Calculate confidence distribution
	confidenceDist := make(map[spatial.ConfidenceLevel]int)
	for _, match := range matches {
		confidenceDist[match.Confidence]++
	}

	// Calculate average scores
	var totalScore, totalShape, totalSize, totalLocation float64
	for _, match := range matches {
		totalScore += match.MatchScore
		totalShape += match.ShapeScore
		totalSize += match.SizeScore
		totalLocation += match.LocationScore
	}

	n := float64(len(matches))
	avgScores := AverageScores{}
	if n > 0 {
		avgScores.Overall = totalScore / n
		avgScores.Shape = totalShape / n
		avgScores.Size = totalSize / n
		avgScores.Location = totalLocation / n
	}

	return MatchReport{
		TotalDetected:          len(detectedObjects),
		TotalKnownEquipment:    len(knownEquipment),
		SuccessfulMatches:      len(matches),
		UnmatchedObjects:       len(unmatched),
		MissingEquipment:       len(missing),
		MatchRate:              float64(len(matches)) / float64(len(knownEquipment)),
		ConfidenceDistribution: confidenceDist,
		AverageScores:          avgScores,
		UnmatchedObjectsList:   unmatched,
		MissingEquipmentList:   missing,
	}
}

// MatchReport summarizes matching results
type MatchReport struct {
	TotalDetected          int
	TotalKnownEquipment    int
	SuccessfulMatches      int
	UnmatchedObjects       int
	MissingEquipment       int
	MatchRate              float64
	ConfidenceDistribution map[spatial.ConfidenceLevel]int
	AverageScores          AverageScores
	UnmatchedObjectsList   []*DetectedObject
	MissingEquipmentList   []KnownEquipment
}

// AverageScores holds average matching scores
type AverageScores struct {
	Overall  float64
	Shape    float64
	Size     float64
	Location float64
}
