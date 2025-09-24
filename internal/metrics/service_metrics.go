package metrics

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ServiceMetrics provides comprehensive metrics for service operations
type ServiceMetrics struct {
	serviceName string
	collector   *Collector
	mu          sync.RWMutex

	// Service-specific metrics
	operationCounters   map[string]*Metric
	operationDurations  map[string]*Metric
	operationErrors     map[string]*Metric
	operationRetries    map[string]*Metric
	circuitBreakerState map[string]*Metric
	fallbackUsage       map[string]*Metric
	batchOperationSize  map[string]*Metric
	concurrentOps       map[string]*Metric
}

// ServiceOperation represents a service operation being tracked
type ServiceOperation struct {
	serviceName string
	operation   string
	startTime   time.Time
	metrics     *ServiceMetrics
}

// NewServiceMetrics creates a new service metrics instance
func NewServiceMetrics(serviceName string) *ServiceMetrics {
	collector := GetCollector()

	sm := &ServiceMetrics{
		serviceName:         serviceName,
		collector:           collector,
		operationCounters:   make(map[string]*Metric),
		operationDurations:  make(map[string]*Metric),
		operationErrors:     make(map[string]*Metric),
		operationRetries:    make(map[string]*Metric),
		circuitBreakerState: make(map[string]*Metric),
		fallbackUsage:       make(map[string]*Metric),
		batchOperationSize:  make(map[string]*Metric),
		concurrentOps:       make(map[string]*Metric),
	}

	// Register default service metrics
	sm.registerDefaultMetrics()

	return sm
}

