package postgis

import (
	"compress/gzip"
	"context"
	"database/sql"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/jmoiron/sqlx"
)

// ObjectRepository implements building.ObjectRepository using PostgreSQL + filesystem
type ObjectRepository struct {
	db        *sqlx.DB
	storePath string // Base path for object storage (e.g., ~/.arxos/objects/)
}

// NewObjectRepository creates a new PostgreSQL-backed object repository
func NewObjectRepository(db *sqlx.DB, storePath string) *ObjectRepository {
	return &ObjectRepository{
		db:        db,
		storePath: storePath,
	}
}

// Store stores an object and returns its hash
func (r *ObjectRepository) Store(ctxAny any, obj *building.Object) (string, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return "", fmt.Errorf("invalid context type")
	}

	// Calculate hash if not already set
	if obj.Hash == "" {
		obj.Hash = building.CalculateObjectHash(obj.Type, obj.Size, obj.Contents)
	}

	// Set creation time if not set
	if obj.CreatedAt.IsZero() {
		obj.CreatedAt = time.Now()
	}

	// Initialize ref count if not set
	if obj.RefCount == 0 {
		obj.RefCount = 1
	}

	// Determine storage strategy based on size
	if obj.Size < 1024 { // < 1KB: store in database
		return r.storeInDatabase(ctx, obj)
	} else if obj.Size < 10*1024*1024 { // 1KB - 10MB: store in filesystem
		return r.storeInFilesystem(ctx, obj, false)
	} else { // > 10MB: store compressed in filesystem
		return r.storeInFilesystem(ctx, obj, true)
	}
}

// storeInDatabase stores small objects directly in PostgreSQL
func (r *ObjectRepository) storeInDatabase(ctx context.Context, obj *building.Object) (string, error) {
	query := `
		INSERT INTO version_objects (hash, type, size, contents, store_path, created_at, ref_count, compressed)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		ON CONFLICT (hash) DO UPDATE
		SET ref_count = version_objects.ref_count + 1
		RETURNING hash
	`

	var hash string
	err := r.db.QueryRowContext(ctx, query,
		obj.Hash,
		obj.Type,
		obj.Size,
		obj.Contents,
		nil, // No file path for DB-stored objects
		obj.CreatedAt,
		obj.RefCount,
		false,
	).Scan(&hash)

	if err != nil {
		return "", fmt.Errorf("failed to store object in database: %w", err)
	}

	return hash, nil
}

// storeInFilesystem stores larger objects in the filesystem
func (r *ObjectRepository) storeInFilesystem(ctx context.Context, obj *building.Object, compress bool) (string, error) {
	// Create object path: objects/{hash[:2]}/{hash[2:]}
	objectPath := r.getObjectPath(obj.Hash)

	// Create directory if it doesn't exist
	dir := filepath.Dir(objectPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", fmt.Errorf("failed to create object directory: %w", err)
	}

	// Check if file already exists
	if _, err := os.Stat(objectPath); err == nil {
		// File exists, just increment ref count in DB
		return r.incrementExistingRef(ctx, obj.Hash)
	}

	// Write file
	file, err := os.Create(objectPath)
	if err != nil {
		return "", fmt.Errorf("failed to create object file: %w", err)
	}
	defer file.Close()

	// Write with optional compression
	if compress {
		gzipWriter := gzip.NewWriter(file)
		defer gzipWriter.Close()
		if _, err := gzipWriter.Write(obj.Contents); err != nil {
			os.Remove(objectPath) // Clean up on error
			return "", fmt.Errorf("failed to write compressed object: %w", err)
		}
		obj.Compressed = true
	} else {
		if _, err := file.Write(obj.Contents); err != nil {
			os.Remove(objectPath) // Clean up on error
			return "", fmt.Errorf("failed to write object: %w", err)
		}
	}

	// Store metadata in database
	query := `
		INSERT INTO version_objects (hash, type, size, contents, store_path, created_at, ref_count, compressed)
		VALUES ($1, $2, $3, NULL, $4, $5, $6, $7)
		ON CONFLICT (hash) DO UPDATE
		SET ref_count = version_objects.ref_count + 1
		RETURNING hash
	`

	var hash string
	err = r.db.QueryRowContext(ctx, query,
		obj.Hash,
		obj.Type,
		obj.Size,
		objectPath,
		obj.CreatedAt,
		obj.RefCount,
		obj.Compressed,
	).Scan(&hash)

	if err != nil {
		os.Remove(objectPath) // Clean up on error
		return "", fmt.Errorf("failed to store object metadata: %w", err)
	}

	return hash, nil
}

