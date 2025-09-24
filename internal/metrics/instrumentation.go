package metrics

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Instrumentation provides comprehensive instrumentation for service operations
type Instrumentation struct {
	serviceName string
	metrics     *ServiceMetrics
	tracer      *Tracer
	mu          sync.RWMutex

	// Operation tracking
	activeOperations map[string]*OperationTracker
	operationCounts  map[string]int64
	errorCounts      map[string]int64
	retryCounts      map[string]int64
}

// OperationTracker tracks an individual operation
type OperationTracker struct {
	Operation  string
	StartTime  time.Time
	Context    context.Context
	Labels     map[string]string
	RetryCount int32
	ErrorCount int32
	mu         sync.RWMutex
}

// Tracer provides distributed tracing capabilities
type Tracer struct {
	serviceName string
	spans       map[string]*Span
	mu          sync.RWMutex
}

// Span represents a trace span
type Span struct {
	TraceID   string
	SpanID    string
	ParentID  string
	Operation string
	Service   string
	StartTime time.Time
	EndTime   time.Time
	Duration  time.Duration
	Labels    map[string]string
	Events    []SpanEvent
	Status    SpanStatus
	mu        sync.RWMutex
}

// SpanEvent represents an event within a span
type SpanEvent struct {
	Timestamp time.Time
	Name      string
	Labels    map[string]string
}

// SpanStatus represents the status of a span
type SpanStatus int

const (
	SpanStatusUnknown SpanStatus = iota
	SpanStatusOK
	SpanStatusError
	SpanStatusCancelled
)

// NewInstrumentation creates a new instrumentation instance
func NewInstrumentation(serviceName string) *Instrumentation {
	return &Instrumentation{
		serviceName:      serviceName,
		metrics:          NewServiceMetrics(serviceName),
		tracer:           NewTracer(serviceName),
		activeOperations: make(map[string]*OperationTracker),
		operationCounts:  make(map[string]int64),
		errorCounts:      make(map[string]int64),
		retryCounts:      make(map[string]int64),
	}
}

// NewTracer creates a new tracer
func NewTracer(serviceName string) *Tracer {
	return &Tracer{
		serviceName: serviceName,
		spans:       make(map[string]*Span),
	}
}

// StartOperation starts tracking a new operation
func (i *Instrumentation) StartOperation(ctx context.Context, operation string, labels map[string]string) *OperationTracker {
	i.mu.Lock()
	defer i.mu.Unlock()

	// Increment operation count
	i.operationCounts[operation]++

	tracker := &OperationTracker{
		Operation:  operation,
		StartTime:  time.Now(),
		Context:    ctx,
		Labels:     labels,
		RetryCount: 0,
		ErrorCount: 0,
	}

	i.activeOperations[operation] = tracker

	// Start metrics collection
	i.metrics.StartOperation(operation)

	// Start tracing
	span := i.tracer.StartSpan(ctx, operation, labels)
	tracker.Labels["span_id"] = span.SpanID
	tracker.Labels["trace_id"] = span.TraceID

	return tracker
}

// CompleteOperation completes an operation successfully
func (i *Instrumentation) CompleteOperation(tracker *OperationTracker) {
	if tracker == nil {
		return
	}

	i.mu.Lock()
	defer i.mu.Unlock()

	duration := time.Since(tracker.StartTime)

	// Complete metrics
	i.metrics.StartOperation(tracker.Operation).CompleteOperation()

	// Complete tracing
	i.tracer.FinishSpan(tracker.Labels["span_id"], SpanStatusOK)

	// Remove from active operations
	delete(i.activeOperations, tracker.Operation)

	// Log operation completion
	logger.Debug("Operation %s completed in %v", tracker.Operation, duration)
}

// CompleteOperationWithError completes an operation with an error
func (i *Instrumentation) CompleteOperationWithError(tracker *OperationTracker, err error) {
	if tracker == nil {
		return
	}

	i.mu.Lock()
	defer i.mu.Unlock()

	duration := time.Since(tracker.StartTime)
	i.errorCounts[tracker.Operation]++
	atomic.AddInt32(&tracker.ErrorCount, 1)

	// Complete metrics with error
	i.metrics.StartOperation(tracker.Operation).CompleteOperationWithError(err)

	// Complete tracing with error
	i.tracer.FinishSpan(tracker.Labels["span_id"], SpanStatusError)

	// Remove from active operations
	delete(i.activeOperations, tracker.Operation)

	// Log operation error
	logger.Warn("Operation %s failed after %v: %v", tracker.Operation, duration, err)
}

