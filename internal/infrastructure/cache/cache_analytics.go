package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/domain"
)

// CacheAnalytics provides detailed analytics about cache performance
type CacheAnalytics struct {
	cache   *UnifiedCache
	logger  domain.Logger
	metrics *AnalyticsMetrics
}

// AnalyticsMetrics tracks detailed cache metrics
type AnalyticsMetrics struct {
	// Performance metrics
	TotalRequests int64   `json:"total_requests"`
	TotalHits     int64   `json:"total_hits"`
	TotalMisses   int64   `json:"total_misses"`
	HitRate       float64 `json:"hit_rate"`

	// Layer-specific metrics
	L1Hits    int64   `json:"l1_hits"`
	L1Misses  int64   `json:"l1_misses"`
	L1HitRate float64 `json:"l1_hit_rate"`

	L2Hits    int64   `json:"l2_hits"`
	L2Misses  int64   `json:"l2_misses"`
	L2HitRate float64 `json:"l2_hit_rate"`

	L3Hits    int64   `json:"l3_hits"`
	L3Misses  int64   `json:"l3_misses"`
	L3HitRate float64 `json:"l3_hit_rate"`

	// Timing metrics
	AverageResponseTime time.Duration `json:"average_response_time"`
	MinResponseTime     time.Duration `json:"min_response_time"`
	MaxResponseTime     time.Duration `json:"max_response_time"`

	// Size metrics
	L1Size    int64 `json:"l1_size"`
	L2Size    int64 `json:"l2_size"`
	L3Size    int64 `json:"l3_size"`
	TotalSize int64 `json:"total_size"`

	// Key metrics
	MostAccessedKeys []KeyMetric `json:"most_accessed_keys"`
	SlowestKeys      []KeyMetric `json:"slowest_keys"`

	// Time-based metrics
	HourlyStats map[int]HourlyStats   `json:"hourly_stats"`
	DailyStats  map[string]DailyStats `json:"daily_stats"`

	// Metadata
	LastUpdated time.Time `json:"last_updated"`
	StartTime   time.Time `json:"start_time"`
}

// KeyMetric represents metrics for a specific cache key
type KeyMetric struct {
	Key          string        `json:"key"`
	AccessCount  int64         `json:"access_count"`
	HitCount     int64         `json:"hit_count"`
	MissCount    int64         `json:"miss_count"`
	HitRate      float64       `json:"hit_rate"`
	AverageTime  time.Duration `json:"average_time"`
	LastAccessed time.Time     `json:"last_accessed"`
	Size         int64         `json:"size"`
}

// HourlyStats represents statistics for a specific hour
type HourlyStats struct {
	Hour        int           `json:"hour"`
	Requests    int64         `json:"requests"`
	Hits        int64         `json:"hits"`
	Misses      int64         `json:"misses"`
	HitRate     float64       `json:"hit_rate"`
	AverageTime time.Duration `json:"average_time"`
}

// DailyStats represents statistics for a specific day
type DailyStats struct {
	Date         string        `json:"date"`
	Requests     int64         `json:"requests"`
	Hits         int64         `json:"hits"`
	Misses       int64         `json:"misses"`
	HitRate      float64       `json:"hit_rate"`
	AverageTime  time.Duration `json:"average_time"`
	PeakHour     int           `json:"peak_hour"`
	PeakRequests int64         `json:"peak_requests"`
}

// NewCacheAnalytics creates a new cache analytics instance
func NewCacheAnalytics(cache *UnifiedCache, logger domain.Logger) *CacheAnalytics {
	return &CacheAnalytics{
		cache:  cache,
		logger: logger,
		metrics: &AnalyticsMetrics{
			StartTime:        time.Now(),
			LastUpdated:      time.Now(),
			HourlyStats:      make(map[int]HourlyStats),
			DailyStats:       make(map[string]DailyStats),
			MostAccessedKeys: make([]KeyMetric, 0),
			SlowestKeys:      make([]KeyMetric, 0),
		},
	}
}

