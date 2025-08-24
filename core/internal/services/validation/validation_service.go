package validation

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/models"
)

// ValidationService handles validation business logic
type ValidationService struct {
	db            *sql.DB
	patternEngine *PatternEngine
	cache         *ValidationCache
}

// NewValidationService creates a new validation service
func NewValidationService(db *sql.DB) *ValidationService {
	return &ValidationService{
		db:            db,
		patternEngine: NewPatternEngine(),
		cache:         NewValidationCache(),
	}
}

// PatternEngine handles pattern learning and application
type PatternEngine struct {
	patterns       map[string]*ValidationPattern
	patternHistory []PatternApplication
}

// ValidationPattern represents a learned pattern
type ValidationPattern struct {
	ID               string                 `json:"id"`
	ObjectType       string                 `json:"object_type"`
	Pattern          map[string]interface{} `json:"pattern"`
	Confidence       float32                `json:"confidence"`
	OccurrenceCount  int                    `json:"occurrence_count"`
	LastUpdated      time.Time              `json:"last_updated"`
	ValidationSource string                 `json:"validation_source"`
}

// PatternApplication represents a pattern application event
type PatternApplication struct {
	PatternID       string    `json:"pattern_id"`
	ObjectID        string    `json:"object_id"`
	OldConfidence   float32   `json:"old_confidence"`
	NewConfidence   float32   `json:"new_confidence"`
	ApplicationTime time.Time `json:"application_time"`
}

// ValidationCache provides caching for validation data
type ValidationCache struct {
	pendingTasks map[string]*models.ValidationTask
	patterns     map[string]*ValidationPattern
	lastUpdate   time.Time
}

// GetPendingValidationsFixed retrieves pending validation tasks with enhanced error handling
func (s *ValidationService) GetPendingValidationsFixed(priority, objectType, limit string) ([]*models.ValidationTask, error) {
	return s.GetPendingValidations(priority, objectType, limit)
}

// GetPendingValidations retrieves pending validation tasks
func (s *ValidationService) GetPendingValidations(priority, objectType, limit string) ([]*models.ValidationTask, error) {
	// Check cache first
	if tasks := s.cache.GetPendingTasks(); tasks != nil && time.Since(s.cache.lastUpdate) < 5*time.Minute {
		return s.filterTasks(tasks, priority, objectType, limit), nil
	}

	// Build query
	query := `
		SELECT 
			v.id, v.object_id, v.object_type, v.confidence,
			v.priority, v.potential_impact, v.created_at,
			COUNT(s.id) as similar_count
		FROM validation_tasks v
		LEFT JOIN arx_objects s ON s.type = v.object_type 
			AND s.id != v.object_id
			AND s.confidence < 0.6
		WHERE v.status = 'pending'
	`

	args := []interface{}{}
	argCount := 1

	if priority != "" {
		query += fmt.Sprintf(" AND v.priority >= $%d", argCount)
		args = append(args, priority)
		argCount++
	}

	if objectType != "" {
		query += fmt.Sprintf(" AND v.object_type = $%d", argCount)
		args = append(args, objectType)
		argCount++
	}

	query += `
		GROUP BY v.id, v.object_id, v.object_type, v.confidence,
			v.priority, v.potential_impact, v.created_at
		ORDER BY v.priority DESC, v.potential_impact DESC
	`

	if limit != "" {
		query += fmt.Sprintf(" LIMIT $%d", argCount)
		args = append(args, limit)
	}

	rows, err := s.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []*models.ValidationTask
	for rows.Next() {
		task := &models.ValidationTask{}
		err := rows.Scan(
			&task.ID, &task.ObjectID, &task.ObjectType,
			&task.Confidence, &task.Priority, &task.PotentialImpact,
			&task.CreatedAt, &task.SimilarCount,
		)
		if err != nil {
			continue
		}
		tasks = append(tasks, task)
	}

	// Update cache
	s.cache.UpdatePendingTasks(tasks)

	return tasks, nil
}

// CreateValidationTask creates a new validation task
func (s *ValidationService) CreateValidationTask(task *models.ValidationTask) error {
	query := `
		INSERT INTO validation_tasks (
			object_id, object_type, confidence, priority,
			potential_impact, status, created_at
		) VALUES ($1, $2, $3, $4, $5, 'pending', $6)
		RETURNING id
	`

	err := s.db.QueryRow(
		query,
		task.ObjectID, task.ObjectType, task.Confidence,
		task.Priority, task.PotentialImpact, task.CreatedAt,
	).Scan(&task.ID)

	if err != nil {
		return err
	}

	// Invalidate cache
	s.cache.InvalidatePendingTasks()

	return nil
}