// incrementExistingRef increments the reference count for an existing object
func (r *ObjectRepository) incrementExistingRef(ctx context.Context, hash string) (string, error) {
	query := `
		UPDATE version_objects
		SET ref_count = ref_count + 1
		WHERE hash = $1
		RETURNING hash
	`

	var returnedHash string
	err := r.db.QueryRowContext(ctx, query, hash).Scan(&returnedHash)
	if err != nil {
		return "", fmt.Errorf("failed to increment ref count: %w", err)
	}

	return returnedHash, nil
}

// Load loads an object by hash
func (r *ObjectRepository) Load(ctxAny any, hash string) (*building.Object, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return nil, fmt.Errorf("invalid context type")
	}

	// Load metadata from database
	query := `
		SELECT hash, type, size, contents, store_path, created_at, ref_count, compressed
		FROM version_objects
		WHERE hash = $1
	`

	var obj building.Object
	var contents sql.NullString
	var storePath sql.NullString

	err := r.db.QueryRowContext(ctx, query, hash).Scan(
		&obj.Hash,
		&obj.Type,
		&obj.Size,
		&contents,
		&storePath,
		&obj.CreatedAt,
		&obj.RefCount,
		&obj.Compressed,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("object not found: %s", hash)
	}
	if err != nil {
		return nil, fmt.Errorf("failed to load object metadata: %w", err)
	}

	// Load contents
	if contents.Valid {
		// Contents stored in database
		obj.Contents = []byte(contents.String)
	} else if storePath.Valid {
		// Contents stored in filesystem
		obj.StorePath = storePath.String
		data, err := r.loadFromFilesystem(obj.StorePath, obj.Compressed)
		if err != nil {
			return nil, fmt.Errorf("failed to load object contents: %w", err)
		}
		obj.Contents = data
	} else {
		return nil, fmt.Errorf("object has no contents: %s", hash)
	}

	return &obj, nil
}

// loadFromFilesystem loads object contents from filesystem
func (r *ObjectRepository) loadFromFilesystem(path string, compressed bool) ([]byte, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open object file: %w", err)
	}
	defer file.Close()

	var reader io.Reader = file
	if compressed {
		gzipReader, err := gzip.NewReader(file)
		if err != nil {
			return nil, fmt.Errorf("failed to create gzip reader: %w", err)
		}
		defer gzipReader.Close()
		reader = gzipReader
	}

	data, err := io.ReadAll(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to read object contents: %w", err)
	}

	return data, nil
}

// Exists checks if an object exists
func (r *ObjectRepository) Exists(ctxAny any, hash string) (bool, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return false, fmt.Errorf("invalid context type")
	}

	query := `SELECT EXISTS(SELECT 1 FROM version_objects WHERE hash = $1)`

	var exists bool
	err := r.db.QueryRowContext(ctx, query, hash).Scan(&exists)
	if err != nil {
		return false, fmt.Errorf("failed to check object existence: %w", err)
	}

	return exists, nil
}

// IncrementRef increments the reference count for an object
func (r *ObjectRepository) IncrementRef(ctxAny any, hash string) error {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return fmt.Errorf("invalid context type")
	}

	query := `
		UPDATE version_objects
		SET ref_count = ref_count + 1
		WHERE hash = $1
	`

	result, err := r.db.ExecContext(ctx, query, hash)
	if err != nil {
		return fmt.Errorf("failed to increment ref count: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("object not found: %s", hash)
	}

	return nil
}

