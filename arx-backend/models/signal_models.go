package models

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

// SignalAnalysis represents a signal propagation analysis in the database
type SignalAnalysis struct {
	ID                string          `json:"id" db:"id"`
	UserID            string          `json:"user_id" db:"user_id"`
	ProjectID         string          `json:"project_id" db:"project_id"`
	RequestData       json.RawMessage `json:"request_data" db:"request_data"`
	ResultData        json.RawMessage `json:"result_data" db:"result_data"`
	Status            string          `json:"status" db:"status"`
	AnalysisType      string          `json:"analysis_type" db:"analysis_type"`
	PropagationModel  string          `json:"propagation_model" db:"propagation_model"`
	EnvironmentType   string          `json:"environment_type" db:"environment_type"`
	Frequency         float64         `json:"frequency" db:"frequency"`
	Power             float64         `json:"power" db:"power"`
	Distance          float64         `json:"distance" db:"distance"`
	PathLoss          float64         `json:"path_loss" db:"path_loss"`
	ReceivedPower     float64         `json:"received_power" db:"received_power"`
	SignalStrength    float64         `json:"signal_strength" db:"signal_strength"`
	SNR               float64         `json:"snr" db:"snr"`
	InterferenceLevel float64         `json:"interference_level" db:"interference_level"`
	AnalysisTime      float64         `json:"analysis_time" db:"analysis_time"`
	CreatedAt         time.Time       `json:"created_at" db:"created_at"`
	UpdatedAt         time.Time       `json:"updated_at" db:"updated_at"`
	CompletedAt       *time.Time      `json:"completed_at" db:"completed_at"`
	Error             *string         `json:"error" db:"error"`
}

