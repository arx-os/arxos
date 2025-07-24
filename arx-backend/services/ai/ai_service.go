package ai

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// AI Service Types
type UserActionType string
type PatternType string
type HTMXEventType string
type AIComponentType string
type AnalyticsType string
type InsightType string

const (
	// User Action Types
	ActionView    UserActionType = "view"
	ActionCreate  UserActionType = "create"
	ActionEdit    UserActionType = "edit"
	ActionDelete  UserActionType = "delete"
	ActionSearch  UserActionType = "search"
	ActionExport  UserActionType = "export"
	ActionImport  UserActionType = "import"
	ActionLogin   UserActionType = "login"
	ActionLogout  UserActionType = "logout"
	ActionNavigate UserActionType = "navigate"

	// Pattern Types
	PatternFrequency PatternType = "frequency"
	PatternSequence  PatternType = "sequence"
	PatternTiming    PatternType = "timing"
	PatternPreference PatternType = "preference"

	// HTMX Event Types
	EventClick   HTMXEventType = "click"
	EventSubmit  HTMXEventType = "submit"
	EventChange  HTMXEventType = "change"
	EventKeyup   HTMXEventType = "keyup"
	EventFocus   HTMXEventType = "focus"
	EventBlur    HTMXEventType = "blur"
	EventScroll  HTMXEventType = "scroll"
	EventResize  HTMXEventType = "resize"

	// AI Component Types
	ComponentSmartForm      AIComponentType = "smart_form"
	ComponentIntelligentSearch AIComponentType = "intelligent_search"
	ComponentContextSuggestions AIComponentType = "context_suggestions"
	ComponentAdaptiveNavigation AIComponentType = "adaptive_navigation"
	ComponentPersonalizedDashboard AIComponentType = "personalized_dashboard"
	ComponentAIAssistant    AIComponentType = "ai_assistant"
	ComponentRecommendationWidget AIComponentType = "recommendation_widget"
	ComponentPredictiveInput AIComponentType = "predictive_input"
	ComponentSmartTable     AIComponentType = "smart_table"
	ComponentIntelligentChart AIComponentType = "intelligent_chart"

	// Analytics Types
	AnalyticsUserBehavior AnalyticsType = "user_behavior"
	AnalyticsSystemPerformance AnalyticsType = "system_performance"
	AnalyticsPredictiveModeling AnalyticsType = "predictive_modeling"
	AnalyticsTrendAnalysis AnalyticsType = "trend_analysis"
	AnalyticsCorrelationAnalysis AnalyticsType = "correlation_analysis"
	AnalyticsAnomalyDetection AnalyticsType = "anomaly_detection"

	// Insight Types
	InsightUsagePattern InsightType = "usage_pattern"
	InsightPerformanceOptimization InsightType = "performance_optimization"
	InsightUserEngagement InsightType = "user_engagement"
	InsightSystemEfficiency InsightType = "system_efficiency"
	InsightPredictiveInsight InsightType = "predictive_insight"
	InsightAnomalyAlert InsightType = "anomaly_alert"
)

// Data Models
type UserContext struct {
	PageURL      string            `json:"page_url"`
	UserAgent    string            `json:"user_agent"`
	ScreenSize   string            `json:"screen_size"`
	TimeZone     string            `json:"time_zone"`
	Language     string            `json:"language"`
	Referrer    string            `json:"referrer"`
	SessionID    string            `json:"session_id"`
	UserID       string            `json:"user_id"`
	CustomData   map[string]string `json:"custom_data"`
}

