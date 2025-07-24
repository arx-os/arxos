package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"go.uber.org/zap"
)

// PersistenceService provides data persistence operations
type PersistenceService struct {
	dbService *DatabaseService
	logger    *zap.Logger
}

// NewPersistenceService creates a new persistence service
func NewPersistenceService(dbService *DatabaseService, logger *zap.Logger) *PersistenceService {
	return &PersistenceService{
		dbService: dbService,
		logger:    logger,
	}
}

// SaveBIMModel saves a BIM model to the database
func (ps *PersistenceService) SaveBIMModel(ctx context.Context, model *BIMModel) error {
	if model.ID == "" {
		return fmt.Errorf("model ID is required")
	}

	now := time.Now()
	if model.CreatedAt.IsZero() {
		model.CreatedAt = now
	}
	model.UpdatedAt = now

	query := `
		INSERT INTO bim_models (
			id, name, description, model_data, model_metadata, 
			created_by, project_id, version, created_at, updated_at, 
			status, tags, properties
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			name = EXCLUDED.name,
			description = EXCLUDED.description,
			model_data = EXCLUDED.model_data,
			model_metadata = EXCLUDED.model_metadata,
			created_by = EXCLUDED.created_by,
			project_id = EXCLUDED.project_id,
			version = EXCLUDED.version,
			updated_at = EXCLUDED.updated_at,
			status = EXCLUDED.status,
			tags = EXCLUDED.tags,
			properties = EXCLUDED.properties
	`

	tagsJSON, _ := json.Marshal(model.Tags)
	propertiesJSON, _ := json.Marshal(model.Properties)

	_, err := ps.dbService.db.ExecContext(ctx, query,
		model.ID, model.Name, model.Description, model.ModelData, model.ModelMetadata,
		model.CreatedBy, model.ProjectID, model.Version, model.CreatedAt, model.UpdatedAt,
		model.Status, tagsJSON, propertiesJSON,
	)

	if err != nil {
		ps.logger.Error("Failed to save BIM model", zap.String("model_id", model.ID), zap.Error(err))
		return fmt.Errorf("failed to save BIM model: %w", err)
	}

	ps.logger.Info("BIM model saved successfully", zap.String("model_id", model.ID))
	return nil
}

// LoadBIMModel loads a BIM model from the database
func (ps *PersistenceService) LoadBIMModel(ctx context.Context, modelID string) (*BIMModel, error) {
	query := `
		SELECT id, name, description, model_data, model_metadata,
			   created_by, project_id, version, created_at, updated_at,
			   status, tags, properties
		FROM bim_models
		WHERE id = ? AND status = 'active'
	`

	var model BIMModel
	var tagsJSON, propertiesJSON []byte

	err := ps.dbService.db.QueryRowContext(ctx, query, modelID).Scan(
		&model.ID, &model.Name, &model.Description, &model.ModelData, &model.ModelMetadata,
		&model.CreatedBy, &model.ProjectID, &model.Version, &model.CreatedAt, &model.UpdatedAt,
		&model.Status, &tagsJSON, &propertiesJSON,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("BIM model not found: %s", modelID)
		}
		ps.logger.Error("Failed to load BIM model", zap.String("model_id", modelID), zap.Error(err))
		return nil, fmt.Errorf("failed to load BIM model: %w", err)
	}

	// Parse JSON fields
	if len(tagsJSON) > 0 {
		json.Unmarshal(tagsJSON, &model.Tags)
	}
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &model.Properties)
	}

	ps.logger.Info("BIM model loaded successfully", zap.String("model_id", modelID))
	return &model, nil
}

