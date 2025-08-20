package services

import (
	"fmt"
	"math"
	"sync"
	"time"

	"arxos/arxobject"
)

// PropagationEngine handles confidence propagation across related objects
type PropagationEngine struct {
	arxEngine          *arxobject.Engine
	propagationRules   map[string]*PropagationRule
	propagationHistory []PropagationEvent
	mu                 sync.RWMutex
}

// PropagationRule defines how confidence propagates
type PropagationRule struct {
	ID               string                 `json:"id"`
	SourceType       arxobject.ArxObjectType `json:"source_type"`
	TargetType       arxobject.ArxObjectType `json:"target_type"`
	PropagationType  string                 `json:"propagation_type"`
	DecayFactor      float32                `json:"decay_factor"`
	MaxDistance      float32                `json:"max_distance"`
	MinSimilarity    float32                `json:"min_similarity"`
	Conditions       map[string]interface{} `json:"conditions"`
}

// PropagationEvent records a propagation occurrence
type PropagationEvent struct {
	ID               string    `json:"id"`
	SourceObjectID   string    `json:"source_object_id"`
	TargetObjectID   string    `json:"target_object_id"`
	OldConfidence    float32   `json:"old_confidence"`
	NewConfidence    float32   `json:"new_confidence"`
	PropagationType  string    `json:"propagation_type"`
	PropagationTime  time.Time `json:"propagation_time"`
	DistanceFactor   float32   `json:"distance_factor"`
	SimilarityFactor float32   `json:"similarity_factor"`
}

// PropagationResult contains the results of a propagation
type PropagationResult struct {
	TotalObjectsAffected int                  `json:"total_objects_affected"`
	AverageImprovement   float32              `json:"average_improvement"`
	PropagationDepth     int                  `json:"propagation_depth"`
	TimeTaken            time.Duration        `json:"time_taken"`
	AffectedObjects      []PropagationImpact  `json:"affected_objects"`
}

// PropagationImpact describes impact on a single object
type PropagationImpact struct {
	ObjectID          string  `json:"object_id"`
	ObjectType        string  `json:"object_type"`
	OldConfidence     float32 `json:"old_confidence"`
	NewConfidence     float32 `json:"new_confidence"`
	ImprovementAmount float32 `json:"improvement_amount"`
	PropagationPath   []string `json:"propagation_path"`
}

// NewPropagationEngine creates a new propagation engine
func NewPropagationEngine(arxEngine *arxobject.Engine) *PropagationEngine {
	engine := &PropagationEngine{
		arxEngine:          arxEngine,
		propagationRules:   make(map[string]*PropagationRule),
		propagationHistory: make([]PropagationEvent, 0),
	}
	
	// Initialize default propagation rules
	engine.initializeDefaultRules()
	
	return engine
}

