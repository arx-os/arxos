// Package auth provides role-based access control (RBAC) utilities.
package auth

import (
	"fmt"
	"strings"

	"github.com/arx-os/arxos/pkg/errors"
)

// Permission represents a specific permission
type Permission string

// Common permissions
const (
	// User permissions
	PermissionUserRead   Permission = "user:read"
	PermissionUserWrite  Permission = "user:write"
	PermissionUserDelete Permission = "user:delete"
	PermissionUserAdmin  Permission = "user:admin"

	// Organization permissions
	PermissionOrgRead   Permission = "organization:read"
	PermissionOrgWrite  Permission = "organization:write"
	PermissionOrgDelete Permission = "organization:delete"
	PermissionOrgAdmin  Permission = "organization:admin"

	// Building permissions
	PermissionBuildingRead   Permission = "building:read"
	PermissionBuildingWrite  Permission = "building:write"
	PermissionBuildingDelete Permission = "building:delete"
	PermissionBuildingAdmin  Permission = "building:admin"

	// Equipment permissions
	PermissionEquipmentRead    Permission = "equipment:read"
	PermissionEquipmentWrite   Permission = "equipment:write"
	PermissionEquipmentDelete  Permission = "equipment:delete"
	PermissionEquipmentControl Permission = "equipment:control"

	// Analytics permissions
	PermissionAnalyticsRead  Permission = "analytics:read"
	PermissionAnalyticsWrite Permission = "analytics:write"

	// System permissions
	PermissionSystemRead  Permission = "system:read"
	PermissionSystemWrite Permission = "system:write"
	PermissionSystemAdmin Permission = "system:admin"

	// API permissions
	PermissionAPIRead  Permission = "api:read"
	PermissionAPIWrite Permission = "api:write"
)

// Role represents a user role
type Role string

// System roles
const (
	RoleSuperAdmin Role = "super_admin"
	RoleAdmin      Role = "admin"
	RoleManager    Role = "manager"
	RoleTechnician Role = "technician"
	RoleViewer     Role = "viewer"
	RoleGuest      Role = "guest"
)

// Organization roles
const (
	OrgRoleOwner  Role = "owner"
	OrgRoleAdmin  Role = "admin"
	OrgRoleMember Role = "member"
	OrgRoleViewer Role = "viewer"
)

// RoleDefinition defines a role with its permissions
type RoleDefinition struct {
	Name        Role         `json:"name"`
	Description string       `json:"description"`
	Permissions []Permission `json:"permissions"`
	Inherits    []Role       `json:"inherits,omitempty"`
}

// RBACConfig holds RBAC configuration
type RBACConfig struct {
	// Default role for new users
	DefaultRole Role

	// Whether to allow permission inheritance
	AllowInheritance bool

	// Whether to allow custom roles
	AllowCustomRoles bool
}

// DefaultRBACConfig returns a default RBAC configuration
func DefaultRBACConfig() *RBACConfig {
	return &RBACConfig{
		DefaultRole:      RoleViewer,
		AllowInheritance: true,
		AllowCustomRoles: true,
	}
}

// RBACManager handles role-based access control
type RBACManager struct {
	config      *RBACConfig
	roleDefs    map[Role]*RoleDefinition
	customRoles map[Role]*RoleDefinition
}

// NewRBACManager creates a new RBAC manager
func NewRBACManager(config *RBACConfig) *RBACManager {
	if config == nil {
		config = DefaultRBACConfig()
	}

	manager := &RBACManager{
		config:      config,
		roleDefs:    make(map[Role]*RoleDefinition),
		customRoles: make(map[Role]*RoleDefinition),
	}

	// Initialize default roles
	manager.initializeDefaultRoles()

	return manager
}