// RecordAccess records a cache access for analytics
func (ca *CacheAnalytics) RecordAccess(key string, hit bool, responseTime time.Duration, layer CacheLayer) {
	now := time.Now()
	hour := now.Hour()
	date := now.Format("2006-01-02")

	// Update overall metrics
	ca.metrics.TotalRequests++
	if hit {
		ca.metrics.TotalHits++
		switch layer {
		case L1Memory:
			ca.metrics.L1Hits++
		case L2Local:
			ca.metrics.L2Hits++
		case L3Network:
			ca.metrics.L3Hits++
		}
	} else {
		ca.metrics.TotalMisses++
		switch layer {
		case L1Memory:
			ca.metrics.L1Misses++
		case L2Local:
			ca.metrics.L2Misses++
		case L3Network:
			ca.metrics.L3Misses++
		}
	}

	// Update hit rates
	ca.updateHitRates()

	// Update response time metrics
	ca.updateResponseTimeMetrics(responseTime)

	// Update hourly stats
	ca.updateHourlyStats(hour, hit, responseTime)

	// Update daily stats
	ca.updateDailyStats(date, hour, hit, responseTime)

	// Update key-specific metrics
	ca.updateKeyMetrics(key, hit, responseTime)

	ca.metrics.LastUpdated = now
}

// GetAnalytics returns current analytics metrics
func (ca *CacheAnalytics) GetAnalytics(ctx context.Context) (*AnalyticsMetrics, error) {
	// Get current cache stats
	cacheStats, err := ca.cache.GetStats(ctx)
	if err != nil {
		return nil, err
	}

	// Update size metrics from cache stats
	ca.metrics.L1Size = cacheStats.L1Hits + cacheStats.L1Misses // Rough estimate
	ca.metrics.L2Size = cacheStats.L2Hits + cacheStats.L2Misses // Rough estimate
	ca.metrics.L3Size = cacheStats.L3Hits + cacheStats.L3Misses // Rough estimate
	ca.metrics.TotalSize = ca.metrics.L1Size + ca.metrics.L2Size + ca.metrics.L3Size

	return ca.metrics, nil
}

// GetPerformanceReport returns a detailed performance report
func (ca *CacheAnalytics) GetPerformanceReport(ctx context.Context) (map[string]any, error) {
	analytics, err := ca.GetAnalytics(ctx)
	if err != nil {
		return nil, err
	}

	report := map[string]any{
		"summary": map[string]any{
			"total_requests":        analytics.TotalRequests,
			"hit_rate":              analytics.HitRate,
			"average_response_time": analytics.AverageResponseTime,
			"uptime":                time.Since(analytics.StartTime),
		},
		"layer_performance": map[string]any{
			"l1": map[string]any{
				"hits":     analytics.L1Hits,
				"misses":   analytics.L1Misses,
				"hit_rate": analytics.L1HitRate,
			},
			"l2": map[string]any{
				"hits":     analytics.L2Hits,
				"misses":   analytics.L2Misses,
				"hit_rate": analytics.L2HitRate,
			},
			"l3": map[string]any{
				"hits":     analytics.L3Hits,
				"misses":   analytics.L3Misses,
				"hit_rate": analytics.L3HitRate,
			},
		},
		"top_keys":      analytics.MostAccessedKeys[:min(10, len(analytics.MostAccessedKeys))],
		"slowest_keys":  analytics.SlowestKeys[:min(10, len(analytics.SlowestKeys))],
		"hourly_trends": analytics.HourlyStats,
		"daily_trends":  analytics.DailyStats,
	}

	return report, nil
}

