package models

// Role represents a user's role in an organization
type Role string

// Standard roles
const (
	RoleOwner   Role = "owner"
	RoleAdmin   Role = "admin"
	RoleEditor  Role = "editor"
	RoleViewer  Role = "viewer"
	RoleGuest   Role = "guest"
)

// Permission represents a specific permission in the system
type Permission string

// Standard permissions
const (
	PermissionViewBuildings   Permission = "view_buildings"
	PermissionEditBuildings   Permission = "edit_buildings"
	PermissionDeleteBuildings Permission = "delete_buildings"
	PermissionViewEquipment   Permission = "view_equipment"
	PermissionEditEquipment   Permission = "edit_equipment"
	PermissionDeleteEquipment Permission = "delete_equipment"
	PermissionViewRooms       Permission = "view_rooms"
	PermissionEditRooms       Permission = "edit_rooms"
	PermissionDeleteRooms     Permission = "delete_rooms"
	PermissionManageUsers     Permission = "manage_users"
	PermissionManageOrg       Permission = "manage_organization"
	PermissionViewReports     Permission = "view_reports"
	PermissionExportData      Permission = "export_data"
	PermissionImportData      Permission = "import_data"
	PermissionManageSync      Permission = "manage_sync"
)

// RolePermissions maps roles to their default permissions
var RolePermissions = map[Role][]Permission{
	RoleOwner: {
		PermissionViewBuildings, PermissionEditBuildings, PermissionDeleteBuildings,
		PermissionViewEquipment, PermissionEditEquipment, PermissionDeleteEquipment,
		PermissionViewRooms, PermissionEditRooms, PermissionDeleteRooms,
		PermissionManageUsers, PermissionManageOrg,
		PermissionViewReports, PermissionExportData, PermissionImportData,
		PermissionManageSync,
	},
	RoleAdmin: {
		PermissionViewBuildings, PermissionEditBuildings, PermissionDeleteBuildings,
		PermissionViewEquipment, PermissionEditEquipment, PermissionDeleteEquipment,
		PermissionViewRooms, PermissionEditRooms, PermissionDeleteRooms,
		PermissionManageUsers,
		PermissionViewReports, PermissionExportData, PermissionImportData,
		PermissionManageSync,
	},
	RoleEditor: {
		PermissionViewBuildings, PermissionEditBuildings,
		PermissionViewEquipment, PermissionEditEquipment,
		PermissionViewRooms, PermissionEditRooms,
		PermissionViewReports, PermissionExportData, PermissionImportData,
	},
	RoleViewer: {
		PermissionViewBuildings,
		PermissionViewEquipment,
		PermissionViewRooms,
		PermissionViewReports,
		PermissionExportData,
	},
	RoleGuest: {
		PermissionViewBuildings,
		PermissionViewEquipment,
		PermissionViewRooms,
	},
}

// HasPermission checks if a role has a specific permission
func (r Role) HasPermission(permission Permission) bool {
	permissions, exists := RolePermissions[r]
	if !exists {
		return false
	}

	for _, p := range permissions {
		if p == permission {
			return true
		}
	}
	return false
}

// String returns the string representation of a role
func (r Role) String() string {
	return string(r)
}

// String returns the string representation of a permission
func (p Permission) String() string {
	return string(p)
}

// IsValid checks if a role is valid
func (r Role) IsValid() bool {
	switch r {
	case RoleOwner, RoleAdmin, RoleEditor, RoleViewer, RoleGuest:
		return true
	default:
		return false
	}
}

// IsValid checks if a permission is valid
func (p Permission) IsValid() bool {
	switch p {
	case PermissionViewBuildings, PermissionEditBuildings, PermissionDeleteBuildings,
		PermissionViewEquipment, PermissionEditEquipment, PermissionDeleteEquipment,
		PermissionViewRooms, PermissionEditRooms, PermissionDeleteRooms,
		PermissionManageUsers, PermissionManageOrg,
		PermissionViewReports, PermissionExportData, PermissionImportData,
		PermissionManageSync:
		return true
	default:
		return false
	}
}