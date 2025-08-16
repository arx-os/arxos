// Package semantic provides architectural intelligence for BIM conversion
package semantic

import (
	"arxos/core/topology"
	"encoding/json"
	"fmt"
	"math"
)

// SpatialRelationship defines architectural patterns
type SpatialRelationship struct {
	ObjectA      string
	Relationship RelationType
	ObjectB      string
	MinDistance  int64 // Nanometers
	MaxDistance  int64
	Confidence   float64
	Context      string // Building type context
	Violations   []string
}

// RelationType defines spatial relationships
type RelationType uint8

const (
	RelationAdjacentTo RelationType = iota
	RelationContains
	RelationNear
	RelationAvoids
	RelationAlignedWith
	RelationPerpendicularTo
	RelationConnectedTo
	RelationAccessibleFrom
)

// ArchitecturalPattern defines expected building patterns
type ArchitecturalPattern struct {
	ObjectType   string
	MinSize      topology.Point2D // Width x Length in nanometers
	MaxSize      topology.Point2D
	AspectRatio  Range
	Adjacencies  []string
	Avoidances   []string
	Orientations []float64 // Preferred angles in radians
	Clusters     ClusterInfo
	Access       AccessPattern
	Typology     string
}

// Range defines min/max values
type Range struct {
	Min float64
	Max float64
}

// ClusterInfo describes grouping patterns
type ClusterInfo struct {
	MinCount     int
	MaxCount     int
	MaxDistance  int64  // Nanometers
	Arrangement  string // "linear", "courtyard", "double_loaded", "pod"
}

// AccessPattern defines door/circulation requirements
type AccessPattern struct {
	MinDoors      int
	MaxDoors      int
	DoorWidth     int64 // Nanometers
	RequiresDirect bool // Direct corridor access
	RequiresSecondary bool // Secondary exit
}

// SemanticEngine provides architectural intelligence
type SemanticEngine struct {
	patterns      map[string]*ArchitecturalPattern
	relationships []SpatialRelationship
	typologies    map[string]*BuildingTypology
	knowledge     *KnowledgeGraph
}

// BuildingTypology defines type-specific rules
type BuildingTypology struct {
	Type              string
	RequiredSpaces    []string
	OptionalSpaces    []string
	CirculationRules  []CirculationRule
	ProximityRules    []ProximityRule
	StandardModules   map[string]topology.Point2D // Standard room sizes
	MinCorridorWidth  int64
	MinDoorWidth      int64
	CeilingHeight     int64
}

// CirculationRule defines movement patterns
type CirculationRule struct {
	SpaceType    string
	RequiresPath []string // Must be accessible from
	MaxDistance  int64    // Maximum path distance
	MinWidth     int64    // Minimum corridor width
}

// ProximityRule defines spatial relationships
type ProximityRule struct {
	SpaceA      string
	SpaceB      string
	Requirement ProximityRequirement
	Distance    int64
}

// ProximityRequirement types
type ProximityRequirement uint8

const (
	ProximityRequired ProximityRequirement = iota
	ProximityPreferred
	ProximityAvoided
	ProximityForbidden
)

// KnowledgeGraph stores learned patterns
type KnowledgeGraph struct {
	Nodes map[string]*KnowledgeNode
	Edges map[string]*KnowledgeEdge
	Stats map[string]*PatternStatistics
}

// KnowledgeNode represents a concept
type KnowledgeNode struct {
	ID         string
	Type       string
	Properties map[string]interface{}
	Frequency  int
	Confidence float64
}

// KnowledgeEdge represents a relationship
type KnowledgeEdge struct {
	ID       string
	Source   string
	Target   string
	Type     string
	Weight   float64
	Examples []string // Building IDs where observed
}

// PatternStatistics tracks pattern occurrences
type PatternStatistics struct {
	Pattern     string
	Occurrences int
	SuccessRate float64
	LastSeen    string
	Variations  []string
}

// NewSemanticEngine creates an intelligence engine
func NewSemanticEngine() *SemanticEngine {
	engine := &SemanticEngine{
		patterns:      make(map[string]*ArchitecturalPattern),
		typologies:    make(map[string]*BuildingTypology),
		knowledge:     NewKnowledgeGraph(),
	}
	
	// Initialize with educational building patterns
	engine.loadEducationalPatterns()
	
	return engine
}

