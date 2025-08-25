package gitops

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arxos/arxos/core/internal/state"
	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
)

// MergeEngine handles merging branches and detecting conflicts
type MergeEngine struct {
	db           *sqlx.DB
	stateManager *state.Manager
	branchMgr    *BranchManager
}

// NewMergeEngine creates a new merge engine
func NewMergeEngine(db *sqlx.DB, stateManager *state.Manager, branchMgr *BranchManager) *MergeEngine {
	return &MergeEngine{
		db:           db,
		stateManager: stateManager,
		branchMgr:    branchMgr,
	}
}

// MergeRequest represents a merge operation request
type MergeRequest struct {
	BuildingID   string
	SourceBranch string
	TargetBranch string
	Strategy     MergeStrategy
	Author       string
	Message      string
	DryRun       bool
}

// MergeStrategy defines how to handle conflicts
type MergeStrategy string

const (
	MergeStrategyFastForward MergeStrategy = "fast-forward"
	MergeStrategyMerge       MergeStrategy = "merge"
	MergeStrategySquash      MergeStrategy = "squash"
	MergeStrategyRebase      MergeStrategy = "rebase"
)

// MergeResult contains the result of a merge operation
type MergeResult struct {
	Success      bool
	MergeStateID string
	Conflicts    []Conflict
	Changes      []Change
	Strategy     MergeStrategy
}

// Conflict represents a merge conflict
type Conflict struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"`
	ObjectID     string                 `json:"object_id"`
	Path         string                 `json:"path"`
	BaseValue    interface{}            `json:"base_value"`
	SourceValue  interface{}            `json:"source_value"`
	TargetValue  interface{}            `json:"target_value"`
	Description  string                 `json:"description"`
	Resolvable   bool                   `json:"resolvable"`
	Resolution   *ConflictResolution    `json:"resolution,omitempty"`
}

// ConflictResolution represents how a conflict was resolved
type ConflictResolution struct {
	Strategy      string      `json:"strategy"`
	ResolvedValue interface{} `json:"resolved_value"`
	ResolvedBy    string      `json:"resolved_by"`
	ResolvedAt    time.Time   `json:"resolved_at"`
}

// Change represents a change in the merge
type Change struct {
	Type        string      `json:"type"`
	ObjectID    string      `json:"object_id"`
	Path        string      `json:"path"`
	OldValue    interface{} `json:"old_value"`
	NewValue    interface{} `json:"new_value"`
	Description string      `json:"description"`
}

// Merge performs a merge operation
func (me *MergeEngine) Merge(ctx context.Context, req *MergeRequest) (*MergeResult, error) {
	// Get branches
	sourceBranch, err := me.branchMgr.GetBranch(ctx, req.BuildingID, req.SourceBranch)
	if err != nil {
		return nil, fmt.Errorf("failed to get source branch: %w", err)
	}

	targetBranch, err := me.branchMgr.GetBranch(ctx, req.BuildingID, req.TargetBranch)
	if err != nil {
		return nil, fmt.Errorf("failed to get target branch: %w", err)
	}

	// Find common ancestor
	baseStateID, err := me.findCommonAncestor(ctx, sourceBranch.HeadStateID, targetBranch.HeadStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to find common ancestor: %w", err)
	}

	// Get states
	baseState, err := me.stateManager.GetState(ctx, baseStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get base state: %w", err)
	}

	sourceState, err := me.stateManager.GetState(ctx, sourceBranch.HeadStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get source state: %w", err)
	}

	targetState, err := me.stateManager.GetState(ctx, targetBranch.HeadStateID)
	if err != nil {
		return nil, fmt.Errorf("failed to get target state: %w", err)
	}

	// Check if fast-forward is possible
	if req.Strategy == MergeStrategyFastForward {
		canFF, err := me.canFastForward(ctx, targetBranch.HeadStateID, sourceBranch.HeadStateID)
		if err != nil {
			return nil, fmt.Errorf("failed to check fast-forward: %w", err)
		}
		if !canFF {
			return &MergeResult{
				Success: false,
				Conflicts: []Conflict{{
					Type:        "strategy",
					Description: "Fast-forward not possible - branches have diverged",
				}},
			}, nil
		}
	}

	// Perform three-way merge
	conflicts, changes, err := me.threeWayMerge(baseState, sourceState, targetState)
	if err != nil {
		return nil, fmt.Errorf("three-way merge failed: %w", err)
	}

	// If dry run, return result without creating state
	if req.DryRun {
		return &MergeResult{
			Success:   len(conflicts) == 0,
			Conflicts: conflicts,
			Changes:   changes,
			Strategy:  req.Strategy,
		}, nil
	}

	// If no conflicts, create merged state
	if len(conflicts) == 0 {
		mergedState, err := me.createMergedState(ctx, req, sourceState, targetState, changes)
		if err != nil {
			return nil, fmt.Errorf("failed to create merged state: %w", err)
		}

		// Update target branch
		if err := me.branchMgr.UpdateBranch(ctx, req.BuildingID, req.TargetBranch, map[string]interface{}{
			"head_state_id": mergedState.ID,
			"updated_at":    time.Now(),
		}); err != nil {
			return nil, fmt.Errorf("failed to update target branch: %w", err)
		}

		return &MergeResult{
			Success:      true,
			MergeStateID: mergedState.ID,
			Changes:      changes,
			Strategy:     req.Strategy,
		}, nil
	}

	return &MergeResult{
		Success:   false,
		Conflicts: conflicts,
		Changes:   changes,
		Strategy:  req.Strategy,
	}, nil
}

