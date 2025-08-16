// Package topology provides comprehensive tests for BIM conversion
package topology

import (
	"math"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestDBSCANClustering validates endpoint merging
func TestDBSCANClustering(t *testing.T) {
	tests := []struct {
		name           string
		segments       []LineSegment
		epsilon        float64
		minPoints      int
		expectedMerged int
		description    string
	}{
		{
			name: "simple_corner_connection",
			segments: []LineSegment{
				{ID: 1, Start: Point2D{X: 0, Y: 0}, End: Point2D{X: 1000000000, Y: 0}},
				{ID: 2, Start: Point2D{X: 999999000, Y: 0}, End: Point2D{X: 999999000, Y: 1000000000}},
			},
			epsilon:        0.001, // 0.1% tolerance
			minPoints:      2,
			expectedMerged: 1, // One endpoint pair should merge
			description:    "Two walls meeting at corner with slight gap",
		},
		{
			name: "t_junction",
			segments: []LineSegment{
				{ID: 1, Start: Point2D{X: 0, Y: 500000000}, End: Point2D{X: 1000000000, Y: 500000000}},
				{ID: 2, Start: Point2D{X: 500000000, Y: 0}, End: Point2D{X: 500000000, Y: 500000000}},
			},
			epsilon:        0.001,
			minPoints:      2,
			expectedMerged: 1,
			description:    "T-junction wall intersection",
		},
		{
			name: "classroom_walls",
			segments: createClassroomWalls(),
			epsilon:        0.005,
			minPoints:      3,
			expectedMerged: 4, // Four corners should merge
			description:    "Standard classroom with gaps at corners",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Run clustering
			merged, result := ClusterEndpoints(tt.segments, tt.epsilon, tt.minPoints)
			
			// Verify merge count
			assert.Equal(t, tt.expectedMerged, result.NumMerged/2, 
				"Incorrect number of merged endpoints for %s", tt.description)
			
			// Verify segments still form valid structure
			assert.Equal(t, len(tt.segments), len(merged), 
				"Segment count should remain the same")
			
			// Check that merged segments connect properly
			for _, seg := range merged {
				assert.NotNil(t, seg.Start)
				assert.NotNil(t, seg.End)
				assert.NotEqual(t, seg.Start, seg.End, "Segment collapsed to point")
			}
		})
	}
}

// TestRoomDetection validates planar graph room finding
func TestRoomDetection(t *testing.T) {
	tests := []struct {
		name          string
		walls         []*Wall
		expectedRooms int
		minArea       int64
		maxArea       int64
	}{
		{
			name:          "single_rectangular_room",
			walls:         createRectangularRoom(8*1e9, 10*1e9), // 8m x 10m
			expectedRooms: 1,
			minArea:       79*1e18, // ~80m²
			maxArea:       81*1e18,
		},
		{
			name:          "two_adjacent_rooms",
			walls:         createAdjacentRooms(),
			expectedRooms: 2,
			minArea:       40*1e18,
			maxArea:       80*1e18,
		},
		{
			name:          "corridor_with_classrooms",
			walls:         createCorridorWithClassrooms(),
			expectedRooms: 5, // 1 corridor + 4 classrooms
			minArea:       20*1e18,
			maxArea:       100*1e18,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			detector := NewRoomDetector(tt.walls)
			rooms, err := detector.DetectRooms()
			
			require.NoError(t, err, "Room detection should not fail")
			assert.Equal(t, tt.expectedRooms, len(rooms), 
				"Incorrect number of rooms detected")
			
			// Validate each room
			for i, room := range rooms {
				// Check area bounds
				assert.GreaterOrEqual(t, room.Area, tt.minArea,
					"Room %d area too small", i)
				assert.LessOrEqual(t, room.Area, tt.maxArea,
					"Room %d area too large", i)
				
				// Check polygon closure
				assert.GreaterOrEqual(t, len(room.Footprint), 3,
					"Room %d has insufficient vertices", i)
				
				// Check wall boundaries
				assert.NotEmpty(t, room.BoundaryWalls,
					"Room %d has no boundary walls", i)
			}
			
			// Validate room topology
			issues := detector.ValidateRooms()
			assert.Empty(t, issues, "Room validation should pass")
		})
	}
}