// AntennaAnalysis represents an antenna analysis in the database
type AntennaAnalysis struct {
	ID               string          `json:"id" db:"id"`
	UserID           string          `json:"user_id" db:"user_id"`
	ProjectID        string          `json:"project_id" db:"project_id"`
	RequestData      json.RawMessage `json:"request_data" db:"request_data"`
	ResultData       json.RawMessage `json:"result_data" db:"result_data"`
	Status           string          `json:"status" db:"status"`
	AnalysisType     string          `json:"analysis_type" db:"analysis_type"`
	AntennaType      string          `json:"antenna_type" db:"antenna_type"`
	Frequency        float64         `json:"frequency" db:"frequency"`
	MaxGain          float64         `json:"max_gain" db:"max_gain"`
	Directivity      float64         `json:"directivity" db:"directivity"`
	Efficiency       float64         `json:"efficiency" db:"efficiency"`
	Bandwidth        float64         `json:"bandwidth" db:"bandwidth"`
	VSWR             float64         `json:"vswr" db:"vswr"`
	BeamwidthH       float64         `json:"beamwidth_h" db:"beamwidth_h"`
	BeamwidthV       float64         `json:"beamwidth_v" db:"beamwidth_v"`
	FrontToBackRatio float64         `json:"front_to_back_ratio" db:"front_to_back_ratio"`
	SideLobeLevel    float64         `json:"side_lobe_level" db:"side_lobe_level"`
	AnalysisTime     float64         `json:"analysis_time" db:"analysis_time"`
	CreatedAt        time.Time       `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time       `json:"updated_at" db:"updated_at"`
	CompletedAt      *time.Time      `json:"completed_at" db:"completed_at"`
	Error            *string         `json:"error" db:"error"`
}

// InterferenceAnalysis represents an interference analysis in the database
type InterferenceAnalysis struct {
	ID                         string          `json:"id" db:"id"`
	UserID                     string          `json:"user_id" db:"user_id"`
	ProjectID                  string          `json:"project_id" db:"project_id"`
	RequestData                json.RawMessage `json:"request_data" db:"request_data"`
	ResultData                 json.RawMessage `json:"result_data" db:"result_data"`
	Status                     string          `json:"status" db:"status"`
	AnalysisType               string          `json:"analysis_type" db:"analysis_type"`
	InterferenceType           string          `json:"interference_type" db:"interference_type"`
	Severity                   string          `json:"severity" db:"severity"`
	InterferenceLevel          float64         `json:"interference_level" db:"interference_level"`
	SignalToInterferenceRatio  float64         `json:"signal_to_interference_ratio" db:"signal_to_interference_ratio"`
	CarrierToInterferenceRatio float64         `json:"carrier_to_interference_ratio" db:"carrier_to_interference_ratio"`
	InterferencePower          float64         `json:"interference_power" db:"interference_power"`
	AnalysisTime               float64         `json:"analysis_time" db:"analysis_time"`
	CreatedAt                  time.Time       `json:"created_at" db:"created_at"`
	UpdatedAt                  time.Time       `json:"updated_at" db:"updated_at"`
	CompletedAt                *time.Time      `json:"completed_at" db:"completed_at"`
	Error                      *string         `json:"error" db:"error"`
}

// SignalProject represents a signal analysis project
type SignalProject struct {
	ID          string    `json:"id" db:"id"`
	UserID      string    `json:"user_id" db:"user_id"`
	Name        string    `json:"name" db:"name"`
	Description string    `json:"description" db:"description"`
	Status      string    `json:"status" db:"status"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// SignalAnalysisRepository provides database operations for signal analysis
type SignalAnalysisRepository struct {
	db     *sql.DB
	logger *logrus.Logger
}

// NewSignalAnalysisRepository creates a new signal analysis repository
func NewSignalAnalysisRepository(db *sql.DB, logger *logrus.Logger) *SignalAnalysisRepository {
	return &SignalAnalysisRepository{
		db:     db,
		logger: logger,
	}
}

// CreateSignalAnalysis creates a new signal analysis record
func (r *SignalAnalysisRepository) CreateSignalAnalysis(analysis *SignalAnalysis) error {
	analysis.ID = uuid.New().String()
	analysis.CreatedAt = time.Now()
	analysis.UpdatedAt = time.Now()
	analysis.Status = "pending"

	query := `
		INSERT INTO signal_analyses (
			id, user_id, project_id, request_data, result_data, status, 
			analysis_type, propagation_model, environment_type, frequency, 
			power, distance, path_loss, received_power, signal_strength, 
			snr, interference_level, analysis_time, created_at, updated_at, 
			completed_at, error
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 
			$15, $16, $17, $18, $19, $20, $21, $22
		)
	`

	_, err := r.db.Exec(query,
		analysis.ID, analysis.UserID, analysis.ProjectID, analysis.RequestData,
		analysis.ResultData, analysis.Status, analysis.AnalysisType,
		analysis.PropagationModel, analysis.EnvironmentType, analysis.Frequency,
		analysis.Power, analysis.Distance, analysis.PathLoss, analysis.ReceivedPower,
		analysis.SignalStrength, analysis.SNR, analysis.InterferenceLevel,
		analysis.AnalysisTime, analysis.CreatedAt, analysis.UpdatedAt,
		analysis.CompletedAt, analysis.Error,
	)

	if err != nil {
		r.logger.Errorf("Failed to create signal analysis: %v", err)
		return fmt.Errorf("failed to create signal analysis: %w", err)
	}

	r.logger.Infof("Created signal analysis with ID: %s", analysis.ID)
	return nil
}

// GetSignalAnalysis retrieves a signal analysis by ID
func (r *SignalAnalysisRepository) GetSignalAnalysis(id string) (*SignalAnalysis, error) {
	query := `
		SELECT id, user_id, project_id, request_data, result_data, status,
			analysis_type, propagation_model, environment_type, frequency,
			power, distance, path_loss, received_power, signal_strength,
			snr, interference_level, analysis_time, created_at, updated_at,
			completed_at, error
		FROM signal_analyses
		WHERE id = $1
	`

	var analysis SignalAnalysis
	err := r.db.QueryRow(query, id).Scan(
		&analysis.ID, &analysis.UserID, &analysis.ProjectID, &analysis.RequestData,
		&analysis.ResultData, &analysis.Status, &analysis.AnalysisType,
		&analysis.PropagationModel, &analysis.EnvironmentType, &analysis.Frequency,
		&analysis.Power, &analysis.Distance, &analysis.PathLoss, &analysis.ReceivedPower,
		&analysis.SignalStrength, &analysis.SNR, &analysis.InterferenceLevel,
		&analysis.AnalysisTime, &analysis.CreatedAt, &analysis.UpdatedAt,
		&analysis.CompletedAt, &analysis.Error,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("signal analysis not found: %s", id)
		}
		r.logger.Errorf("Failed to get signal analysis: %v", err)
		return nil, fmt.Errorf("failed to get signal analysis: %w", err)
	}

	return &analysis, nil
}

