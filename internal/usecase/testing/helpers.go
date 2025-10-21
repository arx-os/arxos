package testing

import (
	"context"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
)

// =============================================================================
// Test Helpers - Common Test Patterns and Utilities
// =============================================================================

// =============================================================================
// Context Helpers
// =============================================================================

// WithTestContext creates a context with a reasonable timeout for tests
func WithTestContext() (context.Context, context.CancelFunc) {
	return context.WithTimeout(context.Background(), 5*time.Second)
}

// WithAuthContext creates a context with user authentication information
func WithAuthContext(userID string) context.Context {
	ctx := context.Background()
	// In a real implementation, this would add auth metadata to context
	// For now, we just return a basic context
	return context.WithValue(ctx, "user_id", userID)
}

// WithOrgContext creates a context with organization information
func WithOrgContext(orgID string) context.Context {
	ctx := context.Background()
	return context.WithValue(ctx, "org_id", orgID)
}

// =============================================================================
// Common Scenario Setup Helpers
// =============================================================================

// SetupBuildingWithFloors creates a building with N floors
func SetupBuildingWithFloors(numFloors int) *domain.Building {
	builder := NewBuildingBuilder()

	for i := 0; i < numFloors; i++ {
		floor := NewFloorBuilder().
			WithLevel(i).
			WithName(formatFloorName(i)).
			Build()
		builder.WithFloor(floor)
	}

	return builder.Build()
}

// SetupBuildingWithFloorsAndRooms creates a building with N floors, each with M rooms
func SetupBuildingWithFloorsAndRooms(numFloors, roomsPerFloor int) *domain.Building {
	builder := NewBuildingBuilder()

	for i := 0; i < numFloors; i++ {
		floorBuilder := NewFloorBuilder().
			WithLevel(i).
			WithName(formatFloorName(i))

		for j := 0; j < roomsPerFloor; j++ {
			room := NewRoomBuilder().
				WithNumber(formatRoomNumber(i, j)).
				WithName(formatRoomName(i, j)).
				Build()
			floorBuilder.WithRoom(room)
		}

		builder.WithFloor(floorBuilder.Build())
	}

	return builder.Build()
}

// SetupUserWithOrg creates a user associated with an organization
func SetupUserWithOrg() (*domain.User, *domain.Organization) {
	org := NewOrganizationBuilder().Build()
	user := NewUserBuilder().Build()
	return user, org
}

// SetupAdminUser creates an admin user
func SetupAdminUser() *domain.User {
	return NewUserBuilder().
		AsAdmin().
		WithEmail("admin@example.com").
		WithName("Admin User").
		Build()
}

// SetupEquipmentInRoom creates N pieces of equipment in a room
func SetupEquipmentInRoom(roomID types.ID, numEquipment int) []*domain.Equipment {
	equipment := make([]*domain.Equipment, numEquipment)

	for i := 0; i < numEquipment; i++ {
		equipment[i] = NewEquipmentBuilder().
			WithName(formatEquipmentName(i)).
			Build()
	}

	return equipment
}

// =============================================================================
// Validation Helpers
// =============================================================================

// AssertValidID checks that an ID is valid (non-zero UUID)
func AssertValidID(t *testing.T, id types.ID) {
	t.Helper()
	if !id.IsValid() {
		t.Errorf("Expected valid ID, got invalid ID")
	}
}

// AssertValidTimestamp checks that a timestamp is recent (within last minute)
func AssertValidTimestamp(t *testing.T, ts time.Time) {
	t.Helper()
	now := time.Now()
	if ts.After(now) {
		t.Errorf("Timestamp %v is in the future", ts)
	}
	if ts.Before(now.Add(-time.Minute)) {
		t.Errorf("Timestamp %v is more than 1 minute old", ts)
	}
}

// AssertRecentTimestamp checks that a timestamp is within a specific duration
func AssertRecentTimestamp(t *testing.T, ts time.Time, within time.Duration) {
	t.Helper()
	now := time.Now()
	if ts.After(now) {
		t.Errorf("Timestamp %v is in the future", ts)
	}
	if ts.Before(now.Add(-within)) {
		t.Errorf("Timestamp %v is older than %v", ts, within)
	}
}

// AssertNonEmpty checks that a string is not empty
func AssertNonEmpty(t *testing.T, value, fieldName string) {
	t.Helper()
	if value == "" {
		t.Errorf("Expected non-empty %s", fieldName)
	}
}

// =============================================================================
// Formatting Helpers (Internal)
// =============================================================================

func formatFloorName(level int) string {
	if level == 0 {
		return "Ground Floor"
	}
	return formatOrdinal(level) + " Floor"
}

func formatRoomNumber(floor, room int) string {
	return formatFloorPrefix(floor) + formatRoomSuffix(room)
}

func formatRoomName(floor, room int) string {
	return "Room " + formatRoomNumber(floor, room)
}

func formatEquipmentName(index int) string {
	return "Equipment " + formatNumeral(index+1)
}

func formatFloorPrefix(floor int) string {
	if floor == 0 {
		return "G"
	}
	return formatNumeral(floor)
}

func formatRoomSuffix(room int) string {
	num := room + 1
	if num < 10 {
		return "0" + formatNumeral(num)
	}
	return formatNumeral(num)
}

func formatNumeral(n int) string {
	// Simple integer to string conversion
	if n < 10 {
		return string(rune('0' + n))
	}
	// For larger numbers, use standard formatting
	result := ""
	for n > 0 {
		result = string(rune('0'+(n%10))) + result
		n /= 10
	}
	return result
}

func formatOrdinal(n int) string {
	suffix := "th"
	if n%100 < 11 || n%100 > 13 {
		switch n % 10 {
		case 1:
			suffix = "st"
		case 2:
			suffix = "nd"
		case 3:
			suffix = "rd"
		}
	}
	return formatNumeral(n) + suffix
}

// =============================================================================
// Mock Setup Helpers
// =============================================================================

// SetupMockSuccess configures a mock to return success for any call
func SetupMockSuccess(repo interface{}) {
	// This is a placeholder for common mock setup patterns
	// Specific implementations would be in individual test files
}

// SetupMockError configures a mock to return an error for any call
func SetupMockError(repo interface{}, err error) {
	// This is a placeholder for common mock setup patterns
	// Specific implementations would be in individual test files
}