// SaveValidation saves a validation and its impact
func (s *ValidationService) SaveValidation(
	submission *models.ValidationSubmission,
	impact *models.ValidationImpact,
) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Save validation record
	validationQuery := `
		INSERT INTO arx_validations (
			object_id, validation_type, validator, confidence,
			data, photo_url, notes, validated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		RETURNING id
	`

	dataJSON, _ := json.Marshal(submission.Data)
	var validationID int64

	err = tx.QueryRow(
		validationQuery,
		submission.ObjectID, submission.ValidationType,
		submission.Validator, submission.Confidence,
		dataJSON, submission.PhotoURL, submission.Notes,
		submission.Timestamp,
	).Scan(&validationID)

	if err != nil {
		return err
	}

	// Save impact record
	impactQuery := `
		INSERT INTO validation_impacts (
			validation_id, object_id, old_confidence, new_confidence,
			confidence_improvement, cascaded_objects, cascaded_count,
			pattern_learned, total_confidence_gain, time_saved,
			created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
	`

	cascadedJSON, _ := json.Marshal(impact.CascadedObjects)

	_, err = tx.Exec(
		impactQuery,
		validationID, impact.ObjectID, impact.OldConfidence,
		impact.NewConfidence, impact.ConfidenceImprovement,
		cascadedJSON, impact.CascadedCount, impact.PatternLearned,
		impact.TotalConfidenceGain, impact.TimeSaved,
		time.Now(),
	)

	if err != nil {
		return err
	}

	// Update object confidence in database
	updateQuery := `
		UPDATE arx_objects 
		SET confidence = $1,
			validation_state = 'validated',
			validated_by = $2,
			validated_at = $3
		WHERE id = $4
	`

	confidenceJSON, _ := json.Marshal(map[string]float32{
		"overall":        impact.NewConfidence,
		"classification": submission.Confidence,
		"position":       submission.Confidence * 0.9,
		"properties":     submission.Confidence * 0.85,
		"relationships":  submission.Confidence * 0.7,
	})

	_, err = tx.Exec(
		updateQuery,
		confidenceJSON, submission.Validator,
		submission.Timestamp, submission.ObjectID,
	)

	if err != nil {
		return err
	}

	// Update validation task status
	taskUpdateQuery := `
		UPDATE validation_tasks
		SET status = 'completed',
			completed_at = $1,
			completed_by = $2
		WHERE object_id = $3 AND status = 'pending'
	`

	_, err = tx.Exec(taskUpdateQuery, time.Now(), submission.Validator, submission.ObjectID)
	if err != nil {
		return err
	}

	return tx.Commit()
}

// LearnPatternFixed learns a pattern from validation with enhanced error handling
func (s *ValidationService) LearnPatternFixed(submission models.ValidationSubmission) (bool, error) {
	// Get the validated object
	validated, err := s.getObjectFromDB(submission.ObjectID)
	if err != nil {
		return false, fmt.Errorf("failed to get validated object: %w", err)
	}

	// Find similar objects
	similar, err := s.findSimilarObjectsForPattern(validated)
	if err != nil {
		return false, fmt.Errorf("failed to find similar objects: %w", err)
	}

	return s.LearnPattern(validated, similar, submission), nil
}

// SaveValidationFixed saves validation with enhanced error handling
func (s *ValidationService) SaveValidationFixed(submission *models.ValidationSubmission) error {
	// Create mock impact for backward compatibility
	impact := &models.ValidationImpact{
		ObjectID:              submission.ObjectID,
		OldConfidence:         0.5, // Mock old confidence
		NewConfidence:         submission.Confidence,
		ConfidenceImprovement: submission.Confidence - 0.5,
		CascadedObjects:       []string{},
		CascadedCount:         0,
		PatternLearned:        false,
		TotalConfidenceGain:   submission.Confidence - 0.5,
		TimeSaved:             0,
	}

	return s.SaveValidation(submission, impact)
}