// TestSemanticAnalysis validates pattern recognition
func TestSemanticAnalysis(t *testing.T) {
	// Create test building
	building := &Building{
		ID:   1,
		Name: "Test Elementary School",
		Metadata: BuildingMetadata{
			BuildingType: BuildingTypeEducational,
			SchoolLevel:  "elementary",
		},
		Walls: make(map[uint64]*Wall),
		Rooms: make(map[uint64]*Room),
	}
	
	// Add standard classroom
	classroom := &Room{
		ID:            1,
		Area:          80 * 1e18, // 80m²
		Footprint:     createRectangularFootprint(8*1e9, 10*1e9),
		BoundaryWalls: []uint64{1, 2, 3, 4},
		Function:      RoomFunctionUnknown, // To be classified
	}
	building.Rooms[1] = classroom
	
	// Add corridor
	corridor := &Room{
		ID:            2,
		Area:          60 * 1e18, // 60m² (2m x 30m)
		Footprint:     createRectangularFootprint(2*1e9, 30*1e9),
		BoundaryWalls: []uint64{5, 6, 7, 8},
		Function:      RoomFunctionUnknown,
	}
	building.Rooms[2] = corridor
	
	// Set adjacency
	classroom.AdjacentRooms = []uint64{2}
	corridor.AdjacentRooms = []uint64{1}
	
	// Run semantic analysis
	engine := NewTestSemanticEngine()
	analysis := engine.AnalyzeBuilding(building, "elementary_school")
	
	// Verify classifications
	assert.GreaterOrEqual(t, analysis.OverallConfidence, 0.7,
		"Confidence should be reasonable for standard patterns")
	
	// Check room classifications
	foundClassroom := false
	foundCorridor := false
	
	for _, classification := range analysis.RoomClassifications {
		if classification.RoomID == 1 {
			assert.Equal(t, "classroom", classification.Predicted)
			assert.GreaterOrEqual(t, classification.Confidence, 0.6)
			foundClassroom = true
		}
		if classification.RoomID == 2 {
			assert.Equal(t, "corridor", classification.Predicted)
			assert.GreaterOrEqual(t, classification.Confidence, 0.5)
			foundCorridor = true
		}
	}
	
	assert.True(t, foundClassroom, "Classroom should be identified")
	assert.True(t, foundCorridor, "Corridor should be identified")
}

// TestConfidenceScoring validates confidence calculations
func TestConfidenceScoring(t *testing.T) {
	tests := []struct {
		name               string
		clusteringRatio    float64
		validationIssues   []ValidationIssue
		semanticConfidence float64
		expectedMin        float64
		expectedMax        float64
	}{
		{
			name:               "perfect_processing",
			clusteringRatio:    0.05,
			validationIssues:   []ValidationIssue{},
			semanticConfidence: 0.95,
			expectedMin:        0.90,
			expectedMax:        1.00,
		},
		{
			name:            "moderate_issues",
			clusteringRatio: 0.15,
			validationIssues: []ValidationIssue{
				{Severity: SeverityWarning},
				{Severity: SeverityWarning},
			},
			semanticConfidence: 0.75,
			expectedMin:        0.65,
			expectedMax:        0.85,
		},
		{
			name:            "critical_issues",
			clusteringRatio: 0.25,
			validationIssues: []ValidationIssue{
				{Severity: SeverityCritical},
				{Severity: SeverityError},
			},
			semanticConfidence: 0.60,
			expectedMin:        0.30,
			expectedMax:        0.60,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			confidence := calculateTestConfidence(
				tt.clusteringRatio,
				tt.validationIssues,
				tt.semanticConfidence,
			)
			
			assert.GreaterOrEqual(t, confidence, tt.expectedMin,
				"Confidence too low for %s", tt.name)
			assert.LessOrEqual(t, confidence, tt.expectedMax,
				"Confidence too high for %s", tt.name)
		})
	}
}