// PropagateValidation propagates validation confidence to related objects
func (pe *PropagationEngine) PropagateValidation(
	validatedObject *arxobject.ArxObject,
	validationConfidence float32,
	maxDepth int,
) (*PropagationResult, error) {
	
	pe.mu.Lock()
	defer pe.mu.Unlock()
	
	startTime := time.Now()
	result := &PropagationResult{
		AffectedObjects: make([]PropagationImpact, 0),
	}
	
	// Track visited objects to avoid cycles
	visited := make(map[string]bool)
	visited[validatedObject.ID] = true
	
	// Queue for breadth-first propagation
	type queueItem struct {
		object   *arxobject.ArxObject
		depth    int
		path     []string
		confidence float32
	}
	
	queue := []queueItem{{
		object:     validatedObject,
		depth:      0,
		path:       []string{validatedObject.ID},
		confidence: validationConfidence,
	}}
	
	maxDepthReached := 0
	
	for len(queue) > 0 {
		current := queue[0]
		queue = queue[1:]
		
		if current.depth > maxDepthReached {
			maxDepthReached = current.depth
		}
		
		if current.depth >= maxDepth {
			continue
		}
		
		// Find related objects
		relatedObjects := pe.findRelatedObjects(current.object)
		
		for _, related := range relatedObjects {
			if visited[related.ID] {
				continue
			}
			visited[related.ID] = true
			
			// Calculate propagation factors
			distanceFactor := pe.calculateDistanceFactor(current.object, related)
			similarityFactor := pe.calculateSimilarityFactor(current.object, related)
			typeFactor := pe.calculateTypeFactor(arxobject.ArxObjectType(current.object.Type), arxobject.ArxObjectType(related.Type))
			
			// Calculate propagated confidence
			propagatedConfidence := current.confidence * 
				distanceFactor * 
				similarityFactor * 
				typeFactor * 
				pe.getDecayFactor(current.depth)
			
			// Only propagate if it improves confidence
			if propagatedConfidence > related.Confidence.Overall {
				oldConfidence := related.Confidence.Overall
				
				// Apply propagated confidence
				pe.applyPropagatedConfidence(related, propagatedConfidence)
				
				// Record impact
				impact := PropagationImpact{
					ObjectID:          related.ID,
					ObjectType:        pe.getObjectTypeName(arxobject.ArxObjectType(related.Type)),
					OldConfidence:     oldConfidence,
					NewConfidence:     related.Confidence.Overall,
					ImprovementAmount: related.Confidence.Overall - oldConfidence,
					PropagationPath:   append(current.path, related.ID),
				}
				result.AffectedObjects = append(result.AffectedObjects, impact)
				
				// Record event
				pe.recordPropagationEvent(current.object, related, oldConfidence, propagatedConfidence, distanceFactor, similarityFactor)
				
				// Add to queue for further propagation
				queue = append(queue, queueItem{
					object:     related,
					depth:      current.depth + 1,
					path:       impact.PropagationPath,
					confidence: propagatedConfidence,
				})
			}
		}
	}
	
	// Calculate statistics
	result.TotalObjectsAffected = len(result.AffectedObjects)
	result.PropagationDepth = maxDepthReached
	result.TimeTaken = time.Since(startTime)
	
	if result.TotalObjectsAffected > 0 {
		totalImprovement := float32(0)
		for _, impact := range result.AffectedObjects {
			totalImprovement += impact.ImprovementAmount
		}
		result.AverageImprovement = totalImprovement / float32(result.TotalObjectsAffected)
	}
	
	return result, nil
}

// findRelatedObjects finds objects related to the given object
func (pe *PropagationEngine) findRelatedObjects(obj *arxobject.ArxObject) []*arxobject.ArxObject {
	related := make([]*arxobject.ArxObject, 0)
	
	// 1. Find spatially adjacent objects
	x, y, _ := obj.GetPositionMeters() // z not used for 2D search
	searchRadius := float32(20.0) // 20 meter radius
	
	nearbyIDs := pe.arxEngine.QueryRegion(
		float32(x)-searchRadius, float32(y)-searchRadius,
		float32(x)+searchRadius, float32(y)+searchRadius,
	)
	
	for _, id := range nearbyIDs {
		if id == obj.ID {
			continue
		}
		
		nearbyObj, err := pe.arxEngine.GetObject(id)
		if err != nil {
			continue
		}
		
		// Check if within actual distance
		objX, objY, _ := nearbyObj.GetPositionMeters()
		distance := math.Sqrt(
			math.Pow(x-objX, 2) + math.Pow(y-objY, 2),
		)
		
		if distance <= float64(searchRadius) {
			related = append(related, nearbyObj)
		}
	}
	
	// 2. Find objects with explicit relationships
	// This would query the relationship table in a real implementation
	
	// 3. Find objects in same spatial container (room, floor, etc.)
	// This would check parent-child relationships
	
	return related
}

// calculateDistanceFactor calculates confidence decay based on distance
func (pe *PropagationEngine) calculateDistanceFactor(obj1, obj2 *arxobject.ArxObject) float32 {
	x1, y1, z1 := obj1.GetPositionMeters()
	x2, y2, z2 := obj2.GetPositionMeters()
	
	distance := math.Sqrt(
		math.Pow(x1-x2, 2) + 
		math.Pow(y1-y2, 2) + 
		math.Pow(z1-z2, 2),
	)
	
	// Exponential decay with distance
	// Full confidence at 0m, 50% at 5m, 10% at 20m
	decayRate := 0.139 // -ln(0.5)/5
	factor := float32(math.Exp(-decayRate * distance))
	
	return pe.clamp(factor, 0.1, 1.0)
}

