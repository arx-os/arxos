package facility

import (
	"fmt"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// InspectionManager manages facility inspections and findings
type InspectionManager struct {
	facilityManager  *FacilityManager
	workOrderManager *WorkOrderManager
	inspections      map[string]*Inspection
	findings         map[string]*InspectionFinding
	metrics          *InspectionMetrics
}

// InspectionMetrics tracks inspection performance
type InspectionMetrics struct {
	TotalInspections      int64   `json:"total_inspections"`
	ScheduledInspections  int64   `json:"scheduled_inspections"`
	InProgressInspections int64   `json:"in_progress_inspections"`
	CompletedInspections  int64   `json:"completed_inspections"`
	FailedInspections     int64   `json:"failed_inspections"`
	OverdueInspections    int64   `json:"overdue_inspections"`
	TotalFindings         int64   `json:"total_findings"`
	OpenFindings          int64   `json:"open_findings"`
	ResolvedFindings      int64   `json:"resolved_findings"`
	CriticalFindings      int64   `json:"critical_findings"`
	HighFindings          int64   `json:"high_findings"`
	MediumFindings        int64   `json:"medium_findings"`
	LowFindings           int64   `json:"low_findings"`
	AverageScore          float64 `json:"average_score"`
	ComplianceRate        float64 `json:"compliance_rate"`
}

// NewInspectionManager creates a new inspection manager
func NewInspectionManager(facilityManager *FacilityManager, workOrderManager *WorkOrderManager) *InspectionManager {
	return &InspectionManager{
		facilityManager:  facilityManager,
		workOrderManager: workOrderManager,
		inspections:      make(map[string]*Inspection),
		findings:         make(map[string]*InspectionFinding),
		metrics:          &InspectionMetrics{},
	}
}

// CreateInspection creates a new inspection
func (im *InspectionManager) CreateInspection(inspection *Inspection) error {
	if inspection == nil {
		return fmt.Errorf("inspection cannot be nil")
	}

	if inspection.ID == "" {
		inspection.ID = fmt.Sprintf("insp_%d", time.Now().UnixNano())
	}

	if inspection.Type == "" {
		return fmt.Errorf("inspection type cannot be empty")
	}

	if inspection.Inspector == "" {
		return fmt.Errorf("inspector cannot be empty")
	}

	// Validate building exists
	if inspection.BuildingID != "" {
		if _, exists := im.facilityManager.buildings[inspection.BuildingID]; !exists {
			return fmt.Errorf("building %s not found", inspection.BuildingID)
		}
	}

	// Validate space exists
	if inspection.SpaceID != "" {
		if _, exists := im.facilityManager.spaces[inspection.SpaceID]; !exists {
			return fmt.Errorf("space %s not found", inspection.SpaceID)
		}
	}

	// Validate asset exists
	if inspection.AssetID != "" {
		if _, exists := im.facilityManager.assets[inspection.AssetID]; !exists {
			return fmt.Errorf("asset %s not found", inspection.AssetID)
		}
	}

	// Set timestamps
	now := time.Now()
	inspection.CreatedAt = now
	inspection.UpdatedAt = now

	// Set default status
	if inspection.Status == "" {
		inspection.Status = InspectionStatusScheduled
	}

	// Store inspection
	im.inspections[inspection.ID] = inspection
	im.metrics.TotalInspections++

	// Update facility manager
	im.facilityManager.inspections[inspection.ID] = inspection

	logger.Info("Inspection created: %s (%s)", inspection.ID, inspection.Type)
	return nil
}

// GetInspection retrieves an inspection by ID
func (im *InspectionManager) GetInspection(inspectionID string) (*Inspection, error) {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return nil, fmt.Errorf("inspection %s not found", inspectionID)
	}
	return inspection, nil
}

