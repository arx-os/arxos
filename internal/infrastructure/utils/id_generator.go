package utils

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"time"
)

// IDGenerator provides ID generation utilities following Clean Architecture
type IDGenerator struct{}

// NewIDGenerator creates a new ID generator
func NewIDGenerator() *IDGenerator {
	return &IDGenerator{}
}

// GenerateUUID generates a random UUID-like string
func (g *IDGenerator) GenerateUUID() string {
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		// Fallback to timestamp-based ID
		return fmt.Sprintf("%d", time.Now().UnixNano())
	}

	// Format as UUID-like string
	return fmt.Sprintf("%s-%s-%s-%s-%s",
		hex.EncodeToString(b[0:4]),
		hex.EncodeToString(b[4:6]),
		hex.EncodeToString(b[6:8]),
		hex.EncodeToString(b[8:10]),
		hex.EncodeToString(b[10:16]))
}

// GenerateEquipmentID generates an equipment ID
func (g *IDGenerator) GenerateEquipmentID(name string) string {
	timestamp := time.Now().Unix()
	return fmt.Sprintf("EQ-%s-%d", sanitizeName(name), timestamp)
}

// GenerateBuildingID generates a building ID
func (g *IDGenerator) GenerateBuildingID(name string) string {
	timestamp := time.Now().Unix()
	return fmt.Sprintf("BLD-%s-%d", sanitizeName(name), timestamp)
}

// GenerateUserID generates a user ID
func (g *IDGenerator) GenerateUserID(email string) string {
	timestamp := time.Now().Unix()
	return fmt.Sprintf("USR-%s-%d", sanitizeName(email), timestamp)
}

// GenerateOrganizationID generates an organization ID
func (g *IDGenerator) GenerateOrganizationID(name string) string {
	timestamp := time.Now().Unix()
	return fmt.Sprintf("ORG-%s-%d", sanitizeName(name), timestamp)
}

// sanitizeName sanitizes a name for use in IDs
func sanitizeName(name string) string {
	// Simple sanitization - replace spaces and special chars with dashes
	result := ""
	for _, char := range name {
		if (char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || (char >= '0' && char <= '9') {
			result += string(char)
		} else {
			result += "-"
		}
	}

	// Limit length and clean up multiple dashes
	if len(result) > 10 {
		result = result[:10]
	}

	// Remove leading/trailing dashes
	for len(result) > 0 && result[0] == '-' {
		result = result[1:]
	}
	for len(result) > 0 && result[len(result)-1] == '-' {
		result = result[:len(result)-1]
	}

	if result == "" {
		result = "ID"
	}

	return result
}
