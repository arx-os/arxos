package notifications

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// NotificationManager manages notification creation and distribution
type NotificationManager struct {
	service *NotificationService
}

// NewNotificationManager creates a new notification manager
func NewNotificationManager(service *NotificationService) *NotificationManager {
	return &NotificationManager{
		service: service,
	}
}

// NotifyBuildingCreated creates a notification when a building is created
func (m *NotificationManager) NotifyBuildingCreated(ctx context.Context, buildingID, buildingName, userID string) error {
	notification := &Notification{
		Type:       "success",
		Title:      "Building Created",
		Message:    "Building '" + buildingName + "' has been successfully created",
		Severity:   "low",
		UserID:     userID,
		BuildingID: buildingID,
		Actions: []NotificationAction{
			{
				ID:    "view",
				Label: "View Building",
				URL:   "/buildings/" + buildingID,
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyBuildingUpdated creates a notification when a building is updated
func (m *NotificationManager) NotifyBuildingUpdated(ctx context.Context, buildingID, buildingName, userID string) error {
	notification := &Notification{
		Type:       "info",
		Title:      "Building Updated",
		Message:    "Building '" + buildingName + "' has been updated",
		Severity:   "low",
		UserID:     userID,
		BuildingID: buildingID,
		Actions: []NotificationAction{
			{
				ID:    "view",
				Label: "View Building",
				URL:   "/buildings/" + buildingID,
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyBuildingDeleted creates a notification when a building is deleted
func (m *NotificationManager) NotifyBuildingDeleted(ctx context.Context, buildingID, buildingName, userID string) error {
	notification := &Notification{
		Type:       "warning",
		Title:      "Building Deleted",
		Message:    "Building '" + buildingName + "' has been deleted",
		Severity:   "medium",
		UserID:     userID,
		BuildingID: buildingID,
	}

	return m.service.AddNotification(notification)
}

// NotifyEquipmentCreated creates a notification when equipment is created
func (m *NotificationManager) NotifyEquipmentCreated(ctx context.Context, equipmentID, equipmentName, buildingID, userID string) error {
	notification := &Notification{
		Type:        "success",
		Title:       "Equipment Added",
		Message:     "Equipment '" + equipmentName + "' has been added to the building",
		Severity:    "low",
		UserID:      userID,
		BuildingID:  buildingID,
		EquipmentID: equipmentID,
		Actions: []NotificationAction{
			{
				ID:    "view",
				Label: "View Equipment",
				URL:   "/equipment/" + equipmentID,
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyEquipmentUpdated creates a notification when equipment is updated
func (m *NotificationManager) NotifyEquipmentUpdated(ctx context.Context, equipmentID, equipmentName, buildingID, userID string) error {
	notification := &Notification{
		Type:        "info",
		Title:       "Equipment Updated",
		Message:     "Equipment '" + equipmentName + "' has been updated",
		Severity:    "low",
		UserID:      userID,
		BuildingID:  buildingID,
		EquipmentID: equipmentID,
		Actions: []NotificationAction{
			{
				ID:    "view",
				Label: "View Equipment",
				URL:   "/equipment/" + equipmentID,
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyEquipmentDeleted creates a notification when equipment is deleted
func (m *NotificationManager) NotifyEquipmentDeleted(ctx context.Context, equipmentID, equipmentName, buildingID, userID string) error {
	notification := &Notification{
		Type:        "warning",
		Title:       "Equipment Removed",
		Message:     "Equipment '" + equipmentName + "' has been removed from the building",
		Severity:    "medium",
		UserID:      userID,
		BuildingID:  buildingID,
		EquipmentID: equipmentID,
	}

	return m.service.AddNotification(notification)
}

// NotifyImportCompleted creates a notification when an import is completed
func (m *NotificationManager) NotifyImportCompleted(ctx context.Context, fileName, buildingID, userID string) error {
	notification := &Notification{
		Type:       "success",
		Title:      "Import Completed",
		Message:    "File '" + fileName + "' has been successfully imported",
		Severity:   "low",
		UserID:     userID,
		BuildingID: buildingID,
		Actions: []NotificationAction{
			{
				ID:    "view",
				Label: "View Building",
				URL:   "/buildings/" + buildingID,
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyImportFailed creates a notification when an import fails
func (m *NotificationManager) NotifyImportFailed(ctx context.Context, fileName, errorMsg, userID string) error {
	notification := &Notification{
		Type:     "error",
		Title:    "Import Failed",
		Message:  "Failed to import file '" + fileName + "': " + errorMsg,
		Severity: "high",
		UserID:   userID,
		Actions: []NotificationAction{
			{
				ID:    "retry",
				Label: "Retry Import",
				URL:   "/upload",
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyExportCompleted creates a notification when an export is completed
func (m *NotificationManager) NotifyExportCompleted(ctx context.Context, fileName, userID string) error {
	notification := &Notification{
		Type:     "success",
		Title:    "Export Completed",
		Message:  "Export '" + fileName + "' has been successfully generated",
		Severity: "low",
		UserID:   userID,
		Actions: []NotificationAction{
			{
				ID:    "download",
				Label: "Download",
				URL:   "/downloads/" + fileName,
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyExportFailed creates a notification when an export fails
func (m *NotificationManager) NotifyExportFailed(ctx context.Context, fileName, errorMsg, userID string) error {
	notification := &Notification{
		Type:     "error",
		Title:    "Export Failed",
		Message:  "Failed to export '" + fileName + "': " + errorMsg,
		Severity: "high",
		UserID:   userID,
		Actions: []NotificationAction{
			{
				ID:    "retry",
				Label: "Retry Export",
				URL:   "/export",
				Type:  "link",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifySystemMaintenance creates a system maintenance notification
func (m *NotificationManager) NotifySystemMaintenance(ctx context.Context, title, message string) error {
	notification := &Notification{
		Type:     "warning",
		Title:    title,
		Message:  message,
		Severity: "medium",
		Actions: []NotificationAction{
			{
				ID:    "dismiss",
				Label: "Dismiss",
				Type:  "dismiss",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifySystemUpdate creates a system update notification
func (m *NotificationManager) NotifySystemUpdate(ctx context.Context, version, message string) error {
	notification := &Notification{
		Type:     "info",
		Title:    "System Update",
		Message:  "ArxOS has been updated to version " + version + ". " + message,
		Severity: "low",
		Actions: []NotificationAction{
			{
				ID:    "dismiss",
				Label: "Dismiss",
				Type:  "dismiss",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyError creates an error notification
func (m *NotificationManager) NotifyError(ctx context.Context, title, message, userID string) error {
	notification := &Notification{
		Type:     "error",
		Title:    title,
		Message:  message,
		Severity: "high",
		UserID:   userID,
		Actions: []NotificationAction{
			{
				ID:    "dismiss",
				Label: "Dismiss",
				Type:  "dismiss",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyWarning creates a warning notification
func (m *NotificationManager) NotifyWarning(ctx context.Context, title, message, userID string) error {
	notification := &Notification{
		Type:     "warning",
		Title:    title,
		Message:  message,
		Severity: "medium",
		UserID:   userID,
		Actions: []NotificationAction{
			{
				ID:    "dismiss",
				Label: "Dismiss",
				Type:  "dismiss",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifyInfo creates an info notification
func (m *NotificationManager) NotifyInfo(ctx context.Context, title, message, userID string) error {
	notification := &Notification{
		Type:     "info",
		Title:    title,
		Message:  message,
		Severity: "low",
		UserID:   userID,
		Actions: []NotificationAction{
			{
				ID:    "dismiss",
				Label: "Dismiss",
				Type:  "dismiss",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// NotifySuccess creates a success notification
func (m *NotificationManager) NotifySuccess(ctx context.Context, title, message, userID string) error {
	notification := &Notification{
		Type:     "success",
		Title:    title,
		Message:  message,
		Severity: "low",
		UserID:   userID,
		Actions: []NotificationAction{
			{
				ID:    "dismiss",
				Label: "Dismiss",
				Type:  "dismiss",
			},
		},
	}

	return m.service.AddNotification(notification)
}

// CleanupOldNotifications removes notifications older than the specified duration
func (m *NotificationManager) CleanupOldNotifications(ctx context.Context, olderThan time.Duration) error {
	cutoff := time.Now().Add(-olderThan)

	// Get all notifications
	notifications, err := m.service.GetAllNotifications(1000) // Get up to 1000 notifications
	if err != nil {
		return err
	}

	// Delete old notifications
	for _, notification := range notifications {
		if notification.Timestamp.Before(cutoff) {
			if err := m.service.DeleteNotification(notification.ID); err != nil {
				logger.Error("Failed to delete old notification %s: %v", notification.ID, err)
			}
		}
	}

	return nil
}
