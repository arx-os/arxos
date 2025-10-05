package main

import (
	"fmt"
	"log"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/domain/validation"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
)

func main() {
	fmt.Println("=== ArxOS UUID Migration Test ===")

	// Test ID generation
	fmt.Println("\n1. Testing ID Generation:")
	idGenerator := utils.NewIDGenerator()

	// Generate new ID
	newID := idGenerator.GenerateID()
	fmt.Printf("New ID: %s (UUID: %s, Legacy: %s)\n", newID.String(), newID.UUID, newID.Legacy)

	// Generate building ID
	buildingID := idGenerator.GenerateBuildingID("Test Building")
	fmt.Printf("Building ID: %s (UUID: %s, Legacy: %s)\n", buildingID.String(), buildingID.UUID, buildingID.Legacy)

	// Generate user ID
	userID := idGenerator.GenerateUserID("test@example.com")
	fmt.Printf("User ID: %s (UUID: %s, Legacy: %s)\n", userID.String(), userID.UUID, userID.Legacy)

	// Test ID validation
	fmt.Println("\n2. Testing ID Validation:")
	validator := validation.NewIDValidator()

	// Test UUID validation
	if err := validator.ValidateUUID(newID.UUID); err != nil {
		fmt.Printf("UUID validation failed: %v\n", err)
	} else {
		fmt.Printf("UUID validation passed: %s\n", newID.UUID)
	}

	// Test legacy ID validation
	if err := validator.ValidateLegacyID(buildingID.Legacy); err != nil {
		fmt.Printf("Legacy ID validation failed: %v\n", err)
	} else {
		fmt.Printf("Legacy ID validation passed: %s\n", buildingID.Legacy)
	}

	// Test full ID validation
	if err := validator.ValidateID(newID); err != nil {
		fmt.Printf("Full ID validation failed: %v\n", err)
	} else {
		fmt.Printf("Full ID validation passed\n")
	}

	// Test ID conversion
	fmt.Println("\n3. Testing ID Conversion:")

	// Test from string
	fromStringID := types.FromString("550e8400-e29b-41d4-a716-446655440000")
	fmt.Printf("From UUID string: %s (UUID: %s, Legacy: %s)\n", fromStringID.String(), fromStringID.UUID, fromStringID.Legacy)

	fromLegacyID := types.FromString("BLD-test-building-1234567890")
	fmt.Printf("From legacy string: %s (UUID: %s, Legacy: %s)\n", fromLegacyID.String(), fromLegacyID.UUID, fromLegacyID.Legacy)

	// Test ID operations
	fmt.Println("\n4. Testing ID Operations:")

	id1 := types.NewID()
	id2 := types.NewID()
	id3 := types.NewIDWithLegacy("test-legacy")

	fmt.Printf("ID1: %s\n", id1.String())
	fmt.Printf("ID2: %s\n", id2.String())
	fmt.Printf("ID3: %s\n", id3.String())

	fmt.Printf("ID1 is empty: %t\n", id1.IsEmpty())
	fmt.Printf("ID1 is valid: %t\n", id1.IsValid())
	fmt.Printf("ID1 is UUID: %t\n", id1.IsUUID())
	fmt.Printf("ID3 is legacy: %t\n", id3.IsLegacy())

	fmt.Printf("ID1 equals ID2: %t\n", id1.Equal(id2))
	fmt.Printf("ID1 equals ID1: %t\n", id1.Equal(id1))

	// Test JSON marshaling
	fmt.Println("\n5. Testing JSON Marshaling:")

	jsonData, err := id1.MarshalJSON()
	if err != nil {
		log.Printf("JSON marshaling failed: %v", err)
	} else {
		fmt.Printf("JSON: %s\n", string(jsonData))
	}

	var unmarshaledID types.ID
	if err := unmarshaledID.UnmarshalJSON(jsonData); err != nil {
		log.Printf("JSON unmarshaling failed: %v", err)
	} else {
		fmt.Printf("Unmarshaled ID: %s\n", unmarshaledID.String())
	}

	fmt.Println("\n=== Test Completed Successfully ===")
}