// DecrementRef decrements the reference count for an object
func (r *ObjectRepository) DecrementRef(ctxAny any, hash string) error {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return fmt.Errorf("invalid context type")
	}

	query := `
		UPDATE version_objects
		SET ref_count = GREATEST(0, ref_count - 1)
		WHERE hash = $1
	`

	result, err := r.db.ExecContext(ctx, query, hash)
	if err != nil {
		return fmt.Errorf("failed to decrement ref count: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("object not found: %s", hash)
	}

	return nil
}

// ListByType lists objects by type
func (r *ObjectRepository) ListByType(ctxAny any, objType building.ObjectType, limit, offset int) ([]*building.Object, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return nil, fmt.Errorf("invalid context type")
	}

	query := `
		SELECT hash, type, size, contents, store_path, created_at, ref_count, compressed
		FROM version_objects
		WHERE type = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := r.db.QueryContext(ctx, query, objType, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to list objects: %w", err)
	}
	defer rows.Close()

	var objects []*building.Object
	for rows.Next() {
		var obj building.Object
		var contents sql.NullString
		var storePath sql.NullString

		err := rows.Scan(
			&obj.Hash,
			&obj.Type,
			&obj.Size,
			&contents,
			&storePath,
			&obj.CreatedAt,
			&obj.RefCount,
			&obj.Compressed,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan object: %w", err)
		}

		// Note: Not loading contents for list operations (performance)
		if storePath.Valid {
			obj.StorePath = storePath.String
		}

		objects = append(objects, &obj)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating objects: %w", err)
	}

	return objects, nil
}

// DeleteUnreferenced deletes objects with zero references older than the specified time
func (r *ObjectRepository) DeleteUnreferenced(ctxAny any, olderThan time.Time) (int, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return 0, fmt.Errorf("invalid context type")
	}

	// First, get objects to delete (need to clean up filesystem)
	selectQuery := `
		SELECT hash, store_path
		FROM version_objects
		WHERE ref_count = 0
		  AND created_at < $1
		  AND store_path IS NOT NULL
	`

	rows, err := r.db.QueryContext(ctx, selectQuery, olderThan)
	if err != nil {
		return 0, fmt.Errorf("failed to select unreferenced objects: %w", err)
	}

	// Collect file paths to delete
	var filesToDelete []string
	for rows.Next() {
		var hash string
		var storePath sql.NullString
		if err := rows.Scan(&hash, &storePath); err != nil {
			rows.Close()
			return 0, fmt.Errorf("failed to scan object: %w", err)
		}
		if storePath.Valid {
			filesToDelete = append(filesToDelete, storePath.String)
		}
	}
	rows.Close()

	// Delete from database
	deleteQuery := `
		DELETE FROM version_objects
		WHERE ref_count = 0
		  AND created_at < $1
	`

	result, err := r.db.ExecContext(ctx, deleteQuery, olderThan)
	if err != nil {
		return 0, fmt.Errorf("failed to delete unreferenced objects: %w", err)
	}

	count, err := result.RowsAffected()
	if err != nil {
		return 0, fmt.Errorf("failed to get rows affected: %w", err)
	}

	// Delete files from filesystem
	for _, path := range filesToDelete {
		if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
			// Log error but don't fail (file might already be deleted)
			fmt.Printf("Warning: failed to delete object file %s: %v\n", path, err)
		}
	}

	return int(count), nil
}

// getObjectPath returns the filesystem path for an object hash
// Format: {storePath}/{hash[:2]}/{hash[2:]}
func (r *ObjectRepository) getObjectPath(hash string) string {
	if len(hash) < 3 {
		return filepath.Join(r.storePath, hash)
	}
	return filepath.Join(r.storePath, hash[:2], hash[2:])
}
