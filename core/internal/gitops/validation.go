package gitops

import (
	"context"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
)

// ValidationEngine performs validation checks on pull requests
type ValidationEngine struct {
	db        *sqlx.DB
	rules     []ValidationRule
	validators map[string]Validator
}

// NewValidationEngine creates a new validation engine
func NewValidationEngine(db *sqlx.DB) *ValidationEngine {
	ve := &ValidationEngine{
		db:         db,
		rules:      []ValidationRule{},
		validators: make(map[string]Validator),
	}

	// Register default validators
	ve.registerDefaultValidators()
	ve.loadDefaultRules()

	return ve
}

// ValidationRule defines a validation check
type ValidationRule struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Severity    string                 `json:"severity"` // error, warning, info
	Validator   string                 `json:"validator"`
	Config      map[string]interface{} `json:"config"`
	Enabled     bool                   `json:"enabled"`
	Description string                 `json:"description"`
}

// Validator performs a specific validation check
type Validator interface {
	Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error)
}

// ValidationResult represents the result of a validation check
type ValidationResult struct {
	Success  bool                   `json:"success"`
	Severity string                 `json:"severity"`
	Message  string                 `json:"message"`
	Details  map[string]interface{} `json:"details"`
	FixHint  string                 `json:"fix_hint,omitempty"`
}

// StatusCheck represents a status check for a PR
type StatusCheck struct {
	ID          string                 `json:"id" db:"id"`
	PRID        string                 `json:"pr_id" db:"pr_id"`
	CheckName   string                 `json:"check_name" db:"check_name"`
	CheckType   string                 `json:"check_type" db:"check_type"`
	Status      string                 `json:"status" db:"status"`
	Conclusion  string                 `json:"conclusion" db:"conclusion"`
	Output      map[string]interface{} `json:"output"`
	DetailsURL  string                 `json:"details_url" db:"details_url"`
	StartedAt   *time.Time             `json:"started_at" db:"started_at"`
	CompletedAt *time.Time             `json:"completed_at" db:"completed_at"`
	CommitID    string                 `json:"commit_id" db:"commit_id"`
	ExternalID  string                 `json:"external_id" db:"external_id"`
}

// ValidatePullRequest runs all validation checks on a pull request
func (ve *ValidationEngine) ValidatePullRequest(ctx context.Context, pr *PullRequest) ([]StatusCheck, error) {
	checks := []StatusCheck{}

	for _, rule := range ve.rules {
		if !rule.Enabled {
			continue
		}

		check := StatusCheck{
			ID:        uuid.New().String(),
			PRID:      pr.ID,
			CheckName: rule.Name,
			CheckType: rule.Type,
			Status:    "running",
			StartedAt: timePtr(time.Now()),
			CommitID:  *pr.SourceStateID,
		}

		// Create status check record
		if err := ve.createStatusCheck(ctx, &check); err != nil {
			return nil, fmt.Errorf("failed to create status check: %w", err)
		}

		// Run validation
		validator, exists := ve.validators[rule.Validator]
		if !exists {
			check.Status = "error"
			check.Conclusion = "error"
			check.Output = map[string]interface{}{
				"error": fmt.Sprintf("validator %s not found", rule.Validator),
			}
		} else {
			result, err := validator.Validate(ctx, pr, rule.Config)
			if err != nil {
				check.Status = "error"
				check.Conclusion = "error"
				check.Output = map[string]interface{}{
					"error": err.Error(),
				}
			} else {
				check.Status = "completed"
				if result.Success {
					check.Conclusion = "success"
				} else {
					check.Conclusion = "failure"
				}
				check.Output = map[string]interface{}{
					"message": result.Message,
					"details": result.Details,
					"fixHint": result.FixHint,
				}
			}
		}

		check.CompletedAt = timePtr(time.Now())

		// Update status check
		if err := ve.updateStatusCheck(ctx, &check); err != nil {
			return nil, fmt.Errorf("failed to update status check: %w", err)
		}

		checks = append(checks, check)
	}

	// Update PR validation status
	allPassed := true
	for _, check := range checks {
		if check.Conclusion != "success" {
			allPassed = false
			break
		}
	}

	if err := ve.updatePRValidationStatus(ctx, pr.ID, allPassed); err != nil {
		return nil, fmt.Errorf("failed to update PR validation status: %w", err)
	}

	return checks, nil
}