// LearnPattern learns a pattern from validation
func (s *ValidationService) LearnPattern(
	validated *arxobject.ArxObject,
	similar []*arxobject.ArxObject,
	submission models.ValidationSubmission,
) bool {

	if len(similar) < 3 {
		return false // Not enough similar objects for pattern
	}

	// Extract pattern features
	pattern := s.extractPattern(validated, submission)
	patternKey := fmt.Sprintf("%s_%v", getObjectTypeName(arxobject.ArxObjectType(validated.Type)), pattern["key"])

	// Check if pattern exists
	existingPattern, exists := s.patternEngine.patterns[patternKey]
	if exists {
		// Update existing pattern
		existingPattern.OccurrenceCount++
		existingPattern.Confidence = (existingPattern.Confidence*float32(existingPattern.OccurrenceCount-1) +
			submission.Confidence) / float32(existingPattern.OccurrenceCount)
		existingPattern.LastUpdated = time.Now()

		// Save to database
		s.updatePatternInDB(existingPattern)
	} else {
		// Create new pattern
		newPattern := &ValidationPattern{
			ID:               patternKey,
			ObjectType:       getObjectTypeName(arxobject.ArxObjectType(validated.Type)),
			Pattern:          pattern,
			Confidence:       submission.Confidence,
			OccurrenceCount:  1,
			LastUpdated:      time.Now(),
			ValidationSource: submission.Validator,
		}

		s.patternEngine.patterns[patternKey] = newPattern

		// Save to database
		s.savePatternToDB(newPattern)
	}

	// Apply pattern to similar objects
	for _, obj := range similar {
		if s.matchesPattern(obj, pattern) {
			oldConfidence := obj.Confidence.Overall

			// Apply pattern boost
			s.applyPatternToObject(obj, existingPattern)

			// Record application
			s.patternEngine.patternHistory = append(s.patternEngine.patternHistory, PatternApplication{
				PatternID:       patternKey,
				ObjectID:        fmt.Sprintf("%d", obj.ID),
				OldConfidence:   oldConfidence,
				NewConfidence:   obj.Confidence.Overall,
				ApplicationTime: time.Now(),
			})
		}
	}

	return true
}

// GetValidationHistory retrieves validation history
func (s *ValidationService) GetValidationHistory(
	objectID, validator, startDate, endDate string,
) ([]models.ValidationRecord, error) {

	query := `
		SELECT 
			v.id, v.object_id, v.validation_type, v.validator,
			v.confidence, v.validated_at,
			i.old_confidence, i.new_confidence, i.confidence_improvement,
			i.cascaded_count, i.pattern_learned, i.time_saved
		FROM arx_validations v
		LEFT JOIN validation_impacts i ON i.validation_id = v.id
		WHERE 1=1
	`

	args := []interface{}{}
	argCount := 1

	if objectID != "" {
		query += fmt.Sprintf(" AND v.object_id = $%d", argCount)
		args = append(args, objectID)
		argCount++
	}

	if validator != "" {
		query += fmt.Sprintf(" AND v.validator = $%d", argCount)
		args = append(args, validator)
		argCount++
	}

	if startDate != "" {
		query += fmt.Sprintf(" AND v.validated_at >= $%d", argCount)
		args = append(args, startDate)
		argCount++
	}

	if endDate != "" {
		query += fmt.Sprintf(" AND v.validated_at <= $%d", argCount)
		args = append(args, endDate)
		argCount++
	}

	query += " ORDER BY v.validated_at DESC"

	rows, err := s.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var records []models.ValidationRecord
	for rows.Next() {
		var record models.ValidationRecord
		err := rows.Scan(
			&record.ID, &record.ObjectID, &record.ValidationType,
			&record.Validator, &record.Confidence, &record.ValidatedAt,
			&record.OldConfidence, &record.NewConfidence,
			&record.ConfidenceImprovement, &record.CascadedCount,
			&record.PatternLearned, &record.TimeSaved,
		)
		if err != nil {
			continue
		}
		records = append(records, record)
	}

	return records, nil
}

// GetLeaderboard retrieves validation leaderboard
func (s *ValidationService) GetLeaderboard(period string) ([]models.ValidatorStats, error) {
	var timeFilter string

	switch period {
	case "daily":
		timeFilter = "AND v.validated_at >= CURRENT_DATE"
	case "weekly":
		timeFilter = "AND v.validated_at >= CURRENT_DATE - INTERVAL '7 days'"
	case "monthly":
		timeFilter = "AND v.validated_at >= CURRENT_DATE - INTERVAL '30 days'"
	default:
		timeFilter = ""
	}

	query := fmt.Sprintf(`
		SELECT 
			v.validator,
			COUNT(v.id) as total_validations,
			AVG(i.confidence_improvement) as avg_improvement,
			SUM(i.cascaded_count) as total_cascaded,
			SUM(CASE WHEN i.pattern_learned THEN 1 ELSE 0 END) as patterns_learned,
			SUM(i.time_saved) as total_time_saved,
			MAX(v.validated_at) as last_validation
		FROM arx_validations v
		LEFT JOIN validation_impacts i ON i.validation_id = v.id
		WHERE 1=1 %s
		GROUP BY v.validator
		ORDER BY total_validations DESC, avg_improvement DESC
		LIMIT 20
	`, timeFilter)

	rows, err := s.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var stats []models.ValidatorStats
	rank := 1
	for rows.Next() {
		var stat models.ValidatorStats
		stat.Rank = rank

		err := rows.Scan(
			&stat.Validator, &stat.TotalValidations,
			&stat.AvgImprovement, &stat.TotalCascaded,
			&stat.PatternsLearned, &stat.TotalTimeSaved,
			&stat.LastValidation,
		)
		if err != nil {
			continue
		}

		// Calculate points (simple scoring system)
		stat.Points = stat.TotalValidations*10 +
			int(stat.AvgImprovement*100) +
			stat.TotalCascaded*2 +
			stat.PatternsLearned*50

		stats = append(stats, stat)
		rank++
	}

	return stats, nil
}