// loadEducationalPatterns defines K-12 school patterns
func (e *SemanticEngine) loadEducationalPatterns() {
	// Standard classroom pattern
	e.patterns["classroom"] = &ArchitecturalPattern{
		ObjectType: "classroom",
		MinSize:    topology.Point2D{X: 7 * 1e9, Y: 9 * 1e9},     // 7m x 9m minimum
		MaxSize:    topology.Point2D{X: 10 * 1e9, Y: 12 * 1e9},   // 10m x 12m maximum
		AspectRatio: Range{Min: 1.2, Max: 1.8},
		Adjacencies: []string{"corridor", "classroom"},
		Avoidances:  []string{"mechanical", "kitchen"},
		Clusters: ClusterInfo{
			MinCount:    4,
			MaxCount:    12,
			MaxDistance: 50 * 1e9, // 50 meters
			Arrangement: "linear",
		},
		Access: AccessPattern{
			MinDoors:       1,
			MaxDoors:       2,
			DoorWidth:      900 * 1e6, // 900mm
			RequiresDirect: true,
		},
		Typology: "educational",
	}
	
	// Corridor pattern
	e.patterns["corridor"] = &ArchitecturalPattern{
		ObjectType:  "corridor",
		MinSize:     topology.Point2D{X: 2 * 1e9, Y: 10 * 1e9}, // 2m wide minimum
		AspectRatio: Range{Min: 5.0, Max: 50.0}, // Long and narrow
		Adjacencies: []string{"classroom", "office", "bathroom"},
		Clusters: ClusterInfo{
			Arrangement: "linear",
		},
		Typology: "educational",
	}
	
	// Elementary school typology
	e.typologies["elementary_school"] = &BuildingTypology{
		Type: "elementary_school",
		RequiredSpaces: []string{
			"classroom", "corridor", "office", "bathroom",
			"cafeteria", "gymnasium", "library",
		},
		OptionalSpaces: []string{
			"music_room", "art_room", "computer_lab",
		},
		StandardModules: map[string]topology.Point2D{
			"classroom": {X: 8 * 1e9, Y: 10 * 1e9},  // 8m x 10m
			"office":    {X: 4 * 1e9, Y: 5 * 1e9},   // 4m x 5m
			"bathroom":  {X: 3 * 1e9, Y: 4 * 1e9},   // 3m x 4m
		},
		MinCorridorWidth: 2400 * 1e6, // 2.4m for evacuation
		MinDoorWidth:     900 * 1e6,  // 900mm
		CeilingHeight:    3000 * 1e6, // 3m standard
	}
	
	// Add spatial relationships
	e.relationships = append(e.relationships, SpatialRelationship{
		ObjectA:      "classroom",
		Relationship: RelationAdjacentTo,
		ObjectB:      "corridor",
		MinDistance:  0,
		MaxDistance:  1 * 1e9, // 1 meter
		Confidence:   0.95,
		Context:      "elementary_school",
	})
	
	e.relationships = append(e.relationships, SpatialRelationship{
		ObjectA:      "bathroom",
		Relationship: RelationNear,
		ObjectB:      "classroom",
		MinDistance:  0,
		MaxDistance:  30 * 1e9, // 30 meters
		Confidence:   0.85,
		Context:      "elementary_school",
	})
}

// AnalyzeBuilding performs semantic analysis
func (e *SemanticEngine) AnalyzeBuilding(building *topology.Building, typology string) *SemanticAnalysis {
	analysis := &SemanticAnalysis{
		BuildingID: building.ID,
		Typology:   typology,
		Timestamp:  getCurrentTimestamp(),
	}
	
	// Classify rooms based on geometry and relationships
	e.classifyRooms(building, analysis)
	
	// Validate spatial relationships
	e.validateRelationships(building, analysis)
	
	// Check typology requirements
	e.checkTypologyRequirements(building, typology, analysis)
	
	// Calculate confidence score
	analysis.OverallConfidence = e.calculateConfidence(analysis)
	
	// Update knowledge graph with findings
	e.updateKnowledge(building, analysis)
	
	return analysis
}

