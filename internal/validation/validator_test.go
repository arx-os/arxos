package validation

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestValidator_Required(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid non-empty string",
			field:    "name",
			value:    "Test Building",
			expected: true,
		},
		{
			name:     "Empty string",
			field:    "name",
			value:    "",
			expected: false,
		},
		{
			name:     "Whitespace only",
			field:    "name",
			value:    "   ",
			expected: false,
		},
		{
			name:     "Tab and newline only",
			field:    "name",
			value:    "\t\n",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.Required(tt.field, tt.value)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
			if !tt.expected {
				assert.Len(t, result.Errors, 1)
				assert.Equal(t, "REQUIRED", result.Errors[0].Code)
			}
		})
	}
}

func TestValidator_MinLength(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		min      int
		expected bool
	}{
		{
			name:     "Valid length",
			field:    "name",
			value:    "Test",
			min:      3,
			expected: true,
		},
		{
			name:     "Exact minimum length",
			field:    "name",
			value:    "Tes",
			min:      3,
			expected: true,
		},
		{
			name:     "Too short",
			field:    "name",
			value:    "Te",
			min:      3,
			expected: false,
		},
		{
			name:     "Empty string",
			field:    "name",
			value:    "",
			min:      3,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.MinLength(tt.field, tt.value, tt.min)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_MaxLength(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		max      int
		expected bool
	}{
		{
			name:     "Valid length",
			field:    "name",
			value:    "Test",
			max:      10,
			expected: true,
		},
		{
			name:     "Exact maximum length",
			field:    "name",
			value:    "TestValue",
			max:      9,
			expected: true,
		},
		{
			name:     "Too long",
			field:    "name",
			value:    "VeryLongName",
			max:      10,
			expected: false,
		},
		{
			name:     "Empty string",
			field:    "name",
			value:    "",
			max:      10,
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.MaxLength(tt.field, tt.value, tt.max)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_Alphanumeric(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid alphanumeric",
			field:    "id",
			value:    "Test123",
			expected: true,
		},
		{
			name:     "Numbers only",
			field:    "id",
			value:    "123456",
			expected: true,
		},
		{
			name:     "Letters only",
			field:    "id",
			value:    "TestBuilding",
			expected: true,
		},
		{
			name:     "Contains spaces",
			field:    "id",
			value:    "Test 123",
			expected: false,
		},
		{
			name:     "Contains special characters",
			field:    "id",
			value:    "Test-123",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.Alphanumeric(tt.field, tt.value)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_AlphanumericWithSpaces(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid with spaces",
			field:    "name",
			value:    "Test Building 123",
			expected: true,
		},
		{
			name:     "Valid without spaces",
			field:    "name",
			value:    "TestBuilding123",
			expected: true,
		},
		{
			name:     "Contains hyphens",
			field:    "name",
			value:    "Test-Building",
			expected: false,
		},
		{
			name:     "Contains special characters",
			field:    "name",
			value:    "Test@Building",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.AlphanumericWithSpaces(tt.field, tt.value)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_AlphanumericWithHyphens(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid with hyphens",
			field:    "name",
			value:    "Test-Building_123",
			expected: true,
		},
		{
			name:     "Valid with spaces",
			field:    "name",
			value:    "Test Building 123",
			expected: true,
		},
		{
			name:     "Contains special characters",
			field:    "name",
			value:    "Test@Building",
			expected: false,
		},
		{
			name:     "Contains parentheses",
			field:    "name",
			value:    "Test(Building)",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.AlphanumericWithHyphens(tt.field, tt.value)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_UUID(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid UUID",
			field:    "id",
			value:    "550e8400-e29b-41d4-a716-446655440000",
			expected: true,
		},
		{
			name:     "Valid UUID uppercase",
			field:    "id",
			value:    "550E8400-E29B-41D4-A716-446655440000",
			expected: true,
		},
		{
			name:     "Invalid UUID format",
			field:    "id",
			value:    "550e8400-e29b-41d4-a716",
			expected: false,
		},
		{
			name:     "Not a UUID",
			field:    "id",
			value:    "test-id-123",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.UUID(tt.field, tt.value)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_Email(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid email",
			field:    "email",
			value:    "test@example.com",
			expected: true,
		},
		{
			name:     "Valid email with subdomain",
			field:    "email",
			value:    "test@mail.example.com",
			expected: true,
		},
		{
			name:     "Invalid email format",
			field:    "email",
			value:    "test@",
			expected: false,
		},
		{
			name:     "Empty email (optional)",
			field:    "email",
			value:    "",
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.Email(tt.field, tt.value)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_Min(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    int
		min      int
		expected bool
	}{
		{
			name:     "Valid minimum",
			field:    "level",
			value:    5,
			min:      3,
			expected: true,
		},
		{
			name:     "Exact minimum",
			field:    "level",
			value:    3,
			min:      3,
			expected: true,
		},
		{
			name:     "Below minimum",
			field:    "level",
			value:    2,
			min:      3,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.Min(tt.field, tt.value, tt.min)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_Max(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    int
		max      int
		expected bool
	}{
		{
			name:     "Valid maximum",
			field:    "level",
			value:    3,
			max:      5,
			expected: true,
		},
		{
			name:     "Exact maximum",
			field:    "level",
			value:    5,
			max:      5,
			expected: true,
		},
		{
			name:     "Above maximum",
			field:    "level",
			value:    6,
			max:      5,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.Max(tt.field, tt.value, tt.max)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_Range(t *testing.T) {
	tests := []struct {
		name     string
		field    string
		value    int
		min      int
		max      int
		expected bool
	}{
		{
			name:     "Valid range",
			field:    "level",
			value:    3,
			min:      1,
			max:      10,
			expected: true,
		},
		{
			name:     "At minimum",
			field:    "level",
			value:    1,
			min:      1,
			max:      10,
			expected: true,
		},
		{
			name:     "At maximum",
			field:    "level",
			value:    10,
			min:      1,
			max:      10,
			expected: true,
		},
		{
			name:     "Below range",
			field:    "level",
			value:    0,
			min:      1,
			max:      10,
			expected: false,
		},
		{
			name:     "Above range",
			field:    "level",
			value:    11,
			min:      1,
			max:      10,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.Range(tt.field, tt.value, tt.min, tt.max)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_In(t *testing.T) {
	allowed := []string{"hvac", "lighting", "security", "fire"}

	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid choice",
			field:    "type",
			value:    "hvac",
			expected: true,
		},
		{
			name:     "Invalid choice",
			field:    "type",
			value:    "invalid",
			expected: false,
		},
		{
			name:     "Empty value (optional)",
			field:    "type",
			value:    "",
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.In(tt.field, tt.value, allowed)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_NotIn(t *testing.T) {
	forbidden := []string{"admin", "root", "system"}

	tests := []struct {
		name     string
		field    string
		value    string
		expected bool
	}{
		{
			name:     "Valid value",
			field:    "username",
			value:    "user123",
			expected: true,
		},
		{
			name:     "Forbidden value",
			field:    "username",
			value:    "admin",
			expected: false,
		},
		{
			name:     "Empty value (optional)",
			field:    "username",
			value:    "",
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			v := New()
			v.NotIn(tt.field, tt.value, forbidden)
			result := v.Validate()
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidator_Chaining(t *testing.T) {
	v := New()
	result := v.
		Required("name", "Test Building").
		MinLength("name", "Test Building", 3).
		MaxLength("name", "Test Building", 255).
		AlphanumericWithHyphens("name", "Test Building").
		Validate()

	assert.True(t, result.Valid)
	assert.Len(t, result.Errors, 0)
}

func TestValidator_MultipleErrors(t *testing.T) {
	v := New()
	result := v.
		Required("name", "").
		MinLength("name", "", 3).
		MaxLength("name", "", 10).
		Validate()

	assert.False(t, result.Valid)
	assert.Len(t, result.Errors, 2) // Required error and min length error
}

func TestSanitizeString(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "Normal string",
			input:    "Test Building",
			expected: "Test Building",
		},
		{
			name:     "String with extra whitespace",
			input:    "  Test   Building  ",
			expected: "Test Building",
		},
		{
			name:     "String with control characters",
			input:    "Test\x00Building\x01",
			expected: "TestBuilding",
		},
		{
			name:     "String with tabs and newlines",
			input:    "Test\t\nBuilding\r",
			expected: "Test Building",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := SanitizeString(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestValidateBuildingName(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid building name",
			input:    "Main Office Building",
			expected: true,
		},
		{
			name:     "Valid with numbers",
			input:    "Building 123",
			expected: true,
		},
		{
			name:     "Valid with hyphens",
			input:    "Main-Office-Building",
			expected: true,
		},
		{
			name:     "Empty name",
			input:    "",
			expected: false,
		},
		{
			name:     "Too long",
			input:    string(make([]byte, 300)), // 300 character string
			expected: false,
		},
		{
			name:     "Invalid characters",
			input:    "Building@#$%",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateBuildingName(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidateEquipmentName(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid equipment name",
			input:    "HVAC Unit A",
			expected: true,
		},
		{
			name:     "Valid with numbers",
			input:    "Camera 123",
			expected: true,
		},
		{
			name:     "Empty name",
			input:    "",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateEquipmentName(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidateRoomName(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid room name",
			input:    "Conference Room A",
			expected: true,
		},
		{
			name:     "Valid with numbers",
			input:    "Room 101",
			expected: true,
		},
		{
			name:     "Empty name",
			input:    "",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateRoomName(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidateID(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid ID",
			input:    "building-123",
			expected: true,
		},
		{
			name:     "Valid UUID",
			input:    "550e8400-e29b-41d4-a716-446655440000",
			expected: true,
		},
		{
			name:     "Empty ID",
			input:    "",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateID(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidateSimulationType(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid simulation type",
			input:    "energy",
			expected: true,
		},
		{
			name:     "Valid HVAC simulation",
			input:    "hvac",
			expected: true,
		},
		{
			name:     "Invalid simulation type",
			input:    "invalid",
			expected: false,
		},
		{
			name:     "Empty simulation type",
			input:    "",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateSimulationType(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidateFilePath(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid file path",
			input:    "/path/to/file.pdf",
			expected: true,
		},
		{
			name:     "Valid relative path",
			input:    "./file.pdf",
			expected: true,
		},
		{
			name:     "Empty path",
			input:    "",
			expected: false,
		},
		{
			name:     "Too long path",
			input:    string(make([]byte, 5000)), // 5000 character path
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateFilePath(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidateDirectoryPath(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid directory path",
			input:    "/path/to/directory",
			expected: true,
		},
		{
			name:     "Valid relative path",
			input:    "./directory",
			expected: true,
		},
		{
			name:     "Empty path",
			input:    "",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateDirectoryPath(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}

func TestValidateConnectionPath(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "Valid connection path",
			input:    "/building/floor/room",
			expected: true,
		},
		{
			name:     "Valid with dots and dashes",
			input:    "building.floor_room",
			expected: true,
		},
		{
			name:     "Empty path",
			input:    "",
			expected: false,
		},
		{
			name:     "Invalid characters",
			input:    "/building@floor#room",
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateConnectionPath(tt.input)
			assert.Equal(t, tt.expected, result.Valid)
		})
	}
}
