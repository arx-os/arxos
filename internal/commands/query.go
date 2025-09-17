package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// ExecuteQuery handles database queries using proper SQL queries
func ExecuteQuery(opts QueryOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewSQLiteDBFromPath("arxos.db")
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Build and execute query
	queryBuilder := NewQueryBuilder(opts)
	query, args := queryBuilder.Build()
	
	logger.Debug("Executing query: %s with args: %v", query, args)
	
	// Execute query based on count flag
	if opts.Count {
		count, err := executeCountQuery(ctx, db, query, args)
		if err != nil {
			return fmt.Errorf("failed to execute count query: %w", err)
		}
		fmt.Printf("Count: %d\n", count)
		return nil
	}

	// Execute regular query
	results, err := executeEquipmentQuery(ctx, db, query, args, opts)
	if err != nil {
		return fmt.Errorf("failed to execute query: %w", err)
	}

	// Output results
	switch opts.Output {
	case "json":
		return outputJSON(results.Equipment, opts.OutputFile)
	case "csv":
		return outputCSV(results.Equipment, opts.OutputFile)
	default:
		return outputTable(results.Equipment, opts.OutputFile)
	}
}

// QueryBuilder builds SQL queries for equipment searches
type QueryBuilder struct {
	opts   QueryOptions
	wheres []string
	args   []interface{}
}

// NewQueryBuilder creates a new query builder
func NewQueryBuilder(opts QueryOptions) *QueryBuilder {
	return &QueryBuilder{
		opts:   opts,
		wheres: make([]string, 0),
		args:   make([]interface{}, 0),
	}
}

// Build constructs the SQL query and returns query string and arguments
func (qb *QueryBuilder) Build() (string, []interface{}) {
	// Base query with joins
	baseQuery := `
		SELECT DISTINCT 
			e.id, e.equipment_tag, e.name, e.equipment_type, e.status, 
			e.manufacturer, e.model, e.serial_number, e.installation_date,
			e.location_x, e.location_y, e.location_z,
			f.level as floor_level, f.name as floor_name,
			r.room_number, r.name as room_name,
			b.name as building_name, b.arxos_id as building_id
		FROM equipment e
		LEFT JOIN buildings b ON e.building_id = b.id
		LEFT JOIN floors f ON e.floor_id = f.id  
		LEFT JOIN rooms r ON e.room_id = r.id`

	// Add WHERE conditions
	qb.addFilters()

	// Construct final query
	query := baseQuery
	if len(qb.wheres) > 0 {
		query += " WHERE " + strings.Join(qb.wheres, " AND ")
	}

	// Add ordering
	query += " ORDER BY b.name, f.level, r.room_number, e.name"

	// Add pagination
	if qb.opts.Limit > 0 {
		query += " LIMIT ?"
		qb.args = append(qb.args, qb.opts.Limit)
		
		if qb.opts.Offset > 0 {
			query += " OFFSET ?"
			qb.args = append(qb.args, qb.opts.Offset)
		}
	}

	return query, qb.args
}

// addFilters adds WHERE conditions based on query options
func (qb *QueryBuilder) addFilters() {
	// Building filter
	if qb.opts.Building != "" {
		qb.wheres = append(qb.wheres, "(b.arxos_id = ? OR b.name LIKE ?)")
		qb.args = append(qb.args, qb.opts.Building, "%"+qb.opts.Building+"%")
	}

	// Floor filter
	if qb.opts.Floor != 0 {
		qb.wheres = append(qb.wheres, "f.level = ?")
		qb.args = append(qb.args, qb.opts.Floor)
	}

	// Equipment type filter
	if qb.opts.Type != "" {
		qb.wheres = append(qb.wheres, "e.equipment_type LIKE ?")
		qb.args = append(qb.args, "%"+qb.opts.Type+"%")
	}

	// Status filter
	if qb.opts.Status != "" {
		qb.wheres = append(qb.wheres, "UPPER(e.status) = UPPER(?)")
		qb.args = append(qb.args, qb.opts.Status)
	}

	// Room filter
	if qb.opts.Room != "" {
		qb.wheres = append(qb.wheres, "(r.room_number LIKE ? OR r.name LIKE ?)")
		qb.args = append(qb.args, "%"+qb.opts.Room+"%", "%"+qb.opts.Room+"%")
	}

	// System filter (matches equipment type patterns)
	if qb.opts.System != "" {
		qb.wheres = append(qb.wheres, "e.equipment_type LIKE ?")
		qb.args = append(qb.args, qb.opts.System+"%")
	}

	// Raw SQL filter (with validation)
	if qb.opts.SQL != "" {
		// Basic SQL injection protection - only allow SELECT-like conditions
		sqlLower := strings.ToLower(strings.TrimSpace(qb.opts.SQL))
		if !strings.Contains(sqlLower, "drop") && 
		   !strings.Contains(sqlLower, "delete") && 
		   !strings.Contains(sqlLower, "insert") && 
		   !strings.Contains(sqlLower, "update") {
			qb.wheres = append(qb.wheres, "("+qb.opts.SQL+")")
		}
	}
}

