package gitops

import (
	"context"
	"encoding/json"
	"fmt"
	"html"
	"strings"

	"github.com/arxos/arxos/core/internal/state"
)

// DiffViewer generates visual diffs for building states
type DiffViewer struct {
	stateManager *state.Manager
}

// NewDiffViewer creates a new diff viewer
func NewDiffViewer(stateManager *state.Manager) *DiffViewer {
	return &DiffViewer{
		stateManager: stateManager,
	}
}

// DiffResult represents the result of a diff operation
type DiffResult struct {
	Summary    DiffSummary    `json:"summary"`
	Objects    []ObjectDiff   `json:"objects"`
	Systems    []SystemDiff   `json:"systems"`
	Properties []PropertyDiff `json:"properties"`
	HTML       string         `json:"html,omitempty"`
}

// DiffSummary provides a high-level overview of changes
type DiffSummary struct {
	ObjectsAdded     int `json:"objects_added"`
	ObjectsModified  int `json:"objects_modified"`
	ObjectsRemoved   int `json:"objects_removed"`
	SystemsChanged   int `json:"systems_changed"`
	PropertiesChanged int `json:"properties_changed"`
	TotalChanges     int `json:"total_changes"`
}

// ObjectDiff represents a difference in an ArxObject
type ObjectDiff struct {
	ID         string      `json:"id"`
	Type       string      `json:"type"` // added, modified, removed
	ObjectType string      `json:"object_type"`
	OldValue   interface{} `json:"old_value,omitempty"`
	NewValue   interface{} `json:"new_value,omitempty"`
	Changes    []FieldDiff `json:"changes,omitempty"`
}

// SystemDiff represents a difference in a system configuration
type SystemDiff struct {
	SystemID string      `json:"system_id"`
	Type     string      `json:"type"` // added, modified, removed
	OldValue interface{} `json:"old_value,omitempty"`
	NewValue interface{} `json:"new_value,omitempty"`
	Changes  []FieldDiff `json:"changes,omitempty"`
}

// PropertyDiff represents a difference in building properties
type PropertyDiff struct {
	Key      string      `json:"key"`
	Type     string      `json:"type"` // added, modified, removed
	OldValue interface{} `json:"old_value,omitempty"`
	NewValue interface{} `json:"new_value,omitempty"`
}

// FieldDiff represents a difference in a specific field
type FieldDiff struct {
	Field    string      `json:"field"`
	Path     string      `json:"path"`
	OldValue interface{} `json:"old_value"`
	NewValue interface{} `json:"new_value"`
}

// GenerateDiff generates a diff between two building states
func (dv *DiffViewer) GenerateDiff(ctx context.Context, oldStateID, newStateID string) (*DiffResult, error) {
	// Get states
	oldState, err := dv.stateManager.GetState(ctx, oldStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get old state: %w", err)
	}

	newState, err := dv.stateManager.GetState(ctx, newStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get new state: %w", err)
	}

	// Parse snapshots
	var oldObjects, newObjects map[string]interface{}
	if err := json.Unmarshal(oldState.ArxObjectSnapshot, &oldObjects); err != nil {
		return nil, fmt.Errorf("failed to parse old objects: %w", err)
	}
	if err := json.Unmarshal(newState.ArxObjectSnapshot, &newObjects); err != nil {
		return nil, fmt.Errorf("failed to parse new objects: %w", err)
	}

	var oldSystems, newSystems map[string]interface{}
	if err := json.Unmarshal(oldState.SystemsState, &oldSystems); err != nil {
		return nil, fmt.Errorf("failed to parse old systems: %w", err)
	}
	if err := json.Unmarshal(newState.SystemsState, &newSystems); err != nil {
		return nil, fmt.Errorf("failed to parse new systems: %w", err)
	}

	// Generate diffs
	objectDiffs := dv.diffObjects(oldObjects, newObjects)
	systemDiffs := dv.diffSystems(oldSystems, newSystems)
	propertyDiffs := dv.diffProperties(oldState.Metadata, newState.Metadata)

	// Create summary
	summary := DiffSummary{
		ObjectsAdded:     countByType(objectDiffs, "added"),
		ObjectsModified:  countByType(objectDiffs, "modified"),
		ObjectsRemoved:   countByType(objectDiffs, "removed"),
		SystemsChanged:   len(systemDiffs),
		PropertiesChanged: len(propertyDiffs),
	}
	summary.TotalChanges = summary.ObjectsAdded + summary.ObjectsModified + 
		summary.ObjectsRemoved + summary.SystemsChanged + summary.PropertiesChanged

	result := &DiffResult{
		Summary:    summary,
		Objects:    objectDiffs,
		Systems:    systemDiffs,
		Properties: propertyDiffs,
	}

	// Generate HTML view
	result.HTML = dv.generateHTMLDiff(result)

	return result, nil
}

