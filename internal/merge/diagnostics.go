package merge

import (
	"encoding/json"
	"fmt"
	"runtime"
	"sort"
	"sync"
	"time"
)

// MergeDiagnostics provides runtime diagnostics for merge operations
type MergeDiagnostics struct {
	enabled     bool
	metrics     *DiagnosticMetrics
	events      []DiagnosticEvent
	performance *PerformanceTracker
	mu          sync.RWMutex
	maxEvents   int
	logLevel    DiagnosticLevel
}

// DiagnosticLevel represents the level of diagnostic detail
type DiagnosticLevel int

const (
	DiagnosticLevelError DiagnosticLevel = iota
	DiagnosticLevelWarn
	DiagnosticLevelInfo
	DiagnosticLevelDebug
	DiagnosticLevelTrace
)

// DiagnosticMetrics tracks merge operation metrics
type DiagnosticMetrics struct {
	TotalMerges          int64            `json:"total_merges"`
	SuccessfulMerges     int64            `json:"successful_merges"`
	FailedMerges         int64            `json:"failed_merges"`
	ConflictsEncountered int64            `json:"conflicts_encountered"`
	ConflictsResolved    int64            `json:"conflicts_resolved"`
	ChangesDetected      int64            `json:"changes_detected"`
	AverageMergeTime     time.Duration    `json:"average_merge_time"`
	MemoryUsage          MemoryStats      `json:"memory_usage"`
	ErrorCounts          map[string]int   `json:"error_counts"`
	SourceTypeCounts     map[string]int64 `json:"source_type_counts"`
	LastUpdate           time.Time        `json:"last_update"`
}

// MemoryStats tracks memory usage
type MemoryStats struct {
	Allocated      uint64 `json:"allocated"`
	TotalAllocated uint64 `json:"total_allocated"`
	System         uint64 `json:"system"`
	NumGC          uint32 `json:"num_gc"`
	HeapObjects    uint64 `json:"heap_objects"`
}

// DiagnosticEvent represents a diagnostic event
type DiagnosticEvent struct {
	ID        string          `json:"id"`
	Timestamp time.Time       `json:"timestamp"`
	Level     DiagnosticLevel `json:"level"`
	Category  string          `json:"category"`
	Message   string          `json:"message"`
	Data      interface{}     `json:"data,omitempty"`
	Error     error           `json:"error,omitempty"`
}

// PerformanceTracker tracks performance metrics
type PerformanceTracker struct {
	operations map[string]*OperationStats
	mu         sync.RWMutex
}

// OperationStats tracks statistics for a specific operation
type OperationStats struct {
	Name          string        `json:"name"`
	Count         int64         `json:"count"`
	TotalTime     time.Duration `json:"total_time"`
	MinTime       time.Duration `json:"min_time"`
	MaxTime       time.Duration `json:"max_time"`
	AverageTime   time.Duration `json:"average_time"`
	LastExecution time.Time     `json:"last_execution"`
}

// NewMergeDiagnostics creates a new diagnostics system
func NewMergeDiagnostics() *MergeDiagnostics {
	return &MergeDiagnostics{
		enabled: true,
		metrics: &DiagnosticMetrics{
			ErrorCounts:      make(map[string]int),
			SourceTypeCounts: make(map[string]int64),
			LastUpdate:       time.Now(),
		},
		events: make([]DiagnosticEvent, 0),
		performance: &PerformanceTracker{
			operations: make(map[string]*OperationStats),
		},
		maxEvents: 1000,
		logLevel:  DiagnosticLevelInfo,
	}
}

// Enable enables or disables diagnostics
func (md *MergeDiagnostics) Enable(enabled bool) {
	md.mu.Lock()
	defer md.mu.Unlock()
	md.enabled = enabled
}

// SetLogLevel sets the diagnostic log level
func (md *MergeDiagnostics) SetLogLevel(level DiagnosticLevel) {
	md.mu.Lock()
	defer md.mu.Unlock()
	md.logLevel = level
}

// RecordMergeStart records the start of a merge operation
func (md *MergeDiagnostics) RecordMergeStart(buildingID string, sourceCount int) string {
	if !md.enabled {
		return ""
	}

	operationID := fmt.Sprintf("merge_%s_%d", buildingID, time.Now().UnixNano())

	md.logEvent(DiagnosticLevelInfo, "merge", "Merge operation started", map[string]interface{}{
		"operation_id": operationID,
		"building_id":  buildingID,
		"source_count": sourceCount,
	})

	return operationID
}

