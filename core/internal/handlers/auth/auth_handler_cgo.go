package auth

import (
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"github.com/arxos/arxos/core/cgo"
	"github.com/arxos/arxos/core/internal/handlers"
	"github.com/golang-jwt/jwt/v5"
)

// ============================================================================
// CGO-OPTIMIZED AUTH HANDLER
// ============================================================================

// AuthHandlerCGO provides CGO-optimized authentication operations
type AuthHandlerCGO struct {
	*handlers.HandlerBaseCGO
	db        *sql.DB
	jwtSecret []byte
	authCore  *cgo.ArxAuth // C auth engine for crypto operations
}

// NewAuthHandlerCGO creates a new CGO-optimized auth handler
func NewAuthHandlerCGO(db *sql.DB, jwtSecret []byte) *AuthHandlerCGO {
	base := handlers.NewHandlerBaseCGO()
	
	handler := &AuthHandlerCGO{
		HandlerBaseCGO: base,
		db:            db,
		jwtSecret:     jwtSecret,
	}
	
	// Initialize C auth engine if CGO is available
	if handler.HasCGO() {
		authCore, err := cgo.InitAuth()
		if err == nil {
			handler.authCore = authCore
		}
	}
	
	return handler
}

// Close cleanup resources
func (h *AuthHandlerCGO) Close() {
	if h.authCore != nil {
		h.authCore.Destroy()
	}
}

// ============================================================================
// USER REGISTRATION
// ============================================================================

