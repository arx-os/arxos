package realtime

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"gorm.io/gorm"
)

// AnalyticsEventType represents types of analytics events
type AnalyticsEventType string

const (
	AnalyticsEventTypeConnection    AnalyticsEventType = "connection"
	AnalyticsEventTypeDisconnection AnalyticsEventType = "disconnection"
	AnalyticsEventTypeMessage       AnalyticsEventType = "message"
	AnalyticsEventTypeEdit          AnalyticsEventType = "edit"
	AnalyticsEventTypeSync          AnalyticsEventType = "sync"
	AnalyticsEventTypeConflict      AnalyticsEventType = "conflict"
	AnalyticsEventTypeAnnotation    AnalyticsEventType = "annotation"
	AnalyticsEventTypeSession       AnalyticsEventType = "session"
	AnalyticsEventTypePerformance   AnalyticsEventType = "performance"
	AnalyticsEventTypeError         AnalyticsEventType = "error"
)

// MetricType represents types of metrics
type MetricType string

const (
	MetricTypeCounter   MetricType = "counter"
	MetricTypeGauge     MetricType = "gauge"
	MetricTypeHistogram MetricType = "histogram"
	MetricTypeTimer     MetricType = "timer"
)

// AnalyticsEvent represents an analytics event
type AnalyticsEvent struct {
	ID        string             `json:"id" gorm:"primaryKey"`
	EventType AnalyticsEventType `json:"event_type"`
	UserID    string             `json:"user_id"`
	SessionID string             `json:"session_id"`
	RoomID    string             `json:"room_id"`
	ElementID *string            `json:"element_id"`
	Data      json.RawMessage    `json:"data"`
	Metadata  json.RawMessage    `json:"metadata"`
	Timestamp time.Time          `json:"timestamp"`
	CreatedAt time.Time          `json:"created_at"`
}

// Metric represents a metric measurement
type Metric struct {
	ID        string          `json:"id" gorm:"primaryKey"`
	Name      string          `json:"name"`
	Type      MetricType      `json:"type"`
	Value     float64         `json:"value"`
	Unit      string          `json:"unit"`
	Tags      json.RawMessage `json:"tags"`
	UserID    *string         `json:"user_id"`
	SessionID *string         `json:"session_id"`
	RoomID    *string         `json:"room_id"`
	Timestamp time.Time       `json:"timestamp"`
	CreatedAt time.Time       `json:"created_at"`
}

// PerformanceMetric represents a performance metric
type PerformanceMetric struct {
	ID           string          `json:"id" gorm:"primaryKey"`
	MetricName   string          `json:"metric_name"`
	Value        float64         `json:"value"`
	Unit         string          `json:"unit"`
	MinValue     float64         `json:"min_value"`
	MaxValue     float64         `json:"max_value"`
	AvgValue     float64         `json:"avg_value"`
	Count        int64           `json:"count"`
	Percentile95 float64         `json:"percentile_95"`
	Percentile99 float64         `json:"percentile_99"`
	Tags         json.RawMessage `json:"tags"`
	Timestamp    time.Time       `json:"timestamp"`
	CreatedAt    time.Time       `json:"created_at"`
}

// UserActivity represents user activity tracking
type UserActivity struct {
	ID           string          `json:"id" gorm:"primaryKey"`
	UserID       string          `json:"user_id"`
	SessionID    string          `json:"session_id"`
	RoomID       string          `json:"room_id"`
	ActivityType string          `json:"activity_type"`
	Duration     time.Duration   `json:"duration"`
	ElementID    *string         `json:"element_id"`
	Data         json.RawMessage `json:"data"`
	StartTime    time.Time       `json:"start_time"`
	EndTime      time.Time       `json:"end_time"`
	CreatedAt    time.Time       `json:"created_at"`
}

