package state

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/pkg/errors"
)

// DiffEngine handles state comparison operations
type DiffEngine struct {
	db      *sqlx.DB
	manager *Manager
}

// NewDiffEngine creates a new diff engine
func NewDiffEngine(db *sqlx.DB, manager *Manager) *DiffEngine {
	return &DiffEngine{
		db:      db,
		manager: manager,
	}
}

// StateDiff represents the complete difference between two states
type StateDiff struct {
	FromStateID string          `json:"from_state_id"`
	ToStateID   string          `json:"to_state_id"`
	FromVersion string          `json:"from_version"`
	ToVersion   string          `json:"to_version"`
	
	// Summary statistics
	Summary DiffSummary `json:"summary"`
	
	// Detailed changes
	ArxObjectChanges  ArxObjectDiff   `json:"arxobject_changes"`
	SystemChanges     SystemDiff      `json:"system_changes"`
	MetricChanges     MetricDiff      `json:"metric_changes,omitempty"`
	ComplianceChanges ComplianceDiff  `json:"compliance_changes,omitempty"`
	
	// Metadata
	CalculatedAt time.Time `json:"calculated_at"`
	CalculationTimeMs int    `json:"calculation_time_ms"`
}

// DiffSummary provides high-level statistics about the diff
type DiffSummary struct {
	TotalChanges      int      `json:"total_changes"`
	ArxObjectsAdded   int      `json:"arxobjects_added"`
	ArxObjectsModified int     `json:"arxobjects_modified"`
	ArxObjectsRemoved int      `json:"arxobjects_removed"`
	SystemsChanged    []string `json:"systems_changed"`
	SeverityLevel     string   `json:"severity_level"` // minor, moderate, major
}

// ArxObjectDiff represents changes to ArxObjects
type ArxObjectDiff struct {
	Added    []ArxObjectChange `json:"added"`
	Modified []ArxObjectChange `json:"modified"`
	Removed  []ArxObjectChange `json:"removed"`
}

// ArxObjectChange represents a single ArxObject change
type ArxObjectChange struct {
	ID         string          `json:"id"`
	Type       string          `json:"type"`
	ChangeType string          `json:"change_type"`
	Before     json.RawMessage `json:"before,omitempty"`
	After      json.RawMessage `json:"after,omitempty"`
	Fields     []FieldChange   `json:"fields,omitempty"`
}

// FieldChange represents a change to a specific field
type FieldChange struct {
	Field    string      `json:"field"`
	OldValue interface{} `json:"old_value"`
	NewValue interface{} `json:"new_value"`
}

// SystemDiff represents changes to building systems
type SystemDiff struct {
	HVAC       []SystemChange `json:"hvac,omitempty"`
	Electrical []SystemChange `json:"electrical,omitempty"`
	Plumbing   []SystemChange `json:"plumbing,omitempty"`
	Security   []SystemChange `json:"security,omitempty"`
	Fire       []SystemChange `json:"fire,omitempty"`
}

// SystemChange represents a change to a building system
type SystemChange struct {
	Component   string      `json:"component"`
	Parameter   string      `json:"parameter"`
	OldValue    interface{} `json:"old_value"`
	NewValue    interface{} `json:"new_value"`
	Impact      string      `json:"impact"` // low, medium, high
	Description string      `json:"description"`
}

// MetricDiff represents changes to performance metrics
type MetricDiff struct {
	EnergyUsage    *MetricChange `json:"energy_usage,omitempty"`
	OccupancyRate  *MetricChange `json:"occupancy_rate,omitempty"`
	ResponseTime   *MetricChange `json:"response_time,omitempty"`
	CustomMetrics  []MetricChange `json:"custom_metrics,omitempty"`
}

// MetricChange represents a change to a metric
type MetricChange struct {
	Name        string  `json:"name"`
	OldValue    float64 `json:"old_value"`
	NewValue    float64 `json:"new_value"`
	Delta       float64 `json:"delta"`
	PercentChange float64 `json:"percent_change"`
	Unit        string  `json:"unit"`
}

