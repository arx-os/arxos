package validation

import (
	"testing"
)

func TestValidateStruct(t *testing.T) {
	tests := []struct {
		name    string
		input   interface{}
		wantErr bool
	}{
		{
			name: "valid email",
			input: struct {
				Email string `validate:"required,email"`
			}{Email: "user@example.com"},
			wantErr: false,
		},
		{
			name: "invalid email",
			input: struct {
				Email string `validate:"required,email"`
			}{Email: "invalid-email"},
			wantErr: true,
		},
		{
			name: "required field missing",
			input: struct {
				Name string `validate:"required"`
			}{Name: ""},
			wantErr: true,
		},
		{
			name: "string length validation",
			input: struct {
				Name string `validate:"required,min=2,max=100"`
			}{Name: "Jo"},
			wantErr: false,
		},
		{
			name: "string too short",
			input: struct {
				Name string `validate:"required,min=2,max=100"`
			}{Name: "J"},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateStruct(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateStruct() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestArxosIDValidation(t *testing.T) {
	tests := []struct {
		name    string
		arxosID string
		wantErr bool
	}{
		{
			name:    "valid simple ArxOS ID",
			arxosID: "ARXOS-001",
			wantErr: false,
		},
		{
			name:    "valid complex ArxOS ID",
			arxosID: "ARXOS-NA-US-NY-NYC-0001",
			wantErr: false,
		},
		{
			name:    "invalid - missing prefix",
			arxosID: "001",
			wantErr: true,
		},
		{
			name:    "invalid - too short",
			arxosID: "ARXOS-0",
			wantErr: true,
		},
		{
			name:    "empty string (should pass - let required handle it)",
			arxosID: "",
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			input := struct {
				ArxosID string `validate:"arxos_id"`
			}{ArxosID: tt.arxosID}
			
			err := ValidateStruct(input)
			if (err != nil) != tt.wantErr {
				t.Errorf("ArxosID validation error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestBuildingPathValidation(t *testing.T) {
	tests := []struct {
		name    string
		path    string
		wantErr bool
	}{
		{
			name:    "valid building path",
			path:    "/B1/3/A/301",
			wantErr: false,
		},
		{
			name:    "valid full path",
			path:    "/B1/3/A/301/HVAC/UNIT-01",
			wantErr: false,
		},
		{
			name:    "invalid - missing leading slash",
			path:    "B1/3/A/301",
			wantErr: true,
		},
		{
			name:    "invalid - too short",
			path:    "/B1",
			wantErr: true,
		},
		{
			name:    "empty string (should pass - let required handle it)",
			path:    "",
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			input := struct {
				Path string `validate:"building_path"`
			}{Path: tt.path}
			
			err := ValidateStruct(input)
			if (err != nil) != tt.wantErr {
				t.Errorf("BuildingPath validation error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestGPSCoordinateValidation(t *testing.T) {
	tests := []struct {
		name      string
		latitude  float64
		longitude float64
		wantErr   bool
	}{
		{
			name:      "valid coordinates - NYC",
			latitude:  40.748817,
			longitude: -73.985428,
			wantErr:   false,
		},
		{
			name:      "valid coordinates - North Pole",
			latitude:  90.0,
			longitude: 0.0,
			wantErr:   false,
		},
		{
			name:      "valid coordinates - South Pole",
			latitude:  -90.0,
			longitude: 180.0,
			wantErr:   false,
		},
		{
			name:      "invalid - latitude too high",
			latitude:  91.0,
			longitude: 0.0,
			wantErr:   true,
		},
		{
			name:      "invalid - latitude too low",
			latitude:  -91.0,
			longitude: 0.0,
			wantErr:   true,
		},
		{
			name:      "invalid - longitude too high",
			latitude:  0.0,
			longitude: 181.0,
			wantErr:   true,
		},
		{
			name:      "invalid - longitude too low",
			latitude:  0.0,
			longitude: -181.0,
			wantErr:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			input := struct {
				Latitude  float64 `validate:"gps_latitude"`
				Longitude float64 `validate:"gps_longitude"`
			}{
				Latitude:  tt.latitude,
				Longitude: tt.longitude,
			}
			
			err := ValidateStruct(input)
			if (err != nil) != tt.wantErr {
				t.Errorf("GPS validation error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestEquipmentStatusValidation(t *testing.T) {
	tests := []struct {
		name    string
		status  string
		wantErr bool
	}{
		{
			name:    "valid - OPERATIONAL",
			status:  "OPERATIONAL",
			wantErr: false,
		},
		{
			name:    "valid - FAILED",
			status:  "FAILED",
			wantErr: false,
		},
		{
			name:    "valid - MAINTENANCE",
			status:  "MAINTENANCE",
			wantErr: false,
		},
		{
			name:    "valid - lowercase operational",
			status:  "operational",
			wantErr: false,
		},
		{
			name:    "invalid status",
			status:  "BROKEN",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			input := struct {
				Status string `validate:"equipment_status"`
			}{Status: tt.status}
			
			err := ValidateStruct(input)
			if (err != nil) != tt.wantErr {
				t.Errorf("EquipmentStatus validation error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestValidationErrors(t *testing.T) {
	input := struct {
		Email    string  `json:"email" validate:"required,email"`
		Password string  `json:"password" validate:"required,min=8"`
		Age      int     `json:"age" validate:"required,gte=0,lte=120"`
		Latitude float64 `json:"latitude" validate:"gps_latitude"`
	}{
		Email:    "invalid",
		Password: "short",
		Age:      150,
		Latitude: 100.0,
	}

	err := ValidateStruct(input)
	if err == nil {
		t.Fatal("Expected validation errors, got nil")
	}

	validationErrs, ok := err.(ValidationErrors)
	if !ok {
		t.Fatalf("Expected ValidationErrors type, got %T", err)
	}

	if len(validationErrs) == 0 {
		t.Fatal("Expected validation errors, got empty slice")
	}

	// Should have errors for email, password, age, and latitude
	if len(validationErrs) < 3 {
		t.Errorf("Expected at least 3 validation errors, got %d", len(validationErrs))
	}

	// Check that fields are properly populated
	for _, ve := range validationErrs {
		if ve.Field == "" {
			t.Error("Validation error missing field name")
		}
		if ve.Message == "" {
			t.Error("Validation error missing message")
		}
		if ve.Tag == "" {
			t.Error("Validation error missing tag")
		}
	}
}

