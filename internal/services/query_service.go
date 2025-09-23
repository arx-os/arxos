package services

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/database"
)

// QueryOptions defines options for the query command
type QueryOptions struct {
	Building   string // Building ID filter
	Status     string
	Type       string
	Floor      int
	System     string   // System filter
	Room       string   // Room filter
	SQL        string   // Raw SQL query
	Output     string   // Output format
	Limit      int      // Max results
	Offset     int      // Result offset
	Count      bool     // Count only
	Fields     []string // Fields to display
	Spatial    string
	Format     string
	OutputFile string

	// Spatial query parameters
	Near     string  // Coordinates for proximity search (x,y,z)
	Radius   float64 // Search radius in meters
	Within   string  // Bounding box (minX,minY,minZ,maxX,maxY,maxZ)
	Contains string  // Point to check containment (x,y,z)
}

// QueryResults contains the results of a query
type QueryResults struct {
	Count   int                      `json:"count"`
	Results []map[string]interface{} `json:"results"`
	Fields  []string                 `json:"fields"`
	Query   string                   `json:"query"`
}

// QueryService handles database queries
type QueryService struct {
	db database.DB
}

// NewQueryService creates a new query service
func NewQueryService(db database.DB) *QueryService {
	return &QueryService{db: db}
}

// ExecuteQuery runs a query with the given options
func (s *QueryService) ExecuteQuery(ctx context.Context, opts QueryOptions) (*QueryResults, error) {
	// Build query based on options
	query, args, err := s.buildQuery(opts)
	if err != nil {
		return nil, fmt.Errorf("failed to build query: %w", err)
	}

	// Execute query
	rows, err := s.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to execute query: %w", err)
	}
	defer rows.Close()

	// Get column names
	columns, err := rows.Columns()
	if err != nil {
		return nil, fmt.Errorf("failed to get columns: %w", err)
	}

	// Build results
	var results []map[string]interface{}
	count := 0

	for rows.Next() {
		// Create slice of interface{} to hold values
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		// Scan row
		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}

		// Create result map
		result := make(map[string]interface{})
		for i, col := range columns {
			result[col] = values[i]
		}

		results = append(results, result)
		count++

		// Apply limit
		if opts.Limit > 0 && count >= opts.Limit {
			break
		}
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("row iteration error: %w", err)
	}

	return &QueryResults{
		Count:   count,
		Results: results,
		Fields:  columns,
		Query:   query,
	}, nil
}

func (s *QueryService) buildQuery(opts QueryOptions) (string, []interface{}, error) {
	var query strings.Builder
	var args []interface{}
	argIndex := 1

	// Start with base query
	if opts.Count {
		query.WriteString("SELECT COUNT(*) as count FROM equipment e")
	} else {
		query.WriteString("SELECT e.* FROM equipment e")
	}

	// Add joins if needed
	if opts.Building != "" {
		query.WriteString(" JOIN floor_plans fp ON e.floor_plan_id = fp.id")
	}

	// Add WHERE clause
	var conditions []string

	if opts.Building != "" {
		conditions = append(conditions, fmt.Sprintf("fp.id = $%d", argIndex))
		args = append(args, opts.Building)
		argIndex++
	}

	if opts.Status != "" {
		conditions = append(conditions, fmt.Sprintf("e.status = $%d", argIndex))
		args = append(args, opts.Status)
		argIndex++
	}

	if opts.Type != "" {
		conditions = append(conditions, fmt.Sprintf("e.type = $%d", argIndex))
		args = append(args, opts.Type)
		argIndex++
	}

	if opts.System != "" {
		conditions = append(conditions, fmt.Sprintf("e.system = $%d", argIndex))
		args = append(args, opts.System)
		argIndex++
	}

	if opts.Room != "" {
		conditions = append(conditions, fmt.Sprintf("e.room_id = $%d", argIndex))
		args = append(args, opts.Room)
		argIndex++
	}

	// Add spatial conditions
	if opts.Near != "" {
		// Parse coordinates
		coords := strings.Split(opts.Near, ",")
		if len(coords) >= 2 {
			conditions = append(conditions, fmt.Sprintf("ST_DWithin(e.location, ST_Point($%d, $%d), $%d)", argIndex, argIndex+1, argIndex+2))
			args = append(args, coords[0], coords[1], opts.Radius)
			argIndex += 3
		}
	}

	if opts.Within != "" {
		// Parse bounding box
		coords := strings.Split(opts.Within, ",")
		if len(coords) >= 6 {
			conditions = append(conditions, fmt.Sprintf("ST_Within(e.location, ST_MakeEnvelope($%d, $%d, $%d, $%d, $%d, $%d))", 
				argIndex, argIndex+1, argIndex+2, argIndex+3, argIndex+4, argIndex+5))
			args = append(args, coords[0], coords[1], coords[2], coords[3], coords[4], coords[5])
			argIndex += 6
		}
	}

	if opts.Contains != "" {
		// Parse point
		coords := strings.Split(opts.Contains, ",")
		if len(coords) >= 2 {
			conditions = append(conditions, fmt.Sprintf("ST_Contains(e.location, ST_Point($%d, $%d))", argIndex, argIndex+1))
			args = append(args, coords[0], coords[1])
			argIndex += 2
		}
	}

	// Add WHERE clause if we have conditions
	if len(conditions) > 0 {
		query.WriteString(" WHERE ")
		query.WriteString(strings.Join(conditions, " AND "))
	}

	// Add ORDER BY
	if !opts.Count {
		query.WriteString(" ORDER BY e.created_at DESC")
	}

	// Add LIMIT and OFFSET
	if opts.Limit > 0 && !opts.Count {
		query.WriteString(fmt.Sprintf(" LIMIT $%d", argIndex))
		args = append(args, opts.Limit)
		argIndex++
	}

	if opts.Offset > 0 && !opts.Count {
		query.WriteString(fmt.Sprintf(" OFFSET $%d", argIndex))
		args = append(args, opts.Offset)
		argIndex++
	}

	return query.String(), args, nil
}