// UpdateSignalAnalysis updates a signal analysis record
func (r *SignalAnalysisRepository) UpdateSignalAnalysis(analysis *SignalAnalysis) error {
	analysis.UpdatedAt = time.Now()

	query := `
		UPDATE signal_analyses SET
			request_data = $1, result_data = $2, status = $3,
			analysis_type = $4, propagation_model = $5, environment_type = $6,
			frequency = $7, power = $8, distance = $9, path_loss = $10,
			received_power = $11, signal_strength = $12, snr = $13,
			interference_level = $14, analysis_time = $15, updated_at = $16,
			completed_at = $17, error = $18
		WHERE id = $19
	`

	_, err := r.db.Exec(query,
		analysis.RequestData, analysis.ResultData, analysis.Status,
		analysis.AnalysisType, analysis.PropagationModel, analysis.EnvironmentType,
		analysis.Frequency, analysis.Power, analysis.Distance, analysis.PathLoss,
		analysis.ReceivedPower, analysis.SignalStrength, analysis.SNR,
		analysis.InterferenceLevel, analysis.AnalysisTime, analysis.UpdatedAt,
		analysis.CompletedAt, analysis.Error, analysis.ID,
	)

	if err != nil {
		r.logger.Errorf("Failed to update signal analysis: %v", err)
		return fmt.Errorf("failed to update signal analysis: %w", err)
	}

	r.logger.Infof("Updated signal analysis with ID: %s", analysis.ID)
	return nil
}

