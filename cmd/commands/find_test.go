package commands

import (
	"fmt"
	"strings"
	"testing"
)

func TestParseSimpleQuery(t *testing.T) {
	tests := []struct {
		name      string
		query     string
		wantType  string
		wantValue string
	}{
		{
			name:      "wildcard query",
			query:     "*",
			wantType:  "",
			wantValue: "",
		},
		{
			name:      "empty query",
			query:     "",
			wantType:  "",
			wantValue: "",
		},
		{
			name:      "type filter",
			query:     "type:floor",
			wantType:  "type",
			wantValue: "floor",
		},
		{
			name:      "status filter",
			query:     "status:active",
			wantType:  "status",
			wantValue: "active",
		},
		{
			name:      "path filter",
			query:     "path:/systems/*",
			wantType:  "path",
			wantValue: "/systems/*",
		},
		{
			name:      "text search",
			query:     "electrical",
			wantType:  "text",
			wantValue: "electrical",
		},
		{
			name:      "text with spaces",
			query:     "hvac system",
			wantType:  "text",
			wantValue: "hvac system",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotType, gotValue := parseSimpleQuery(tt.query)
			if gotType != tt.wantType {
				t.Errorf("parseSimpleQuery() gotType = %v, want %v", gotType, tt.wantType)
			}
			if gotValue != tt.wantValue {
				t.Errorf("parseSimpleQuery() gotValue = %v, want %v", gotValue, tt.wantValue)
			}
		})
	}
}

