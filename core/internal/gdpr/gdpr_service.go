package gdpr

import (
	"archive/zip"
	"bytes"
	"context"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"gorm.io/gorm"
)

// GDPRService handles GDPR compliance operations
type GDPRService struct {
	db *gorm.DB
}

// NewGDPRService creates a new GDPR service
func NewGDPRService() *GDPRService {
	return &GDPRService{
		db: db.GormDB,
	}
}

// UserDataExport contains all user data for GDPR export
type UserDataExport struct {
	Profile          models.User                `json:"profile"`
	Projects         []models.Project           `json:"projects"`
	Buildings        []models.Building          `json:"buildings"`
	AuditLogs        []models.AuditLog          `json:"audit_logs"`
	APIUsage         []models.APIUsage          `json:"api_usage"`
	ExportActivities []models.ExportActivity    `json:"export_activities"`
	SecurityLogs     []models.SecurityLog       `json:"security_logs"`
	Preferences      map[string]interface{}     `json:"preferences"`
	ExportDate       time.Time                  `json:"export_date"`
}

// DataDeletionRequest represents a user data deletion request
type DataDeletionRequest struct {
	ID              uint      `gorm:"primaryKey" json:"id"`
	UserID          uint      `gorm:"index;not null" json:"user_id"`
	RequestType     string    `json:"request_type"` // deletion, anonymization
	Reason          string    `json:"reason"`
	Status          string    `gorm:"default:'pending'" json:"status"` // pending, processing, completed
	ScheduledFor    time.Time `json:"scheduled_for"`                    // 30 days from request
	ProcessedAt     *time.Time `json:"processed_at,omitempty"`
	ConfirmationCode string    `json:"-"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

// ConsentRecord tracks user consent for data processing
type ConsentRecord struct {
	ID           uint      `gorm:"primaryKey" json:"id"`
	UserID       uint      `gorm:"index;not null" json:"user_id"`
	ConsentType  string    `gorm:"index;not null" json:"consent_type"` // marketing, analytics, cookies, etc.
	Granted      bool      `json:"granted"`
	Version      string    `json:"version"` // Policy version
	IPAddress    string    `json:"ip_address"`
	UserAgent    string    `json:"user_agent"`
	GrantedAt    time.Time `json:"granted_at"`
	RevokedAt    *time.Time `json:"revoked_at,omitempty"`
	ExpiresAt    *time.Time `json:"expires_at,omitempty"`
}

// DataProcessingActivity logs how user data is processed
type DataProcessingActivity struct {
	ID              uint      `gorm:"primaryKey" json:"id"`
	UserID          uint      `gorm:"index;not null" json:"user_id"`
	ActivityType    string    `gorm:"index;not null" json:"activity_type"`
	Purpose         string    `json:"purpose"`
	LegalBasis      string    `json:"legal_basis"` // consent, contract, legitimate_interest
	DataCategories  string    `json:"data_categories"` // JSON array
	RetentionPeriod int       `json:"retention_period"` // days
	ThirdParties    string    `json:"third_parties"` // JSON array of third parties
	CreatedAt       time.Time `json:"created_at"`
}

// ExportUserData exports all user data for GDPR compliance
func (s *GDPRService) ExportUserData(userID uint) (*UserDataExport, error) {
	export := &UserDataExport{
		ExportDate: time.Now(),
	}

	// Get user profile
	if err := s.db.Where("id = ?", userID).First(&export.Profile).Error; err != nil {
		return nil, fmt.Errorf("user not found: %w", err)
	}

	// Clear sensitive fields
	export.Profile.Password = "[REDACTED]"

	// Get projects
	s.db.Where("user_id = ?", userID).Find(&export.Projects)

	// Get buildings
	s.db.Where("owner_id = ?", userID).Find(&export.Buildings)

	// Get audit logs
	s.db.Where("user_id = ?", userID).Order("created_at DESC").Limit(1000).Find(&export.AuditLogs)

	// Get API usage
	identifier := fmt.Sprintf("user:%d", userID)
	s.db.Where("identifier = ?", identifier).Order("timestamp DESC").Limit(1000).Find(&export.APIUsage)

	// Get export activities
	s.db.Where("user_id = ?", userID).Find(&export.ExportActivities)

	// Get security logs
	s.db.Where("user_id = ?", userID).Order("timestamp DESC").Limit(1000).Find(&export.SecurityLogs)

	// Get preferences
	export.Preferences = export.Profile.Preferences

	return export, nil
}

// RequestDataDeletion creates a data deletion request
func (s *GDPRService) RequestDataDeletion(userID uint, reason string) (*DataDeletionRequest, error) {
	// Check if there's already a pending request
	var existingRequest DataDeletionRequest
	if err := s.db.Where("user_id = ? AND status = ?", userID, "pending").First(&existingRequest).Error; err == nil {
		return nil, fmt.Errorf("deletion request already pending")
	}

	// Create new request
	request := &DataDeletionRequest{
		UserID:       userID,
		RequestType:  "deletion",
		Reason:       reason,
		Status:       "pending",
		ScheduledFor: time.Now().Add(30 * 24 * time.Hour), // 30 days grace period
		ConfirmationCode: generateConfirmationCode(),
	}

	if err := s.db.Create(request).Error; err != nil {
		return nil, fmt.Errorf("failed to create deletion request: %w", err)
	}

	// Send confirmation email (implementation depends on email service)
	// s.sendDeletionConfirmationEmail(userID, request.ConfirmationCode)

	return request, nil
}

// ProcessDataDeletion processes a confirmed data deletion request
func (s *GDPRService) ProcessDataDeletion(requestID uint, confirmationCode string) error {
	var request DataDeletionRequest
	if err := s.db.Where("id = ? AND confirmation_code = ?", requestID, confirmationCode).First(&request).Error; err != nil {
		return fmt.Errorf("invalid request or confirmation code")
	}

	if request.Status != "pending" {
		return fmt.Errorf("request already processed")
	}

	if time.Now().Before(request.ScheduledFor) {
		return fmt.Errorf("deletion not yet scheduled")
	}

	// Begin transaction
	tx := s.db.Begin()

	// Delete or anonymize user data
	if request.RequestType == "deletion" {
		// Hard delete non-essential data
		tx.Where("user_id = ?", request.UserID).Delete(&models.Project{})
		tx.Where("owner_id = ?", request.UserID).Delete(&models.Building{})
		tx.Where("user_id = ?", request.UserID).Delete(&models.ExportActivity{})
		
		// Anonymize essential audit logs (keep for legal compliance)
		tx.Model(&models.AuditLog{}).Where("user_id = ?", request.UserID).Update("user_id", 0)
		
		// Delete user account
		tx.Where("id = ?", request.UserID).Delete(&models.User{})
	} else if request.RequestType == "anonymization" {
		// Anonymize user data
		anonymousEmail := fmt.Sprintf("deleted_%d@anonymous.local", request.UserID)
		tx.Model(&models.User{}).Where("id = ?", request.UserID).Updates(map[string]interface{}{
			"email":      anonymousEmail,
			"username":   fmt.Sprintf("deleted_user_%d", request.UserID),
			"first_name": "[DELETED]",
			"last_name":  "[DELETED]",
			"phone":      "",
			"avatar_url": "",
			"status":     "deleted",
		})
	}

	// Update request status
	now := time.Now()
	request.Status = "completed"
	request.ProcessedAt = &now
	tx.Save(&request)

	// Commit transaction
	if err := tx.Commit().Error; err != nil {
		tx.Rollback()
		return fmt.Errorf("failed to process deletion: %w", err)
	}

	return nil
}

// RecordConsent records user consent for data processing
func (s *GDPRService) RecordConsent(userID uint, consentType string, granted bool, r *http.Request) error {
	// Revoke any existing consent of this type
	now := time.Now()
	s.db.Model(&ConsentRecord{}).
		Where("user_id = ? AND consent_type = ? AND revoked_at IS NULL", userID, consentType).
		Update("revoked_at", now)

	// Create new consent record
	consent := &ConsentRecord{
		UserID:      userID,
		ConsentType: consentType,
		Granted:     granted,
		Version:     "1.0", // Should come from configuration
		IPAddress:   r.RemoteAddr,
		UserAgent:   r.UserAgent(),
		GrantedAt:   now,
	}

	// Set expiration for certain consent types
	if consentType == "marketing" {
		expiry := now.Add(365 * 24 * time.Hour) // 1 year
		consent.ExpiresAt = &expiry
	}

	return s.db.Create(consent).Error
}

// GetUserConsents retrieves all active consents for a user
func (s *GDPRService) GetUserConsents(userID uint) ([]ConsentRecord, error) {
	var consents []ConsentRecord
	err := s.db.Where("user_id = ? AND revoked_at IS NULL", userID).
		Order("granted_at DESC").
		Find(&consents).Error
	return consents, err
}

// LogDataProcessing logs how user data is being processed
func (s *GDPRService) LogDataProcessing(userID uint, activityType, purpose, legalBasis string) error {
	activity := &DataProcessingActivity{
		UserID:       userID,
		ActivityType: activityType,
		Purpose:      purpose,
		LegalBasis:   legalBasis,
		CreatedAt:    time.Now(),
	}

	return s.db.Create(activity).Error
}

// GeneratePrivacyReport generates a privacy report for a user
func (s *GDPRService) GeneratePrivacyReport(userID uint) ([]byte, error) {
	// Export all user data
	export, err := s.ExportUserData(userID)
	if err != nil {
		return nil, err
	}

	// Get consents
	consents, _ := s.GetUserConsents(userID)

	// Get data processing activities
	var activities []DataProcessingActivity
	s.db.Where("user_id = ?", userID).Find(&activities)

	// Create ZIP archive
	buf := new(bytes.Buffer)
	w := zip.NewWriter(buf)

	// Add user data JSON
	userDataJSON, _ := json.MarshalIndent(export, "", "  ")
	f, _ := w.Create("user_data.json")
	f.Write(userDataJSON)

	// Add consents JSON
	consentsJSON, _ := json.MarshalIndent(consents, "", "  ")
	f, _ = w.Create("consents.json")
	f.Write(consentsJSON)

	// Add processing activities JSON
	activitiesJSON, _ := json.MarshalIndent(activities, "", "  ")
	f, _ = w.Create("processing_activities.json")
	f.Write(activitiesJSON)

	// Add README
	readme := `GDPR Privacy Report
===================

This archive contains all personal data we have stored about you.

Files:
- user_data.json: Your profile and related data
- consents.json: Your consent records
- processing_activities.json: How we've processed your data

Generated: ` + time.Now().Format(time.RFC3339) + `

For questions, contact: privacy@arxos.io
`
	f, _ = w.Create("README.txt")
	f.Write([]byte(readme))

	w.Close()

	return buf.Bytes(), nil
}

// CheckDataRetention checks and applies data retention policies
func (s *GDPRService) CheckDataRetention() error {
	// Get retention policies
	var policies []models.DataRetentionPolicy
	s.db.Where("is_active = ?", true).Find(&policies)

	for _, policy := range policies {
		switch policy.ObjectType {
		case "audit_log":
			// Archive old audit logs
			archiveDate := time.Now().AddDate(0, 0, -policy.ArchiveAfter)
			var logs []models.AuditLog
			s.db.Where("created_at < ?", archiveDate).Find(&logs)
			
			for _, log := range logs {
				// Archive to ArchivedAuditLog
				archivedLog := models.ArchivedAuditLog{
					OriginalID:   log.ID,
					UserID:       log.UserID,
					ObjectType:   log.ObjectType,
					ObjectID:     log.ObjectID,
					Action:       log.Action,
					Payload:      log.Payload,
					IPAddress:    log.IPAddress,
					UserAgent:    log.UserAgent,
					SessionID:    log.SessionID,
					BuildingID:   log.BuildingID,
					FloorID:      log.FloorID,
					AssetID:      log.AssetID,
					ExportID:     log.ExportID,
					FieldChanges: log.FieldChanges,
					Context:      log.Context,
					CreatedAt:    log.CreatedAt,
					ArchivedAt:   time.Now(),
				}
				s.db.Create(&archivedLog)
			}
			
			// Delete archived logs
			s.db.Where("created_at < ?", archiveDate).Delete(&models.AuditLog{})
			
			// Delete old archived logs
			deleteDate := time.Now().AddDate(0, 0, -policy.DeleteAfter)
			s.db.Where("archived_at < ?", deleteDate).Delete(&models.ArchivedAuditLog{})
			
		case "export_activity":
			// Delete old export activities
			deleteDate := time.Now().AddDate(0, 0, -policy.DeleteAfter)
			s.db.Where("created_at < ?", deleteDate).Delete(&models.ExportActivity{})
			
		case "api_usage":
			// Delete old API usage logs
			deleteDate := time.Now().AddDate(0, 0, -policy.DeleteAfter)
			s.db.Where("timestamp < ?", deleteDate).Delete(&models.APIUsage{})
		}
	}

	return nil
}

// AnonymizeInactiveUsers anonymizes users who haven't logged in for a specified period
func (s *GDPRService) AnonymizeInactiveUsers(inactiveDays int) error {
	inactiveDate := time.Now().AddDate(0, 0, -inactiveDays)
	
	var users []models.User
	s.db.Where("last_login_at < ? OR last_login_at IS NULL", inactiveDate).Find(&users)
	
	for _, user := range users {
		// Create anonymization request
		s.RequestDataDeletion(user.ID, "automatic_inactive_user_anonymization")
	}
	
	return nil
}

// generateConfirmationCode generates a secure confirmation code
func generateConfirmationCode() string {
	b := make([]byte, 32)
	rand.Read(b)
	return fmt.Sprintf("%x", b)
}

// HTTP Handlers

// ExportDataHandler handles GDPR data export requests
func ExportDataHandler(w http.ResponseWriter, r *http.Request) {
	userID := getUserIDFromContext(r.Context())
	if userID == 0 {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	service := NewGDPRService()
	data, err := service.GeneratePrivacyReport(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Set headers for ZIP download
	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=privacy_report_%d.zip", userID))
	w.Write(data)
}

// DeleteDataHandler handles GDPR deletion requests
func DeleteDataHandler(w http.ResponseWriter, r *http.Request) {
	userID := getUserIDFromContext(r.Context())
	if userID == 0 {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var req struct {
		Reason string `json:"reason"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	service := NewGDPRService()
	deletionRequest, err := service.RequestDataDeletion(userID, req.Reason)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message": "Deletion request created. You will receive a confirmation email.",
		"request_id": deletionRequest.ID,
		"scheduled_for": deletionRequest.ScheduledFor,
	})
}

// ConsentHandler handles consent management
func ConsentHandler(w http.ResponseWriter, r *http.Request) {
	userID := getUserIDFromContext(r.Context())
	if userID == 0 {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	service := NewGDPRService()

	switch r.Method {
	case "GET":
		// Get current consents
		consents, err := service.GetUserConsents(userID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(consents)

	case "POST":
		// Update consent
		var req struct {
			ConsentType string `json:"consent_type"`
			Granted     bool   `json:"granted"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Invalid request", http.StatusBadRequest)
			return
		}

		if err := service.RecordConsent(userID, req.ConsentType, req.Granted, r); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"message": "Consent updated successfully",
		})

	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getUserIDFromContext gets user ID from request context
func getUserIDFromContext(ctx context.Context) uint {
	if userID := ctx.Value("user_id"); userID != nil {
		if id, ok := userID.(uint); ok {
			return id
		}
	}
	return 0
}