// RecordMergeComplete records the completion of a merge operation
func (md *MergeDiagnostics) RecordMergeComplete(
	operationID string,
	result *FusionResult,
	duration time.Duration,
) {
	if !md.enabled {
		return
	}

	md.mu.Lock()
	defer md.mu.Unlock()

	md.metrics.TotalMerges++
	md.metrics.SuccessfulMerges++
	md.metrics.ConflictsEncountered += int64(len(result.Conflicts))
	md.metrics.ConflictsResolved += int64(len(result.Resolutions))
	md.metrics.ChangesDetected += int64(len(result.Changes))

	// Update average merge time
	if md.metrics.AverageMergeTime == 0 {
		md.metrics.AverageMergeTime = duration
	} else {
		md.metrics.AverageMergeTime = (md.metrics.AverageMergeTime + duration) / 2
	}

	// Update source type counts
	for sourceType, count := range result.Statistics.SourceBreakdown {
		md.metrics.SourceTypeCounts[sourceType] += int64(count)
	}

	md.metrics.LastUpdate = time.Now()

	// Record performance
	md.performance.recordOperation("merge", duration)

	// Log event
	md.logEventUnlocked(DiagnosticLevelInfo, "merge", "Merge operation completed", map[string]interface{}{
		"operation_id":    operationID,
		"duration":        duration,
		"equipment_count": len(result.MergedEquipment),
		"conflicts":       len(result.Conflicts),
		"resolutions":     len(result.Resolutions),
		"changes":         len(result.Changes),
	})
}

// RecordMergeError records a merge error
func (md *MergeDiagnostics) RecordMergeError(operationID string, err error) {
	if !md.enabled {
		return
	}

	md.mu.Lock()
	defer md.mu.Unlock()

	md.metrics.FailedMerges++

	// Count error types
	errorType := fmt.Sprintf("%T", err)
	md.metrics.ErrorCounts[errorType]++

	md.logEventUnlocked(DiagnosticLevelError, "merge", "Merge operation failed", map[string]interface{}{
		"operation_id": operationID,
		"error":        err.Error(),
		"error_type":   errorType,
	})
}

// RecordConflict records a detected conflict
func (md *MergeDiagnostics) RecordConflict(conflict Conflict) {
	if !md.enabled || md.logLevel > DiagnosticLevelDebug {
		return
	}

	md.logEvent(DiagnosticLevelDebug, "conflict", "Conflict detected", map[string]interface{}{
		"equipment_id": conflict.EquipmentID,
		"type":         conflict.Type,
		"difference":   conflict.Difference,
		"source1":      conflict.Source1.Type,
		"source2":      conflict.Source2.Type,
	})
}

// RecordResolution records a conflict resolution
func (md *MergeDiagnostics) RecordResolution(conflict Conflict, resolution *ResolutionResult) {
	if !md.enabled || md.logLevel > DiagnosticLevelDebug {
		return
	}

	data := map[string]interface{}{
		"equipment_id":  conflict.EquipmentID,
		"conflict_type": conflict.Type,
		"method":        resolution.Method,
		"confidence":    resolution.Confidence,
	}

	if resolution.RuleApplied != nil {
		data["rule"] = resolution.RuleApplied.Name
	}

	md.logEvent(DiagnosticLevelDebug, "resolution", "Conflict resolved", data)
}

// RecordChange records a detected change
func (md *MergeDiagnostics) RecordChange(change Change) {
	if !md.enabled || md.logLevel > DiagnosticLevelDebug {
		return
	}

	md.logEvent(DiagnosticLevelDebug, "change", "Change detected", map[string]interface{}{
		"equipment_id": change.EquipmentID,
		"type":         change.Type,
		"field":        change.Field,
		"magnitude":    change.Magnitude,
		"confidence":   change.Confidence,
	})
}

// StartOperation starts tracking an operation
func (md *MergeDiagnostics) StartOperation(name string) func() {
	if !md.enabled {
		return func() {}
	}

	start := time.Now()
	return func() {
		duration := time.Since(start)
		md.performance.recordOperation(name, duration)

		if md.logLevel <= DiagnosticLevelTrace {
			md.logEvent(DiagnosticLevelTrace, "performance", fmt.Sprintf("Operation %s completed", name), map[string]interface{}{
				"operation": name,
				"duration":  duration,
			})
		}
	}
}

