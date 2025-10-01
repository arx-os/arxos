package services

import (
	"context"

	"github.com/arx-os/arxos/internal/domain/analytics"
)

// AnalyticsApplicationService provides application-level analytics operations
type AnalyticsApplicationService struct {
	analyticsService analytics.Service
}

// NewAnalyticsApplicationService creates a new analytics application service
func NewAnalyticsApplicationService(analyticsService analytics.Service) *AnalyticsApplicationService {
	return &AnalyticsApplicationService{
		analyticsService: analyticsService,
	}
}

// ProcessDataPoint processes a data point through the analytics pipeline
func (s *AnalyticsApplicationService) ProcessDataPoint(ctx context.Context, dataPoint analytics.EnergyDataPoint) error {
	return s.analyticsService.ProcessDataPoint(ctx, dataPoint)
}

// GenerateReport generates a comprehensive analytics report
func (s *AnalyticsApplicationService) GenerateReport(ctx context.Context, reportType string, parameters map[string]interface{}) (*analytics.Report, error) {
	return s.analyticsService.GenerateReport(ctx, reportType, parameters)
}

// GetOptimizationRecommendations returns energy optimization recommendations
func (s *AnalyticsApplicationService) GetOptimizationRecommendations(ctx context.Context, buildingID string) ([]analytics.EnergyRecommendation, error) {
	return s.analyticsService.GetOptimizationRecommendations(ctx, buildingID)
}

// GetForecast returns predictive forecasts
func (s *AnalyticsApplicationService) GetForecast(ctx context.Context, metric string, duration int64) (*analytics.Forecast, error) {
	// Convert duration from nanoseconds to time.Duration
	durationTime := duration
	return s.analyticsService.GetForecast(ctx, metric, durationTime)
}

// GetAnomalies returns detected anomalies
func (s *AnalyticsApplicationService) GetAnomalies(ctx context.Context, severity string) ([]analytics.Anomaly, error) {
	return s.analyticsService.GetAnomalies(ctx, severity)
}

// GetAlerts returns active alerts
func (s *AnalyticsApplicationService) GetAlerts(ctx context.Context, status string) ([]analytics.Alert, error) {
	return s.analyticsService.GetAlerts(ctx, status)
}

// GetMetrics returns analytics engine metrics
func (s *AnalyticsApplicationService) GetMetrics(ctx context.Context) (*analytics.AnalyticsMetrics, error) {
	return s.analyticsService.GetMetrics(ctx)
}

// UpdateMetrics updates analytics metrics
func (s *AnalyticsApplicationService) UpdateMetrics(ctx context.Context) error {
	return s.analyticsService.UpdateMetrics(ctx)
}