// classifyRooms infers room types from patterns
func (e *SemanticEngine) classifyRooms(building *topology.Building, analysis *SemanticAnalysis) {
	for _, room := range building.Rooms {
		classification := e.classifyRoom(room, building)
		
		analysis.RoomClassifications = append(analysis.RoomClassifications, RoomClassification{
			RoomID:     room.ID,
			Predicted:  classification.Type,
			Confidence: classification.Confidence,
			Evidence:   classification.Evidence,
		})
		
		// Update room function if confident
		if classification.Confidence > 0.8 {
			room.Function = mapToRoomFunction(classification.Type)
		}
	}
}

// classifyRoom determines room type
func (e *SemanticEngine) classifyRoom(room *topology.Room, building *topology.Building) *Classification {
	classification := &Classification{
		Confidence: 0.0,
		Evidence:   []string{},
	}
	
	// Check size against patterns
	area := float64(room.Area) / 1e18 // Convert to square meters
	aspectRatio := calculateAspectRatio(room.Footprint)
	
	for patternName, pattern := range e.patterns {
		score := 0.0
		
		// Check size match
		minArea := float64(pattern.MinSize.X*pattern.MinSize.Y) / 1e18
		maxArea := float64(pattern.MaxSize.X*pattern.MaxSize.Y) / 1e18
		
		if area >= minArea && area <= maxArea {
			score += 0.3
			classification.Evidence = append(classification.Evidence,
				fmt.Sprintf("Size matches %s (%.1f m²)", patternName, area))
		}
		
		// Check aspect ratio
		if aspectRatio >= pattern.AspectRatio.Min && aspectRatio <= pattern.AspectRatio.Max {
			score += 0.2
			classification.Evidence = append(classification.Evidence,
				fmt.Sprintf("Aspect ratio matches %s (%.2f)", patternName, aspectRatio))
		}
		
		// Check adjacencies
		adjacentTypes := e.getAdjacentRoomTypes(room, building)
		for _, required := range pattern.Adjacencies {
			if contains(adjacentTypes, required) {
				score += 0.2
				classification.Evidence = append(classification.Evidence,
					fmt.Sprintf("Adjacent to %s", required))
			}
		}
		
		// Check clustering
		if pattern.Clusters.MinCount > 0 {
			nearbyCount := e.countNearbyRooms(room, building, patternName, pattern.Clusters.MaxDistance)
			if nearbyCount >= pattern.Clusters.MinCount {
				score += 0.3
				classification.Evidence = append(classification.Evidence,
					fmt.Sprintf("Part of %s cluster (%d nearby)", patternName, nearbyCount))
			}
		}
		
		if score > classification.Confidence {
			classification.Type = patternName
			classification.Confidence = score
		}
	}
	
	return classification
}

// SemanticAnalysis contains analysis results
type SemanticAnalysis struct {
	BuildingID          uint64
	Typology            string
	Timestamp           string
	RoomClassifications []RoomClassification
	Violations          []SemanticViolation
	Suggestions         []Suggestion
	OverallConfidence   float64
	RequirementsMet     []string
	RequirementsMissing []string
}

// RoomClassification contains room type prediction
type RoomClassification struct {
	RoomID     uint64
	Predicted  string
	Confidence float64
	Evidence   []string
}

// SemanticViolation represents architectural rule violation
type SemanticViolation struct {
	Type        string
	Severity    topology.IssueSeverity
	Description string
	AffectedIDs []uint64
	Rule        string
}

// Suggestion provides improvement recommendations
type Suggestion struct {
	Type        string
	Description string
	Impact      string
	Confidence  float64
}

// Classification result
type Classification struct {
	Type       string
	Confidence float64
	Evidence   []string
}

// validateRelationships checks spatial rules
func (e *SemanticEngine) validateRelationships(building *topology.Building, analysis *SemanticAnalysis) {
	for _, rel := range e.relationships {
		if rel.Context != "" && rel.Context != analysis.Typology {
			continue // Skip rules for other typologies
		}
		
		violations := e.checkRelationship(building, rel)
		for _, v := range violations {
			analysis.Violations = append(analysis.Violations, v)
		}
	}
}