// AnalyticsConfig represents analytics configuration
type AnalyticsConfig struct {
	EventRetentionPeriod       time.Duration `json:"event_retention_period"`
	MetricRetentionPeriod      time.Duration `json:"metric_retention_period"`
	PerformanceRetentionPeriod time.Duration `json:"performance_retention_period"`
	ActivityRetentionPeriod    time.Duration `json:"activity_retention_period"`
	BatchSize                  int           `json:"batch_size"`
	FlushInterval              time.Duration `json:"flush_interval"`
	EnableRealTimeMetrics      bool          `json:"enable_real_time_metrics"`
	EnablePerformanceTracking  bool          `json:"enable_performance_tracking"`
	EnableUserActivityTracking bool          `json:"enable_user_activity_tracking"`
	CleanupInterval            time.Duration `json:"cleanup_interval"`
	MaxEventsPerBatch          int           `json:"max_events_per_batch"`
	EnableCompression          bool          `json:"enable_compression"`
}

// RealtimeAnalyticsService handles real-time analytics and metrics
type RealtimeAnalyticsService struct {
	db              *gorm.DB
	mu              sync.RWMutex
	events          map[string]*AnalyticsEvent
	metrics         map[string]*Metric
	performance     map[string]*PerformanceMetric
	activities      map[string]*UserActivity
	config          *AnalyticsConfig
	eventChan       chan *AnalyticsEvent
	metricChan      chan *Metric
	performanceChan chan *PerformanceMetric
	activityChan    chan *UserActivity
	stopChan        chan struct{}
	isRunning       bool
}

// NewRealtimeAnalyticsService creates a new real-time analytics service
func NewRealtimeAnalyticsService(db *gorm.DB, config *AnalyticsConfig) *RealtimeAnalyticsService {
	if config == nil {
		config = &AnalyticsConfig{
			EventRetentionPeriod:       24 * time.Hour,
			MetricRetentionPeriod:      7 * 24 * time.Hour,
			PerformanceRetentionPeriod: 7 * 24 * time.Hour,
			ActivityRetentionPeriod:    30 * 24 * time.Hour,
			BatchSize:                  1000,
			FlushInterval:              5 * time.Second,
			EnableRealTimeMetrics:      true,
			EnablePerformanceTracking:  true,
			EnableUserActivityTracking: true,
			CleanupInterval:            1 * time.Hour,
			MaxEventsPerBatch:          1000,
			EnableCompression:          true,
		}
	}

	return &RealtimeAnalyticsService{
		db:              db,
		events:          make(map[string]*AnalyticsEvent),
		metrics:         make(map[string]*Metric),
		performance:     make(map[string]*PerformanceMetric),
		activities:      make(map[string]*UserActivity),
		config:          config,
		eventChan:       make(chan *AnalyticsEvent, 10000),
		metricChan:      make(chan *Metric, 10000),
		performanceChan: make(chan *PerformanceMetric, 10000),
		activityChan:    make(chan *UserActivity, 10000),
		stopChan:        make(chan struct{}),
	}
}

// Start starts the real-time analytics service
func (ras *RealtimeAnalyticsService) Start(ctx context.Context) error {
	ras.mu.Lock()
	defer ras.mu.Unlock()

	if ras.isRunning {
		return fmt.Errorf("analytics service is already running")
	}

	// Auto-migrate database tables
	if err := ras.db.AutoMigrate(&AnalyticsEvent{}, &Metric{}, &PerformanceMetric{}, &UserActivity{}); err != nil {
		return fmt.Errorf("failed to migrate analytics tables: %w", err)
	}

	// Load existing data from database
	if err := ras.loadExistingData(ctx); err != nil {
		return fmt.Errorf("failed to load existing data: %w", err)
	}

	ras.isRunning = true

	// Start background goroutines
	go ras.eventProcessingLoop(ctx)
	go ras.metricProcessingLoop(ctx)
	go ras.performanceProcessingLoop(ctx)
	go ras.activityProcessingLoop(ctx)
	go ras.cleanupLoop(ctx)

	return nil
}

// Stop stops the real-time analytics service
func (ras *RealtimeAnalyticsService) Stop() {
	ras.mu.Lock()
	defer ras.mu.Unlock()

	if !ras.isRunning {
		return
	}

	close(ras.stopChan)
	ras.isRunning = false
}

