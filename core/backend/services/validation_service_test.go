package services

import (
	"fmt"
	"testing"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/models"
	testhelpers "github.com/arxos/arxos/core/backend/testing"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gorm.io/gorm"
)

// TestValidationServiceSuite contains all validation service tests
type TestValidationServiceSuite struct {
	db      *gorm.DB
	service *ValidationService
	engine  *arxobject.Engine
}

// setupTestSuite initializes the test suite
func setupTestSuite(t *testing.T) *TestValidationServiceSuite {
	db := testhelpers.SetupTestDB(t)
	service := NewValidationService(db)
	engine := testhelpers.SetupTestEngine()
	
	return &TestValidationServiceSuite{
		db:      db,
		service: service,
		engine:  engine,
	}
}

func TestNewValidationService(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	
	db := testhelpers.SetupTestDB(t)
	service := NewValidationService(db)
	
	assert.NotNil(t, service)
	assert.NotNil(t, service.db)
	assert.NotNil(t, service.sqlDB)
	assert.NotNil(t, service.patternEngine)
	assert.NotNil(t, service.cache)
}

func TestGetPendingValidations(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	suite := setupTestSuite(t)
	
	// Create test validation tasks
	tasks := []*models.ValidationTask{
		{
			ObjectID:        "wall_001",
			ObjectType:      "wall",
			Confidence:      0.45,
			Priority:        8,
			PotentialImpact: 0.75,
			CreatedAt:       time.Now(),
		},
		{
			ObjectID:        "door_001",
			ObjectType:      "door", 
			Confidence:      0.55,
			Priority:        6,
			PotentialImpact: 0.6,
			CreatedAt:       time.Now(),
		},
	}
	
	// Insert test data
	for _, task := range tasks {
		err := suite.db.Create(task).Error
		require.NoError(t, err)
	}
	
	tests := []struct {
		name         string
		priority     string
		objectType   string
		limit        string
		expectedLen  int
		expectedErr  bool
	}{
		{
			name:        "Get all pending validations",
			priority:    "",
			objectType:  "",
			limit:       "",
			expectedLen: 2,
			expectedErr: false,
		},
		{
			name:        "Filter by priority",
			priority:    "7",
			objectType:  "",
			limit:       "",
			expectedLen: 1,
			expectedErr: false,
		},
		{
			name:        "Filter by object type",
			priority:    "",
			objectType:  "wall",
			limit:       "",
			expectedLen: 1,
			expectedErr: false,
		},
		{
			name:        "Limit results",
			priority:    "",
			objectType:  "",
			limit:       "1",
			expectedLen: 1,
			expectedErr: false,
		},
	}
	
	testhelpers.RunTableTests(t, toTableTests(tests), func(t *testing.T, test testhelpers.TableTest) {
		testCase := test.Input.(struct {
			priority   string
			objectType string
			limit      string
		})
		expected := test.ExpectedOutput.(struct {
			expectedLen int
			expectedErr bool
		})
		
		result, err := suite.service.GetPendingValidations(
			testCase.priority, testCase.objectType, testCase.limit)
		
		if expected.expectedErr {
			assert.Error(t, err)
		} else {
			assert.NoError(t, err)
			assert.Len(t, result, expected.expectedLen)
		}
	})
}

func TestCreateValidationTask(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	suite := setupTestSuite(t)
	
	task := &models.ValidationTask{
		ObjectID:        "test_object_001",
		ObjectType:      "wall",
		Confidence:      0.42,
		Priority:        7,
		PotentialImpact: 0.8,
		CreatedAt:       time.Now(),
	}
	
	err := suite.service.CreateValidationTask(task)
	assert.NoError(t, err)
	assert.NotZero(t, task.ID)
	
	// Verify task was created in database
	var saved models.ValidationTask
	err = suite.db.Where("object_id = ?", task.ObjectID).First(&saved).Error
	assert.NoError(t, err)
	assert.Equal(t, task.ObjectID, saved.ObjectID)
	assert.Equal(t, task.ObjectType, saved.ObjectType)
	testhelpers.AssertFloat32Equal(t, task.Confidence, saved.Confidence, 0.001)
}

func TestSaveValidation(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	suite := setupTestSuite(t)
	
	submission := &models.ValidationSubmission{
		ObjectID:       "wall_001",
		ValidationType: "dimension",
		Data: map[string]interface{}{
			"length":   10.5,
			"width":    0.15,
			"material": "concrete",
		},
		Validator:  "test_validator",
		Confidence: 0.95,
		Timestamp:  time.Now(),
		PhotoURL:   "https://example.com/photo.jpg",
		Notes:      "Measured with laser scanner",
	}
	
	impact := &models.ValidationImpact{
		ObjectID:              "wall_001",
		OldConfidence:         0.45,
		NewConfidence:         0.85,
		ConfidenceImprovement: 0.40,
		CascadedObjects:       []string{"wall_002", "wall_003"},
		CascadedCount:         2,
		PatternLearned:        true,
		TotalConfidenceGain:   0.8,
		TimeSaved:             5.0,
	}
	
	// Test performance constraint
	testhelpers.AssertPerformance(t, 100*time.Millisecond, func() {
		err := suite.service.SaveValidation(submission, impact)
		assert.NoError(t, err)
	})
}