// ListSignalAnalyses retrieves signal analyses with pagination
func (r *SignalAnalysisRepository) ListSignalAnalyses(userID string, limit, offset int) ([]*SignalAnalysis, error) {
	query := `
		SELECT id, user_id, project_id, request_data, result_data, status,
			analysis_type, propagation_model, environment_type, frequency,
			power, distance, path_loss, received_power, signal_strength,
			snr, interference_level, analysis_time, created_at, updated_at,
			completed_at, error
		FROM signal_analyses
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := r.db.Query(query, userID, limit, offset)
	if err != nil {
		r.logger.Errorf("Failed to list signal analyses: %v", err)
		return nil, fmt.Errorf("failed to list signal analyses: %w", err)
	}
	defer rows.Close()

	var analyses []*SignalAnalysis
	for rows.Next() {
		var analysis SignalAnalysis
		err := rows.Scan(
			&analysis.ID, &analysis.UserID, &analysis.ProjectID, &analysis.RequestData,
			&analysis.ResultData, &analysis.Status, &analysis.AnalysisType,
			&analysis.PropagationModel, &analysis.EnvironmentType, &analysis.Frequency,
			&analysis.Power, &analysis.Distance, &analysis.PathLoss, &analysis.ReceivedPower,
			&analysis.SignalStrength, &analysis.SNR, &analysis.InterferenceLevel,
			&analysis.AnalysisTime, &analysis.CreatedAt, &analysis.UpdatedAt,
			&analysis.CompletedAt, &analysis.Error,
		)
		if err != nil {
			r.logger.Errorf("Failed to scan signal analysis: %v", err)
			continue
		}
		analyses = append(analyses, &analysis)
	}

	return analyses, nil
}

// DeleteSignalAnalysis deletes a signal analysis record
func (r *SignalAnalysisRepository) DeleteSignalAnalysis(id string) error {
	query := `DELETE FROM signal_analyses WHERE id = $1`

	_, err := r.db.Exec(query, id)
	if err != nil {
		r.logger.Errorf("Failed to delete signal analysis: %v", err)
		return fmt.Errorf("failed to delete signal analysis: %w", err)
	}

	r.logger.Infof("Deleted signal analysis with ID: %s", id)
	return nil
}

// AntennaAnalysisRepository provides database operations for antenna analysis
type AntennaAnalysisRepository struct {
	db     *sql.DB
	logger *logrus.Logger
}

// NewAntennaAnalysisRepository creates a new antenna analysis repository
func NewAntennaAnalysisRepository(db *sql.DB, logger *logrus.Logger) *AntennaAnalysisRepository {
	return &AntennaAnalysisRepository{
		db:     db,
		logger: logger,
	}
}

// CreateAntennaAnalysis creates a new antenna analysis record
func (r *AntennaAnalysisRepository) CreateAntennaAnalysis(analysis *AntennaAnalysis) error {
	analysis.ID = uuid.New().String()
	analysis.CreatedAt = time.Now()
	analysis.UpdatedAt = time.Now()
	analysis.Status = "pending"

	query := `
		INSERT INTO antenna_analyses (
			id, user_id, project_id, request_data, result_data, status,
			analysis_type, antenna_type, frequency, max_gain, directivity,
			efficiency, bandwidth, vswr, beamwidth_h, beamwidth_v,
			front_to_back_ratio, side_lobe_level, analysis_time, created_at,
			updated_at, completed_at, error
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
			$15, $16, $17, $18, $19, $20, $21, $22, $23
		)
	`

	_, err := r.db.Exec(query,
		analysis.ID, analysis.UserID, analysis.ProjectID, analysis.RequestData,
		analysis.ResultData, analysis.Status, analysis.AnalysisType,
		analysis.AntennaType, analysis.Frequency, analysis.MaxGain,
		analysis.Directivity, analysis.Efficiency, analysis.Bandwidth,
		analysis.VSWR, analysis.BeamwidthH, analysis.BeamwidthV,
		analysis.FrontToBackRatio, analysis.SideLobeLevel, analysis.AnalysisTime,
		analysis.CreatedAt, analysis.UpdatedAt, analysis.CompletedAt, analysis.Error,
	)

	if err != nil {
		r.logger.Errorf("Failed to create antenna analysis: %v", err)
		return fmt.Errorf("failed to create antenna analysis: %w", err)
	}

	r.logger.Infof("Created antenna analysis with ID: %s", analysis.ID)
	return nil
}

// GetAntennaAnalysis retrieves an antenna analysis by ID
func (r *AntennaAnalysisRepository) GetAntennaAnalysis(id string) (*AntennaAnalysis, error) {
	query := `
		SELECT id, user_id, project_id, request_data, result_data, status,
			analysis_type, antenna_type, frequency, max_gain, directivity,
			efficiency, bandwidth, vswr, beamwidth_h, beamwidth_v,
			front_to_back_ratio, side_lobe_level, analysis_time, created_at,
			updated_at, completed_at, error
		FROM antenna_analyses
		WHERE id = $1
	`

	var analysis AntennaAnalysis
	err := r.db.QueryRow(query, id).Scan(
		&analysis.ID, &analysis.UserID, &analysis.ProjectID, &analysis.RequestData,
		&analysis.ResultData, &analysis.Status, &analysis.AnalysisType,
		&analysis.AntennaType, &analysis.Frequency, &analysis.MaxGain,
		&analysis.Directivity, &analysis.Efficiency, &analysis.Bandwidth,
		&analysis.VSWR, &analysis.BeamwidthH, &analysis.BeamwidthV,
		&analysis.FrontToBackRatio, &analysis.SideLobeLevel, &analysis.AnalysisTime,
		&analysis.CreatedAt, &analysis.UpdatedAt, &analysis.CompletedAt, &analysis.Error,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("antenna analysis not found: %s", id)
		}
		r.logger.Errorf("Failed to get antenna analysis: %v", err)
		return nil, fmt.Errorf("failed to get antenna analysis: %w", err)
	}

	return &analysis, nil
}

// UpdateAntennaAnalysis updates an antenna analysis record
func (r *AntennaAnalysisRepository) UpdateAntennaAnalysis(analysis *AntennaAnalysis) error {
	analysis.UpdatedAt = time.Now()

	query := `
		UPDATE antenna_analyses SET
			request_data = $1, result_data = $2, status = $3,
			analysis_type = $4, antenna_type = $5, frequency = $6,
			max_gain = $7, directivity = $8, efficiency = $9,
			bandwidth = $10, vswr = $11, beamwidth_h = $12,
			beamwidth_v = $13, front_to_back_ratio = $14, side_lobe_level = $15,
			analysis_time = $16, updated_at = $17, completed_at = $18, error = $19
		WHERE id = $20
	`

	_, err := r.db.Exec(query,
		analysis.RequestData, analysis.ResultData, analysis.Status,
		analysis.AnalysisType, analysis.AntennaType, analysis.Frequency,
		analysis.MaxGain, analysis.Directivity, analysis.Efficiency,
		analysis.Bandwidth, analysis.VSWR, analysis.BeamwidthH,
		analysis.BeamwidthV, analysis.FrontToBackRatio, analysis.SideLobeLevel,
		analysis.AnalysisTime, analysis.UpdatedAt, analysis.CompletedAt, analysis.Error,
		analysis.ID,
	)

	if err != nil {
		r.logger.Errorf("Failed to update antenna analysis: %v", err)
		return fmt.Errorf("failed to update antenna analysis: %w", err)
	}

	r.logger.Infof("Updated antenna analysis with ID: %s", analysis.ID)
	return nil
}

// ListAntennaAnalyses retrieves antenna analyses with pagination
func (r *AntennaAnalysisRepository) ListAntennaAnalyses(userID string, limit, offset int) ([]*AntennaAnalysis, error) {
	query := `
		SELECT id, user_id, project_id, request_data, result_data, status,
			analysis_type, antenna_type, frequency, max_gain, directivity,
			efficiency, bandwidth, vswr, beamwidth_h, beamwidth_v,
			front_to_back_ratio, side_lobe_level, analysis_time, created_at,
			updated_at, completed_at, error
		FROM antenna_analyses
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := r.db.Query(query, userID, limit, offset)
	if err != nil {
		r.logger.Errorf("Failed to list antenna analyses: %v", err)
		return nil, fmt.Errorf("failed to list antenna analyses: %w", err)
	}
	defer rows.Close()

	var analyses []*AntennaAnalysis
	for rows.Next() {
		var analysis AntennaAnalysis
		err := rows.Scan(
			&analysis.ID, &analysis.UserID, &analysis.ProjectID, &analysis.RequestData,
			&analysis.ResultData, &analysis.Status, &analysis.AnalysisType,
			&analysis.AntennaType, &analysis.Frequency, &analysis.MaxGain,
			&analysis.Directivity, &analysis.Efficiency, &analysis.Bandwidth,
			&analysis.VSWR, &analysis.BeamwidthH, &analysis.BeamwidthV,
			&analysis.FrontToBackRatio, &analysis.SideLobeLevel, &analysis.AnalysisTime,
			&analysis.CreatedAt, &analysis.UpdatedAt, &analysis.CompletedAt, &analysis.Error,
		)
		if err != nil {
			r.logger.Errorf("Failed to scan antenna analysis: %v", err)
			continue
		}
		analyses = append(analyses, &analysis)
	}

	return analyses, nil
}

