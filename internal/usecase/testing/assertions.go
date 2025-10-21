package testing

import (
	"fmt"
	"math"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
)

// =============================================================================
// Custom Assertions - Domain-Specific Comparisons
// =============================================================================
//
// Custom assertions provide domain-aware equality checks and better error
// messages for test failures. They understand the nuances of domain objects
// and provide detailed failure reports.

// =============================================================================
// Building Assertions
// =============================================================================

// AssertBuildingEqual checks if two buildings are semantically equal
func AssertBuildingEqual(t *testing.T, expected, actual *domain.Building) bool {
	t.Helper()

	if expected == nil && actual == nil {
		return true
	}

	if expected == nil || actual == nil {
		t.Errorf("Building nil mismatch:\n  Expected: %v\n  Actual: %v", expected, actual)
		return false
	}

	failures := []string{}

	if expected.ID != actual.ID {
		failures = append(failures, fmt.Sprintf("  ID: expected %s, got %s", expected.ID, actual.ID))
	}

	if expected.Name != actual.Name {
		failures = append(failures, fmt.Sprintf("  Name: expected %q, got %q", expected.Name, actual.Name))
	}

	if expected.Address != actual.Address {
		failures = append(failures, fmt.Sprintf("  Address: expected %q, got %q", expected.Address, actual.Address))
	}

	if !locationsEqual(expected.Coordinates, actual.Coordinates, 0.000001) {
		failures = append(failures, fmt.Sprintf("  Coordinates: expected %v, got %v", expected.Coordinates, actual.Coordinates))
	}

	if len(expected.Floors) != len(actual.Floors) {
		failures = append(failures, fmt.Sprintf("  Floor count: expected %d, got %d", len(expected.Floors), len(actual.Floors)))
	}

	if len(failures) > 0 {
		t.Errorf("Buildings differ:\n%s", joinFailures(failures))
		return false
	}

	return true
}

// AssertBuildingExists checks that a building is not nil and has a valid ID
func AssertBuildingExists(t *testing.T, building *domain.Building) bool {
	t.Helper()

	if building == nil {
		t.Error("Building is nil")
		return false
	}

	if !building.ID.IsValid() {
		t.Error("Building has invalid ID")
		return false
	}

	return true
}

// =============================================================================
// Location/Spatial Assertions
// =============================================================================

// AssertLocationNear checks if two locations are within a tolerance
func AssertLocationNear(t *testing.T, expected, actual *domain.Location, tolerance float64) bool {
	t.Helper()

	if expected == nil && actual == nil {
		return true
	}

	if expected == nil || actual == nil {
		t.Errorf("Location nil mismatch:\n  Expected: %v\n  Actual: %v", expected, actual)
		return false
	}

	if !locationsEqual(expected, actual, tolerance) {
		distance := locationDistance(expected, actual)
		t.Errorf("Locations differ:\n"+
			"  Expected: (%.6f, %.6f, %.6f)\n"+
			"  Actual: (%.6f, %.6f, %.6f)\n"+
			"  Distance: %.9f (tolerance: %.9f)",
			expected.X, expected.Y, expected.Z,
			actual.X, actual.Y, actual.Z,
			distance, tolerance)
		return false
	}

	return true
}

// AssertLocationEqual checks if two locations are exactly equal
func AssertLocationEqual(t *testing.T, expected, actual *domain.Location) bool {
	t.Helper()
	return AssertLocationNear(t, expected, actual, 0.0)
}

// =============================================================================
// User Assertions
// =============================================================================

// AssertUserEqual checks if two users are semantically equal
func AssertUserEqual(t *testing.T, expected, actual *domain.User) bool {
	t.Helper()

	if expected == nil && actual == nil {
		return true
	}

	if expected == nil || actual == nil {
		t.Errorf("User nil mismatch:\n  Expected: %v\n  Actual: %v", expected, actual)
		return false
	}

	failures := []string{}

	if expected.ID != actual.ID {
		failures = append(failures, fmt.Sprintf("  ID: expected %s, got %s", expected.ID, actual.ID))
	}

	if expected.Email != actual.Email {
		failures = append(failures, fmt.Sprintf("  Email: expected %q, got %q", expected.Email, actual.Email))
	}

	if expected.Name != actual.Name {
		failures = append(failures, fmt.Sprintf("  Name: expected %q, got %q", expected.Name, actual.Name))
	}

	if expected.Role != actual.Role {
		failures = append(failures, fmt.Sprintf("  Role: expected %q, got %q", expected.Role, actual.Role))
	}

	if expected.Active != actual.Active {
		failures = append(failures, fmt.Sprintf("  Active: expected %v, got %v", expected.Active, actual.Active))
	}

	if len(failures) > 0 {
		t.Errorf("Users differ:\n%s", joinFailures(failures))
		return false
	}

	return true
}

// =============================================================================
// Organization Assertions
// =============================================================================