func TestLearnPattern(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	suite := setupTestSuite(t)
	
	// Create validated object
	objID := suite.engine.CreateObjectWithConfidence(
		arxobject.StructuralWall, 10, 20, 0,
		arxobject.NewConfidenceScore(0.9, 0.9, 0.9, 0.9),
	)
	validated, exists := suite.engine.GetObject(objID)
	require.True(t, exists)
	
	// Create similar objects
	similar := []*arxobject.ArxObject{}
	for i := 0; i < 5; i++ {
		simObjID := suite.engine.CreateObjectWithConfidence(
			arxobject.StructuralWall, float32(10+i*2), 20, 0,
			arxobject.NewConfidenceScore(0.5, 0.5, 0.5, 0.5),
		)
		simObj, exists := suite.engine.GetObject(simObjID)
		require.True(t, exists)
		similar = append(similar, simObj)
	}
	
	submission := models.ValidationSubmission{
		ObjectID:       "wall_001",
		ValidationType: "dimension",
		Data: map[string]interface{}{
			"material": "concrete",
			"thickness": 0.15,
		},
		Validator:  "expert_validator",
		Confidence: 0.95,
		Timestamp:  time.Now(),
	}
	
	// Test with enough similar objects
	learned := suite.service.LearnPattern(validated, similar, submission)
	assert.True(t, learned)
	
	// Test with too few similar objects
	learnedFew := suite.service.LearnPattern(validated, similar[:2], submission)
	assert.False(t, learnedFew)
}

func TestGetValidationHistory(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	suite := setupTestSuite(t)
	
	// Create test validation records
	testRecords := []models.ValidationRecord{
		{
			ID:                    1,
			ObjectID:              "wall_001",
			ValidationType:        "dimension",
			Validator:             "validator_1",
			Confidence:            0.95,
			ValidatedAt:           time.Now(),
			OldConfidence:         0.45,
			NewConfidence:         0.85,
			ConfidenceImprovement: 0.40,
			CascadedCount:         3,
			PatternLearned:        true,
			TimeSaved:             7.5,
		},
		{
			ID:                    2,
			ObjectID:              "wall_002",
			ValidationType:        "material",
			Validator:             "validator_2",
			Confidence:            0.88,
			ValidatedAt:           time.Now().Add(-1 * time.Hour),
			OldConfidence:         0.35,
			NewConfidence:         0.75,
			ConfidenceImprovement: 0.40,
			CascadedCount:         2,
			PatternLearned:        false,
			TimeSaved:             5.0,
		},
	}
	
	// Insert test data using raw SQL since we don't have proper GORM models set up
	for _, record := range testRecords {
		query := `
			INSERT INTO arx_validations 
			(id, object_id, validation_type, validator, confidence, validated_at)
			VALUES (?, ?, ?, ?, ?, ?)
		`
		err := suite.db.Exec(query, 
			record.ID, record.ObjectID, record.ValidationType, 
			record.Validator, record.Confidence, record.ValidatedAt).Error
		require.NoError(t, err)
		
		impactQuery := `
			INSERT INTO validation_impacts
			(validation_id, object_id, old_confidence, new_confidence, 
			 confidence_improvement, cascaded_count, pattern_learned, time_saved)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		`
		err = suite.db.Exec(impactQuery,
			record.ID, record.ObjectID, record.OldConfidence, record.NewConfidence,
			record.ConfidenceImprovement, record.CascadedCount, record.PatternLearned, record.TimeSaved).Error
		require.NoError(t, err)
	}
	
	// Test getting all history
	history, err := suite.service.GetValidationHistory("", "", "", "")
	assert.NoError(t, err)
	assert.Len(t, history, 2)
	
	// Test filtering by object ID
	history, err = suite.service.GetValidationHistory("wall_001", "", "", "")
	assert.NoError(t, err)
	assert.Len(t, history, 1)
	assert.Equal(t, "wall_001", history[0].ObjectID)
	
	// Test filtering by validator
	history, err = suite.service.GetValidationHistory("", "validator_1", "", "")
	assert.NoError(t, err)
	assert.Len(t, history, 1)
	assert.Equal(t, "validator_1", history[0].Validator)
}

