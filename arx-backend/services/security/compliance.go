package security

import (
	"fmt"
	"sync"
	"time"
)

// ComplianceStandard represents a compliance standard
type ComplianceStandard string

const (
	StandardGDPR     ComplianceStandard = "GDPR"
	StandardHIPAA    ComplianceStandard = "HIPAA"
	StandardSOC2     ComplianceStandard = "SOC2"
	StandardISO27001 ComplianceStandard = "ISO27001"
	StandardPCI      ComplianceStandard = "PCI"
)

// ComplianceRequirement represents a compliance requirement
type ComplianceRequirement struct {
	ID          string                 `json:"id"`
	Standard    ComplianceStandard     `json:"standard"`
	Section     string                 `json:"section"`
	Requirement string                 `json:"requirement"`
	Description string                 `json:"description"`
	Category    string                 `json:"category"`
	Priority    string                 `json:"priority"` // high, medium, low
	Status      string                 `json:"status"`   // compliant, non-compliant, pending, not-applicable
	Evidence    string                 `json:"evidence"`
	LastChecked time.Time              `json:"last_checked"`
	NextReview  time.Time              `json:"next_review"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ComplianceCheck represents a compliance check
type ComplianceCheck struct {
	ID            string                 `json:"id"`
	RequirementID string                 `json:"requirement_id"`
	CheckType     string                 `json:"check_type"` // automated, manual, periodic
	Status        string                 `json:"status"`     // passed, failed, warning
	Result        string                 `json:"result"`
	Details       map[string]interface{} `json:"details"`
	PerformedAt   time.Time              `json:"performed_at"`
	PerformedBy   string                 `json:"performed_by"`
	Metadata      map[string]interface{} `json:"metadata"`
}

// ComplianceReport represents a compliance report
type ComplianceReport struct {
	ID           string                  `json:"id"`
	Title        string                  `json:"title"`
	Standard     ComplianceStandard      `json:"standard"`
	Period       string                  `json:"period"`
	GeneratedAt  time.Time               `json:"generated_at"`
	GeneratedBy  string                  `json:"generated_by"`
	Summary      ComplianceSummary       `json:"summary"`
	Requirements []ComplianceRequirement `json:"requirements"`
	Checks       []ComplianceCheck       `json:"checks"`
	Metadata     map[string]interface{}  `json:"metadata"`
}

// ComplianceSummary represents a compliance summary
type ComplianceSummary struct {
	TotalRequirements    int     `json:"total_requirements"`
	CompliantCount       int     `json:"compliant_count"`
	NonCompliantCount    int     `json:"non_compliant_count"`
	PendingCount         int     `json:"pending_count"`
	NotApplicableCount   int     `json:"not_applicable_count"`
	ComplianceRate       float64 `json:"compliance_rate"`
	HighPriorityIssues   int     `json:"high_priority_issues"`
	MediumPriorityIssues int     `json:"medium_priority_issues"`
	LowPriorityIssues    int     `json:"low_priority_issues"`
}

// ComplianceService provides compliance management and reporting
type ComplianceService struct {
	requirements map[string]*ComplianceRequirement
	checks       map[string]*ComplianceCheck
	reports      map[string]*ComplianceReport
	standards    map[ComplianceStandard][]*ComplianceRequirement
	serviceMutex sync.RWMutex
	auditService *AuditService
}

// NewComplianceService creates a new compliance service
func NewComplianceService(auditService *AuditService) *ComplianceService {
	cs := &ComplianceService{
		requirements: make(map[string]*ComplianceRequirement),
		checks:       make(map[string]*ComplianceCheck),
		reports:      make(map[string]*ComplianceReport),
		standards:    make(map[ComplianceStandard][]*ComplianceRequirement),
		auditService: auditService,
	}

	// Initialize default compliance requirements
	cs.initializeDefaultRequirements()

	return cs
}

// initializeDefaultRequirements sets up default compliance requirements
func (cs *ComplianceService) initializeDefaultRequirements() {
	// GDPR Requirements
	gdprRequirements := []*ComplianceRequirement{
		{
			ID:          "GDPR-001",
			Standard:    StandardGDPR,
			Section:     "Article 5",
			Requirement: "Lawfulness, fairness and transparency",
			Description: "Personal data shall be processed lawfully, fairly and in a transparent manner",
			Category:    "Data Processing",
			Priority:    "high",
			Status:      "pending",
			CreatedAt:   time.Now(),
		},
		{
			ID:          "GDPR-002",
			Standard:    StandardGDPR,
			Section:     "Article 25",
			Requirement: "Data protection by design and by default",
			Description: "Implement appropriate technical and organisational measures",
			Category:    "Technical Measures",
			Priority:    "high",
			Status:      "pending",
			CreatedAt:   time.Now(),
		},
		{
			ID:          "GDPR-003",
			Standard:    StandardGDPR,
			Section:     "Article 32",
			Requirement: "Security of processing",
			Description: "Implement appropriate security measures",
			Category:    "Security",
			Priority:    "high",
			Status:      "pending",
			CreatedAt:   time.Now(),
		},
	}

	// HIPAA Requirements
	hipaaRequirements := []*ComplianceRequirement{
		{
			ID:          "HIPAA-001",
			Standard:    StandardHIPAA,
			Section:     "164.308(a)(1)",
			Requirement: "Security Management Process",
			Description: "Implement policies and procedures to prevent, detect, contain, and correct security violations",
			Category:    "Security Management",
			Priority:    "high",
			Status:      "pending",
			CreatedAt:   time.Now(),
		},
		{
			ID:          "HIPAA-002",
			Standard:    StandardHIPAA,
			Section:     "164.312(a)(1)",
			Requirement: "Access Control",
			Description: "Implement technical policies and procedures for electronic information systems",
			Category:    "Access Control",
			Priority:    "high",
			Status:      "pending",
			CreatedAt:   time.Now(),
		},
	}

	// Add all requirements
	for _, req := range gdprRequirements {
		cs.AddRequirement(req)
	}
	for _, req := range hipaaRequirements {
		cs.AddRequirement(req)
	}
}

// AddRequirement adds a new compliance requirement
func (cs *ComplianceService) AddRequirement(requirement *ComplianceRequirement) error {
	if requirement.ID == "" {
		requirement.ID = generateRequirementID()
	}

	requirement.CreatedAt = time.Now()
	requirement.UpdatedAt = time.Now()

	cs.serviceMutex.Lock()
	cs.requirements[requirement.ID] = requirement
	cs.standards[requirement.Standard] = append(cs.standards[requirement.Standard], requirement)
	cs.serviceMutex.Unlock()

	// Log compliance requirement addition
	if cs.auditService != nil {
		cs.auditService.LogEvent(LevelInfo, "compliance", "requirement_added",
			fmt.Sprintf("Compliance requirement added: %s - %s", requirement.Standard, requirement.Requirement),
			map[string]interface{}{
				"requirement_id": requirement.ID,
				"standard":       requirement.Standard,
				"requirement":    requirement.Requirement,
				"priority":       requirement.Priority,
			})
	}

	return nil
}

// UpdateRequirement updates a compliance requirement
func (cs *ComplianceService) UpdateRequirement(requirementID string, updates map[string]interface{}) error {
	cs.serviceMutex.Lock()
	requirement, exists := cs.requirements[requirementID]
	if !exists {
		cs.serviceMutex.Unlock()
		return fmt.Errorf("requirement not found: %s", requirementID)
	}

	// Update fields
	if status, ok := updates["status"].(string); ok {
		requirement.Status = status
	}
	if evidence, ok := updates["evidence"].(string); ok {
		requirement.Evidence = evidence
	}
	if nextReview, ok := updates["next_review"].(time.Time); ok {
		requirement.NextReview = nextReview
	}
	if description, ok := updates["description"].(string); ok {
		requirement.Description = description
	}
	if priority, ok := updates["priority"].(string); ok {
		requirement.Priority = priority
	}

	requirement.UpdatedAt = time.Now()
	cs.serviceMutex.Unlock()

	// Log compliance requirement update
	if cs.auditService != nil {
		cs.auditService.LogEvent(LevelInfo, "compliance", "requirement_updated",
			fmt.Sprintf("Compliance requirement updated: %s", requirementID),
			map[string]interface{}{
				"requirement_id": requirementID,
				"updates":        updates,
			})
	}

	return nil
}

// GetRequirement retrieves a compliance requirement
func (cs *ComplianceService) GetRequirement(requirementID string) (*ComplianceRequirement, error) {
	cs.serviceMutex.RLock()
	defer cs.serviceMutex.RUnlock()

	requirement, exists := cs.requirements[requirementID]
	if !exists {
		return nil, fmt.Errorf("requirement not found: %s", requirementID)
	}

	return requirement, nil
}

// ListRequirements returns all compliance requirements
func (cs *ComplianceService) ListRequirements() []*ComplianceRequirement {
	cs.serviceMutex.RLock()
	defer cs.serviceMutex.RUnlock()

	requirements := make([]*ComplianceRequirement, 0, len(cs.requirements))
	for _, requirement := range cs.requirements {
		requirements = append(requirements, requirement)
	}

	return requirements
}

// GetRequirementsByStandard returns requirements for a specific standard
func (cs *ComplianceService) GetRequirementsByStandard(standard ComplianceStandard) []*ComplianceRequirement {
	cs.serviceMutex.RLock()
	defer cs.serviceMutex.RUnlock()

	return cs.standards[standard]
}

// PerformComplianceCheck performs a compliance check
func (cs *ComplianceService) PerformComplianceCheck(requirementID, checkType, performedBy string, details map[string]interface{}) (*ComplianceCheck, error) {
	cs.serviceMutex.RLock()
	requirement, exists := cs.requirements[requirementID]
	cs.serviceMutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("requirement not found: %s", requirementID)
	}

	check := &ComplianceCheck{
		ID:            generateCheckID(),
		RequirementID: requirementID,
		CheckType:     checkType,
		Status:        "pending",
		Result:        "",
		Details:       details,
		PerformedAt:   time.Now(),
		PerformedBy:   performedBy,
		Metadata:      make(map[string]interface{}),
	}

	// Perform automated checks based on check type
	switch checkType {
	case "automated":
		check.Status = cs.performAutomatedCheck(requirement, details)
	case "manual":
		check.Status = "pending" // Manual checks require human review
	default:
		check.Status = "pending"
	}

	cs.serviceMutex.Lock()
	cs.checks[check.ID] = check
	cs.serviceMutex.Unlock()

	// Update requirement status based on check result
	if check.Status == "passed" {
		cs.UpdateRequirement(requirementID, map[string]interface{}{
			"status":       "compliant",
			"last_checked": time.Now(),
		})
	} else if check.Status == "failed" {
		cs.UpdateRequirement(requirementID, map[string]interface{}{
			"status":       "non-compliant",
			"last_checked": time.Now(),
		})
	}

	// Log compliance check
	if cs.auditService != nil {
		cs.auditService.LogEvent(LevelInfo, "compliance", "check_performed",
			fmt.Sprintf("Compliance check performed: %s - %s", requirementID, check.Status),
			map[string]interface{}{
				"check_id":       check.ID,
				"requirement_id": requirementID,
				"check_type":     checkType,
				"status":         check.Status,
				"performed_by":   performedBy,
			})
	}

	return check, nil
}

// performAutomatedCheck performs an automated compliance check
func (cs *ComplianceService) performAutomatedCheck(requirement *ComplianceRequirement, details map[string]interface{}) string {
	// This is a simplified implementation
	// In a real system, this would perform actual checks based on the requirement type

	switch requirement.Category {
	case "Security":
		// Check if security measures are in place
		if securityEnabled, ok := details["security_enabled"].(bool); ok && securityEnabled {
			return "passed"
		}
		return "failed"
	case "Access Control":
		// Check if access controls are implemented
		if accessControls, ok := details["access_controls"].(bool); ok && accessControls {
			return "passed"
		}
		return "failed"
	case "Data Processing":
		// Check if data processing is lawful
		if lawfulProcessing, ok := details["lawful_processing"].(bool); ok && lawfulProcessing {
			return "passed"
		}
		return "failed"
	default:
		return "pending"
	}
}

// GenerateComplianceReport generates a compliance report
func (cs *ComplianceService) GenerateComplianceReport(standard ComplianceStandard, period, generatedBy string) (*ComplianceReport, error) {
	requirements := cs.GetRequirementsByStandard(standard)

	summary := cs.calculateComplianceSummary(requirements)

	report := &ComplianceReport{
		ID:           generateReportID(),
		Title:        fmt.Sprintf("%s Compliance Report", standard),
		Standard:     standard,
		Period:       period,
		GeneratedAt:  time.Now(),
		GeneratedBy:  generatedBy,
		Summary:      summary,
		Requirements: requirements,
		Checks:       cs.getChecksForRequirements(requirements),
		Metadata:     make(map[string]interface{}),
	}

	cs.serviceMutex.Lock()
	cs.reports[report.ID] = report
	cs.serviceMutex.Unlock()

	// Log report generation
	if cs.auditService != nil {
		cs.auditService.LogEvent(LevelInfo, "compliance", "report_generated",
			fmt.Sprintf("Compliance report generated: %s", report.ID),
			map[string]interface{}{
				"report_id":       report.ID,
				"standard":        standard,
				"period":          period,
				"compliance_rate": summary.ComplianceRate,
			})
	}

	return report, nil
}

// calculateComplianceSummary calculates compliance summary statistics
func (cs *ComplianceService) calculateComplianceSummary(requirements []*ComplianceRequirement) ComplianceSummary {
	summary := ComplianceSummary{
		TotalRequirements: len(requirements),
	}

	for _, req := range requirements {
		switch req.Status {
		case "compliant":
			summary.CompliantCount++
		case "non-compliant":
			summary.NonCompliantCount++
		case "pending":
			summary.PendingCount++
		case "not-applicable":
			summary.NotApplicableCount++
		}

		switch req.Priority {
		case "high":
			if req.Status == "non-compliant" {
				summary.HighPriorityIssues++
			}
		case "medium":
			if req.Status == "non-compliant" {
				summary.MediumPriorityIssues++
			}
		case "low":
			if req.Status == "non-compliant" {
				summary.LowPriorityIssues++
			}
		}
	}

	if summary.TotalRequirements > 0 {
		summary.ComplianceRate = float64(summary.CompliantCount) / float64(summary.TotalRequirements) * 100
	}

	return summary
}

// getChecksForRequirements gets all checks for the given requirements
func (cs *ComplianceService) getChecksForRequirements(requirements []*ComplianceRequirement) []ComplianceCheck {
	cs.serviceMutex.RLock()
	defer cs.serviceMutex.RUnlock()

	var checks []ComplianceCheck
	requirementIDs := make(map[string]bool)

	for _, req := range requirements {
		requirementIDs[req.ID] = true
	}

	for _, check := range cs.checks {
		if requirementIDs[check.RequirementID] {
			checks = append(checks, *check)
		}
	}

	return checks
}

// GetComplianceStats returns compliance statistics
func (cs *ComplianceService) GetComplianceStats() map[string]interface{} {
	cs.serviceMutex.RLock()
	defer cs.serviceMutex.RUnlock()

	totalRequirements := len(cs.requirements)
	compliantCount := 0
	nonCompliantCount := 0
	pendingCount := 0
	notApplicableCount := 0

	standards := make(map[string]int)
	categories := make(map[string]int)

	for _, req := range cs.requirements {
		switch req.Status {
		case "compliant":
			compliantCount++
		case "non-compliant":
			nonCompliantCount++
		case "pending":
			pendingCount++
		case "not-applicable":
			notApplicableCount++
		}

		standards[string(req.Standard)]++
		categories[req.Category]++
	}

	complianceRate := 0.0
	if totalRequirements > 0 {
		complianceRate = float64(compliantCount) / float64(totalRequirements) * 100
	}

	return map[string]interface{}{
		"total_requirements": totalRequirements,
		"compliant":          compliantCount,
		"non_compliant":      nonCompliantCount,
		"pending":            pendingCount,
		"not_applicable":     notApplicableCount,
		"compliance_rate":    complianceRate,
		"standards":          standards,
		"categories":         categories,
	}
}

// GetReport retrieves a compliance report
func (cs *ComplianceService) GetReport(reportID string) (*ComplianceReport, error) {
	cs.serviceMutex.RLock()
	defer cs.serviceMutex.RUnlock()

	report, exists := cs.reports[reportID]
	if !exists {
		return nil, fmt.Errorf("report not found: %s", reportID)
	}

	return report, nil
}

// ListReports returns all compliance reports
func (cs *ComplianceService) ListReports() []*ComplianceReport {
	cs.serviceMutex.RLock()
	defer cs.serviceMutex.RUnlock()

	reports := make([]*ComplianceReport, 0, len(cs.reports))
	for _, report := range cs.reports {
		reports = append(reports, report)
	}

	return reports
}

// generateRequirementID generates a unique requirement ID
func generateRequirementID() string {
	return fmt.Sprintf("req_%d", time.Now().UnixNano())
}

// generateCheckID generates a unique check ID
func generateCheckID() string {
	return fmt.Sprintf("check_%d", time.Now().UnixNano())
}

// generateReportID generates a unique report ID
func generateReportID() string {
	return fmt.Sprintf("report_%d", time.Now().UnixNano())
}
