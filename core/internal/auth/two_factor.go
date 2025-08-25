package auth

import (
	"context"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/arxos/arxos/core/internal/db"
	"github.com/arxos/arxos/core/internal/models"
	"github.com/pquerna/otp/totp"
	qrcode "github.com/skip2/go-qrcode"
	"gorm.io/gorm"
)

// TwoFactorService handles 2FA operations
type TwoFactorService struct {
	db     *gorm.DB
	issuer string
}

// AuthManager handles authentication operations
type AuthManager struct {
	db *gorm.DB
}

// NewTwoFactorService creates a new 2FA service
func NewTwoFactorService() *TwoFactorService {
	return &TwoFactorService{
		db:     db.GormDB,
		issuer: "ARXOS",
	}
}

// TwoFactorSetup contains 2FA setup information
type TwoFactorSetup struct {
	Secret       string   `json:"secret"`
	QRCode       string   `json:"qr_code"`
	BackupCodes  []string `json:"backup_codes"`
	ManualEntry  string   `json:"manual_entry"`
}

// Generate2FASetup creates a new 2FA setup for a user
func (s *TwoFactorService) Generate2FASetup(userID uint, email string) (*TwoFactorSetup, error) {
	// Generate secret key
	key, err := totp.Generate(totp.GenerateOpts{
		Issuer:      s.issuer,
		AccountName: email,
		Secret:      nil, // Will generate random secret
	})
	if err != nil {
		return nil, fmt.Errorf("failed to generate TOTP key: %w", err)
	}

	// Generate QR code
	qrBytes, err := qrcode.Encode(key.URL(), qrcode.Medium, 256)
	if err != nil {
		return nil, fmt.Errorf("failed to generate QR code: %w", err)
	}

	// Encode QR code as base64 for embedding in HTML
	qrBase64 := base64.StdEncoding.EncodeToString(qrBytes)

	// Generate backup codes
	backupCodes := s.generateBackupCodes(8)

	// Store setup in database (encrypted)
	setup := &models.TwoFactorAuth{
		UserID:      userID,
		Secret:      s.encryptSecret(key.Secret()),
		BackupCodes: s.hashBackupCodes(backupCodes),
		IsEnabled:   false, // Not enabled until verified
		CreatedAt:   time.Now(),
	}

	if err := s.db.Create(setup).Error; err != nil {
		return nil, fmt.Errorf("failed to save 2FA setup: %w", err)
	}

	return &TwoFactorSetup{
		Secret:      key.Secret(),
		QRCode:      "data:image/png;base64," + qrBase64,
		BackupCodes: backupCodes,
		ManualEntry: key.Secret(),
	}, nil
}

// Enable2FA verifies and enables 2FA for a user
func (s *TwoFactorService) Enable2FA(userID uint, token string) error {
	// Get user's 2FA setup
	var setup models.TwoFactorAuth
	if err := s.db.Where("user_id = ?", userID).First(&setup).Error; err != nil {
		return fmt.Errorf("2FA not set up for user")
	}

	// Verify token
	secret := s.decryptSecret(setup.Secret)
	if !totp.Validate(token, secret) {
		return fmt.Errorf("invalid verification code")
	}

	// Enable 2FA
	setup.IsEnabled = true
	setup.EnabledAt = &time.Time{}
	*setup.EnabledAt = time.Now()

	if err := s.db.Save(&setup).Error; err != nil {
		return fmt.Errorf("failed to enable 2FA: %w", err)
	}

	// Log security event
	s.logSecurityEvent(userID, "2FA_ENABLED", nil)

	return nil
}

// Verify2FA checks a TOTP token
func (s *TwoFactorService) Verify2FA(userID uint, token string) (bool, error) {
	// Get user's 2FA setup
	var setup models.TwoFactorAuth
	if err := s.db.Where("user_id = ? AND is_enabled = ?", userID, true).First(&setup).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			return false, nil // 2FA not enabled
		}
		return false, err
	}

	// Check if it's a backup code
	if s.verifyBackupCode(&setup, token) {
		// Save updated backup codes
		s.db.Save(&setup)
		s.logSecurityEvent(userID, "2FA_BACKUP_CODE_USED", map[string]interface{}{
			"remaining_codes": len(setup.BackupCodes),
		})
		return true, nil
	}

	// Verify TOTP token
	secret := s.decryptSecret(setup.Secret)
	valid := totp.Validate(token, secret)

	if valid {
		// Update last used time
		setup.LastUsedAt = &time.Time{}
		*setup.LastUsedAt = time.Now()
		s.db.Save(&setup)
	} else {
		// Log failed attempt
		s.logSecurityEvent(userID, "2FA_FAILED", nil)
	}

	return valid, nil
}

// Disable2FA removes 2FA for a user
func (s *TwoFactorService) Disable2FA(userID uint, password string) error {
	// Verify user's password first
	var user models.User
	if err := s.db.Where("id = ?", userID).First(&user).Error; err != nil {
		return fmt.Errorf("user not found")
	}

	if !checkPasswordHash(password, user.Password) {
		return fmt.Errorf("invalid password")
	}

	// Delete 2FA setup
	if err := s.db.Where("user_id = ?", userID).Delete(&models.TwoFactorAuth{}).Error; err != nil {
		return fmt.Errorf("failed to disable 2FA: %w", err)
	}

	// Log security event
	s.logSecurityEvent(userID, "2FA_DISABLED", nil)

	return nil
}

