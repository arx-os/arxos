package models

import (
	"time"
)

// ValidationTask represents a pending validation task
type ValidationTask struct {
	ID              int64     `json:"id" db:"id"`
	ObjectID        string    `json:"object_id" db:"object_id"`
	ObjectType      string    `json:"object_type" db:"object_type"`
	Confidence      float32   `json:"confidence" db:"confidence"`
	Priority        int       `json:"priority" db:"priority"`
	PotentialImpact float32   `json:"potential_impact" db:"potential_impact"`
	SimilarCount    int       `json:"similar_count" db:"similar_count"`
	Status          string    `json:"status" db:"status"`
	CreatedAt       time.Time `json:"created_at" db:"created_at"`
	CompletedAt     *time.Time `json:"completed_at,omitempty" db:"completed_at"`
	CompletedBy     string    `json:"completed_by,omitempty" db:"completed_by"`
}

// ValidationSubmission represents a validation submission
type ValidationSubmission struct {
	ObjectID        string                 `json:"object_id"`
	ValidationType  string                 `json:"validation_type"`
	Data            map[string]interface{} `json:"data"`
	Validator       string                 `json:"validator"`
	Confidence      float32                `json:"confidence"`
	Timestamp       time.Time              `json:"timestamp"`
	PhotoURL        string                 `json:"photo_url,omitempty"`
	Notes           string                 `json:"notes,omitempty"`
}

// ValidationImpact represents the impact of a validation
type ValidationImpact struct {
	ObjectID              string   `json:"object_id"`
	OldConfidence         float32  `json:"old_confidence"`
	NewConfidence         float32  `json:"new_confidence"`
	ConfidenceImprovement float32  `json:"confidence_improvement"`
	CascadedObjects       []string `json:"cascaded_objects"`
	CascadedCount         int      `json:"cascaded_count"`
	PatternLearned        bool     `json:"pattern_learned"`
	TotalConfidenceGain   float32  `json:"total_confidence_gain"`
	TimeSaved             float32  `json:"time_saved"`
}

// ValidationRecord represents a historical validation record
type ValidationRecord struct {
	ID                    int64     `json:"id" db:"id"`
	ObjectID              string    `json:"object_id" db:"object_id"`
	ValidationType        string    `json:"validation_type" db:"validation_type"`
	Validator             string    `json:"validator" db:"validator"`
	Confidence            float32   `json:"confidence" db:"confidence"`
	ValidatedAt           time.Time `json:"validated_at" db:"validated_at"`
	OldConfidence         float32   `json:"old_confidence" db:"old_confidence"`
	NewConfidence         float32   `json:"new_confidence" db:"new_confidence"`
	ConfidenceImprovement float32   `json:"confidence_improvement" db:"confidence_improvement"`
	CascadedCount         int       `json:"cascaded_count" db:"cascaded_count"`
	PatternLearned        bool      `json:"pattern_learned" db:"pattern_learned"`
	TimeSaved             float32   `json:"time_saved" db:"time_saved"`
}

// ValidatorStats represents statistics for a validator
type ValidatorStats struct {
	Rank              int       `json:"rank"`
	Validator         string    `json:"validator" db:"validator"`
	TotalValidations  int       `json:"total_validations" db:"total_validations"`
	AvgImprovement    float32   `json:"avg_improvement" db:"avg_improvement"`
	TotalCascaded     int       `json:"total_cascaded" db:"total_cascaded"`
	PatternsLearned   int       `json:"patterns_learned" db:"patterns_learned"`
	TotalTimeSaved    float32   `json:"total_time_saved" db:"total_time_saved"`
	Points            int       `json:"points"`
	LastValidation    time.Time `json:"last_validation" db:"last_validation"`
}

// ValidationPattern represents a learned validation pattern
type ValidationPattern struct {
	ID               string                 `json:"id" db:"pattern_id"`
	ObjectType       string                 `json:"object_type" db:"object_type"`
	PatternData      map[string]interface{} `json:"pattern_data" db:"pattern_data"`
	Confidence       float32                `json:"confidence" db:"confidence"`
	OccurrenceCount  int                    `json:"occurrence_count" db:"occurrence_count"`
	ValidationSource string                 `json:"validation_source" db:"validation_source"`
	CreatedAt        time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time              `json:"updated_at" db:"updated_at"`
}

// ValidationQuality represents quality metrics for validations
type ValidationQuality struct {
	TotalValidations      int     `json:"total_validations"`
	AverageConfidence     float32 `json:"average_confidence"`
	PatternCoverage       float32 `json:"pattern_coverage"`
	CascadeEfficiency     float32 `json:"cascade_efficiency"`
	ValidationCompleteness float32 `json:"validation_completeness"`
}