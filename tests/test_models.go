package tests

import (
	"arx/db"
	"arx/models"
	"encoding/json"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"gorm.io/gorm"
)

func setupTestDB(t *testing.T) *gorm.DB {
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

func cleanupTestDB(t *testing.T, database *gorm.DB) {
	database.Migrator().DropTable(&models.SecurityAlert{}, &models.BuildingAsset{}, &models.Building{}, &models.User{})
}

func TestSecurityAlertModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Convert map to JSON bytes for datatypes.JSON field
	detailsJSON, _ := json.Marshal(map[string]interface{}{"attempts": 5})

	// Test creating a security alert
	alert := models.SecurityAlert{
		AlertType: "authentication_failure",
		Severity:  "high",
		IPAddress: "192.168.1.100",
		UserAgent: "Mozilla/5.0",
		Path:      "/api/login",
		Method:    "POST",
		Details:   detailsJSON,
		CreatedAt: time.Now(),
	}

	err := db.Create(&alert).Error
	assert.NoError(t, err)
	assert.NotZero(t, alert.ID)

	// Test retrieving the alert
	var retrieved models.SecurityAlert
	err = db.First(&retrieved, alert.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, alert.AlertType, retrieved.AlertType)
	assert.Equal(t, alert.Severity, retrieved.Severity)
	assert.Equal(t, alert.IPAddress, retrieved.IPAddress)

	// Test resolving the alert
	retrieved.IsResolved = true
	retrieved.ResolvedBy = &[]uint{1}[0]
	resolvedAt := time.Now()
	retrieved.ResolvedAt = &resolvedAt
	retrieved.Notes = "Resolved by admin"

	err = db.Save(&retrieved).Error
	assert.NoError(t, err)

	// Verify resolution
	var resolved models.SecurityAlert
	err = db.First(&resolved, alert.ID).Error
	assert.NoError(t, err)
	assert.True(t, resolved.IsResolved)
	assert.NotNil(t, resolved.ResolvedBy)
	assert.NotNil(t, resolved.ResolvedAt)
}

func TestDataVendorAPIKeyModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Test creating a data vendor API key
	apiKey := models.DataVendorAPIKey{
		Key:         "arx_test_key_1234567890",
		VendorName:  "Test Vendor",
		Email:       "test@vendor.com",
		AccessLevel: "premium",
		RateLimit:   1000,
		IsActive:    true,
		ExpiresAt:   time.Now().AddDate(0, 1, 0), // 1 month from now
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	err := db.Create(&apiKey).Error
	assert.NoError(t, err)
	assert.NotZero(t, apiKey.ID)

	// Test retrieving the API key
	var retrieved models.DataVendorAPIKey
	err = db.First(&retrieved, apiKey.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, apiKey.Key, retrieved.Key)
	assert.Equal(t, apiKey.VendorName, retrieved.VendorName)
	assert.Equal(t, apiKey.AccessLevel, retrieved.AccessLevel)

	// Test deactivating the API key
	retrieved.IsActive = false
	err = db.Save(&retrieved).Error
	assert.NoError(t, err)

	// Verify deactivation
	var deactivated models.DataVendorAPIKey
	err = db.First(&deactivated, apiKey.ID).Error
	assert.NoError(t, err)
	assert.False(t, deactivated.IsActive)
}

func TestAPIKeyUsageModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Create a test API key first
	apiKey := models.DataVendorAPIKey{
		Key:         "arx_test_key_usage",
		VendorName:  "Usage Test Vendor",
		Email:       "usage@vendor.com",
		AccessLevel: "basic",
		RateLimit:   500,
		IsActive:    true,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
	db.Create(&apiKey)

	// Test creating API key usage record
	usage := models.APIKeyUsage{
		APIKeyID:     apiKey.ID,
		Endpoint:     "/api/vendor/buildings",
		Method:       "GET",
		Status:       200,
		ResponseTime: 150,
		RequestSize:  1024,
		ResponseSize: 2048,
		IPAddress:    "192.168.1.100",
		UserAgent:    "Test Client/1.0",
		CreatedAt:    time.Now(),
	}

	err := db.Create(&usage).Error
	assert.NoError(t, err)
	assert.NotZero(t, usage.ID)

	// Test retrieving usage with API key relationship
	var retrieved models.APIKeyUsage
	err = db.Preload("APIKey").First(&retrieved, usage.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, usage.Endpoint, retrieved.Endpoint)
	assert.Equal(t, usage.Status, retrieved.Status)
	assert.NotNil(t, retrieved.APIKey)
	assert.Equal(t, apiKey.VendorName, retrieved.APIKey.VendorName)
}

func TestExportActivityModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Create a test user
	user := models.User{
		Email:    "test@example.com",
		Username: "testuser",
		Password: "hashedpassword",
		Role:     "admin",
	}
	db.Create(&user)

	// Create a test building
	building := models.Building{
		Name:    "Test Building",
		Address: "123 Test St",
		OwnerID: user.ID,
	}
	db.Create(&building)

	// Test creating export activity
	export := models.ExportActivity{
		UserID:         user.ID,
		BuildingID:     building.ID,
		ExportType:     "asset_inventory",
		Format:         "csv",
		Filters:        `{"system": "electrical"}`,
		Status:         "completed",
		FileSize:       1024000,
		DownloadCount:  5,
		ProcessingTime: 2500,
		IPAddress:      "192.168.1.50",
		UserAgent:      "Export Tool/2.0",
		RequestedAt:    time.Now(),
		CompletedAt:    &[]time.Time{time.Now()}[0],
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}

	err := db.Create(&export).Error
	assert.NoError(t, err)
	assert.NotZero(t, export.ID)

	// Test retrieving export with relationships
	var retrieved models.ExportActivity
	err = db.Preload("User").Preload("Building").First(&retrieved, export.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, export.ExportType, retrieved.ExportType)
	assert.Equal(t, export.Status, retrieved.Status)
	assert.NotNil(t, retrieved.User)
	assert.NotNil(t, retrieved.Building)
	assert.Equal(t, user.Username, retrieved.User.Username)
	assert.Equal(t, building.Name, retrieved.Building.Name)

	// Test updating download count
	retrieved.DownloadCount++
	err = db.Save(&retrieved).Error
	assert.NoError(t, err)

	// Verify update
	var updated models.ExportActivity
	err = db.First(&updated, export.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, export.DownloadCount+1, updated.DownloadCount)
}

func TestDataRetentionPolicyModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Test creating a data retention policy
	policy := models.DataRetentionPolicy{
		ObjectType:      "audit_logs",
		RetentionPeriod: 1825, // 5 years
		ArchiveAfter:    90,   // 90 days
		DeleteAfter:     1825, // 5 years
		IsActive:        true,
		Description:     "Audit logs retention policy",
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}

	err := db.Create(&policy).Error
	assert.NoError(t, err)
	assert.NotZero(t, policy.ID)

	// Test retrieving the policy
	var retrieved models.DataRetentionPolicy
	err = db.First(&retrieved, policy.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, policy.ObjectType, retrieved.ObjectType)
	assert.Equal(t, policy.RetentionPeriod, retrieved.RetentionPeriod)
	assert.Equal(t, policy.IsActive, retrieved.IsActive)

	// Test deactivating the policy
	retrieved.IsActive = false
	err = db.Save(&retrieved).Error
	assert.NoError(t, err)

	// Verify deactivation
	var deactivated models.DataRetentionPolicy
	err = db.First(&deactivated, policy.ID).Error
	assert.NoError(t, err)
	assert.False(t, deactivated.IsActive)
}

func TestComplianceReportModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Create a test user
	user := models.User{
		Email:    "auditor@example.com",
		Username: "auditor",
		Password: "hashedpassword",
		Role:     "auditor",
	}
	db.Create(&user)

	// Convert map to JSON bytes for datatypes.JSON field
	parametersJSON, _ := json.Marshal(map[string]interface{}{
		"date_from": "2024-01-01",
		"date_to":   "2024-12-31",
		"format":    "csv",
	})

	// Test creating a compliance report
	report := models.ComplianceReport{
		ReportType:  "data_access",
		ReportName:  "Data Access Report Q1 2024",
		GeneratedBy: user.ID,
		Parameters:  parametersJSON,
		FilePath:    "/reports/data_access_2024_q1.csv",
		FileSize:    1024000,
		Format:      "csv",
		Status:      "completed",
		CreatedAt:   time.Now(),
		CompletedAt: &[]time.Time{time.Now()}[0],
	}

	err := db.Create(&report).Error
	assert.NoError(t, err)
	assert.NotZero(t, report.ID)

	// Test retrieving the report
	var retrieved models.ComplianceReport
	err = db.Preload("User").First(&retrieved, report.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, report.ReportType, retrieved.ReportType)
	assert.Equal(t, report.ReportName, retrieved.ReportName)
	assert.Equal(t, report.Status, retrieved.Status)
	assert.NotNil(t, retrieved.User)
	assert.Equal(t, user.Username, retrieved.User.Username)
}

func TestDataAccessLogModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Create a test user
	user := models.User{
		Email:    "user@example.com",
		Username: "testuser",
		Password: "hashedpassword",
		Role:     "user",
	}
	db.Create(&user)

	// Test creating a data access log
	accessLog := models.DataAccessLog{
		UserID:      user.ID,
		Action:      "view",
		ObjectType:  "building",
		ObjectID:    "building_123",
		IPAddress:   "192.168.1.100",
		UserAgent:   "Mozilla/5.0",
		SessionID:   "session_abc123",
		BuildingID:  &[]uint{1}[0],
		AccessLevel: "basic",
		CreatedAt:   time.Now(),
	}

	err := db.Create(&accessLog).Error
	assert.NoError(t, err)
	assert.NotZero(t, accessLog.ID)

	// Test retrieving the access log
	var retrieved models.DataAccessLog
	err = db.Preload("User").First(&retrieved, accessLog.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, accessLog.Action, retrieved.Action)
	assert.Equal(t, accessLog.ObjectType, retrieved.ObjectType)
	assert.Equal(t, accessLog.ObjectID, retrieved.ObjectID)
	assert.NotNil(t, retrieved.User)
	assert.Equal(t, user.Username, retrieved.User.Username)
}

func TestAuditLogModel(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Convert map to JSON bytes for datatypes.JSON fields
	payloadJSON, _ := json.Marshal(map[string]interface{}{
		"action": "create",
		"data":   map[string]interface{}{"name": "test building"},
	})

	fieldChangesJSON, _ := json.Marshal(map[string]interface{}{
		"name": map[string]interface{}{
			"before": "",
			"after":  "test building",
		},
	})

	contextJSON, _ := json.Marshal(map[string]interface{}{
		"ip_address": "192.168.1.100",
		"user_agent": "Test Client",
	})

	// Test creating an audit log
	auditLog := models.AuditLog{
		UserID:       1,
		ObjectType:   "building",
		ObjectID:     "building_123",
		Action:       "create",
		Payload:      payloadJSON,
		IPAddress:    "192.168.1.100",
		UserAgent:    "Test Client",
		SessionID:    "session_abc123",
		BuildingID:   &[]uint{1}[0],
		FieldChanges: fieldChangesJSON,
		Context:      contextJSON,
		CreatedAt:    time.Now(),
	}

	err := db.Create(&auditLog).Error
	assert.NoError(t, err)
	assert.NotZero(t, auditLog.ID)

	// Test retrieving the audit log
	var retrieved models.AuditLog
	err = db.First(&retrieved, auditLog.ID).Error
	assert.NoError(t, err)
	assert.Equal(t, auditLog.ObjectType, retrieved.ObjectType)
	assert.Equal(t, auditLog.ObjectID, retrieved.ObjectID)
	assert.Equal(t, auditLog.Action, retrieved.Action)
}

func TestModelValidations(t *testing.T) {
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	// Test user validation
	t.Run("User Validation", func(t *testing.T) {
		// Test required fields
		user := models.User{}
		err := db.Create(&user).Error
		assert.Error(t, err) // Should fail due to required fields

		// Test valid user
		validUser := models.User{
			Email:    "valid@example.com",
			Username: "validuser",
			Password: "hashedpassword",
			Role:     "user",
		}
		err = db.Create(&validUser).Error
		assert.NoError(t, err)
	})

	// Test building validation
	t.Run("Building Validation", func(t *testing.T) {
		// Test required fields
		building := models.Building{}
		err := db.Create(&building).Error
		assert.Error(t, err) // Should fail due to required fields

		// Test valid building
		validBuilding := models.Building{
			Name:    "Valid Building",
			Address: "123 Valid St",
			OwnerID: 1,
		}
		err = db.Create(&validBuilding).Error
		assert.NoError(t, err)
	})

	// Test security alert validation
	t.Run("Security Alert Validation", func(t *testing.T) {
		// Test required fields
		alert := models.SecurityAlert{}
		err := db.Create(&alert).Error
		assert.Error(t, err) // Should fail due to required fields

		// Test valid alert
		detailsJSON, _ := json.Marshal(map[string]interface{}{"test": "data"})
		validAlert := models.SecurityAlert{
			AlertType: "test_alert",
			Severity:  "low",
			Details:   detailsJSON,
		}
		err = db.Create(&validAlert).Error
		assert.NoError(t, err)
	})
}
