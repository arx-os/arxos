package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/hardware"
)

// TemplateService implements device template management for the hardware platform
type TemplateService struct {
	db *database.PostGISDB
}

// NewTemplateService creates a new TemplateService
func NewTemplateService(db *database.PostGISDB) *TemplateService {
	return &TemplateService{db: db}
}

// GetTemplates retrieves all available device templates
func (ts *TemplateService) GetTemplates(ctx context.Context) ([]*hardware.DeviceTemplate, error) {
	query := `
		SELECT id, name, type, description, schema, firmware, sdk, certification, created_at, updated_at
		FROM device_templates
		ORDER BY created_at DESC
	`

	rows, err := ts.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list templates: %w", err)
	}
	defer rows.Close()

	var templates []*hardware.DeviceTemplate
	for rows.Next() {
		var template hardware.DeviceTemplate
		var schemaJSON, firmwareJSON, sdkJSON, certJSON []byte
		err := rows.Scan(
			&template.ID,
			&template.Name,
			&template.Type,
			&template.Description,
			&schemaJSON,
			&firmwareJSON,
			&sdkJSON,
			&certJSON,
			&template.CreatedAt,
			&template.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan template: %w", err)
		}

		// Parse JSON fields
		if err := json.Unmarshal(schemaJSON, &template.Schema); err != nil {
			template.Schema = make(map[string]interface{})
		}
		if err := json.Unmarshal(firmwareJSON, &template.Firmware); err != nil {
			template.Firmware = []byte{}
		}
		if err := json.Unmarshal(sdkJSON, &template.SDK); err != nil {
			template.SDK = hardware.SDKInfo{}
		}
		if err := json.Unmarshal(certJSON, &template.Certification); err != nil {
			template.Certification = hardware.CertificationInfo{}
		}

		templates = append(templates, &template)
	}

	return templates, nil
}

// GetTemplate retrieves a specific device template
func (ts *TemplateService) GetTemplate(ctx context.Context, templateID string) (*hardware.DeviceTemplate, error) {
	query := `
		SELECT id, name, type, description, schema, firmware, sdk, certification, created_at, updated_at
		FROM device_templates
		WHERE id = $1
	`

	var template hardware.DeviceTemplate
	var schemaJSON, firmwareJSON, sdkJSON, certJSON []byte
	err := ts.db.QueryRow(ctx, query, templateID).Scan(
		&template.ID,
		&template.Name,
		&template.Type,
		&template.Description,
		&schemaJSON,
		&firmwareJSON,
		&sdkJSON,
		&certJSON,
		&template.CreatedAt,
		&template.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("template not found")
		}
		return nil, fmt.Errorf("failed to get template: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(schemaJSON, &template.Schema); err != nil {
		template.Schema = make(map[string]interface{})
	}
	if err := json.Unmarshal(firmwareJSON, &template.Firmware); err != nil {
		template.Firmware = []byte{}
	}
	if err := json.Unmarshal(sdkJSON, &template.SDK); err != nil {
		template.SDK = hardware.SDKInfo{}
	}
	if err := json.Unmarshal(certJSON, &template.Certification); err != nil {
		template.Certification = hardware.CertificationInfo{}
	}

	return &template, nil
}