// logEvent logs a diagnostic event
func (md *MergeDiagnostics) logEvent(level DiagnosticLevel, category, message string, data interface{}) {
	md.mu.Lock()
	defer md.mu.Unlock()
	md.logEventUnlocked(level, category, message, data)
}

// logEventUnlocked logs an event without locking (caller must hold lock)
func (md *MergeDiagnostics) logEventUnlocked(level DiagnosticLevel, category, message string, data interface{}) {
	if level > md.logLevel {
		return
	}

	event := DiagnosticEvent{
		ID:        fmt.Sprintf("event_%d", time.Now().UnixNano()),
		Timestamp: time.Now(),
		Level:     level,
		Category:  category,
		Message:   message,
		Data:      data,
	}

	md.events = append(md.events, event)

	// Trim events if exceeded max
	if len(md.events) > md.maxEvents {
		md.events = md.events[len(md.events)-md.maxEvents:]
	}
}

// recordOperation records operation performance
func (pt *PerformanceTracker) recordOperation(name string, duration time.Duration) {
	pt.mu.Lock()
	defer pt.mu.Unlock()

	stats, exists := pt.operations[name]
	if !exists {
		stats = &OperationStats{
			Name:    name,
			MinTime: duration,
			MaxTime: duration,
		}
		pt.operations[name] = stats
	}

	stats.Count++
	stats.TotalTime += duration
	stats.AverageTime = stats.TotalTime / time.Duration(stats.Count)
	stats.LastExecution = time.Now()

	if duration < stats.MinTime {
		stats.MinTime = duration
	}
	if duration > stats.MaxTime {
		stats.MaxTime = duration
	}
}

// GetMetrics returns current diagnostic metrics
func (md *MergeDiagnostics) GetMetrics() *DiagnosticMetrics {
	md.mu.RLock()
	defer md.mu.RUnlock()

	// Update memory stats
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	md.metrics.MemoryUsage = MemoryStats{
		Allocated:      memStats.Alloc,
		TotalAllocated: memStats.TotalAlloc,
		System:         memStats.Sys,
		NumGC:          memStats.NumGC,
		HeapObjects:    memStats.HeapObjects,
	}

	return md.metrics
}

// GetPerformanceStats returns performance statistics
func (md *MergeDiagnostics) GetPerformanceStats() map[string]*OperationStats {
	md.performance.mu.RLock()
	defer md.performance.mu.RUnlock()

	// Create a copy
	stats := make(map[string]*OperationStats)
	for k, v := range md.performance.operations {
		statsCopy := *v
		stats[k] = &statsCopy
	}

	return stats
}

// GetRecentEvents returns recent diagnostic events
func (md *MergeDiagnostics) GetRecentEvents(count int) []DiagnosticEvent {
	md.mu.RLock()
	defer md.mu.RUnlock()

	if count > len(md.events) {
		count = len(md.events)
	}

	// Return most recent events
	start := len(md.events) - count
	if start < 0 {
		start = 0
	}

	result := make([]DiagnosticEvent, count)
	copy(result, md.events[start:])

	return result
}

// GetEventsByLevel returns events filtered by level
func (md *MergeDiagnostics) GetEventsByLevel(level DiagnosticLevel, limit int) []DiagnosticEvent {
	md.mu.RLock()
	defer md.mu.RUnlock()

	filtered := make([]DiagnosticEvent, 0)
	for i := len(md.events) - 1; i >= 0 && len(filtered) < limit; i-- {
		if md.events[i].Level <= level {
			filtered = append(filtered, md.events[i])
		}
	}

	return filtered
}

// GenerateHealthReport generates a health report for the merge system
func (md *MergeDiagnostics) GenerateHealthReport() *HealthReport {
	md.mu.RLock()
	defer md.mu.RUnlock()

	report := &HealthReport{
		Timestamp:   time.Now(),
		Status:      md.calculateHealthStatus(),
		Metrics:     md.GetMetrics(),
		Issues:      md.detectIssues(),
		Performance: md.analyzePerformance(),
	}

	return report
}

