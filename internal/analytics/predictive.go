package analytics

import (
	"fmt"
	"math"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ProcessDataPoint processes a data point for predictive analytics
func (pe *PredictiveEngine) ProcessDataPoint(dataPoint EnergyDataPoint) error {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	// Convert data point to training data
	trainingPoint := TrainingDataPoint{
		Features: map[string]float64{
			"consumption": dataPoint.Consumption,
			"temperature": dataPoint.Temperature,
			"humidity":    dataPoint.Humidity,
			"occupancy":   float64(dataPoint.Occupancy),
			"hour":        float64(dataPoint.Timestamp.Hour()),
			"day_of_week": float64(dataPoint.Timestamp.Weekday()),
			"month":       float64(dataPoint.Timestamp.Month()),
		},
		Target:    dataPoint.Consumption,
		Timestamp: dataPoint.Timestamp,
		Weight:    1.0,
	}

	// Update models with new data
	for _, model := range pe.models {
		if model.Status == "ready" {
			if err := pe.updateModel(&model, trainingPoint); err != nil {
				logger.Error("Error updating model %s: %v", model.ID, err)
			}
		}
	}

	// Update trends
	if err := pe.updateTrends(dataPoint); err != nil {
		logger.Error("Error updating trends: %v", err)
		return err
	}

	// Update metrics
	pe.updatePredictiveMetrics()

	logger.Debug("Predictive data processed successfully")
	return nil
}

// updateModel updates a predictive model with new training data
func (pe *PredictiveEngine) updateModel(model *PredictiveModel, trainingPoint TrainingDataPoint) error {
	// Add training point to model
	model.TrainingData = append(model.TrainingData, trainingPoint)

	// Keep only recent training data (last 1000 points)
	if len(model.TrainingData) > 1000 {
		model.TrainingData = model.TrainingData[len(model.TrainingData)-1000:]
	}

	// Update model accuracy (simplified calculation)
	if len(model.TrainingData) > 10 {
		accuracy := pe.calculateModelAccuracy(model)
		model.Accuracy = accuracy
		model.LastTrained = time.Now()
	}

	return nil
}

// calculateModelAccuracy calculates model accuracy
func (pe *PredictiveEngine) calculateModelAccuracy(model *PredictiveModel) float64 {
	if len(model.TrainingData) < 2 {
		return 0.0
	}

	// Simple accuracy calculation based on variance
	var totalError float64
	var totalVariance float64
	mean := pe.calculateMean(model.TrainingData)

	for _, point := range model.TrainingData {
		error := math.Abs(point.Target - mean)
		totalError += error * error
		totalVariance += (point.Target - mean) * (point.Target - mean)
	}

	if totalVariance == 0 {
		return 1.0
	}

	accuracy := 1.0 - (totalError / totalVariance)
	return math.Max(0.0, math.Min(1.0, accuracy))
}

// calculateMean calculates the mean of training data targets
func (pe *PredictiveEngine) calculateMean(data []TrainingDataPoint) float64 {
	if len(data) == 0 {
		return 0.0
	}

	var sum float64
	for _, point := range data {
		sum += point.Target
	}

	return sum / float64(len(data))
}

// updateTrends updates trend analysis
func (pe *PredictiveEngine) updateTrends(dataPoint EnergyDataPoint) error {
	metric := "energy_consumption"
	key := fmt.Sprintf("%s_%s", metric, dataPoint.BuildingID)

	trend, exists := pe.trends[key]
	if !exists {
		trend = Trend{
			ID:           key,
			Metric:       metric,
			Direction:    "stable",
			Slope:        0,
			R2:           0,
			PValue:       1.0,
			Significance: false,
			StartTime:    dataPoint.Timestamp,
			EndTime:      dataPoint.Timestamp,
			DataPoints:   1,
		}
	} else {
		// Update trend with new data point
		trend.EndTime = dataPoint.Timestamp
		trend.DataPoints++

		// Calculate new slope and R2
		slope, r2, pValue := pe.calculateTrend(trend, dataPoint)
		trend.Slope = slope
		trend.R2 = r2
		trend.PValue = pValue

		// Update direction based on slope
		if slope > 0.01 {
			trend.Direction = "increasing"
		} else if slope < -0.01 {
			trend.Direction = "decreasing"
		} else {
			trend.Direction = "stable"
		}

		// Update significance
		trend.Significance = pValue < 0.05
	}

	pe.trends[key] = trend
	return nil
}

// calculateTrend calculates trend statistics
func (pe *PredictiveEngine) calculateTrend(trend Trend, dataPoint EnergyDataPoint) (float64, float64, float64) {
	// Simplified trend calculation
	// In a real implementation, this would use proper statistical methods

	// Calculate slope using simple linear regression
	n := float64(trend.DataPoints)
	if n < 2 {
		return 0, 0, 1.0
	}

	// Calculate time difference in hours
	timeDiff := dataPoint.Timestamp.Sub(trend.StartTime).Hours()
	if timeDiff == 0 {
		return 0, 0, 1.0
	}

	// Simple slope calculation
	slope := dataPoint.Consumption / timeDiff

	// Calculate R2 (simplified)
	r2 := 0.8 // Placeholder value

	// Calculate p-value (simplified)
	pValue := 0.05 // Placeholder value

	return slope, r2, pValue
}

// updatePredictiveMetrics updates predictive analytics metrics
func (pe *PredictiveEngine) updatePredictiveMetrics() {
	pe.metrics.TotalModels = int64(len(pe.models))

	activeModels := 0
	trainingModels := 0
	errorModels := 0
	var totalAccuracy float64
	var totalPrecision float64
	var totalRecall float64
	var totalF1Score float64

	for _, model := range pe.models {
		switch model.Status {
		case "ready":
			activeModels++
		case "training":
			trainingModels++
		case "error":
			errorModels++
		}

		totalAccuracy += model.Accuracy
		totalPrecision += model.Precision
		totalRecall += model.Recall
		totalF1Score += model.F1Score
	}

	pe.metrics.ActiveModels = int64(activeModels)
	pe.metrics.TrainingModels = int64(trainingModels)
	pe.metrics.ErrorModels = int64(errorModels)

	if len(pe.models) > 0 {
		pe.metrics.AverageAccuracy = totalAccuracy / float64(len(pe.models))
		pe.metrics.AveragePrecision = totalPrecision / float64(len(pe.models))
		pe.metrics.AverageRecall = totalRecall / float64(len(pe.models))
		pe.metrics.AverageF1Score = totalF1Score / float64(len(pe.models))
	}
}

// CreateModel creates a new predictive model
func (pe *PredictiveEngine) CreateModel(model PredictiveModel) error {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	if model.ID == "" {
		model.ID = fmt.Sprintf("model_%d", time.Now().UnixNano())
	}

	model.Status = "training"
	model.LastTrained = time.Now()
	pe.models[model.ID] = model

	logger.Info("Predictive model created: %s", model.ID)
	return nil
}

// UpdateModel updates an existing predictive model
func (pe *PredictiveEngine) UpdateModel(modelID string, model PredictiveModel) error {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	if _, exists := pe.models[modelID]; !exists {
		return fmt.Errorf("model not found: %s", modelID)
	}

	model.ID = modelID
	pe.models[modelID] = model

	logger.Info("Predictive model updated: %s", modelID)
	return nil
}

// DeleteModel deletes a predictive model
func (pe *PredictiveEngine) DeleteModel(modelID string) error {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	if _, exists := pe.models[modelID]; !exists {
		return fmt.Errorf("model not found: %s", modelID)
	}

	delete(pe.models, modelID)
	logger.Info("Predictive model deleted: %s", modelID)
	return nil
}

// GetModel returns a specific predictive model
func (pe *PredictiveEngine) GetModel(modelID string) (*PredictiveModel, error) {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	model, exists := pe.models[modelID]
	if !exists {
		return nil, fmt.Errorf("model not found: %s", modelID)
	}

	return &model, nil
}

// GetModels returns all predictive models
func (pe *PredictiveEngine) GetModels() []PredictiveModel {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	var models []PredictiveModel
	for _, model := range pe.models {
		models = append(models, model)
	}

	return models
}

// TrainModel trains a predictive model
func (pe *PredictiveEngine) TrainModel(modelID string) error {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	model, exists := pe.models[modelID]
	if !exists {
		return fmt.Errorf("model not found: %s", modelID)
	}

	model.Status = "training"
	pe.models[modelID] = model

	// Simulate training process
	go func() {
		time.Sleep(5 * time.Second) // Simulate training time

		pe.mu.Lock()
		defer pe.mu.Unlock()

		model.Status = "ready"
		model.LastTrained = time.Now()
		pe.models[modelID] = model

		logger.Info("Model training completed: %s", modelID)
	}()

	logger.Info("Model training started: %s", modelID)
	return nil
}

// GetForecast generates a forecast for a specific metric
func (pe *PredictiveEngine) GetForecast(metric string, duration time.Duration) (*Forecast, error) {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	// Find the best model for this metric
	var bestModel *PredictiveModel
	bestAccuracy := 0.0

	for _, model := range pe.models {
		if model.Status == "ready" && model.Target == metric {
			if model.Accuracy > bestAccuracy {
				bestAccuracy = model.Accuracy
				bestModel = &model
			}
		}
	}

	if bestModel == nil {
		return nil, fmt.Errorf("no trained model found for metric: %s", metric)
	}

	// Generate forecast
	forecast := pe.generateForecast(bestModel, duration)
	pe.forecasts[forecast.ID] = forecast

	pe.metrics.TotalForecasts++
	if forecast.Accuracy > 0.8 {
		pe.metrics.AccurateForecasts++
	}

	return &forecast, nil
}

// generateForecast generates a forecast using a model
func (pe *PredictiveEngine) generateForecast(model *PredictiveModel, duration time.Duration) Forecast {
	forecastID := fmt.Sprintf("forecast_%d", time.Now().UnixNano())
	startTime := time.Now()
	endTime := startTime.Add(duration)
	interval := time.Hour

	var values []ForecastValue
	currentTime := startTime

	for currentTime.Before(endTime) {
		// Generate forecast value (simplified)
		value := pe.predictValue(model, currentTime)
		confidence := model.Accuracy

		// Calculate bounds
		variance := 1.0 - confidence
		lowerBound := value - variance
		upperBound := value + variance

		values = append(values, ForecastValue{
			Timestamp:  currentTime,
			Value:      value,
			LowerBound: lowerBound,
			UpperBound: upperBound,
			Confidence: confidence,
		})

		currentTime = currentTime.Add(interval)
	}

	return Forecast{
		ID:         forecastID,
		ModelID:    model.ID,
		Target:     model.Target,
		StartTime:  startTime,
		EndTime:    endTime,
		Interval:   interval,
		Values:     values,
		Confidence: model.Accuracy,
		Accuracy:   model.Accuracy,
		CreatedAt:  time.Now(),
	}
}

// predictValue predicts a value using a model
func (pe *PredictiveEngine) predictValue(model *PredictiveModel, timestamp time.Time) float64 {
	// Simplified prediction based on historical data
	if len(model.TrainingData) == 0 {
		return 0.0
	}

	// Calculate average from training data
	var sum float64
	for _, point := range model.TrainingData {
		sum += point.Target
	}
	average := sum / float64(len(model.TrainingData))

	// Add some time-based variation
	hour := float64(timestamp.Hour())
	dayOfWeek := float64(timestamp.Weekday())

	// Simple time-based adjustment
	timeAdjustment := math.Sin(hour*math.Pi/12) * 0.1
	dayAdjustment := math.Sin(dayOfWeek*math.Pi/7) * 0.05

	return average + timeAdjustment + dayAdjustment
}

// GetTrends returns trend analysis
func (pe *PredictiveEngine) GetTrends(metric string) ([]Trend, error) {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	var trends []Trend
	for _, trend := range pe.trends {
		if metric == "" || trend.Metric == metric {
			trends = append(trends, trend)
		}
	}

	// Sort by significance
	sort.Slice(trends, func(i, j int) bool {
		return trends[i].Significance && !trends[j].Significance
	})

	return trends, nil
}

// GetTrend returns a specific trend
func (pe *PredictiveEngine) GetTrend(trendID string) (*Trend, error) {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	trend, exists := pe.trends[trendID]
	if !exists {
		return nil, fmt.Errorf("trend not found: %s", trendID)
	}

	return &trend, nil
}

// AddAlgorithm adds a new machine learning algorithm
func (pe *PredictiveEngine) AddAlgorithm(algorithm Algorithm) error {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	if algorithm.ID == "" {
		algorithm.ID = fmt.Sprintf("algo_%d", time.Now().UnixNano())
	}

	algorithm.Status = "ready"
	pe.algorithms[algorithm.ID] = algorithm

	logger.Info("Algorithm added: %s", algorithm.ID)
	return nil
}

// GetAlgorithm returns a specific algorithm
func (pe *PredictiveEngine) GetAlgorithm(algorithmID string) (*Algorithm, error) {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	algorithm, exists := pe.algorithms[algorithmID]
	if !exists {
		return nil, fmt.Errorf("algorithm not found: %s", algorithmID)
	}

	return &algorithm, nil
}

// GetAlgorithms returns all algorithms
func (pe *PredictiveEngine) GetAlgorithms() []Algorithm {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	var algorithms []Algorithm
	for _, algorithm := range pe.algorithms {
		algorithms = append(algorithms, algorithm)
	}

	return algorithms
}

// GetPredictiveMetrics returns predictive analytics metrics
func (pe *PredictiveEngine) GetPredictiveMetrics() *PredictiveMetrics {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	return pe.metrics
}

// GetForecasts returns all forecasts
func (pe *PredictiveEngine) GetForecasts() []Forecast {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	var forecasts []Forecast
	for _, forecast := range pe.forecasts {
		forecasts = append(forecasts, forecast)
	}

	return forecasts
}

// GetForecast returns a specific forecast
func (pe *PredictiveEngine) GetForecastByID(forecastID string) (*Forecast, error) {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	forecast, exists := pe.forecasts[forecastID]
	if !exists {
		return nil, fmt.Errorf("forecast not found: %s", forecastID)
	}

	return &forecast, nil
}

// DeleteForecast deletes a forecast
func (pe *PredictiveEngine) DeleteForecast(forecastID string) error {
	pe.mu.Lock()
	defer pe.mu.Unlock()

	if _, exists := pe.forecasts[forecastID]; !exists {
		return fmt.Errorf("forecast not found: %s", forecastID)
	}

	delete(pe.forecasts, forecastID)
	logger.Info("Forecast deleted: %s", forecastID)
	return nil
}
