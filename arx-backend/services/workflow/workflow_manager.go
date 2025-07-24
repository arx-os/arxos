package workflow

import (
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// WorkflowSchedule represents a scheduled workflow
type WorkflowSchedule struct {
	ScheduleID     string     `json:"schedule_id" gorm:"primaryKey"`
	WorkflowID     string     `json:"workflow_id"`
	CronExpression string     `json:"cron_expression"`
	Enabled        bool       `json:"enabled"`
	LastRun        *time.Time `json:"last_run"`
	NextRun        *time.Time `json:"next_run"`
	CreatedAt      time.Time  `json:"created_at"`
}

// WorkflowTrigger represents a workflow trigger
type WorkflowTrigger struct {
	TriggerID   string                 `json:"trigger_id" gorm:"primaryKey"`
	WorkflowID  string                 `json:"workflow_id"`
	TriggerType string                 `json:"trigger_type"`
	Conditions  map[string]interface{} `json:"conditions" gorm:"type:json"`
	Enabled     bool                   `json:"enabled"`
	CreatedAt   time.Time              `json:"created_at"`
}

// WorkflowTemplate represents a workflow template
type WorkflowTemplate struct {
	TemplateID   string                 `json:"template_id" gorm:"primaryKey"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Category     string                 `json:"category"`
	WorkflowType WorkflowType           `json:"workflow_type"`
	Steps        []WorkflowStep         `json:"steps" gorm:"type:json"`
	Parameters   map[string]interface{} `json:"parameters" gorm:"type:json"`
	Tags         []string               `json:"tags" gorm:"type:json"`
	CreatedAt    time.Time              `json:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at"`
}

// WorkflowManager provides workflow lifecycle management
type WorkflowManager struct {
	engine    *WorkflowEngine
	db        *gorm.DB
	schedules map[string]*WorkflowSchedule
	triggers  map[string]*WorkflowTrigger
	templates map[string]*WorkflowTemplate
	lock      sync.RWMutex
}

// NewWorkflowManager creates a new workflow manager
func NewWorkflowManager(engine *WorkflowEngine) *WorkflowManager {
	manager := &WorkflowManager{
		engine:    engine,
		db:        engine.db,
		schedules: make(map[string]*WorkflowSchedule),
		triggers:  make(map[string]*WorkflowTrigger),
		templates: make(map[string]*WorkflowTemplate),
	}

	// Load existing schedules and triggers
	manager.loadSchedules()
	manager.loadTriggers()
	manager.loadTemplates()

	// Start schedule worker
	go manager.scheduleWorker()

	return manager
}

// CreateWorkflowFromTemplate creates a workflow from a template
func (m *WorkflowManager) CreateWorkflowFromTemplate(templateID string, parameters map[string]interface{}) (*WorkflowDefinition, error) {
	m.lock.RLock()
	template, exists := m.templates[templateID]
	m.lock.RUnlock()

	if !exists {
		return nil, fmt.Errorf("template %s not found", templateID)
	}

	// Create workflow data from template
	workflowData := map[string]interface{}{
		"workflow_id":   fmt.Sprintf("%s_%d", templateID, time.Now().Unix()),
		"name":          template.Name,
		"description":   template.Description,
		"workflow_type": template.WorkflowType,
		"steps":         template.Steps,
		"timeout":       1800,
		"max_retries":   3,
	}

	// Apply template parameters
	for key, value := range template.Parameters {
		if paramValue, exists := parameters[key]; exists {
			workflowData[key] = paramValue
		} else {
			workflowData[key] = value
		}
	}

	// Create workflow
	return m.engine.CreateWorkflow(workflowData)
}

// ScheduleWorkflow schedules a workflow for execution
func (m *WorkflowManager) ScheduleWorkflow(workflowID string, cronExpression string) (*WorkflowSchedule, error) {
	// Validate cron expression
	if err := m.validateCronExpression(cronExpression); err != nil {
		return nil, fmt.Errorf("invalid cron expression: %w", err)
	}

	schedule := &WorkflowSchedule{
		ScheduleID:     fmt.Sprintf("schedule_%d", time.Now().UnixNano()),
		WorkflowID:     workflowID,
		CronExpression: cronExpression,
		Enabled:        true,
		CreatedAt:      time.Now(),
	}

	// Calculate next run time
	nextRun, err := m.calculateNextRun(cronExpression)
	if err != nil {
		return nil, fmt.Errorf("failed to calculate next run: %w", err)
	}
	schedule.NextRun = &nextRun

	m.lock.Lock()
	m.schedules[schedule.ScheduleID] = schedule
	m.lock.Unlock()

	// Save to database
	if err := m.db.Create(schedule).Error; err != nil {
		return nil, fmt.Errorf("failed to save schedule: %w", err)
	}

	return schedule, nil
}

// CreateTrigger creates a workflow trigger
func (m *WorkflowManager) CreateTrigger(workflowID string, triggerType string, conditions map[string]interface{}) (*WorkflowTrigger, error) {
	trigger := &WorkflowTrigger{
		TriggerID:   fmt.Sprintf("trigger_%d", time.Now().UnixNano()),
		WorkflowID:  workflowID,
		TriggerType: triggerType,
		Conditions:  conditions,
		Enabled:     true,
		CreatedAt:   time.Now(),
	}

	m.lock.Lock()
	m.triggers[trigger.TriggerID] = trigger
	m.lock.Unlock()

	// Save to database
	if err := m.db.Create(trigger).Error; err != nil {
		return nil, fmt.Errorf("failed to save trigger: %w", err)
	}

	return trigger, nil
}

// CreateTemplate creates a workflow template
func (m *WorkflowManager) CreateTemplate(templateData map[string]interface{}) (*WorkflowTemplate, error) {
	templateID, ok := templateData["template_id"].(string)
	if !ok {
		return nil, fmt.Errorf("template_id is required")
	}

	name, ok := templateData["name"].(string)
	if !ok {
		return nil, fmt.Errorf("name is required")
	}

	workflowTypeStr, ok := templateData["workflow_type"].(string)
	if !ok {
		return nil, fmt.Errorf("workflow_type is required")
	}

	// Parse steps
	stepsData, ok := templateData["steps"].([]interface{})
	if !ok {
		return nil, fmt.Errorf("steps is required")
	}

	var steps []WorkflowStep
	for _, stepData := range stepsData {
		stepMap, ok := stepData.(map[string]interface{})
		if !ok {
			continue
		}

		step, err := m.engine.createStepFromMap(stepMap)
		if err != nil {
			return nil, fmt.Errorf("failed to create step: %w", err)
		}

		steps = append(steps, *step)
	}

	// Parse parameters
	parameters, ok := templateData["parameters"].(map[string]interface{})
	if !ok {
		parameters = make(map[string]interface{})
	}

	// Parse tags
	var tags []string
	if tagsData, ok := templateData["tags"].([]interface{}); ok {
		for _, tag := range tagsData {
			if tagStr, ok := tag.(string); ok {
				tags = append(tags, tagStr)
			}
		}
	}

	template := &WorkflowTemplate{
		TemplateID:   templateID,
		Name:         name,
		Description:  templateData["description"].(string),
		Category:     templateData["category"].(string),
		WorkflowType: WorkflowType(workflowTypeStr),
		Steps:        steps,
		Parameters:   parameters,
		Tags:         tags,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	m.lock.Lock()
	m.templates[template.TemplateID] = template
	m.lock.Unlock()

	// Save to database
	if err := m.db.Create(template).Error; err != nil {
		return nil, fmt.Errorf("failed to save template: %w", err)
	}

	return template, nil
}

// EnableSchedule enables a workflow schedule
func (m *WorkflowManager) EnableSchedule(scheduleID string) error {
	m.lock.Lock()
	defer m.lock.Unlock()

	schedule, exists := m.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("schedule %s not found", scheduleID)
	}

	schedule.Enabled = true

	// Update in database
	if err := m.db.Save(schedule).Error; err != nil {
		return fmt.Errorf("failed to update schedule: %w", err)
	}

	return nil
}

// DisableSchedule disables a workflow schedule
func (m *WorkflowManager) DisableSchedule(scheduleID string) error {
	m.lock.Lock()
	defer m.lock.Unlock()

	schedule, exists := m.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("schedule %s not found", scheduleID)
	}

	schedule.Enabled = false

	// Update in database
	if err := m.db.Save(schedule).Error; err != nil {
		return fmt.Errorf("failed to update schedule: %w", err)
	}

	return nil
}