// ComplianceDiff represents changes to compliance status
type ComplianceDiff struct {
	StatusChanges []ComplianceChange `json:"status_changes"`
	NewViolations []string          `json:"new_violations"`
	ResolvedViolations []string     `json:"resolved_violations"`
}

// ComplianceChange represents a compliance status change
type ComplianceChange struct {
	Regulation string `json:"regulation"`
	OldStatus  string `json:"old_status"`
	NewStatus  string `json:"new_status"`
	Details    string `json:"details,omitempty"`
}

// CompareStates compares two building states and returns the differences
func (de *DiffEngine) CompareStates(ctx context.Context, stateAID, stateBID string) (*StateDiff, error) {
	startTime := time.Now()

	// Check cache first
	cached, err := de.getCachedComparison(ctx, stateAID, stateBID)
	if err == nil && cached != nil {
		return cached, nil
	}

	// Fetch both states
	stateA, err := de.manager.GetState(ctx, stateAID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to fetch state A")
	}

	stateB, err := de.manager.GetState(ctx, stateBID)
	if err != nil {
		return nil, errors.Wrap(err, "failed to fetch state B")
	}

	// Ensure states are from the same building
	if stateA.BuildingID != stateB.BuildingID {
		return nil, errors.New("cannot compare states from different buildings")
	}

	// Create diff
	diff := &StateDiff{
		FromStateID: stateAID,
		ToStateID:   stateBID,
		FromVersion: stateA.Version,
		ToVersion:   stateB.Version,
		CalculatedAt: time.Now(),
	}

	// Compare ArxObjects using Merkle trees
	arxDiff, err := de.compareArxObjects(stateA.ArxObjectSnapshot, stateB.ArxObjectSnapshot)
	if err != nil {
		return nil, errors.Wrap(err, "failed to compare ArxObjects")
	}
	diff.ArxObjectChanges = *arxDiff

	// Compare systems
	sysDiff, err := de.compareSystems(stateA.SystemsState, stateB.SystemsState)
	if err != nil {
		return nil, errors.Wrap(err, "failed to compare systems")
	}
	diff.SystemChanges = *sysDiff

	// Compare metrics if available
	if stateA.PerformanceMetrics != nil && stateB.PerformanceMetrics != nil {
		metricDiff, _ := de.compareMetrics(stateA.PerformanceMetrics, stateB.PerformanceMetrics)
		diff.MetricChanges = *metricDiff
	}

	// Compare compliance if available
	if stateA.ComplianceStatus != nil && stateB.ComplianceStatus != nil {
		complianceDiff, _ := de.compareCompliance(stateA.ComplianceStatus, stateB.ComplianceStatus)
		diff.ComplianceChanges = *complianceDiff
	}

	// Calculate summary
	diff.Summary = de.calculateSummary(diff)

	// Calculate processing time
	diff.CalculationTimeMs = int(time.Since(startTime).Milliseconds())

	// Cache the result
	de.cacheComparison(ctx, stateAID, stateBID, diff)

	return diff, nil
}

// CompareWithCurrent compares a historical state with the current building state
func (de *DiffEngine) CompareWithCurrent(ctx context.Context, buildingID, historicalStateID string) (*StateDiff, error) {
	// Capture current state
	currentState, err := de.manager.CaptureState(ctx, buildingID, "main", CaptureOptions{
		Message: "Temporary snapshot for comparison",
	})
	if err != nil {
		return nil, errors.Wrap(err, "failed to capture current state")
	}

	// Compare states
	return de.CompareStates(ctx, historicalStateID, currentState.ID)
}