// registerDefaultValidators registers built-in validators
func (ve *ValidationEngine) registerDefaultValidators() {
	ve.validators["title_format"] = &TitleFormatValidator{}
	ve.validators["description_length"] = &DescriptionLengthValidator{}
	ve.validators["conflict_check"] = &ConflictCheckValidator{db: ve.db}
	ve.validators["size_limit"] = &SizeLimitValidator{}
	ve.validators["arxobject_integrity"] = &ArxObjectIntegrityValidator{db: ve.db}
	ve.validators["system_compatibility"] = &SystemCompatibilityValidator{db: ve.db}
	ve.validators["branch_protection"] = &BranchProtectionValidator{db: ve.db}
	ve.validators["commit_message"] = &CommitMessageValidator{db: ve.db}
}

// loadDefaultRules loads default validation rules
func (ve *ValidationEngine) loadDefaultRules() {
	ve.rules = []ValidationRule{
		{
			ID:          "title-format",
			Name:        "PR Title Format",
			Type:        "validation",
			Severity:    "warning",
			Validator:   "title_format",
			Config:      map[string]interface{}{"pattern": `^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+$`},
			Enabled:     true,
			Description: "Validates PR title follows conventional format",
		},
		{
			ID:          "description-length",
			Name:        "Description Length",
			Type:        "validation",
			Severity:    "info",
			Validator:   "description_length",
			Config:      map[string]interface{}{"min": 50, "max": 5000},
			Enabled:     true,
			Description: "Ensures PR description is adequate",
		},
		{
			ID:          "conflict-check",
			Name:        "Merge Conflicts",
			Type:        "validation",
			Severity:    "error",
			Validator:   "conflict_check",
			Config:      map[string]interface{}{},
			Enabled:     true,
			Description: "Checks for merge conflicts",
		},
		{
			ID:          "size-limit",
			Name:        "Change Size",
			Type:        "validation",
			Severity:    "warning",
			Validator:   "size_limit",
			Config:      map[string]interface{}{"maxFiles": 50, "maxLines": 1000},
			Enabled:     true,
			Description: "Ensures PR is not too large",
		},
		{
			ID:          "arxobject-integrity",
			Name:        "ArxObject Integrity",
			Type:        "validation",
			Severity:    "error",
			Validator:   "arxobject_integrity",
			Config:      map[string]interface{}{},
			Enabled:     true,
			Description: "Validates ArxObject data integrity",
		},
		{
			ID:          "system-compatibility",
			Name:        "System Compatibility",
			Type:        "validation",
			Severity:    "error",
			Validator:   "system_compatibility",
			Config:      map[string]interface{}{},
			Enabled:     true,
			Description: "Checks system configuration compatibility",
		},
	}
}

// TitleFormatValidator validates PR title format
type TitleFormatValidator struct{}

func (v *TitleFormatValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	pattern, ok := config["pattern"].(string)
	if !ok {
		pattern = `.*` // Default: allow any
	}

	matched, err := regexp.MatchString(pattern, pr.Title)
	if err != nil {
		return nil, fmt.Errorf("invalid pattern: %w", err)
	}

	if !matched {
		return &ValidationResult{
			Success:  false,
			Severity: "warning",
			Message:  "PR title does not follow conventional format",
			Details: map[string]interface{}{
				"title":   pr.Title,
				"pattern": pattern,
			},
			FixHint: "Use format: type(scope): description",
		}, nil
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "PR title format is valid",
	}, nil
}

// DescriptionLengthValidator validates PR description length
type DescriptionLengthValidator struct{}

func (v *DescriptionLengthValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	minLength := 50
	maxLength := 5000

	if min, ok := config["min"].(float64); ok {
		minLength = int(min)
	}
	if max, ok := config["max"].(float64); ok {
		maxLength = int(max)
	}

	length := len(pr.Description)

	if length < minLength {
		return &ValidationResult{
			Success:  false,
			Severity: "info",
			Message:  "PR description is too short",
			Details: map[string]interface{}{
				"length":    length,
				"minLength": minLength,
			},
			FixHint: fmt.Sprintf("Add more details (minimum %d characters)", minLength),
		}, nil
	}

	if length > maxLength {
		return &ValidationResult{
			Success:  false,
			Severity: "warning",
			Message:  "PR description is too long",
			Details: map[string]interface{}{
				"length":    length,
				"maxLength": maxLength,
			},
			FixHint: fmt.Sprintf("Consider being more concise (maximum %d characters)", maxLength),
		}, nil
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "PR description length is appropriate",
	}, nil
}

// ConflictCheckValidator checks for merge conflicts
type ConflictCheckValidator struct {
	db *sqlx.DB
}

func (v *ConflictCheckValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	if pr.HasConflicts {
		var conflictCount int
		err := v.db.GetContext(ctx, &conflictCount,
			"SELECT COUNT(*) FROM merge_conflicts WHERE pr_id = $1 AND status = 'unresolved'",
			pr.ID)
		if err != nil {
			return nil, err
		}

		return &ValidationResult{
			Success:  false,
			Severity: "error",
			Message:  "PR has unresolved merge conflicts",
			Details: map[string]interface{}{
				"conflictCount": conflictCount,
			},
			FixHint: "Resolve all conflicts before merging",
		}, nil
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "No merge conflicts detected",
	}, nil
}

