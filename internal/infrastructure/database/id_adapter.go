package database

import (
	"context"
	"database/sql/driver"
	"fmt"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/jmoiron/sqlx"
)

// IDAdapter provides database operations that handle both UUID and legacy ID formats
// This enables gradual migration while maintaining backward compatibility
type IDAdapter struct {
	db     *sqlx.DB
	logger domain.Logger
}

// NewIDAdapter creates a new ID adapter
func NewIDAdapter(db *sqlx.DB, logger domain.Logger) *IDAdapter {
	return &IDAdapter{
		db:     db,
		logger: logger,
	}
}

// QueryRow executes a query that returns a single row, handling both ID formats
func (a *IDAdapter) QueryRow(ctx context.Context, query string, args ...interface{}) *sqlx.Row {
	// Convert args to handle both ID formats
	convertedArgs := a.convertArgs(args)
	return a.db.QueryRowxContext(ctx, query, convertedArgs...)
}

// Query executes a query that returns multiple rows, handling both ID formats
func (a *IDAdapter) Query(ctx context.Context, query string, args ...interface{}) (*sqlx.Rows, error) {
	// Convert args to handle both ID formats
	convertedArgs := a.convertArgs(args)
	return a.db.QueryxContext(ctx, query, convertedArgs...)
}

// Exec executes a query without returning rows, handling both ID formats
func (a *IDAdapter) Exec(ctx context.Context, query string, args ...interface{}) (driver.Result, error) {
	// Convert args to handle both ID formats
	convertedArgs := a.convertArgs(args)
	return a.db.ExecContext(ctx, query, convertedArgs...)
}

// Get executes a query and scans the result into a struct, handling both ID formats
func (a *IDAdapter) Get(ctx context.Context, dest interface{}, query string, args ...interface{}) error {
	// Convert args to handle both ID formats
	convertedArgs := a.convertArgs(args)
	return a.db.GetContext(ctx, dest, query, convertedArgs...)
}

// Select executes a query and scans the results into a slice, handling both ID formats
func (a *IDAdapter) Select(ctx context.Context, dest interface{}, query string, args ...interface{}) error {
	// Convert args to handle both ID formats
	convertedArgs := a.convertArgs(args)
	return a.db.SelectContext(ctx, dest, query, convertedArgs...)
}

// NamedQuery executes a named query, handling both ID formats
func (a *IDAdapter) NamedQuery(ctx context.Context, query string, arg interface{}) (*sqlx.Rows, error) {
	// Convert named args to handle both ID formats
	convertedArg := a.convertNamedArgs(arg)
	return a.db.NamedQueryContext(ctx, query, convertedArg)
}

// NamedExec executes a named query without returning rows, handling both ID formats
func (a *IDAdapter) NamedExec(ctx context.Context, query string, arg interface{}) (driver.Result, error) {
	// Convert named args to handle both ID formats
	convertedArg := a.convertNamedArgs(arg)
	return a.db.NamedExecContext(ctx, query, convertedArg)
}

// convertArgs converts interface{} arguments to handle both ID formats
func (a *IDAdapter) convertArgs(args []interface{}) []interface{} {
	converted := make([]interface{}, len(args))
	for i, arg := range args {
		converted[i] = a.convertArg(arg)
	}
	return converted
}

// convertArg converts a single argument to handle both ID formats
func (a *IDAdapter) convertArg(arg interface{}) interface{} {
	switch v := arg.(type) {
	case types.ID:
		// For ID types, use the primary identifier (UUID if available, otherwise legacy)
		return v.String()
	case *types.ID:
		if v != nil {
			return v.String()
		}
		return nil
	default:
		return arg
	}
}

// convertNamedArgs converts named arguments to handle both ID formats
func (a *IDAdapter) convertNamedArgs(arg interface{}) interface{} {
	switch v := arg.(type) {
	case map[string]interface{}:
		converted := make(map[string]interface{})
		for key, value := range v {
			converted[key] = a.convertArg(value)
		}
		return converted
	default:
		// For structs, we need to handle this differently
		// This is a simplified approach - in practice, you might want to use reflection
		return arg
	}
}