// Helper methods

func (s *ValidationService) extractPattern(
	obj *arxobject.ArxObject,
	submission models.ValidationSubmission,
) map[string]interface{} {

	pattern := make(map[string]interface{})

	// Extract key features
	pattern["type"] = obj.Type
	pattern["has_dimensions"] = obj.Width > 0 && obj.Height > 0
	pattern["scale_level"] = obj.ScaleMin

	// Extract validation-specific features
	if submission.Data != nil {
		for key, value := range submission.Data {
			pattern["val_"+key] = value
		}
	}

	// Create pattern key
	pattern["key"] = fmt.Sprintf("%s_%d_%v",
		obj.Type, obj.ScaleMin, pattern["has_dimensions"])

	return pattern
}

func (s *ValidationService) matchesPattern(
	obj *arxobject.ArxObject,
	pattern map[string]interface{},
) bool {

	// Check type match
	if patternType, ok := pattern["type"].(string); ok {
		if obj.Type != patternType {
			return false
		}
	}

	// Check scale level
	if scaleLevel, ok := pattern["scale_level"].(int); ok {
		if obj.ScaleMin != scaleLevel {
			return false
		}
	}

	// Check dimensions
	if hasDims, ok := pattern["has_dimensions"].(bool); ok {
		objHasDims := obj.Width > 0 && obj.Height > 0
		if hasDims != objHasDims {
			return false
		}
	}

	// If all checks pass, consider it a match
	return true
}

func (s *ValidationService) applyPatternToObject(
	obj *arxobject.ArxObject,
	pattern *ValidationPattern,
) {
	if pattern == nil {
		return
	}

	// Apply confidence boost based on pattern confidence
	boost := float32(pattern.Confidence * 0.3) // 30% of pattern confidence

	// Boost different dimensions
	obj.Confidence.Classification = minFloat32(obj.Confidence.Classification+boost, 0.90)
	obj.Confidence.Properties = minFloat32(obj.Confidence.Properties+float32(boost*0.8), 0.90)

	// Recalculate overall
	obj.Confidence.CalculateOverall()
}

func (s *ValidationService) savePatternToDB(pattern *ValidationPattern) error {
	query := `
		INSERT INTO arx_patterns (
			pattern_id, object_type, pattern_data, confidence,
			occurrence_count, validation_source, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`

	patternJSON, _ := json.Marshal(pattern.Pattern)

	_, err := s.db.Exec(
		query,
		pattern.ID, pattern.ObjectType, patternJSON,
		pattern.Confidence, pattern.OccurrenceCount,
		pattern.ValidationSource, time.Now(), pattern.LastUpdated,
	)

	return err
}

func (s *ValidationService) updatePatternInDB(pattern *ValidationPattern) error {
	query := `
		UPDATE arx_patterns
		SET confidence = $1,
			occurrence_count = $2,
			updated_at = $3
		WHERE pattern_id = $4
	`

	_, err := s.db.Exec(
		query,
		pattern.Confidence, pattern.OccurrenceCount,
		pattern.LastUpdated, pattern.ID,
	)

	return err
}

func (s *ValidationService) filterTasks(
	tasks []*models.ValidationTask,
	priority, objectType, limit string,
) []*models.ValidationTask {

	var filtered []*models.ValidationTask

	for _, task := range tasks {
		// Filter by priority
		if priority != "" {
			var minPriority int
			fmt.Sscanf(priority, "%d", &minPriority)
			if task.Priority < minPriority {
				continue
			}
		}

		// Filter by type
		if objectType != "" && task.ObjectType != objectType {
			continue
		}

		filtered = append(filtered, task)

		// Apply limit
		if limit != "" {
			var maxCount int
			fmt.Sscanf(limit, "%d", &maxCount)
			if len(filtered) >= maxCount {
				break
			}
		}
	}

	return filtered
}