// SizeLimitValidator checks PR size
type SizeLimitValidator struct{}

func (v *SizeLimitValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	maxFiles := 50
	maxLines := 1000

	if max, ok := config["maxFiles"].(float64); ok {
		maxFiles = int(max)
	}
	if max, ok := config["maxLines"].(float64); ok {
		maxLines = int(max)
	}

	totalLines := pr.LinesAdded + pr.LinesRemoved

	if pr.FilesChanged > maxFiles {
		return &ValidationResult{
			Success:  false,
			Severity: "warning",
			Message:  "PR changes too many files",
			Details: map[string]interface{}{
				"filesChanged": pr.FilesChanged,
				"maxFiles":     maxFiles,
			},
			FixHint: "Consider breaking into smaller PRs",
		}, nil
	}

	if totalLines > maxLines {
		return &ValidationResult{
			Success:  false,
			Severity: "warning",
			Message:  "PR has too many line changes",
			Details: map[string]interface{}{
				"totalLines": totalLines,
				"maxLines":   maxLines,
			},
			FixHint: "Consider breaking into smaller PRs",
		}, nil
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "PR size is acceptable",
	}, nil
}

// ArxObjectIntegrityValidator validates ArxObject data integrity
type ArxObjectIntegrityValidator struct {
	db *sqlx.DB
}

func (v *ArxObjectIntegrityValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	// Get source state
	var arxObjectSnapshot json.RawMessage
	err := v.db.GetContext(ctx, &arxObjectSnapshot,
		"SELECT arxobject_snapshot FROM building_states WHERE id = $1",
		pr.SourceStateID)
	if err != nil {
		return nil, err
	}

	// Validate ArxObject structure
	var objects map[string]interface{}
	if err := json.Unmarshal(arxObjectSnapshot, &objects); err != nil {
		return &ValidationResult{
			Success:  false,
			Severity: "error",
			Message:  "Invalid ArxObject JSON structure",
			Details: map[string]interface{}{
				"error": err.Error(),
			},
		}, nil
	}

	// Check for required fields in each object
	invalidObjects := []string{}
	for id, obj := range objects {
		objMap, ok := obj.(map[string]interface{})
		if !ok {
			invalidObjects = append(invalidObjects, id)
			continue
		}

		// Check required fields
		requiredFields := []string{"type", "coordinates", "properties"}
		for _, field := range requiredFields {
			if _, exists := objMap[field]; !exists {
				invalidObjects = append(invalidObjects, fmt.Sprintf("%s (missing %s)", id, field))
			}
		}
	}

	if len(invalidObjects) > 0 {
		return &ValidationResult{
			Success:  false,
			Severity: "error",
			Message:  "ArxObject integrity check failed",
			Details: map[string]interface{}{
				"invalidObjects": invalidObjects,
			},
			FixHint: "Ensure all ArxObjects have required fields",
		}, nil
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "ArxObject integrity check passed",
		Details: map[string]interface{}{
			"objectCount": len(objects),
		},
	}, nil
}

// SystemCompatibilityValidator checks system configuration compatibility
type SystemCompatibilityValidator struct {
	db *sqlx.DB
}

func (v *SystemCompatibilityValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	// Get systems state
	var systemsState json.RawMessage
	err := v.db.GetContext(ctx, &systemsState,
		"SELECT systems_state FROM building_states WHERE id = $1",
		pr.SourceStateID)
	if err != nil {
		return nil, err
	}

	// Validate systems configuration
	var systems map[string]interface{}
	if err := json.Unmarshal(systemsState, &systems); err != nil {
		return &ValidationResult{
			Success:  false,
			Severity: "error",
			Message:  "Invalid systems JSON structure",
			Details: map[string]interface{}{
				"error": err.Error(),
			},
		}, nil
	}

	// Check for system compatibility issues
	issues := []string{}
	
	// Example: Check HVAC and electrical compatibility
	if hvac, hasHVAC := systems["hvac"]; hasHVAC {
		if electrical, hasElectrical := systems["electrical"]; hasElectrical {
			// Simplified compatibility check
			hvacMap, _ := hvac.(map[string]interface{})
			electricalMap, _ := electrical.(map[string]interface{})
			
			hvacPower, _ := hvacMap["powerRequirement"].(float64)
			electricalCapacity, _ := electricalMap["capacity"].(float64)
			
			if hvacPower > electricalCapacity {
				issues = append(issues, "HVAC power requirement exceeds electrical capacity")
			}
		}
	}

	if len(issues) > 0 {
		return &ValidationResult{
			Success:  false,
			Severity: "error",
			Message:  "System compatibility issues detected",
			Details: map[string]interface{}{
				"issues": issues,
			},
			FixHint: "Review system configurations for compatibility",
		}, nil
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "System configurations are compatible",
	}, nil
}