// UpdateInspection updates an existing inspection
func (im *InspectionManager) UpdateInspection(inspectionID string, updates map[string]interface{}) error {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return fmt.Errorf("inspection %s not found", inspectionID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "type":
			if inspType, ok := value.(string); ok {
				inspection.Type = inspType
			}
		case "status":
			if status, ok := value.(string); ok {
				inspection.Status = InspectionStatus(status)
			}
		case "inspector":
			if inspector, ok := value.(string); ok {
				inspection.Inspector = inspector
			}
		case "scheduled_date":
			if date, ok := value.(time.Time); ok {
				inspection.ScheduledDate = date
			}
		case "start_date":
			if date, ok := value.(time.Time); ok {
				inspection.StartDate = &date
			}
		case "end_date":
			if date, ok := value.(time.Time); ok {
				inspection.EndDate = &date
			}
		case "score":
			if score, ok := value.(float64); ok {
				inspection.Score = score
			}
		case "notes":
			if notes, ok := value.(string); ok {
				inspection.Notes = notes
			}
		}
	}

	inspection.UpdatedAt = time.Now()
	logger.Info("Inspection updated: %s", inspectionID)
	return nil
}

// DeleteInspection deletes an inspection
func (im *InspectionManager) DeleteInspection(inspectionID string) error {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return fmt.Errorf("inspection %s not found", inspectionID)
	}

	// Delete associated findings
	for _, finding := range inspection.Findings {
		delete(im.findings, finding.ID)
	}

	// Delete inspection
	delete(im.inspections, inspectionID)
	delete(im.facilityManager.inspections, inspectionID)
	im.metrics.TotalInspections--

	logger.Info("Inspection deleted: %s (%s)", inspectionID, inspection.Type)
	return nil
}

// ListInspections returns all inspections
func (im *InspectionManager) ListInspections() []*Inspection {
	inspections := make([]*Inspection, 0, len(im.inspections))
	for _, inspection := range im.inspections {
		inspections = append(inspections, inspection)
	}
	return inspections
}

// GetInspectionsByType returns inspections by type
func (im *InspectionManager) GetInspectionsByType(inspType InspectionType) []*Inspection {
	var inspections []*Inspection
	for _, inspection := range im.inspections {
		if inspection.Type == string(inspType) {
			inspections = append(inspections, inspection)
		}
	}
	return inspections
}

// GetInspectionsByStatus returns inspections by status
func (im *InspectionManager) GetInspectionsByStatus(status InspectionStatus) []*Inspection {
	var inspections []*Inspection
	for _, inspection := range im.inspections {
		if inspection.Status == status {
			inspections = append(inspections, inspection)
		}
	}
	return inspections
}

// GetInspectionsByBuilding returns inspections for a specific building
func (im *InspectionManager) GetInspectionsByBuilding(buildingID string) []*Inspection {
	var inspections []*Inspection
	for _, inspection := range im.inspections {
		if inspection.BuildingID == buildingID {
			inspections = append(inspections, inspection)
		}
	}
	return inspections
}

// GetInspectionsBySpace returns inspections for a specific space
func (im *InspectionManager) GetInspectionsBySpace(spaceID string) []*Inspection {
	var inspections []*Inspection
	for _, inspection := range im.inspections {
		if inspection.SpaceID == spaceID {
			inspections = append(inspections, inspection)
		}
	}
	return inspections
}

// GetInspectionsByAsset returns inspections for a specific asset
func (im *InspectionManager) GetInspectionsByAsset(assetID string) []*Inspection {
	var inspections []*Inspection
	for _, inspection := range im.inspections {
		if inspection.AssetID == assetID {
			inspections = append(inspections, inspection)
		}
	}
	return inspections
}

// GetInspectionsByInspector returns inspections by a specific inspector
func (im *InspectionManager) GetInspectionsByInspector(inspectorID string) []*Inspection {
	var inspections []*Inspection
	for _, inspection := range im.inspections {
		if inspection.Inspector == inspectorID {
			inspections = append(inspections, inspection)
		}
	}
	return inspections
}

// GetOverdueInspections returns overdue inspections
func (im *InspectionManager) GetOverdueInspections() []*Inspection {
	var overdueInspections []*Inspection
	now := time.Now()

	for _, inspection := range im.inspections {
		if inspection.Status == InspectionStatusScheduled && inspection.ScheduledDate.Before(now) {
			overdueInspections = append(overdueInspections, inspection)
		}
	}

	return overdueInspections
}