type UserAction struct {
	ID          string       `json:"id"`
	UserID      string       `json:"user_id"`
	SessionID   string       `json:"session_id"`
	ActionType  UserActionType `json:"action_type"`
	Resource    string       `json:"resource"`
	Context     UserContext  `json:"context"`
	Timestamp   time.Time    `json:"timestamp"`
	Duration    int          `json:"duration"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type UserSession struct {
	ID          string    `json:"id"`
	UserID      string    `json:"user_id"`
	StartTime   time.Time `json:"start_time"`
	EndTime     *time.Time `json:"end_time"`
	Duration    int        `json:"duration"`
	PageViews   int        `json:"page_views"`
	Actions     int        `json:"actions"`
	DeviceInfo  string     `json:"device_info"`
	Location    string     `json:"location"`
}

type UserPattern struct {
	ID          string     `json:"id"`
	UserID      string     `json:"user_id"`
	PatternType PatternType `json:"pattern_type"`
	Pattern     string     `json:"pattern"`
	Frequency   int        `json:"frequency"`
	Confidence  float64    `json:"confidence"`
	LastSeen    time.Time  `json:"last_seen"`
	CreatedAt   time.Time  `json:"created_at"`
}

type UserPreference struct {
	ID          string                 `json:"id"`
	UserID      string                 `json:"user_id"`
	Category    string                 `json:"category"`
	Key         string                 `json:"key"`
	Value       interface{}            `json:"value"`
	Confidence  float64                `json:"confidence"`
	LastUpdated time.Time              `json:"last_updated"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type UserRecommendation struct {
	ID          string                 `json:"id"`
	UserID      string                 `json:"user_id"`
	Type        string                 `json:"type"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Priority    int                    `json:"priority"`
	Confidence  float64                `json:"confidence"`
	CreatedAt   time.Time              `json:"created_at"`
	AppliedAt   *time.Time             `json:"applied_at"`
	DismissedAt *time.Time             `json:"dismissed_at"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type UserAnalytics struct {
	UserID           string    `json:"user_id"`
	TotalSessions    int       `json:"total_sessions"`
	TotalActions     int       `json:"total_actions"`
	AverageSessionDuration int `json:"average_session_duration"`
	MostUsedFeatures []string  `json:"most_used_features"`
	LastActive       time.Time `json:"last_active"`
	EngagementScore  float64   `json:"engagement_score"`
	PatternsCount    int       `json:"patterns_count"`
	RecommendationsCount int   `json:"recommendations_count"`
	LastUpdated      time.Time `json:"last_updated"`
}

type HTMXRequest struct {
	EventType   HTMXEventType         `json:"event_type"`
	Target      string                `json:"target"`
	Trigger     string                `json:"trigger"`
	UserID      string                `json:"user_id"`
	SessionID   string                `json:"session_id"`
	Data        map[string]interface{} `json:"data"`
	Context     UserContext           `json:"context"`
	Timestamp   time.Time             `json:"timestamp"`
}

type HTMXResponse struct {
	HTML        string                 `json:"html"`
	JavaScript  string                 `json:"javascript"`
	CSS         string                 `json:"css"`
	Headers     map[string]string      `json:"headers"`
	Status      int                    `json:"status"`
	Message     string                 `json:"message"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type AIComponent struct {
	ID          string                 `json:"id"`
	Type        AIComponentType        `json:"type"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	HTML        string                 `json:"html"`
	JavaScript  string                 `json:"javascript"`
	CSS         string                 `json:"css"`
	Config      map[string]interface{} `json:"config"`
	UserID      string                 `json:"user_id"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type SmartFormField struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Label       string                 `json:"label"`
	Placeholder string                 `json:"placeholder"`
	Required    bool                   `json:"required"`
	Validation  map[string]interface{} `json:"validation"`
	Suggestions []string               `json:"suggestions"`
	DefaultValue interface{}           `json:"default_value"`
}

type IntelligentSearch struct {
	Query       string                 `json:"query"`
	Filters     map[string]interface{} `json:"filters"`
	SortBy      string                 `json:"sort_by"`
	SortOrder   string                 `json:"sort_order"`
	Limit       int                    `json:"limit"`
	Offset      int                    `json:"offset"`
	UserID      string                 `json:"user_id"`
	Context     UserContext            `json:"context"`
}

type AIAssistant struct {
	ID          string                 `json:"id"`
	UserID      string                 `json:"user_id"`
	Message     string                 `json:"message"`
	Response    string                 `json:"response"`
	Context     string                 `json:"context"`
	Confidence  float64                `json:"confidence"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type PredictionModel struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Algorithm   string                 `json:"algorithm"`
	Accuracy    float64                `json:"accuracy"`
	Parameters  map[string]interface{} `json:"parameters"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type AnalyticsDataset struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        AnalyticsType          `json:"type"`
	Description string                 `json:"description"`
	Data        []interface{}          `json:"data"`
	Schema      map[string]string      `json:"schema"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

type PredictionResult struct {
	ID          string                 `json:"id"`
	ModelID     string                 `json:"model_id"`
	Input       map[string]interface{} `json:"input"`
	Output      interface{}            `json:"output"`
	Confidence  float64                `json:"confidence"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type TrendAnalysis struct {
	ID          string                 `json:"id"`
	DatasetID   string                 `json:"dataset_id"`
	Metric      string                 `json:"metric"`
	Trend       string                 `json:"trend"`
	Slope       float64                `json:"slope"`
	R2          float64                `json:"r2"`
	PValue      float64                `json:"p_value"`
	Confidence  float64                `json:"confidence"`
	Period      string                 `json:"period"`
	DataPoints  []interface{}          `json:"data_points"`
	CreatedAt   time.Time              `json:"created_at"`
}

type CorrelationAnalysis struct {
	ID          string                 `json:"id"`
	DatasetID   string                 `json:"dataset_id"`
	Variable1   string                 `json:"variable1"`
	Variable2   string                 `json:"variable2"`
	Correlation float64                `json:"correlation"`
	PValue      float64                `json:"p_value"`
	Significance string                `json:"significance"`
	SampleSize  int                    `json:"sample_size"`
	CreatedAt   time.Time              `json:"created_at"`
}

type AnomalyDetection struct {
	ID          string                 `json:"id"`
	DatasetID   string                 `json:"dataset_id"`
	Metric      string                 `json:"metric"`
	AnomalyType string                 `json:"anomaly_type"`
	Value       interface{}            `json:"value"`
	Threshold   float64                `json:"threshold"`
	Severity    string                 `json:"severity"`
	Timestamp   time.Time              `json:"timestamp"`
	Description string                 `json:"description"`
	CreatedAt   time.Time              `json:"created_at"`
}

type Insight struct {
	ID          string                 `json:"id"`
	Type        InsightType            `json:"type"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Category    string                 `json:"category"`
	Priority    int                    `json:"priority"`
	Confidence  float64                `json:"confidence"`
	Data        map[string]interface{} `json:"data"`
	CreatedAt   time.Time              `json:"created_at"`
	ExpiresAt   *time.Time             `json:"expires_at"`
}

type PerformanceMetrics struct {
	ID          string                 `json:"id"`
	Category    string                 `json:"category"`
	Metric      string                 `json:"metric"`
	Value       float64                `json:"value"`
	Unit        string                 `json:"unit"`
	Threshold   float64                `json:"threshold"`
	Status      string                 `json:"status"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Request/Response Models
type RecordUserActionRequest struct {
	UserID      string                 `json:"user_id"`
	SessionID   string                 `json:"session_id"`
	ActionType  UserActionType         `json:"action_type"`
	Resource    string                 `json:"resource"`
	Context     UserContext            `json:"context"`
	Duration    int                    `json:"duration"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type GetUserPatternsRequest struct {
	UserID      string      `json:"user_id"`
	PatternType *PatternType `json:"pattern_type"`
	Limit       int          `json:"limit"`
	Offset      int          `json:"offset"`
}

type GetUserRecommendationsRequest struct {
	UserID string `json:"user_id"`
	Limit  int    `json:"limit"`
	Offset int    `json:"offset"`
}

type ProcessHTMXRequest struct {
	EventType   HTMXEventType         `json:"event_type"`
	Target      string                `json:"target"`
	Trigger     string                `json:"trigger"`
	UserID      string                `json:"user_id"`
	SessionID   string                `json:"session_id"`
	Data        map[string]interface{} `json:"data"`
	Context     UserContext           `json:"context"`
}

type CreateAnalyticsDatasetRequest struct {
	Name        string        `json:"name"`
	Type        AnalyticsType `json:"type"`
	Description string        `json:"description"`
	Data        []interface{} `json:"data"`
	Schema      map[string]string `json:"schema"`
}

type PredictUserBehaviorRequest struct {
	UserID      string                 `json:"user_id"`
	ModelType   string                 `json:"model_type"`
	Input       map[string]interface{} `json:"input"`
	Horizon     int                    `json:"horizon"`
}

type AnalyzeTrendsRequest struct {
	DatasetID   string `json:"dataset_id"`
	Metric      string `json:"metric"`
	Period      string `json:"period"`
	Confidence  float64 `json:"confidence"`
}

type AnalyzeCorrelationsRequest struct {
	DatasetID   string `json:"dataset_id"`
	Variable1   string `json:"variable1"`
	Variable2   string `json:"variable2"`
}

type DetectAnomaliesRequest struct {
	DatasetID   string  `json:"dataset_id"`
	Metric      string  `json:"metric"`
	Threshold   float64 `json:"threshold"`
	WindowSize  int     `json:"window_size"`
}

type GenerateInsightsRequest struct {
	UserID      string   `json:"user_id"`
	Categories  []string `json:"categories"`
	Limit       int      `json:"limit"`
	Confidence  float64  `json:"confidence"`
}

type TrackPerformanceMetricsRequest struct {
	Category    string                 `json:"category"`
	Metric      string                 `json:"metric"`
	Value       float64                `json:"value"`
	Unit        string                 `json:"unit"`
	Threshold   float64                `json:"threshold"`
	Metadata    map[string]interface{} `json:"metadata"`
}

type DismissRecommendationRequest struct {
	RecommendationID string `json:"recommendation_id"`
	UserID           string `json:"user_id"`
	Reason           string `json:"reason"`
}

type ApplyRecommendationRequest struct {
	RecommendationID string                 `json:"recommendation_id"`
	UserID           string                 `json:"user_id"`
	Parameters       map[string]interface{} `json:"parameters"`
}

// AIService handles AI integration with Python services
type AIService struct {
	baseURL    string
	httpClient *http.Client
}

// NewAIService creates a new AI service client
func NewAIService(baseURL string) *AIService {
	return &AIService{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// User Pattern Learning Methods
func (s *AIService) RecordUserAction(req RecordUserActionRequest) (*UserAction, error) {
	url := fmt.Sprintf("%s/ai/user-actions", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to record user action: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to record user action: status %d", resp.StatusCode)
	}
	
	var userAction UserAction
	if err := json.NewDecoder(resp.Body).Decode(&userAction); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &userAction, nil
}

func (s *AIService) GetUserPatterns(req GetUserPatternsRequest) ([]UserPattern, error) {
	url := fmt.Sprintf("%s/ai/user-patterns", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to get user patterns: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get user patterns: status %d", resp.StatusCode)
	}
	
	var patterns []UserPattern
	if err := json.NewDecoder(resp.Body).Decode(&patterns); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return patterns, nil
}

func (s *AIService) GetUserRecommendations(req GetUserRecommendationsRequest) ([]UserRecommendation, error) {
	url := fmt.Sprintf("%s/ai/user-recommendations", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to get user recommendations: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get user recommendations: status %d", resp.StatusCode)
	}
	
	var recommendations []UserRecommendation
	if err := json.NewDecoder(resp.Body).Decode(&recommendations); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return recommendations, nil
}

func (s *AIService) GetUserAnalytics(userID string) (*UserAnalytics, error) {
	url := fmt.Sprintf("%s/ai/user-analytics/%s", s.baseURL, userID)
	
	resp, err := s.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to get user analytics: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get user analytics: status %d", resp.StatusCode)
	}
	
	var analytics UserAnalytics
	if err := json.NewDecoder(resp.Body).Decode(&analytics); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &analytics, nil
}

// AI Frontend Integration Methods
func (s *AIService) ProcessHTMXRequest(req ProcessHTMXRequest) (*HTMXResponse, error) {
	url := fmt.Sprintf("%s/ai/htmx/process", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to process HTMX request: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to process HTMX request: status %d", resp.StatusCode)
	}
	
	var htmxResponse HTMXResponse
	if err := json.NewDecoder(resp.Body).Decode(&htmxResponse); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &htmxResponse, nil
}

func (s *AIService) GetAIComponent(componentID string) (*AIComponent, error) {
	url := fmt.Sprintf("%s/ai/components/%s", s.baseURL, componentID)
	
	resp, err := s.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to get AI component: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get AI component: status %d", resp.StatusCode)
	}
	
	var component AIComponent
	if err := json.NewDecoder(resp.Body).Decode(&component); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &component, nil
}

// Advanced AI Analytics Methods
func (s *AIService) CreateAnalyticsDataset(req CreateAnalyticsDatasetRequest) (*AnalyticsDataset, error) {
	url := fmt.Sprintf("%s/ai/analytics/datasets", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create analytics dataset: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to create analytics dataset: status %d", resp.StatusCode)
	}
	
	var dataset AnalyticsDataset
	if err := json.NewDecoder(resp.Body).Decode(&dataset); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &dataset, nil
}

func (s *AIService) PredictUserBehavior(req PredictUserBehaviorRequest) (*PredictionResult, error) {
	url := fmt.Sprintf("%s/ai/analytics/predict", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to predict user behavior: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to predict user behavior: status %d", resp.StatusCode)
	}
	
	var result PredictionResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &result, nil
}

func (s *AIService) AnalyzeTrends(req AnalyzeTrendsRequest) (*TrendAnalysis, error) {
	url := fmt.Sprintf("%s/ai/analytics/trends", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to analyze trends: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to analyze trends: status %d", resp.StatusCode)
	}
	
	var analysis TrendAnalysis
	if err := json.NewDecoder(resp.Body).Decode(&analysis); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &analysis, nil
}

func (s *AIService) AnalyzeCorrelations(req AnalyzeCorrelationsRequest) (*CorrelationAnalysis, error) {
	url := fmt.Sprintf("%s/ai/analytics/correlations", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to analyze correlations: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to analyze correlations: status %d", resp.StatusCode)
	}
	
	var analysis CorrelationAnalysis
	if err := json.NewDecoder(resp.Body).Decode(&analysis); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &analysis, nil
}

func (s *AIService) DetectAnomalies(req DetectAnomaliesRequest) (*AnomalyDetection, error) {
	url := fmt.Sprintf("%s/ai/analytics/anomalies", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to detect anomalies: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to detect anomalies: status %d", resp.StatusCode)
	}
	
	var detection AnomalyDetection
	if err := json.NewDecoder(resp.Body).Decode(&detection); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &detection, nil
}

func (s *AIService) GenerateInsights(req GenerateInsightsRequest) ([]Insight, error) {
	url := fmt.Sprintf("%s/ai/analytics/insights", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to generate insights: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to generate insights: status %d", resp.StatusCode)
	}
	
	var insights []Insight
	if err := json.NewDecoder(resp.Body).Decode(&insights); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return insights, nil
}

func (s *AIService) TrackPerformanceMetrics(req TrackPerformanceMetricsRequest) (*PerformanceMetrics, error) {
	url := fmt.Sprintf("%s/ai/analytics/performance", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to track performance metrics: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to track performance metrics: status %d", resp.StatusCode)
	}
	
	var metrics PerformanceMetrics
	if err := json.NewDecoder(resp.Body).Decode(&metrics); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}
	
	return &metrics, nil
}

// Recommendation Management Methods
func (s *AIService) DismissRecommendation(req DismissRecommendationRequest) error {
	url := fmt.Sprintf("%s/ai/recommendations/dismiss", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to dismiss recommendation: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to dismiss recommendation: status %d", resp.StatusCode)
	}
	
	return nil
}

func (s *AIService) ApplyRecommendation(req ApplyRecommendationRequest) error {
	url := fmt.Sprintf("%s/ai/recommendations/apply", s.baseURL)
	
	jsonData, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %v", err)
	}
	
	resp, err := s.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to apply recommendation: %v", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to apply recommendation: status %d", resp.StatusCode)
	}
	
	return nil
}