// BranchProtectionValidator checks branch protection rules
type BranchProtectionValidator struct {
	db *sqlx.DB
}

func (v *BranchProtectionValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	// Get branch protection rules
	var rules []struct {
		RequireApprovals int    `db:"require_approvals"`
		RequireStatusChecks bool `db:"require_status_checks"`
	}

	err := v.db.SelectContext(ctx, &rules,
		`SELECT require_approvals, require_status_checks 
		 FROM branch_protection_rules 
		 WHERE building_id = $1 AND $2 LIKE branch_pattern AND is_active = true`,
		pr.BuildingID, pr.TargetBranch)
	if err != nil {
		return nil, err
	}

	if len(rules) == 0 {
		return &ValidationResult{
			Success:  true,
			Severity: "info",
			Message:  "No branch protection rules apply",
		}, nil
	}

	rule := rules[0] // Use most specific rule

	// Check approval requirements
	if rule.RequireApprovals > 0 {
		var approvalCount int
		err := v.db.GetContext(ctx, &approvalCount,
			"SELECT COUNT(*) FROM pr_reviews WHERE pr_id = $1 AND status = 'approved' AND dismissed_at IS NULL",
			pr.ID)
		if err != nil {
			return nil, err
		}

		if approvalCount < rule.RequireApprovals {
			return &ValidationResult{
				Success:  false,
				Severity: "error",
				Message:  "Insufficient approvals for protected branch",
				Details: map[string]interface{}{
					"required": rule.RequireApprovals,
					"current":  approvalCount,
				},
				FixHint: fmt.Sprintf("Need %d more approval(s)", rule.RequireApprovals-approvalCount),
			}, nil
		}
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "Branch protection requirements met",
	}, nil
}

// CommitMessageValidator validates commit messages
type CommitMessageValidator struct {
	db *sqlx.DB
}

func (v *CommitMessageValidator) Validate(ctx context.Context, pr *PullRequest, config map[string]interface{}) (*ValidationResult, error) {
	// Get commit messages
	var messages []string
	err := v.db.SelectContext(ctx, &messages,
		"SELECT commit_message FROM pr_commits WHERE pr_id = $1 ORDER BY commit_order",
		pr.ID)
	if err != nil {
		return nil, err
	}

	invalidMessages := []string{}
	for _, msg := range messages {
		if len(msg) < 10 {
			invalidMessages = append(invalidMessages, "Message too short: "+msg)
		}
		if !strings.Contains(msg, " ") {
			invalidMessages = append(invalidMessages, "Message lacks description: "+msg)
		}
	}

	if len(invalidMessages) > 0 {
		return &ValidationResult{
			Success:  false,
			Severity: "warning",
			Message:  "Some commit messages need improvement",
			Details: map[string]interface{}{
				"invalidMessages": invalidMessages,
			},
			FixHint: "Use descriptive commit messages",
		}, nil
	}

	return &ValidationResult{
		Success:  true,
		Severity: "info",
		Message:  "All commit messages are valid",
	}, nil
}

// Helper functions

func (ve *ValidationEngine) createStatusCheck(ctx context.Context, check *StatusCheck) error {
	query := `
		INSERT INTO pr_status_checks (
			id, pr_id, check_name, check_type, status,
			started_at, commit_id
		) VALUES ($1, $2, $3, $4, $5, $6, $7)`

	_, err := ve.db.ExecContext(ctx, query,
		check.ID, check.PRID, check.CheckName, check.CheckType,
		check.Status, check.StartedAt, check.CommitID)
	return err
}

func (ve *ValidationEngine) updateStatusCheck(ctx context.Context, check *StatusCheck) error {
	outputJSON, _ := json.Marshal(check.Output)
	
	query := `
		UPDATE pr_status_checks 
		SET status = $1, conclusion = $2, output = $3, completed_at = $4
		WHERE id = $5`

	_, err := ve.db.ExecContext(ctx, query,
		check.Status, check.Conclusion, outputJSON, check.CompletedAt, check.ID)
	return err
}

func (ve *ValidationEngine) updatePRValidationStatus(ctx context.Context, prID string, passed bool) error {
	query := `UPDATE pull_requests SET validation_passed = $1 WHERE id = $2`
	_, err := ve.db.ExecContext(ctx, query, passed, prID)
	return err
}

func timePtr(t time.Time) *time.Time {
	return &t
}