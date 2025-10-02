package validation

import (
	"strings"
	"testing"
)

// TestBuilding represents a test building struct
type TestBuilding struct {
	ID           string  `json:"id"`
	Name         string  `json:"name"`
	Address      string  `json:"address"`
	BuildingType string  `json:"building_type"`
	Status       string  `json:"status"`
	GridScale    float64 `json:"grid_scale"`
	Coverage     float64 `json:"coverage"`
}

// TestFloor represents a test floor struct
type TestFloor struct {
	ID     string  `json:"id"`
	Level  int     `json:"level"`
	Name   string  `json:"name"`
	Height float64 `json:"height"`
}

// TestEquipment represents a test equipment struct
type TestEquipment struct {
	ID     string `json:"id"`
	Name   string `json:"name"`
	Type   string `json:"type"`
	Path   string `json:"path"`
	Status string `json:"status"`
	Model  string `json:"model"`
}

// TestRoom represents a test room struct
type TestRoom struct {
	ID   string  `json:"id"`
	Name string  `json:"name"`
	Type string  `json:"type"`
	Area float64 `json:"area"`
}

// TestSpatial represents a test spatial struct
type TestSpatial struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

func TestBaseValidator(t *testing.T) {
	validator := NewBaseValidator()

	// Add test rules
	validator.AddRule("name", ValidationRule{
		Name:     "name",
		Required: true,
		Type:     "string",
		Min:      1,
		Max:      100,
	})

	validator.AddRule("age", ValidationRule{
		Name:     "age",
		Required: false,
		Type:     "int",
		Min:      0,
		Max:      150,
	})

	// Test valid data
	validData := struct {
		Name string `json:"name"`
		Age  int    `json:"age"`
	}{
		Name: "John Doe",
		Age:  30,
	}

	result := validator.Validate(validData)
	if !result.IsValid() {
		t.Errorf("Expected valid data to pass validation, got errors: %v", result.Errors)
	}

	// Test invalid data
	invalidData := struct {
		Name string `json:"name"`
		Age  int    `json:"age"`
	}{
		Name: "",  // Empty name should fail
		Age:  200, // Age too high should fail
	}

	result = validator.Validate(invalidData)
	if result.IsValid() {
		t.Error("Expected invalid data to fail validation")
	}

	if len(result.Errors) != 2 {
		t.Errorf("Expected 2 errors, got %d", len(result.Errors))
	}
}

func TestBuildingValidator(t *testing.T) {
	validator := NewBuildingValidator()

	tests := []struct {
		name     string
		building TestBuilding
		expected bool
	}{
		{
			name: "Valid building",
			building: TestBuilding{
				ID:           "building-001",
				Name:         "Test Building",
				Address:      "123 Main St",
				BuildingType: "office",
				Status:       "active",
				GridScale:    1.0,
				Coverage:     75.5,
			},
			expected: true,
		},
		{
			name: "Missing required fields",
			building: TestBuilding{
				ID:   "",
				Name: "",
			},
			expected: false,
		},
		{
			name: "Invalid building type",
			building: TestBuilding{
				ID:           "building-002",
				Name:         "Test Building 2",
				BuildingType: "invalid_type",
			},
			expected: false,
		},
		{
			name: "Invalid status",
			building: TestBuilding{
				ID:     "building-003",
				Name:   "Test Building 3",
				Status: "invalid_status",
			},
			expected: false,
		},
		{
			name: "Invalid grid scale",
			building: TestBuilding{
				ID:        "building-004",
				Name:      "Test Building 4",
				GridScale: -1.0, // Negative scale
			},
			expected: false,
		},
		{
			name: "Invalid coverage",
			building: TestBuilding{
				ID:       "building-005",
				Name:     "Test Building 5",
				Coverage: 150.0, // Over 100%
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.ValidateBuilding(tt.building)
			if result.IsValid() != tt.expected {
				t.Errorf("Expected validation result %v, got %v. Errors: %v", tt.expected, result.IsValid(), result.Errors)
			}
		})
	}
}

