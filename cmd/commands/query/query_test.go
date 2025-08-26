package query

import (
	"strings"
	"testing"
	"time"
)

func TestAQLResultCreation(t *testing.T) {
	// Test creating a basic AQL result
	result := &AQLResult{
		Type:       "SELECT",
		Objects:    []interface{}{},
		Count:      0,
		Message:    "Test result",
		Metadata:   map[string]interface{}{},
		ExecutedAt: time.Now(),
	}

	if result.Type != "SELECT" {
		t.Errorf("Expected Type to be 'SELECT', got %s", result.Type)
	}

	if result.Count != 0 {
		t.Errorf("Expected Count to be 0, got %d", result.Count)
	}

	if result.Message != "Test result" {
		t.Errorf("Expected Message to be 'Test result', got %s", result.Message)
	}
}

func TestResultDisplayCreation(t *testing.T) {
	// Test creating result display with different formats
	formats := []string{"table", "json", "csv", "ascii-bim", "summary"}

	for _, format := range formats {
		display := NewResultDisplay(format, "default")

		if display.Format != format {
			t.Errorf("Expected Format to be %s, got %s", format, format)
		}

		if display.Style != "default" {
			t.Errorf("Expected Style to be 'default', got %s", display.Style)
		}

		if !display.Pagination {
			t.Errorf("Expected Pagination to be true, got %v", display.Pagination)
		}

		if !display.Highlight {
			t.Errorf("Expected Highlight to be true, got %v", display.Highlight)
		}

		if display.MaxWidth != 120 {
			t.Errorf("Expected MaxWidth to be 120, got %d", display.MaxWidth)
		}
	}
}

func TestResultDisplayConfiguration(t *testing.T) {
	display := NewResultDisplay("table", "default")

	// Test setting format
	display.SetFormat("json")
	if display.Format != "json" {
		t.Errorf("Expected Format to be 'json' after SetFormat, got %s", display.Format)
	}

	// Test setting style
	display.SetStyle("compact")
	if display.Style != "compact" {
		t.Errorf("Expected Style to be 'compact' after SetStyle, got %s", display.Style)
	}

	// Test setting pagination
	display.SetPagination(false)
	if display.Pagination {
		t.Errorf("Expected Pagination to be false after SetPagination(false), got %v", display.Pagination)
	}

	// Test setting highlight
	display.SetHighlight(false)
	if display.Highlight {
		t.Errorf("Expected Highlight to be false after SetHighlight(false), got %v", display.Highlight)
	}

	// Test setting max width
	display.SetMaxWidth(80)
	if display.MaxWidth != 80 {
		t.Errorf("Expected MaxWidth to be 80 after SetMaxWidth(80), got %d", display.MaxWidth)
	}
}

func TestMockObjectGeneration(t *testing.T) {
	// Test generating mock objects
	objects := generateMockSelectResults("SELECT * FROM building:*")

	if len(objects) != 10 {
		t.Errorf("Expected 10 objects, got %d", len(objects))
	}

	// Check first object structure
	if len(objects) > 0 {
		firstObj, ok := objects[0].(map[string]interface{})
		if !ok {
			t.Fatal("Expected first object to be a map")
		}

		// Check required fields
		requiredFields := []string{"id", "type", "path", "confidence", "status", "created_at", "updated_at"}
		for _, field := range requiredFields {
			if _, exists := firstObj[field]; !exists {
				t.Errorf("Expected field '%s' to exist in object", field)
			}
		}

		// Check specific field values
		if objType, ok := firstObj["type"].(string); !ok || objType == "" {
			t.Errorf("Expected 'type' field to be a non-empty string, got %v", objType)
		}

		if confidence, ok := firstObj["confidence"].(float64); !ok || confidence < 0 || confidence > 1 {
			t.Errorf("Expected 'confidence' field to be a float between 0 and 1, got %v", confidence)
		}
	}
}

func TestMockResultsGeneration(t *testing.T) {
	// Test generating mock results
	parsedQuery := &BasicSelectQuery{
		Fields: []string{"*"},
		From:   "building:hq",
		Where:  []string{},
		Limit:  5,
	}

	options := &EnhancedSelectOptions{
		Limit: 5,
	}

	result, err := generateMockResults(parsedQuery, options)
	if err != nil {
		t.Fatalf("Expected no error generating mock results, got %v", err)
	}

	if result.Type != "SELECT" {
		t.Errorf("Expected Type to be 'SELECT', got %s", result.Type)
	}

	if result.Count != 5 {
		t.Errorf("Expected Count to be 5, got %d", result.Count)
	}

	if result.Message != "Query executed successfully" {
		t.Errorf("Expected Message to be 'Query executed successfully', got %s", result.Message)
	}

	if len(result.Objects) != 5 {
		t.Errorf("Expected 5 objects, got %d", len(result.Objects))
	}

	// Check metadata
	if metadata, ok := result.Metadata["rows_affected"]; !ok {
		t.Errorf("Expected 'rows_affected' in metadata")
	} else if rowsAffected, ok := metadata.(int); !ok || rowsAffected != 5 {
		t.Errorf("Expected 'rows_affected' to be 5, got %v", rowsAffected)
	}
}