// initializeDefaultRoles sets up the default role definitions
func (rm *RBACManager) initializeDefaultRoles() {
	// Super Admin - has all permissions
	rm.roleDefs[RoleSuperAdmin] = &RoleDefinition{
		Name:        RoleSuperAdmin,
		Description: "Super administrator with full system access",
		Permissions: []Permission{
			PermissionUserRead, PermissionUserWrite, PermissionUserDelete, PermissionUserAdmin,
			PermissionOrgRead, PermissionOrgWrite, PermissionOrgDelete, PermissionOrgAdmin,
			PermissionBuildingRead, PermissionBuildingWrite, PermissionBuildingDelete, PermissionBuildingAdmin,
			PermissionEquipmentRead, PermissionEquipmentWrite, PermissionEquipmentDelete, PermissionEquipmentControl,
			PermissionAnalyticsRead, PermissionAnalyticsWrite,
			PermissionSystemRead, PermissionSystemWrite, PermissionSystemAdmin,
			PermissionAPIRead, PermissionAPIWrite,
		},
	}

	// Admin - has most permissions except system admin
	rm.roleDefs[RoleAdmin] = &RoleDefinition{
		Name:        RoleAdmin,
		Description: "Administrator with organization management access",
		Permissions: []Permission{
			PermissionUserRead, PermissionUserWrite,
			PermissionOrgRead, PermissionOrgWrite,
			PermissionBuildingRead, PermissionBuildingWrite, PermissionBuildingDelete, PermissionBuildingAdmin,
			PermissionEquipmentRead, PermissionEquipmentWrite, PermissionEquipmentDelete, PermissionEquipmentControl,
			PermissionAnalyticsRead, PermissionAnalyticsWrite,
			PermissionAPIRead, PermissionAPIWrite,
		},
	}

	// Manager - has building and equipment management permissions
	rm.roleDefs[RoleManager] = &RoleDefinition{
		Name:        RoleManager,
		Description: "Manager with building and equipment management access",
		Permissions: []Permission{
			PermissionUserRead,
			PermissionOrgRead,
			PermissionBuildingRead, PermissionBuildingWrite, PermissionBuildingDelete,
			PermissionEquipmentRead, PermissionEquipmentWrite, PermissionEquipmentControl,
			PermissionAnalyticsRead,
			PermissionAPIRead, PermissionAPIWrite,
		},
	}

	// Technician - has equipment control permissions
	rm.roleDefs[RoleTechnician] = &RoleDefinition{
		Name:        RoleTechnician,
		Description: "Technician with equipment control access",
		Permissions: []Permission{
			PermissionBuildingRead,
			PermissionEquipmentRead, PermissionEquipmentWrite, PermissionEquipmentControl,
			PermissionAPIRead,
		},
	}

	// Viewer - read-only access
	rm.roleDefs[RoleViewer] = &RoleDefinition{
		Name:        RoleViewer,
		Description: "Viewer with read-only access",
		Permissions: []Permission{
			PermissionBuildingRead,
			PermissionEquipmentRead,
			PermissionAnalyticsRead,
			PermissionAPIRead,
		},
	}

	// Guest - minimal access
	rm.roleDefs[RoleGuest] = &RoleDefinition{
		Name:        RoleGuest,
		Description: "Guest with minimal access",
		Permissions: []Permission{
			PermissionBuildingRead,
		},
	}

	// Organization roles
	rm.roleDefs[OrgRoleOwner] = &RoleDefinition{
		Name:        OrgRoleOwner,
		Description: "Organization owner with full organization access",
		Permissions: []Permission{
			PermissionOrgRead, PermissionOrgWrite, PermissionOrgDelete, PermissionOrgAdmin,
			PermissionUserRead, PermissionUserWrite,
			PermissionBuildingRead, PermissionBuildingWrite, PermissionBuildingDelete, PermissionBuildingAdmin,
			PermissionEquipmentRead, PermissionEquipmentWrite, PermissionEquipmentDelete, PermissionEquipmentControl,
			PermissionAnalyticsRead, PermissionAnalyticsWrite,
			PermissionAPIRead, PermissionAPIWrite,
		},
	}

	rm.roleDefs[OrgRoleAdmin] = &RoleDefinition{
		Name:        OrgRoleAdmin,
		Description: "Organization administrator",
		Permissions: []Permission{
			PermissionOrgRead, PermissionOrgWrite,
			PermissionUserRead, PermissionUserWrite,
			PermissionBuildingRead, PermissionBuildingWrite, PermissionBuildingDelete,
			PermissionEquipmentRead, PermissionEquipmentWrite, PermissionEquipmentControl,
			PermissionAnalyticsRead,
			PermissionAPIRead, PermissionAPIWrite,
		},
	}

	rm.roleDefs[OrgRoleMember] = &RoleDefinition{
		Name:        OrgRoleMember,
		Description: "Organization member",
		Permissions: []Permission{
			PermissionOrgRead,
			PermissionBuildingRead, PermissionBuildingWrite,
			PermissionEquipmentRead, PermissionEquipmentWrite,
			PermissionAPIRead,
		},
	}

	rm.roleDefs[OrgRoleViewer] = &RoleDefinition{
		Name:        OrgRoleViewer,
		Description: "Organization viewer",
		Permissions: []Permission{
			PermissionOrgRead,
			PermissionBuildingRead,
			PermissionEquipmentRead,
			PermissionAPIRead,
		},
	}
}