func TestFloorValidator(t *testing.T) {
	validator := NewFloorValidator()

	tests := []struct {
		name     string
		floor    TestFloor
		expected bool
	}{
		{
			name: "Valid floor",
			floor: TestFloor{
				ID:     "floor-001",
				Level:  1,
				Name:   "Ground Floor",
				Height: 3.5,
			},
			expected: true,
		},
		{
			name: "Missing required fields",
			floor: TestFloor{
				ID:    "",
				Level: 0,
				Name:  "",
			},
			expected: false,
		},
		{
			name: "Invalid level",
			floor: TestFloor{
				ID:    "floor-002",
				Level: -20, // Too low
				Name:  "Basement Floor",
			},
			expected: false,
		},
		{
			name: "Invalid height",
			floor: TestFloor{
				ID:     "floor-003",
				Level:  2,
				Name:   "Second Floor",
				Height: -1.0, // Negative height
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.Validate(tt.floor)
			if result.IsValid() != tt.expected {
				t.Errorf("Expected validation result %v, got %v. Errors: %v", tt.expected, result.IsValid(), result.Errors)
			}
		})
	}
}

func TestEquipmentValidator(t *testing.T) {
	validator := NewEquipmentValidator()

	tests := []struct {
		name      string
		equipment TestEquipment
		expected  bool
	}{
		{
			name: "Valid equipment",
			equipment: TestEquipment{
				ID:     "equipment-001",
				Name:   "HVAC Unit 1",
				Type:   "hvac",
				Path:   "N/3/A/301/E",
				Status: "OPERATIONAL",
				Model:  "HVAC-1000",
			},
			expected: true,
		},
		{
			name: "Missing required fields",
			equipment: TestEquipment{
				ID:   "",
				Name: "",
				Type: "",
			},
			expected: false,
		},
		{
			name: "Invalid equipment type",
			equipment: TestEquipment{
				ID:   "equipment-002",
				Name: "Test Equipment",
				Type: "invalid_type",
			},
			expected: false,
		},
		{
			name: "Invalid equipment path",
			equipment: TestEquipment{
				ID:   "equipment-003",
				Name: "Test Equipment",
				Type: "hvac",
				Path: "invalid/path/format",
			},
			expected: false,
		},
		{
			name: "Invalid status",
			equipment: TestEquipment{
				ID:     "equipment-004",
				Name:   "Test Equipment",
				Type:   "hvac",
				Status: "INVALID_STATUS",
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.Validate(tt.equipment)
			if result.IsValid() != tt.expected {
				t.Errorf("Expected validation result %v, got %v. Errors: %v", tt.expected, result.IsValid(), result.Errors)
			}
		})
	}
}

func TestRoomValidator(t *testing.T) {
	validator := NewRoomValidator()

	tests := []struct {
		name     string
		room     TestRoom
		expected bool
	}{
		{
			name: "Valid room",
			room: TestRoom{
				ID:   "room-001",
				Name: "Office 101",
				Type: "office",
				Area: 25.5,
			},
			expected: true,
		},
		{
			name: "Missing required fields",
			room: TestRoom{
				ID:   "",
				Name: "",
			},
			expected: false,
		},
		{
			name: "Invalid room type",
			room: TestRoom{
				ID:   "room-002",
				Name: "Test Room",
				Type: "invalid_type",
			},
			expected: false,
		},
		{
			name: "Invalid area",
			room: TestRoom{
				ID:   "room-003",
				Name: "Test Room",
				Type: "office",
				Area: -10.0, // Negative area
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.Validate(tt.room)
			if result.IsValid() != tt.expected {
				t.Errorf("Expected validation result %v, got %v. Errors: %v", tt.expected, result.IsValid(), result.Errors)
			}
		})
	}
}

func TestSpatialValidator(t *testing.T) {
	validator := NewSpatialValidator()

	tests := []struct {
		name     string
		spatial  TestSpatial
		expected bool
	}{
		{
			name: "Valid spatial data",
			spatial: TestSpatial{
				X: 1000.0,
				Y: 2000.0,
				Z: 100.0,
			},
			expected: true,
		},
		{
			name: "Invalid coordinates",
			spatial: TestSpatial{
				X: 2000000.0, // Too large
				Y: 2000000.0,
				Z: 2000000.0,
			},
			expected: false,
		},
		{
			name: "Negative coordinates",
			spatial: TestSpatial{
				X: -2000000.0, // Too small
				Y: -2000000.0,
				Z: -2000000.0,
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validator.Validate(tt.spatial)
			if result.IsValid() != tt.expected {
				t.Errorf("Expected validation result %v, got %v. Errors: %v", tt.expected, result.IsValid(), result.Errors)
			}
		})
	}
}