// checkRelationship validates a single rule
func (e *SemanticEngine) checkRelationship(building *topology.Building, rel SpatialRelationship) []SemanticViolation {
	var violations []SemanticViolation
	
	// Find all rooms of type A
	roomsA := e.findRoomsByType(building, rel.ObjectA)
	roomsB := e.findRoomsByType(building, rel.ObjectB)
	
	for _, roomA := range roomsA {
		satisfied := false
		
		for _, roomB := range roomsB {
			distance := e.calculateRoomDistance(roomA, roomB)
			
			switch rel.Relationship {
			case RelationAdjacentTo:
				if e.areRoomsAdjacent(roomA, roomB, building) {
					satisfied = true
				}
			case RelationNear:
				if distance >= rel.MinDistance && distance <= rel.MaxDistance {
					satisfied = true
				}
			case RelationAvoids:
				if distance > rel.MaxDistance {
					satisfied = true
				}
			}
		}
		
		if !satisfied {
			violations = append(violations, SemanticViolation{
				Type:        "spatial_relationship",
				Severity:    topology.SeverityWarning,
				Description: fmt.Sprintf("%s should be %v %s", rel.ObjectA, rel.Relationship, rel.ObjectB),
				AffectedIDs: []uint64{roomA.ID},
				Rule:        fmt.Sprintf("%s_%v_%s", rel.ObjectA, rel.Relationship, rel.ObjectB),
			})
		}
	}
	
	return violations
}

// Helper functions

func NewKnowledgeGraph() *KnowledgeGraph {
	return &KnowledgeGraph{
		Nodes: make(map[string]*KnowledgeNode),
		Edges: make(map[string]*KnowledgeEdge),
		Stats: make(map[string]*PatternStatistics),
	}
}

func getCurrentTimestamp() string {
	return "2024-01-01T00:00:00Z" // Placeholder
}

func mapToRoomFunction(roomType string) topology.RoomFunction {
	mapping := map[string]topology.RoomFunction{
		"classroom":  topology.RoomFunctionClassroom,
		"office":     topology.RoomFunctionOffice,
		"corridor":   topology.RoomFunctionCorridor,
		"bathroom":   topology.RoomFunctionBathroom,
		"cafeteria":  topology.RoomFunctionCafeteria,
		"gymnasium":  topology.RoomFunctionGymnasium,
		"library":    topology.RoomFunctionLibrary,
		"laboratory": topology.RoomFunctionLaboratory,
	}
	
	if f, exists := mapping[roomType]; exists {
		return f
	}
	return topology.RoomFunctionUnknown
}