// GenerateChangeLog generates a human-readable changelog between states
func (de *DiffEngine) GenerateChangeLog(ctx context.Context, diff *StateDiff) string {
	var changelog string

	// Header
	changelog += fmt.Sprintf("# Changes from v%s to v%s\n\n", diff.FromVersion, diff.ToVersion)
	changelog += fmt.Sprintf("Generated: %s\n", diff.CalculatedAt.Format(time.RFC3339))
	changelog += fmt.Sprintf("Total Changes: %d\n\n", diff.Summary.TotalChanges)

	// ArxObject changes
	if len(diff.ArxObjectChanges.Added) > 0 || len(diff.ArxObjectChanges.Modified) > 0 || len(diff.ArxObjectChanges.Removed) > 0 {
		changelog += "## ArxObject Changes\n\n"
		
		if len(diff.ArxObjectChanges.Added) > 0 {
			changelog += fmt.Sprintf("### Added (%d)\n", len(diff.ArxObjectChanges.Added))
			for _, obj := range diff.ArxObjectChanges.Added {
				changelog += fmt.Sprintf("- %s (Type: %s)\n", obj.ID, obj.Type)
			}
			changelog += "\n"
		}

		if len(diff.ArxObjectChanges.Modified) > 0 {
			changelog += fmt.Sprintf("### Modified (%d)\n", len(diff.ArxObjectChanges.Modified))
			for _, obj := range diff.ArxObjectChanges.Modified {
				changelog += fmt.Sprintf("- %s (Type: %s)\n", obj.ID, obj.Type)
				for _, field := range obj.Fields {
					changelog += fmt.Sprintf("  - %s: %v → %v\n", field.Field, field.OldValue, field.NewValue)
				}
			}
			changelog += "\n"
		}

		if len(diff.ArxObjectChanges.Removed) > 0 {
			changelog += fmt.Sprintf("### Removed (%d)\n", len(diff.ArxObjectChanges.Removed))
			for _, obj := range diff.ArxObjectChanges.Removed {
				changelog += fmt.Sprintf("- %s (Type: %s)\n", obj.ID, obj.Type)
			}
			changelog += "\n"
		}
	}

	// System changes
	if hasSystemChanges(&diff.SystemChanges) {
		changelog += "## System Changes\n\n"
		appendSystemChanges(&changelog, "HVAC", diff.SystemChanges.HVAC)
		appendSystemChanges(&changelog, "Electrical", diff.SystemChanges.Electrical)
		appendSystemChanges(&changelog, "Plumbing", diff.SystemChanges.Plumbing)
		appendSystemChanges(&changelog, "Security", diff.SystemChanges.Security)
		appendSystemChanges(&changelog, "Fire", diff.SystemChanges.Fire)
	}

	// Metric changes
	if hasMetricChanges(&diff.MetricChanges) {
		changelog += "## Performance Metric Changes\n\n"
		if diff.MetricChanges.EnergyUsage != nil {
			appendMetricChange(&changelog, diff.MetricChanges.EnergyUsage)
		}
		if diff.MetricChanges.OccupancyRate != nil {
			appendMetricChange(&changelog, diff.MetricChanges.OccupancyRate)
		}
		if diff.MetricChanges.ResponseTime != nil {
			appendMetricChange(&changelog, diff.MetricChanges.ResponseTime)
		}
	}

	// Compliance changes
	if hasComplianceChanges(&diff.ComplianceChanges) {
		changelog += "## Compliance Changes\n\n"
		for _, change := range diff.ComplianceChanges.StatusChanges {
			changelog += fmt.Sprintf("- %s: %s → %s\n", change.Regulation, change.OldStatus, change.NewStatus)
		}
		if len(diff.ComplianceChanges.NewViolations) > 0 {
			changelog += fmt.Sprintf("\n### New Violations: %v\n", diff.ComplianceChanges.NewViolations)
		}
		if len(diff.ComplianceChanges.ResolvedViolations) > 0 {
			changelog += fmt.Sprintf("### Resolved Violations: %v\n", diff.ComplianceChanges.ResolvedViolations)
		}
	}

	return changelog
}

// Helper methods

