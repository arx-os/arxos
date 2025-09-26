package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
)

// CertificationService manages device certification and compliance
type CertificationService struct {
	db *database.PostGISDB
}

// NewCertificationService creates a new CertificationService
func NewCertificationService(db *database.PostGISDB) *CertificationService {
	return &CertificationService{db: db}
}

// CertificationRequest represents a device certification request
type CertificationRequest struct {
	DeviceID           string                 `json:"device_id"`
	DeviceName         string                 `json:"device_name"`
	DeviceType         string                 `json:"device_type"`
	Manufacturer       string                 `json:"manufacturer"`
	Model              string                 `json:"model"`
	Specifications     map[string]interface{} `json:"specifications"`
	Documentation      []string               `json:"documentation"`
	TestResults        map[string]interface{} `json:"test_results"`
	ComplianceDocs     []string               `json:"compliance_docs"`
	CertificationLevel string                 `json:"certification_level"`
	RequestedBy        string                 `json:"requested_by"`
	Notes              string                 `json:"notes"`
}

// CertificationResult represents the result of a certification process
type CertificationResult struct {
	ID                  string                 `json:"id"`
	DeviceID            string                 `json:"device_id"`
	Status              string                 `json:"status"`
	CertificationLevel  string                 `json:"certification_level"`
	CertificationNumber string                 `json:"certification_number"`
	ValidFrom           time.Time              `json:"valid_from"`
	ValidUntil          time.Time              `json:"valid_until"`
	TestResults         map[string]interface{} `json:"test_results"`
	ComplianceScore     float64                `json:"compliance_score"`
	IssuedBy            string                 `json:"issued_by"`
	Notes               string                 `json:"notes"`
	CreatedAt           time.Time              `json:"created_at"`
	UpdatedAt           time.Time              `json:"updated_at"`
}