// RecordRetry records a retry attempt
func (i *Instrumentation) RecordRetry(tracker *OperationTracker) {
	if tracker == nil {
		return
	}

	atomic.AddInt32(&tracker.RetryCount, 1)
	i.retryCounts[tracker.Operation]++

	// Record retry metrics
	i.metrics.RecordRetry(tracker.Operation)

	// Add retry event to span
	i.tracer.AddEvent(tracker.Labels["span_id"], "retry", map[string]string{
		"retry_count": fmt.Sprintf("%d", tracker.RetryCount),
	})

	logger.Debug("Operation %s retry #%d", tracker.Operation, tracker.RetryCount)
}

// RecordCircuitBreakerState records circuit breaker state
func (i *Instrumentation) RecordCircuitBreakerState(operation string, state int) {
	i.metrics.RecordCircuitBreakerState(operation, state)

	stateName := "closed"
	switch state {
	case 1:
		stateName = "open"
	case 2:
		stateName = "half-open"
	}

	logger.Info("Circuit breaker for %s:%s is %s", i.serviceName, operation, stateName)
}

// RecordFallbackUsage records fallback operation usage
func (i *Instrumentation) RecordFallbackUsage(operation string) {
	i.metrics.RecordFallbackUsage(operation)
	logger.Info("Fallback used for %s:%s", i.serviceName, operation)
}

// RecordBatchOperation records a batch operation
func (i *Instrumentation) RecordBatchOperation(operation string, batchSize int) {
	i.metrics.RecordBatchOperation(operation, batchSize)
	logger.Debug("Batch operation %s:%s processed %d items", i.serviceName, operation, batchSize)
}

// GetActiveOperations returns currently active operations
func (i *Instrumentation) GetActiveOperations() map[string]*OperationTracker {
	i.mu.RLock()
	defer i.mu.RUnlock()

	result := make(map[string]*OperationTracker)
	for name, tracker := range i.activeOperations {
		result[name] = tracker
	}
	return result
}

// GetOperationStats returns statistics for operations
func (i *Instrumentation) GetOperationStats() map[string]OperationStats {
	i.mu.RLock()
	defer i.mu.RUnlock()

	stats := make(map[string]OperationStats)

	for operation := range i.operationCounts {
		stats[operation] = OperationStats{
			TotalCount: i.operationCounts[operation],
			ErrorCount: i.errorCounts[operation],
			RetryCount: i.retryCounts[operation],
			IsActive:   i.activeOperations[operation] != nil,
		}
	}

	return stats
}

// OperationStats provides statistics for an operation
type OperationStats struct {
	TotalCount int64 `json:"total_count"`
	ErrorCount int64 `json:"error_count"`
	RetryCount int64 `json:"retry_count"`
	IsActive   bool  `json:"is_active"`
}

// Tracer methods

// StartSpan starts a new trace span
func (t *Tracer) StartSpan(ctx context.Context, operation string, labels map[string]string) *Span {
	t.mu.Lock()
	defer t.mu.Unlock()

	spanID := generateSpanID()
	traceID := getTraceIDFromContext(ctx)
	if traceID == "" {
		traceID = generateTraceID()
	}

	span := &Span{
		TraceID:   traceID,
		SpanID:    spanID,
		Operation: operation,
		Service:   t.serviceName,
		StartTime: time.Now(),
		Labels:    labels,
		Events:    make([]SpanEvent, 0),
		Status:    SpanStatusUnknown,
	}

	t.spans[spanID] = span
	return span
}

// FinishSpan finishes a span
func (t *Tracer) FinishSpan(spanID string, status SpanStatus) {
	t.mu.Lock()
	defer t.mu.Unlock()

	span, exists := t.spans[spanID]
	if !exists {
		return
	}

	span.EndTime = time.Now()
	span.Duration = span.EndTime.Sub(span.StartTime)
	span.Status = status

	// Log span completion
	logger.Debug("Span %s completed with status %d in %v", spanID, status, span.Duration)

	// Remove from active spans (in production, you might want to keep them for a while)
	delete(t.spans, spanID)
}

