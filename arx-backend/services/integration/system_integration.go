package integration

import (
	"context"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"gorm.io/gorm"
)

// SystemType represents supported external system types
type SystemType string

const (
	SystemTypeCMMS   SystemType = "cmms"
	SystemTypeERP    SystemType = "erp"
	SystemTypeSCADA  SystemType = "scada"
	SystemTypeBMS    SystemType = "bms"
	SystemTypeIOT    SystemType = "iot"
	SystemTypeCustom SystemType = "custom"
)

// ConnectionStatus represents connection status
type ConnectionStatus string

const (
	ConnectionStatusConnected    ConnectionStatus = "connected"
	ConnectionStatusDisconnected ConnectionStatus = "disconnected"
	ConnectionStatusConnecting   ConnectionStatus = "connecting"
	ConnectionStatusError        ConnectionStatus = "error"
	ConnectionStatusMaintenance  ConnectionStatus = "maintenance"
)

// SyncDirection represents synchronization direction
type SyncDirection string

const (
	SyncDirectionInbound       SyncDirection = "inbound"
	SyncDirectionOutbound      SyncDirection = "outbound"
	SyncDirectionBidirectional SyncDirection = "bidirectional"
)

// ConflictResolution represents conflict resolution strategies
type ConflictResolution string

const (
	ConflictResolutionArxosWins      ConflictResolution = "arxos_wins"
	ConflictResolutionExternalWins   ConflictResolution = "external_wins"
	ConflictResolutionManual         ConflictResolution = "manual"
	ConflictResolutionMerge          ConflictResolution = "merge"
	ConflictResolutionTimestampBased ConflictResolution = "timestamp_based"
)

// SystemConnection represents a system connection configuration
type SystemConnection struct {
	ID             string           `json:"id" gorm:"primaryKey"`
	SystemID       string           `json:"system_id"`
	SystemType     SystemType       `json:"system_type"`
	ConnectionName string           `json:"connection_name"`
	Host           string           `json:"host"`
	Port           int              `json:"port"`
	Username       string           `json:"username"`
	Password       string           `json:"password"`
	Database       *string          `json:"database"`
	APIKey         *string          `json:"api_key"`
	SSLEnabled     bool             `json:"ssl_enabled"`
	Timeout        int              `json:"timeout"`
	RetryAttempts  int              `json:"retry_attempts"`
	Status         ConnectionStatus `json:"status"`
	LastSync       *time.Time       `json:"last_sync"`
	CreatedAt      time.Time        `json:"created_at"`
	UpdatedAt      time.Time        `json:"updated_at"`
}

// FieldMapping represents field mapping configuration
type FieldMapping struct {
	ID                 string    `json:"id" gorm:"primaryKey"`
	SystemID           string    `json:"system_id"`
	ArxosField         string    `json:"arxos_field"`
	ExternalField      string    `json:"external_field"`
	TransformationRule *string   `json:"transformation_rule"`
	IsRequired         bool      `json:"is_required"`
	DataType           string    `json:"data_type"`
	ValidationRule     *string   `json:"validation_rule"`
	CreatedAt          time.Time `json:"created_at"`
	UpdatedAt          time.Time `json:"updated_at"`
}