// DeleteAntennaAnalysis deletes an antenna analysis record
func (r *AntennaAnalysisRepository) DeleteAntennaAnalysis(id string) error {
	query := `DELETE FROM antenna_analyses WHERE id = $1`

	_, err := r.db.Exec(query, id)
	if err != nil {
		r.logger.Errorf("Failed to delete antenna analysis: %v", err)
		return fmt.Errorf("failed to delete antenna analysis: %w", err)
	}

	r.logger.Infof("Deleted antenna analysis with ID: %s", id)
	return nil
}

// InterferenceAnalysisRepository provides database operations for interference analysis
type InterferenceAnalysisRepository struct {
	db     *sql.DB
	logger *logrus.Logger
}

// NewInterferenceAnalysisRepository creates a new interference analysis repository
func NewInterferenceAnalysisRepository(db *sql.DB, logger *logrus.Logger) *InterferenceAnalysisRepository {
	return &InterferenceAnalysisRepository{
		db:     db,
		logger: logger,
	}
}

// CreateInterferenceAnalysis creates a new interference analysis record
func (r *InterferenceAnalysisRepository) CreateInterferenceAnalysis(analysis *InterferenceAnalysis) error {
	analysis.ID = uuid.New().String()
	analysis.CreatedAt = time.Now()
	analysis.UpdatedAt = time.Now()
	analysis.Status = "pending"

	query := `
		INSERT INTO interference_analyses (
			id, user_id, project_id, request_data, result_data, status,
			analysis_type, interference_type, severity, interference_level,
			signal_to_interference_ratio, carrier_to_interference_ratio,
			interference_power, analysis_time, created_at, updated_at,
			completed_at, error
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
			$15, $16, $17, $18
		)
	`

	_, err := r.db.Exec(query,
		analysis.ID, analysis.UserID, analysis.ProjectID, analysis.RequestData,
		analysis.ResultData, analysis.Status, analysis.AnalysisType,
		analysis.InterferenceType, analysis.Severity, analysis.InterferenceLevel,
		analysis.SignalToInterferenceRatio, analysis.CarrierToInterferenceRatio,
		analysis.InterferencePower, analysis.AnalysisTime, analysis.CreatedAt,
		analysis.UpdatedAt, analysis.CompletedAt, analysis.Error,
	)

	if err != nil {
		r.logger.Errorf("Failed to create interference analysis: %v", err)
		return fmt.Errorf("failed to create interference analysis: %w", err)
	}

	r.logger.Infof("Created interference analysis with ID: %s", analysis.ID)
	return nil
}