func TestValidationContext(t *testing.T) {
	context := NewValidationContext("building-001", "user-001", "create")

	if context.BuildingID != "building-001" {
		t.Errorf("Expected building ID 'building-001', got '%s'", context.BuildingID)
	}

	if context.UserID != "user-001" {
		t.Errorf("Expected user ID 'user-001', got '%s'", context.UserID)
	}

	if context.Operation != "create" {
		t.Errorf("Expected operation 'create', got '%s'", context.Operation)
	}

	if context.Timestamp.IsZero() {
		t.Error("Expected timestamp to be set")
	}
}

func TestValidationError(t *testing.T) {
	err := ValidationError{
		Field:   "name",
		Message: "field is required",
		Code:    "REQUIRED",
		Value:   "",
	}

	expected := "validation failed for field 'name': field is required"
	if err.Error() != expected {
		t.Errorf("Expected error message '%s', got '%s'", expected, err.Error())
	}
}

func TestValidationResult(t *testing.T) {
	result := &ValidationResult{Valid: true}

	// Test adding error
	result.AddError("field1", "error message", "ERROR_CODE", "value")
	if result.IsValid() {
		t.Error("Expected result to be invalid after adding error")
	}

	if len(result.Errors) != 1 {
		t.Errorf("Expected 1 error, got %d", len(result.Errors))
	}

	// Test adding warning
	result.AddWarning("field2", "warning message", "WARNING_CODE", "value")
	if len(result.Warnings) != 1 {
		t.Errorf("Expected 1 warning, got %d", len(result.Warnings))
	}
}

func TestHelperFunctions(t *testing.T) {
	// Test isValidEmail
	tests := []struct {
		email    string
		expected bool
	}{
		{"test@example.com", true},
		{"user.name+tag@domain.co.uk", true},
		{"invalid-email", false},
		{"@domain.com", false},
		{"user@", false},
		{"", false},
	}

	for _, tt := range tests {
		result := isValidEmail(tt.email)
		if result != tt.expected {
			t.Errorf("Expected isValidEmail('%s') to be %v, got %v", tt.email, tt.expected, result)
		}
	}

	// Test isValidUUID
	uuidTests := []struct {
		uuid     string
		expected bool
	}{
		{"550e8400-e29b-41d4-a716-446655440000", true},
		{"550E8400-E29B-41D4-A716-446655440000", true}, // Case insensitive
		{"invalid-uuid", false},
		{"550e8400-e29b-41d4-a716", false}, // Too short
		{"", false},
	}

	for _, tt := range uuidTests {
		result := isValidUUID(tt.uuid)
		if result != tt.expected {
			t.Errorf("Expected isValidUUID('%s') to be %v, got %v", tt.uuid, tt.expected, result)
		}
	}
}

func TestCustomValidation(t *testing.T) {
	validator := NewBaseValidator()

	// Add custom validation rule
	validator.AddRule("custom_field", ValidationRule{
		Name:        "custom_field",
		Description: "Custom field validation",
		Required:    true,
		Type:        "string",
		Custom: func(value interface{}) bool {
			if str, ok := value.(string); ok {
				return len(str) >= 5 && strings.Contains(str, "test")
			}
			return false
		},
	})

	// Test valid custom value
	validData := struct {
		CustomField string `json:"custom_field"`
	}{
		CustomField: "test123",
	}

	result := validator.Validate(validData)
	if !result.IsValid() {
		t.Errorf("Expected valid custom data to pass validation, got errors: %v", result.Errors)
	}

	// Test invalid custom value
	invalidData := struct {
		CustomField string `json:"custom_field"`
	}{
		CustomField: "short", // Too short and doesn't contain "test"
	}

	result = validator.Validate(invalidData)
	if result.IsValid() {
		t.Error("Expected invalid custom data to fail validation")
	}
}
