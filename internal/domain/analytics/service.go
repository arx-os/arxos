package analytics

import (
	"context"
	"time"

	"github.com/google/uuid"
)

// Service defines the interface for analytics business logic following Clean Architecture principles
type Service interface {
	// Energy analytics
	GetEnergyConsumption(ctx context.Context, req EnergyConsumptionRequest) (*EnergyConsumption, error)
	GetEnergyTrends(ctx context.Context, req EnergyTrendsRequest) ([]*EnergyTrend, error)
	PredictEnergyUsage(ctx context.Context, req PredictEnergyRequest) (*EnergyPrediction, error)

	// Performance analytics
	GetPerformanceMetrics(ctx context.Context, req PerformanceMetricsRequest) (*PerformanceMetrics, error)
	GetPerformanceTrends(ctx context.Context, req PerformanceTrendsRequest) ([]*PerformanceTrend, error)

	// Anomaly detection
	DetectAnomalies(ctx context.Context, req AnomalyDetectionRequest) ([]*Anomaly, error)
	GetAnomalyHistory(ctx context.Context, req AnomalyHistoryRequest) ([]*Anomaly, error)

	// Reporting
	GenerateReport(ctx context.Context, req ReportRequest) (*Report, error)
	GetReportHistory(ctx context.Context, req ReportHistoryRequest) ([]*Report, error)
}

// EnergyConsumption represents energy consumption data
type EnergyConsumption struct {
	BuildingID         uuid.UUID `json:"building_id"`
	TotalConsumption   float64   `json:"total_consumption"`
	PeakConsumption    float64   `json:"peak_consumption"`
	AverageConsumption float64   `json:"average_consumption"`
	Period             string    `json:"period"`
	Timestamp          time.Time `json:"timestamp"`
}

// EnergyTrend represents energy trend data
type EnergyTrend struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
	Trend     string    `json:"trend"` // increasing, decreasing, stable
}

// EnergyPrediction represents energy usage prediction
type EnergyPrediction struct {
	PredictedUsage float64   `json:"predicted_usage"`
	Confidence     float64   `json:"confidence"`
	Period         string    `json:"period"`
	Timestamp      time.Time `json:"timestamp"`
}

// PerformanceMetrics represents performance metrics
type PerformanceMetrics struct {
	BuildingID  uuid.UUID `json:"building_id"`
	Efficiency  float64   `json:"efficiency"`
	Utilization float64   `json:"utilization"`
	Occupancy   float64   `json:"occupancy"`
	Temperature float64   `json:"temperature"`
	Humidity    float64   `json:"humidity"`
	Timestamp   time.Time `json:"timestamp"`
}

// PerformanceTrend represents performance trend data
type PerformanceTrend struct {
	Timestamp time.Time `json:"timestamp"`
	Metric    string    `json:"metric"`
	Value     float64   `json:"value"`
	Trend     string    `json:"trend"`
}

// Anomaly represents an anomaly detection result
type Anomaly struct {
	ID          uuid.UUID `json:"id"`
	Type        string    `json:"type"`
	Severity    string    `json:"severity"` // low, medium, high, critical
	Description string    `json:"description"`
	Location    string    `json:"location"`
	Timestamp   time.Time `json:"timestamp"`
	Resolved    bool      `json:"resolved"`
}

// Report represents an analytics report
type Report struct {
	ID          uuid.UUID `json:"id"`
	Type        string    `json:"type"`
	Title       string    `json:"title"`
	Content     string    `json:"content"`
	GeneratedAt time.Time `json:"generated_at"`
	GeneratedBy string    `json:"generated_by"`
}

// Request types
type EnergyConsumptionRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
	Period     string    `json:"period"` // hourly, daily, weekly, monthly
}

type EnergyTrendsRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
	Period     string    `json:"period"`
}

type PredictEnergyRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	Period     string    `json:"period" validate:"required"`
	Days       int       `json:"days" validate:"min=1,max=365"`
}

type PerformanceMetricsRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
}

type PerformanceTrendsRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
	Metric     string    `json:"metric"`
}

type AnomalyDetectionRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
	Severity   string    `json:"severity"`
}

type AnomalyHistoryRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
	Resolved   *bool     `json:"resolved"`
}

type ReportRequest struct {
	Type       string    `json:"type" validate:"required"`
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
	Format     string    `json:"format"` // json, pdf, csv
}

type ReportHistoryRequest struct {
	BuildingID uuid.UUID `json:"building_id" validate:"required"`
	StartDate  time.Time `json:"start_date" validate:"required"`
	EndDate    time.Time `json:"end_date" validate:"required"`
	Type       string    `json:"type"`
}