// TrackEvent tracks an analytics event
func (ras *RealtimeAnalyticsService) TrackEvent(ctx context.Context, eventType AnalyticsEventType, userID, sessionID, roomID string, elementID *string, data map[string]interface{}) error {
	event := &AnalyticsEvent{
		ID:        generateEventID(),
		EventType: eventType,
		UserID:    userID,
		SessionID: sessionID,
		RoomID:    roomID,
		ElementID: elementID,
		Data:      mustMarshalJSON(data),
		Timestamp: time.Now(),
		CreatedAt: time.Now(),
	}

	// Send to processing channel
	select {
	case ras.eventChan <- event:
		return nil
	default:
		return fmt.Errorf("event channel is full")
	}
}

// TrackMetric tracks a metric
func (ras *RealtimeAnalyticsService) TrackMetric(ctx context.Context, name string, metricType MetricType, value float64, unit string, tags map[string]string, userID, sessionID, roomID *string) error {
	metric := &Metric{
		ID:        generateMetricID(),
		Name:      name,
		Type:      metricType,
		Value:     value,
		Unit:      unit,
		Tags:      mustMarshalJSON(tags),
		UserID:    userID,
		SessionID: sessionID,
		RoomID:    roomID,
		Timestamp: time.Now(),
		CreatedAt: time.Now(),
	}

	// Send to processing channel
	select {
	case ras.metricChan <- metric:
		return nil
	default:
		return fmt.Errorf("metric channel is full")
	}
}

// TrackPerformance tracks a performance metric
func (ras *RealtimeAnalyticsService) TrackPerformance(ctx context.Context, metricName string, value float64, unit string, tags map[string]string) error {
	performance := &PerformanceMetric{
		ID:           generatePerformanceID(),
		MetricName:   metricName,
		Value:        value,
		Unit:         unit,
		MinValue:     value,
		MaxValue:     value,
		AvgValue:     value,
		Count:        1,
		Percentile95: value,
		Percentile99: value,
		Tags:         mustMarshalJSON(tags),
		Timestamp:    time.Now(),
		CreatedAt:    time.Now(),
	}

	// Send to processing channel
	select {
	case ras.performanceChan <- performance:
		return nil
	default:
		return fmt.Errorf("performance channel is full")
	}
}

// TrackActivity tracks user activity
func (ras *RealtimeAnalyticsService) TrackActivity(ctx context.Context, userID, sessionID, roomID, activityType string, elementID *string, data map[string]interface{}, duration time.Duration) error {
	activity := &UserActivity{
		ID:           generateActivityID(),
		UserID:       userID,
		SessionID:    sessionID,
		RoomID:       roomID,
		ActivityType: activityType,
		Duration:     duration,
		ElementID:    elementID,
		Data:         mustMarshalJSON(data),
		StartTime:    time.Now().Add(-duration),
		EndTime:      time.Now(),
		CreatedAt:    time.Now(),
	}

	// Send to processing channel
	select {
	case ras.activityChan <- activity:
		return nil
	default:
		return fmt.Errorf("activity channel is full")
	}
}

// GetEvents retrieves analytics events with filters
func (ras *RealtimeAnalyticsService) GetEvents(ctx context.Context, eventType *AnalyticsEventType, userID *string, sessionID *string, roomID *string, startTime, endTime *time.Time, limit int) ([]AnalyticsEvent, error) {
	ras.mu.RLock()
	defer ras.mu.RUnlock()

	if limit <= 0 {
		limit = 100
	}

	query := ras.db.Model(&AnalyticsEvent{})

	if eventType != nil {
		query = query.Where("event_type = ?", *eventType)
	}
	if userID != nil {
		query = query.Where("user_id = ?", *userID)
	}
	if sessionID != nil {
		query = query.Where("session_id = ?", *sessionID)
	}
	if roomID != nil {
		query = query.Where("room_id = ?", *roomID)
	}
	if startTime != nil {
		query = query.Where("timestamp >= ?", *startTime)
	}
	if endTime != nil {
		query = query.Where("timestamp <= ?", *endTime)
	}

	var events []AnalyticsEvent
	if err := query.Order("timestamp DESC").Limit(limit).Find(&events).Error; err != nil {
		return nil, fmt.Errorf("failed to get events: %w", err)
	}

	return events, nil
}

