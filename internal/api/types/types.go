package types

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/interfaces"
	domainmodels "github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
)

// Config holds configuration for the API server
type Config struct {
	CORS      CORSConfig      `json:"cors"`
	RateLimit RateLimitConfig `json:"rate_limit"`
	TLS       TLSConfig       `json:"tls"`
}

// CORSConfig configures Cross-Origin Resource Sharing
type CORSConfig struct {
	AllowedOrigins []string `json:"allowed_origins"`
	AllowedMethods []string `json:"allowed_methods"`
	AllowedHeaders []string `json:"allowed_headers"`
	MaxAge         int      `json:"max_age"`
}

// RateLimitConfig configures rate limiting
type RateLimitConfig struct {
	RequestsPerMinute int           `json:"requests_per_minute"`
	BurstSize         int           `json:"burst_size"`
	CleanupInterval   time.Duration `json:"cleanup_interval"`
	ClientTTL         time.Duration `json:"client_ttl"`
}

// TLSConfig configures TLS/HTTPS settings
type TLSConfig struct {
	Enabled         bool     `json:"enabled"`
	CertFile        string   `json:"cert_file"`
	KeyFile         string   `json:"key_file"`
	AutoCert        bool     `json:"auto_cert"`
	AutoCertDomains []string `json:"auto_cert_domains"`
	MinVersion      uint16   `json:"min_version"`
}

// Server represents the API server
type Server struct {
	Addr     string
	Config   *Config
	Services *Services
	Server   interface{} // *http.Server - avoiding import cycle
	Router   interface{} // *http.ServeMux - avoiding import cycle
}

// Services holds all service dependencies
type Services struct {
	DB           interface{} // *sql.DB - avoiding import cycle
	Auth         AuthService
	Building     BuildingService
	User         UserService
	Organization OrganizationService
	Equipment    EquipmentService
	FloorPlan    FloorPlanService
	Simulation   SimulationService
	Export       ExportService
	Import       ImportService
	Search       SearchService
	Cache        CacheService
	Telemetry    TelemetryService
	Email        EmailService
	Security     SecurityService
}

// Service interfaces (simplified to avoid import cycles)
type BuildingService interface {
	CreateBuilding(ctx context.Context, name string) (interface{}, error)
	GetBuilding(ctx context.Context, id string) (interface{}, error)
	GetBuildings(ctx context.Context) ([]interface{}, error)
	ListBuildings(ctx context.Context, orgID string, page, limit int) ([]interface{}, error)
	UpdateBuilding(ctx context.Context, id, name string) (interface{}, error)
	DeleteBuilding(ctx context.Context, id string) error
	GetConnectionGraph(ctx context.Context, buildingID string) (interface{}, error)
	CreateConnection(ctx context.Context, fromID, toID, connType string) (interface{}, error)
	DeleteConnection(ctx context.Context, connectionID string) error
	ListRooms(ctx context.Context, buildingID string) ([]interface{}, error)
	ListEquipment(ctx context.Context, buildingID string, filters map[string]interface{}) ([]interface{}, error)
}

type UserService interface {
	GetUserByEmail(ctx context.Context, email string) (interface{}, error)
	GetUser(ctx context.Context, id string) (interface{}, error)
	CreateUser(ctx context.Context, email, password, name string) (interface{}, error)
	UpdateUser(ctx context.Context, id string, updates map[string]interface{}) (interface{}, error)
	DeleteUser(ctx context.Context, id string) error
	RequestPasswordReset(ctx context.Context, email string) error
	ConfirmPasswordReset(ctx context.Context, token, newPassword string) error
	ListUsers(ctx context.Context, filter interface{}) ([]interface{}, error)
	ChangePassword(ctx context.Context, userID, currentPassword, newPassword string) error
	GetUserOrganizations(ctx context.Context, userID string) ([]interface{}, error)
	GetUserSessions(ctx context.Context, userID string) ([]interface{}, error)
	DeleteSession(ctx context.Context, userID, sessionID string) error
}