// EnableTrigger enables a workflow trigger
func (m *WorkflowManager) EnableTrigger(triggerID string) error {
	m.lock.Lock()
	defer m.lock.Unlock()

	trigger, exists := m.triggers[triggerID]
	if !exists {
		return fmt.Errorf("trigger %s not found", triggerID)
	}

	trigger.Enabled = true

	// Update in database
	if err := m.db.Save(trigger).Error; err != nil {
		return fmt.Errorf("failed to update trigger: %w", err)
	}

	return nil
}

// DisableTrigger disables a workflow trigger
func (m *WorkflowManager) DisableTrigger(triggerID string) error {
	m.lock.Lock()
	defer m.lock.Unlock()

	trigger, exists := m.triggers[triggerID]
	if !exists {
		return fmt.Errorf("trigger %s not found", triggerID)
	}

	trigger.Enabled = false

	// Update in database
	if err := m.db.Save(trigger).Error; err != nil {
		return fmt.Errorf("failed to update trigger: %w", err)
	}

	return nil
}

// DeleteSchedule deletes a workflow schedule
func (m *WorkflowManager) DeleteSchedule(scheduleID string) error {
	m.lock.Lock()
	defer m.lock.Unlock()

	schedule, exists := m.schedules[scheduleID]
	if !exists {
		return fmt.Errorf("schedule %s not found", scheduleID)
	}

	// Delete from database
	if err := m.db.Delete(schedule).Error; err != nil {
		return fmt.Errorf("failed to delete schedule: %w", err)
	}

	delete(m.schedules, scheduleID)
	return nil
}