// ListBIMModels lists BIM models with optional filtering
func (ps *PersistenceService) ListBIMModels(ctx context.Context, projectID, createdBy string, activeOnly bool) ([]*BIMModel, error) {
	query := `
		SELECT id, name, description, model_data, model_metadata,
			   created_by, project_id, version, created_at, updated_at,
			   status, tags, properties
		FROM bim_models
		WHERE 1=1
	`
	args := []interface{}{}

	if projectID != "" {
		query += " AND project_id = ?"
		args = append(args, projectID)
	}
	if createdBy != "" {
		query += " AND created_by = ?"
		args = append(args, createdBy)
	}
	if activeOnly {
		query += " AND status = 'active'"
	}
	query += " ORDER BY updated_at DESC"

	rows, err := ps.dbService.db.QueryContext(ctx, query, args...)
	if err != nil {
		ps.logger.Error("Failed to list BIM models", zap.Error(err))
		return nil, fmt.Errorf("failed to list BIM models: %w", err)
	}
	defer rows.Close()

	var models []*BIMModel
	for rows.Next() {
		var model BIMModel
		var tagsJSON, propertiesJSON []byte

		err := rows.Scan(
			&model.ID, &model.Name, &model.Description, &model.ModelData, &model.ModelMetadata,
			&model.CreatedBy, &model.ProjectID, &model.Version, &model.CreatedAt, &model.UpdatedAt,
			&model.Status, &tagsJSON, &propertiesJSON,
		)
		if err != nil {
			ps.logger.Error("Failed to scan BIM model row", zap.Error(err))
			continue
		}

		// Parse JSON fields
		if len(tagsJSON) > 0 {
			json.Unmarshal(tagsJSON, &model.Tags)
		}
		if len(propertiesJSON) > 0 {
			json.Unmarshal(propertiesJSON, &model.Properties)
		}

		models = append(models, &model)
	}

	ps.logger.Info("BIM models listed successfully", zap.Int("count", len(models)))
	return models, nil
}

// DeleteBIMModel deletes a BIM model from the database
func (ps *PersistenceService) DeleteBIMModel(ctx context.Context, modelID string) error {
	query := `DELETE FROM bim_models WHERE id = ?`

	result, err := ps.dbService.db.ExecContext(ctx, query, modelID)
	if err != nil {
		ps.logger.Error("Failed to delete BIM model", zap.String("model_id", modelID), zap.Error(err))
		return fmt.Errorf("failed to delete BIM model: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("BIM model not found: %s", modelID)
	}

	ps.logger.Info("BIM model deleted successfully", zap.String("model_id", modelID))
	return nil
}

// SaveSymbol saves a symbol to the database
func (ps *PersistenceService) SaveSymbol(ctx context.Context, symbol *SymbolLibrary) error {
	if symbol.ID == "" {
		return fmt.Errorf("symbol ID is required")
	}

	now := time.Now()
	if symbol.CreatedAt.IsZero() {
		symbol.CreatedAt = now
	}
	symbol.UpdatedAt = now

	query := `
		INSERT INTO symbol_libraries (
			id, name, category, system, symbol_data, metadata,
			created_by, created_at, updated_at, status, version, properties
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			name = EXCLUDED.name,
			category = EXCLUDED.category,
			system = EXCLUDED.system,
			symbol_data = EXCLUDED.symbol_data,
			metadata = EXCLUDED.metadata,
			created_by = EXCLUDED.created_by,
			updated_at = EXCLUDED.updated_at,
			status = EXCLUDED.status,
			version = EXCLUDED.version,
			properties = EXCLUDED.properties
	`

	propertiesJSON, _ := json.Marshal(symbol.Properties)

	_, err := ps.dbService.db.ExecContext(ctx, query,
		symbol.ID, symbol.Name, symbol.Category, symbol.System, symbol.SymbolData, symbol.Metadata,
		symbol.CreatedBy, symbol.CreatedAt, symbol.UpdatedAt, symbol.Status, symbol.Version, propertiesJSON,
	)

	if err != nil {
		ps.logger.Error("Failed to save symbol", zap.String("symbol_id", symbol.ID), zap.Error(err))
		return fmt.Errorf("failed to save symbol: %w", err)
	}

	ps.logger.Info("Symbol saved successfully", zap.String("symbol_id", symbol.ID))
	return nil
}

// LoadSymbol loads a symbol from the database
func (ps *PersistenceService) LoadSymbol(ctx context.Context, symbolID string) (*SymbolLibrary, error) {
	query := `
		SELECT id, name, category, system, symbol_data, metadata,
			   created_by, created_at, updated_at, status, version, properties
		FROM symbol_libraries
		WHERE id = ? AND status = 'active'
	`

	var symbol SymbolLibrary
	var propertiesJSON []byte

	err := ps.dbService.db.QueryRowContext(ctx, query, symbolID).Scan(
		&symbol.ID, &symbol.Name, &symbol.Category, &symbol.System, &symbol.SymbolData, &symbol.Metadata,
		&symbol.CreatedBy, &symbol.CreatedAt, &symbol.UpdatedAt, &symbol.Status, &symbol.Version, &propertiesJSON,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("symbol not found: %s", symbolID)
		}
		ps.logger.Error("Failed to load symbol", zap.String("symbol_id", symbolID), zap.Error(err))
		return nil, fmt.Errorf("failed to load symbol: %w", err)
	}

	// Parse JSON fields
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &symbol.Properties)
	}

	ps.logger.Info("Symbol loaded successfully", zap.String("symbol_id", symbolID))
	return &symbol, nil
}

