package tests

import (
	"arxos/db"
	"arxos/models"
	"encoding/json"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"gorm.io/gorm"
)

// SetupTestDB initializes a test database connection
func SetupTestDB(t *testing.T) *gorm.DB {
	// Set up test environment
	os.Setenv("JWT_SECRET", "test-secret-key")
	os.Setenv("DB_HOST", "localhost")
	os.Setenv("DB_PORT", "5432")
	os.Setenv("DB_USER", "arxos_user")
	os.Setenv("DB_PASSWORD", "arxos_password")
	os.Setenv("DB_NAME", "arxos_test")

	// Connect to test database
	db.Connect()

	// Clean up tables
	db.DB.Migrator().DropTable(&models.SecurityAlert{}, &models.BuildingAsset{}, &models.Building{}, &models.User{})

	// Auto migrate
	db.DB.AutoMigrate(&models.User{}, &models.Building{}, &models.BuildingAsset{}, &models.SecurityAlert{})

	return db.DB
}

// CleanupTestDB cleans up the test database
func CleanupTestDB(t *testing.T, database *gorm.DB) {
	database.Migrator().DropTable(&models.SecurityAlert{}, &models.BuildingAsset{}, &models.Building{}, &models.User{})
}

// CreateTestUser creates a test user with the given email, username, and role
func CreateTestUser(t *testing.T, email, username, role string) models.User {
	user := models.User{
		Email:     email,
		Username:  username,
		Password:  "hashedpassword",
		Role:      role,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	database := SetupTestDB(t)
	err := database.Create(&user).Error
	assert.NoError(t, err)

	return user
}

// CreateTestBuilding creates a test building for the given ownerID
func CreateTestBuilding(t *testing.T, ownerID uint) models.Building {
	building := models.Building{
		Name:      "Test Building",
		Address:   "123 Test St",
		OwnerID:   ownerID,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	database := SetupTestDB(t)
	err := database.Create(&building).Error
	assert.NoError(t, err)

	return building
}

// CreateTestAsset creates a test asset for the given buildingID
func CreateTestAsset(t *testing.T, buildingID uint) models.BuildingAsset {
	location := models.AssetLocation{
		Floor: "1st Floor",
		Room:  "101",
		X:     150.5,
		Y:     200.0,
	}

	specifications := map[string]interface{}{
		"manufacturer": "Test Corp",
		"model":        "TEST-100",
	}

	specsJSON, _ := json.Marshal(specifications)

	asset := models.BuildingAsset{
		BuildingID:      buildingID,
		FloorID:         1,
		RoomID:          "ROOM_101",
		SymbolID:        "test_symbol",
		AssetType:       "HVAC",
		System:          "Heating",
		Subsystem:       "Air Handling",
		Location:        location,
		Specifications:  specsJSON,
		EstimatedValue:  10000.00,
		ReplacementCost: 12000.00,
		Status:          "active",
		CreatedBy:       1,
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}

	database := SetupTestDB(t)
	err := database.Create(&asset).Error
	assert.NoError(t, err)

	return asset
}

// CreateTestAPIKey creates a test API key for data vendor testing
func CreateTestAPIKey(t *testing.T, vendorName, email, accessLevel string) models.DataVendorAPIKey {
	apiKey := models.DataVendorAPIKey{
		Key:         fmt.Sprintf("arx_test_%s_%d", vendorName, time.Now().Unix()),
		VendorName:  vendorName,
		Email:       email,
		AccessLevel: accessLevel,
		RateLimit:   1000,
		IsActive:    true,
		ExpiresAt:   time.Now().AddDate(0, 1, 0),
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	database := SetupTestDB(t)
	err := database.Create(&apiKey).Error
	assert.NoError(t, err)

	return apiKey
}

// GenerateTestToken generates a test JWT token for the given userID and role
func GenerateTestToken(userID uint, role string) string {
	// This is a simple test token - in a real implementation, you'd use proper JWT signing
	return fmt.Sprintf("test.jwt.token.for.user.%d.role.%s", userID, role)
}