// GetMetrics retrieves metrics with filters
func (ras *RealtimeAnalyticsService) GetMetrics(ctx context.Context, name *string, metricType *MetricType, userID *string, sessionID *string, roomID *string, startTime, endTime *time.Time, limit int) ([]Metric, error) {
	ras.mu.RLock()
	defer ras.mu.RUnlock()

	if limit <= 0 {
		limit = 100
	}

	query := ras.db.Model(&Metric{})

	if name != nil {
		query = query.Where("name = ?", *name)
	}
	if metricType != nil {
		query = query.Where("type = ?", *metricType)
	}
	if userID != nil {
		query = query.Where("user_id = ?", *userID)
	}
	if sessionID != nil {
		query = query.Where("session_id = ?", *sessionID)
	}
	if roomID != nil {
		query = query.Where("room_id = ?", *roomID)
	}
	if startTime != nil {
		query = query.Where("timestamp >= ?", *startTime)
	}
	if endTime != nil {
		query = query.Where("timestamp <= ?", *endTime)
	}

	var metrics []Metric
	if err := query.Order("timestamp DESC").Limit(limit).Find(&metrics).Error; err != nil {
		return nil, fmt.Errorf("failed to get metrics: %w", err)
	}

	return metrics, nil
}

// GetPerformanceMetrics retrieves performance metrics
func (ras *RealtimeAnalyticsService) GetPerformanceMetrics(ctx context.Context, metricName *string, startTime, endTime *time.Time, limit int) ([]PerformanceMetric, error) {
	ras.mu.RLock()
	defer ras.mu.RUnlock()

	if limit <= 0 {
		limit = 100
	}

	query := ras.db.Model(&PerformanceMetric{})

	if metricName != nil {
		query = query.Where("metric_name = ?", *metricName)
	}
	if startTime != nil {
		query = query.Where("timestamp >= ?", *startTime)
	}
	if endTime != nil {
		query = query.Where("timestamp <= ?", *endTime)
	}

	var metrics []PerformanceMetric
	if err := query.Order("timestamp DESC").Limit(limit).Find(&metrics).Error; err != nil {
		return nil, fmt.Errorf("failed to get performance metrics: %w", err)
	}

	return metrics, nil
}

// GetUserActivities retrieves user activities
func (ras *RealtimeAnalyticsService) GetUserActivities(ctx context.Context, userID *string, sessionID *string, roomID *string, activityType *string, startTime, endTime *time.Time, limit int) ([]UserActivity, error) {
	ras.mu.RLock()
	defer ras.mu.RUnlock()

	if limit <= 0 {
		limit = 100
	}

	query := ras.db.Model(&UserActivity{})

	if userID != nil {
		query = query.Where("user_id = ?", *userID)
	}
	if sessionID != nil {
		query = query.Where("session_id = ?", *sessionID)
	}
	if roomID != nil {
		query = query.Where("room_id = ?", *roomID)
	}
	if activityType != nil {
		query = query.Where("activity_type = ?", *activityType)
	}
	if startTime != nil {
		query = query.Where("start_time >= ?", *startTime)
	}
	if endTime != nil {
		query = query.Where("end_time <= ?", *endTime)
	}

	var activities []UserActivity
	if err := query.Order("start_time DESC").Limit(limit).Find(&activities).Error; err != nil {
		return nil, fmt.Errorf("failed to get user activities: %w", err)
	}

	return activities, nil
}