// GetRecommendations returns cache optimization recommendations
func (ca *CacheAnalytics) GetRecommendations(ctx context.Context) ([]string, error) {
	var recommendations []string

	analytics, err := ca.GetAnalytics(ctx)
	if err != nil {
		return nil, err
	}

	// Hit rate recommendations
	if analytics.HitRate < 0.7 {
		recommendations = append(recommendations,
			"Low hit rate detected. Consider increasing TTL for frequently accessed data.")
	}

	if analytics.L1HitRate < 0.5 {
		recommendations = append(recommendations,
			"Low L1 hit rate. Consider increasing L1 cache size or optimizing data access patterns.")
	}

	if analytics.L2HitRate < 0.3 {
		recommendations = append(recommendations,
			"Low L2 hit rate. Consider enabling L2 cache or increasing L2 TTL.")
	}

	// Response time recommendations
	if analytics.AverageResponseTime > 100*time.Millisecond {
		recommendations = append(recommendations,
			"High average response time. Consider optimizing cache layers or increasing L1 cache size.")
	}

	// Size recommendations
	if analytics.L1Size > 1000000 { // 1MB
		recommendations = append(recommendations,
			"L1 cache size is large. Consider implementing LRU eviction or increasing L1 capacity.")
	}

	// Key access pattern recommendations
	if len(analytics.MostAccessedKeys) > 0 {
		topKey := analytics.MostAccessedKeys[0]
		if topKey.HitRate < 0.5 {
			recommendations = append(recommendations,
				fmt.Sprintf("Key '%s' has low hit rate (%f). Consider increasing its TTL.",
					topKey.Key, topKey.HitRate))
		}
	}

	return recommendations, nil
}

// ExportAnalytics exports analytics data in various formats
func (ca *CacheAnalytics) ExportAnalytics(ctx context.Context, format string) ([]byte, error) {
	analytics, err := ca.GetAnalytics(ctx)
	if err != nil {
		return nil, err
	}

	switch format {
	case "json":
		return json.MarshalIndent(analytics, "", "  ")
	case "csv":
		return ca.exportCSV(analytics), nil
	default:
		return nil, fmt.Errorf("unsupported export format: %s", format)
	}
}

// Helper methods

func (ca *CacheAnalytics) updateHitRates() {
	if ca.metrics.TotalRequests > 0 {
		ca.metrics.HitRate = float64(ca.metrics.TotalHits) / float64(ca.metrics.TotalRequests)
	}

	if ca.metrics.L1Hits+ca.metrics.L1Misses > 0 {
		ca.metrics.L1HitRate = float64(ca.metrics.L1Hits) / float64(ca.metrics.L1Hits+ca.metrics.L1Misses)
	}

	if ca.metrics.L2Hits+ca.metrics.L2Misses > 0 {
		ca.metrics.L2HitRate = float64(ca.metrics.L2Hits) / float64(ca.metrics.L2Hits+ca.metrics.L2Misses)
	}

	if ca.metrics.L3Hits+ca.metrics.L3Misses > 0 {
		ca.metrics.L3HitRate = float64(ca.metrics.L3Hits) / float64(ca.metrics.L3Hits+ca.metrics.L3Misses)
	}
}

func (ca *CacheAnalytics) updateResponseTimeMetrics(responseTime time.Duration) {
	if ca.metrics.TotalRequests == 1 {
		ca.metrics.AverageResponseTime = responseTime
		ca.metrics.MinResponseTime = responseTime
		ca.metrics.MaxResponseTime = responseTime
	} else {
		// Update average
		ca.metrics.AverageResponseTime = time.Duration(
			(int64(ca.metrics.AverageResponseTime)*(ca.metrics.TotalRequests-1) + int64(responseTime)) / ca.metrics.TotalRequests)

		// Update min/max
		if responseTime < ca.metrics.MinResponseTime {
			ca.metrics.MinResponseTime = responseTime
		}
		if responseTime > ca.metrics.MaxResponseTime {
			ca.metrics.MaxResponseTime = responseTime
		}
	}
}

func (ca *CacheAnalytics) updateHourlyStats(hour int, hit bool, responseTime time.Duration) {
	stats := ca.metrics.HourlyStats[hour]
	stats.Hour = hour
	stats.Requests++
	if hit {
		stats.Hits++
	} else {
		stats.Misses++
	}

	if stats.Requests > 0 {
		stats.HitRate = float64(stats.Hits) / float64(stats.Requests)
		stats.AverageTime = time.Duration(
			(int64(stats.AverageTime)*(stats.Requests-1) + int64(responseTime)) / stats.Requests)
	}

	ca.metrics.HourlyStats[hour] = stats
}