// GetUpcomingInspections returns inspections scheduled in the next specified days
func (im *InspectionManager) GetUpcomingInspections(days int) []*Inspection {
	var upcomingInspections []*Inspection
	now := time.Now()
	cutoff := now.AddDate(0, 0, days)

	for _, inspection := range im.inspections {
		if inspection.Status == InspectionStatusScheduled &&
			inspection.ScheduledDate.After(now) && inspection.ScheduledDate.Before(cutoff) {
			upcomingInspections = append(upcomingInspections, inspection)
		}
	}

	return upcomingInspections
}

// StartInspection starts an inspection
func (im *InspectionManager) StartInspection(inspectionID string) error {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return fmt.Errorf("inspection %s not found", inspectionID)
	}

	if inspection.Status != InspectionStatusScheduled {
		return fmt.Errorf("inspection must be scheduled to start")
	}

	now := time.Now()
	inspection.Status = InspectionStatusInProgress
	inspection.StartDate = &now
	inspection.UpdatedAt = now

	logger.Info("Inspection %s started", inspectionID)
	return nil
}

// CompleteInspection completes an inspection
func (im *InspectionManager) CompleteInspection(inspectionID string, score float64, notes string) error {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return fmt.Errorf("inspection %s not found", inspectionID)
	}

	if inspection.Status != InspectionStatusInProgress {
		return fmt.Errorf("inspection must be in progress to complete")
	}

	now := time.Now()
	inspection.Status = InspectionStatusCompleted
	inspection.EndDate = &now
	inspection.Score = score
	inspection.Notes = notes
	inspection.UpdatedAt = now

	logger.Info("Inspection %s completed with score %.2f", inspectionID, score)
	return nil
}

// FailInspection marks an inspection as failed
func (im *InspectionManager) FailInspection(inspectionID string, reason string) error {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return fmt.Errorf("inspection %s not found", inspectionID)
	}

	if inspection.Status != InspectionStatusInProgress {
		return fmt.Errorf("inspection must be in progress to fail")
	}

	now := time.Now()
	inspection.Status = InspectionStatusFailed
	inspection.EndDate = &now
	inspection.Notes = fmt.Sprintf("Failed: %s", reason)
	inspection.UpdatedAt = now

	logger.Info("Inspection %s failed: %s", inspectionID, reason)
	return nil
}

// CancelInspection cancels an inspection
func (im *InspectionManager) CancelInspection(inspectionID string, reason string) error {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return fmt.Errorf("inspection %s not found", inspectionID)
	}

	inspection.Status = InspectionStatusCancelled
	inspection.Notes = fmt.Sprintf("Cancelled: %s", reason)
	inspection.UpdatedAt = time.Now()

	logger.Info("Inspection %s cancelled: %s", inspectionID, reason)
	return nil
}

// AddFinding adds a finding to an inspection
func (im *InspectionManager) AddFinding(inspectionID string, finding *InspectionFinding) error {
	inspection, exists := im.inspections[inspectionID]
	if !exists {
		return fmt.Errorf("inspection %s not found", inspectionID)
	}

	if finding == nil {
		return fmt.Errorf("finding cannot be nil")
	}

	if finding.ID == "" {
		finding.ID = fmt.Sprintf("finding_%d", time.Now().UnixNano())
	}

	if finding.Description == "" {
		return fmt.Errorf("finding description cannot be empty")
	}

	// Set default status
	if finding.Status == "" {
		finding.Status = FindingStatusOpen
	}

	// Store finding
	im.findings[finding.ID] = finding
	inspection.Findings = append(inspection.Findings, *finding)
	im.metrics.TotalFindings++

	logger.Info("Finding added to inspection %s: %s", inspectionID, finding.ID)
	return nil
}