// calculateSimilarityFactor calculates confidence based on object similarity
func (pe *PropagationEngine) calculateSimilarityFactor(obj1, obj2 *arxobject.ArxObject) float32 {
	similarity := float32(0)
	
	// Type similarity
	if obj1.Type == obj2.Type {
		similarity += 0.4
	} else if pe.areTypesRelated(arxobject.ArxObjectType(obj1.Type), arxobject.ArxObjectType(obj2.Type)) {
		similarity += 0.2
	}
	
	// Scale level similarity
	if obj1.ScaleMin == obj2.ScaleMin && obj1.ScaleMax == obj2.ScaleMax {
		similarity += 0.2
	}
	
	// Dimensional similarity (using width as proxy for length)
	if obj1.Width > 0 && obj2.Width > 0 {
		widthRatio := float32(math.Min(float64(obj1.Width), float64(obj2.Width))) / 
			float32(math.Max(float64(obj1.Width), float64(obj2.Width)))
		similarity += widthRatio * 0.2
	}
	
	if obj1.Width > 0 && obj2.Width > 0 {
		widthRatio := float32(math.Min(float64(obj1.Width), float64(obj2.Width))) / 
			float32(math.Max(float64(obj1.Width), float64(obj2.Width)))
		similarity += widthRatio * 0.1
	}
	
	if obj1.Height > 0 && obj2.Height > 0 {
		heightRatio := float32(math.Min(float64(obj1.Height), float64(obj2.Height))) / 
			float32(math.Max(float64(obj1.Height), float64(obj2.Height)))
		similarity += heightRatio * 0.1
	}
	
	return pe.clamp(similarity, 0.1, 1.0)
}

// calculateTypeFactor calculates propagation factor based on object types
func (pe *PropagationEngine) calculateTypeFactor(sourceType, targetType arxobject.ArxObjectType) float32 {
	// Same type - high propagation
	if sourceType == targetType {
		return 1.0
	}
	
	// Related types - medium propagation
	if pe.areTypesRelated(sourceType, targetType) {
		return 0.7
	}
	
	// Different system - low propagation
	if pe.getSystem(sourceType) != pe.getSystem(targetType) {
		return 0.3
	}
	
	// Same system - medium propagation
	return 0.5
}

// applyPropagatedConfidence applies propagated confidence to an object
func (pe *PropagationEngine) applyPropagatedConfidence(obj *arxobject.ArxObject, propagatedConfidence float32) {
	// Calculate boost for each dimension
	boost := propagatedConfidence - obj.Confidence.Overall
	
	// Apply weighted boost to different dimensions
	obj.Confidence.Classification = pe.clamp(
		obj.Confidence.Classification + boost*0.3, 0, 0.95,
	)
	obj.Confidence.Position = pe.clamp(
		obj.Confidence.Position + boost*0.4, 0, 0.95,
	)
	obj.Confidence.Properties = pe.clamp(
		obj.Confidence.Properties + boost*0.2, 0, 0.95,
	)
	obj.Confidence.Relationships = pe.clamp(
		obj.Confidence.Relationships + boost*0.1, 0, 0.95,
	)
	
	// Recalculate overall
	obj.Confidence.CalculateOverall()
}

// getDecayFactor returns decay factor for propagation depth
func (pe *PropagationEngine) getDecayFactor(depth int) float32 {
	// Each level reduces confidence by 10%
	return float32(math.Pow(0.9, float64(depth)))
}

// recordPropagationEvent records a propagation event
func (pe *PropagationEngine) recordPropagationEvent(
	source, target *arxobject.ArxObject,
	oldConfidence, newConfidence float32,
	distanceFactor, similarityFactor float32,
) {
	event := PropagationEvent{
		ID:               fmt.Sprintf("prop_%d_%d_%d", source.ID, target.ID, time.Now().Unix()),
		SourceObjectID:   source.ID,
		TargetObjectID:   target.ID,
		OldConfidence:    oldConfidence,
		NewConfidence:    newConfidence,
		PropagationType:  "validation",
		PropagationTime:  time.Now(),
		DistanceFactor:   distanceFactor,
		SimilarityFactor: similarityFactor,
	}
	
	pe.propagationHistory = append(pe.propagationHistory, event)
	
	// Keep only last 1000 events
	if len(pe.propagationHistory) > 1000 {
		pe.propagationHistory = pe.propagationHistory[len(pe.propagationHistory)-1000:]
	}
}