// diffObjects compares ArxObjects between states
func (dv *DiffViewer) diffObjects(oldObjs, newObjs map[string]interface{}) []ObjectDiff {
	diffs := []ObjectDiff{}

	// Check for added and modified objects
	for id, newObj := range newObjs {
		oldObj, exists := oldObjs[id]
		
		if !exists {
			// Object added
			diffs = append(diffs, ObjectDiff{
				ID:         id,
				Type:       "added",
				ObjectType: extractObjectType(newObj),
				NewValue:   newObj,
			})
		} else if !dv.objectsEqual(oldObj, newObj) {
			// Object modified
			changes := dv.findFieldDiffs(oldObj, newObj, "")
			diffs = append(diffs, ObjectDiff{
				ID:         id,
				Type:       "modified",
				ObjectType: extractObjectType(newObj),
				OldValue:   oldObj,
				NewValue:   newObj,
				Changes:    changes,
			})
		}
	}

	// Check for removed objects
	for id, oldObj := range oldObjs {
		if _, exists := newObjs[id]; !exists {
			diffs = append(diffs, ObjectDiff{
				ID:         id,
				Type:       "removed",
				ObjectType: extractObjectType(oldObj),
				OldValue:   oldObj,
			})
		}
	}

	return diffs
}

// diffSystems compares system configurations
func (dv *DiffViewer) diffSystems(oldSys, newSys map[string]interface{}) []SystemDiff {
	diffs := []SystemDiff{}

	// Check all systems
	allSystems := make(map[string]bool)
	for id := range oldSys {
		allSystems[id] = true
	}
	for id := range newSys {
		allSystems[id] = true
	}

	for sysID := range allSystems {
		oldConfig, oldExists := oldSys[sysID]
		newConfig, newExists := newSys[sysID]

		if !oldExists && newExists {
			// System added
			diffs = append(diffs, SystemDiff{
				SystemID: sysID,
				Type:     "added",
				NewValue: newConfig,
			})
		} else if oldExists && !newExists {
			// System removed
			diffs = append(diffs, SystemDiff{
				SystemID: sysID,
				Type:     "removed",
				OldValue: oldConfig,
			})
		} else if !dv.objectsEqual(oldConfig, newConfig) {
			// System modified
			changes := dv.findFieldDiffs(oldConfig, newConfig, "")
			diffs = append(diffs, SystemDiff{
				SystemID: sysID,
				Type:     "modified",
				OldValue: oldConfig,
				NewValue: newConfig,
				Changes:  changes,
			})
		}
	}

	return diffs
}

// diffProperties compares metadata properties
func (dv *DiffViewer) diffProperties(oldMeta, newMeta map[string]interface{}) []PropertyDiff {
	diffs := []PropertyDiff{}

	// Check all properties
	allKeys := make(map[string]bool)
	for key := range oldMeta {
		allKeys[key] = true
	}
	for key := range newMeta {
		allKeys[key] = true
	}

	for key := range allKeys {
		oldVal, oldExists := oldMeta[key]
		newVal, newExists := newMeta[key]

		if !oldExists && newExists {
			diffs = append(diffs, PropertyDiff{
				Key:      key,
				Type:     "added",
				NewValue: newVal,
			})
		} else if oldExists && !newExists {
			diffs = append(diffs, PropertyDiff{
				Key:      key,
				Type:     "removed",
				OldValue: oldVal,
			})
		} else if !dv.valuesEqual(oldVal, newVal) {
			diffs = append(diffs, PropertyDiff{
				Key:      key,
				Type:     "modified",
				OldValue: oldVal,
				NewValue: newVal,
			})
		}
	}

	return diffs
}

// findFieldDiffs recursively finds differences between two objects
func (dv *DiffViewer) findFieldDiffs(oldObj, newObj interface{}, path string) []FieldDiff {
	diffs := []FieldDiff{}

	oldMap, oldIsMap := oldObj.(map[string]interface{})
	newMap, newIsMap := newObj.(map[string]interface{})

	if !oldIsMap || !newIsMap {
		if !dv.valuesEqual(oldObj, newObj) {
			diffs = append(diffs, FieldDiff{
				Field:    extractFieldName(path),
				Path:     path,
				OldValue: oldObj,
				NewValue: newObj,
			})
		}
		return diffs
	}

	// Compare maps
	allKeys := make(map[string]bool)
	for key := range oldMap {
		allKeys[key] = true
	}
	for key := range newMap {
		allKeys[key] = true
	}

	for key := range allKeys {
		fieldPath := path
		if fieldPath != "" {
			fieldPath += "."
		}
		fieldPath += key

		oldVal, oldExists := oldMap[key]
		newVal, newExists := newMap[key]

		if !oldExists {
			diffs = append(diffs, FieldDiff{
				Field:    key,
				Path:     fieldPath,
				OldValue: nil,
				NewValue: newVal,
			})
		} else if !newExists {
			diffs = append(diffs, FieldDiff{
				Field:    key,
				Path:     fieldPath,
				OldValue: oldVal,
				NewValue: nil,
			})
		} else {
			// Recursively check nested differences
			nestedDiffs := dv.findFieldDiffs(oldVal, newVal, fieldPath)
			diffs = append(diffs, nestedDiffs...)
		}
	}

	return diffs
}