func TestMatchesSimpleQuery(t *testing.T) {
	entry := DirectoryEntry{
		Name:     "Electrical Panel A",
		Type:     "electrical_panel",
		Path:     "/systems/electrical/panel-a",
		IsDir:    false,
		Metadata: map[string]interface{}{"status": "active", "voltage": "480V"},
	}

	tests := []struct {
		name      string
		queryType string
		queryValue string
		want      bool
	}{
		{
			name:      "empty query matches all",
			queryType: "",
			queryValue: "",
			want:      true,
		},
		{
			name:      "text search in name",
			queryType: "text",
			queryValue: "electrical",
			want:      true,
		},
		{
			name:      "text search in type",
			queryType: "text",
			queryValue: "panel",
			want:      true,
		},
		{
			name:      "text search no match",
			queryType: "text",
			queryValue: "plumbing",
			want:      false,
		},
		{
			name:      "type filter exact match",
			queryType: "type",
			queryValue: "electrical_panel",
			want:      true,
		},
		{
			name:      "type filter case insensitive",
			queryType: "type",
			queryValue: "ELECTRICAL_PANEL",
			want:      true,
		},
		{
			name:      "type filter no match",
			queryType: "type",
			queryValue: "floor",
			want:      false,
		},
		{
			name:      "status filter match",
			queryType: "status",
			queryValue: "active",
			want:      true,
		},
		{
			name:      "status filter no match",
			queryType: "status",
			queryValue: "inactive",
			want:      false,
		},
		{
			name:      "path filter match",
			queryType: "path",
			queryValue: "electrical",
			want:      true,
		},
		{
			name:      "path filter no match",
			queryType: "path",
			queryValue: "plumbing",
			want:      false,
		},
		{
			name:      "metadata filter match",
			queryType: "voltage",
			queryValue: "480V",
			want:      true,
		},
		{
			name:      "metadata filter no match",
			queryType: "voltage",
			queryValue: "240V",
			want:      false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := matchesSimpleQuery(entry, tt.queryType, tt.queryValue)
			if got != tt.want {
				t.Errorf("matchesSimpleQuery() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestExecuteSimpleSearch(t *testing.T) {
	// Create a test index
	index := &Index{
		PathToEntries: map[string][]DirectoryEntry{
			"/": {
				{Name: "Floor 1", Type: "floor", Path: "/floor-1", IsDir: true},
				{Name: "Floor 2", Type: "floor", Path: "/floor-2", IsDir: true},
				{Name: "Systems", Type: "directory", Path: "/systems", IsDir: true},
			},
			"/systems": {
				{Name: "Electrical", Type: "system", Path: "/systems/electrical", IsDir: true},
				{Name: "HVAC", Type: "system", Path: "/systems/hvac", IsDir: true},
			},
			"/systems/electrical": {
				{Name: "Panel A", Type: "electrical_panel", Path: "/systems/electrical/panel-a", IsDir: false},
				{Name: "Panel B", Type: "electrical_panel", Path: "/systems/electrical/panel-b", IsDir: false},
			},
		},
	}

	tests := []struct {
		name    string
		query   string
		limit   int
		wantLen int
	}{
		{
			name:    "find all floors",
			query:   "type:floor",
			limit:   10,
			wantLen: 2,
		},
		{
			name:    "find electrical panels",
			query:   "type:electrical_panel",
			limit:   10,
			wantLen: 2,
		},
		{
			name:    "find systems",
			query:   "type:system",
			limit:   10,
			wantLen: 2,
		},
		{
			name:    "text search electrical",
			query:   "electrical",
			limit:   10,
			wantLen: 3, // electrical system + 2 panels
		},
		{
			name:    "limit results",
			query:   "*",
			limit:   2,
			wantLen: 2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			options := &FindOptions{
				Query:  tt.query,
				Limit:  tt.limit,
				Format: "table",
			}

			results, err := executeSimpleSearch(index, options)
			if err != nil {
				t.Errorf("executeSimpleSearch() error = %v", err)
				return
			}

			if len(results) != tt.wantLen {
				t.Errorf("executeSimpleSearch() got %d results, want %d", len(results), tt.wantLen)
			}

			// Check that limit is respected
			if len(results) > tt.limit {
				t.Errorf("executeSimpleSearch() got %d results, limit was %d", len(results), tt.limit)
			}
		})
	}
}

func TestFormatMetadata(t *testing.T) {
	tests := []struct {
		name     string
		metadata map[string]interface{}
		want     string
	}{
		{
			name:     "empty metadata",
			metadata: map[string]interface{}{},
			want:     "",
		},
		{
			name: "single property",
			metadata: map[string]interface{}{
				"status": "active",
			},
			want: "status=active",
		},
		{
			name: "multiple properties",
			metadata: map[string]interface{}{
				"status":  "active",
				"voltage": "480V",
				"phase":   3,
			},
			want: "phase=3;status=active;voltage=480V", // Note: map iteration order is not guaranteed
		},
		{
			name: "mixed types",
			metadata: map[string]interface{}{
				"status":   true,
				"count":    42,
				"name":     "test",
				"distance": 3.14,
			},
			want: "count=42;distance=3.14;name=test;status=true", // Note: map iteration order is not guaranteed
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := formatMetadata(tt.metadata)
			if got != tt.want && len(tt.metadata) > 1 {
				// For multiple properties, check that all are present
				for k, v := range tt.metadata {
					expected := fmt.Sprintf("%s=%v", k, v)
					if !strings.Contains(got, expected) {
						t.Errorf("formatMetadata() missing %s", expected)
					}
				}
			} else if got != tt.want {
				t.Errorf("formatMetadata() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestDisplaySimpleResults(t *testing.T) {
	results := []DirectoryEntry{
		{Name: "Test Entry", Type: "test", Path: "/test", IsDir: false, Metadata: map[string]interface{}{"status": "active"}},
	}

	tests := []struct {
		name   string
		format string
		want   error
	}{
		{
			name:   "table format",
			format: "table",
			want:   nil,
		},
		{
			name:   "json format",
			format: "json",
			want:   nil,
		},
		{
			name:   "csv format",
			format: "csv",
			want:   nil,
		},
		{
			name:   "default format",
			format: "",
			want:   nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			options := &FindOptions{Format: tt.format}
			got := displaySimpleResults(results, options)
			if got != tt.want {
				t.Errorf("displaySimpleResults() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestFindOptions(t *testing.T) {
	options := &FindOptions{
		Limit:  100,
		Format: "json",
		Query:  "test",
	}

	if options.Limit != 100 {
		t.Errorf("FindOptions.Limit = %v, want 100", options.Limit)
	}

	if options.Format != "json" {
		t.Errorf("FindOptions.Format = %v, want json", options.Format)
	}

	if options.Query != "test" {
		t.Errorf("FindOptions.Query = %v, want test", options.Query)
	}
}