// ListSymbols lists symbols with optional filtering
func (ps *PersistenceService) ListSymbols(ctx context.Context, system, category string, activeOnly bool) ([]*SymbolLibrary, error) {
	query := `
		SELECT id, name, category, system, symbol_data, metadata,
			   created_by, created_at, updated_at, status, version, properties
		FROM symbol_libraries
		WHERE 1=1
	`
	args := []interface{}{}

	if system != "" {
		query += " AND system = ?"
		args = append(args, system)
	}
	if category != "" {
		query += " AND category = ?"
		args = append(args, category)
	}
	if activeOnly {
		query += " AND status = 'active'"
	}
	query += " ORDER BY name ASC"

	rows, err := ps.dbService.db.QueryContext(ctx, query, args...)
	if err != nil {
		ps.logger.Error("Failed to list symbols", zap.Error(err))
		return nil, fmt.Errorf("failed to list symbols: %w", err)
	}
	defer rows.Close()

	var symbols []*SymbolLibrary
	for rows.Next() {
		var symbol SymbolLibrary
		var propertiesJSON []byte

		err := rows.Scan(
			&symbol.ID, &symbol.Name, &symbol.Category, &symbol.System, &symbol.SymbolData, &symbol.Metadata,
			&symbol.CreatedBy, &symbol.CreatedAt, &symbol.UpdatedAt, &symbol.Status, &symbol.Version, &propertiesJSON,
		)
		if err != nil {
			ps.logger.Error("Failed to scan symbol row", zap.Error(err))
			continue
		}

		// Parse JSON fields
		if len(propertiesJSON) > 0 {
			json.Unmarshal(propertiesJSON, &symbol.Properties)
		}

		symbols = append(symbols, &symbol)
	}

	ps.logger.Info("Symbols listed successfully", zap.Int("count", len(symbols)))
	return symbols, nil
}

// DeleteSymbol deletes a symbol from the database
func (ps *PersistenceService) DeleteSymbol(ctx context.Context, symbolID string) error {
	query := `DELETE FROM symbol_libraries WHERE id = ?`

	result, err := ps.dbService.db.ExecContext(ctx, query, symbolID)
	if err != nil {
		ps.logger.Error("Failed to delete symbol", zap.String("symbol_id", symbolID), zap.Error(err))
		return fmt.Errorf("failed to delete symbol: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("symbol not found: %s", symbolID)
	}

	ps.logger.Info("Symbol deleted successfully", zap.String("symbol_id", symbolID))
	return nil
}

// SaveUser saves a user to the database
func (ps *PersistenceService) SaveUser(ctx context.Context, user *User) error {
	if user.ID == "" {
		return fmt.Errorf("user ID is required")
	}

	now := time.Now()
	if user.CreatedAt.IsZero() {
		user.CreatedAt = now
	}
	user.UpdatedAt = now

	query := `
		INSERT INTO users (
			id, username, email, password_hash, first_name, last_name,
			role, status, created_at, updated_at, last_login_at, properties
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(id) DO UPDATE SET
			username = EXCLUDED.username,
			email = EXCLUDED.email,
			password_hash = EXCLUDED.password_hash,
			first_name = EXCLUDED.first_name,
			last_name = EXCLUDED.last_name,
			role = EXCLUDED.role,
			status = EXCLUDED.status,
			updated_at = EXCLUDED.updated_at,
			last_login_at = EXCLUDED.last_login_at,
			properties = EXCLUDED.properties
	`

	propertiesJSON, _ := json.Marshal(user.Properties)

	_, err := ps.dbService.db.ExecContext(ctx, query,
		user.ID, user.Username, user.Email, user.PasswordHash, user.FirstName, user.LastName,
		user.Role, user.Status, user.CreatedAt, user.UpdatedAt, user.LastLoginAt, propertiesJSON,
	)

	if err != nil {
		ps.logger.Error("Failed to save user", zap.String("user_id", user.ID), zap.Error(err))
		return fmt.Errorf("failed to save user: %w", err)
	}

	ps.logger.Info("User saved successfully", zap.String("user_id", user.ID))
	return nil
}

// LoadUser loads a user from the database
func (ps *PersistenceService) LoadUser(ctx context.Context, userID string) (*User, error) {
	query := `
		SELECT id, username, email, password_hash, first_name, last_name,
			   role, status, created_at, updated_at, last_login_at, properties
		FROM users
		WHERE id = ?
	`

	var user User
	var propertiesJSON []byte

	err := ps.dbService.db.QueryRowContext(ctx, query, userID).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.FirstName, &user.LastName,
		&user.Role, &user.Status, &user.CreatedAt, &user.UpdatedAt, &user.LastLoginAt, &propertiesJSON,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found: %s", userID)
		}
		ps.logger.Error("Failed to load user", zap.String("user_id", userID), zap.Error(err))
		return nil, fmt.Errorf("failed to load user: %w", err)
	}

	// Parse JSON fields
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &user.Properties)
	}

	ps.logger.Info("User loaded successfully", zap.String("user_id", userID))
	return &user, nil
}