// CertificationStandard represents a certification standard
type CertificationStandard struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Version      string                 `json:"version"`
	Description  string                 `json:"description"`
	Requirements map[string]interface{} `json:"requirements"`
	TestSuite    []string               `json:"test_suite"`
	IsActive     bool                   `json:"is_active"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// SubmitCertificationRequest submits a device for certification
func (cs *CertificationService) SubmitCertificationRequest(ctx context.Context, req CertificationRequest) (*CertificationResult, error) {
	// Validate request
	if req.DeviceID == "" {
		return nil, fmt.Errorf("device ID is required")
	}
	if req.DeviceName == "" {
		return nil, fmt.Errorf("device name is required")
	}
	if req.DeviceType == "" {
		return nil, fmt.Errorf("device type is required")
	}
	if req.Manufacturer == "" {
		return nil, fmt.Errorf("manufacturer is required")
	}
	if req.Model == "" {
		return nil, fmt.Errorf("model is required")
	}

	// Generate certification ID
	certificationID := generateCertificationID()

	// Create certification result
	result := &CertificationResult{
		ID:                  certificationID,
		DeviceID:            req.DeviceID,
		Status:              "pending",
		CertificationLevel:  req.CertificationLevel,
		CertificationNumber: fmt.Sprintf("ARX-CERT-%s", certificationID),
		ValidFrom:           time.Now(),
		ValidUntil:          time.Now().AddDate(2, 0, 0), // 2 years
		TestResults:         req.TestResults,
		ComplianceScore:     0.0,
		IssuedBy:            "ArxOS Certification Authority",
		Notes:               req.Notes,
		CreatedAt:           time.Now(),
		UpdatedAt:           time.Now(),
	}

	// Insert certification request into database
	query := `
		INSERT INTO certification_requests (
			id, device_id, device_name, device_type, manufacturer, model,
			specifications, documentation, test_results, compliance_docs,
			certification_level, requested_by, notes, status, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'pending', NOW(), NOW())
		RETURNING id, device_id, device_name, device_type, manufacturer, model,
				  specifications, documentation, test_results, compliance_docs,
				  certification_level, requested_by, notes, status, created_at, updated_at`

	var insertedReq struct {
		ID                 string                 `json:"id"`
		DeviceID           string                 `json:"device_id"`
		DeviceName         string                 `json:"device_name"`
		DeviceType         string                 `json:"device_type"`
		Manufacturer       string                 `json:"manufacturer"`
		Model              string                 `json:"model"`
		Specifications     map[string]interface{} `json:"specifications"`
		Documentation      []string               `json:"documentation"`
		TestResults        map[string]interface{} `json:"test_results"`
		ComplianceDocs     []string               `json:"compliance_docs"`
		CertificationLevel string                 `json:"certification_level"`
		RequestedBy        string                 `json:"requested_by"`
		Notes              string                 `json:"notes"`
		Status             string                 `json:"status"`
		CreatedAt          time.Time              `json:"created_at"`
		UpdatedAt          time.Time              `json:"updated_at"`
	}

	var specsJSON, docsJSON, testJSON, complianceJSON []byte
	err := cs.db.QueryRow(ctx, query,
		certificationID,
		req.DeviceID,
		req.DeviceName,
		req.DeviceType,
		req.Manufacturer,
		req.Model,
		req.Specifications,
		req.Documentation,
		req.TestResults,
		req.ComplianceDocs,
		req.CertificationLevel,
		req.RequestedBy,
		req.Notes,
	).Scan(
		&insertedReq.ID,
		&insertedReq.DeviceID,
		&insertedReq.DeviceName,
		&insertedReq.DeviceType,
		&insertedReq.Manufacturer,
		&insertedReq.Model,
		&specsJSON,
		&docsJSON,
		&testJSON,
		&complianceJSON,
		&insertedReq.CertificationLevel,
		&insertedReq.RequestedBy,
		&insertedReq.Notes,
		&insertedReq.Status,
		&insertedReq.CreatedAt,
		&insertedReq.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to submit certification request: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(specsJSON, &insertedReq.Specifications); err != nil {
		insertedReq.Specifications = make(map[string]interface{})
	}
	if err := json.Unmarshal(docsJSON, &insertedReq.Documentation); err != nil {
		insertedReq.Documentation = []string{}
	}
	if err := json.Unmarshal(testJSON, &insertedReq.TestResults); err != nil {
		insertedReq.TestResults = make(map[string]interface{})
	}
	if err := json.Unmarshal(complianceJSON, &insertedReq.ComplianceDocs); err != nil {
		insertedReq.ComplianceDocs = []string{}
	}

	return result, nil
}

// ProcessCertificationRequest processes a certification request
func (cs *CertificationService) ProcessCertificationRequest(ctx context.Context, requestID string, approved bool, notes string) (*CertificationResult, error) {
	// Get certification request
	req, err := cs.GetCertificationRequest(ctx, requestID)
	if err != nil {
		return nil, fmt.Errorf("failed to get certification request: %w", err)
	}

	// Determine certification level based on test results and compliance
	complianceScore := cs.calculateComplianceScore(req.TestResults, req.ComplianceDocs)
	certificationLevel := cs.determineCertificationLevel(complianceScore, req.CertificationLevel)

	// Create certification result
	result := &CertificationResult{
		ID:                  requestID,
		DeviceID:            req.DeviceID,
		Status:              map[bool]string{true: "certified", false: "rejected"}[approved],
		CertificationLevel:  certificationLevel,
		CertificationNumber: fmt.Sprintf("ARX-CERT-%s", requestID),
		ValidFrom:           time.Now(),
		ValidUntil:          time.Now().AddDate(2, 0, 0), // 2 years
		TestResults:         req.TestResults,
		ComplianceScore:     complianceScore,
		IssuedBy:            "ArxOS Certification Authority",
		Notes:               notes,
		CreatedAt:           time.Now(),
		UpdatedAt:           time.Now(),
	}

	// Update request status
	status := map[bool]string{true: "certified", false: "rejected"}[approved]
	updateQuery := `
		UPDATE certification_requests 
		SET status = $1, notes = $2, updated_at = NOW()
		WHERE id = $3
	`
	_, err = cs.db.Exec(ctx, updateQuery, status, notes, requestID)
	if err != nil {
		return nil, fmt.Errorf("failed to update certification request: %w", err)
	}

	// If approved, add to certified devices marketplace
	if approved {
		err = cs.addToMarketplace(ctx, req, result)
		if err != nil {
			return nil, fmt.Errorf("failed to add device to marketplace: %w", err)
		}
	}

	return result, nil
}

// GetCertificationRequest retrieves a certification request
func (cs *CertificationService) GetCertificationRequest(ctx context.Context, requestID string) (*CertificationRequest, error) {
	query := `
		SELECT id, device_id, device_name, device_type, manufacturer, model,
			   specifications, documentation, test_results, compliance_docs,
			   certification_level, requested_by, notes, status, created_at, updated_at
		FROM certification_requests
		WHERE id = $1
	`

	var req CertificationRequest
	var specsJSON, docsJSON, testJSON, complianceJSON []byte
	var status string
	var createdAt, updatedAt time.Time

	err := cs.db.QueryRow(ctx, query, requestID).Scan(
		&req.DeviceID,
		&req.DeviceID,
		&req.DeviceName,
		&req.DeviceType,
		&req.Manufacturer,
		&req.Model,
		&specsJSON,
		&docsJSON,
		&testJSON,
		&complianceJSON,
		&req.CertificationLevel,
		&req.RequestedBy,
		&req.Notes,
		&status,
		&createdAt,
		&updatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("certification request not found")
		}
		return nil, fmt.Errorf("failed to get certification request: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(specsJSON, &req.Specifications); err != nil {
		req.Specifications = make(map[string]interface{})
	}
	if err := json.Unmarshal(docsJSON, &req.Documentation); err != nil {
		req.Documentation = []string{}
	}
	if err := json.Unmarshal(testJSON, &req.TestResults); err != nil {
		req.TestResults = make(map[string]interface{})
	}
	if err := json.Unmarshal(complianceJSON, &req.ComplianceDocs); err != nil {
		req.ComplianceDocs = []string{}
	}

	return &req, nil
}

// ListCertificationRequests lists all certification requests
func (cs *CertificationService) ListCertificationRequests(ctx context.Context, status string) ([]*CertificationRequest, error) {
	query := `
		SELECT id, device_id, device_name, device_type, manufacturer, model,
			   specifications, documentation, test_results, compliance_docs,
			   certification_level, requested_by, notes, status, created_at, updated_at
		FROM certification_requests
	`
	args := []interface{}{}
	argIndex := 1

	if status != "" {
		query += fmt.Sprintf(" WHERE status = $%d", argIndex)
		args = append(args, status)
		argIndex++
	}

	query += " ORDER BY created_at DESC"

	rows, err := cs.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list certification requests: %w", err)
	}
	defer rows.Close()

	var requests []*CertificationRequest
	for rows.Next() {
		var req CertificationRequest
		var specsJSON, docsJSON, testJSON, complianceJSON []byte
		var status string
		var createdAt, updatedAt time.Time

		err := rows.Scan(
			&req.DeviceID,
			&req.DeviceID,
			&req.DeviceName,
			&req.DeviceType,
			&req.Manufacturer,
			&req.Model,
			&specsJSON,
			&docsJSON,
			&testJSON,
			&complianceJSON,
			&req.CertificationLevel,
			&req.RequestedBy,
			&req.Notes,
			&status,
			&createdAt,
			&updatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan certification request: %w", err)
		}

		// Parse JSON fields
		if err := json.Unmarshal(specsJSON, &req.Specifications); err != nil {
			req.Specifications = make(map[string]interface{})
		}
		if err := json.Unmarshal(docsJSON, &req.Documentation); err != nil {
			req.Documentation = []string{}
		}
		if err := json.Unmarshal(testJSON, &req.TestResults); err != nil {
			req.TestResults = make(map[string]interface{})
		}
		if err := json.Unmarshal(complianceJSON, &req.ComplianceDocs); err != nil {
			req.ComplianceDocs = []string{}
		}

		requests = append(requests, &req)
	}

	return requests, nil
}

// Helper methods

func (cs *CertificationService) calculateComplianceScore(testResults map[string]interface{}, complianceDocs []string) float64 {
	// Simple compliance scoring algorithm
	// In a real implementation, this would be much more sophisticated
	score := 0.0

	// Check test results
	if testResults != nil {
		if _, ok := testResults["safety_tests"]; ok {
			score += 0.3
		}
		if _, ok := testResults["performance_tests"]; ok {
			score += 0.3
		}
		if _, ok := testResults["security_tests"]; ok {
			score += 0.2
		}
		if _, ok := testResults["compatibility_tests"]; ok {
			score += 0.2
		}
	}

	// Check compliance documentation
	if len(complianceDocs) > 0 {
		score += 0.1 * float64(len(complianceDocs))
		if score > 1.0 {
			score = 1.0
		}
	}

	return score
}

func (cs *CertificationService) determineCertificationLevel(complianceScore float64, requestedLevel string) string {
	if complianceScore >= 0.9 {
		return "Premium"
	} else if complianceScore >= 0.7 {
		return "Standard"
	} else if complianceScore >= 0.5 {
		return "Basic"
	}
	return "Pending"
}

func (cs *CertificationService) addToMarketplace(ctx context.Context, req *CertificationRequest, result *CertificationResult) error {
	// Calculate pricing based on certification level and device type
	basePrice := 99.99
	switch result.CertificationLevel {
	case "Premium":
		basePrice = 299.99
	case "Standard":
		basePrice = 199.99
	case "Basic":
		basePrice = 99.99
	}

	// Add to certified devices table
	query := `
		INSERT INTO certified_devices (
			id, name, type, price, certification, description, features, specifications,
			availability, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'available', NOW())
	`

	features := []string{
		fmt.Sprintf("ArxOS %s Certified", result.CertificationLevel),
		"Hardware Compatibility Guaranteed",
		"SDK and Documentation Included",
		"Community Support",
	}

	if result.CertificationLevel == "Premium" {
		features = append(features, "Priority Support", "Advanced Analytics", "Custom Integration")
	}

	_, err := cs.db.Exec(ctx, query,
		req.DeviceID,
		req.DeviceName,
		req.DeviceType,
		basePrice,
		result.CertificationNumber,
		fmt.Sprintf("Certified %s device from %s", req.DeviceType, req.Manufacturer),
		features,
		req.Specifications,
	)

	return err
}

func generateCertificationID() string {
	return fmt.Sprintf("cert_%d", time.Now().UnixNano())
}