// BuildQuery builds a query that can handle both UUID and legacy ID lookups
func (a *IDAdapter) BuildQuery(baseQuery, idColumn string, id types.ID) (string, []interface{}) {
	if id.IsEmpty() {
		return baseQuery + " WHERE 1=0", []interface{}{} // Return empty result for empty ID
	}

	var whereClause string
	var args []interface{}

	if id.UUID != "" && id.Legacy != "" {
		// Both UUID and legacy available - check both columns
		whereClause = fmt.Sprintf(" WHERE (%s = $1 OR %s = $2)", idColumn, idColumn)
		args = []interface{}{id.UUID, id.Legacy}
	} else if id.UUID != "" {
		// Only UUID available
		whereClause = fmt.Sprintf(" WHERE %s = $1", idColumn)
		args = []interface{}{id.UUID}
	} else {
		// Only legacy available
		whereClause = fmt.Sprintf(" WHERE %s = $1", idColumn)
		args = []interface{}{id.Legacy}
	}

	return baseQuery + whereClause, args
}

// BuildInsertQuery builds an insert query that handles both UUID and legacy ID columns
func (a *IDAdapter) BuildInsertQuery(table string, id types.ID, data map[string]interface{}) (string, []interface{}) {
	columns := make([]string, 0, len(data)+2) // +2 for id and uuid_id
	placeholders := make([]string, 0, len(data)+2)
	args := make([]interface{}, 0, len(data)+2)

	// Add ID columns
	if id.Legacy != "" {
		columns = append(columns, "id")
		placeholders = append(placeholders, fmt.Sprintf("$%d", len(args)+1))
		args = append(args, id.Legacy)
	}

	if id.UUID != "" {
		columns = append(columns, "uuid_id")
		placeholders = append(placeholders, fmt.Sprintf("$%d", len(args)+1))
		args = append(args, id.UUID)
	}

	// Add data columns
	for column, value := range data {
		columns = append(columns, column)
		placeholders = append(placeholders, fmt.Sprintf("$%d", len(args)+1))
		args = append(args, value)
	}

	query := fmt.Sprintf(
		"INSERT INTO %s (%s) VALUES (%s)",
		table,
		fmt.Sprintf("%v", columns),
		fmt.Sprintf("%v", placeholders),
	)

	return query, args
}

// BuildUpdateQuery builds an update query that handles both UUID and legacy ID columns
func (a *IDAdapter) BuildUpdateQuery(table string, id types.ID, data map[string]interface{}) (string, []interface{}) {
	setClauses := make([]string, 0, len(data))
	args := make([]interface{}, 0, len(data))

	// Add data columns
	for column, value := range data {
		setClauses = append(setClauses, fmt.Sprintf("%s = $%d", column, len(args)+1))
		args = append(args, value)
	}

	// Build WHERE clause
	var whereClause string
	if id.UUID != "" && id.Legacy != "" {
		// Both UUID and legacy available - check both columns
		whereClause = fmt.Sprintf(" WHERE (uuid_id = $%d OR id = $%d)", len(args)+1, len(args)+2)
		args = append(args, id.UUID, id.Legacy)
	} else if id.UUID != "" {
		// Only UUID available
		whereClause = fmt.Sprintf(" WHERE uuid_id = $%d", len(args)+1)
		args = append(args, id.UUID)
	} else {
		// Only legacy available
		whereClause = fmt.Sprintf(" WHERE id = $%d", len(args)+1)
		args = append(args, id.Legacy)
	}

	query := fmt.Sprintf(
		"UPDATE %s SET %s%s",
		table,
		fmt.Sprintf("%v", setClauses),
		whereClause,
	)

	return query, args
}

// BuildDeleteQuery builds a delete query that handles both UUID and legacy ID columns
func (a *IDAdapter) BuildDeleteQuery(table string, id types.ID) (string, []interface{}) {
	var whereClause string
	var args []interface{}

	if id.UUID != "" && id.Legacy != "" {
		// Both UUID and legacy available - check both columns
		whereClause = fmt.Sprintf(" WHERE (uuid_id = $1 OR id = $2)")
		args = []interface{}{id.UUID, id.Legacy}
	} else if id.UUID != "" {
		// Only UUID available
		whereClause = fmt.Sprintf(" WHERE uuid_id = $1")
		args = []interface{}{id.UUID}
	} else {
		// Only legacy available
		whereClause = fmt.Sprintf(" WHERE id = $1")
		args = []interface{}{id.Legacy}
	}

	query := fmt.Sprintf("DELETE FROM %s%s", table, whereClause)
	return query, args
}
