package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// --- User Management Methods ---

// GetUser retrieves a user by ID
func (p *PostGISDB) GetUser(ctx context.Context, id string) (*models.User, error) {
	query := `
		SELECT
			id, email, username, password_hash, full_name,
			role, is_active, email_verified, phone, avatar_url,
			preferences, metadata, last_login, failed_login_attempts,
			locked_until, created_at, updated_at
		FROM users
		WHERE id = $1
	`

	var user models.User
	var preferences, metadata sql.NullString
	var lastLogin, lockedUntil sql.NullTime
	var phone, avatarURL sql.NullString

	err := p.db.QueryRowContext(ctx, query, id).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash, &user.FullName,
		&user.Role, &user.IsActive, &user.EmailVerified, &phone, &avatarURL,
		&preferences, &metadata, &lastLogin, &user.FailedLoginAttempts,
		&lockedUntil, &user.CreatedAt, &user.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New(errors.CodeNotFound,
			fmt.Sprintf("user not found: %s", id))
	}

	if err != nil {
		return nil, errors.Wrap(err, errors.CodeDatabase, "get user")
	}

	// Set nullable fields
	if phone.Valid {
		user.Phone = phone.String
	}
	if avatarURL.Valid {
		user.AvatarURL = avatarURL.String
	}
	if lastLogin.Valid {
		user.LastLogin = &lastLogin.Time
	}
	if lockedUntil.Valid {
		user.LockedUntil = &lockedUntil.Time
	}

	return &user, nil
}

// GetUserByEmail retrieves a user by email
func (p *PostGISDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	query := `
		SELECT
			id, email, username, password_hash, full_name,
			role, is_active, email_verified, phone, avatar_url,
			preferences, metadata, last_login, failed_login_attempts,
			locked_until, created_at, updated_at
		FROM users
		WHERE email = $1
	`

	var user models.User
	var preferences, metadata sql.NullString
	var lastLogin, lockedUntil sql.NullTime
	var phone, avatarURL sql.NullString

	err := p.db.QueryRowContext(ctx, query, email).Scan(
		&user.ID, &user.Email, &user.Username, &user.PasswordHash, &user.FullName,
		&user.Role, &user.IsActive, &user.EmailVerified, &phone, &avatarURL,
		&preferences, &metadata, &lastLogin, &user.FailedLoginAttempts,
		&lockedUntil, &user.CreatedAt, &user.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New(errors.CodeNotFound,
			fmt.Sprintf("user not found: %s", email))
	}

	if err != nil {
		return nil, errors.Wrap(err, errors.CodeDatabase, "get user by email")
	}

	// Set nullable fields
	if phone.Valid {
		user.Phone = phone.String
	}
	if avatarURL.Valid {
		user.AvatarURL = avatarURL.String
	}
	if lastLogin.Valid {
		user.LastLogin = &lastLogin.Time
	}
	if lockedUntil.Valid {
		user.LockedUntil = &lockedUntil.Time
	}

	return &user, nil
}

// CreateUserWithPassword creates a new user with a plain text password
func (p *PostGISDB) CreateUserWithPassword(ctx context.Context, user *models.User, password string) error {
	// Generate UUID if not provided
	if user.ID == "" {
		user.ID = uuid.New().String()
	}

	// Hash password
	if password != "" {
		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
		if err != nil {
			return errors.Wrap(err, errors.CodeDatabase, "hash password")
		}
		user.PasswordHash = string(hashedPassword)
	} else {
		return fmt.Errorf("password is required")
	}

	return p.CreateUser(ctx, user)
}

// CreateUser creates a new user
func (p *PostGISDB) CreateUser(ctx context.Context, user *models.User) error {
	// Generate UUID if not provided
	if user.ID == "" {
		user.ID = uuid.New().String()
	}

	// Password should already be hashed in user.PasswordHash
	if user.PasswordHash == "" {
		return fmt.Errorf("password hash is required")
	}

	query := `
		INSERT INTO users (
			id, email, username, password_hash, full_name,
			role, is_active, email_verified, phone, avatar_url,
			preferences, metadata
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
		)
		RETURNING created_at, updated_at
	`

	err := p.db.QueryRowContext(ctx, query,
		user.ID, user.Email, user.Username, user.PasswordHash, user.FullName,
		user.Role, user.IsActive, user.EmailVerified,
		sql.NullString{String: user.Phone, Valid: user.Phone != ""},
		sql.NullString{String: user.AvatarURL, Valid: user.AvatarURL != ""},
		"{}",  // preferences
		"{}",  // metadata
	).Scan(&user.CreatedAt, &user.UpdatedAt)

	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "create user")
	}

	logger.Info("Created user: %s (%s)", user.Username, user.Email)
	return nil
}