// CreateTemplate creates a new device template
func (ts *TemplateService) CreateTemplate(ctx context.Context, req hardware.CreateTemplateRequest) (*hardware.DeviceTemplate, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("template name is required")
	}
	if req.Type == "" {
		return nil, fmt.Errorf("template type is required")
	}

	// Validate template
	template := &hardware.DeviceTemplate{
		ID:          generateTemplateID(),
		Name:        req.Name,
		Type:        req.Type,
		Description: req.Description,
		Schema:      req.Schema,
		Firmware:    req.Firmware,
		SDK:         req.SDK,
		Certification: hardware.CertificationInfo{
			Standard:    "ArxOS Certified",
			Level:       "Basic",
			CertifiedAt: time.Now(),
			ExpiresAt:   time.Now().AddDate(1, 0, 0), // 1 year
			Certifier:   "ArxOS Certification Authority",
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if err := ts.ValidateTemplate(ctx, template); err != nil {
		return nil, fmt.Errorf("template validation failed: %w", err)
	}

	// Insert template
	query := `
		INSERT INTO device_templates (id, name, type, description, schema, firmware, sdk, certification, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
		RETURNING id, name, type, description, schema, firmware, sdk, certification, created_at, updated_at`

	var createdTemplate hardware.DeviceTemplate
	var schemaJSON, firmwareJSON, sdkJSON, certJSON []byte
	err := ts.db.QueryRow(ctx, query,
		template.ID,
		template.Name,
		template.Type,
		template.Description,
		template.Schema,
		template.Firmware,
		template.SDK,
		template.Certification,
	).Scan(
		&createdTemplate.ID,
		&createdTemplate.Name,
		&createdTemplate.Type,
		&createdTemplate.Description,
		&schemaJSON,
		&firmwareJSON,
		&sdkJSON,
		&certJSON,
		&createdTemplate.CreatedAt,
		&createdTemplate.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create template: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(schemaJSON, &createdTemplate.Schema); err != nil {
		createdTemplate.Schema = make(map[string]interface{})
	}
	if err := json.Unmarshal(firmwareJSON, &createdTemplate.Firmware); err != nil {
		createdTemplate.Firmware = []byte{}
	}
	if err := json.Unmarshal(sdkJSON, &createdTemplate.SDK); err != nil {
		createdTemplate.SDK = hardware.SDKInfo{}
	}
	if err := json.Unmarshal(certJSON, &createdTemplate.Certification); err != nil {
		createdTemplate.Certification = hardware.CertificationInfo{}
	}

	return &createdTemplate, nil
}

// CreateDeviceFromTemplate creates a new device from a template
func (ts *TemplateService) CreateDeviceFromTemplate(ctx context.Context, templateID string, userID string) (*hardware.Device, error) {
	// Get template
	template, err := ts.GetTemplate(ctx, templateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get template: %w", err)
	}

	// Create device request
	req := hardware.RegisterDeviceRequest{
		Name:       fmt.Sprintf("%s Device", template.Name),
		Type:       template.Type,
		TemplateID: template.ID,
		Config:     make(map[string]interface{}),
		Location: hardware.DeviceLocation{
			BuildingID: "default",
			Floor:      "1",
			Room:       "101",
			Position:   make(map[string]interface{}),
			Path:       "/buildings/default/floors/1/rooms/101",
		},
	}

	// Initialize config from template schema
	if template.Schema != nil {
		req.Config = make(map[string]interface{})
		for key, value := range template.Schema {
			req.Config[key] = value
		}
	}

	// Create hardware service and register device
	hardwareService := NewHardwareService(ts.db)
	return hardwareService.RegisterDevice(ctx, req)
}

// ValidateTemplate validates a device template
func (ts *TemplateService) ValidateTemplate(ctx context.Context, template *hardware.DeviceTemplate) error {
	// Basic validation
	if template.Name == "" {
		return fmt.Errorf("template name is required")
	}
	if template.Type == "" {
		return fmt.Errorf("template type is required")
	}
	if template.Schema == nil {
		return fmt.Errorf("template schema is required")
	}

	// Validate schema structure
	if _, ok := template.Schema["properties"]; !ok {
		return fmt.Errorf("template schema must contain 'properties' field")
	}

	// Validate SDK info
	if template.SDK.Version == "" {
		return fmt.Errorf("SDK version is required")
	}
	if template.SDK.Language == "" {
		return fmt.Errorf("SDK language is required")
	}

	// Validate certification
	if template.Certification.Standard == "" {
		return fmt.Errorf("certification standard is required")
	}

	return nil
}

// Helper functions

func generateTemplateID() string {
	return fmt.Sprintf("tpl_%d", time.Now().UnixNano())
}