// threeWayMerge performs a three-way merge and detects conflicts
func (me *MergeEngine) threeWayMerge(base, source, target *state.BuildingState) ([]Conflict, []Change, error) {
	conflicts := []Conflict{}
	changes := []Change{}

	// Unmarshal snapshots
	var baseData, sourceData, targetData map[string]interface{}
	if err := json.Unmarshal(base.ArxObjectSnapshot, &baseData); err != nil {
		return nil, nil, fmt.Errorf("failed to unmarshal base snapshot: %w", err)
	}
	if err := json.Unmarshal(source.ArxObjectSnapshot, &sourceData); err != nil {
		return nil, nil, fmt.Errorf("failed to unmarshal source snapshot: %w", err)
	}
	if err := json.Unmarshal(target.ArxObjectSnapshot, &targetData); err != nil {
		return nil, nil, fmt.Errorf("failed to unmarshal target snapshot: %w", err)
	}

	// Compare ArxObjects
	objectConflicts, objectChanges := me.compareObjects(baseData, sourceData, targetData)
	conflicts = append(conflicts, objectConflicts...)
	changes = append(changes, objectChanges...)

	// Compare systems
	var baseSystemsData, sourceSystemsData, targetSystemsData map[string]interface{}
	if err := json.Unmarshal(base.SystemsState, &baseSystemsData); err != nil {
		return nil, nil, fmt.Errorf("failed to unmarshal base systems: %w", err)
	}
	if err := json.Unmarshal(source.SystemsState, &sourceSystemsData); err != nil {
		return nil, nil, fmt.Errorf("failed to unmarshal source systems: %w", err)
	}
	if err := json.Unmarshal(target.SystemsState, &targetSystemsData); err != nil {
		return nil, nil, fmt.Errorf("failed to unmarshal target systems: %w", err)
	}

	systemConflicts, systemChanges := me.compareSystems(baseSystemsData, sourceSystemsData, targetSystemsData)
	conflicts = append(conflicts, systemConflicts...)
	changes = append(changes, systemChanges...)

	return conflicts, changes, nil
}