func (de *DiffEngine) compareArxObjects(snapshotA, snapshotB json.RawMessage) (*ArxObjectDiff, error) {
	// Build Merkle trees
	treeA, err := BuildFromSnapshot(snapshotA)
	if err != nil {
		return nil, err
	}

	treeB, err := BuildFromSnapshot(snapshotB)
	if err != nil {
		return nil, err
	}

	// Compare trees
	treeDiff, err := treeA.Compare(treeB)
	if err != nil {
		return nil, err
	}

	// Convert tree diff to ArxObject diff
	arxDiff := &ArxObjectDiff{
		Added:    make([]ArxObjectChange, 0),
		Modified: make([]ArxObjectChange, 0),
		Removed:  make([]ArxObjectChange, 0),
	}

	// Parse snapshots for detailed comparison
	var objectsA, objectsB []map[string]interface{}
	json.Unmarshal(snapshotA, &objectsA)
	json.Unmarshal(snapshotB, &objectsB)

	// Create maps for lookup
	mapA := make(map[string]map[string]interface{})
	mapB := make(map[string]map[string]interface{})

	for _, obj := range objectsA {
		if id, ok := obj["id"].(string); ok {
			mapA[id] = obj
		}
	}

	for _, obj := range objectsB {
		if id, ok := obj["id"].(string); ok {
			mapB[id] = obj
		}
	}

	// Process additions
	for _, id := range treeDiff.Added {
		if obj, exists := mapB[id]; exists {
			after, _ := json.Marshal(obj)
			arxDiff.Added = append(arxDiff.Added, ArxObjectChange{
				ID:         id,
				Type:       fmt.Sprintf("%v", obj["type"]),
				ChangeType: "added",
				After:      after,
			})
		}
	}

	// Process modifications
	for _, id := range treeDiff.Modified {
		objA := mapA[id]
		objB := mapB[id]
		before, _ := json.Marshal(objA)
		after, _ := json.Marshal(objB)
		
		change := ArxObjectChange{
			ID:         id,
			Type:       fmt.Sprintf("%v", objB["type"]),
			ChangeType: "modified",
			Before:     before,
			After:      after,
			Fields:     compareFields(objA, objB),
		}
		arxDiff.Modified = append(arxDiff.Modified, change)
	}

	// Process removals
	for _, id := range treeDiff.Removed {
		if obj, exists := mapA[id]; exists {
			before, _ := json.Marshal(obj)
			arxDiff.Removed = append(arxDiff.Removed, ArxObjectChange{
				ID:         id,
				Type:       fmt.Sprintf("%v", obj["type"]),
				ChangeType: "removed",
				Before:     before,
			})
		}
	}

	return arxDiff, nil
}

func (de *DiffEngine) compareSystems(stateA, stateB json.RawMessage) (*SystemDiff, error) {
	var sysA, sysB map[string]interface{}
	json.Unmarshal(stateA, &sysA)
	json.Unmarshal(stateB, &sysB)

	diff := &SystemDiff{
		HVAC:       make([]SystemChange, 0),
		Electrical: make([]SystemChange, 0),
		Plumbing:   make([]SystemChange, 0),
		Security:   make([]SystemChange, 0),
		Fire:       make([]SystemChange, 0),
	}

	// Compare each system
	compareSystemCategory(sysA, sysB, "hvac", &diff.HVAC)
	compareSystemCategory(sysA, sysB, "electrical", &diff.Electrical)
	compareSystemCategory(sysA, sysB, "plumbing", &diff.Plumbing)
	compareSystemCategory(sysA, sysB, "security", &diff.Security)
	compareSystemCategory(sysA, sysB, "fire", &diff.Fire)

	return diff, nil
}

func (de *DiffEngine) compareMetrics(metricsA, metricsB json.RawMessage) (*MetricDiff, error) {
	var mA, mB map[string]interface{}
	json.Unmarshal(metricsA, &mA)
	json.Unmarshal(metricsB, &mB)

	diff := &MetricDiff{}

	// Compare standard metrics
	if energy, ok := compareMetricValue(mA, mB, "energy_usage_kwh"); ok {
		diff.EnergyUsage = energy
	}

	if occupancy, ok := compareMetricValue(mA, mB, "occupancy_rate"); ok {
		diff.OccupancyRate = occupancy
	}

	if response, ok := compareMetricValue(mA, mB, "response_time_ms"); ok {
		diff.ResponseTime = response
	}

	return diff, nil
}