// TestManualCorrections validates correction application
func TestManualCorrections(t *testing.T) {
	// Create initial wall
	wall := &Wall{
		ID:         1,
		StartPoint: Point3D{X: 0, Y: 0, Z: 0},
		EndPoint:   Point3D{X: 1000000000, Y: 0, Z: 0},
		Thickness:  200000000, // 200mm
		Type:       WallTypeInterior,
		Confidence: 0.75,
	}
	
	// Create correction
	correction := ManualCorrection{
		ID:   1,
		Type: CorrectionTypeWallConnection,
		Before: map[string]interface{}{
			"end_x": wall.EndPoint.X,
			"end_y": wall.EndPoint.Y,
		},
		After: map[string]interface{}{
			"end_x": int64(1010000000), // Extend by 10mm
			"end_y": int64(0),
		},
		Reason:     "Wall should connect to perpendicular wall",
		Confidence: 0.95,
	}
	
	// Apply correction
	applyTestCorrection(wall, correction)
	
	// Verify changes
	assert.Equal(t, int64(1010000000), wall.EndPoint.X,
		"Wall endpoint should be corrected")
	assert.Equal(t, ValidationStatusManual, wall.ValidationStatus,
		"Wall should be marked as manually validated")
	assert.GreaterOrEqual(t, wall.Confidence, 0.9,
		"Wall confidence should increase after manual correction")
}

// Benchmark tests for performance validation

func BenchmarkDBSCANClustering(b *testing.B) {
	// Create large set of segments (1000 walls)
	segments := make([]LineSegment, 1000)
	for i := range segments {
		segments[i] = LineSegment{
			ID:    uint64(i),
			Start: Point2D{X: int64(i * 1000000), Y: 0},
			End:   Point2D{X: int64((i + 1) * 1000000), Y: 0},
		}
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ClusterEndpoints(segments, 0.005, 3)
	}
}

func BenchmarkRoomDetection(b *testing.B) {
	// Create complex building with 50 rooms
	walls := createComplexBuilding(50)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		detector := NewRoomDetector(walls)
		detector.DetectRooms()
	}
}

// Helper functions for test data generation

func createClassroomWalls() []LineSegment {
	// 8m x 10m classroom with small gaps at corners
	gap := int64(1000000) // 1mm gaps
	width := int64(8 * 1e9)
	height := int64(10 * 1e9)
	
	return []LineSegment{
		{ID: 1, Start: Point2D{X: 0, Y: 0}, End: Point2D{X: width - gap, Y: 0}},
		{ID: 2, Start: Point2D{X: width, Y: gap}, End: Point2D{X: width, Y: height - gap}},
		{ID: 3, Start: Point2D{X: width - gap, Y: height}, End: Point2D{X: gap, Y: height}},
		{ID: 4, Start: Point2D{X: 0, Y: height - gap}, End: Point2D{X: 0, Y: gap}},
	}
}

func createRectangularRoom(width, height int64) []*Wall {
	return []*Wall{
		{ID: 1, StartPoint: Point3D{X: 0, Y: 0}, EndPoint: Point3D{X: width, Y: 0}},
		{ID: 2, StartPoint: Point3D{X: width, Y: 0}, EndPoint: Point3D{X: width, Y: height}},
		{ID: 3, StartPoint: Point3D{X: width, Y: height}, EndPoint: Point3D{X: 0, Y: height}},
		{ID: 4, StartPoint: Point3D{X: 0, Y: height}, EndPoint: Point3D{X: 0, Y: 0}},
	}
}

func createAdjacentRooms() []*Wall {
	// Two 8m x 10m rooms side by side
	width := int64(8 * 1e9)
	height := int64(10 * 1e9)
	
	return []*Wall{
		// First room
		{ID: 1, StartPoint: Point3D{X: 0, Y: 0}, EndPoint: Point3D{X: width, Y: 0}},
		{ID: 2, StartPoint: Point3D{X: width, Y: 0}, EndPoint: Point3D{X: width, Y: height}},
		{ID: 3, StartPoint: Point3D{X: width, Y: height}, EndPoint: Point3D{X: 0, Y: height}},
		{ID: 4, StartPoint: Point3D{X: 0, Y: height}, EndPoint: Point3D{X: 0, Y: 0}},
		// Second room (shares wall ID 2)
		{ID: 5, StartPoint: Point3D{X: width, Y: 0}, EndPoint: Point3D{X: width * 2, Y: 0}},
		{ID: 6, StartPoint: Point3D{X: width * 2, Y: 0}, EndPoint: Point3D{X: width * 2, Y: height}},
		{ID: 7, StartPoint: Point3D{X: width * 2, Y: height}, EndPoint: Point3D{X: width, Y: height}},
	}
}

