package symbols

import (
	"fmt"
	"time"

	"gorm.io/gorm"
)

// AnalyticsMetric represents a single analytics metric
type AnalyticsMetric struct {
	ID          uint                   `json:"id" gorm:"primaryKey"`
	MetricName  string                 `json:"metric_name"`
	MetricValue float64                `json:"metric_value"`
	Category    string                 `json:"category"`
	System      string                 `json:"system"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata" gorm:"type:json"`
}

// SymbolUsage represents symbol usage data
type SymbolUsage struct {
	ID         uint      `json:"id" gorm:"primaryKey"`
	SymbolID   string    `json:"symbol_id"`
	UsageCount int       `json:"usage_count"`
	LastUsed   time.Time `json:"last_used"`
	System     string    `json:"system"`
	Category   string    `json:"category"`
	UserID     string    `json:"user_id,omitempty"`
	ProjectID  string    `json:"project_id,omitempty"`
}

// SymbolPerformance represents symbol performance metrics
type SymbolPerformance struct {
	ID              uint      `json:"id" gorm:"primaryKey"`
	SymbolID        string    `json:"symbol_id"`
	RenderTime      float64   `json:"render_time_ms"`
	LoadTime        float64   `json:"load_time_ms"`
	MemoryUsage     float64   `json:"memory_usage_kb"`
	ComplexityScore float64   `json:"complexity_score"`
	Timestamp       time.Time `json:"timestamp"`
}

// AnalyticsReport represents a comprehensive analytics report
type AnalyticsReport struct {
	GeneratedAt       time.Time             `json:"generated_at"`
	TimeRange         string                `json:"time_range"`
	TotalSymbols      int                   `json:"total_symbols"`
	SystemBreakdown   map[string]int        `json:"system_breakdown"`
	CategoryBreakdown map[string]int        `json:"category_breakdown"`
	UsageStats        UsageStatistics       `json:"usage_stats"`
	PerformanceStats  PerformanceStatistics `json:"performance_stats"`
	Trends            TrendAnalysis         `json:"trends"`
	Recommendations   []string              `json:"recommendations"`
}

// UsageStatistics represents usage statistics
type UsageStatistics struct {
	TotalUsage      int            `json:"total_usage"`
	MostUsedSymbols []SymbolUsage  `json:"most_used_symbols"`
	UsageBySystem   map[string]int `json:"usage_by_system"`
	UsageByCategory map[string]int `json:"usage_by_category"`
	RecentActivity  []SymbolUsage  `json:"recent_activity"`
}

// PerformanceStatistics represents performance statistics
type PerformanceStatistics struct {
	AverageRenderTime   float64             `json:"average_render_time_ms"`
	AverageLoadTime     float64             `json:"average_load_time_ms"`
	AverageMemoryUsage  float64             `json:"average_memory_usage_kb"`
	SlowestSymbols      []SymbolPerformance `json:"slowest_symbols"`
	PerformanceBySystem map[string]float64  `json:"performance_by_system"`
}

// TrendAnalysis represents trend analysis data
type TrendAnalysis struct {
	SymbolGrowth     []TrendPoint `json:"symbol_growth"`
	UsageGrowth      []TrendPoint `json:"usage_growth"`
	PerformanceTrend []TrendPoint `json:"performance_trend"`
	PopularSystems   []TrendPoint `json:"popular_systems"`
}

// TrendPoint represents a single trend data point
type TrendPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
	Category  string    `json:"category,omitempty"`
}

// SymbolAnalytics provides analytics functionality for symbols
type SymbolAnalytics struct {
	db *gorm.DB
}

// NewSymbolAnalytics creates a new symbol analytics service
func NewSymbolAnalytics(db *gorm.DB) *SymbolAnalytics {
	return &SymbolAnalytics{
		db: db,
	}
}

// TrackSymbolUsage tracks usage of a symbol
func (a *SymbolAnalytics) TrackSymbolUsage(symbolID string, system string, category string, userID string, projectID string) error {
	usage := SymbolUsage{
		SymbolID:   symbolID,
		UsageCount: 1,
		LastUsed:   time.Now(),
		System:     system,
		Category:   category,
		UserID:     userID,
		ProjectID:  projectID,
	}

	// Check if usage record already exists
	var existingUsage SymbolUsage
	result := a.db.Where("symbol_id = ? AND system = ? AND category = ?", symbolID, system, category).First(&existingUsage)

	if result.Error == nil {
		// Update existing record
		existingUsage.UsageCount++
		existingUsage.LastUsed = time.Now()
		if userID != "" {
			existingUsage.UserID = userID
		}
		if projectID != "" {
			existingUsage.ProjectID = projectID
		}
		return a.db.Save(&existingUsage).Error
	}

	// Create new record
	return a.db.Create(&usage).Error
}

