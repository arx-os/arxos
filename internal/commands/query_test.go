package commands

import (
	"testing"
	"time"

	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
)

func TestQueryBuilder_Build(t *testing.T) {
	tests := []struct {
		name     string
		opts     QueryOptions
		wantSQL  string
		wantArgs int
	}{
		{
			name: "basic query with no filters",
			opts: QueryOptions{},
			wantSQL: `SELECT DISTINCT 
			e.id, e.equipment_tag, e.name, e.equipment_type, e.status, 
			e.manufacturer, e.model, e.serial_number, e.installation_date,
			e.location_x, e.location_y, e.location_z,
			f.level as floor_level, f.name as floor_name,
			r.room_number, r.name as room_name,
			b.name as building_name, b.arxos_id as building_id
		FROM equipment e
		LEFT JOIN buildings b ON e.building_id = b.id
		LEFT JOIN floors f ON e.floor_id = f.id  
		LEFT JOIN rooms r ON e.room_id = r.id ORDER BY b.name, f.level, r.room_number, e.name`,
			wantArgs: 0,
		},
		{
			name: "query with building filter",
			opts: QueryOptions{
				Building: "ARXOS-001",
			},
			wantArgs: 2, // building ID and building name LIKE
		},
		{
			name: "query with multiple filters",
			opts: QueryOptions{
				Building: "ARXOS-001",
				Floor:    3,
				Type:     "outlet",
				Status:   "operational",
			},
			wantArgs: 5, // building (2) + floor (1) + type (1) + status (1)
		},
		{
			name: "query with pagination",
			opts: QueryOptions{
				Limit:  50,
				Offset: 10,
			},
			wantArgs: 2, // limit + offset
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			qb := NewQueryBuilder(tt.opts)
			query, args := qb.Build()
			
			assert.NotEmpty(t, query)
			assert.Len(t, args, tt.wantArgs)
			
			// Verify query contains expected components
			assert.Contains(t, query, "SELECT DISTINCT")
			assert.Contains(t, query, "FROM equipment e")
			assert.Contains(t, query, "ORDER BY")
		})
	}
}

func TestQueryBuilder_addFilters(t *testing.T) {
	tests := []struct {
		name      string
		opts      QueryOptions
		wantWheres int
		wantArgs   int
	}{
		{
			name:      "no filters",
			opts:      QueryOptions{},
			wantWheres: 0,
			wantArgs:   0,
		},
		{
			name: "building filter",
			opts: QueryOptions{Building: "ARXOS-001"},
			wantWheres: 1,
			wantArgs:   2,
		},
		{
			name: "multiple filters",
			opts: QueryOptions{
				Building: "ARXOS-001",
				Floor:    3,
				Type:     "outlet",
				Status:   "operational",
				Room:     "101",
			},
			wantWheres: 5,
			wantArgs:   7, // building(2) + floor(1) + type(1) + status(1) + room(2)
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			qb := NewQueryBuilder(tt.opts)
			qb.addFilters()
			
			assert.Len(t, qb.wheres, tt.wantWheres)
			assert.Len(t, qb.args, tt.wantArgs)
		})
	}
}

func TestGetStringFromMetadata(t *testing.T) {
	tests := []struct {
		name         string
		metadata     map[string]interface{}
		key          string
		defaultValue string
		want         string
	}{
		{
			name:         "nil metadata",
			metadata:     nil,
			key:          "test",
			defaultValue: "default",
			want:         "default",
		},
		{
			name:         "key not found",
			metadata:     map[string]interface{}{"other": "value"},
			key:          "test",
			defaultValue: "default",
			want:         "default",
		},
		{
			name:         "string value",
			metadata:     map[string]interface{}{"test": "value"},
			key:          "test",
			defaultValue: "default",
			want:         "value",
		},
		{
			name:         "int value",
			metadata:     map[string]interface{}{"floor": 3},
			key:          "floor",
			defaultValue: "default",
			want:         "3",
		},
		{
			name:         "float value",
			metadata:     map[string]interface{}{"temp": 23.5},
			key:          "temp",
			defaultValue: "default",
			want:         "24", // rounded
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := getStringFromMetadata(tt.metadata, tt.key, tt.defaultValue)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestCsvEscape(t *testing.T) {
	tests := []struct {
		name  string
		field string
		want  string
	}{
		{
			name:  "empty string",
			field: "",
			want:  "",
		},
		{
			name:  "simple string",
			field: "test",
			want:  "test",
		},
		{
			name:  "string with comma",
			field: "test,value",
			want:  "\"test,value\"",
		},
		{
			name:  "string with quote",
			field: "test\"value",
			want:  "\"test\"\"value\"",
		},
		{
			name:  "string with newline",
			field: "test\nvalue",
			want:  "\"test\nvalue\"",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := csvEscape(tt.field)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestQueryResult(t *testing.T) {
	// Test QueryResult structure
	equipment := []*models.Equipment{
		{
			ID:     "EQ001",
			Name:   "Test Equipment",
			Type:   "outlet",
			Status: "operational",
			Location: &models.Point{X: 10.5, Y: 20.3},
			Metadata: map[string]interface{}{
				"building_name": "Test Building",
				"floor_level":   3,
			},
		},
	}

	result := &QueryResult{
		Equipment:  equipment,
		Count:      len(equipment),
		Total:      len(equipment),
		Offset:     0,
		Limit:      50,
		QueryTime:  time.Millisecond * 10,
		ExecutedAt: time.Now(),
	}

	assert.Equal(t, 1, result.Count)
	assert.Equal(t, 1, result.Total)
	assert.Equal(t, 0, result.Offset)
	assert.Equal(t, 50, result.Limit)
	assert.NotZero(t, result.QueryTime)
	assert.NotZero(t, result.ExecutedAt)
	assert.Len(t, result.Equipment, 1)
	
	// Test equipment data
	eq := result.Equipment[0]
	assert.Equal(t, "EQ001", eq.ID)
	assert.Equal(t, "Test Equipment", eq.Name)
	assert.Equal(t, "outlet", eq.Type)
	assert.Equal(t, "operational", eq.Status)
	assert.NotNil(t, eq.Location)
	assert.Equal(t, 10.5, eq.Location.X)
	assert.Equal(t, 20.3, eq.Location.Y)
	assert.NotNil(t, eq.Metadata)
	assert.Equal(t, "Test Building", eq.Metadata["building_name"])
	assert.Equal(t, 3, eq.Metadata["floor_level"])
}