// generateHTMLDiff generates an HTML representation of the diff
func (dv *DiffViewer) generateHTMLDiff(diff *DiffResult) string {
	var sb strings.Builder

	// Start HTML
	sb.WriteString(`<div class="diff-viewer">`)
	
	// Summary section
	sb.WriteString(`<div class="diff-summary">`)
	sb.WriteString(`<h3>Changes Summary</h3>`)
	sb.WriteString(`<div class="summary-stats">`)
	if diff.Summary.ObjectsAdded > 0 {
		sb.WriteString(fmt.Sprintf(`<span class="added">+%d objects</span>`, diff.Summary.ObjectsAdded))
	}
	if diff.Summary.ObjectsModified > 0 {
		sb.WriteString(fmt.Sprintf(`<span class="modified">~%d objects</span>`, diff.Summary.ObjectsModified))
	}
	if diff.Summary.ObjectsRemoved > 0 {
		sb.WriteString(fmt.Sprintf(`<span class="removed">-%d objects</span>`, diff.Summary.ObjectsRemoved))
	}
	if diff.Summary.SystemsChanged > 0 {
		sb.WriteString(fmt.Sprintf(`<span class="systems">%d systems</span>`, diff.Summary.SystemsChanged))
	}
	sb.WriteString(`</div></div>`)

	// Object changes
	if len(diff.Objects) > 0 {
		sb.WriteString(`<div class="diff-section">`)
		sb.WriteString(`<h4>Object Changes</h4>`)
		for _, obj := range diff.Objects {
			sb.WriteString(dv.renderObjectDiff(obj))
		}
		sb.WriteString(`</div>`)
	}

	// System changes
	if len(diff.Systems) > 0 {
		sb.WriteString(`<div class="diff-section">`)
		sb.WriteString(`<h4>System Changes</h4>`)
		for _, sys := range diff.Systems {
			sb.WriteString(dv.renderSystemDiff(sys))
		}
		sb.WriteString(`</div>`)
	}

	// Property changes
	if len(diff.Properties) > 0 {
		sb.WriteString(`<div class="diff-section">`)
		sb.WriteString(`<h4>Property Changes</h4>`)
		for _, prop := range diff.Properties {
			sb.WriteString(dv.renderPropertyDiff(prop))
		}
		sb.WriteString(`</div>`)
	}

	sb.WriteString(`</div>`)
	
	// Add CSS
	sb.WriteString(dv.getDiffCSS())

	return sb.String()
}

// renderObjectDiff renders a single object diff as HTML
func (dv *DiffViewer) renderObjectDiff(diff ObjectDiff) string {
	class := "diff-item " + diff.Type
	icon := getChangeIcon(diff.Type)
	
	var details string
	if diff.Type == "modified" && len(diff.Changes) > 0 {
		details = `<div class="diff-details">`
		for _, change := range diff.Changes {
			details += fmt.Sprintf(`<div class="field-change">
				<span class="field-name">%s:</span>
				<span class="old-value">%v</span>
				<span class="arrow">→</span>
				<span class="new-value">%v</span>
			</div>`, html.EscapeString(change.Field), 
				formatValue(change.OldValue), formatValue(change.NewValue))
		}
		details += `</div>`
	}

	return fmt.Sprintf(`<div class="%s">
		<div class="diff-header">
			<span class="icon">%s</span>
			<span class="object-id">%s</span>
			<span class="object-type">(%s)</span>
		</div>
		%s
	</div>`, class, icon, html.EscapeString(diff.ID), 
		html.EscapeString(diff.ObjectType), details)
}

// renderSystemDiff renders a system diff as HTML
func (dv *DiffViewer) renderSystemDiff(diff SystemDiff) string {
	class := "diff-item " + diff.Type
	icon := getChangeIcon(diff.Type)
	
	return fmt.Sprintf(`<div class="%s">
		<div class="diff-header">
			<span class="icon">%s</span>
			<span class="system-id">%s</span>
		</div>
	</div>`, class, icon, html.EscapeString(diff.SystemID))
}