// TrackSymbolPerformance tracks performance metrics for a symbol
func (a *SymbolAnalytics) TrackSymbolPerformance(symbolID string, renderTime float64, loadTime float64, memoryUsage float64, complexityScore float64) error {
	performance := SymbolPerformance{
		SymbolID:        symbolID,
		RenderTime:      renderTime,
		LoadTime:        loadTime,
		MemoryUsage:     memoryUsage,
		ComplexityScore: complexityScore,
		Timestamp:       time.Now(),
	}

	return a.db.Create(&performance).Error
}

// RecordMetric records a custom analytics metric
func (a *SymbolAnalytics) RecordMetric(metricName string, metricValue float64, category string, system string, metadata map[string]interface{}) error {
	metric := AnalyticsMetric{
		MetricName:  metricName,
		MetricValue: metricValue,
		Category:    category,
		System:      system,
		Timestamp:   time.Now(),
		Metadata:    metadata,
	}

	return a.db.Create(&metric).Error
}

// GenerateAnalyticsReport generates a comprehensive analytics report
func (a *SymbolAnalytics) GenerateAnalyticsReport(timeRange string) (*AnalyticsReport, error) {
	report := &AnalyticsReport{
		GeneratedAt: time.Now(),
		TimeRange:   timeRange,
	}

	// Get total symbols count
	var totalSymbols int64
	if err := a.db.Model(&Symbol{}).Count(&totalSymbols).Error; err != nil {
		return nil, fmt.Errorf("failed to count symbols: %w", err)
	}
	report.TotalSymbols = int(totalSymbols)

	// Get system breakdown
	systemBreakdown, err := a.getSystemBreakdown()
	if err != nil {
		return nil, fmt.Errorf("failed to get system breakdown: %w", err)
	}
	report.SystemBreakdown = systemBreakdown

	// Get category breakdown
	categoryBreakdown, err := a.getCategoryBreakdown()
	if err != nil {
		return nil, fmt.Errorf("failed to get category breakdown: %w", err)
	}
	report.CategoryBreakdown = categoryBreakdown

	// Get usage statistics
	usageStats, err := a.getUsageStatistics(timeRange)
	if err != nil {
		return nil, fmt.Errorf("failed to get usage statistics: %w", err)
	}
	report.UsageStats = *usageStats

	// Get performance statistics
	performanceStats, err := a.getPerformanceStatistics(timeRange)
	if err != nil {
		return nil, fmt.Errorf("failed to get performance statistics: %w", err)
	}
	report.PerformanceStats = *performanceStats

	// Get trends
	trends, err := a.getTrendAnalysis(timeRange)
	if err != nil {
		return nil, fmt.Errorf("failed to get trend analysis: %w", err)
	}
	report.Trends = *trends

	// Generate recommendations
	report.Recommendations = a.generateRecommendations(report)

	return report, nil
}

// GetMostUsedSymbols returns the most used symbols
func (a *SymbolAnalytics) GetMostUsedSymbols(limit int) ([]SymbolUsage, error) {
	var usages []SymbolUsage
	if err := a.db.Order("usage_count DESC").Limit(limit).Find(&usages).Error; err != nil {
		return nil, fmt.Errorf("failed to get most used symbols: %w", err)
	}
	return usages, nil
}

// GetSlowestSymbols returns the slowest symbols by render time
func (a *SymbolAnalytics) GetSlowestSymbols(limit int) ([]SymbolPerformance, error) {
	var performances []SymbolPerformance
	if err := a.db.Order("render_time DESC").Limit(limit).Find(&performances).Error; err != nil {
		return nil, fmt.Errorf("failed to get slowest symbols: %w", err)
	}
	return performances, nil
}

// GetUsageBySystem returns usage statistics by system
func (a *SymbolAnalytics) GetUsageBySystem() (map[string]int, error) {
	var results []struct {
		System string `json:"system"`
		Count  int    `json:"count"`
	}

	if err := a.db.Model(&SymbolUsage{}).
		Select("system, SUM(usage_count) as count").
		Group("system").
		Scan(&results).Error; err != nil {
		return nil, fmt.Errorf("failed to get usage by system: %w", err)
	}

	usageBySystem := make(map[string]int)
	for _, result := range results {
		usageBySystem[result.System] = result.Count
	}

	return usageBySystem, nil
}