// CheckPermission checks if a role has a specific permission
func (rm *RBACManager) CheckPermission(role Role, permission Permission) bool {
	// Check if role exists
	roleDef, exists := rm.roleDefs[role]
	if !exists {
		// Check custom roles
		roleDef, exists = rm.customRoles[role]
		if !exists {
			return false
		}
	}

	// Check direct permissions
	for _, perm := range roleDef.Permissions {
		if perm == permission {
			return true
		}
		// Check wildcard permissions
		if rm.isWildcardMatch(string(perm), string(permission)) {
			return true
		}
	}

	// Check inherited permissions
	if rm.config.AllowInheritance {
		for _, inheritedRole := range roleDef.Inherits {
			if rm.CheckPermission(inheritedRole, permission) {
				return true
			}
		}
	}

	return false
}

// CheckMultiplePermissions checks if a role has all specified permissions
func (rm *RBACManager) CheckMultiplePermissions(role Role, permissions []Permission) bool {
	for _, permission := range permissions {
		if !rm.CheckPermission(role, permission) {
			return false
		}
	}
	return true
}

// CheckAnyPermission checks if a role has any of the specified permissions
func (rm *RBACManager) CheckAnyPermission(role Role, permissions []Permission) bool {
	for _, permission := range permissions {
		if rm.CheckPermission(role, permission) {
			return true
		}
	}
	return false
}

// GetRolePermissions returns all permissions for a role
func (rm *RBACManager) GetRolePermissions(role Role) []Permission {
	roleDef, exists := rm.roleDefs[role]
	if !exists {
		roleDef, exists = rm.customRoles[role]
		if !exists {
			return nil
		}
	}

	permissions := make([]Permission, len(roleDef.Permissions))
	copy(permissions, roleDef.Permissions)

	// Add inherited permissions
	if rm.config.AllowInheritance {
		for _, inheritedRole := range roleDef.Inherits {
			inheritedPerms := rm.GetRolePermissions(inheritedRole)
			permissions = append(permissions, inheritedPerms...)
		}
	}

	return rm.deduplicatePermissions(permissions)
}

// CreateCustomRole creates a custom role
func (rm *RBACManager) CreateCustomRole(name Role, description string, permissions []Permission, inherits []Role) error {
	if !rm.config.AllowCustomRoles {
		return errors.New(errors.CodeForbidden, "custom roles are not allowed")
	}

	if _, exists := rm.roleDefs[name]; exists {
		return errors.New(errors.CodeAlreadyExists, "role already exists")
	}

	if _, exists := rm.customRoles[name]; exists {
		return errors.New(errors.CodeAlreadyExists, "custom role already exists")
	}

	// Validate inherited roles
	for _, inheritedRole := range inherits {
		if !rm.RoleExists(inheritedRole) {
			return errors.New(errors.CodeInvalidInput, "inherited role does not exist: "+string(inheritedRole))
		}
	}

	rm.customRoles[name] = &RoleDefinition{
		Name:        name,
		Description: description,
		Permissions: permissions,
		Inherits:    inherits,
	}

	return nil
}