// UpdateUser updates a user
func (p *PostGISDB) UpdateUser(ctx context.Context, user *models.User) error {
	// Password should be updated separately via ChangePassword method

	query := `
		UPDATE users SET
			email = $2,
			username = $3,
			password_hash = COALESCE(NULLIF($4, ''), password_hash),
			full_name = $5,
			role = $6,
			is_active = $7,
			email_verified = $8,
			phone = $9,
			avatar_url = $10,
			updated_at = NOW()
		WHERE id = $1
		RETURNING updated_at
	`

	err := p.db.QueryRowContext(ctx, query,
		user.ID, user.Email, user.Username, user.PasswordHash, user.FullName,
		user.Role, user.IsActive, user.EmailVerified,
		sql.NullString{String: user.Phone, Valid: user.Phone != ""},
		sql.NullString{String: user.AvatarURL, Valid: user.AvatarURL != ""},
	).Scan(&user.UpdatedAt)

	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "update user")
	}

	logger.Info("Updated user: %s", user.ID)
	return nil
}

// DeleteUser deletes a user
func (p *PostGISDB) DeleteUser(ctx context.Context, id string) error {
	query := `DELETE FROM users WHERE id = $1`

	result, err := p.db.ExecContext(ctx, query, id)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "delete user")
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "check delete result")
	}

	if rowsAffected == 0 {
		return errors.New(errors.CodeNotFound,
			fmt.Sprintf("user not found: %s", id))
	}

	logger.Info("Deleted user: %s", id)
	return nil
}

// UpdateUserLoginInfo updates login information after successful authentication
func (p *PostGISDB) UpdateUserLoginInfo(ctx context.Context, userID string, success bool) error {
	if success {
		query := `
			UPDATE users SET
				last_login = NOW(),
				failed_login_attempts = 0,
				locked_until = NULL
			WHERE id = $1
		`
		_, err := p.db.ExecContext(ctx, query, userID)
		return err
	}

	// Failed login - increment attempts and potentially lock account
	query := `
		UPDATE users SET
			failed_login_attempts = failed_login_attempts + 1,
			locked_until = CASE
				WHEN failed_login_attempts >= 4 THEN NOW() + INTERVAL '15 minutes'
				ELSE locked_until
			END
		WHERE id = $1
	`

	_, err := p.db.ExecContext(ctx, query, userID)
	return err
}

// --- Session Management Methods ---

// CreateSession creates a new user session
func (p *PostGISDB) CreateSession(ctx context.Context, session *models.UserSession) error {
	if session.ID == "" {
		session.ID = uuid.New().String()
	}

	query := `
		INSERT INTO user_sessions (
			id, user_id, token, refresh_token, ip_address,
			user_agent, device_info, is_active, expires_at,
			refresh_expires_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10
		)
		RETURNING created_at
	`

	err := p.db.QueryRowContext(ctx, query,
		session.ID, session.UserID, session.Token, session.RefreshToken,
		sql.NullString{String: session.IPAddress, Valid: session.IPAddress != ""},
		sql.NullString{String: session.UserAgent, Valid: session.UserAgent != ""},
		"{}",  // device_info
		true,  // is_active
		session.ExpiresAt, session.RefreshExpiresAt,
	).Scan(&session.CreatedAt)

	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "create session")
	}

	logger.Debug("Created session for user: %s", session.UserID)
	return nil
}

