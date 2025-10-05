package utils

import (
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/google/uuid"
)

// IDGenerator provides ID generation utilities following Clean Architecture
type IDGenerator struct{}

// NewIDGenerator creates a new ID generator
func NewIDGenerator() *IDGenerator {
	return &IDGenerator{}
}

// GenerateID generates a new ID with UUID
func (g *IDGenerator) GenerateID() types.ID {
	return types.NewID()
}

// GenerateIDWithLegacy generates a new ID with both UUID and legacy values
func (g *IDGenerator) GenerateIDWithLegacy(legacy string) types.ID {
	return types.NewIDWithLegacy(legacy)
}

// GenerateUUID generates a random UUID string
func (g *IDGenerator) GenerateUUID() string {
	return uuid.New().String()
}

// GenerateEquipmentID generates an equipment ID with legacy format for backward compatibility
func (g *IDGenerator) GenerateEquipmentID(name string) types.ID {
	timestamp := time.Now().Unix()
	legacyID := fmt.Sprintf("EQ-%s-%d", sanitizeName(name), timestamp)
	return types.NewIDWithLegacy(legacyID)
}

// GenerateBuildingID generates a building ID with legacy format for backward compatibility
func (g *IDGenerator) GenerateBuildingID(name string) types.ID {
	timestamp := time.Now().Unix()
	legacyID := fmt.Sprintf("BLD-%s-%d", sanitizeName(name), timestamp)
	return types.NewIDWithLegacy(legacyID)
}

// GenerateUserID generates a user ID with legacy format for backward compatibility
func (g *IDGenerator) GenerateUserID(email string) types.ID {
	timestamp := time.Now().Unix()
	legacyID := fmt.Sprintf("USR-%s-%d", sanitizeName(email), timestamp)
	return types.NewIDWithLegacy(legacyID)
}

// GenerateOrganizationID generates an organization ID with legacy format for backward compatibility
func (g *IDGenerator) GenerateOrganizationID(name string) types.ID {
	timestamp := time.Now().Unix()
	legacyID := fmt.Sprintf("ORG-%s-%d", sanitizeName(name), timestamp)
	return types.NewIDWithLegacy(legacyID)
}

// GenerateFloorID generates a floor ID with legacy format for backward compatibility
func (g *IDGenerator) GenerateFloorID(buildingID types.ID, level int) types.ID {
	timestamp := time.Now().Unix()
	legacyID := fmt.Sprintf("FLR-%s-%d-%d", buildingID.String(), level, timestamp)
	return types.NewIDWithLegacy(legacyID)
}

// GenerateRoomID generates a room ID with legacy format for backward compatibility
func (g *IDGenerator) GenerateRoomID(floorID types.ID, roomNumber string) types.ID {
	timestamp := time.Now().Unix()
	legacyID := fmt.Sprintf("RM-%s-%s-%d", floorID.String(), sanitizeName(roomNumber), timestamp)
	return types.NewIDWithLegacy(legacyID)
}

// sanitizeName sanitizes a name for use in IDs
func sanitizeName(name string) string {
	// Simple sanitization - replace spaces and special chars with dashes
	// This maintains backward compatibility with existing ID formats
	if name == "" {
		return "unknown"
	}

	// Replace spaces and special characters with dashes
	result := ""
	for _, char := range name {
		if char >= 'a' && char <= 'z' || char >= 'A' && char <= 'Z' || char >= '0' && char <= '9' {
			result += string(char)
		} else {
			result += "-"
		}
	}

	// Limit length and clean up multiple dashes
	if len(result) > 20 {
		result = result[:20]
	}

	// Remove leading/trailing dashes
	for len(result) > 0 && result[0] == '-' {
		result = result[1:]
	}
	for len(result) > 0 && result[len(result)-1] == '-' {
		result = result[:len(result)-1]
	}

	if result == "" {
		return "unknown"
	}

	return result
}