func (de *DiffEngine) compareCompliance(complianceA, complianceB json.RawMessage) (*ComplianceDiff, error) {
	var cA, cB map[string]interface{}
	json.Unmarshal(complianceA, &cA)
	json.Unmarshal(complianceB, &cB)

	diff := &ComplianceDiff{
		StatusChanges:      make([]ComplianceChange, 0),
		NewViolations:      make([]string, 0),
		ResolvedViolations: make([]string, 0),
	}

	// Compare compliance statuses
	for reg, statusA := range cA {
		if statusB, exists := cB[reg]; exists {
			if statusA != statusB {
				diff.StatusChanges = append(diff.StatusChanges, ComplianceChange{
					Regulation: reg,
					OldStatus:  fmt.Sprintf("%v", statusA),
					NewStatus:  fmt.Sprintf("%v", statusB),
				})
			}
		}
	}

	return diff, nil
}

func (de *DiffEngine) calculateSummary(diff *StateDiff) DiffSummary {
	summary := DiffSummary{
		ArxObjectsAdded:    len(diff.ArxObjectChanges.Added),
		ArxObjectsModified: len(diff.ArxObjectChanges.Modified),
		ArxObjectsRemoved:  len(diff.ArxObjectChanges.Removed),
		SystemsChanged:     make([]string, 0),
	}

	// Calculate total changes
	summary.TotalChanges = summary.ArxObjectsAdded + summary.ArxObjectsModified + summary.ArxObjectsRemoved

	// Identify changed systems
	if len(diff.SystemChanges.HVAC) > 0 {
		summary.SystemsChanged = append(summary.SystemsChanged, "HVAC")
	}
	if len(diff.SystemChanges.Electrical) > 0 {
		summary.SystemsChanged = append(summary.SystemsChanged, "Electrical")
	}
	if len(diff.SystemChanges.Plumbing) > 0 {
		summary.SystemsChanged = append(summary.SystemsChanged, "Plumbing")
	}
	if len(diff.SystemChanges.Security) > 0 {
		summary.SystemsChanged = append(summary.SystemsChanged, "Security")
	}
	if len(diff.SystemChanges.Fire) > 0 {
		summary.SystemsChanged = append(summary.SystemsChanged, "Fire")
	}

	// Determine severity level
	if summary.TotalChanges == 0 {
		summary.SeverityLevel = "none"
	} else if summary.TotalChanges < 10 {
		summary.SeverityLevel = "minor"
	} else if summary.TotalChanges < 50 {
		summary.SeverityLevel = "moderate"
	} else {
		summary.SeverityLevel = "major"
	}

	return summary
}

func (de *DiffEngine) getCachedComparison(ctx context.Context, stateAID, stateBID string) (*StateDiff, error) {
	var cached struct {
		DiffSummary json.RawMessage `db:"diff_summary"`
	}

	err := de.db.GetContext(ctx, &cached, `
		SELECT diff_summary FROM state_comparisons
		WHERE (state_a_id = $1 AND state_b_id = $2) OR (state_a_id = $2 AND state_b_id = $1)
		ORDER BY last_accessed_at DESC
		LIMIT 1
	`, stateAID, stateBID)

	if err != nil {
		return nil, err
	}

	var diff StateDiff
	if err := json.Unmarshal(cached.DiffSummary, &diff); err != nil {
		return nil, err
	}

	// Update access count and time
	de.db.ExecContext(ctx, `
		UPDATE state_comparisons 
		SET accessed_count = accessed_count + 1, last_accessed_at = NOW()
		WHERE (state_a_id = $1 AND state_b_id = $2) OR (state_a_id = $2 AND state_b_id = $1)
	`, stateAID, stateBID)

	return &diff, nil
}

func (de *DiffEngine) cacheComparison(ctx context.Context, stateAID, stateBID string, diff *StateDiff) error {
	diffJSON, err := json.Marshal(diff)
	if err != nil {
		return err
	}

	_, err = de.db.ExecContext(ctx, `
		INSERT INTO state_comparisons (
			id, state_a_id, state_b_id, diff_summary,
			arxobjects_added, arxobjects_modified, arxobjects_removed,
			systems_changed, comparison_time_ms, created_at, last_accessed_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10
		) ON CONFLICT (state_a_id, state_b_id) DO UPDATE
		SET diff_summary = $4, last_accessed_at = $10
	`, uuid.New().String(), stateAID, stateBID, diffJSON,
		diff.Summary.ArxObjectsAdded, diff.Summary.ArxObjectsModified, diff.Summary.ArxObjectsRemoved,
		diff.Summary.SystemsChanged, diff.CalculationTimeMs, time.Now())

	return err
}