type OrganizationService interface {
	ListOrganizations(ctx context.Context, userID string) ([]interface{}, error)
	GetOrganization(ctx context.Context, id string) (interface{}, error)
	CreateOrganization(ctx context.Context, name, description, userID string) (interface{}, error)
	UpdateOrganization(ctx context.Context, id string, updates map[string]interface{}) (interface{}, error)
	DeleteOrganization(ctx context.Context, id string) error
	GetMembers(ctx context.Context, orgID string) ([]interface{}, error)
	GetMemberRole(ctx context.Context, orgID, userID string) (string, error)
	AddMember(ctx context.Context, orgID, userID, role string) error
	UpdateMemberRole(ctx context.Context, orgID, userID, role string) error
	RemoveMember(ctx context.Context, orgID, userID string) error
	CreateInvitation(ctx context.Context, orgID, email, role string) (interface{}, error)
	ListPendingInvitations(ctx context.Context, orgID string) ([]interface{}, error)
	AcceptInvitation(ctx context.Context, token string) error
	RevokeInvitation(ctx context.Context, orgID, invitationID string) error
}

type EquipmentService interface {
	CreateEquipment(ctx context.Context, name, eqType, buildingID, roomID string, x, y, z float64) (interface{}, error)
	GetEquipment(ctx context.Context) ([]interface{}, error)
	GetEquipmentByID(ctx context.Context, id string) (interface{}, error)
	UpdateEquipment(ctx context.Context, id, name, eqType string, x, y, z float64) (interface{}, error)
	DeleteEquipment(ctx context.Context, id string) error
}

type FloorPlanService interface{}

type SimulationService interface{}

type ExportService interface {
	ExportBIM(ctx context.Context, buildingID, format string) (interface{}, error)
}

type ImportService interface {
	ImportIFC(ctx context.Context, file interface{}, filename string) (interface{}, error)
}

type SearchService interface {
	SpatialQuery(ctx context.Context, query string, limit int) ([]interface{}, error)
	ProximitySearch(ctx context.Context, x, y, z, radius float64, limit int) ([]interface{}, error)
}

type CacheService interface{}

type TelemetryService interface{}

type EmailService interface{}

type SecurityService interface{}

// AuthService interface for authentication operations
type AuthService interface {
	Login(ctx context.Context, email, password string) (interface{}, error)
	Register(ctx context.Context, email, password, name string) (interface{}, error)
	Logout(ctx context.Context, token string) error
	GenerateToken(ctx context.Context, userID, email, role, orgID string) (string, error)
	ValidateToken(ctx context.Context, token string) (*interfaces.TokenClaims, error)
	RefreshToken(ctx context.Context, refreshToken string) (string, string, error)
	RevokeToken(ctx context.Context, token string) error
	DeleteSession(ctx context.Context, userID, sessionID string) error
}

// Helper methods for Server
func (s *Server) RespondError(w http.ResponseWriter, statusCode int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(map[string]string{"error": message})
}

func (s *Server) RespondJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(data)
}

// GetCurrentUser extracts the current user from the request context
func (s *Server) GetCurrentUser(r *http.Request) (*domainmodels.User, error) {
	// This would typically extract user from JWT token or session
	// For now, return a placeholder implementation
	userID := r.Header.Get("X-User-ID")
	if userID == "" {
		return nil, fmt.Errorf("user not authenticated")
	}

	// In a real implementation, you would:
	// 1. Extract token from Authorization header
	// 2. Validate token with AuthService
	// 3. Return user information
	return &domainmodels.User{
		ID:   userID,
		Role: "user", // This would come from token claims
	}, nil
}

// HasOrgAccess checks if a user has access to an organization
func (s *Server) HasOrgAccess(ctx context.Context, user *domainmodels.User, orgID string) bool {
	// This would typically check user's organization membership
	// For now, return true as a placeholder
	return true
}

// ValidateRequest validates request data using a validator
func (s *Server) ValidateRequest(data interface{}) error {
	// This would use a validation library like go-playground/validator
	// For now, return nil as a placeholder
	return nil
}

// LogRequest logs the incoming request
func (s *Server) LogRequest(r *http.Request, statusCode int, duration time.Duration) {
	// This would use the logger to log request details
	// For now, it's a placeholder
}

// GenerateID generates a new unique ID
func (s *Server) GenerateID() string {
	return uuid.New().String()
}