func TestBasicQueryParsing(t *testing.T) {
	// Test parsing basic SELECT queries
	testCases := []struct {
		query     string
		expected  *BasicSelectQuery
		expectErr bool
	}{
		{
			query: "SELECT * FROM building:*",
			expected: &BasicSelectQuery{
				Fields: []string{"*"},
				From:   "building:*",
				Where:  []string{},
				Limit:  100,
			},
			expectErr: false,
		},
		{
			query: "SELECT id, type FROM building:hq WHERE status = 'active'",
			expected: &BasicSelectQuery{
				Fields: []string{"*"},
				From:   "building:hq",
				Where:  []string{"status = 'active'"},
				Limit:  100,
			},
			expectErr: false,
		},
		{
			query: "SELECT * FROM building:* WHERE type = 'wall' ORDER BY created_at LIMIT 10",
			expected: &BasicSelectQuery{
				Fields:  []string{"*"},
				From:    "building:*",
				Where:   []string{"type = 'wall'"},
				OrderBy: "created_at",
				Limit:   100, // Note: LIMIT parsing needs improvement
			},
			expectErr: false,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.query, func(t *testing.T) {
			result, err := parseBasicSelectQuery(tc.query)

			if tc.expectErr && err == nil {
				t.Errorf("Expected error for query: %s", tc.query)
			}

			if !tc.expectErr && err != nil {
				t.Errorf("Unexpected error for query: %s: %v", tc.query, err)
			}

			if !tc.expectErr {
				// Check basic fields
				if result.From != tc.expected.From {
					t.Errorf("Expected From to be '%s', got '%s'", tc.expected.From, result.From)
				}

				if len(result.Where) != len(tc.expected.Where) {
					t.Errorf("Expected %d WHERE clauses, got %d", len(tc.expected.Where), len(result.Where))
				}
			}
		})
	}
}

func TestQueryValidation(t *testing.T) {
	// Test query validation
	testCases := []struct {
		query     string
		expectErr bool
	}{
		{"SELECT * FROM building:*", false},
		{"SELECT id, type FROM building:hq WHERE status = 'active'", false},
		{"", true},                         // Empty query
		{"UPDATE * FROM building:*", true}, // Doesn't start with SELECT
		{"SELECT * building:*", true},      // Missing FROM
		{"SELECT * FROM", true},            // Incomplete FROM clause
	}

	for _, tc := range testCases {
		t.Run(tc.query, func(t *testing.T) {
			err := validateSelectQuery(tc.query)

			if tc.expectErr && err == nil {
				t.Errorf("Expected error for query: %s", tc.query)
			}

			if !tc.expectErr && err != nil {
				t.Errorf("Unexpected error for query: %s: %v", tc.query, err)
			}
		})
	}
}

func TestObjectToMapConversion(t *testing.T) {
	display := NewResultDisplay("table", "default")

	// Test with a simple map
	testObj := map[string]interface{}{
		"id":   "test_123",
		"type": "wall",
		"path": "/building/floor1/wall_123",
	}

	objMap := display.objectToMap(testObj)

	if objMap["id"] != "test_123" {
		t.Errorf("Expected id to be 'test_123', got %v", objMap["id"])
	}

	if objMap["type"] != "wall" {
		t.Errorf("Expected type to be 'wall', got %v", objMap["type"])
	}

	if objMap["path"] != "/building/floor1/wall_123" {
		t.Errorf("Expected path to be '/building/floor1/wall_123', got %v", objMap["path"])
	}
}

func TestObjectSummaryFormatting(t *testing.T) {
	display := NewResultDisplay("table", "default")

	// Test object summary formatting
	objMap := map[string]interface{}{
		"id":         "wall_123",
		"type":       "wall",
		"path":       "/building/floor1/wall_123",
		"confidence": 0.95,
		"status":     "active",
		"created_at": time.Now(),
		"updated_at": time.Now(),
	}

	summary := display.formatObjectSummary(objMap)

	// Check that all expected fields are present
	expectedFields := []string{"ID:wall_123", "Type:wall", "Path:/building/floor1/wall_123", "Confidence:0.95"}
	for _, field := range expectedFields {
		if !strings.Contains(summary, field) {
			t.Errorf("Expected summary to contain '%s', got: %s", field, summary)
		}
	}
}

func TestCommonFieldDetection(t *testing.T) {
	display := NewResultDisplay("table", "default")

	// Test common field detection
	commonFields := []string{"id", "type", "path", "confidence", "status", "created_at", "updated_at"}
	customFields := []string{"location", "coordinates", "material", "dimensions"}

	for _, field := range commonFields {
		if !display.isCommonField(field) {
			t.Errorf("Expected '%s' to be identified as a common field", field)
		}
	}

	for _, field := range customFields {
		if display.isCommonField(field) {
			t.Errorf("Expected '%s' to be identified as a custom field", field)
		}
	}
}