// LoadUserByUsername loads a user by username
func (ps *PersistenceService) LoadUserByUsername(ctx context.Context, username string) (*User, error) {
	query := `
		SELECT id, username, email, password_hash, first_name, last_name,
			   role, status, created_at, updated_at, last_login_at, properties
		FROM users
		WHERE username = ?
	`

	var user User
	var propertiesJSON []byte

	err := ps.dbService.db.QueryRowContext(ctx, query, username).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.FirstName, &user.LastName,
		&user.Role, &user.Status, &user.CreatedAt, &user.UpdatedAt, &user.LastLoginAt, &propertiesJSON,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found: %s", username)
		}
		ps.logger.Error("Failed to load user by username", zap.String("username", username), zap.Error(err))
		return nil, fmt.Errorf("failed to load user by username: %w", err)
	}

	// Parse JSON fields
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &user.Properties)
	}

	ps.logger.Info("User loaded by username successfully", zap.String("username", username))
	return &user, nil
}

// LoadUserByEmail loads a user by email
func (ps *PersistenceService) LoadUserByEmail(ctx context.Context, email string) (*User, error) {
	query := `
		SELECT id, username, email, password_hash, first_name, last_name,
			   role, status, created_at, updated_at, last_login_at, properties
		FROM users
		WHERE email = ?
	`

	var user User
	var propertiesJSON []byte

	err := ps.dbService.db.QueryRowContext(ctx, query, email).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.FirstName, &user.LastName,
		&user.Role, &user.Status, &user.CreatedAt, &user.UpdatedAt, &user.LastLoginAt, &propertiesJSON,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found: %s", email)
		}
		ps.logger.Error("Failed to load user by email", zap.String("email", email), zap.Error(err))
		return nil, fmt.Errorf("failed to load user by email: %w", err)
	}

	// Parse JSON fields
	if len(propertiesJSON) > 0 {
		json.Unmarshal(propertiesJSON, &user.Properties)
	}

	ps.logger.Info("User loaded by email successfully", zap.String("email", email))
	return &user, nil
}

// ListUsers lists all users
func (ps *PersistenceService) ListUsers(ctx context.Context) ([]*User, error) {
	query := `
		SELECT id, username, email, password_hash, first_name, last_name,
			   role, status, created_at, updated_at, last_login_at, properties
		FROM users
		ORDER BY username ASC
	`

	rows, err := ps.dbService.db.QueryContext(ctx, query)
	if err != nil {
		ps.logger.Error("Failed to list users", zap.Error(err))
		return nil, fmt.Errorf("failed to list users: %w", err)
	}
	defer rows.Close()

	var users []*User
	for rows.Next() {
		var user User
		var propertiesJSON []byte

		err := rows.Scan(
			&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.FirstName, &user.LastName,
			&user.Role, &user.Status, &user.CreatedAt, &user.UpdatedAt, &user.LastLoginAt, &propertiesJSON,
		)
		if err != nil {
			ps.logger.Error("Failed to scan user row", zap.Error(err))
			continue
		}

		// Parse JSON fields
		if len(propertiesJSON) > 0 {
			json.Unmarshal(propertiesJSON, &user.Properties)
		}

		users = append(users, &user)
	}

	ps.logger.Info("Users listed successfully", zap.Int("count", len(users)))
	return users, nil
}

// DeleteUser deletes a user from the database
func (ps *PersistenceService) DeleteUser(ctx context.Context, userID string) error {
	query := `DELETE FROM users WHERE id = ?`

	result, err := ps.dbService.db.ExecContext(ctx, query, userID)
	if err != nil {
		ps.logger.Error("Failed to delete user", zap.String("user_id", userID), zap.Error(err))
		return fmt.Errorf("failed to delete user: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("user not found: %s", userID)
	}

	ps.logger.Info("User deleted successfully", zap.String("user_id", userID))
	return nil
}