// registerDefaultMetrics registers default metrics for the service
func (sm *ServiceMetrics) registerDefaultMetrics() {
	// Register service-level counters
	sm.operationCounters["total_operations"] = sm.collector.RegisterCounter(
		fmt.Sprintf("arxos_%s_operations_total", sm.serviceName),
		fmt.Sprintf("Total number of operations for %s service", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)

	sm.operationCounters["successful_operations"] = sm.collector.RegisterCounter(
		fmt.Sprintf("arxos_%s_successful_operations_total", sm.serviceName),
		fmt.Sprintf("Total number of successful operations for %s service", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)

	sm.operationCounters["failed_operations"] = sm.collector.RegisterCounter(
		fmt.Sprintf("arxos_%s_failed_operations_total", sm.serviceName),
		fmt.Sprintf("Total number of failed operations for %s service", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)

	// Register service-level duration histogram
	sm.operationDurations["operation_duration"] = sm.collector.RegisterHistogram(
		fmt.Sprintf("arxos_%s_operation_duration_seconds", sm.serviceName),
		fmt.Sprintf("Duration of operations for %s service in seconds", sm.serviceName),
		[]float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
	)

	// Register error counter
	sm.operationErrors["total_errors"] = sm.collector.RegisterCounter(
		fmt.Sprintf("arxos_%s_errors_total", sm.serviceName),
		fmt.Sprintf("Total number of errors for %s service", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)

	// Register retry counter
	sm.operationRetries["total_retries"] = sm.collector.RegisterCounter(
		fmt.Sprintf("arxos_%s_retries_total", sm.serviceName),
		fmt.Sprintf("Total number of retries for %s service", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)

	// Register circuit breaker state gauge
	sm.circuitBreakerState["circuit_breaker_state"] = sm.collector.RegisterGauge(
		fmt.Sprintf("arxos_%s_circuit_breaker_state", sm.serviceName),
		fmt.Sprintf("Circuit breaker state for %s service (0=closed, 1=open, 2=half-open)", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)

	// Register fallback usage counter
	sm.fallbackUsage["fallback_usage"] = sm.collector.RegisterCounter(
		fmt.Sprintf("arxos_%s_fallback_usage_total", sm.serviceName),
		fmt.Sprintf("Total number of fallback operations for %s service", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)

	// Register batch operation size histogram
	sm.batchOperationSize["batch_size"] = sm.collector.RegisterHistogram(
		fmt.Sprintf("arxos_%s_batch_operation_size", sm.serviceName),
		fmt.Sprintf("Size of batch operations for %s service", sm.serviceName),
		[]float64{1, 5, 10, 25, 50, 100, 250, 500, 1000},
	)

	// Register concurrent operations gauge
	sm.concurrentOps["concurrent_operations"] = sm.collector.RegisterGauge(
		fmt.Sprintf("arxos_%s_concurrent_operations", sm.serviceName),
		fmt.Sprintf("Number of concurrent operations for %s service", sm.serviceName),
		map[string]string{"service": sm.serviceName},
	)
}

// StartOperation starts tracking a service operation
func (sm *ServiceMetrics) StartOperation(operation string) *ServiceOperation {
	// Increment total operations counter
	sm.incrementOperationCounter(operation, "total")

	// Increment concurrent operations
	sm.incrementConcurrentOps(operation)

	return &ServiceOperation{
		serviceName: sm.serviceName,
		operation:   operation,
		startTime:   time.Now(),
		metrics:     sm,
	}
}

// CompleteOperation completes a service operation successfully
func (so *ServiceOperation) CompleteOperation() {
	duration := time.Since(so.startTime)

	// Record success metrics
	so.metrics.incrementOperationCounter(so.operation, "success")
	so.metrics.recordOperationDuration(so.operation, duration)
	so.metrics.decrementConcurrentOps(so.operation)
}

// CompleteOperationWithError completes a service operation with an error
func (so *ServiceOperation) CompleteOperationWithError(err error) {
	duration := time.Since(so.startTime)

	// Record error metrics
	so.metrics.incrementOperationCounter(so.operation, "error")
	so.metrics.recordOperationDuration(so.operation, duration)
	so.metrics.recordOperationError(so.operation, err)
	so.metrics.decrementConcurrentOps(so.operation)
}

// RecordRetry records a retry attempt
func (sm *ServiceMetrics) RecordRetry(operation string) {
	sm.incrementOperationRetry(operation)
}

// RecordCircuitBreakerState records the circuit breaker state
func (sm *ServiceMetrics) RecordCircuitBreakerState(operation string, state int) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific circuit breaker metric
	metricName := fmt.Sprintf("circuit_breaker_%s", operation)
	metric, exists := sm.circuitBreakerState[metricName]
	if !exists {
		metric = sm.collector.RegisterGauge(
			fmt.Sprintf("arxos_%s_circuit_breaker_%s_state", sm.serviceName, operation),
			fmt.Sprintf("Circuit breaker state for %s operation in %s service", operation, sm.serviceName),
			map[string]string{"service": sm.serviceName, "operation": operation},
		)
		sm.circuitBreakerState[metricName] = metric
	}

	metric.Set(float64(state))
}

// RecordFallbackUsage records fallback operation usage
func (sm *ServiceMetrics) RecordFallbackUsage(operation string) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific fallback metric
	metricName := fmt.Sprintf("fallback_%s", operation)
	metric, exists := sm.fallbackUsage[metricName]
	if !exists {
		metric = sm.collector.RegisterCounter(
			fmt.Sprintf("arxos_%s_fallback_%s_total", sm.serviceName, operation),
			fmt.Sprintf("Fallback usage for %s operation in %s service", operation, sm.serviceName),
			map[string]string{"service": sm.serviceName, "operation": operation},
		)
		sm.fallbackUsage[metricName] = metric
	}

	metric.Inc()
}

// RecordBatchOperation records a batch operation
func (sm *ServiceMetrics) RecordBatchOperation(operation string, batchSize int) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific batch size metric
	metricName := fmt.Sprintf("batch_%s", operation)
	metric, exists := sm.batchOperationSize[metricName]
	if !exists {
		metric = sm.collector.RegisterHistogram(
			fmt.Sprintf("arxos_%s_batch_%s_size", sm.serviceName, operation),
			fmt.Sprintf("Batch size for %s operation in %s service", operation, sm.serviceName),
			[]float64{1, 5, 10, 25, 50, 100, 250, 500, 1000},
		)
		sm.batchOperationSize[metricName] = metric
	}

	metric.Observe(float64(batchSize))
}

// Helper methods for internal metric management

func (sm *ServiceMetrics) incrementOperationCounter(operation, counterType string) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific counter
	metricName := fmt.Sprintf("%s_%s", counterType, operation)
	metric, exists := sm.operationCounters[metricName]
	if !exists {
		metric = sm.collector.RegisterCounter(
			fmt.Sprintf("arxos_%s_%s_%s_total", sm.serviceName, counterType, operation),
			fmt.Sprintf("%s operations for %s in %s service", counterType, operation, sm.serviceName),
			map[string]string{"service": sm.serviceName, "operation": operation},
		)
		sm.operationCounters[metricName] = metric
	}

	metric.Inc()
}

func (sm *ServiceMetrics) recordOperationDuration(operation string, duration time.Duration) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific duration metric
	metricName := fmt.Sprintf("duration_%s", operation)
	metric, exists := sm.operationDurations[metricName]
	if !exists {
		metric = sm.collector.RegisterHistogram(
			fmt.Sprintf("arxos_%s_%s_duration_seconds", sm.serviceName, operation),
			fmt.Sprintf("Duration of %s operation in %s service", operation, sm.serviceName),
			[]float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
		)
		sm.operationDurations[metricName] = metric
	}

	metric.Observe(duration.Seconds())
}

func (sm *ServiceMetrics) recordOperationError(operation string, err error) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific error metric
	metricName := fmt.Sprintf("error_%s", operation)
	metric, exists := sm.operationErrors[metricName]
	if !exists {
		metric = sm.collector.RegisterCounter(
			fmt.Sprintf("arxos_%s_%s_errors_total", sm.serviceName, operation),
			fmt.Sprintf("Errors for %s operation in %s service", operation, sm.serviceName),
			map[string]string{"service": sm.serviceName, "operation": operation},
		)
		sm.operationErrors[metricName] = metric
	}

	metric.Inc()
}

func (sm *ServiceMetrics) incrementOperationRetry(operation string) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific retry metric
	metricName := fmt.Sprintf("retry_%s", operation)
	metric, exists := sm.operationRetries[metricName]
	if !exists {
		metric = sm.collector.RegisterCounter(
			fmt.Sprintf("arxos_%s_%s_retries_total", sm.serviceName, operation),
			fmt.Sprintf("Retries for %s operation in %s service", operation, sm.serviceName),
			map[string]string{"service": sm.serviceName, "operation": operation},
		)
		sm.operationRetries[metricName] = metric
	}

	metric.Inc()
}