// HealthReport represents system health status
type HealthReport struct {
	Timestamp   time.Time           `json:"timestamp"`
	Status      HealthStatus        `json:"status"`
	Metrics     *DiagnosticMetrics  `json:"metrics"`
	Issues      []HealthIssue       `json:"issues"`
	Performance PerformanceAnalysis `json:"performance"`
}

// HealthStatus represents overall health status
type HealthStatus string

const (
	HealthStatusHealthy   HealthStatus = "healthy"
	HealthStatusDegraded  HealthStatus = "degraded"
	HealthStatusUnhealthy HealthStatus = "unhealthy"
)

// HealthIssue represents a detected health issue
type HealthIssue struct {
	Severity    string `json:"severity"`
	Category    string `json:"category"`
	Description string `json:"description"`
	Impact      string `json:"impact"`
	Resolution  string `json:"resolution"`
}

// PerformanceAnalysis represents performance analysis results
type PerformanceAnalysis struct {
	SlowOperations []string `json:"slow_operations"`
	Bottlenecks    []string `json:"bottlenecks"`
	ThroughputRate float64  `json:"throughput_rate"`
	ErrorRate      float64  `json:"error_rate"`
	ResolutionRate float64  `json:"resolution_rate"`
}

// calculateHealthStatus calculates overall health status
func (md *MergeDiagnostics) calculateHealthStatus() HealthStatus {
	if md.metrics.TotalMerges == 0 {
		return HealthStatusHealthy
	}

	errorRate := float64(md.metrics.FailedMerges) / float64(md.metrics.TotalMerges)

	// Calculate resolution rate only if there were conflicts
	var resolutionRate float64 = 1.0
	if md.metrics.ConflictsEncountered > 0 {
		resolutionRate = float64(md.metrics.ConflictsResolved) / float64(md.metrics.ConflictsEncountered)
	}

	if errorRate > 0.5 || resolutionRate < 0.3 {
		return HealthStatusUnhealthy
	} else if errorRate > 0.2 || resolutionRate < 0.6 {
		return HealthStatusDegraded
	}

	return HealthStatusHealthy
}

// detectIssues detects potential health issues
func (md *MergeDiagnostics) detectIssues() []HealthIssue {
	issues := make([]HealthIssue, 0)

	// Check error rate
	if md.metrics.TotalMerges > 0 {
		errorRate := float64(md.metrics.FailedMerges) / float64(md.metrics.TotalMerges)
		if errorRate > 0.1 {
			issues = append(issues, HealthIssue{
				Severity:    "high",
				Category:    "reliability",
				Description: fmt.Sprintf("High error rate: %.1f%%", errorRate*100),
				Impact:      "Merge operations are failing frequently",
				Resolution:  "Review error logs and fix underlying issues",
			})
		}
	}

	// Check conflict resolution rate
	if md.metrics.ConflictsEncountered > 0 {
		resolutionRate := float64(md.metrics.ConflictsResolved) / float64(md.metrics.ConflictsEncountered)
		if resolutionRate < 0.5 {
			issues = append(issues, HealthIssue{
				Severity:    "medium",
				Category:    "conflicts",
				Description: fmt.Sprintf("Low conflict resolution rate: %.1f%%", resolutionRate*100),
				Impact:      "Many conflicts remain unresolved",
				Resolution:  "Review conflict resolution rules and add missing patterns",
			})
		}
	}

	// Check memory usage
	if md.metrics.MemoryUsage.Allocated > 500*1024*1024 { // 500MB
		issues = append(issues, HealthIssue{
			Severity:    "medium",
			Category:    "performance",
			Description: fmt.Sprintf("High memory usage: %d MB", md.metrics.MemoryUsage.Allocated/(1024*1024)),
			Impact:      "System may experience performance degradation",
			Resolution:  "Review memory allocation patterns and optimize data structures",
		})
	}

	// Check processing time
	if md.metrics.AverageMergeTime > 10*time.Second {
		issues = append(issues, HealthIssue{
			Severity:    "low",
			Category:    "performance",
			Description: fmt.Sprintf("Slow average merge time: %v", md.metrics.AverageMergeTime),
			Impact:      "Merge operations are taking longer than expected",
			Resolution:  "Optimize merge algorithms and consider parallelization",
		})
	}

	return issues
}