// TransformationRule represents a data transformation rule
type TransformationRule struct {
	ID             string    `json:"id" gorm:"primaryKey"`
	RuleName       string    `json:"rule_name"`
	RuleType       string    `json:"rule_type"` // calculation, validation, formatting
	RuleExpression string    `json:"rule_expression"`
	InputFields    []string  `json:"input_fields"`
	OutputField    string    `json:"output_field"`
	Description    *string   `json:"description"`
	IsActive       bool      `json:"is_active"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

// SyncResult represents synchronization result
type SyncResult struct {
	ID                string        `json:"id" gorm:"primaryKey"`
	SystemID          string        `json:"system_id"`
	Direction         SyncDirection `json:"direction"`
	RecordsProcessed  int           `json:"records_processed"`
	RecordsSuccessful int           `json:"records_successful"`
	RecordsFailed     int           `json:"records_failed"`
	ConflictsResolved int           `json:"conflicts_resolved"`
	SyncDuration      float64       `json:"sync_duration"`
	Status            string        `json:"status"`
	ErrorMessage      *string       `json:"error_message"`
	Timestamp         time.Time     `json:"timestamp"`
}

// SystemIntegration handles multi-system integration
type SystemIntegration struct {
	db              *gorm.DB
	mu              sync.RWMutex
	connections     map[string]*SystemConnection
	transformations map[string]*TransformationRule
	httpClient      *http.Client
	config          *IntegrationConfig
}

// IntegrationConfig holds configuration for system integration
type IntegrationConfig struct {
	DefaultTimeout     time.Duration `json:"default_timeout"`
	MaxRetryAttempts   int           `json:"max_retry_attempts"`
	EnableSSL          bool          `json:"enable_ssl"`
	EnableCompression  bool          `json:"enable_compression"`
	EnableEncryption   bool          `json:"enable_encryption"`
	EncryptionKey      string        `json:"encryption_key"`
	EnableMonitoring   bool          `json:"enable_monitoring"`
	MonitoringInterval time.Duration `json:"monitoring_interval"`
}

// NewSystemIntegration creates a new system integration service
func NewSystemIntegration(db *gorm.DB, config *IntegrationConfig) *SystemIntegration {
	if config == nil {
		config = &IntegrationConfig{
			DefaultTimeout:     30 * time.Second,
			MaxRetryAttempts:   3,
			EnableSSL:          true,
			EnableCompression:  true,
			EnableEncryption:   true,
			EnableMonitoring:   true,
			MonitoringInterval: 5 * time.Minute,
		}
	}

	return &SystemIntegration{
		db:              db,
		connections:     make(map[string]*SystemConnection),
		transformations: make(map[string]*TransformationRule),
		httpClient:      &http.Client{Timeout: config.DefaultTimeout},
		config:          config,
	}
}

// CreateSystemConnection creates a new system connection
func (si *SystemIntegration) CreateSystemConnection(ctx context.Context, connection *SystemConnection) error {
	// Validate connection configuration
	if err := si.validateConnectionConfig(connection); err != nil {
		return fmt.Errorf("invalid connection config: %w", err)
	}

	// Encrypt sensitive data
	if si.config.EnableEncryption {
		if err := si.encryptConnectionData(connection); err != nil {
			return fmt.Errorf("failed to encrypt connection data: %w", err)
		}
	}

	connection.ID = generateIntegrationID()
	connection.Status = ConnectionStatusDisconnected
	connection.CreatedAt = time.Now()
	connection.UpdatedAt = time.Now()

	if err := si.db.WithContext(ctx).Create(connection).Error; err != nil {
		return fmt.Errorf("failed to create connection: %w", err)
	}

	si.mu.Lock()
	si.connections[connection.ID] = connection
	si.mu.Unlock()

	return nil
}

// TestConnection tests a system connection
func (si *SystemIntegration) TestConnection(ctx context.Context, systemID string) (*map[string]interface{}, error) {
	var connection SystemConnection
	if err := si.db.WithContext(ctx).Where("system_id = ?", systemID).First(&connection).Error; err != nil {
		return nil, fmt.Errorf("connection not found: %w", err)
	}

	// Decrypt sensitive data for testing
	if si.config.EnableEncryption {
		if err := si.decryptConnectionData(&connection); err != nil {
			return nil, fmt.Errorf("failed to decrypt connection data: %w", err)
		}
	}

	result, err := si.testSystemConnection(&connection)
	if err != nil {
		// Update connection status to error
		connection.Status = ConnectionStatusError
		connection.UpdatedAt = time.Now()
		si.db.WithContext(ctx).Save(&connection)
		return nil, err
	}

	// Update connection status to connected
	connection.Status = ConnectionStatusConnected
	connection.UpdatedAt = time.Now()
	si.db.WithContext(ctx).Save(&connection)

	return result, nil
}

// CreateFieldMapping creates a new field mapping
func (si *SystemIntegration) CreateFieldMapping(ctx context.Context, mapping *FieldMapping) error {
	if err := si.validateMappingConfig(mapping); err != nil {
		return fmt.Errorf("invalid mapping config: %w", err)
	}

	mapping.ID = generateIntegrationID()
	mapping.CreatedAt = time.Now()
	mapping.UpdatedAt = time.Now()

	return si.db.WithContext(ctx).Create(mapping).Error
}

// TransformData transforms data according to field mappings
func (si *SystemIntegration) TransformData(ctx context.Context, data map[string]interface{}, systemID string, direction string) (map[string]interface{}, error) {
	var mappings []FieldMapping
	if err := si.db.WithContext(ctx).Where("system_id = ?", systemID).Find(&mappings).Error; err != nil {
		return nil, fmt.Errorf("failed to get field mappings: %w", err)
	}

	transformedData := make(map[string]interface{})

	for _, mapping := range mappings {
		var sourceField, targetField string

		if direction == "inbound" {
			sourceField = mapping.ExternalField
			targetField = mapping.ArxosField
		} else {
			sourceField = mapping.ArxosField
			targetField = mapping.ExternalField
		}

		if value, exists := data[sourceField]; exists {
			transformedValue := value

			// Apply transformation rule if specified
			if mapping.TransformationRule != nil {
				if transformed, err := si.applyTransformationRule(value, *mapping.TransformationRule); err == nil {
					transformedValue = transformed
				}
			}

			// Apply validation rule if specified
			if mapping.ValidationRule != nil {
				if valid, err := si.applyValidationRule(transformedValue, *mapping.ValidationRule); err != nil || !valid {
					if mapping.IsRequired {
						return nil, fmt.Errorf("validation failed for required field %s", sourceField)
					}
					continue // Skip this field if validation fails and it's not required
				}
			}

			transformedData[targetField] = transformedValue
		} else if mapping.IsRequired {
			return nil, fmt.Errorf("required field %s not found in data", sourceField)
		}
	}

	return transformedData, nil
}

// SyncData synchronizes data with external systems
func (si *SystemIntegration) SyncData(ctx context.Context, systemID string, direction SyncDirection, data []map[string]interface{}, conflictResolution ConflictResolution) (*SyncResult, error) {
	startTime := time.Now()

	var connection SystemConnection
	if err := si.db.WithContext(ctx).Where("system_id = ?", systemID).First(&connection).Error; err != nil {
		return nil, fmt.Errorf("connection not found: %w", err)
	}

	// Decrypt connection data
	if si.config.EnableEncryption {
		if err := si.decryptConnectionData(&connection); err != nil {
			return nil, fmt.Errorf("failed to decrypt connection data: %w", err)
		}
	}

	result := &SyncResult{
		ID:               generateIntegrationID(),
		SystemID:         systemID,
		Direction:        direction,
		RecordsProcessed: len(data),
		Status:           "in_progress",
		Timestamp:        time.Now(),
	}

	// Perform synchronization based on system type
	syncResult, err := si.performSync(&connection, direction, data, conflictResolution)
	if err != nil {
		result.Status = "failed"
		errorMsg := err.Error()
		result.ErrorMessage = &errorMsg
		result.SyncDuration = time.Since(startTime).Seconds()

		// Save result
		si.db.WithContext(ctx).Create(result)
		return result, err
	}

	// Update result with sync details
	result.RecordsSuccessful = syncResult["records_successful"].(int)
	result.RecordsFailed = syncResult["records_failed"].(int)
	result.ConflictsResolved = syncResult["conflicts_resolved"].(int)
	result.Status = "completed"
	result.SyncDuration = time.Since(startTime).Seconds()

	// Update connection last sync time
	connection.LastSync = &result.Timestamp
	connection.UpdatedAt = time.Now()
	si.db.WithContext(ctx).Save(&connection)

	// Save result
	si.db.WithContext(ctx).Create(result)

	return result, nil
}

// GetConnectionStatus gets the status of a system connection
func (si *SystemIntegration) GetConnectionStatus(ctx context.Context, systemID string) (*map[string]interface{}, error) {
	var connection SystemConnection
	if err := si.db.WithContext(ctx).Where("system_id = ?", systemID).First(&connection).Error; err != nil {
		return nil, fmt.Errorf("connection not found: %w", err)
	}

	status := map[string]interface{}{
		"system_id":       connection.SystemID,
		"status":          connection.Status,
		"last_sync":       connection.LastSync,
		"updated_at":      connection.UpdatedAt,
		"connection_name": connection.ConnectionName,
	}

	// Add health check if connection is active
	if connection.Status == ConnectionStatusConnected {
		if health, err := si.checkConnectionHealth(&connection); err == nil {
			status["health"] = health
		}
	}

	return &status, nil
}

// GetAllConnections gets all system connections
func (si *SystemIntegration) GetAllConnections(ctx context.Context) ([]SystemConnection, error) {
	var connections []SystemConnection
	if err := si.db.WithContext(ctx).Find(&connections).Error; err != nil {
		return nil, fmt.Errorf("failed to get connections: %w", err)
	}
	return connections, nil
}

// GetSyncHistory gets synchronization history
func (si *SystemIntegration) GetSyncHistory(ctx context.Context, systemID *string, startDate *time.Time, endDate *time.Time) ([]SyncResult, error) {
	var results []SyncResult
	query := si.db.WithContext(ctx)

	if systemID != nil {
		query = query.Where("system_id = ?", *systemID)
	}

	if startDate != nil {
		query = query.Where("timestamp >= ?", *startDate)
	}

	if endDate != nil {
		query = query.Where("timestamp <= ?", *endDate)
	}

	if err := query.Order("timestamp DESC").Find(&results).Error; err != nil {
		return nil, fmt.Errorf("failed to get sync history: %w", err)
	}

	return results, nil
}

// validateConnectionConfig validates connection configuration
func (si *SystemIntegration) validateConnectionConfig(connection *SystemConnection) error {
	if connection.SystemID == "" {
		return fmt.Errorf("system_id is required")
	}
	if connection.ConnectionName == "" {
		return fmt.Errorf("connection_name is required")
	}
	if connection.Host == "" {
		return fmt.Errorf("host is required")
	}
	if connection.Port <= 0 || connection.Port > 65535 {
		return fmt.Errorf("port must be between 1 and 65535")
	}
	if connection.Username == "" {
		return fmt.Errorf("username is required")
	}
	if connection.Password == "" {
		return fmt.Errorf("password is required")
	}
	return nil
}

// validateMappingConfig validates mapping configuration
func (si *SystemIntegration) validateMappingConfig(mapping *FieldMapping) error {
	if mapping.SystemID == "" {
		return fmt.Errorf("system_id is required")
	}
	if mapping.ArxosField == "" {
		return fmt.Errorf("arxos_field is required")
	}
	if mapping.ExternalField == "" {
		return fmt.Errorf("external_field is required")
	}
	return nil
}

// testSystemConnection tests a system connection
func (si *SystemIntegration) testSystemConnection(connection *SystemConnection) (*map[string]interface{}, error) {
	switch connection.SystemType {
	case SystemTypeCMMS:
		return si.testCMMSConnection(connection)
	case SystemTypeERP:
		return si.testERPConnection(connection)
	case SystemTypeSCADA:
		return si.testSCADAConnection(connection)
	case SystemTypeBMS:
		return si.testBMSConnection(connection)
	case SystemTypeIOT:
		return si.testIOTConnection(connection)
	default:
		return nil, fmt.Errorf("unsupported system type: %s", connection.SystemType)
	}
}

// testCMMSConnection tests a CMMS connection
func (si *SystemIntegration) testCMMSConnection(connection *SystemConnection) (*map[string]interface{}, error) {
	// Mock implementation - in real implementation, this would test CMMS API connectivity
	result := map[string]interface{}{
		"status":    "success",
		"message":   "CMMS connection test successful",
		"timestamp": time.Now(),
	}
	return &result, nil
}

// testERPConnection tests an ERP connection
func (si *SystemIntegration) testERPConnection(connection *SystemConnection) (*map[string]interface{}, error) {
	// Mock implementation - in real implementation, this would test ERP API connectivity
	result := map[string]interface{}{
		"status":    "success",
		"message":   "ERP connection test successful",
		"timestamp": time.Now(),
	}
	return &result, nil
}

// testSCADAConnection tests a SCADA connection
func (si *SystemIntegration) testSCADAConnection(connection *SystemConnection) (*map[string]interface{}, error) {
	// Mock implementation - in real implementation, this would test SCADA connectivity
	result := map[string]interface{}{
		"status":    "success",
		"message":   "SCADA connection test successful",
		"timestamp": time.Now(),
	}
	return &result, nil
}

// testBMSConnection tests a BMS connection
func (si *SystemIntegration) testBMSConnection(connection *SystemConnection) (*map[string]interface{}, error) {
	// Mock implementation - in real implementation, this would test BMS connectivity
	result := map[string]interface{}{
		"status":    "success",
		"message":   "BMS connection test successful",
		"timestamp": time.Now(),
	}
	return &result, nil
}

// testIOTConnection tests an IoT connection
func (si *SystemIntegration) testIOTConnection(connection *SystemConnection) (*map[string]interface{}, error) {
	// Mock implementation - in real implementation, this would test IoT connectivity
	result := map[string]interface{}{
		"status":    "success",
		"message":   "IoT connection test successful",
		"timestamp": time.Now(),
	}
	return &result, nil
}

// performSync performs data synchronization
func (si *SystemIntegration) performSync(connection *SystemConnection, direction SyncDirection, data []map[string]interface{}, conflictResolution ConflictResolution) (map[string]interface{}, error) {
	// Mock implementation - in real implementation, this would perform actual synchronization
	result := map[string]interface{}{
		"records_successful": len(data),
		"records_failed":     0,
		"conflicts_resolved": 0,
		"status":             "completed",
	}
	return result, nil
}

// applyTransformationRule applies a transformation rule to data
func (si *SystemIntegration) applyTransformationRule(value interface{}, rule string) (interface{}, error) {
	// Mock implementation - in real implementation, this would apply complex transformation rules
	return value, nil
}

// applyValidationRule applies a validation rule to data
func (si *SystemIntegration) applyValidationRule(value interface{}, rule string) (bool, error) {
	// Mock implementation - in real implementation, this would apply validation rules
	return true, nil
}

// checkConnectionHealth checks the health of a connection
func (si *SystemIntegration) checkConnectionHealth(connection *SystemConnection) (map[string]interface{}, error) {
	// Mock implementation - in real implementation, this would perform health checks
	return map[string]interface{}{
		"status":    "healthy",
		"latency":   50.0,
		"timestamp": time.Now(),
	}, nil
}

// encryptConnectionData encrypts sensitive connection data
func (si *SystemIntegration) encryptConnectionData(connection *SystemConnection) error {
	if si.config.EncryptionKey == "" {
		return fmt.Errorf("encryption key not configured")
	}

	// Encrypt password
	if connection.Password != "" {
		encrypted, err := si.encryptString(connection.Password)
		if err != nil {
			return err
		}
		connection.Password = encrypted
	}

	// Encrypt API key if present
	if connection.APIKey != nil && *connection.APIKey != "" {
		encrypted, err := si.encryptString(*connection.APIKey)
		if err != nil {
			return err
		}
		connection.APIKey = &encrypted
	}

	return nil
}

// decryptConnectionData decrypts sensitive connection data
func (si *SystemIntegration) decryptConnectionData(connection *SystemConnection) error {
	if si.config.EncryptionKey == "" {
		return fmt.Errorf("encryption key not configured")
	}

	// Decrypt password
	if connection.Password != "" {
		decrypted, err := si.decryptString(connection.Password)
		if err != nil {
			return err
		}
		connection.Password = decrypted
	}

	// Decrypt API key if present
	if connection.APIKey != nil && *connection.APIKey != "" {
		decrypted, err := si.decryptString(*connection.APIKey)
		if err != nil {
			return err
		}
		connection.APIKey = &decrypted
	}

	return nil
}

// encryptString encrypts a string using AES
func (si *SystemIntegration) encryptString(plaintext string) (string, error) {
	key := sha256.Sum256([]byte(si.config.EncryptionKey))
	block, err := aes.NewCipher(key[:])
	if err != nil {
		return "", err
	}

	ciphertext := make([]byte, aes.BlockSize+len(plaintext))
	iv := ciphertext[:aes.BlockSize]
	if _, err := io.ReadFull(rand.Reader, iv); err != nil {
		return "", err
	}

	stream := cipher.NewCFBEncrypter(block, iv)
	stream.XORKeyStream(ciphertext[aes.BlockSize:], []byte(plaintext))

	return base64.URLEncoding.EncodeToString(ciphertext), nil
}

// decryptString decrypts a string using AES
func (si *SystemIntegration) decryptString(ciphertext string) (string, error) {
	key := sha256.Sum256([]byte(si.config.EncryptionKey))
	block, err := aes.NewCipher(key[:])
	if err != nil {
		return "", err
	}

	ciphertextBytes, err := base64.URLEncoding.DecodeString(ciphertext)
	if err != nil {
		return "", err
	}

	if len(ciphertextBytes) < aes.BlockSize {
		return "", fmt.Errorf("ciphertext too short")
	}

	iv := ciphertextBytes[:aes.BlockSize]
	ciphertextBytes = ciphertextBytes[aes.BlockSize:]

	stream := cipher.NewCFBDecrypter(block, iv)
	stream.XORKeyStream(ciphertextBytes, ciphertextBytes)

	return string(ciphertextBytes), nil
}

// generateIntegrationID generates a unique ID for integration entities
func generateIntegrationID() string {
	return fmt.Sprintf("int_%d", time.Now().UnixNano())
}