// compareObjects compares ArxObject states
func (me *MergeEngine) compareObjects(base, source, target map[string]interface{}) ([]Conflict, []Change) {
	conflicts := []Conflict{}
	changes := []Change{}

	// Get all object IDs
	allIDs := make(map[string]bool)
	for id := range base {
		allIDs[id] = true
	}
	for id := range source {
		allIDs[id] = true
	}
	for id := range target {
		allIDs[id] = true
	}

	// Check each object
	for id := range allIDs {
		baseObj, baseExists := base[id]
		sourceObj, sourceExists := source[id]
		targetObj, targetExists := target[id]

		// Object added in source only
		if !baseExists && sourceExists && !targetExists {
			changes = append(changes, Change{
				Type:        "add",
				ObjectID:    id,
				NewValue:    sourceObj,
				Description: fmt.Sprintf("Object %s added", id),
			})
			continue
		}

		// Object added in target only
		if !baseExists && !sourceExists && targetExists {
			// No change needed, target already has it
			continue
		}

		// Object added in both (conflict)
		if !baseExists && sourceExists && targetExists {
			if !me.objectsEqual(sourceObj, targetObj) {
				conflicts = append(conflicts, Conflict{
					ID:          uuid.New().String(),
					Type:        "add-add",
					ObjectID:    id,
					SourceValue: sourceObj,
					TargetValue: targetObj,
					Description: fmt.Sprintf("Object %s added differently in both branches", id),
					Resolvable:  false,
				})
			}
			continue
		}

		// Object deleted in source only
		if baseExists && !sourceExists && targetExists {
			if me.objectsEqual(baseObj, targetObj) {
				changes = append(changes, Change{
					Type:        "delete",
					ObjectID:    id,
					OldValue:    baseObj,
					Description: fmt.Sprintf("Object %s deleted", id),
				})
			} else {
				conflicts = append(conflicts, Conflict{
					ID:          uuid.New().String(),
					Type:        "delete-modify",
					ObjectID:    id,
					BaseValue:   baseObj,
					TargetValue: targetObj,
					Description: fmt.Sprintf("Object %s deleted in source but modified in target", id),
					Resolvable:  false,
				})
			}
			continue
		}

		// Object deleted in target only
		if baseExists && sourceExists && !targetExists {
			if me.objectsEqual(baseObj, sourceObj) {
				// No change needed, already deleted in target
				continue
			} else {
				conflicts = append(conflicts, Conflict{
					ID:          uuid.New().String(),
					Type:        "modify-delete",
					ObjectID:    id,
					BaseValue:   baseObj,
					SourceValue: sourceObj,
					Description: fmt.Sprintf("Object %s modified in source but deleted in target", id),
					Resolvable:  false,
				})
			}
			continue
		}

		// Object modified
		if baseExists && sourceExists && targetExists {
			sourceModified := !me.objectsEqual(baseObj, sourceObj)
			targetModified := !me.objectsEqual(baseObj, targetObj)

			if sourceModified && !targetModified {
				changes = append(changes, Change{
					Type:        "modify",
					ObjectID:    id,
					OldValue:    baseObj,
					NewValue:    sourceObj,
					Description: fmt.Sprintf("Object %s modified", id),
				})
			} else if sourceModified && targetModified {
				if !me.objectsEqual(sourceObj, targetObj) {
					conflicts = append(conflicts, Conflict{
						ID:          uuid.New().String(),
						Type:        "modify-modify",
						ObjectID:    id,
						BaseValue:   baseObj,
						SourceValue: sourceObj,
						TargetValue: targetObj,
						Description: fmt.Sprintf("Object %s modified differently in both branches", id),
						Resolvable:  false,
					})
				}
			}
		}
	}

	return conflicts, changes
}

// compareSystems compares system states
func (me *MergeEngine) compareSystems(base, source, target map[string]interface{}) ([]Conflict, []Change) {
	// Similar logic to compareObjects but for systems
	// Simplified for brevity - would have system-specific comparison logic
	return []Conflict{}, []Change{}
}

// objectsEqual checks if two objects are equal
func (me *MergeEngine) objectsEqual(a, b interface{}) bool {
	aJSON, _ := json.Marshal(a)
	bJSON, _ := json.Marshal(b)
	return string(aJSON) == string(bJSON)
}

// findCommonAncestor finds the common ancestor of two states
func (me *MergeEngine) findCommonAncestor(ctx context.Context, stateID1, stateID2 string) (string, error) {
	// Build ancestry chain for both states
	ancestors1, err := me.getAncestors(ctx, stateID1)
	if err != nil {
		return "", err
	}

	ancestors2, err := me.getAncestors(ctx, stateID2)
	if err != nil {
		return "", err
	}

	// Find common ancestor
	ancestors2Map := make(map[string]bool)
	for _, id := range ancestors2 {
		ancestors2Map[id] = true
	}

	for _, id := range ancestors1 {
		if ancestors2Map[id] {
			return id, nil
		}
	}

	return "", fmt.Errorf("no common ancestor found")
}

// getAncestors returns the ancestry chain of a state
func (me *MergeEngine) getAncestors(ctx context.Context, stateID string) ([]string, error) {
	ancestors := []string{stateID}
	
	currentID := stateID
	for {
		var parentID *string
		err := me.db.GetContext(ctx, &parentID,
			"SELECT parent_state_id FROM building_states WHERE id = $1",
			currentID)
		if err != nil {
			return nil, err
		}
		
		if parentID == nil {
			break
		}
		
		ancestors = append(ancestors, *parentID)
		currentID = *parentID
	}
	
	return ancestors, nil
}