func TestGetLeaderboard(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	suite := setupTestSuite(t)
	
	// Create test validation data
	testData := []struct {
		validator            string
		validations          int
		avgImprovement       float32
		totalCascaded        int
		patternsLearned      int
		totalTimeSaved       float32
	}{
		{"expert_1", 15, 0.35, 45, 8, 112.5},
		{"expert_2", 12, 0.42, 38, 6, 95.0},
		{"novice_1", 8, 0.28, 20, 2, 60.0},
	}
	
	// Insert test data (simplified for testing)
	for i, data := range testData {
		for j := 0; j < data.validations; j++ {
			validationQuery := `
				INSERT INTO arx_validations (id, object_id, validator, confidence, validated_at)
				VALUES (?, ?, ?, ?, ?)
			`
			validationID := i*100 + j + 1
			err := suite.db.Exec(validationQuery,
				validationID, fmt.Sprintf("obj_%d_%d", i, j), data.validator, 0.9, time.Now()).Error
			require.NoError(t, err)
			
			impactQuery := `
				INSERT INTO validation_impacts 
				(validation_id, object_id, confidence_improvement, cascaded_count, 
				 pattern_learned, time_saved)
				VALUES (?, ?, ?, ?, ?, ?)
			`
			err = suite.db.Exec(impactQuery,
				validationID, fmt.Sprintf("obj_%d_%d", i, j), data.avgImprovement,
				data.totalCascaded/data.validations,
				j < data.patternsLearned, data.totalTimeSaved/float32(data.validations)).Error
			require.NoError(t, err)
		}
	}
	
	// Test weekly leaderboard
	leaderboard, err := suite.service.GetLeaderboard("weekly")
	assert.NoError(t, err)
	assert.GreaterOrEqual(t, len(leaderboard), 3)
	
	// Check ordering (should be by total validations DESC)
	for i := 1; i < len(leaderboard); i++ {
		assert.GreaterOrEqual(t, leaderboard[i-1].TotalValidations, leaderboard[i].TotalValidations)
	}
	
	// Check rank assignment
	for i, stat := range leaderboard {
		assert.Equal(t, i+1, stat.Rank)
	}
}

func TestValidationCache(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	
	cache := NewValidationCache()
	assert.NotNil(t, cache)
	
	// Test empty cache
	tasks := cache.GetPendingTasks()
	assert.Nil(t, tasks)
	
	// Test cache update
	testTasks := testhelpers.CreateTestValidationTasks()
	cache.UpdatePendingTasks(testTasks)
	
	// Test cache retrieval
	cachedTasks := cache.GetPendingTasks()
	assert.NotNil(t, cachedTasks)
	assert.Len(t, cachedTasks, 3)
	
	// Test cache invalidation
	cache.InvalidatePendingTasks()
	tasks = cache.GetPendingTasks()
	assert.Nil(t, tasks)
}

func TestPatternEngine(t *testing.T) {
	testhelpers.SkipIfIntegration(t)
	
	engine := NewPatternEngine()
	assert.NotNil(t, engine)
	assert.NotNil(t, engine.patterns)
	assert.NotNil(t, engine.patternHistory)
	
	// Test pattern creation
	pattern := &ValidationPattern{
		ID:               "wall_concrete_standard",
		ObjectType:       "wall",
		Pattern:          map[string]interface{}{"material": "concrete", "thickness": 0.15},
		Confidence:       0.85,
		OccurrenceCount:  1,
		LastUpdated:      time.Now(),
		ValidationSource: "expert",
	}
	
	engine.patterns[pattern.ID] = pattern
	assert.Contains(t, engine.patterns, pattern.ID)
	assert.Equal(t, pattern, engine.patterns[pattern.ID])
}

// Benchmark tests
func BenchmarkGetPendingValidations(b *testing.B) {
	helper := testhelpers.SetupBenchmark(b, 1000)
	service := NewValidationService(helper.DB)
	
	// Create test validation tasks
	for i := 0; i < 100; i++ {
		task := &models.ValidationTask{
			ObjectID:        fmt.Sprintf("obj_%d", i),
			ObjectType:      "wall",
			Confidence:      0.5,
			Priority:        5,
			PotentialImpact: 0.6,
			CreatedAt:       time.Now(),
		}
		helper.DB.Create(task)
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		_, err := service.GetPendingValidations("", "", "50")
		if err != nil {
			b.Fatal(err)
		}
	}
}

func BenchmarkLearnPattern(b *testing.B) {
	helper := testhelpers.SetupBenchmark(b, 1000)
	service := NewValidationService(helper.DB)
	
	// Create test objects
	validated, _ := helper.Engine.GetObject(helper.ObjectIDs[0])
	similar := make([]*arxobject.ArxObject, 10)
	for i := 0; i < 10; i++ {
		similar[i], _ = helper.Engine.GetObject(helper.ObjectIDs[i+1])
	}
	
	submission := models.ValidationSubmission{
		ValidationType: "dimension",
		Confidence:     0.95,
		Validator:      "benchmark_validator",
		Timestamp:      time.Now(),
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		service.LearnPattern(validated, similar, submission)
	}
}

// Helper functions for table tests
func toTableTests(tests []struct {
	name         string
	priority     string
	objectType   string
	limit        string
	expectedLen  int
	expectedErr  bool
}) []testhelpers.TableTest {
	result := make([]testhelpers.TableTest, len(tests))
	for i, test := range tests {
		result[i] = testhelpers.TableTest{
			Name: test.name,
			Input: struct {
				priority   string
				objectType string
				limit      string
			}{test.priority, test.objectType, test.limit},
			ExpectedOutput: struct {
				expectedLen int
				expectedErr bool
			}{test.expectedLen, test.expectedErr},
		}
	}
	return result
}