// GetSession retrieves a session by token
func (p *PostGISDB) GetSession(ctx context.Context, token string) (*models.UserSession, error) {
	query := `
		SELECT
			id, user_id, token, refresh_token, ip_address,
			user_agent, is_active, expires_at, refresh_expires_at,
			last_activity, created_at
		FROM user_sessions
		WHERE token = $1 AND is_active = true AND expires_at > NOW()
	`

	var session models.UserSession
	var ipAddress, userAgent sql.NullString
	var lastActivity sql.NullTime

	err := p.db.QueryRowContext(ctx, query, token).Scan(
		&session.ID, &session.UserID, &session.Token, &session.RefreshToken,
		&ipAddress, &userAgent, &session.IsActive, &session.ExpiresAt,
		&session.RefreshExpiresAt, &lastActivity, &session.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New(errors.CodeNotFound,
			"session not found or expired")
	}

	if err != nil {
		return nil, errors.Wrap(err, errors.CodeDatabase, "get session")
	}

	// Set nullable fields
	if ipAddress.Valid {
		session.IPAddress = ipAddress.String
	}
	if userAgent.Valid {
		session.UserAgent = userAgent.String
	}
	if lastActivity.Valid {
		session.LastActivity = lastActivity.Time
	}

	// Update last activity
	go p.updateSessionActivity(context.Background(), session.ID)

	return &session, nil
}

// GetSessionByRefreshToken retrieves a session by refresh token
func (p *PostGISDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error) {
	query := `
		SELECT
			id, user_id, token, refresh_token, ip_address,
			user_agent, is_active, expires_at, refresh_expires_at,
			last_activity, created_at
		FROM user_sessions
		WHERE refresh_token = $1 AND is_active = true AND refresh_expires_at > NOW()
	`

	var session models.UserSession
	var ipAddress, userAgent sql.NullString
	var lastActivity sql.NullTime

	err := p.db.QueryRowContext(ctx, query, refreshToken).Scan(
		&session.ID, &session.UserID, &session.Token, &session.RefreshToken,
		&ipAddress, &userAgent, &session.IsActive, &session.ExpiresAt,
		&session.RefreshExpiresAt, &lastActivity, &session.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New(errors.CodeNotFound,
			"session not found or expired")
	}

	if err != nil {
		return nil, errors.Wrap(err, errors.CodeDatabase, "get session by refresh token")
	}

	// Set nullable fields
	if ipAddress.Valid {
		session.IPAddress = ipAddress.String
	}
	if userAgent.Valid {
		session.UserAgent = userAgent.String
	}
	if lastActivity.Valid {
		session.LastActivity = lastActivity.Time
	}

	return &session, nil
}

// UpdateSession updates a session (typically for refresh)
func (p *PostGISDB) UpdateSession(ctx context.Context, session *models.UserSession) error {
	query := `
		UPDATE user_sessions SET
			token = $2,
			expires_at = $3,
			last_activity = NOW()
		WHERE id = $1
	`

	_, err := p.db.ExecContext(ctx, query,
		session.ID, session.Token, session.ExpiresAt)

	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "update session")
	}

	return nil
}

// DeleteSession deletes a session (logout)
func (p *PostGISDB) DeleteSession(ctx context.Context, id string) error {
	query := `
		UPDATE user_sessions SET
			is_active = false
		WHERE id = $1
	`

	_, err := p.db.ExecContext(ctx, query, id)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "delete session")
	}

	logger.Debug("Deactivated session: %s", id)
	return nil
}

// DeleteExpiredSessions removes all expired sessions
func (p *PostGISDB) DeleteExpiredSessions(ctx context.Context) error {
	query := `
		DELETE FROM user_sessions
		WHERE expires_at < NOW() OR is_active = false
	`

	result, err := p.db.ExecContext(ctx, query)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "delete expired sessions")
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected > 0 {
		logger.Info("Deleted %d expired sessions", rowsAffected)
	}

	return nil
}

// GetUserSessions gets all sessions for a user
func (p *PostGISDB) GetUserSessions(ctx context.Context, userID string) ([]*models.UserSession, error) {
	query := `
		SELECT id, user_id, token, refresh_token, ip_address, user_agent,
			   device_info, is_active, expires_at, refresh_expires_at,
			   last_activity, created_at
		FROM user_sessions
		WHERE user_id = $1
		ORDER BY created_at DESC
	`

	rows, err := p.db.QueryContext(ctx, query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to query user sessions: %w", err)
	}
	defer rows.Close()

	var sessions []*models.UserSession

	for rows.Next() {
		var session models.UserSession
		var ipAddress, userAgent sql.NullString
		var deviceInfo json.RawMessage

		err := rows.Scan(
			&session.ID, &session.UserID, &session.Token, &session.RefreshToken,
			&ipAddress, &userAgent, &deviceInfo, &session.IsActive,
			&session.ExpiresAt, &session.RefreshExpiresAt,
			&session.LastActivity, &session.CreatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan session: %w", err)
		}

		// Handle nullable fields
		session.IPAddress = ipAddress.String
		session.UserAgent = userAgent.String

		// Parse device info
		if deviceInfo != nil {
			if err := json.Unmarshal(deviceInfo, &session.DeviceInfo); err != nil {
				logger.Error("Failed to parse device info: %v", err)
			}
		}

		sessions = append(sessions, &session)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating sessions: %w", err)
	}

	return sessions, nil
}