// QueryResult holds query results and metadata
type QueryResult struct {
	Equipment    []*models.Equipment `json:"equipment"`
	Total        int                 `json:"total"`
	Count        int                 `json:"count"`
	Offset       int                 `json:"offset"`
	Limit        int                 `json:"limit"`
	QueryTime    time.Duration       `json:"query_time"`
	ExecutedAt   time.Time           `json:"executed_at"`
}

// executeCountQuery executes a count query and returns the result
func executeCountQuery(ctx context.Context, db *database.SQLiteDB, query string, args []interface{}) (int, error) {
	// Convert SELECT query to COUNT query
	countQuery := strings.Replace(query, "SELECT DISTINCT", "SELECT COUNT(DISTINCT", 1)
	
	// Find the FROM clause and wrap everything before it
	fromIndex := strings.Index(strings.ToUpper(countQuery), "FROM")
	if fromIndex == -1 {
		return 0, fmt.Errorf("invalid query: no FROM clause found")
	}
	
	// Rebuild as count query
	countQuery = "SELECT COUNT(*) FROM (" + query + ") as count_query"
	
	var count int
	row := db.QueryRow(ctx, countQuery, args...)
	if err := row.Scan(&count); err != nil {
		return 0, fmt.Errorf("failed to scan count result: %w", err)
	}
	
	return count, nil
}

// executeEquipmentQuery executes the equipment query and returns results
func executeEquipmentQuery(ctx context.Context, db *database.SQLiteDB, query string, args []interface{}, opts QueryOptions) (*QueryResult, error) {
	start := time.Now()
	
	rows, err := db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to execute query: %w", err)
	}
	defer rows.Close()
	
	var equipment []*models.Equipment
	for rows.Next() {
		eq, err := scanEquipmentRow(rows)
		if err != nil {
			return nil, fmt.Errorf("failed to scan equipment row: %w", err)
		}
		equipment = append(equipment, eq)
	}
	
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating rows: %w", err)
	}
	
	queryTime := time.Since(start)
	
	result := &QueryResult{
		Equipment:  equipment,
		Count:      len(equipment),
		Offset:     opts.Offset,
		Limit:      opts.Limit,
		QueryTime:  queryTime,
		ExecutedAt: time.Now(),
	}
	
	// Get total count if pagination is used
	if opts.Limit > 0 {
		totalCount, err := executeCountQuery(ctx, db, query, args)
		if err != nil {
			logger.Warn("Failed to get total count: %v", err)
			result.Total = len(equipment) // Fallback to current count
		} else {
			result.Total = totalCount
		}
	} else {
		result.Total = len(equipment)
	}
	
	return result, nil
}

// scanEquipmentRow scans a database row into an Equipment model
func scanEquipmentRow(rows interface{ Scan(...interface{}) error }) (*models.Equipment, error) {
	var eq models.Equipment
	var locationX, locationY, locationZ *float64
	var floorLevel *int
	var floorName, roomNumber, roomName, buildingName, buildingID *string
	var installationDate *time.Time
	
	err := rows.Scan(
		&eq.ID,
		&eq.Path,           // equipment_tag maps to Path
		&eq.Name,
		&eq.Type,
		&eq.Status,
		&eq.Model,
		&eq.Model,          // manufacturer -> model for now
		&eq.Serial,
		&installationDate,
		&locationX,
		&locationY,
		&locationZ,
		&floorLevel,
		&floorName,
		&roomNumber,
		&roomName,
		&buildingName,
		&buildingID,
	)
	
	if err != nil {
		return nil, err
	}
	
	// Set location if coordinates exist
	if locationX != nil && locationY != nil {
		eq.Location = &models.Point{
			X: *locationX,
			Y: *locationY,
		}
	}
	
	// Set installation date
	if installationDate != nil {
		eq.Installed = installationDate
	}
	
	// Build metadata with additional info
	eq.Metadata = make(map[string]interface{})
	if floorLevel != nil {
		eq.Metadata["floor_level"] = *floorLevel
	}
	if floorName != nil {
		eq.Metadata["floor_name"] = *floorName
	}
	if roomNumber != nil {
		eq.Metadata["room_number"] = *roomNumber
	}
	if roomName != nil {
		eq.Metadata["room_name"] = *roomName
	}
	if buildingName != nil {
		eq.Metadata["building_name"] = *buildingName
	}
	if buildingID != nil {
		eq.Metadata["building_id"] = *buildingID
	}
	if locationZ != nil {
		eq.Metadata["location_z"] = *locationZ
	}
	
	return &eq, nil
}