// UpdateFinding updates an existing finding
func (im *InspectionManager) UpdateFinding(findingID string, updates map[string]interface{}) error {
	finding, exists := im.findings[findingID]
	if !exists {
		return fmt.Errorf("finding %s not found", findingID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "description":
			if desc, ok := value.(string); ok {
				finding.Description = desc
			}
		case "severity":
			if severity, ok := value.(string); ok {
				finding.Severity = FindingSeverity(severity)
			}
		case "category":
			if category, ok := value.(string); ok {
				finding.Category = category
			}
		case "location":
			if location, ok := value.(string); ok {
				finding.Location = location
			}
		case "recommendation":
			if recommendation, ok := value.(string); ok {
				finding.Recommendation = recommendation
			}
		case "status":
			if status, ok := value.(string); ok {
				finding.Status = FindingStatus(status)
			}
		case "due_date":
			if dueDate, ok := value.(time.Time); ok {
				finding.DueDate = &dueDate
			}
		case "resolved_date":
			if resolvedDate, ok := value.(time.Time); ok {
				finding.ResolvedDate = &resolvedDate
			}
		}
	}

	logger.Info("Finding updated: %s", findingID)
	return nil
}

// DeleteFinding deletes a finding
func (im *InspectionManager) DeleteFinding(findingID string) error {
	_, exists := im.findings[findingID]
	if !exists {
		return fmt.Errorf("finding %s not found", findingID)
	}

	// Remove from inspection
	for inspectionID, inspection := range im.inspections {
		for i, f := range inspection.Findings {
			if f.ID == findingID {
				inspection.Findings = append(inspection.Findings[:i], inspection.Findings[i+1:]...)
				break
			}
		}
		// Update inspection in map
		im.inspections[inspectionID] = inspection
	}

	// Delete finding
	delete(im.findings, findingID)
	im.metrics.TotalFindings--

	logger.Info("Finding deleted: %s", findingID)
	return nil
}

// GetFindingsBySeverity returns findings by severity
func (im *InspectionManager) GetFindingsBySeverity(severity FindingSeverity) []*InspectionFinding {
	var findings []*InspectionFinding
	for _, finding := range im.findings {
		if finding.Severity == severity {
			findings = append(findings, finding)
		}
	}
	return findings
}

// GetFindingsByStatus returns findings by status
func (im *InspectionManager) GetFindingsByStatus(status FindingStatus) []*InspectionFinding {
	var findings []*InspectionFinding
	for _, finding := range im.findings {
		if finding.Status == status {
			findings = append(findings, finding)
		}
	}
	return findings
}

// GetFindingsByCategory returns findings by category
func (im *InspectionManager) GetFindingsByCategory(category string) []*InspectionFinding {
	var findings []*InspectionFinding
	for _, finding := range im.findings {
		if finding.Category == category {
			findings = append(findings, finding)
		}
	}
	return findings
}

// GetOverdueFindings returns overdue findings
func (im *InspectionManager) GetOverdueFindings() []*InspectionFinding {
	var overdueFindings []*InspectionFinding
	now := time.Now()

	for _, finding := range im.findings {
		if finding.DueDate != nil && finding.DueDate.Before(now) &&
			(finding.Status == FindingStatusOpen || finding.Status == FindingStatusInProgress) {
			overdueFindings = append(overdueFindings, finding)
		}
	}

	return overdueFindings
}

// ResolveFinding resolves a finding
func (im *InspectionManager) ResolveFinding(findingID string, resolution string) error {
	finding, exists := im.findings[findingID]
	if !exists {
		return fmt.Errorf("finding %s not found", findingID)
	}

	now := time.Now()
	finding.Status = FindingStatusResolved
	finding.ResolvedDate = &now
	finding.Recommendation = resolution

	logger.Info("Finding %s resolved", findingID)
	return nil
}

// CloseFinding closes a finding
func (im *InspectionManager) CloseFinding(findingID string) error {
	finding, exists := im.findings[findingID]
	if !exists {
		return fmt.Errorf("finding %s not found", findingID)
	}

	finding.Status = FindingStatusClosed

	logger.Info("Finding %s closed", findingID)
	return nil
}