// RegenerateBackupCodes creates new backup codes
func (s *TwoFactorService) RegenerateBackupCodes(userID uint) ([]string, error) {
	var setup models.TwoFactorAuth
	if err := s.db.Where("user_id = ?", userID).First(&setup).Error; err != nil {
		return nil, fmt.Errorf("2FA not set up for user")
	}

	// Generate new backup codes
	backupCodes := s.generateBackupCodes(8)
	setup.BackupCodes = s.hashBackupCodes(backupCodes)

	if err := s.db.Save(&setup).Error; err != nil {
		return nil, fmt.Errorf("failed to save backup codes: %w", err)
	}

	// Log security event
	s.logSecurityEvent(userID, "2FA_BACKUP_CODES_REGENERATED", nil)

	return backupCodes, nil
}

// Helper functions

func (s *TwoFactorService) generateBackupCodes(count int) []string {
	codes := make([]string, count)
	for i := 0; i < count; i++ {
		b := make([]byte, 4)
		rand.Read(b)
		codes[i] = fmt.Sprintf("%08x", b)
	}
	return codes
}

func (s *TwoFactorService) hashBackupCodes(codes []string) []byte {
	hashed := make([]string, len(codes))
	for i, code := range codes {
		hash := sha256.Sum256([]byte(code))
		hashed[i] = base64.StdEncoding.EncodeToString(hash[:])
	}
	data, _ := json.Marshal(hashed)
	return data
}

func (s *TwoFactorService) verifyBackupCode(setup *models.TwoFactorAuth, code string) bool {
	var hashedCodes []string
	if err := json.Unmarshal(setup.BackupCodes, &hashedCodes); err != nil {
		return false
	}

	codeHash := sha256.Sum256([]byte(code))
	codeHashStr := base64.StdEncoding.EncodeToString(codeHash[:])

	for i, hashed := range hashedCodes {
		if subtle.ConstantTimeCompare([]byte(hashed), []byte(codeHashStr)) == 1 {
			// Remove used code
			hashedCodes = append(hashedCodes[:i], hashedCodes[i+1:]...)
			setup.BackupCodes, _ = json.Marshal(hashedCodes)
			return true
		}
	}

	return false
}

func (s *TwoFactorService) encryptSecret(secret string) string {
	// In production, use proper encryption with key management
	// This is a simplified version
	key := []byte(getEncryptionKey())
	h := hmac.New(sha256.New, key)
	h.Write([]byte(secret))
	return base64.StdEncoding.EncodeToString(h.Sum(nil))
}

func (s *TwoFactorService) decryptSecret(encrypted string) string {
	// In production, use proper decryption
	// This is a simplified version that should match the encryption
	data, _ := base64.StdEncoding.DecodeString(encrypted)
	return string(data)
}

func (s *TwoFactorService) logSecurityEvent(userID uint, eventType string, details map[string]interface{}) {
	event := models.SecurityLog{
		UserID:    userID,
		EventType: eventType,
		Details:   details,
		Timestamp: time.Now(),
	}
	s.db.Create(&event)
}

// HTTP Handlers for 2FA

// Setup2FAHandler initiates 2FA setup
func (am *AuthManager) Setup2FAHandler(w http.ResponseWriter, r *http.Request) {
	userID := getUserIDFromContext(r.Context())
	if userID == 0 {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Get user email
	var user models.User
	if err := db.GormDB.Where("id = ?", userID).First(&user).Error; err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	// Check if user is admin or has 2FA required
	if !user.IsAdmin && !user.Requires2FA {
		http.Error(w, "2FA not required for this account", http.StatusForbidden)
		return
	}

	// Generate 2FA setup
	twoFA := NewTwoFactorService()
	setup, err := twoFA.Generate2FASetup(userID, user.Email)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Return setup information
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(setup)
}

// Enable2FAHandler verifies and enables 2FA
func (am *AuthManager) Enable2FAHandler(w http.ResponseWriter, r *http.Request) {
	userID := getUserIDFromContext(r.Context())
	if userID == 0 {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var req struct {
		Token string `json:"token"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	twoFA := NewTwoFactorService()
	if err := twoFA.Enable2FA(userID, req.Token); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"message": "2FA enabled successfully",
	})
}

// Verify2FAHandler checks 2FA token during login
func (am *AuthManager) Verify2FAHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		UserID uint   `json:"user_id"`
		Token  string `json:"token"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	twoFA := NewTwoFactorService()
	valid, err := twoFA.Verify2FA(req.UserID, req.Token)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if !valid {
		http.Error(w, "Invalid 2FA token", http.StatusUnauthorized)
		return
	}

	// Generate auth token after successful 2FA
	token, err := am.generateToken(req.UserID)
	if err != nil {
		http.Error(w, "Failed to generate token", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"token": token,
		"message": "2FA verification successful",
	})
}

// getEncryptionKey returns the encryption key for 2FA secrets
func getEncryptionKey() string {
	// In production, use proper key management (AWS KMS, HashiCorp Vault, etc.)
	key := os.Getenv("TWO_FACTOR_ENCRYPTION_KEY")
	if key == "" {
		// Generate a key if not set (development only)
		key = "development-key-do-not-use-in-production"
	}
	return key
}

// checkPasswordHash checks if password matches hash
func checkPasswordHash(password, hash string) bool {
	// This should use bcrypt or similar
	// Placeholder implementation
	return password == hash
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

// generateToken generates JWT token for user
func (am *AuthManager) generateToken(userID uint) (string, error) {
	// Placeholder implementation
	// In production, use proper JWT library
	return fmt.Sprintf("token_%d_%d", userID, time.Now().Unix()), nil
}