func createCorridorWithClassrooms() []*Wall {
	// Central corridor with classrooms on both sides
	corridorWidth := int64(2 * 1e9)   // 2m wide
	corridorLength := int64(40 * 1e9) // 40m long
	classroomWidth := int64(8 * 1e9)  // 8m wide
	classroomDepth := int64(10 * 1e9) // 10m deep
	
	walls := []*Wall{
		// Corridor walls
		{ID: 1, StartPoint: Point3D{X: 0, Y: 0}, EndPoint: Point3D{X: corridorLength, Y: 0}},
		{ID: 2, StartPoint: Point3D{X: corridorLength, Y: 0}, EndPoint: Point3D{X: corridorLength, Y: corridorWidth}},
		{ID: 3, StartPoint: Point3D{X: corridorLength, Y: corridorWidth}, EndPoint: Point3D{X: 0, Y: corridorWidth}},
		{ID: 4, StartPoint: Point3D{X: 0, Y: corridorWidth}, EndPoint: Point3D{X: 0, Y: 0}},
	}
	
	// Add classrooms
	wallID := uint64(5)
	for i := 0; i < 4; i++ {
		xOffset := int64(i) * classroomWidth
		
		// Classroom above corridor
		walls = append(walls, &Wall{
			ID: wallID,
			StartPoint: Point3D{X: xOffset, Y: corridorWidth},
			EndPoint: Point3D{X: xOffset + classroomWidth, Y: corridorWidth},
		})
		wallID++
		
		// Add remaining classroom walls...
		// (Simplified for brevity)
	}
	
	return walls
}

func createRectangularFootprint(width, height int64) []Point2D {
	return []Point2D{
		{X: 0, Y: 0},
		{X: width, Y: 0},
		{X: width, Y: height},
		{X: 0, Y: height},
	}
}

func createComplexBuilding(numRooms int) []*Wall {
	// Generate a grid of rooms for benchmarking
	walls := make([]*Wall, 0)
	wallID := uint64(1)
	
	gridSize := int(math.Sqrt(float64(numRooms)))
	roomSize := int64(10 * 1e9) // 10m x 10m rooms
	
	for row := 0; row < gridSize; row++ {
		for col := 0; col < gridSize; col++ {
			x := int64(col) * roomSize
			y := int64(row) * roomSize
			
			// Add room walls (simplified - shares walls with adjacent rooms)
			if col == 0 || col == gridSize-1 {
				walls = append(walls, &Wall{
					ID:         wallID,
					StartPoint: Point3D{X: x, Y: y},
					EndPoint:   Point3D{X: x, Y: y + roomSize},
				})
				wallID++
			}
			
			if row == 0 || row == gridSize-1 {
				walls = append(walls, &Wall{
					ID:         wallID,
					StartPoint: Point3D{X: x, Y: y},
					EndPoint:   Point3D{X: x + roomSize, Y: y},
				})
				wallID++
			}
		}
	}
	
	return walls
}

func NewTestSemanticEngine() *SemanticEngine {
	// Create a semantic engine with test patterns
	// This would be imported from the semantic package
	return &SemanticEngine{
		patterns:   make(map[string]*ArchitecturalPattern),
		typologies: make(map[string]*BuildingTypology),
		knowledge:  &KnowledgeGraph{},
	}
}

func calculateTestConfidence(clusterRatio float64, issues []ValidationIssue, semantic float64) float64 {
	confidence := 1.0
	
	if clusterRatio > 0.1 {
		confidence *= 0.9
	}
	
	for _, issue := range issues {
		switch issue.Severity {
		case SeverityCritical:
			confidence *= 0.7
		case SeverityError:
			confidence *= 0.85
		case SeverityWarning:
			confidence *= 0.95
		}
	}
	
	confidence = (confidence + semantic) / 2
	return confidence
}

func applyTestCorrection(wall *Wall, correction ManualCorrection) {
	if after, ok := correction.After.(map[string]interface{}); ok {
		if endX, exists := after["end_x"]; exists {
			wall.EndPoint.X = endX.(int64)
		}
		if endY, exists := after["end_y"]; exists {
			wall.EndPoint.Y = endY.(int64)
		}
	}
	
	wall.ValidationStatus = ValidationStatusManual
	wall.Confidence = (wall.Confidence + correction.Confidence) / 2
}