// analyzePerformance analyzes performance metrics
func (md *MergeDiagnostics) analyzePerformance() PerformanceAnalysis {
	analysis := PerformanceAnalysis{
		SlowOperations: make([]string, 0),
		Bottlenecks:    make([]string, 0),
	}

	// Calculate rates
	if md.metrics.TotalMerges > 0 {
		analysis.ErrorRate = float64(md.metrics.FailedMerges) / float64(md.metrics.TotalMerges)

		timeSinceStart := time.Since(md.metrics.LastUpdate.Add(-time.Hour * 24))
		if timeSinceStart > 0 {
			analysis.ThroughputRate = float64(md.metrics.TotalMerges) / timeSinceStart.Hours()
		}
	}

	if md.metrics.ConflictsEncountered > 0 {
		analysis.ResolutionRate = float64(md.metrics.ConflictsResolved) /
			float64(md.metrics.ConflictsEncountered)
	}

	// Identify slow operations
	for name, stats := range md.performance.operations {
		if stats.AverageTime > time.Second {
			analysis.SlowOperations = append(analysis.SlowOperations,
				fmt.Sprintf("%s (avg: %v)", name, stats.AverageTime))
		}

		// Check for bottlenecks (operations with high max time)
		if stats.MaxTime > 5*stats.AverageTime && stats.Count > 10 {
			analysis.Bottlenecks = append(analysis.Bottlenecks, name)
		}
	}

	return analysis
}

// ExportDiagnostics exports diagnostics data
func (md *MergeDiagnostics) ExportDiagnostics() ([]byte, error) {
	md.mu.RLock()
	defer md.mu.RUnlock()

	export := map[string]interface{}{
		"timestamp":   time.Now(),
		"metrics":     md.metrics,
		"performance": md.GetPerformanceStats(),
		"events":      md.events,
		"health":      md.GenerateHealthReport(),
	}

	return json.MarshalIndent(export, "", "  ")
}

// Reset resets all diagnostic data
func (md *MergeDiagnostics) Reset() {
	md.mu.Lock()
	defer md.mu.Unlock()

	md.metrics = &DiagnosticMetrics{
		ErrorCounts:      make(map[string]int),
		SourceTypeCounts: make(map[string]int64),
		LastUpdate:       time.Now(),
	}
	md.events = make([]DiagnosticEvent, 0)

	md.performance.mu.Lock()
	md.performance.operations = make(map[string]*OperationStats)
	md.performance.mu.Unlock()
}

// GetSummary returns a summary of diagnostic data
func (md *MergeDiagnostics) GetSummary() string {
	md.mu.RLock()
	defer md.mu.RUnlock()

	health := md.calculateHealthStatus()

	summary := fmt.Sprintf(
		"Merge Diagnostics Summary\n"+
			"=========================\n"+
			"Health Status: %s\n"+
			"Total Merges: %d (Success: %d, Failed: %d)\n"+
			"Conflicts: %d encountered, %d resolved (%.1f%%)\n"+
			"Changes Detected: %d\n"+
			"Average Merge Time: %v\n"+
			"Memory Usage: %.1f MB\n",
		health,
		md.metrics.TotalMerges,
		md.metrics.SuccessfulMerges,
		md.metrics.FailedMerges,
		md.metrics.ConflictsEncountered,
		md.metrics.ConflictsResolved,
		float64(md.metrics.ConflictsResolved)/float64(md.metrics.ConflictsEncountered+1)*100,
		md.metrics.ChangesDetected,
		md.metrics.AverageMergeTime,
		float64(md.metrics.MemoryUsage.Allocated)/(1024*1024),
	)

	// Add top errors
	if len(md.metrics.ErrorCounts) > 0 {
		summary += "\nTop Errors:\n"
		errors := make([]string, 0, len(md.metrics.ErrorCounts))
		for errorType, count := range md.metrics.ErrorCounts {
			errors = append(errors, fmt.Sprintf("  %s: %d", errorType, count))
		}
		sort.Strings(errors)
		for _, e := range errors {
			summary += e + "\n"
		}
	}

	return summary
}

// String returns the string representation of diagnostic level
func (dl DiagnosticLevel) String() string {
	switch dl {
	case DiagnosticLevelError:
		return "ERROR"
	case DiagnosticLevelWarn:
		return "WARN"
	case DiagnosticLevelInfo:
		return "INFO"
	case DiagnosticLevelDebug:
		return "DEBUG"
	case DiagnosticLevelTrace:
		return "TRACE"
	default:
		return "UNKNOWN"
	}
}