// Cache methods

func NewValidationCache() *ValidationCache {
	return &ValidationCache{
		pendingTasks: make(map[string]*models.ValidationTask),
		patterns:     make(map[string]*ValidationPattern),
		lastUpdate:   time.Now(),
	}
}

func (c *ValidationCache) GetPendingTasks() []*models.ValidationTask {
	if time.Since(c.lastUpdate) > 5*time.Minute {
		return nil // Cache expired
	}

	tasks := make([]*models.ValidationTask, 0, len(c.pendingTasks))
	for _, task := range c.pendingTasks {
		tasks = append(tasks, task)
	}
	return tasks
}

func (c *ValidationCache) UpdatePendingTasks(tasks []*models.ValidationTask) {
	c.pendingTasks = make(map[string]*models.ValidationTask)
	for _, task := range tasks {
		c.pendingTasks[task.ObjectID] = task
	}
	c.lastUpdate = time.Now()
}

func (c *ValidationCache) InvalidatePendingTasks() {
	c.pendingTasks = make(map[string]*models.ValidationTask)
	c.lastUpdate = time.Time{}
}

// Pattern Engine methods

func NewPatternEngine() *PatternEngine {
	return &PatternEngine{
		patterns:       make(map[string]*ValidationPattern),
		patternHistory: make([]PatternApplication, 0),
	}
}

// Helper functions

func getObjectTypeName(t arxobject.ArxObjectType) string {
	// This should match the implementation in validation.go
	typeNames := map[arxobject.ArxObjectType]string{
		arxobject.StructuralWall:   "wall",
		arxobject.StructuralColumn: "column",
		arxobject.StructuralBeam:   "beam",
		// Add more as needed
	}

	if name, ok := typeNames[t]; ok {
		return name
	}
	return "unknown"
}

// Helper methods for fixed validation service

func (s *ValidationService) getObjectFromDB(objectID string) (*arxobject.ArxObject, error) {
	query := `
		SELECT id, uuid, type, system, x, y, z,
			   width, height, depth, scale_min, scale_max,
			   building_id, floor_id, room_id, parent_id,
			   properties, confidence, extraction_method, source,
			   created_at, updated_at
		FROM arx_objects WHERE id = $1
	`

	var obj arxobject.ArxObject
	var confidenceJSON []byte

	err := s.db.QueryRow(query, objectID).Scan(
		&obj.ID, &obj.UUID, &obj.Type, &obj.System, &obj.X, &obj.Y, &obj.Z,
		&obj.Width, &obj.Height, &obj.Depth, &obj.ScaleMin, &obj.ScaleMax,
		&obj.BuildingID, &obj.FloorID, &obj.RoomID, &obj.ParentID,
		&obj.Properties, &confidenceJSON, &obj.ExtractionMethod, &obj.Source,
		&obj.CreatedAt, &obj.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to get object %s: %w", objectID, err)
	}

	json.Unmarshal(confidenceJSON, &obj.Confidence)
	return &obj, nil
}

func (s *ValidationService) findSimilarObjectsForPattern(obj *arxobject.ArxObject) ([]*arxobject.ArxObject, error) {
	query := `
		SELECT id, uuid, type, system, x, y, z,
			   width, height, depth, scale_min, scale_max,
			   properties, confidence
		FROM arx_objects
		WHERE type = $1 AND system = $2
		  AND ABS(width - $3) < $4
		  AND ABS(height - $5) < $6
		  AND id != $7
		  AND validated_at IS NULL
		LIMIT 50
	`

	tolerance := int64(100000) // 0.1mm tolerance in nanometers

	rows, err := s.db.Query(query,
		obj.Type, obj.System,
		obj.Width, tolerance,
		obj.Height, tolerance,
		obj.ID,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to find similar objects: %w", err)
	}
	defer rows.Close()

	var similar []*arxobject.ArxObject
	for rows.Next() {
		var simObj arxobject.ArxObject
		var confidenceJSON []byte

		err := rows.Scan(
			&simObj.ID, &simObj.UUID, &simObj.Type, &simObj.System,
			&simObj.X, &simObj.Y, &simObj.Z,
			&simObj.Width, &simObj.Height, &simObj.Depth,
			&simObj.ScaleMin, &simObj.ScaleMax,
			&simObj.Properties, &confidenceJSON,
		)
		if err != nil {
			continue
		}

		json.Unmarshal(confidenceJSON, &simObj.Confidence)
		similar = append(similar, &simObj)
	}

	return similar, nil
}

func minFloat32(a, b float32) float32 {
	if a < b {
		return a
	}
	return b
}