// GetUsageByCategory returns usage statistics by category
func (a *SymbolAnalytics) GetUsageByCategory() (map[string]int, error) {
	var results []struct {
		Category string `json:"category"`
		Count    int    `json:"count"`
	}

	if err := a.db.Model(&SymbolUsage{}).
		Select("category, SUM(usage_count) as count").
		Group("category").
		Scan(&results).Error; err != nil {
		return nil, fmt.Errorf("failed to get usage by category: %w", err)
	}

	usageByCategory := make(map[string]int)
	for _, result := range results {
		usageByCategory[result.Category] = result.Count
	}

	return usageByCategory, nil
}

// GetPerformanceBySystem returns performance statistics by system
func (a *SymbolAnalytics) GetPerformanceBySystem() (map[string]float64, error) {
	var results []struct {
		System        string  `json:"system"`
		AvgRenderTime float64 `json:"avg_render_time"`
	}

	if err := a.db.Model(&SymbolPerformance{}).
		Select("system, AVG(render_time) as avg_render_time").
		Group("system").
		Scan(&results).Error; err != nil {
		return nil, fmt.Errorf("failed to get performance by system: %w", err)
	}

	performanceBySystem := make(map[string]float64)
	for _, result := range results {
		performanceBySystem[result.System] = result.AvgRenderTime
	}

	return performanceBySystem, nil
}

// Helper methods

func (a *SymbolAnalytics) getSystemBreakdown() (map[string]int, error) {
	var results []struct {
		System string `json:"system"`
		Count  int64  `json:"count"`
	}

	if err := a.db.Model(&Symbol{}).
		Select("system, COUNT(*) as count").
		Group("system").
		Scan(&results).Error; err != nil {
		return nil, err
	}

	breakdown := make(map[string]int)
	for _, result := range results {
		breakdown[result.System] = int(result.Count)
	}

	return breakdown, nil
}

func (a *SymbolAnalytics) getCategoryBreakdown() (map[string]int, error) {
	var results []struct {
		Category string `json:"category"`
		Count    int64  `json:"count"`
	}

	if err := a.db.Model(&Symbol{}).
		Select("category, COUNT(*) as count").
		Group("category").
		Scan(&results).Error; err != nil {
		return nil, err
	}

	breakdown := make(map[string]int)
	for _, result := range results {
		breakdown[result.Category] = int(result.Count)
	}

	return breakdown, nil
}

func (a *SymbolAnalytics) getUsageStatistics(timeRange string) (*UsageStatistics, error) {
	stats := &UsageStatistics{}

	// Get total usage
	var totalUsage int64
	if err := a.db.Model(&SymbolUsage{}).Select("SUM(usage_count)").Scan(&totalUsage).Error; err != nil {
		return nil, err
	}
	stats.TotalUsage = int(totalUsage)

	// Get most used symbols
	var mostUsed []SymbolUsage
	if err := a.db.Order("usage_count DESC").Limit(10).Find(&mostUsed).Error; err != nil {
		return nil, err
	}
	stats.MostUsedSymbols = mostUsed

	// Get usage by system
	usageBySystem, err := a.GetUsageBySystem()
	if err != nil {
		return nil, err
	}
	stats.UsageBySystem = usageBySystem

	// Get usage by category
	usageByCategory, err := a.GetUsageByCategory()
	if err != nil {
		return nil, err
	}
	stats.UsageByCategory = usageByCategory

	// Get recent activity
	var recentActivity []SymbolUsage
	if err := a.db.Order("last_used DESC").Limit(20).Find(&recentActivity).Error; err != nil {
		return nil, err
	}
	stats.RecentActivity = recentActivity

	return stats, nil
}

func (a *SymbolAnalytics) getPerformanceStatistics(timeRange string) (*PerformanceStatistics, error) {
	stats := &PerformanceStatistics{}

	// Get average render time
	var avgRenderTime float64
	if err := a.db.Model(&SymbolPerformance{}).Select("AVG(render_time)").Scan(&avgRenderTime).Error; err != nil {
		return nil, err
	}
	stats.AverageRenderTime = avgRenderTime

	// Get average load time
	var avgLoadTime float64
	if err := a.db.Model(&SymbolPerformance{}).Select("AVG(load_time)").Scan(&avgLoadTime).Error; err != nil {
		return nil, err
	}
	stats.AverageLoadTime = avgLoadTime

	// Get average memory usage
	var avgMemoryUsage float64
	if err := a.db.Model(&SymbolPerformance{}).Select("AVG(memory_usage)").Scan(&avgMemoryUsage).Error; err != nil {
		return nil, err
	}
	stats.AverageMemoryUsage = avgMemoryUsage

	// Get slowest symbols
	var slowestSymbols []SymbolPerformance
	if err := a.db.Order("render_time DESC").Limit(10).Find(&slowestSymbols).Error; err != nil {
		return nil, err
	}
	stats.SlowestSymbols = slowestSymbols

	// Get performance by system
	performanceBySystem, err := a.GetPerformanceBySystem()
	if err != nil {
		return nil, err
	}
	stats.PerformanceBySystem = performanceBySystem

	return stats, nil
}

