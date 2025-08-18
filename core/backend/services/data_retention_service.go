package services

import (
	"github.com/arxos/arxos/core/backend/models"
	"fmt"
	"log"
	"time"

	"gorm.io/gorm"
)

// DataRetentionService handles automated data retention operations
type DataRetentionService struct {
	db *gorm.DB
}

// NewDataRetentionService creates a new data retention service
func NewDataRetentionService(db *gorm.DB) *DataRetentionService {
	return &DataRetentionService{db: db}
}

// RetentionStats tracks retention operation statistics
type RetentionStats struct {
	ObjectType     string `json:"object_type"`
	ArchivedCount  int64  `json:"archived_count"`
	DeletedCount   int64  `json:"deleted_count"`
	ErrorCount     int64  `json:"error_count"`
	ProcessingTime int64  `json:"processing_time_ms"`
}

// RetentionOperation represents a retention operation
type RetentionOperation struct {
	ID          uint      `json:"id"`
	ObjectType  string    `json:"object_type"`
	Operation   string    `json:"operation"` // archive, delete
	RecordCount int64     `json:"record_count"`
	Status      string    `json:"status"` // success, failed, partial
	ErrorMsg    string    `json:"error_message,omitempty"`
	StartedAt   time.Time `json:"started_at"`
	CompletedAt time.Time `json:"completed_at"`
}

// ProcessRetentionPolicies processes all active retention policies
func (s *DataRetentionService) ProcessRetentionPolicies() ([]RetentionStats, error) {
	var policies []models.DataRetentionPolicy
	if err := s.db.Where("is_active = ?", true).Find(&policies).Error; err != nil {
		return nil, fmt.Errorf("failed to fetch retention policies: %w", err)
	}

	var stats []RetentionStats
	for _, policy := range policies {
		stat, err := s.processPolicy(policy)
		if err != nil {
			log.Printf("Error processing policy for %s: %v", policy.ObjectType, err)
			stat.ErrorCount++
		}
		stats = append(stats, stat)
	}

	return stats, nil
}

// processPolicy processes a single retention policy
func (s *DataRetentionService) processPolicy(policy models.DataRetentionPolicy) (RetentionStats, error) {
	startTime := time.Now()
	stats := RetentionStats{
		ObjectType: policy.ObjectType,
	}

	// Archive old records
	if policy.ArchiveAfter > 0 {
		archivedCount, err := s.archiveOldRecords(policy)
		if err != nil {
			return stats, fmt.Errorf("failed to archive records: %w", err)
		}
		stats.ArchivedCount = archivedCount
	}

	// Delete very old records
	if policy.DeleteAfter > 0 {
		deletedCount, err := s.deleteOldRecords(policy)
		if err != nil {
			return stats, fmt.Errorf("failed to delete records: %w", err)
		}
		stats.DeletedCount = deletedCount
	}

	stats.ProcessingTime = time.Since(startTime).Milliseconds()
	return stats, nil
}

// archiveOldRecords archives records older than the archive threshold
func (s *DataRetentionService) archiveOldRecords(policy models.DataRetentionPolicy) (int64, error) {
	archiveDate := time.Now().AddDate(0, 0, -policy.ArchiveAfter)

	switch policy.ObjectType {
	case "audit_log":
		return s.archiveAuditLogs(archiveDate)
	case "export_activity":
		return s.archiveExportActivities(archiveDate)
	case "asset_history":
		return s.archiveAssetHistory(archiveDate)
	case "maintenance_task":
		return s.archiveMaintenanceTasks(archiveDate)
	case "data_vendor_request":
		return s.archiveDataVendorRequests(archiveDate)
	default:
		return 0, fmt.Errorf("unsupported object type: %s", policy.ObjectType)
	}
}