func (sm *ServiceMetrics) incrementConcurrentOps(operation string) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific concurrent ops metric
	metricName := fmt.Sprintf("concurrent_%s", operation)
	metric, exists := sm.concurrentOps[metricName]
	if !exists {
		metric = sm.collector.RegisterGauge(
			fmt.Sprintf("arxos_%s_%s_concurrent_operations", sm.serviceName, operation),
			fmt.Sprintf("Concurrent %s operations in %s service", operation, sm.serviceName),
			map[string]string{"service": sm.serviceName, "operation": operation},
		)
		sm.concurrentOps[metricName] = metric
	}

	metric.Inc()
}

func (sm *ServiceMetrics) decrementConcurrentOps(operation string) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create operation-specific concurrent ops metric
	metricName := fmt.Sprintf("concurrent_%s", operation)
	metric, exists := sm.concurrentOps[metricName]
	if !exists {
		metric = sm.collector.RegisterGauge(
			fmt.Sprintf("arxos_%s_%s_concurrent_operations", sm.serviceName, operation),
			fmt.Sprintf("Concurrent %s operations in %s service", operation, sm.serviceName),
			map[string]string{"service": sm.serviceName, "operation": operation},
		)
		sm.concurrentOps[metricName] = metric
	}

	metric.Set(metric.Get() - 1)
}

// Service metrics aggregation and reporting

// ServiceMetricsSummary provides a summary of service metrics
type ServiceMetricsSummary struct {
	ServiceName          string                 `json:"service_name"`
	TotalOperations      int64                  `json:"total_operations"`
	SuccessfulOperations int64                  `json:"successful_operations"`
	FailedOperations     int64                  `json:"failed_operations"`
	ErrorRate            float64                `json:"error_rate"`
	AverageDuration      float64                `json:"average_duration_seconds"`
	ConcurrentOps        int64                  `json:"concurrent_operations"`
	CircuitBreakerState  map[string]int         `json:"circuit_breaker_states"`
	OperationMetrics     map[string]interface{} `json:"operation_metrics"`
	Timestamp            time.Time              `json:"timestamp"`
}