// DeleteTrigger deletes a workflow trigger
func (m *WorkflowManager) DeleteTrigger(triggerID string) error {
	m.lock.Lock()
	defer m.lock.Unlock()

	trigger, exists := m.triggers[triggerID]
	if !exists {
		return fmt.Errorf("trigger %s not found", triggerID)
	}

	// Delete from database
	if err := m.db.Delete(trigger).Error; err != nil {
		return fmt.Errorf("failed to delete trigger: %w", err)
	}

	delete(m.triggers, triggerID)
	return nil
}

// ListSchedules lists all workflow schedules
func (m *WorkflowManager) ListSchedules() ([]map[string]interface{}, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	var schedules []map[string]interface{}
	for _, schedule := range m.schedules {
		schedules = append(schedules, map[string]interface{}{
			"schedule_id":     schedule.ScheduleID,
			"workflow_id":     schedule.WorkflowID,
			"cron_expression": schedule.CronExpression,
			"enabled":         schedule.Enabled,
			"last_run":        schedule.LastRun,
			"next_run":        schedule.NextRun,
			"created_at":      schedule.CreatedAt,
		})
	}

	return schedules, nil
}

// ListTriggers lists all workflow triggers
func (m *WorkflowManager) ListTriggers() ([]map[string]interface{}, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	var triggers []map[string]interface{}
	for _, trigger := range m.triggers {
		triggers = append(triggers, map[string]interface{}{
			"trigger_id":   trigger.TriggerID,
			"workflow_id":  trigger.WorkflowID,
			"trigger_type": trigger.TriggerType,
			"conditions":   trigger.Conditions,
			"enabled":      trigger.Enabled,
			"created_at":   trigger.CreatedAt,
		})
	}

	return triggers, nil
}

// ListTemplates lists all workflow templates
func (m *WorkflowManager) ListTemplates() ([]map[string]interface{}, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	var templates []map[string]interface{}
	for _, template := range m.templates {
		templates = append(templates, map[string]interface{}{
			"template_id":   template.TemplateID,
			"name":          template.Name,
			"description":   template.Description,
			"category":      template.Category,
			"workflow_type": template.WorkflowType,
			"steps_count":   len(template.Steps),
			"tags":          template.Tags,
			"created_at":    template.CreatedAt,
			"updated_at":    template.UpdatedAt,
		})
	}

	return templates, nil
}