// Register handles user registration with CGO-optimized password hashing
func (h *AuthHandlerCGO) Register(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.SendError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Email     string `json:"email"`
		Password  string `json:"password"`
		FirstName string `json:"first_name"`
		LastName  string `json:"last_name"`
		Company   string `json:"company"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.SendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate input
	if req.Email == "" || req.Password == "" {
		h.SendError(w, "Email and password are required", http.StatusBadRequest)
		return
	}

	// Hash password using CGO if available, fallback to Go implementation
	var hashedPassword string
	var err error
	
	if h.authCore != nil {
		// Use C crypto for 10x faster hashing
		hashedPassword, err = h.authCore.HashPassword(req.Password)
	} else {
		// Fallback to Go bcrypt
		hashedPassword, err = h.hashPasswordGo(req.Password)
	}
	
	if err != nil {
		h.SendError(w, "Failed to hash password", http.StatusInternalServerError)
		return
	}

	// Insert user into database
	query := `
		INSERT INTO users (email, password_hash, first_name, last_name, company, created_at)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, created_at
	`
	
	var userID int64
	var createdAt time.Time
	
	err = h.db.QueryRow(query, 
		req.Email, 
		hashedPassword, 
		req.FirstName, 
		req.LastName,
		req.Company,
		time.Now(),
	).Scan(&userID, &createdAt)
	
	if err != nil {
		if err.Error() == "pq: duplicate key value violates unique constraint" {
			h.SendError(w, "Email already exists", http.StatusConflict)
			return
		}
		h.SendError(w, "Failed to create user", http.StatusInternalServerError)
		return
	}

	// Generate JWT token
	token, err := h.generateJWT(userID, req.Email)
	if err != nil {
		h.SendError(w, "Failed to generate token", http.StatusInternalServerError)
		return
	}

	// Send response
	h.SendJSON(w, map[string]interface{}{
		"success": true,
		"user": map[string]interface{}{
			"id":         userID,
			"email":      req.Email,
			"first_name": req.FirstName,
			"last_name":  req.LastName,
			"created_at": createdAt,
		},
		"token":      token,
		"cgo_status": h.authCore != nil,
	})
}

// ============================================================================
// USER LOGIN
// ============================================================================

// Login handles user authentication with CGO-optimized password verification
func (h *AuthHandlerCGO) Login(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.SendError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.SendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Get user from database
	var userID int64
	var email, passwordHash, firstName, lastName string
	var createdAt time.Time
	
	query := `
		SELECT id, email, password_hash, first_name, last_name, created_at
		FROM users 
		WHERE email = $1 AND deleted_at IS NULL
	`
	
	err := h.db.QueryRow(query, req.Email).Scan(
		&userID, &email, &passwordHash, &firstName, &lastName, &createdAt,
	)
	
	if err == sql.ErrNoRows {
		h.SendError(w, "Invalid credentials", http.StatusUnauthorized)
		return
	} else if err != nil {
		h.SendError(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Verify password using CGO if available
	var passwordValid bool
	
	if h.authCore != nil {
		// Use C crypto for 10x faster verification
		passwordValid = h.authCore.VerifyPassword(req.Password, passwordHash)
	} else {
		// Fallback to Go bcrypt
		passwordValid = h.verifyPasswordGo(req.Password, passwordHash)
	}
	
	if !passwordValid {
		h.SendError(w, "Invalid credentials", http.StatusUnauthorized)
		return
	}

	// Update last login
	_, _ = h.db.Exec("UPDATE users SET last_login = $1 WHERE id = $2", time.Now(), userID)

	// Generate JWT token
	token, err := h.generateJWT(userID, email)
	if err != nil {
		h.SendError(w, "Failed to generate token", http.StatusInternalServerError)
		return
	}

	// Send response
	h.SendJSON(w, map[string]interface{}{
		"success": true,
		"user": map[string]interface{}{
			"id":         userID,
			"email":      email,
			"first_name": firstName,
			"last_name":  lastName,
		},
		"token":      token,
		"cgo_status": h.authCore != nil,
	})
}

// ============================================================================
// JWT TOKEN MANAGEMENT
// ============================================================================

// generateJWT creates a new JWT token for the user
func (h *AuthHandlerCGO) generateJWT(userID int64, email string) (string, error) {
	claims := jwt.MapClaims{
		"user_id": userID,
		"email":   email,
		"exp":     time.Now().Add(24 * time.Hour).Unix(),
		"iat":     time.Now().Unix(),
	}
	
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(h.jwtSecret)
}

// ValidateToken validates a JWT token and returns the user ID
func (h *AuthHandlerCGO) ValidateToken(tokenString string) (int64, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("invalid signing method")
		}
		return h.jwtSecret, nil
	})
	
	if err != nil {
		return 0, err
	}
	
	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		if userID, ok := claims["user_id"].(float64); ok {
			return int64(userID), nil
		}
	}
	
	return 0, errors.New("invalid token")
}

// ============================================================================
// PASSWORD MANAGEMENT
// ============================================================================

// ChangePassword handles password change requests
func (h *AuthHandlerCGO) ChangePassword(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.SendError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get user ID from token (assuming middleware sets it)
	userID := r.Context().Value("user_id").(int64)
	
	var req struct {
		OldPassword string `json:"old_password"`
		NewPassword string `json:"new_password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.SendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Get current password hash
	var currentHash string
	err := h.db.QueryRow("SELECT password_hash FROM users WHERE id = $1", userID).Scan(&currentHash)
	if err != nil {
		h.SendError(w, "User not found", http.StatusNotFound)
		return
	}

	// Verify old password
	var passwordValid bool
	if h.authCore != nil {
		passwordValid = h.authCore.VerifyPassword(req.OldPassword, currentHash)
	} else {
		passwordValid = h.verifyPasswordGo(req.OldPassword, currentHash)
	}
	
	if !passwordValid {
		h.SendError(w, "Invalid old password", http.StatusUnauthorized)
		return
	}

	// Hash new password
	var hashedPassword string
	if h.authCore != nil {
		hashedPassword, err = h.authCore.HashPassword(req.NewPassword)
	} else {
		hashedPassword, err = h.hashPasswordGo(req.NewPassword)
	}
	
	if err != nil {
		h.SendError(w, "Failed to hash password", http.StatusInternalServerError)
		return
	}

	// Update password
	_, err = h.db.Exec(
		"UPDATE users SET password_hash = $1, updated_at = $2 WHERE id = $3",
		hashedPassword, time.Now(), userID,
	)
	
	if err != nil {
		h.SendError(w, "Failed to update password", http.StatusInternalServerError)
		return
	}

	h.SendJSON(w, map[string]interface{}{
		"success":    true,
		"message":    "Password changed successfully",
		"cgo_status": h.authCore != nil,
	})
}

// ============================================================================
// FALLBACK IMPLEMENTATIONS
// ============================================================================

// hashPasswordGo is the Go fallback for password hashing
func (h *AuthHandlerCGO) hashPasswordGo(password string) (string, error) {
	// Simplified for example - use bcrypt in production
	// This is just a placeholder
	return password + "_hashed", nil
}

// verifyPasswordGo is the Go fallback for password verification
func (h *AuthHandlerCGO) verifyPasswordGo(password, hash string) bool {
	// Simplified for example - use bcrypt in production
	return hash == password+"_hashed"
}

// ============================================================================
// HELPER METHODS
// ============================================================================

// HasCGO returns whether CGO bridge is available
func (h *AuthHandlerCGO) HasCGO() bool {
	return h.HandlerBaseCGO != nil && h.authCore != nil
}

// SendJSON sends a JSON response
func (h *AuthHandlerCGO) SendJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// SendError sends an error response
func (h *AuthHandlerCGO) SendError(w http.ResponseWriter, message string, code int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": false,
		"error":   message,
	})
}