// deleteOldRecords deletes records older than the delete threshold
func (s *DataRetentionService) deleteOldRecords(policy models.DataRetentionPolicy) (int64, error) {
	deleteDate := time.Now().AddDate(0, 0, -policy.DeleteAfter)

	switch policy.ObjectType {
	case "audit_log":
		return s.deleteAuditLogs(deleteDate)
	case "export_activity":
		return s.deleteExportActivities(deleteDate)
	case "asset_history":
		return s.deleteAssetHistory(deleteDate)
	case "maintenance_task":
		return s.deleteMaintenanceTasks(deleteDate)
	case "data_vendor_request":
		return s.deleteDataVendorRequests(deleteDate)
	default:
		return 0, fmt.Errorf("unsupported object type: %s", policy.ObjectType)
	}
}

// archiveAuditLogs archives old audit logs
func (s *DataRetentionService) archiveAuditLogs(archiveDate time.Time) (int64, error) {
	// Start a transaction
	tx := s.db.Begin()
	defer func() {
		if r := recover(); r != nil {
			tx.Rollback()
		}
	}()

	// Get logs to archive
	var logs []models.AuditLog
	if err := tx.Where("created_at < ? AND archived = ?", archiveDate, false).Find(&logs).Error; err != nil {
		tx.Rollback()
		return 0, err
	}

	if len(logs) == 0 {
		tx.Rollback()
		return 0, nil
	}

	// Archive logs
	for _, log := range logs {
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

		if err := tx.Create(&archivedLog).Error; err != nil {
			tx.Rollback()
			return 0, err
		}
	}

	// Mark original logs as archived
	result := tx.Model(&models.AuditLog{}).
		Where("created_at < ? AND archived = ?", archiveDate, false).
		Update("archived", true)

	if result.Error != nil {
		tx.Rollback()
		return 0, result.Error
	}

	// Commit transaction
	if err := tx.Commit().Error; err != nil {
		return 0, err
	}

	return int64(len(logs)), nil
}