func calculateAspectRatio(footprint []topology.Point2D) float64 {
	if len(footprint) < 4 {
		return 1.0
	}
	
	// Simple bounding box aspect ratio
	minX, maxX := footprint[0].X, footprint[0].X
	minY, maxY := footprint[0].Y, footprint[0].Y
	
	for _, p := range footprint {
		if p.X < minX {
			minX = p.X
		}
		if p.X > maxX {
			maxX = p.X
		}
		if p.Y < minY {
			minY = p.Y
		}
		if p.Y > maxY {
			maxY = p.Y
		}
	}
	
	width := float64(maxX - minX)
	height := float64(maxY - minY)
	
	if height == 0 {
		return 1.0
	}
	
	return width / height
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func (e *SemanticEngine) getAdjacentRoomTypes(room *topology.Room, building *topology.Building) []string {
	var types []string
	
	for _, adjID := range room.AdjacentRooms {
		if adjRoom, exists := building.Rooms[adjID]; exists {
			// Get room type from classification or function
			roomType := e.getRoomType(adjRoom)
			if roomType != "" && !contains(types, roomType) {
				types = append(types, roomType)
			}
		}
	}
	
	return types
}

func (e *SemanticEngine) getRoomType(room *topology.Room) string {
	// Map room function to type string
	functionMap := map[topology.RoomFunction]string{
		topology.RoomFunctionClassroom:  "classroom",
		topology.RoomFunctionOffice:     "office",
		topology.RoomFunctionCorridor:   "corridor",
		topology.RoomFunctionBathroom:   "bathroom",
		topology.RoomFunctionCafeteria:  "cafeteria",
		topology.RoomFunctionGymnasium:  "gymnasium",
		topology.RoomFunctionLibrary:    "library",
		topology.RoomFunctionLaboratory: "laboratory",
	}
	
	if t, exists := functionMap[room.Function]; exists {
		return t
	}
	
	return ""
}

func (e *SemanticEngine) countNearbyRooms(room *topology.Room, building *topology.Building, roomType string, maxDistance int64) int {
	count := 0
	
	for _, other := range building.Rooms {
		if other.ID == room.ID {
			continue
		}
		
		if e.getRoomType(other) == roomType {
			distance := e.calculateRoomDistance(room, other)
			if distance <= maxDistance {
				count++
			}
		}
	}
	
	return count
}

func (e *SemanticEngine) calculateRoomDistance(room1, room2 *topology.Room) int64 {
	dx := room2.Centroid.X - room1.Centroid.X
	dy := room2.Centroid.Y - room1.Centroid.Y
	return int64(math.Sqrt(float64(dx*dx + dy*dy)))
}

func (e *SemanticEngine) areRoomsAdjacent(room1, room2 *topology.Room, building *topology.Building) bool {
	// Check if rooms share a wall
	for _, wall1ID := range room1.BoundaryWalls {
		for _, wall2ID := range room2.BoundaryWalls {
			if wall1ID == wall2ID {
				return true
			}
		}
	}
	return false
}

func (e *SemanticEngine) findRoomsByType(building *topology.Building, roomType string) []*topology.Room {
	var rooms []*topology.Room
	
	for _, room := range building.Rooms {
		if e.getRoomType(room) == roomType {
			rooms = append(rooms, room)
		}
	}
	
	return rooms
}

func (e *SemanticEngine) checkTypologyRequirements(building *topology.Building, typology string, analysis *SemanticAnalysis) {
	typ, exists := e.typologies[typology]
	if !exists {
		return
	}
	
	// Check required spaces
	foundSpaces := make(map[string]bool)
	for _, room := range building.Rooms {
		roomType := e.getRoomType(room)
		if roomType != "" {
			foundSpaces[roomType] = true
		}
	}
	
	for _, required := range typ.RequiredSpaces {
		if foundSpaces[required] {
			analysis.RequirementsMet = append(analysis.RequirementsMet, required)
		} else {
			analysis.RequirementsMissing = append(analysis.RequirementsMissing, required)
			
			analysis.Suggestions = append(analysis.Suggestions, Suggestion{
				Type:        "missing_space",
				Description: fmt.Sprintf("Missing required %s for %s", required, typology),
				Impact:      "high",
				Confidence:  0.9,
			})
		}
	}
}

func (e *SemanticEngine) calculateConfidence(analysis *SemanticAnalysis) float64 {
	if len(analysis.RoomClassifications) == 0 {
		return 0.0
	}
	
	totalConfidence := 0.0
	for _, classification := range analysis.RoomClassifications {
		totalConfidence += classification.Confidence
	}
	
	avgConfidence := totalConfidence / float64(len(analysis.RoomClassifications))
	
	// Reduce confidence for violations
	violationPenalty := float64(len(analysis.Violations)) * 0.05
	avgConfidence = math.Max(0.0, avgConfidence-violationPenalty)
	
	// Reduce confidence for missing requirements
	requirementPenalty := float64(len(analysis.RequirementsMissing)) * 0.1
	avgConfidence = math.Max(0.0, avgConfidence-requirementPenalty)
	
	return avgConfidence
}

func (e *SemanticEngine) updateKnowledge(building *topology.Building, analysis *SemanticAnalysis) {
	// Update pattern statistics
	for _, classification := range analysis.RoomClassifications {
		statKey := fmt.Sprintf("%s_%s", analysis.Typology, classification.Predicted)
		
		if stat, exists := e.knowledge.Stats[statKey]; exists {
			stat.Occurrences++
			stat.LastSeen = building.Name
		} else {
			e.knowledge.Stats[statKey] = &PatternStatistics{
				Pattern:     classification.Predicted,
				Occurrences: 1,
				SuccessRate: classification.Confidence,
				LastSeen:    building.Name,
			}
		}
	}
	
	// Add nodes for rooms
	for _, room := range building.Rooms {
		nodeID := fmt.Sprintf("room_%d", room.ID)
		e.knowledge.Nodes[nodeID] = &KnowledgeNode{
			ID:   nodeID,
			Type: e.getRoomType(room),
			Properties: map[string]interface{}{
				"area":     room.Area,
				"building": building.Name,
			},
			Frequency:  1,
			Confidence: analysis.OverallConfidence,
		}
	}
}

// Export/Import functions for persistence
func (e *SemanticEngine) ExportKnowledge() ([]byte, error) {
	return json.Marshal(e.knowledge)
}

func (e *SemanticEngine) ImportKnowledge(data []byte) error {
	return json.Unmarshal(data, &e.knowledge)
}