// DeleteCustomRole deletes a custom role
func (rm *RBACManager) DeleteCustomRole(name Role) error {
	if _, exists := rm.roleDefs[name]; exists {
		return errors.New(errors.CodeForbidden, "cannot delete system role")
	}

	if _, exists := rm.customRoles[name]; !exists {
		return errors.New(errors.CodeNotFound, "custom role not found")
	}

	delete(rm.customRoles, name)
	return nil
}

// RoleExists checks if a role exists
func (rm *RBACManager) RoleExists(role Role) bool {
	_, exists := rm.roleDefs[role]
	if exists {
		return true
	}
	_, exists = rm.customRoles[role]
	return exists
}

// GetAvailableRoles returns all available roles
func (rm *RBACManager) GetAvailableRoles() []Role {
	var roles []Role

	// Add system roles
	for role := range rm.roleDefs {
		roles = append(roles, role)
	}

	// Add custom roles
	for role := range rm.customRoles {
		roles = append(roles, role)
	}

	return roles
}

// GetRoleDefinition returns the definition for a role
func (rm *RBACManager) GetRoleDefinition(role Role) (*RoleDefinition, error) {
	if roleDef, exists := rm.roleDefs[role]; exists {
		return roleDef, nil
	}

	if roleDef, exists := rm.customRoles[role]; exists {
		return roleDef, nil
	}

	return nil, errors.New(errors.CodeNotFound, "role not found")
}

// Helper methods

func (rm *RBACManager) isWildcardMatch(pattern, permission string) bool {
	// Simple wildcard matching for permissions like "building:*"
	if strings.HasSuffix(pattern, ":*") {
		prefix := strings.TrimSuffix(pattern, ":*")
		return strings.HasPrefix(permission, prefix+":")
	}

	// Check for exact wildcard
	if pattern == "*" {
		return true
	}

	return false
}

func (rm *RBACManager) deduplicatePermissions(permissions []Permission) []Permission {
	seen := make(map[Permission]bool)
	var result []Permission

	for _, perm := range permissions {
		if !seen[perm] {
			seen[perm] = true
			result = append(result, perm)
		}
	}

	return result
}

// AuthorizationContext represents the context for authorization decisions
type AuthorizationContext struct {
	UserID         string
	OrganizationID string
	Role           Role
	Permissions    []Permission
	ResourceID     string
	ResourceType   string
	Action         string
}

// Authorize checks if a user is authorized to perform an action
func (rm *RBACManager) Authorize(ctx *AuthorizationContext) error {
	if ctx == nil {
		return errors.New(errors.CodeInvalidInput, "authorization context is required")
	}

	// Check if user has the required role
	if !rm.RoleExists(ctx.Role) {
		return errors.New(errors.CodeForbidden, "invalid role")
	}

	// Check permissions
	for _, permission := range ctx.Permissions {
		if !rm.CheckPermission(ctx.Role, permission) {
			return errors.New(errors.CodeForbidden, fmt.Sprintf("insufficient permissions for %s", permission))
		}
	}

	return nil
}

// RequirePermission creates a permission requirement
func RequirePermission(permission Permission) func(*RBACManager, *AuthorizationContext) error {
	return func(rm *RBACManager, ctx *AuthorizationContext) error {
		if !rm.CheckPermission(ctx.Role, permission) {
			return errors.New(errors.CodeForbidden, fmt.Sprintf("permission required: %s", permission))
		}
		return nil
	}
}

// RequireAnyPermission creates a requirement for any of the specified permissions
func RequireAnyPermission(permissions ...Permission) func(*RBACManager, *AuthorizationContext) error {
	return func(rm *RBACManager, ctx *AuthorizationContext) error {
		if !rm.CheckAnyPermission(ctx.Role, permissions) {
			return errors.New(errors.CodeForbidden, "insufficient permissions")
		}
		return nil
	}
}

// RequireAllPermissions creates a requirement for all specified permissions
func RequireAllPermissions(permissions ...Permission) func(*RBACManager, *AuthorizationContext) error {
	return func(rm *RBACManager, ctx *AuthorizationContext) error {
		if !rm.CheckMultiplePermissions(ctx.Role, permissions) {
			return errors.New(errors.CodeForbidden, "insufficient permissions")
		}
		return nil
	}
}