// deleteAuditLogs deletes old archived audit logs
func (s *DataRetentionService) deleteAuditLogs(deleteDate time.Time) (int64, error) {
	// Delete from archived_audit_logs table
	result := s.db.Where("created_at < ?", deleteDate).Delete(&models.ArchivedAuditLog{})
	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// archiveExportActivities archives old export activities
func (s *DataRetentionService) archiveExportActivities(archiveDate time.Time) (int64, error) {
	// For export activities, we'll mark them as archived by updating a status field
	// In a real implementation, you might move them to a separate archive table
	result := s.db.Model(&models.ExportActivity{}).
		Where("created_at < ? AND status != 'archived'", archiveDate).
		Update("status", "archived")

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// deleteExportActivities deletes old archived export activities
func (s *DataRetentionService) deleteExportActivities(deleteDate time.Time) (int64, error) {
	result := s.db.Where("created_at < ? AND status = 'archived'", deleteDate).
		Delete(&models.ExportActivity{})

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// archiveAssetHistory archives old asset history records
func (s *DataRetentionService) archiveAssetHistory(archiveDate time.Time) (int64, error) {
	// For asset history, we'll mark them as archived
	result := s.db.Model(&models.AssetHistory{}).
		Where("created_at < ? AND archived = ?", archiveDate, false).
		Update("archived", true)

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// deleteAssetHistory deletes old archived asset history records
func (s *DataRetentionService) deleteAssetHistory(deleteDate time.Time) (int64, error) {
	result := s.db.Where("created_at < ? AND archived = ?", deleteDate, true).
		Delete(&models.AssetHistory{})

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// archiveMaintenanceTasks archives old maintenance tasks
func (s *DataRetentionService) archiveMaintenanceTasks(archiveDate time.Time) (int64, error) {
	// For maintenance tasks, we'll mark them as archived
	result := s.db.Model(&models.MaintenanceTask{}).
		Where("created_at < ? AND archived = ?", archiveDate, false).
		Update("archived", true)

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// deleteMaintenanceTasks deletes old archived maintenance tasks
func (s *DataRetentionService) deleteMaintenanceTasks(deleteDate time.Time) (int64, error) {
	result := s.db.Where("created_at < ? AND archived = ?", deleteDate, true).
		Delete(&models.MaintenanceTask{})

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// archiveDataVendorRequests archives old data vendor requests
func (s *DataRetentionService) archiveDataVendorRequests(archiveDate time.Time) (int64, error) {
	// For data vendor requests, we'll mark them as archived
	result := s.db.Model(&models.DataVendorRequest{}).
		Where("created_at < ? AND archived = ?", archiveDate, false).
		Update("archived", true)

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// deleteDataVendorRequests deletes old archived data vendor requests
func (s *DataRetentionService) deleteDataVendorRequests(deleteDate time.Time) (int64, error) {
	result := s.db.Where("created_at < ? AND archived = ?", deleteDate, true).
		Delete(&models.DataVendorRequest{})

	if result.Error != nil {
		return 0, result.Error
	}

	return result.RowsAffected, nil
}

// GetRetentionStats returns statistics about data retention
func (s *DataRetentionService) GetRetentionStats() (map[string]interface{}, error) {
	stats := make(map[string]interface{})

	// Get counts by object type
	objectTypes := []string{"audit_log", "export_activity", "asset_history", "maintenance_task", "data_vendor_request"}

	for _, objectType := range objectTypes {
		objectStats := make(map[string]interface{})

		switch objectType {
		case "audit_log":
			var totalCount, archivedCount int64
			s.db.Model(&models.AuditLog{}).Count(&totalCount)
			s.db.Model(&models.AuditLog{}).Where("archived = ?", true).Count(&archivedCount)
			s.db.Model(&models.ArchivedAuditLog{}).Count(&archivedCount)

			objectStats["total"] = totalCount
			objectStats["archived"] = archivedCount
			objectStats["active"] = totalCount - archivedCount

		case "export_activity":
			var totalCount, archivedCount int64
			s.db.Model(&models.ExportActivity{}).Count(&totalCount)
			s.db.Model(&models.ExportActivity{}).Where("status = 'archived'").Count(&archivedCount)

			objectStats["total"] = totalCount
			objectStats["archived"] = archivedCount
			objectStats["active"] = totalCount - archivedCount

		case "asset_history":
			var totalCount, archivedCount int64
			s.db.Model(&models.AssetHistory{}).Count(&totalCount)
			s.db.Model(&models.AssetHistory{}).Where("archived = ?", true).Count(&archivedCount)

			objectStats["total"] = totalCount
			objectStats["archived"] = archivedCount
			objectStats["active"] = totalCount - archivedCount

		case "maintenance_task":
			var totalCount, archivedCount int64
			s.db.Model(&models.MaintenanceTask{}).Count(&totalCount)
			s.db.Model(&models.MaintenanceTask{}).Where("archived = ?", true).Count(&archivedCount)

			objectStats["total"] = totalCount
			objectStats["archived"] = archivedCount
			objectStats["active"] = totalCount - archivedCount

		case "data_vendor_request":
			var totalCount, archivedCount int64
			s.db.Model(&models.DataVendorRequest{}).Count(&totalCount)
			s.db.Model(&models.DataVendorRequest{}).Where("archived = ?", true).Count(&archivedCount)

			objectStats["total"] = totalCount
			objectStats["archived"] = archivedCount
			objectStats["active"] = totalCount - archivedCount
		}

		stats[objectType] = objectStats
	}

	// Get retention policies
	var policies []models.DataRetentionPolicy
	s.db.Where("is_active = ?", true).Find(&policies)
	stats["policies"] = policies

	return stats, nil
}

// LogRetentionOperation logs a retention operation for audit purposes
func (s *DataRetentionService) LogRetentionOperation(operation RetentionOperation) error {
	// In a real implementation, you would log this to a retention_operations table
	log.Printf("Retention operation: %s for %s - %d records, status: %s",
		operation.Operation, operation.ObjectType, operation.RecordCount, operation.Status)
	return nil
}