// GetAnalyticsSummary returns a summary of analytics data
func (ras *RealtimeAnalyticsService) GetAnalyticsSummary(ctx context.Context, startTime, endTime time.Time) (map[string]interface{}, error) {
	ras.mu.RLock()
	defer ras.mu.RUnlock()

	summary := make(map[string]interface{})

	// Event counts by type
	var eventCounts []struct {
		EventType string `json:"event_type"`
		Count     int64  `json:"count"`
	}
	if err := ras.db.Model(&AnalyticsEvent{}).
		Select("event_type, count(*) as count").
		Where("timestamp BETWEEN ? AND ?", startTime, endTime).
		Group("event_type").
		Find(&eventCounts).Error; err != nil {
		return nil, fmt.Errorf("failed to get event counts: %w", err)
	}
	summary["event_counts"] = eventCounts

	// Metric summaries
	var metricSummaries []struct {
		Name  string  `json:"name"`
		Type  string  `json:"type"`
		Avg   float64 `json:"avg"`
		Min   float64 `json:"min"`
		Max   float64 `json:"max"`
		Count int64   `json:"count"`
	}
	if err := ras.db.Model(&Metric{}).
		Select("name, type, avg(value) as avg, min(value) as min, max(value) as max, count(*) as count").
		Where("timestamp BETWEEN ? AND ?", startTime, endTime).
		Group("name, type").
		Find(&metricSummaries).Error; err != nil {
		return nil, fmt.Errorf("failed to get metric summaries: %w", err)
	}
	summary["metric_summaries"] = metricSummaries

	// Performance summaries
	var performanceSummaries []struct {
		MetricName string  `json:"metric_name"`
		AvgValue   float64 `json:"avg_value"`
		MinValue   float64 `json:"min_value"`
		MaxValue   float64 `json:"max_value"`
		Count      int64   `json:"count"`
	}
	if err := ras.db.Model(&PerformanceMetric{}).
		Select("metric_name, avg(avg_value) as avg_value, min(min_value) as min_value, max(max_value) as max_value, sum(count) as count").
		Where("timestamp BETWEEN ? AND ?", startTime, endTime).
		Group("metric_name").
		Find(&performanceSummaries).Error; err != nil {
		return nil, fmt.Errorf("failed to get performance summaries: %w", err)
	}
	summary["performance_summaries"] = performanceSummaries

	// Activity summaries
	var activitySummaries []struct {
		ActivityType  string  `json:"activity_type"`
		TotalDuration float64 `json:"total_duration"`
		Count         int64   `json:"count"`
	}
	if err := ras.db.Model(&UserActivity{}).
		Select("activity_type, sum(extract(epoch from duration)) as total_duration, count(*) as count").
		Where("start_time BETWEEN ? AND ?", startTime, endTime).
		Group("activity_type").
		Find(&activitySummaries).Error; err != nil {
		return nil, fmt.Errorf("failed to get activity summaries: %w", err)
	}
	summary["activity_summaries"] = activitySummaries

	return summary, nil
}

// loadExistingData loads existing data from database
func (ras *RealtimeAnalyticsService) loadExistingData(ctx context.Context) error {
	// Load recent events (last 10000)
	var events []AnalyticsEvent
	if err := ras.db.Order("created_at DESC").Limit(10000).Find(&events).Error; err != nil {
		return fmt.Errorf("failed to load events: %w", err)
	}

	for _, event := range events {
		ras.events[event.ID] = &event
	}

	// Load recent metrics (last 10000)
	var metrics []Metric
	if err := ras.db.Order("created_at DESC").Limit(10000).Find(&metrics).Error; err != nil {
		return fmt.Errorf("failed to load metrics: %w", err)
	}

	for _, metric := range metrics {
		ras.metrics[metric.ID] = &metric
	}

	// Load recent performance metrics (last 10000)
	var performance []PerformanceMetric
	if err := ras.db.Order("created_at DESC").Limit(10000).Find(&performance).Error; err != nil {
		return fmt.Errorf("failed to load performance metrics: %w", err)
	}

	for _, perf := range performance {
		ras.performance[perf.ID] = &perf
	}

	// Load recent activities (last 10000)
	var activities []UserActivity
	if err := ras.db.Order("created_at DESC").Limit(10000).Find(&activities).Error; err != nil {
		return fmt.Errorf("failed to load activities: %w", err)
	}

	for _, activity := range activities {
		ras.activities[activity.ID] = &activity
	}

	return nil
}

// eventProcessingLoop processes analytics events
func (ras *RealtimeAnalyticsService) eventProcessingLoop(ctx context.Context) {
	batch := make([]*AnalyticsEvent, 0, ras.config.BatchSize)
	ticker := time.NewTicker(ras.config.FlushInterval)
	defer ticker.Stop()

	for {
		select {
		case event := <-ras.eventChan:
			batch = append(batch, event)
			if len(batch) >= ras.config.MaxEventsPerBatch {
				ras.flushEvents(batch)
				batch = batch[:0]
			}
		case <-ticker.C:
			if len(batch) > 0 {
				ras.flushEvents(batch)
				batch = batch[:0]
			}
		case <-ras.stopChan:
			if len(batch) > 0 {
				ras.flushEvents(batch)
			}
			return
		case <-ctx.Done():
			if len(batch) > 0 {
				ras.flushEvents(batch)
			}
			return
		}
	}
}