// initializeDefaultRules sets up default propagation rules
func (pe *PropagationEngine) initializeDefaultRules() {
	// Wall to wall propagation
	pe.propagationRules["wall_to_wall"] = &PropagationRule{
		ID:              "wall_to_wall",
		SourceType:      arxobject.StructuralWall,
		TargetType:      arxobject.StructuralWall,
		PropagationType: "structural",
		DecayFactor:     0.9,
		MaxDistance:     10.0,
		MinSimilarity:   0.6,
	}
	
	// Column to column propagation
	pe.propagationRules["column_to_column"] = &PropagationRule{
		ID:              "column_to_column",
		SourceType:      arxobject.StructuralColumn,
		TargetType:      arxobject.StructuralColumn,
		PropagationType: "structural",
		DecayFactor:     0.85,
		MaxDistance:     15.0,
		MinSimilarity:   0.7,
	}
	
	// Electrical panel to outlet propagation
	pe.propagationRules["panel_to_outlet"] = &PropagationRule{
		ID:              "panel_to_outlet",
		SourceType:      arxobject.ElectricalPanel,
		TargetType:      arxobject.ElectricalOutlet,
		PropagationType: "electrical",
		DecayFactor:     0.8,
		MaxDistance:     50.0,
		MinSimilarity:   0.4,
	}
	
	// HVAC unit to duct propagation
	pe.propagationRules["hvac_to_duct"] = &PropagationRule{
		ID:              "hvac_to_duct",
		SourceType:      arxobject.HVACUnit,
		TargetType:      arxobject.HVACDuct,
		PropagationType: "mechanical",
		DecayFactor:     0.85,
		MaxDistance:     30.0,
		MinSimilarity:   0.5,
	}
}

// Helper methods

func (pe *PropagationEngine) areTypesRelated(type1, type2 arxobject.ArxObjectType) bool {
	// Structural elements are related
	if pe.isStructural(type1) && pe.isStructural(type2) {
		return true
	}
	
	// Electrical elements are related
	if pe.isElectrical(type1) && pe.isElectrical(type2) {
		return true
	}
	
	// MEP elements are related
	if pe.isMEP(type1) && pe.isMEP(type2) {
		return true
	}
	
	return false
}

func (pe *PropagationEngine) getSystem(objType arxobject.ArxObjectType) string {
	if pe.isStructural(objType) {
		return "structural"
	}
	if pe.isElectrical(objType) {
		return "electrical"
	}
	if pe.isMEP(objType) {
		return "mep"
	}
	if pe.isFireSafety(objType) {
		return "fire_safety"
	}
	return "other"
}

func (pe *PropagationEngine) isStructural(objType arxobject.ArxObjectType) bool {
	return objType >= arxobject.StructuralBeam && objType <= arxobject.StructuralFoundation
}

func (pe *PropagationEngine) isElectrical(objType arxobject.ArxObjectType) bool {
	return objType >= arxobject.ElectricalOutlet && objType <= arxobject.ElectricalConduit
}

func (pe *PropagationEngine) isMEP(objType arxobject.ArxObjectType) bool {
	return objType >= arxobject.HVACDuct && objType <= arxobject.PlumbingFixture
}

func (pe *PropagationEngine) isFireSafety(objType arxobject.ArxObjectType) bool {
	return objType >= arxobject.FireSprinkler && objType <= arxobject.SmokeDetector
}

func (pe *PropagationEngine) getObjectTypeName(t arxobject.ArxObjectType) string {
	typeNames := map[arxobject.ArxObjectType]string{
		arxobject.StructuralWall:   "wall",
		arxobject.StructuralColumn: "column",
		arxobject.StructuralBeam:   "beam",
		arxobject.ElectricalPanel:  "electrical_panel",
		arxobject.HVACUnit:         "hvac_unit",
		// Add more as needed
	}
	
	if name, ok := typeNames[t]; ok {
		return name
	}
	return "unknown"
}

func (pe *PropagationEngine) clamp(value, min, max float32) float32 {
	if value < min {
		return min
	}
	if value > max {
		return max
	}
	return value
}

// GetPropagationStats returns statistics about propagation
func (pe *PropagationEngine) GetPropagationStats() map[string]interface{} {
	pe.mu.RLock()
	defer pe.mu.RUnlock()
	
	totalEvents := len(pe.propagationHistory)
	avgImprovement := float32(0)
	
	if totalEvents > 0 {
		for _, event := range pe.propagationHistory {
			avgImprovement += (event.NewConfidence - event.OldConfidence)
		}
		avgImprovement /= float32(totalEvents)
	}
	
	return map[string]interface{}{
		"total_propagation_events": totalEvents,
		"average_improvement":      avgImprovement,
		"active_rules":            len(pe.propagationRules),
		"last_propagation":        pe.propagationHistory[len(pe.propagationHistory)-1].PropagationTime,
	}
}