// GetServiceSummary returns a summary of service metrics
func (sm *ServiceMetrics) GetServiceSummary() *ServiceMetricsSummary {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	summary := &ServiceMetricsSummary{
		ServiceName:         sm.serviceName,
		CircuitBreakerState: make(map[string]int),
		OperationMetrics:    make(map[string]interface{}),
		Timestamp:           time.Now(),
	}

	// Get basic metrics
	if totalOps, exists := sm.operationCounters["total_operations"]; exists {
		summary.TotalOperations = int64(totalOps.Get())
	}

	if successOps, exists := sm.operationCounters["successful_operations"]; exists {
		summary.SuccessfulOperations = int64(successOps.Get())
	}

	if failedOps, exists := sm.operationCounters["failed_operations"]; exists {
		summary.FailedOperations = int64(failedOps.Get())
	}

	// Calculate error rate
	if summary.TotalOperations > 0 {
		summary.ErrorRate = float64(summary.FailedOperations) / float64(summary.TotalOperations)
	}

	// Get average duration (simplified - would need proper implementation)
	if durationMetric, exists := sm.operationDurations["operation_duration"]; exists {
		summary.AverageDuration = durationMetric.Get() // This would need to be implemented in Metric
	}

	// Get concurrent operations
	if concurrentOps, exists := sm.concurrentOps["concurrent_operations"]; exists {
		summary.ConcurrentOps = int64(concurrentOps.Get())
	}

	// Get circuit breaker states
	for name, metric := range sm.circuitBreakerState {
		summary.CircuitBreakerState[name] = int(metric.Get())
	}

	return summary
}

// Service metrics middleware

// ServiceMetricsMiddleware provides middleware for automatic service metrics collection
type ServiceMetricsMiddleware struct {
	metrics *ServiceMetrics
}

// NewServiceMetricsMiddleware creates a new service metrics middleware
func NewServiceMetricsMiddleware(serviceName string) *ServiceMetricsMiddleware {
	return &ServiceMetricsMiddleware{
		metrics: NewServiceMetrics(serviceName),
	}
}

// WrapOperation wraps an operation with metrics collection
func (m *ServiceMetricsMiddleware) WrapOperation(operation string, fn func() error) error {
	op := m.metrics.StartOperation(operation)
	defer func() {
		if r := recover(); r != nil {
			op.CompleteOperationWithError(fmt.Errorf("panic: %v", r))
			panic(r) // Re-panic after recording metrics
		}
	}()

	err := fn()
	if err != nil {
		op.CompleteOperationWithError(err)
		return err
	}

	op.CompleteOperation()
	return nil
}

// WrapOperationWithContext wraps an operation with context and metrics collection
func (m *ServiceMetricsMiddleware) WrapOperationWithContext(ctx context.Context, operation string, fn func(context.Context) error) error {
	op := m.metrics.StartOperation(operation)
	defer func() {
		if r := recover(); r != nil {
			op.CompleteOperationWithError(fmt.Errorf("panic: %v", r))
			panic(r) // Re-panic after recording metrics
		}
	}()

	err := fn(ctx)
	if err != nil {
		op.CompleteOperationWithError(err)
		return err
	}

	op.CompleteOperation()
	return nil
}

// GetMetrics returns the service metrics instance
func (m *ServiceMetricsMiddleware) GetMetrics() *ServiceMetrics {
	return m.metrics
}

// Global service metrics registry

var (
	serviceMetricsRegistry = make(map[string]*ServiceMetrics)
	registryMu             sync.RWMutex
)

// GetServiceMetrics returns metrics for a service, creating if necessary
func GetServiceMetrics(serviceName string) *ServiceMetrics {
	registryMu.Lock()
	defer registryMu.Unlock()

	if metrics, exists := serviceMetricsRegistry[serviceName]; exists {
		return metrics
	}

	metrics := NewServiceMetrics(serviceName)
	serviceMetricsRegistry[serviceName] = metrics
	return metrics
}

// GetAllServiceMetrics returns all registered service metrics
func GetAllServiceMetrics() map[string]*ServiceMetrics {
	registryMu.RLock()
	defer registryMu.RUnlock()

	result := make(map[string]*ServiceMetrics)
	for name, metrics := range serviceMetricsRegistry {
		result[name] = metrics
	}
	return result
}

// GetServiceMetricsSummary returns a summary of all service metrics
func GetServiceMetricsSummary() map[string]*ServiceMetricsSummary {
	allMetrics := GetAllServiceMetrics()
	summary := make(map[string]*ServiceMetricsSummary)

	for name, metrics := range allMetrics {
		summary[name] = metrics.GetServiceSummary()
	}

	return summary
}