func (a *SymbolAnalytics) getTrendAnalysis(timeRange string) (*TrendAnalysis, error) {
	trends := &TrendAnalysis{}

	// Generate trend points for symbol growth
	symbolGrowth, err := a.generateSymbolGrowthTrend(timeRange)
	if err != nil {
		return nil, err
	}
	trends.SymbolGrowth = symbolGrowth

	// Generate trend points for usage growth
	usageGrowth, err := a.generateUsageGrowthTrend(timeRange)
	if err != nil {
		return nil, err
	}
	trends.UsageGrowth = usageGrowth

	// Generate trend points for performance
	performanceTrend, err := a.generatePerformanceTrend(timeRange)
	if err != nil {
		return nil, err
	}
	trends.PerformanceTrend = performanceTrend

	// Generate trend points for popular systems
	popularSystems, err := a.generatePopularSystemsTrend(timeRange)
	if err != nil {
		return nil, err
	}
	trends.PopularSystems = popularSystems

	return trends, nil
}

func (a *SymbolAnalytics) generateSymbolGrowthTrend(timeRange string) ([]TrendPoint, error) {
	// This is a simplified implementation
	// In practice, you'd query the database for actual growth data
	var trends []TrendPoint

	// Generate sample trend points
	for i := 0; i < 7; i++ {
		trends = append(trends, TrendPoint{
			Timestamp: time.Now().AddDate(0, 0, -6+i),
			Value:     float64(100 + i*10),
		})
	}

	return trends, nil
}

func (a *SymbolAnalytics) generateUsageGrowthTrend(timeRange string) ([]TrendPoint, error) {
	// This is a simplified implementation
	var trends []TrendPoint

	for i := 0; i < 7; i++ {
		trends = append(trends, TrendPoint{
			Timestamp: time.Now().AddDate(0, 0, -6+i),
			Value:     float64(500 + i*50),
		})
	}

	return trends, nil
}

func (a *SymbolAnalytics) generatePerformanceTrend(timeRange string) ([]TrendPoint, error) {
	// This is a simplified implementation
	var trends []TrendPoint

	for i := 0; i < 7; i++ {
		trends = append(trends, TrendPoint{
			Timestamp: time.Now().AddDate(0, 0, -6+i),
			Value:     float64(100 - i*2), // Improving performance
		})
	}

	return trends, nil
}

func (a *SymbolAnalytics) generatePopularSystemsTrend(timeRange string) ([]TrendPoint, error) {
	// This is a simplified implementation
	var trends []TrendPoint

	systems := []string{"electrical", "mechanical", "plumbing", "hvac"}
	for i, system := range systems {
		trends = append(trends, TrendPoint{
			Timestamp: time.Now().AddDate(0, 0, -6+i),
			Value:     float64(100 + i*20),
			Category:  system,
		})
	}

	return trends, nil
}

func (a *SymbolAnalytics) generateRecommendations(report *AnalyticsReport) []string {
	var recommendations []string

	// Analyze performance issues
	if report.PerformanceStats.AverageRenderTime > 200 {
		recommendations = append(recommendations, "Consider optimizing symbols with render times > 200ms")
	}

	// Analyze usage patterns
	if len(report.UsageStats.MostUsedSymbols) > 0 {
		topSymbol := report.UsageStats.MostUsedSymbols[0]
		if topSymbol.UsageCount > 1000 {
			recommendations = append(recommendations, "Consider creating variations of high-usage symbols")
		}
	}

	// Analyze system distribution
	if len(report.SystemBreakdown) > 0 {
		recommendations = append(recommendations, "Consider expanding symbol library for underrepresented systems")
	}

	// Analyze trends
	if len(report.Trends.UsageGrowth) > 1 {
		latest := report.Trends.UsageGrowth[len(report.Trends.UsageGrowth)-1]
		previous := report.Trends.UsageGrowth[len(report.Trends.UsageGrowth)-2]
		if latest.Value < previous.Value {
			recommendations = append(recommendations, "Usage is declining - consider user engagement strategies")
		}
	}

	return recommendations
}