// Helper functions

func compareFields(objA, objB map[string]interface{}) []FieldChange {
	changes := make([]FieldChange, 0)

	// Check all fields in objB
	for field, valueB := range objB {
		if valueA, exists := objA[field]; exists {
			if !equalValues(valueA, valueB) {
				changes = append(changes, FieldChange{
					Field:    field,
					OldValue: valueA,
					NewValue: valueB,
				})
			}
		} else {
			changes = append(changes, FieldChange{
				Field:    field,
				OldValue: nil,
				NewValue: valueB,
			})
		}
	}

	// Check for removed fields
	for field, valueA := range objA {
		if _, exists := objB[field]; !exists {
			changes = append(changes, FieldChange{
				Field:    field,
				OldValue: valueA,
				NewValue: nil,
			})
		}
	}

	return changes
}

func equalValues(a, b interface{}) bool {
	// Simple equality check - could be enhanced
	return fmt.Sprintf("%v", a) == fmt.Sprintf("%v", b)
}

func compareSystemCategory(sysA, sysB map[string]interface{}, category string, changes *[]SystemChange) {
	catA, okA := sysA[category].(map[string]interface{})
	catB, okB := sysB[category].(map[string]interface{})

	if !okA || !okB {
		return
	}

	for param, valueB := range catB {
		if valueA, exists := catA[param]; exists {
			if !equalValues(valueA, valueB) {
				*changes = append(*changes, SystemChange{
					Component: category,
					Parameter: param,
					OldValue:  valueA,
					NewValue:  valueB,
					Impact:    determineImpact(param, valueA, valueB),
				})
			}
		}
	}
}

func compareMetricValue(mA, mB map[string]interface{}, metric string) (*MetricChange, bool) {
	valueA, okA := mA[metric].(float64)
	valueB, okB := mB[metric].(float64)

	if !okA || !okB {
		return nil, false
	}

	if valueA == valueB {
		return nil, false
	}

	delta := valueB - valueA
	percentChange := (delta / valueA) * 100

	return &MetricChange{
		Name:          metric,
		OldValue:      valueA,
		NewValue:      valueB,
		Delta:         delta,
		PercentChange: percentChange,
	}, true
}

func determineImpact(param string, oldValue, newValue interface{}) string {
	// Simplified impact determination
	// In production, would have more sophisticated logic
	if param == "status" {
		return "high"
	}
	return "medium"
}

func hasSystemChanges(sd *SystemDiff) bool {
	return len(sd.HVAC) > 0 || len(sd.Electrical) > 0 || len(sd.Plumbing) > 0 ||
		len(sd.Security) > 0 || len(sd.Fire) > 0
}

func hasMetricChanges(md *MetricDiff) bool {
	return md.EnergyUsage != nil || md.OccupancyRate != nil || md.ResponseTime != nil ||
		len(md.CustomMetrics) > 0
}

func hasComplianceChanges(cd *ComplianceDiff) bool {
	return len(cd.StatusChanges) > 0 || len(cd.NewViolations) > 0 || len(cd.ResolvedViolations) > 0
}

func appendSystemChanges(changelog *string, system string, changes []SystemChange) {
	if len(changes) > 0 {
		*changelog += fmt.Sprintf("### %s\n", system)
		for _, change := range changes {
			*changelog += fmt.Sprintf("- %s: %v → %v (Impact: %s)\n",
				change.Parameter, change.OldValue, change.NewValue, change.Impact)
		}
		*changelog += "\n"
	}
}

func appendMetricChange(changelog *string, metric *MetricChange) {
	*changelog += fmt.Sprintf("- %s: %.2f → %.2f (%.1f%% change)\n",
		metric.Name, metric.OldValue, metric.NewValue, metric.PercentChange)
}