// AddEvent adds an event to a span
func (t *Tracer) AddEvent(spanID string, eventName string, labels map[string]string) {
	t.mu.RLock()
	defer t.mu.RUnlock()

	span, exists := t.spans[spanID]
	if !exists {
		return
	}

	span.mu.Lock()
	defer span.mu.Unlock()

	event := SpanEvent{
		Timestamp: time.Now(),
		Name:      eventName,
		Labels:    labels,
	}

	span.Events = append(span.Events, event)
}

// GetSpans returns all active spans
func (t *Tracer) GetSpans() map[string]*Span {
	t.mu.RLock()
	defer t.mu.RUnlock()

	result := make(map[string]*Span)
	for id, span := range t.spans {
		result[id] = span
	}
	return result
}

// Instrumentation middleware

// InstrumentationMiddleware provides middleware for automatic instrumentation
type InstrumentationMiddleware struct {
	instrumentation *Instrumentation
}

// NewInstrumentationMiddleware creates a new instrumentation middleware
func NewInstrumentationMiddleware(serviceName string) *InstrumentationMiddleware {
	return &InstrumentationMiddleware{
		instrumentation: NewInstrumentation(serviceName),
	}
}

// WrapOperation wraps an operation with instrumentation
func (m *InstrumentationMiddleware) WrapOperation(ctx context.Context, operation string, labels map[string]string, fn func(context.Context) error) error {
	tracker := m.instrumentation.StartOperation(ctx, operation, labels)
	defer func() {
		if r := recover(); r != nil {
			m.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("panic: %v", r))
			panic(r) // Re-panic after recording metrics
		}
	}()

	err := fn(ctx)
	if err != nil {
		m.instrumentation.CompleteOperationWithError(tracker, err)
		return err
	}

	m.instrumentation.CompleteOperation(tracker)
	return nil
}

// WrapOperationWithRetry wraps an operation with retry logic and instrumentation
func (m *InstrumentationMiddleware) WrapOperationWithRetry(ctx context.Context, operation string, labels map[string]string, maxRetries int, fn func(context.Context) error) error {
	tracker := m.instrumentation.StartOperation(ctx, operation, labels)
	defer func() {
		if r := recover(); r != nil {
			m.instrumentation.CompleteOperationWithError(tracker, fmt.Errorf("panic: %v", r))
			panic(r) // Re-panic after recording metrics
		}
	}()

	var lastErr error
	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			m.instrumentation.RecordRetry(tracker)
		}

		err := fn(ctx)
		if err == nil {
			m.instrumentation.CompleteOperation(tracker)
			return nil
		}

		lastErr = err

		// Don't retry on last attempt
		if attempt == maxRetries {
			break
		}

		// Check if error is retryable
		if !isRetryableError(err) {
			break
		}

		// Wait before retry
		select {
		case <-ctx.Done():
			m.instrumentation.CompleteOperationWithError(tracker, ctx.Err())
			return ctx.Err()
		case <-time.After(time.Duration(attempt+1) * 100 * time.Millisecond):
		}
	}

	m.instrumentation.CompleteOperationWithError(tracker, lastErr)
	return lastErr
}

// GetInstrumentation returns the instrumentation instance
func (m *InstrumentationMiddleware) GetInstrumentation() *Instrumentation {
	return m.instrumentation
}

// Helper functions

func generateSpanID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}

func generateTraceID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}

func getTraceIDFromContext(ctx context.Context) string {
	if traceID := ctx.Value("trace_id"); traceID != nil {
		if id, ok := traceID.(string); ok {
			return id
		}
	}
	return ""
}

func isRetryableError(err error) bool {
	// This would typically check error types to determine if retryable
	// For now, return true for all errors
	return true
}

// Global instrumentation registry

var (
	instrumentationRegistry = make(map[string]*Instrumentation)
	instrumentationMu       sync.RWMutex
)