// GetInterferenceAnalysis retrieves an interference analysis by ID
func (r *InterferenceAnalysisRepository) GetInterferenceAnalysis(id string) (*InterferenceAnalysis, error) {
	query := `
		SELECT id, user_id, project_id, request_data, result_data, status,
			analysis_type, interference_type, severity, interference_level,
			signal_to_interference_ratio, carrier_to_interference_ratio,
			interference_power, analysis_time, created_at, updated_at,
			completed_at, error
		FROM interference_analyses
		WHERE id = $1
	`

	var analysis InterferenceAnalysis
	err := r.db.QueryRow(query, id).Scan(
		&analysis.ID, &analysis.UserID, &analysis.ProjectID, &analysis.RequestData,
		&analysis.ResultData, &analysis.Status, &analysis.AnalysisType,
		&analysis.InterferenceType, &analysis.Severity, &analysis.InterferenceLevel,
		&analysis.SignalToInterferenceRatio, &analysis.CarrierToInterferenceRatio,
		&analysis.InterferencePower, &analysis.AnalysisTime, &analysis.CreatedAt,
		&analysis.UpdatedAt, &analysis.CompletedAt, &analysis.Error,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("interference analysis not found: %s", id)
		}
		r.logger.Errorf("Failed to get interference analysis: %v", err)
		return nil, fmt.Errorf("failed to get interference analysis: %w", err)
	}

	return &analysis, nil
}