func outputTable(equipment []*models.Equipment, outputFile string) error {
	var w *tabwriter.Writer

	if outputFile != "" {
		file, err := os.Create(outputFile)
		if err != nil {
			return err
		}
		defer file.Close()
		w = tabwriter.NewWriter(file, 0, 0, 2, ' ', 0)
	} else {
		w = tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	}

	// Enhanced header with more columns
	fmt.Fprintln(w, "ID\tName\tType\tStatus\tBuilding\tFloor\tRoom\tLocation")
	fmt.Fprintln(w, "---\t----\t----\t------\t--------\t-----\t----\t--------")

	// Data with enhanced information
	for _, eq := range equipment {
		// Location coordinates
		location := "N/A"
		if eq.Location != nil {
			location = fmt.Sprintf("%.1f,%.1f", eq.Location.X, eq.Location.Y)
		}
		
		// Building info from metadata
		building := getStringFromMetadata(eq.Metadata, "building_name", "N/A")
		floor := getStringFromMetadata(eq.Metadata, "floor_level", "N/A")
		room := getStringFromMetadata(eq.Metadata, "room_number", "N/A")
		
		// Truncate long names for better table formatting
		name := eq.Name
		if len(name) > 20 {
			name = name[:17] + "..."
		}
		
		eqType := eq.Type
		if len(eqType) > 15 {
			eqType = eqType[:12] + "..."
		}
		
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n", 
			eq.ID, name, eqType, eq.Status, building, floor, room, location)
	}

	return w.Flush()
}

// getStringFromMetadata safely extracts a string value from metadata
func getStringFromMetadata(metadata map[string]interface{}, key, defaultValue string) string {
	if metadata == nil {
		return defaultValue
	}
	
	if value, exists := metadata[key]; exists {
		if strValue, ok := value.(string); ok {
			return strValue
		}
		// Handle numeric values (like floor_level)
		if numValue, ok := value.(int); ok {
			return fmt.Sprintf("%d", numValue)
		}
		if floatValue, ok := value.(float64); ok {
			return fmt.Sprintf("%.0f", floatValue)
		}
	}
	
	return defaultValue
}

func outputJSON(equipment []*models.Equipment, outputFile string) error {
	output := os.Stdout
	if outputFile != "" {
		var err error
		output, err = os.Create(outputFile)
		if err != nil {
			return err
		}
		defer output.Close()
	}

	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	return encoder.Encode(equipment)
}

func outputCSV(equipment []*models.Equipment, outputFile string) error {
	output := os.Stdout
	if outputFile != "" {
		var err error
		output, err = os.Create(outputFile)
		if err != nil {
			return err
		}
		defer output.Close()
	}

	// Enhanced CSV header
	fmt.Fprintln(output, "ID,Name,Type,Status,Building,Floor,Room,LocationX,LocationY,Model,Serial,Installed")

	// Enhanced CSV data
	for _, eq := range equipment {
		locationX := ""
		locationY := ""
		if eq.Location != nil {
			locationX = fmt.Sprintf("%.3f", eq.Location.X)
			locationY = fmt.Sprintf("%.3f", eq.Location.Y)
		}
		
		// Building info from metadata
		building := getStringFromMetadata(eq.Metadata, "building_name", "")
		floor := getStringFromMetadata(eq.Metadata, "floor_level", "")
		room := getStringFromMetadata(eq.Metadata, "room_number", "")
		
		// Installation date
		installed := ""
		if eq.Installed != nil {
			installed = eq.Installed.Format("2006-01-02")
		}
		
		// Escape CSV fields that might contain commas or quotes
		fields := []string{
			csvEscape(eq.ID),
			csvEscape(eq.Name),
			csvEscape(eq.Type),
			csvEscape(eq.Status),
			csvEscape(building),
			csvEscape(floor),
			csvEscape(room),
			csvEscape(locationX),
			csvEscape(locationY),
			csvEscape(eq.Model),
			csvEscape(eq.Serial),
			csvEscape(installed),
		}
		
		fmt.Fprintf(output, "%s\n", strings.Join(fields, ","))
	}

	return nil
}

// csvEscape properly escapes CSV field values
func csvEscape(field string) string {
	if field == "" {
		return ""
	}
	
	// If field contains comma, newline, or quote, wrap in quotes and escape quotes
	if strings.Contains(field, ",") || strings.Contains(field, "\n") || strings.Contains(field, "\"") {
		field = strings.ReplaceAll(field, "\"", "\"\"")
		return "\"" + field + "\""
	}
	
	return field
}