// GetInstrumentation returns instrumentation for a service
func GetInstrumentation(serviceName string) *Instrumentation {
	instrumentationMu.Lock()
	defer instrumentationMu.Unlock()

	if inst, exists := instrumentationRegistry[serviceName]; exists {
		return inst
	}

	inst := NewInstrumentation(serviceName)
	instrumentationRegistry[serviceName] = inst
	return inst
}

// GetAllInstrumentation returns all registered instrumentation
func GetAllInstrumentation() map[string]*Instrumentation {
	instrumentationMu.RLock()
	defer instrumentationMu.RUnlock()

	result := make(map[string]*Instrumentation)
	for name, inst := range instrumentationRegistry {
		result[name] = inst
	}
	return result
}

// System metrics collection

// SystemMetricsCollector collects system-level metrics
type SystemMetricsCollector struct {
	collector *Collector
	ticker    *time.Ticker
	stopCh    chan struct{}
}

// NewSystemMetricsCollector creates a new system metrics collector
func NewSystemMetricsCollector() *SystemMetricsCollector {
	return &SystemMetricsCollector{
		collector: GetCollector(),
		stopCh:    make(chan struct{}),
	}
}

// Start starts collecting system metrics
func (smc *SystemMetricsCollector) Start(interval time.Duration) {
	smc.ticker = time.NewTicker(interval)

	go func() {
		for {
			select {
			case <-smc.ticker.C:
				smc.collectSystemMetrics()
			case <-smc.stopCh:
				return
			}
		}
	}()
}

// Stop stops collecting system metrics
func (smc *SystemMetricsCollector) Stop() {
	if smc.ticker != nil {
		smc.ticker.Stop()
	}
	close(smc.stopCh)
}

// collectSystemMetrics collects current system metrics
func (smc *SystemMetricsCollector) collectSystemMetrics() {
	// Update goroutine count
	smc.collector.UpdateGoroutineCount()

	// Update memory usage (placeholder)
	// smc.collector.UpdateMemoryUsage()

	// Update CPU usage (placeholder)
	// smc.collector.UpdateCPUUsage()
}

// Performance monitoring

// PerformanceMonitor monitors performance metrics
type PerformanceMonitor struct {
	instrumentation *Instrumentation
	thresholds      map[string]time.Duration
	alerts          chan PerformanceAlert
	mu              sync.RWMutex
}

// PerformanceAlert represents a performance alert
type PerformanceAlert struct {
	Service   string
	Operation string
	Duration  time.Duration
	Threshold time.Duration
	Timestamp time.Time
	Severity  string
}

// NewPerformanceMonitor creates a new performance monitor
func NewPerformanceMonitor(serviceName string) *PerformanceMonitor {
	return &PerformanceMonitor{
		instrumentation: GetInstrumentation(serviceName),
		thresholds:      make(map[string]time.Duration),
		alerts:          make(chan PerformanceAlert, 100),
	}
}

// SetThreshold sets a performance threshold for an operation
func (pm *PerformanceMonitor) SetThreshold(operation string, threshold time.Duration) {
	pm.mu.Lock()
	defer pm.mu.Unlock()
	pm.thresholds[operation] = threshold
}

// MonitorOperation monitors an operation for performance issues
func (pm *PerformanceMonitor) MonitorOperation(operation string, duration time.Duration) {
	pm.mu.RLock()
	threshold, exists := pm.thresholds[operation]
	pm.mu.RUnlock()

	if !exists {
		return
	}

	if duration > threshold {
		alert := PerformanceAlert{
			Service:   pm.instrumentation.serviceName,
			Operation: operation,
			Duration:  duration,
			Threshold: threshold,
			Timestamp: time.Now(),
			Severity:  "warning",
		}

		if duration > threshold*2 {
			alert.Severity = "critical"
		}

		select {
		case pm.alerts <- alert:
		default:
			// Channel full, log instead
			logger.Warn("Performance alert (channel full): %s:%s took %v (threshold: %v)",
				alert.Service, alert.Operation, alert.Duration, alert.Threshold)
		}
	}
}

// GetAlerts returns performance alerts
func (pm *PerformanceMonitor) GetAlerts() []PerformanceAlert {
	alerts := make([]PerformanceAlert, 0, len(pm.alerts))

	for {
		select {
		case alert := <-pm.alerts:
			alerts = append(alerts, alert)
		default:
			return alerts
		}
	}
}