// metricProcessingLoop processes metrics
func (ras *RealtimeAnalyticsService) metricProcessingLoop(ctx context.Context) {
	batch := make([]*Metric, 0, ras.config.BatchSize)
	ticker := time.NewTicker(ras.config.FlushInterval)
	defer ticker.Stop()

	for {
		select {
		case metric := <-ras.metricChan:
			batch = append(batch, metric)
			if len(batch) >= ras.config.MaxEventsPerBatch {
				ras.flushMetrics(batch)
				batch = batch[:0]
			}
		case <-ticker.C:
			if len(batch) > 0 {
				ras.flushMetrics(batch)
				batch = batch[:0]
			}
		case <-ras.stopChan:
			if len(batch) > 0 {
				ras.flushMetrics(batch)
			}
			return
		case <-ctx.Done():
			if len(batch) > 0 {
				ras.flushMetrics(batch)
			}
			return
		}
	}
}

// performanceProcessingLoop processes performance metrics
func (ras *RealtimeAnalyticsService) performanceProcessingLoop(ctx context.Context) {
	batch := make([]*PerformanceMetric, 0, ras.config.BatchSize)
	ticker := time.NewTicker(ras.config.FlushInterval)
	defer ticker.Stop()

	for {
		select {
		case perf := <-ras.performanceChan:
			batch = append(batch, perf)
			if len(batch) >= ras.config.MaxEventsPerBatch {
				ras.flushPerformanceMetrics(batch)
				batch = batch[:0]
			}
		case <-ticker.C:
			if len(batch) > 0 {
				ras.flushPerformanceMetrics(batch)
				batch = batch[:0]
			}
		case <-ras.stopChan:
			if len(batch) > 0 {
				ras.flushPerformanceMetrics(batch)
			}
			return
		case <-ctx.Done():
			if len(batch) > 0 {
				ras.flushPerformanceMetrics(batch)
			}
			return
		}
	}
}

// activityProcessingLoop processes user activities
func (ras *RealtimeAnalyticsService) activityProcessingLoop(ctx context.Context) {
	batch := make([]*UserActivity, 0, ras.config.BatchSize)
	ticker := time.NewTicker(ras.config.FlushInterval)
	defer ticker.Stop()

	for {
		select {
		case activity := <-ras.activityChan:
			batch = append(batch, activity)
			if len(batch) >= ras.config.MaxEventsPerBatch {
				ras.flushActivities(batch)
				batch = batch[:0]
			}
		case <-ticker.C:
			if len(batch) > 0 {
				ras.flushActivities(batch)
				batch = batch[:0]
			}
		case <-ras.stopChan:
			if len(batch) > 0 {
				ras.flushActivities(batch)
			}
			return
		case <-ctx.Done():
			if len(batch) > 0 {
				ras.flushActivities(batch)
			}
			return
		}
	}
}

// flushEvents flushes events to database
func (ras *RealtimeAnalyticsService) flushEvents(events []*AnalyticsEvent) {
	if len(events) == 0 {
		return
	}

	ras.mu.Lock()
	defer ras.mu.Unlock()

	// Store in memory
	for _, event := range events {
		ras.events[event.ID] = event
	}

	// Save to database
	if err := ras.db.CreateInBatches(events, ras.config.BatchSize).Error; err != nil {
		// Log error but continue
	}
}

// flushMetrics flushes metrics to database
func (ras *RealtimeAnalyticsService) flushMetrics(metrics []*Metric) {
	if len(metrics) == 0 {
		return
	}

	ras.mu.Lock()
	defer ras.mu.Unlock()

	// Store in memory
	for _, metric := range metrics {
		ras.metrics[metric.ID] = metric
	}

	// Save to database
	if err := ras.db.CreateInBatches(metrics, ras.config.BatchSize).Error; err != nil {
		// Log error but continue
	}
}

