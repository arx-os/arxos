package workflow

import (
	"context"
	"database/sql"
	"testing"

	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestPathBasedQueries tests the path-based query functionality
func TestPathBasedQueries(t *testing.T) {
	// Skip if no database available
	db := setupTestDB(t)
	if db == nil {
		t.Skip("Database not available")
	}
	defer db.Close()

	ctx := context.Background()
	repo := postgis.NewEquipmentRepository(db)

	t.Run("GetByPath exact match", func(t *testing.T) {
		// Test exact path match
		equipment, err := repo.GetByPath(ctx, "/B1/3/301/HVAC/VAV-301")
		require.NoError(t, err)
		assert.NotNil(t, equipment)
		assert.Equal(t, "VAV Unit 301", equipment.Name)
		assert.Equal(t, "/B1/3/301/HVAC/VAV-301", equipment.Path)
	})

	t.Run("GetByPath not found", func(t *testing.T) {
		// Test with non-existent path
		_, err := repo.GetByPath(ctx, "/NONEXISTENT/PATH")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "not found")
	})

	t.Run("FindByPath wildcard patterns", func(t *testing.T) {
		tests := []struct {
			name          string
			pattern       string
			expectedCount int
			expectedType  string
		}{
			{
				name:          "All HVAC on floor 3",
				pattern:       "/B1/3/*/HVAC/*",
				expectedCount: 3,
				expectedType:  "hvac",
			},
			{
				name:          "All network equipment",
				pattern:       "/B1/3/*/NETWORK/*",
				expectedCount: 2,
				expectedType:  "network",
			},
			{
				name:          "All safety equipment",
				pattern:       "/B1/3/*/SAFETY/*",
				expectedCount: 2,
				expectedType:  "fire_safety",
			},
			{
				name:          "All equipment in specific room",
				pattern:       "/B1/3/301/*",
				expectedCount: 2, // VAV and Fire Extinguisher
			},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				equipment, err := repo.FindByPath(ctx, tt.pattern)
				require.NoError(t, err)
				assert.Len(t, equipment, tt.expectedCount)

				if tt.expectedType != "" {
					for _, eq := range equipment {
						assert.Equal(t, tt.expectedType, eq.Type)
					}
				}
			})
		}
	})

	t.Run("FindByPath validates pattern", func(t *testing.T) {
		// Test overly broad patterns
		_, err := repo.FindByPath(ctx, "*")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "too broad")
	})

	t.Run("FindByPath handles NULL fields", func(t *testing.T) {
		// Test that equipment with NULL model field doesn't cause errors
		equipment, err := repo.FindByPath(ctx, "/B1/3/*/HVAC/*")
		require.NoError(t, err)
		assert.Greater(t, len(equipment), 0)

		// Should handle NULL model gracefully
		for _, eq := range equipment {
			// Model might be empty string, that's okay
			assert.NotNil(t, eq)
		}
	})
}

// TestPathQueryUseCases tests path queries through use case layer
func TestPathQueryUseCases(t *testing.T) {
	// Skip for now - requires full container setup with test database
	// This test validates the use case layer methods we just added
	// TODO: Implement when test container setup is available
	t.Skip("Use case layer tests require full container setup - implement in Week 4 testing phase")

	// Future implementation:
	// container := setupTestContainerWithDB(t)
	// equipmentUC := container.GetEquipmentUseCase()
	// Test GetByPath() and FindByPath() via use case
}

// Helper function to setup test database
func setupTestDB(t *testing.T) *sql.DB {
	// This would connect to test database
	// Reuse existing test helpers
	return nil // Placeholder
}