// UpdateInterferenceAnalysis updates an interference analysis record
func (r *InterferenceAnalysisRepository) UpdateInterferenceAnalysis(analysis *InterferenceAnalysis) error {
	analysis.UpdatedAt = time.Now()

	query := `
		UPDATE interference_analyses SET
			request_data = $1, result_data = $2, status = $3,
			analysis_type = $4, interference_type = $5, severity = $6,
			interference_level = $7, signal_to_interference_ratio = $8,
			carrier_to_interference_ratio = $9, interference_power = $10,
			analysis_time = $11, updated_at = $12, completed_at = $13, error = $14
		WHERE id = $15
	`

	_, err := r.db.Exec(query,
		analysis.RequestData, analysis.ResultData, analysis.Status,
		analysis.AnalysisType, analysis.InterferenceType, analysis.Severity,
		analysis.InterferenceLevel, analysis.SignalToInterferenceRatio,
		analysis.CarrierToInterferenceRatio, analysis.InterferencePower,
		analysis.AnalysisTime, analysis.UpdatedAt, analysis.CompletedAt, analysis.Error,
		analysis.ID,
	)

	if err != nil {
		r.logger.Errorf("Failed to update interference analysis: %v", err)
		return fmt.Errorf("failed to update interference analysis: %w", err)
	}

	r.logger.Infof("Updated interference analysis with ID: %s", analysis.ID)
	return nil
}