// GetInspectionStatistics returns inspection statistics
func (im *InspectionManager) GetInspectionStatistics() map[string]interface{} {
	stats := make(map[string]interface{})

	// Count by type
	typeCounts := make(map[InspectionType]int)
	for _, inspection := range im.inspections {
		typeCounts[InspectionType(inspection.Type)]++
	}
	stats["type_counts"] = typeCounts

	// Count by status
	statusCounts := make(map[InspectionStatus]int)
	for _, inspection := range im.inspections {
		statusCounts[inspection.Status]++
	}
	stats["status_counts"] = statusCounts

	// Count findings by severity
	severityCounts := make(map[FindingSeverity]int)
	for _, finding := range im.findings {
		severityCounts[finding.Severity]++
	}
	stats["severity_counts"] = severityCounts

	// Count findings by status
	findingStatusCounts := make(map[FindingStatus]int)
	for _, finding := range im.findings {
		findingStatusCounts[finding.Status]++
	}
	stats["finding_status_counts"] = findingStatusCounts

	// Calculate average score
	var totalScore float64
	var scoreCount int
	for _, inspection := range im.inspections {
		if inspection.Score > 0 {
			totalScore += inspection.Score
			scoreCount++
		}
	}

	if scoreCount > 0 {
		stats["average_score"] = totalScore / float64(scoreCount)
	}

	// Count upcoming and overdue
	stats["upcoming_inspections"] = len(im.GetUpcomingInspections(30))
	stats["overdue_inspections"] = len(im.GetOverdueInspections())
	stats["overdue_findings"] = len(im.GetOverdueFindings())

	stats["total_inspections"] = len(im.inspections)
	stats["total_findings"] = len(im.findings)

	return stats
}

// GetInspectionMetrics returns inspection metrics
func (im *InspectionManager) GetInspectionMetrics() *InspectionMetrics {
	// Update metrics
	im.metrics.TotalInspections = int64(len(im.inspections))
	im.metrics.TotalFindings = int64(len(im.findings))

	// Count by status
	im.metrics.ScheduledInspections = 0
	im.metrics.CompletedInspections = 0
	im.metrics.FailedInspections = 0
	im.metrics.OverdueInspections = 0

	now := time.Now()
	for _, inspection := range im.inspections {
		switch inspection.Status {
		case InspectionStatusScheduled:
			im.metrics.ScheduledInspections++
			if inspection.ScheduledDate.Before(now) {
				im.metrics.OverdueInspections++
			}
		case InspectionStatusCompleted:
			im.metrics.CompletedInspections++
		case InspectionStatusFailed:
			im.metrics.FailedInspections++
		}
	}

	// Count findings by status
	im.metrics.OpenFindings = 0
	im.metrics.ResolvedFindings = 0
	im.metrics.CriticalFindings = 0
	im.metrics.HighFindings = 0
	im.metrics.MediumFindings = 0
	im.metrics.LowFindings = 0

	for _, finding := range im.findings {
		switch finding.Status {
		case FindingStatusOpen, FindingStatusInProgress:
			im.metrics.OpenFindings++
		case FindingStatusResolved, FindingStatusClosed:
			im.metrics.ResolvedFindings++
		}

		switch finding.Severity {
		case FindingSeverityCritical:
			im.metrics.CriticalFindings++
		case FindingSeverityHigh:
			im.metrics.HighFindings++
		case FindingSeverityMedium:
			im.metrics.MediumFindings++
		case FindingSeverityLow:
			im.metrics.LowFindings++
		}
	}

	// Calculate average score
	var totalScore float64
	var scoreCount int
	for _, inspection := range im.inspections {
		if inspection.Score > 0 {
			totalScore += inspection.Score
			scoreCount++
		}
	}

	if scoreCount > 0 {
		im.metrics.AverageScore = totalScore / float64(scoreCount)
	}

	// Calculate compliance rate
	if im.metrics.TotalInspections > 0 {
		im.metrics.ComplianceRate = float64(im.metrics.CompletedInspections) / float64(im.metrics.TotalInspections) * 100
	}

	return im.metrics
}

