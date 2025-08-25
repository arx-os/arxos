package cgo

import (
	"errors"
	"time"
	"unsafe"
)

// ============================================================================
// AUTHENTICATION TYPES
// ============================================================================

// ArxFileFormat represents supported file formats for ingestion
type ArxFileFormat int

const (
	ArxFormatPDF ArxFileFormat = iota
	ArxFormatIFC
	ArxFormatDWG
	ArxFormatImage
	ArxFormatExcel
	ArxFormatLiDAR
	ArxFormatUnknown = 99
)

// ArxAuthAlgorithm represents JWT signing algorithms
type ArxAuthAlgorithm int

const (
	ArxAuthHS256 ArxAuthAlgorithm = iota
	ArxAuthHS384
	ArxAuthHS512
)

// ArxJWTClaims represents JWT claims for token creation
type ArxJWTClaims struct {
	Issuer       string    `json:"issuer"`
	Subject      string    `json:"subject"`
	Audience     string    `json:"audience"`
	IssuedAt     time.Time `json:"issued_at"`
	NotBefore    time.Time `json:"not_before"`
	ExpiresAt    time.Time `json:"expires_at"`
	JWTID        string    `json:"jwt_id"`
	Type         string    `json:"type"`
	CustomClaims string    `json:"custom_claims"`
}

// ArxJWTToken represents a JWT token structure
type ArxJWTToken struct {
	Header    string        `json:"header"`
	Payload   string        `json:"payload"`
	Signature string        `json:"signature"`
	RawToken  string        `json:"raw_token"`
	Claims    *ArxJWTClaims `json:"claims"`
	IsValid   bool          `json:"is_valid"`
}

// ArxUser represents user authentication data
type ArxUser struct {
	UserID            uint32    `json:"user_id"`
	Username          string    `json:"username"`
	Email             string    `json:"email"`
	PasswordHash      string    `json:"password_hash"`
	IsAdmin           bool      `json:"is_admin"`
	IsActive          bool      `json:"is_active"`
	CreatedAt         time.Time `json:"created_at"`
	LastLogin         time.Time `json:"last_login"`
	PasswordChangedAt time.Time `json:"password_changed_at"`
}

// ArxRefreshToken represents refresh token data
type ArxRefreshToken struct {
	TokenHash     string     `json:"token_hash"`
	UserID        uint32     `json:"user_id"`
	ExpiresAt     time.Time  `json:"expires_at"`
	CreatedAt     time.Time  `json:"created_at"`
	LastUsedAt    *time.Time `json:"last_used_at"`
	UserAgent     string     `json:"user_agent"`
	IPAddress     string     `json:"ip_address"`
	IsRevoked     bool       `json:"is_revoked"`
	RevokedAt     *time.Time `json:"revoked_at"`
	RevokedReason string     `json:"revoked_reason"`
}

// ArxTwoFactorAuth represents two-factor authentication data
type ArxTwoFactorAuth struct {
	UserID          uint32     `json:"user_id"`
	Secret          string     `json:"secret"`
	BackupCodesHash string     `json:"backup_codes_hash"`
	IsEnabled       bool       `json:"is_enabled"`
	CreatedAt       time.Time  `json:"created_at"`
	LastUsedAt      *time.Time `json:"last_used_at"`
}

// ArxAuthOptions represents authentication configuration options
type ArxAuthOptions struct {
	JWTSecret        string           `json:"jwt_secret"`
	JWTAlgorithm     ArxAuthAlgorithm `json:"jwt_algorithm"`
	PasswordCost     int              `json:"password_cost"`
	TokenTTL         int              `json:"token_ttl"`
	RefreshTTL       int              `json:"refresh_ttl"`
	MaxRefreshTokens int              `json:"max_refresh_tokens"`
	Require2FA       bool             `json:"require_2fa"`
	Issuer           string           `json:"issuer"`
}