// AssertOrganizationEqual checks if two organizations are semantically equal
func AssertOrganizationEqual(t *testing.T, expected, actual *domain.Organization) bool {
	t.Helper()

	if expected == nil && actual == nil {
		return true
	}

	if expected == nil || actual == nil {
		t.Errorf("Organization nil mismatch:\n  Expected: %v\n  Actual: %v", expected, actual)
		return false
	}

	failures := []string{}

	if expected.ID != actual.ID {
		failures = append(failures, fmt.Sprintf("  ID: expected %s, got %s", expected.ID, actual.ID))
	}

	if expected.Name != actual.Name {
		failures = append(failures, fmt.Sprintf("  Name: expected %q, got %q", expected.Name, actual.Name))
	}

	if expected.Plan != actual.Plan {
		failures = append(failures, fmt.Sprintf("  Plan: expected %q, got %q", expected.Plan, actual.Plan))
	}

	if expected.Active != actual.Active {
		failures = append(failures, fmt.Sprintf("  Active: expected %v, got %v", expected.Active, actual.Active))
	}

	if len(failures) > 0 {
		t.Errorf("Organizations differ:\n%s", joinFailures(failures))
		return false
	}

	return true
}

// =============================================================================
// Equipment Assertions
// =============================================================================

// AssertEquipmentEqual checks if two pieces of equipment are semantically equal
func AssertEquipmentEqual(t *testing.T, expected, actual *domain.Equipment) bool {
	t.Helper()

	if expected == nil && actual == nil {
		return true
	}

	if expected == nil || actual == nil {
		t.Errorf("Equipment nil mismatch:\n  Expected: %v\n  Actual: %v", expected, actual)
		return false
	}

	failures := []string{}

	if expected.ID != actual.ID {
		failures = append(failures, fmt.Sprintf("  ID: expected %s, got %s", expected.ID, actual.ID))
	}

	if expected.Name != actual.Name {
		failures = append(failures, fmt.Sprintf("  Name: expected %q, got %q", expected.Name, actual.Name))
	}

	if expected.Type != actual.Type {
		failures = append(failures, fmt.Sprintf("  Type: expected %q, got %q", expected.Type, actual.Type))
	}

	if expected.Status != actual.Status {
		failures = append(failures, fmt.Sprintf("  Status: expected %q, got %q", expected.Status, actual.Status))
	}

	if !locationsEqual(expected.Location, actual.Location, 0.000001) {
		failures = append(failures, fmt.Sprintf("  Location: expected %v, got %v", expected.Location, actual.Location))
	}

	if len(failures) > 0 {
		t.Errorf("Equipment differ:\n%s", joinFailures(failures))
		return false
	}

	return true
}

// =============================================================================
// Collection Assertions
// =============================================================================

// AssertFloorCount checks if a building has the expected number of floors
func AssertFloorCount(t *testing.T, building *domain.Building, expected int) bool {
	t.Helper()

	if building == nil {
		t.Error("Building is nil")
		return false
	}

	actual := len(building.Floors)
	if actual != expected {
		t.Errorf("Floor count mismatch:\n  Expected: %d\n  Actual: %d", expected, actual)
		return false
	}

	return true
}

// AssertRoomCount checks if a floor has the expected number of rooms
func AssertRoomCount(t *testing.T, floor *domain.Floor, expected int) bool {
	t.Helper()

	if floor == nil {
		t.Error("Floor is nil")
		return false
	}

	actual := len(floor.Rooms)
	if actual != expected {
		t.Errorf("Room count mismatch:\n  Expected: %d\n  Actual: %d", expected, actual)
		return false
	}

	return true
}

// AssertEquipmentCount checks if an entity has the expected number of equipment
func AssertEquipmentCount(t *testing.T, equipment []*domain.Equipment, expected int) bool {
	t.Helper()

	actual := len(equipment)
	if actual != expected {
		t.Errorf("Equipment count mismatch:\n  Expected: %d\n  Actual: %d", expected, actual)
		return false
	}

	return true
}

// =============================================================================
// ID Assertions
// =============================================================================

// AssertIDsEqual checks if two IDs are equal
func AssertIDsEqual(t *testing.T, expected, actual types.ID) bool {
	t.Helper()
	return assert.Equal(t, expected, actual, "IDs should be equal")
}

// AssertIDsDiffer checks if two IDs are different
func AssertIDsDiffer(t *testing.T, id1, id2 types.ID) bool {
	t.Helper()
	if id1 == id2 {
		t.Errorf("IDs should differ but are both: %s", id1)
		return false
	}
	return true
}

// =============================================================================
// Helper Functions
// =============================================================================

func locationsEqual(loc1, loc2 *domain.Location, tolerance float64) bool {
	if loc1 == nil && loc2 == nil {
		return true
	}
	if loc1 == nil || loc2 == nil {
		return false
	}

	return math.Abs(loc1.X-loc2.X) <= tolerance &&
		math.Abs(loc1.Y-loc2.Y) <= tolerance &&
		math.Abs(loc1.Z-loc2.Z) <= tolerance
}

func locationDistance(loc1, loc2 *domain.Location) float64 {
	if loc1 == nil || loc2 == nil {
		return math.Inf(1)
	}

	dx := loc1.X - loc2.X
	dy := loc1.Y - loc2.Y
	dz := loc1.Z - loc2.Z

	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

func joinFailures(failures []string) string {
	result := ""
	for _, failure := range failures {
		result += failure + "\n"
	}
	return result
}
