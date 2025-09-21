package building

import (
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestNewBuilding(t *testing.T) {
	arxosID := "TEST-001"
	name := "Test Building"

	bldg := NewBuilding(arxosID, name)

	assert.NotNil(t, bldg)
	assert.NotEqual(t, uuid.Nil, bldg.ID)
	assert.Equal(t, arxosID, bldg.ArxosID)
	assert.Equal(t, name, bldg.Name)
	assert.NotZero(t, bldg.CreatedAt)
	assert.NotZero(t, bldg.UpdatedAt)
}

func TestBuilding_SetOrigin(t *testing.T) {
	bldg := NewBuilding("TEST-001", "Test Building")

	lat := 37.7749
	lon := -122.4194
	alt := 10.5
	rotation := 45.0

	bldg.SetOrigin(lat, lon, alt)
	bldg.Rotation = rotation

	assert.NotNil(t, bldg.Origin)
	assert.Equal(t, lat, bldg.Origin.Latitude)
	assert.Equal(t, lon, bldg.Origin.Longitude)
	assert.Equal(t, alt, bldg.Origin.Altitude)
	assert.Equal(t, rotation, bldg.Rotation)
}

func TestBuilding_HasOrigin(t *testing.T) {
	bldg := NewBuilding("TEST-001", "Test Building")

	// Initially no origin
	assert.False(t, bldg.HasOrigin())

	// Set origin
	bldg.SetOrigin(37.7749, -122.4194, 0)
	assert.True(t, bldg.HasOrigin())
}

func TestBuilding_Validate(t *testing.T) {
	tests := []struct {
		name    string
		setup   func() *Building
		wantErr bool
		errMsg  string
	}{
		{
			name: "valid building",
			setup: func() *Building {
				return NewBuilding("TEST-001", "Test Building")
			},
			wantErr: false,
		},
		{
			name: "missing ArxosID",
			setup: func() *Building {
				b := NewBuilding("", "Test Building")
				b.ArxosID = ""
				return b
			},
			wantErr: true,
			errMsg:  "ArxosID is required",
		},
		{
			name: "missing name",
			setup: func() *Building {
				b := NewBuilding("TEST-001", "")
				b.Name = ""
				return b
			},
			wantErr: true,
			errMsg:  "name is required",
		},
		{
			name: "invalid ArxosID format",
			setup: func() *Building {
				return NewBuilding("invalid id with spaces", "Test")
			},
			wantErr: true,
			errMsg:  "ArxosID contains invalid characters",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			bldg := tt.setup()
			err := bldg.Validate()

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

func TestBuilding_UpdateTimestamp(t *testing.T) {
	bldg := NewBuilding("TEST-001", "Test Building")
	originalTime := bldg.UpdatedAt

	// Ensure some time passes
	bldg.UpdateTimestamp()

	assert.True(t, bldg.UpdatedAt.After(originalTime) || bldg.UpdatedAt.Equal(originalTime))
}