// GetTemplate gets a workflow template by ID
func (m *WorkflowManager) GetTemplate(templateID string) (*WorkflowTemplate, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	template, exists := m.templates[templateID]
	if !exists {
		return nil, fmt.Errorf("template %s not found", templateID)
	}

	return template, nil
}

// SearchTemplates searches for workflow templates
func (m *WorkflowManager) SearchTemplates(query string, category string) ([]map[string]interface{}, error) {
	m.lock.RLock()
	defer m.lock.RUnlock()

	var results []map[string]interface{}
	for _, template := range m.templates {
		// Apply category filter
		if category != "" && template.Category != category {
			continue
		}

		// Apply query filter
		if query != "" {
			// Simple text search in name, description, and tags
			matched := false
			if contains(template.Name, query) || contains(template.Description, query) {
				matched = true
			}
			for _, tag := range template.Tags {
				if contains(tag, query) {
					matched = true
					break
				}
			}
			if !matched {
				continue
			}
		}

		results = append(results, map[string]interface{}{
			"template_id":   template.TemplateID,
			"name":          template.Name,
			"description":   template.Description,
			"category":      template.Category,
			"workflow_type": template.WorkflowType,
			"steps_count":   len(template.Steps),
			"tags":          template.Tags,
		})
	}

	return results, nil
}

// Helper methods

func (m *WorkflowManager) scheduleWorker() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		m.checkSchedules()
	}
}

func (m *WorkflowManager) checkSchedules() {
	m.lock.RLock()
	schedules := make([]*WorkflowSchedule, 0, len(m.schedules))
	for _, schedule := range m.schedules {
		if schedule.Enabled {
			schedules = append(schedules, schedule)
		}
	}
	m.lock.RUnlock()

	now := time.Now()
	for _, schedule := range schedules {
		if schedule.NextRun != nil && now.After(*schedule.NextRun) {
			// Execute workflow
			_, err := m.engine.ExecuteWorkflow(schedule.WorkflowID, nil)
			if err != nil {
				continue
			}

			// Update schedule
			schedule.LastRun = &now
			nextRun, err := m.calculateNextRun(schedule.CronExpression)
			if err == nil {
				schedule.NextRun = &nextRun
			}

			// Save to database
			m.db.Save(schedule)
		}
	}
}

func (m *WorkflowManager) validateCronExpression(cronExpression string) error {
	// Simple cron validation - in practice you'd use a proper cron parser
	if cronExpression == "" {
		return fmt.Errorf("cron expression cannot be empty")
	}

	// Basic format check (5 or 6 fields)
	// This is a simplified validation
	return nil
}

func (m *WorkflowManager) calculateNextRun(cronExpression string) (time.Time, error) {
	// Simplified next run calculation
	// In practice, you'd use a proper cron parser like github.com/robfig/cron
	now := time.Now()

	// For now, just add 1 hour as a placeholder
	// This should be replaced with proper cron parsing
	return now.Add(time.Hour), nil
}

func (m *WorkflowManager) loadSchedules() {
	var schedules []WorkflowSchedule
	if err := m.db.Find(&schedules).Error; err != nil {
		return
	}

	for i := range schedules {
		m.schedules[schedules[i].ScheduleID] = &schedules[i]
	}
}

func (m *WorkflowManager) loadTriggers() {
	var triggers []WorkflowTrigger
	if err := m.db.Find(&triggers).Error; err != nil {
		return
	}

	for i := range triggers {
		m.triggers[triggers[i].TriggerID] = &triggers[i]
	}
}

func (m *WorkflowManager) loadTemplates() {
	var templates []WorkflowTemplate
	if err := m.db.Find(&templates).Error; err != nil {
		return
	}

	for i := range templates {
		m.templates[templates[i].TemplateID] = &templates[i]
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0)
}