// flushPerformanceMetrics flushes performance metrics to database
func (ras *RealtimeAnalyticsService) flushPerformanceMetrics(metrics []*PerformanceMetric) {
	if len(metrics) == 0 {
		return
	}

	ras.mu.Lock()
	defer ras.mu.Unlock()

	// Store in memory
	for _, metric := range metrics {
		ras.performance[metric.ID] = metric
	}

	// Save to database
	if err := ras.db.CreateInBatches(metrics, ras.config.BatchSize).Error; err != nil {
		// Log error but continue
	}
}

// flushActivities flushes activities to database
func (ras *RealtimeAnalyticsService) flushActivities(activities []*UserActivity) {
	if len(activities) == 0 {
		return
	}

	ras.mu.Lock()
	defer ras.mu.Unlock()

	// Store in memory
	for _, activity := range activities {
		ras.activities[activity.ID] = activity
	}

	// Save to database
	if err := ras.db.CreateInBatches(activities, ras.config.BatchSize).Error; err != nil {
		// Log error but continue
	}
}

// cleanupLoop runs periodic cleanup tasks
func (ras *RealtimeAnalyticsService) cleanupLoop(ctx context.Context) {
	ticker := time.NewTicker(ras.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			ras.cleanupExpiredData(ctx)
		case <-ras.stopChan:
			return
		case <-ctx.Done():
			return
		}
	}
}

// cleanupExpiredData cleans up expired data
func (ras *RealtimeAnalyticsService) cleanupExpiredData(ctx context.Context) {
	ras.mu.Lock()
	defer ras.mu.Unlock()

	now := time.Now()

	// Clean up old events
	eventCutoff := now.Add(-ras.config.EventRetentionPeriod)
	if err := ras.db.Where("created_at < ?", eventCutoff).Delete(&AnalyticsEvent{}).Error; err != nil {
		// Log error but continue
	}

	// Clean up old metrics
	metricCutoff := now.Add(-ras.config.MetricRetentionPeriod)
	if err := ras.db.Where("created_at < ?", metricCutoff).Delete(&Metric{}).Error; err != nil {
		// Log error but continue
	}

	// Clean up old performance metrics
	perfCutoff := now.Add(-ras.config.PerformanceRetentionPeriod)
	if err := ras.db.Where("created_at < ?", perfCutoff).Delete(&PerformanceMetric{}).Error; err != nil {
		// Log error but continue
	}

	// Clean up old activities
	activityCutoff := now.Add(-ras.config.ActivityRetentionPeriod)
	if err := ras.db.Where("created_at < ?", activityCutoff).Delete(&UserActivity{}).Error; err != nil {
		// Log error but continue
	}
}

// GetAnalyticsStats returns statistics about analytics
func (ras *RealtimeAnalyticsService) GetAnalyticsStats() map[string]interface{} {
	ras.mu.RLock()
	defer ras.mu.RUnlock()

	var totalEvents, totalMetrics, totalPerformance, totalActivities int64

	// Count events
	ras.db.Model(&AnalyticsEvent{}).Count(&totalEvents)

	// Count metrics
	ras.db.Model(&Metric{}).Count(&totalMetrics)

	// Count performance metrics
	ras.db.Model(&PerformanceMetric{}).Count(&totalPerformance)

	// Count activities
	ras.db.Model(&UserActivity{}).Count(&totalActivities)

	return map[string]interface{}{
		"total_events":       totalEvents,
		"total_metrics":      totalMetrics,
		"total_performance":  totalPerformance,
		"total_activities":   totalActivities,
		"memory_events":      len(ras.events),
		"memory_metrics":     len(ras.metrics),
		"memory_performance": len(ras.performance),
		"memory_activities":  len(ras.activities),
		"is_running":         ras.isRunning,
		"config":             ras.config,
	}
}

// Helper functions
func generateEventID() string {
	return fmt.Sprintf("event_%d", time.Now().UnixNano())
}

func generateMetricID() string {
	return fmt.Sprintf("metric_%d", time.Now().UnixNano())
}

func generatePerformanceID() string {
	return fmt.Sprintf("perf_%d", time.Now().UnixNano())
}

func generateActivityID() string {
	return fmt.Sprintf("activity_%d", time.Now().UnixNano())
}

func mustMarshalJSON(v interface{}) json.RawMessage {
	data, err := json.Marshal(v)
	if err != nil {
		panic(fmt.Sprintf("failed to marshal JSON: %v", err))
	}
	return data
}