func (ca *CacheAnalytics) updateDailyStats(date string, hour int, hit bool, responseTime time.Duration) {
	stats := ca.metrics.DailyStats[date]
	stats.Date = date
	stats.Requests++
	if hit {
		stats.Hits++
	} else {
		stats.Misses++
	}

	if stats.Requests > 0 {
		stats.HitRate = float64(stats.Hits) / float64(stats.Requests)
		stats.AverageTime = time.Duration(
			(int64(stats.AverageTime)*(stats.Requests-1) + int64(responseTime)) / stats.Requests)
	}

	// Track peak hour
	hourlyStats := ca.metrics.HourlyStats[hour]
	if hourlyStats.Requests > stats.PeakRequests {
		stats.PeakHour = hour
		stats.PeakRequests = hourlyStats.Requests
	}

	ca.metrics.DailyStats[date] = stats
}

func (ca *CacheAnalytics) updateKeyMetrics(key string, hit bool, responseTime time.Duration) {
	// Find existing key metric or create new one
	var keyMetric *KeyMetric
	for i, km := range ca.metrics.MostAccessedKeys {
		if km.Key == key {
			keyMetric = &ca.metrics.MostAccessedKeys[i]
			break
		}
	}

	if keyMetric == nil {
		keyMetric = &KeyMetric{
			Key: key,
		}
		ca.metrics.MostAccessedKeys = append(ca.metrics.MostAccessedKeys, *keyMetric)
	}

	// Update metrics
	keyMetric.AccessCount++
	if hit {
		keyMetric.HitCount++
	} else {
		keyMetric.MissCount++
	}

	if keyMetric.AccessCount > 0 {
		keyMetric.HitRate = float64(keyMetric.HitCount) / float64(keyMetric.AccessCount)
		keyMetric.AverageTime = time.Duration(
			(int64(keyMetric.AverageTime)*(keyMetric.AccessCount-1) + int64(responseTime)) / keyMetric.AccessCount)
	}

	keyMetric.LastAccessed = time.Now()

	// Sort by access count
	sort.Slice(ca.metrics.MostAccessedKeys, func(i, j int) bool {
		return ca.metrics.MostAccessedKeys[i].AccessCount > ca.metrics.MostAccessedKeys[j].AccessCount
	})

	// Update slowest keys
	ca.updateSlowestKeys(keyMetric)
}

func (ca *CacheAnalytics) updateSlowestKeys(keyMetric *KeyMetric) {
	// Find in slowest keys or add new
	found := false
	for i, sk := range ca.metrics.SlowestKeys {
		if sk.Key == keyMetric.Key {
			ca.metrics.SlowestKeys[i] = *keyMetric
			found = true
			break
		}
	}

	if !found {
		ca.metrics.SlowestKeys = append(ca.metrics.SlowestKeys, *keyMetric)
	}

	// Sort by average time
	sort.Slice(ca.metrics.SlowestKeys, func(i, j int) bool {
		return ca.metrics.SlowestKeys[i].AverageTime > ca.metrics.SlowestKeys[j].AverageTime
	})
}

func (ca *CacheAnalytics) exportCSV(analytics *AnalyticsMetrics) []byte {
	// Simple CSV export - in production, use proper CSV library
	csv := fmt.Sprintf("metric,value\n")
	csv += fmt.Sprintf("total_requests,%d\n", analytics.TotalRequests)
	csv += fmt.Sprintf("hit_rate,%.4f\n", analytics.HitRate)
	csv += fmt.Sprintf("average_response_time,%d\n", analytics.AverageResponseTime.Nanoseconds())
	csv += fmt.Sprintf("l1_hit_rate,%.4f\n", analytics.L1HitRate)
	csv += fmt.Sprintf("l2_hit_rate,%.4f\n", analytics.L2HitRate)
	csv += fmt.Sprintf("l3_hit_rate,%.4f\n", analytics.L3HitRate)

	return []byte(csv)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
