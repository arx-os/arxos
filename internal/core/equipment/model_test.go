package equipment

import (
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestNewEquipment(t *testing.T) {
	buildingID := uuid.New()
	path := "1/101/OUTLET-001"
	name := "Main Outlet"
	eqType := "electrical.outlet"

	eq := NewEquipment(buildingID, path, name, eqType)

	assert.NotNil(t, eq)
	assert.NotEqual(t, uuid.Nil, eq.ID)
	assert.Equal(t, buildingID, eq.BuildingID)
	assert.Equal(t, path, eq.Path)
	assert.Equal(t, name, eq.Name)
	assert.Equal(t, eqType, eq.Type)
	assert.Equal(t, StatusUnknown, eq.Status)
	assert.Equal(t, ConfidenceUnknown, eq.Confidence)
	assert.NotZero(t, eq.CreatedAt)
	assert.NotZero(t, eq.UpdatedAt)
}

func TestEquipment_SetPosition(t *testing.T) {
	eq := NewEquipment(uuid.New(), "test/path", "Test", "sensor")

	pos := &Position{
		X: -122.4194,
		Y: 37.7749,
		Z: 10.5,
	}

	eq.SetPosition(pos, ConfidenceSurveyed)

	assert.NotNil(t, eq.Position)
	assert.Equal(t, pos.X, eq.Position.X)
	assert.Equal(t, pos.Y, eq.Position.Y)
	assert.Equal(t, pos.Z, eq.Position.Z)
	assert.Equal(t, ConfidenceSurveyed, eq.Confidence)
}

func TestEquipment_HasPosition(t *testing.T) {
	eq := NewEquipment(uuid.New(), "test/path", "Test", "sensor")

	// Initially no position
	assert.False(t, eq.HasPosition())

	// Set position
	eq.SetPosition(&Position{X: 1, Y: 2, Z: 3}, ConfidenceEstimated)
	assert.True(t, eq.HasPosition())
}

func TestEquipment_Validate(t *testing.T) {
	tests := []struct {
		name    string
		setup   func() *Equipment
		wantErr bool
		errMsg  string
	}{
		{
			name: "valid equipment",
			setup: func() *Equipment {
				return NewEquipment(uuid.New(), "1/101/EQ-001", "Test Equipment", "sensor")
			},
			wantErr: false,
		},
		{
			name: "missing building ID",
			setup: func() *Equipment {
				eq := NewEquipment(uuid.Nil, "path", "name", "type")
				eq.BuildingID = uuid.Nil
				return eq
			},
			wantErr: true,
			errMsg:  "building ID is required",
		},
		{
			name: "missing path",
			setup: func() *Equipment {
				eq := NewEquipment(uuid.New(), "", "name", "type")
				eq.Path = ""
				return eq
			},
			wantErr: true,
			errMsg:  "path is required",
		},
		{
			name: "missing name",
			setup: func() *Equipment {
				eq := NewEquipment(uuid.New(), "path", "", "type")
				eq.Name = ""
				return eq
			},
			wantErr: true,
			errMsg:  "name is required",
		},
		{
			name: "missing type",
			setup: func() *Equipment {
				eq := NewEquipment(uuid.New(), "path", "name", "")
				eq.Type = ""
				return eq
			},
			wantErr: true,
			errMsg:  "type is required",
		},
		{
			name: "invalid status",
			setup: func() *Equipment {
				eq := NewEquipment(uuid.New(), "path", "name", "type")
				eq.Status = "invalid_status"
				return eq
			},
			wantErr: true,
			errMsg:  "invalid status",
		},
		{
			name: "invalid confidence",
			setup: func() *Equipment {
				eq := NewEquipment(uuid.New(), "path", "name", "type")
				eq.Confidence = 99
				return eq
			},
			wantErr: true,
			errMsg:  "invalid confidence level",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			eq := tt.setup()
			err := eq.Validate()

			if tt.wantErr {
				assert.Error(t, err)
				if tt.errMsg != "" {
					assert.Contains(t, err.Error(), tt.errMsg)
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestEquipment_IsOperational(t *testing.T) {
	eq := NewEquipment(uuid.New(), "path", "name", "type")

	// Test different statuses
	testCases := []struct {
		status     string
		expected   bool
	}{
		{StatusOperational, true},
		{StatusDegraded, false},
		{StatusFailed, false},
		{StatusOffline, false},
		{StatusMaintenance, false},
		{StatusUnknown, false},
	}

	for _, tc := range testCases {
		eq.Status = tc.status
		assert.Equal(t, tc.expected, eq.IsOperational(), "Status: %s", tc.status)
	}
}

func TestEquipment_NeedsAttention(t *testing.T) {
	eq := NewEquipment(uuid.New(), "path", "name", "type")

	// Test different statuses
	testCases := []struct {
		status     string
		expected   bool
	}{
		{StatusOperational, false},
		{StatusDegraded, true},
		{StatusFailed, true},
		{StatusOffline, false},
		{StatusMaintenance, true},
		{StatusUnknown, false},
	}

	for _, tc := range testCases {
		eq.Status = tc.status
		assert.Equal(t, tc.expected, eq.NeedsAttention(), "Status: %s", tc.status)
	}
}

func TestConfidenceLevel_String(t *testing.T) {
	tests := []struct {
		level    ConfidenceLevel
		expected string
	}{
		{ConfidenceUnknown, "unknown"},
		{ConfidenceEstimated, "estimated"},
		{ConfidenceScanned, "scanned"},
		{ConfidenceSurveyed, "surveyed"},
		{ConfidenceLevel(99), "unknown"},
	}

	for _, tt := range tests {
		assert.Equal(t, tt.expected, tt.level.String())
	}
}

func TestPosition_IsValid(t *testing.T) {
	tests := []struct {
		name     string
		position *Position
		expected bool
	}{
		{
			name:     "valid position",
			position: &Position{X: -122.4194, Y: 37.7749, Z: 10},
			expected: true,
		},
		{
			name:     "invalid latitude",
			position: &Position{X: -122.4194, Y: 91, Z: 10},
			expected: false,
		},
		{
			name:     "invalid longitude",
			position: &Position{X: 181, Y: 37.7749, Z: 10},
			expected: false,
		},
		{
			name:     "nil position",
			position: nil,
			expected: false,
		},
		{
			name:     "zero position",
			position: &Position{X: 0, Y: 0, Z: 0},
			expected: true, // 0,0 is valid (Gulf of Guinea)
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.expected, tt.position.IsValid())
		})
	}
}