// ListInterferenceAnalyses retrieves interference analyses with pagination
func (r *InterferenceAnalysisRepository) ListInterferenceAnalyses(userID string, limit, offset int) ([]*InterferenceAnalysis, error) {
	query := `
		SELECT id, user_id, project_id, request_data, result_data, status,
			analysis_type, interference_type, severity, interference_level,
			signal_to_interference_ratio, carrier_to_interference_ratio,
			interference_power, analysis_time, created_at, updated_at,
			completed_at, error
		FROM interference_analyses
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := r.db.Query(query, userID, limit, offset)
	if err != nil {
		r.logger.Errorf("Failed to list interference analyses: %v", err)
		return nil, fmt.Errorf("failed to list interference analyses: %w", err)
	}
	defer rows.Close()

	var analyses []*InterferenceAnalysis
	for rows.Next() {
		var analysis InterferenceAnalysis
		err := rows.Scan(
			&analysis.ID, &analysis.UserID, &analysis.ProjectID, &analysis.RequestData,
			&analysis.ResultData, &analysis.Status, &analysis.AnalysisType,
			&analysis.InterferenceType, &analysis.Severity, &analysis.InterferenceLevel,
			&analysis.SignalToInterferenceRatio, &analysis.CarrierToInterferenceRatio,
			&analysis.InterferencePower, &analysis.AnalysisTime, &analysis.CreatedAt,
			&analysis.UpdatedAt, &analysis.CompletedAt, &analysis.Error,
		)
		if err != nil {
			r.logger.Errorf("Failed to scan interference analysis: %v", err)
			continue
		}
		analyses = append(analyses, &analysis)
	}

	return analyses, nil
}

// DeleteInterferenceAnalysis deletes an interference analysis record
func (r *InterferenceAnalysisRepository) DeleteInterferenceAnalysis(id string) error {
	query := `DELETE FROM interference_analyses WHERE id = $1`

	_, err := r.db.Exec(query, id)
	if err != nil {
		r.logger.Errorf("Failed to delete interference analysis: %v", err)
		return fmt.Errorf("failed to delete interference analysis: %w", err)
	}

	r.logger.Infof("Deleted interference analysis with ID: %s", id)
	return nil
}

// SignalProjectRepository provides database operations for signal projects
type SignalProjectRepository struct {
	db     *sql.DB
	logger *logrus.Logger
}

// NewSignalProjectRepository creates a new signal project repository
func NewSignalProjectRepository(db *sql.DB, logger *logrus.Logger) *SignalProjectRepository {
	return &SignalProjectRepository{
		db:     db,
		logger: logger,
	}
}

// CreateSignalProject creates a new signal project
func (r *SignalProjectRepository) CreateSignalProject(project *SignalProject) error {
	project.ID = uuid.New().String()
	project.CreatedAt = time.Now()
	project.UpdatedAt = time.Now()

	query := `
		INSERT INTO signal_projects (
			id, user_id, name, description, status, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7)
	`

	_, err := r.db.Exec(query,
		project.ID, project.UserID, project.Name, project.Description,
		project.Status, project.CreatedAt, project.UpdatedAt,
	)

	if err != nil {
		r.logger.Errorf("Failed to create signal project: %v", err)
		return fmt.Errorf("failed to create signal project: %w", err)
	}

	r.logger.Infof("Created signal project with ID: %s", project.ID)
	return nil
}

// GetSignalProject retrieves a signal project by ID
func (r *SignalProjectRepository) GetSignalProject(id string) (*SignalProject, error) {
	query := `
		SELECT id, user_id, name, description, status, created_at, updated_at
		FROM signal_projects
		WHERE id = $1
	`

	var project SignalProject
	err := r.db.QueryRow(query, id).Scan(
		&project.ID, &project.UserID, &project.Name, &project.Description,
		&project.Status, &project.CreatedAt, &project.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("signal project not found: %s", id)
		}
		r.logger.Errorf("Failed to get signal project: %v", err)
		return nil, fmt.Errorf("failed to get signal project: %w", err)
	}

	return &project, nil
}

// UpdateSignalProject updates a signal project
func (r *SignalProjectRepository) UpdateSignalProject(project *SignalProject) error {
	project.UpdatedAt = time.Now()

	query := `
		UPDATE signal_projects SET
			name = $1, description = $2, status = $3, updated_at = $4
		WHERE id = $5
	`

	_, err := r.db.Exec(query,
		project.Name, project.Description, project.Status, project.UpdatedAt, project.ID,
	)

	if err != nil {
		r.logger.Errorf("Failed to update signal project: %v", err)
		return fmt.Errorf("failed to update signal project: %w", err)
	}

	r.logger.Infof("Updated signal project with ID: %s", project.ID)
	return nil
}

// ListSignalProjects retrieves signal projects with pagination
func (r *SignalProjectRepository) ListSignalProjects(userID string, limit, offset int) ([]*SignalProject, error) {
	query := `
		SELECT id, user_id, name, description, status, created_at, updated_at
		FROM signal_projects
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := r.db.Query(query, userID, limit, offset)
	if err != nil {
		r.logger.Errorf("Failed to list signal projects: %v", err)
		return nil, fmt.Errorf("failed to list signal projects: %w", err)
	}
	defer rows.Close()

	var projects []*SignalProject
	for rows.Next() {
		var project SignalProject
		err := rows.Scan(
			&project.ID, &project.UserID, &project.Name, &project.Description,
			&project.Status, &project.CreatedAt, &project.UpdatedAt,
		)
		if err != nil {
			r.logger.Errorf("Failed to scan signal project: %v", err)
			continue
		}
		projects = append(projects, &project)
	}

	return projects, nil
}

// DeleteSignalProject deletes a signal project
func (r *SignalProjectRepository) DeleteSignalProject(id string) error {
	query := `DELETE FROM signal_projects WHERE id = $1`

	_, err := r.db.Exec(query, id)
	if err != nil {
		r.logger.Errorf("Failed to delete signal project: %v", err)
		return fmt.Errorf("failed to delete signal project: %w", err)
	}

	r.logger.Infof("Deleted signal project with ID: %s", id)
	return nil
}