// ArxAuthResult represents authentication operation results
type ArxAuthResult struct {
	Success      bool      `json:"success"`
	ErrorMessage string    `json:"error_message"`
	Token        string    `json:"token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
	User         *ArxUser  `json:"user"`
}

// ============================================================================
// CONVERSION FUNCTIONS
// ============================================================================

// toCArxJWTClaims converts Go JWT claims to C structure
func (claims *ArxJWTClaims) toCArxJWTClaims() unsafe.Pointer {
	if claims == nil {
		return nil
	}

	// Create C structure
	cClaims := C.malloc(C.sizeof_ArxJWTClaims)
	if cClaims == nil {
		return nil
	}

	// Convert fields
	cClaimsStruct := (*C.ArxJWTClaims)(cClaims)

	if claims.Issuer != "" {
		cClaimsStruct.issuer = C.CString(claims.Issuer)
	}
	if claims.Subject != "" {
		cClaimsStruct.subject = C.CString(claims.Subject)
	}
	if claims.Audience != "" {
		cClaimsStruct.audience = C.CString(claims.Audience)
	}
	if claims.JWTID != "" {
		cClaimsStruct.jwt_id = C.CString(claims.JWTID)
	}
	if claims.Type != "" {
		cClaimsStruct.type_ = C.CString(claims.Type)
	}
	if claims.CustomClaims != "" {
		cClaimsStruct.custom_claims = C.CString(claims.CustomClaims)
	}

	cClaimsStruct.issued_at = C.time_t(claims.IssuedAt.Unix())
	cClaimsStruct.not_before = C.time_t(claims.NotBefore.Unix())
	cClaimsStruct.expires_at = C.time_t(claims.ExpiresAt.Unix())

	return cClaims
}

// toCArxAuthOptions converts Go auth options to C structure
func (opts *ArxAuthOptions) toCArxAuthOptions() unsafe.Pointer {
	if opts == nil {
		return nil
	}

	// Create C structure
	cOpts := C.malloc(C.sizeof_ArxAuthOptions)
	if cOpts == nil {
		return nil
	}

	// Convert fields
	cOptsStruct := (*C.ArxAuthOptions)(cOpts)

	if opts.JWTSecret != "" {
		cOptsStruct.jwt_secret = C.CString(opts.JWTSecret)
	}
	if opts.Issuer != "" {
		cOptsStruct.issuer = C.CString(opts.Issuer)
	}

	cOptsStruct.jwt_algorithm = C.int(opts.JWTAlgorithm)
	cOptsStruct.password_cost = C.int(opts.PasswordCost)
	cOptsStruct.token_ttl = C.int(opts.TokenTTL)
	cOptsStruct.refresh_ttl = C.int(opts.RefreshTTL)
	cOptsStruct.max_refresh_tokens = C.int(opts.MaxRefreshTokens)
	cOptsStruct.require_2fa = C.bool(opts.Require2FA)

	return cOpts
}

// fromCArxUser converts C user structure to Go
func fromCArxUser(cUser unsafe.Pointer) *ArxUser {
	if cUser == nil {
		return nil
	}

	cUserStruct := (*C.ArxUser)(cUser)

	user := &ArxUser{
		UserID:   uint32(cUserStruct.user_id),
		Username: C.GoString(cUserStruct.username),
		Email:    C.GoString(cUserStruct.email),
		IsAdmin:  bool(cUserStruct.is_admin),
		IsActive: bool(cUserStruct.is_active),
	}

	// Convert time fields
	if cUserStruct.created_at > 0 {
		user.CreatedAt = time.Unix(int64(cUserStruct.created_at), 0)
	}
	if cUserStruct.last_login > 0 {
		user.LastLogin = time.Unix(int64(cUserStruct.last_login), 0)
	}
	if cUserStruct.password_changed_at > 0 {
		user.PasswordChangedAt = time.Unix(int64(cUserStruct.password_changed_at), 0)
	}

	return user
}

// fromCArxJWTToken converts C JWT token structure to Go
func fromCArxJWTToken(cToken unsafe.Pointer) *ArxJWTToken {
	if cToken == nil {
		return nil
	}

	cTokenStruct := (*C.ArxJWTToken)(cToken)

	token := &ArxJWTToken{
		Header:    C.GoString(cTokenStruct.header),
		Payload:   C.GoString(cTokenStruct.payload),
		Signature: C.GoString(cTokenStruct.signature),
		RawToken:  C.GoString(cTokenStruct.raw_token),
		IsValid:   bool(cTokenStruct.is_valid),
	}

	// Convert claims if present
	if cTokenStruct.claims != nil {
		token.Claims = fromCArxJWTClaims(cTokenStruct.claims)
	}

	return token
}

// fromCArxJWTClaims converts C JWT claims structure to Go
func fromCArxJWTClaims(cClaims unsafe.Pointer) *ArxJWTClaims {
	if cClaims == nil {
		return nil
	}

	cClaimsStruct := (*C.ArxJWTClaims)(cClaims)

	claims := &ArxJWTClaims{}

	if cClaimsStruct.issuer != nil {
		claims.Issuer = C.GoString(cClaimsStruct.issuer)
	}
	if cClaimsStruct.subject != nil {
		claims.Subject = C.GoString(cClaimsStruct.subject)
	}
	if cClaimsStruct.audience != nil {
		claims.Audience = C.GoString(cClaimsStruct.audience)
	}
	if cClaimsStruct.jwt_id != nil {
		claims.JWTID = C.GoString(cClaimsStruct.jwt_id)
	}
	if cClaimsStruct.type_ != nil {
		claims.Type = C.GoString(cClaimsStruct.type_)
	}
	if cClaimsStruct.custom_claims != nil {
		claims.CustomClaims = C.GoString(cClaimsStruct.custom_claims)
	}

	// Convert time fields
	if cClaimsStruct.issued_at > 0 {
		claims.IssuedAt = time.Unix(int64(cClaimsStruct.issued_at), 0)
	}
	if cClaimsStruct.not_before > 0 {
		claims.NotBefore = time.Unix(int64(cClaimsStruct.not_before), 0)
	}
	if cClaimsStruct.expires_at > 0 {
		claims.ExpiresAt = time.Unix(int64(cClaimsStruct.expires_at), 0)
	}

	return claims
}

// fromCArxAuthResult converts C auth result structure to Go
func fromCArxAuthResult(cResult unsafe.Pointer) *ArxAuthResult {
	if cResult == nil {
		return nil
	}

	cResultStruct := (*C.ArxAuthResult)(cResult)

	result := &ArxAuthResult{
		Success:      bool(cResultStruct.success),
		ErrorMessage: C.GoString(cResultStruct.error_message),
		Token:        C.GoString(cResultStruct.token),
		RefreshToken: C.GoString(cResultStruct.refresh_token),
	}

	// Convert time fields
	if cResultStruct.expires_at > 0 {
		result.ExpiresAt = time.Unix(int64(cResultStruct.expires_at), 0)
	}

	// Convert user if present
	if cResultStruct.user != nil {
		result.User = fromCArxUser(cResultStruct.user)
	}

	return result
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// DefaultAuthOptions returns default authentication options
func DefaultAuthOptions() *ArxAuthOptions {
	return &ArxAuthOptions{
		JWTSecret:        "arxos_default_secret",
		JWTAlgorithm:     ArxAuthHS256,
		PasswordCost:     10,
		TokenTTL:         3600,   // 1 hour
		RefreshTTL:       604800, // 7 days
		MaxRefreshTokens: 5,
		Require2FA:       false,
		Issuer:           "ARXOS",
	}
}

// ValidateAuthOptions validates authentication options
func ValidateAuthOptions(opts *ArxAuthOptions) error {
	if opts == nil {
		return errors.New("auth options cannot be nil")
	}

	if opts.JWTSecret == "" {
		return errors.New("JWT secret cannot be empty")
	}

	if opts.PasswordCost < 4 || opts.PasswordCost > 31 {
		return errors.New("password cost must be between 4 and 31")
	}

	if opts.TokenTTL <= 0 {
		return errors.New("token TTL must be positive")
	}

	if opts.RefreshTTL <= 0 {
		return errors.New("refresh TTL must be positive")
	}

	if opts.MaxRefreshTokens <= 0 {
		return errors.New("max refresh tokens must be positive")
	}

	return nil
}