// Helper methods

// SortInspectionsByScheduledDate sorts inspections by scheduled date
func (im *InspectionManager) SortInspectionsByScheduledDate(inspections []*Inspection) []*Inspection {
	sort.Slice(inspections, func(i, j int) bool {
		return inspections[i].ScheduledDate.Before(inspections[j].ScheduledDate)
	})
	return inspections
}

// SortInspectionsByScore sorts inspections by score
func (im *InspectionManager) SortInspectionsByScore(inspections []*Inspection) []*Inspection {
	sort.Slice(inspections, func(i, j int) bool {
		return inspections[i].Score > inspections[j].Score
	})
	return inspections
}

// SortFindingsBySeverity sorts findings by severity
func (im *InspectionManager) SortFindingsBySeverity(findings []*InspectionFinding) []*InspectionFinding {
	severityOrder := map[FindingSeverity]int{
		FindingSeverityCritical: 4,
		FindingSeverityHigh:     3,
		FindingSeverityMedium:   2,
		FindingSeverityLow:      1,
	}

	sort.Slice(findings, func(i, j int) bool {
		return severityOrder[findings[i].Severity] > severityOrder[findings[j].Severity]
	})
	return findings
}

// SortFindingsByDueDate sorts findings by due date
func (im *InspectionManager) SortFindingsByDueDate(findings []*InspectionFinding) []*InspectionFinding {
	sort.Slice(findings, func(i, j int) bool {
		if findings[i].DueDate == nil {
			return false
		}
		if findings[j].DueDate == nil {
			return true
		}
		return findings[i].DueDate.Before(*findings[j].DueDate)
	})
	return findings
}

// GetInspectionsByDateRange returns inspections within a date range
func (im *InspectionManager) GetInspectionsByDateRange(startDate, endDate time.Time) []*Inspection {
	var inspections []*Inspection
	for _, inspection := range im.inspections {
		if inspection.ScheduledDate.After(startDate) && inspection.ScheduledDate.Before(endDate) {
			inspections = append(inspections, inspection)
		}
	}
	return inspections
}

// GetFindingsByDateRange returns findings within a date range
func (im *InspectionManager) GetFindingsByDateRange(startDate, endDate time.Time) []*InspectionFinding {
	var findings []*InspectionFinding
	for _, finding := range im.findings {
		if finding.DueDate != nil && finding.DueDate.After(startDate) && finding.DueDate.Before(endDate) {
			findings = append(findings, finding)
		}
	}
	return findings
}

// CreateFinding creates a new inspection finding
func (im *InspectionManager) CreateFinding(finding *InspectionFinding) error {
	if finding == nil {
		return fmt.Errorf("finding cannot be nil")
	}

	if finding.ID == "" {
		finding.ID = fmt.Sprintf("finding_%d", time.Now().UnixNano())
	}

	if finding.InspectionID == "" {
		return fmt.Errorf("inspection ID is required")
	}

	// Verify inspection exists
	if _, exists := im.inspections[finding.InspectionID]; !exists {
		return fmt.Errorf("inspection %s not found", finding.InspectionID)
	}

	finding.CreatedAt = time.Now()
	finding.UpdatedAt = time.Now()
	im.findings[finding.ID] = finding
	im.metrics.TotalFindings++

	// Update finding count by severity
	switch finding.Severity {
	case FindingSeverityCritical:
		im.metrics.CriticalFindings++
	case FindingSeverityHigh:
		im.metrics.HighFindings++
	case FindingSeverityMedium:
		im.metrics.MediumFindings++
	case FindingSeverityLow:
		im.metrics.LowFindings++
	}

	logger.Info("Inspection finding %s created for inspection %s", finding.ID, finding.InspectionID)
	return nil
}

// GetFinding retrieves an inspection finding by ID
func (im *InspectionManager) GetFinding(findingID string) (*InspectionFinding, error) {
	finding, exists := im.findings[findingID]
	if !exists {
		return nil, fmt.Errorf("finding %s not found", findingID)
	}
	return finding, nil
}
