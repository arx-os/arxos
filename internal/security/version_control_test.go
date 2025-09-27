package security

import (
	"testing"
	"time"
)

func TestVersionControlSecurity(t *testing.T) {
	// Create security manager
	encryptionKey := []byte("test-encryption-key-32-bytes")
	vcs := NewVersionControlSecurity(encryptionKey)

	// Test user permissions
	userID := "test-user"
	permissions := &UserPermissions{
		UserID: userID,
		RoomAccess: map[string]*RoomAccess{
			"/buildings/main/floors/1/rooms/room-101": {
				RoomPath:     "/buildings/main/floors/1/rooms/room-101",
				CanRead:      true,
				CanWrite:     true,
				CanCommit:    true,
				CanBranch:    true,
				CanMerge:     false,
				CanReview:    false,
				CanEmergency: false,
				Branches:     []string{"main", "feature"},
			},
		},
		GlobalAccess: &GlobalAccess{
			CanCreateRooms:    false,
			CanDeleteRooms:    false,
			CanManageUsers:    false,
			CanViewAuditLogs:  true,
			CanManageSecurity: false,
			AllowedBuildings:  []string{"main"},
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Set permissions
	err := vcs.SetUserPermissions(userID, permissions)
	if err != nil {
		t.Fatalf("Failed to set user permissions: %v", err)
	}

	// Test permission retrieval
	retrievedPermissions, err := vcs.GetUserPermissions(userID)
	if err != nil {
		t.Fatalf("Failed to get user permissions: %v", err)
	}

	if retrievedPermissions.UserID != userID {
		t.Errorf("Expected user ID %s, got %s", userID, retrievedPermissions.UserID)
	}

	// Test permission checking
	ctx := &SecurityContext{
		UserID:      userID,
		IPAddress:   "192.168.1.100",
		UserAgent:   "test-agent",
		Permissions: permissions,
		SessionID:   "test-session",
	}

	roomPath := "/buildings/main/floors/1/rooms/room-101"

	// Should succeed
	err = vcs.CheckPermission(ctx, "read", roomPath)
	if err != nil {
		t.Errorf("Expected read permission to succeed, got error: %v", err)
	}

	err = vcs.CheckPermission(ctx, "write", roomPath)
	if err != nil {
		t.Errorf("Expected write permission to succeed, got error: %v", err)
	}

	err = vcs.CheckPermission(ctx, "commit", roomPath)
	if err != nil {
		t.Errorf("Expected commit permission to succeed, got error: %v", err)
	}

	err = vcs.CheckPermission(ctx, "branch", roomPath)
	if err != nil {
		t.Errorf("Expected branch permission to succeed, got error: %v", err)
	}

	// Should fail
	err = vcs.CheckPermission(ctx, "merge", roomPath)
	if err == nil {
		t.Error("Expected merge permission to fail")
	}

	err = vcs.CheckPermission(ctx, "review", roomPath)
	if err == nil {
		t.Error("Expected review permission to fail")
	}

	err = vcs.CheckPermission(ctx, "emergency", roomPath)
	if err == nil {
		t.Error("Expected emergency permission to fail")
	}

	// Test global permissions
	err = vcs.CheckPermission(ctx, "view_audit_logs", "")
	if err != nil {
		t.Errorf("Expected view_audit_logs permission to succeed, got error: %v", err)
	}

	err = vcs.CheckPermission(ctx, "create_room", "")
	if err == nil {
		t.Error("Expected create_room permission to fail")
	}

	err = vcs.CheckPermission(ctx, "manage_security", "")
	if err == nil {
		t.Error("Expected manage_security permission to fail")
	}
}

func TestAuditLogger(t *testing.T) {
	// Create audit logger
	al := NewAuditLogger()

	// Test logging
	entry := &AuditLogEntry{
		ID:       "test-audit-1",
		UserID:   "test-user",
		Action:   "commit",
		Resource: "room-101",
		RoomPath: "/buildings/main/floors/1/rooms/room-101",
		Details: map[string]interface{}{
			"result": "success",
		},
		IPAddress: "192.168.1.100",
		UserAgent: "test-agent",
		Timestamp: time.Now(),
		Success:   true,
		Severity:  "INFO",
		Category:  "version_control",
	}

	al.Log(entry)

	// Test log retrieval
	filter := &AuditLogFilter{
		UserID: "test-user",
		Limit:  10,
	}

	logs, err := al.GetLogs(filter)
	if err != nil {
		t.Fatalf("Failed to get audit logs: %v", err)
	}

	if len(logs) == 0 {
		t.Fatal("Expected at least one audit log entry")
	}

	found := false
	for _, log := range logs {
		if log.ID == entry.ID {
			found = true
			break
		}
	}

	if !found {
		t.Error("Expected to find the logged entry")
	}
}