// canFastForward checks if fast-forward is possible
func (me *MergeEngine) canFastForward(ctx context.Context, targetHead, sourceHead string) (bool, error) {
	// Check if target head is an ancestor of source head
	ancestors, err := me.getAncestors(ctx, sourceHead)
	if err != nil {
		return false, err
	}

	for _, id := range ancestors {
		if id == targetHead {
			return true, nil
		}
	}

	return false, nil
}

// createMergedState creates a new merged state
func (me *MergeEngine) createMergedState(ctx context.Context, req *MergeRequest, source, target *state.BuildingState, changes []Change) (*state.BuildingState, error) {
	// Apply changes to target state
	var targetData map[string]interface{}
	if err := json.Unmarshal(target.ArxObjectSnapshot, &targetData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal target snapshot: %w", err)
	}

	// Apply changes
	for _, change := range changes {
		switch change.Type {
		case "add", "modify":
			targetData[change.ObjectID] = change.NewValue
		case "delete":
			delete(targetData, change.ObjectID)
		}
	}

	// Create new snapshot
	mergedSnapshot, err := json.Marshal(targetData)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal merged snapshot: %w", err)
	}

	// Create merged state
	mergedState := &state.BuildingState{
		ID:                uuid.New().String(),
		BuildingID:        req.BuildingID,
		Branch:            req.TargetBranch,
		Version:           fmt.Sprintf("merge-%d", time.Now().Unix()),
		ParentStateID:     &target.ID,
		ArxObjectSnapshot: mergedSnapshot,
		SystemsState:      target.SystemsState, // Simplified - would merge systems too
		CommitMessage:     req.Message,
		CommittedBy:       req.Author,
		CreatedAt:         time.Now(),
	}

	// Save to database
	tx, err := me.db.BeginTxx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()

	// Insert merged state
	query := `
		INSERT INTO building_states (
			id, building_id, branch, version, parent_state_id,
			arxobject_snapshot, systems_state, 
			commit_message, committed_by, created_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10
		)`

	_, err = tx.ExecContext(ctx, query,
		mergedState.ID, mergedState.BuildingID, mergedState.Branch,
		mergedState.Version, mergedState.ParentStateID,
		mergedState.ArxObjectSnapshot, mergedState.SystemsState,
		mergedState.CommitMessage, mergedState.CommittedBy, mergedState.CreatedAt)
	if err != nil {
		return nil, fmt.Errorf("failed to insert merged state: %w", err)
	}

	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return mergedState, nil
}

// ResolveConflict resolves a specific conflict
func (me *MergeEngine) ResolveConflict(ctx context.Context, prID string, conflictID string, resolution *ConflictResolution) error {
	query := `
		UPDATE merge_conflicts 
		SET status = 'resolved',
		    resolution_strategy = $1,
		    resolved_value = $2,
		    resolved_by = $3,
		    resolved_at = $4
		WHERE pr_id = $5 AND id = $6`

	resolvedValue, err := json.Marshal(resolution.ResolvedValue)
	if err != nil {
		return fmt.Errorf("failed to marshal resolved value: %w", err)
	}

	_, err = me.db.ExecContext(ctx, query,
		resolution.Strategy, resolvedValue, resolution.ResolvedBy,
		resolution.ResolvedAt, prID, conflictID)
	if err != nil {
		return fmt.Errorf("failed to update conflict resolution: %w", err)
	}

	return nil
}

// GetConflicts returns conflicts for a pull request
func (me *MergeEngine) GetConflicts(ctx context.Context, prID string) ([]Conflict, error) {
	query := `
		SELECT id, conflict_type, object_id, base_value, source_value, target_value, status
		FROM merge_conflicts
		WHERE pr_id = $1 AND status = 'unresolved'`

	rows, err := me.db.QueryContext(ctx, query, prID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var conflicts []Conflict
	for rows.Next() {
		var c Conflict
		var baseValue, sourceValue, targetValue []byte
		
		err := rows.Scan(&c.ID, &c.Type, &c.ObjectID, &baseValue, &sourceValue, &targetValue, &c.Resolvable)
		if err != nil {
			return nil, err
		}

		json.Unmarshal(baseValue, &c.BaseValue)
		json.Unmarshal(sourceValue, &c.SourceValue)
		json.Unmarshal(targetValue, &c.TargetValue)
		
		conflicts = append(conflicts, c)
	}

	return conflicts, nil
}