// renderPropertyDiff renders a property diff as HTML
func (dv *DiffViewer) renderPropertyDiff(diff PropertyDiff) string {
	class := "diff-item property " + diff.Type
	icon := getChangeIcon(diff.Type)
	
	var valueDisplay string
	switch diff.Type {
	case "added":
		valueDisplay = fmt.Sprintf(`<span class="new-value">%v</span>`, formatValue(diff.NewValue))
	case "removed":
		valueDisplay = fmt.Sprintf(`<span class="old-value">%v</span>`, formatValue(diff.OldValue))
	case "modified":
		valueDisplay = fmt.Sprintf(`<span class="old-value">%v</span>
			<span class="arrow">→</span>
			<span class="new-value">%v</span>`, 
			formatValue(diff.OldValue), formatValue(diff.NewValue))
	}
	
	return fmt.Sprintf(`<div class="%s">
		<span class="icon">%s</span>
		<span class="property-key">%s:</span>
		%s
	</div>`, class, icon, html.EscapeString(diff.Key), valueDisplay)
}

// getDiffCSS returns CSS for styling the diff
func (dv *DiffViewer) getDiffCSS() string {
	return `<style>
		.diff-viewer { font-family: monospace; }
		.diff-summary { 
			background: #f5f5f5; 
			padding: 10px; 
			margin-bottom: 20px;
			border-radius: 4px;
		}
		.summary-stats span { 
			margin-right: 15px; 
			padding: 2px 8px;
			border-radius: 3px;
		}
		.summary-stats .added { background: #d4f4dd; color: #22863a; }
		.summary-stats .modified { background: #fff5b1; color: #735c0f; }
		.summary-stats .removed { background: #ffeef0; color: #d73a49; }
		.summary-stats .systems { background: #e1f5ff; color: #0366d6; }
		
		.diff-section { margin-bottom: 20px; }
		.diff-section h4 { 
			margin: 10px 0;
			padding-bottom: 5px;
			border-bottom: 1px solid #ddd;
		}
		
		.diff-item { 
			margin: 5px 0; 
			padding: 5px;
			border-left: 3px solid #ddd;
		}
		.diff-item.added { 
			background: #f0fff4; 
			border-color: #28a745;
		}
		.diff-item.modified { 
			background: #fffbdd; 
			border-color: #ffc107;
		}
		.diff-item.removed { 
			background: #ffebe9; 
			border-color: #dc3545;
		}
		
		.diff-header { font-weight: bold; }
		.icon { margin-right: 5px; }
		.object-type { 
			color: #666; 
			font-size: 0.9em;
			margin-left: 5px;
		}
		
		.diff-details { 
			margin-top: 5px;
			padding-left: 20px;
			font-size: 0.9em;
		}
		.field-change { margin: 2px 0; }
		.field-name { 
			color: #0366d6;
			margin-right: 5px;
		}
		.old-value { 
			color: #d73a49;
			text-decoration: line-through;
		}
		.new-value { color: #22863a; }
		.arrow { 
			margin: 0 5px;
			color: #666;
		}
	</style>`
}

// Helper functions

func (dv *DiffViewer) objectsEqual(a, b interface{}) bool {
	aJSON, _ := json.Marshal(a)
	bJSON, _ := json.Marshal(b)
	return string(aJSON) == string(bJSON)
}

func (dv *DiffViewer) valuesEqual(a, b interface{}) bool {
	return fmt.Sprintf("%v", a) == fmt.Sprintf("%v", b)
}

func extractObjectType(obj interface{}) string {
	if m, ok := obj.(map[string]interface{}); ok {
		if objType, exists := m["type"]; exists {
			return fmt.Sprintf("%v", objType)
		}
	}
	return "unknown"
}

func extractFieldName(path string) string {
	parts := strings.Split(path, ".")
	if len(parts) > 0 {
		return parts[len(parts)-1]
	}
	return path
}

func countByType(diffs []ObjectDiff, diffType string) int {
	count := 0
	for _, d := range diffs {
		if d.Type == diffType {
			count++
		}
	}
	return count
}

func getChangeIcon(changeType string) string {
	switch changeType {
	case "added":
		return "+"
	case "modified":
		return "~"
	case "removed":
		return "-"
	default:
		return "?"
	}
}

func formatValue(v interface{}) string {
	if v == nil {
		return "null"
	}
	
	// Truncate long values
	str := fmt.Sprintf("%v", v)
	if len(str) > 50 {
		return html.EscapeString(str[:47] + "...")
	}
	return html.EscapeString(str)
}