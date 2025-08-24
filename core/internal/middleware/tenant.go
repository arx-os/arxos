package middleware

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"strings"
	
	"github.com/arxos/arxos/core/internal/db"
	"github.com/golang-jwt/jwt/v4"
)

// TenantContextKey is the context key for tenant information
type TenantContextKey string

const (
	// TenantIDKey is the context key for tenant ID
	TenantIDKey TenantContextKey = "tenant_id"
	// TenantSlugKey is the context key for tenant slug
	TenantSlugKey TenantContextKey = "tenant_slug"
)

// TenantInfo represents tenant information stored in context
type TenantInfo struct {
	ID   string `json:"id"`
	Slug string `json:"slug"`
	Name string `json:"name"`
}

// TenantMiddleware extracts and validates tenant information from requests
func TenantMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		tenantID, err := extractTenantID(r)
		if err != nil {
			// For now, use default tenant if none specified
			tenantID = "00000000-0000-0000-0000-000000000000"
		}
		
		// Set tenant context in database connection
		if err := setDatabaseTenant(tenantID); err != nil {
			http.Error(w, "Failed to set tenant context", http.StatusInternalServerError)
			return
		}
		
		// Add tenant ID to request context
		ctx := context.WithValue(r.Context(), TenantIDKey, tenantID)
		r = r.WithContext(ctx)
		
		next.ServeHTTP(w, r)
	})
}

// extractTenantID extracts tenant ID from the request
func extractTenantID(r *http.Request) (string, error) {
	// Method 1: Check subdomain (e.g., tenant1.arxos.com)
	host := r.Host
	if strings.Contains(host, ".") {
		parts := strings.Split(host, ".")
		if len(parts) > 2 {
			subdomain := parts[0]
			// Look up tenant by subdomain
			tenantID, err := getTenantIDBySlug(subdomain)
			if err == nil {
				return tenantID, nil
			}
		}
	}
	
	// Method 2: Check X-Tenant-ID header
	if tenantID := r.Header.Get("X-Tenant-ID"); tenantID != "" {
		// Validate tenant ID exists
		if validateTenantID(tenantID) {
			return tenantID, nil
		}
	}
	
	// Method 3: Extract from JWT token
	if tenantID := extractTenantFromJWT(r); tenantID != "" {
		return tenantID, nil
	}
	
	// Method 4: Check query parameter (useful for development)
	if tenantID := r.URL.Query().Get("tenant_id"); tenantID != "" {
		if validateTenantID(tenantID) {
			return tenantID, nil
		}
	}
	
	return "", fmt.Errorf("no tenant ID found")
}

// extractTenantFromJWT extracts tenant ID from JWT token
func extractTenantFromJWT(r *http.Request) string {
	// Get token from Authorization header
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return ""
	}
	
	tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
	if tokenStr == authHeader {
		return ""
	}
	
	// Parse token without validation (validation happens in auth middleware)
	token, _ := jwt.Parse(tokenStr, nil)
	if token == nil {
		return ""
	}
	
	// Extract claims
	if claims, ok := token.Claims.(jwt.MapClaims); ok {
		if tenantID, ok := claims["tenant_id"].(string); ok {
			return tenantID
		}
	}
	
	return ""
}

// getTenantIDBySlug looks up tenant ID by subdomain slug
func getTenantIDBySlug(slug string) (string, error) {
	var tenantID string
	err := db.DB.Raw(`
		SELECT id FROM tenants 
		WHERE slug = ? AND status = 'active'
		LIMIT 1
	`, slug).Scan(&tenantID).Error
	
	if err != nil {
		return "", fmt.Errorf("tenant not found: %w", err)
	}
	
	return tenantID, nil
}

// validateTenantID checks if a tenant ID exists and is active
func validateTenantID(tenantID string) bool {
	var count int64
	db.DB.Raw(`
		SELECT COUNT(*) FROM tenants 
		WHERE id = ? AND status = 'active'
	`, tenantID).Scan(&count)
	
	return count > 0
}

// setDatabaseTenant sets the current tenant for row-level security
func setDatabaseTenant(tenantID string) error {
	// Get raw database connection
	sqlDB, err := db.DB.DB()
	if err != nil {
		return fmt.Errorf("failed to get database connection: %w", err)
	}
	
	// Set the tenant context for this connection
	_, err = sqlDB.Exec("SELECT set_config('app.current_tenant', $1, false)", tenantID)
	if err != nil {
		return fmt.Errorf("failed to set tenant context: %w", err)
	}
	
	return nil
}

// GetTenantID retrieves tenant ID from request context
func GetTenantID(ctx context.Context) (string, bool) {
	tenantID, ok := ctx.Value(TenantIDKey).(string)
	return tenantID, ok
}

// GetTenantInfo retrieves full tenant information from database
func GetTenantInfo(tenantID string) (*TenantInfo, error) {
	var info TenantInfo
	err := db.DB.Raw(`
		SELECT id, slug, name 
		FROM tenants 
		WHERE id = ? AND status = 'active'
		LIMIT 1
	`, tenantID).Scan(&info).Error
	
	if err != nil {
		return nil, fmt.Errorf("failed to get tenant info: %w", err)
	}
	
	return &info, nil
}

// RequireTenant ensures a valid tenant is present in the context
func RequireTenant(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		tenantID, ok := GetTenantID(r.Context())
		if !ok || tenantID == "" {
			http.Error(w, "Tenant context required", http.StatusBadRequest)
			return
		}
		
		// Validate tenant is active
		if !validateTenantID(tenantID) {
			http.Error(w, "Invalid or inactive tenant", http.StatusForbidden)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

// TenantScopedDB returns a database connection with tenant context set
func TenantScopedDB(tenantID string) (*sql.DB, error) {
	sqlDB, err := db.DB.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}
	
	// Create a new connection with tenant context
	conn, err := sqlDB.Conn(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to create connection: %w", err)
	}
	
	// Set tenant context
	_, err = conn.ExecContext(context.Background(), 
		"SELECT set_config('app.current_tenant', $1, false)", tenantID)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("failed to set tenant context: %w", err)
	}
	
	return sqlDB, nil
}

// WithTenant adds tenant filtering to database queries
func WithTenant(tenantID string) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		return db.Where("tenant_id = ?", tenantID)
	}
}

// EnsureTenantIsolation validates that a resource belongs to the current tenant
func EnsureTenantIsolation(resourceTenantID, currentTenantID string) error {
	if resourceTenantID != currentTenantID {
		return fmt.Errorf("access denied: resource belongs to different tenant")
	}
	return nil
}