// DeleteUserSessions deletes all sessions for a user
func (p *PostGISDB) DeleteUserSessions(ctx context.Context, userID string) error {
	query := `
		UPDATE user_sessions SET
			is_active = false
		WHERE user_id = $1
	`

	_, err := p.db.ExecContext(ctx, query, userID)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "delete user sessions")
	}

	logger.Info("Deactivated all sessions for user: %s", userID)
	return nil
}

// updateSessionActivity updates the last activity timestamp
func (p *PostGISDB) updateSessionActivity(ctx context.Context, sessionID string) {
	query := `
		UPDATE user_sessions SET
			last_activity = NOW()
		WHERE id = $1
	`

	_, err := p.db.ExecContext(ctx, query, sessionID)
	if err != nil {
		logger.Warn("Failed to update session activity: %v", err)
	}
}

// --- Password Reset Methods ---

// CreatePasswordResetToken creates a new password reset token
func (p *PostGISDB) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error {
	if token.ID == "" {
		token.ID = uuid.New().String()
	}

	// Set expiry to 1 hour from now if not set
	if token.ExpiresAt.IsZero() {
		token.ExpiresAt = time.Now().Add(1 * time.Hour)
	}

	query := `
		INSERT INTO password_reset_tokens (
			id, user_id, token, expires_at
		) VALUES (
			$1, $2, $3, $4
		)
		RETURNING created_at
	`

	err := p.db.QueryRowContext(ctx, query,
		token.ID, token.UserID, token.Token, token.ExpiresAt,
	).Scan(&token.CreatedAt)

	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "create password reset token")
	}

	logger.Info("Created password reset token for user: %s", token.UserID)
	return nil
}

// GetPasswordResetToken retrieves a password reset token
func (p *PostGISDB) GetPasswordResetToken(ctx context.Context, tokenStr string) (*models.PasswordResetToken, error) {
	query := `
		SELECT
			id, user_id, token, expires_at, used_at, created_at
		FROM password_reset_tokens
		WHERE token = $1 AND expires_at > NOW() AND used_at IS NULL
	`

	var token models.PasswordResetToken
	var usedAt sql.NullTime

	err := p.db.QueryRowContext(ctx, query, tokenStr).Scan(
		&token.ID, &token.UserID, &token.Token,
		&token.ExpiresAt, &usedAt, &token.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New(errors.CodeNotFound,
			"token not found or expired")
	}

	if err != nil {
		return nil, errors.Wrap(err, errors.CodeDatabase, "get password reset token")
	}

	if usedAt.Valid {
		token.UsedAt = &usedAt.Time
	}

	return &token, nil
}

// MarkPasswordResetTokenUsed marks a password reset token as used
func (p *PostGISDB) MarkPasswordResetTokenUsed(ctx context.Context, tokenStr string) error {
	query := `
		UPDATE password_reset_tokens SET
			used_at = NOW()
		WHERE token = $1 AND used_at IS NULL
	`

	result, err := p.db.ExecContext(ctx, query, tokenStr)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "mark token used")
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return errors.New(errors.CodeNotFound,
			"token not found or already used")
	}

	return nil
}

// DeleteExpiredPasswordResetTokens removes expired tokens
func (p *PostGISDB) DeleteExpiredPasswordResetTokens(ctx context.Context) error {
	query := `
		DELETE FROM password_reset_tokens
		WHERE expires_at < NOW() OR used_at IS NOT NULL
	`

	result, err := p.db.ExecContext(ctx, query)
	if err != nil {
		return errors.Wrap(err, errors.CodeDatabase, "delete expired tokens")
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected > 0 {
		logger.Info("Deleted %d expired password reset tokens", rowsAffected)
	}

	return nil
}