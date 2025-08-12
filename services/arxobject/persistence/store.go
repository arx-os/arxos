// Package persistence provides fast, efficient storage for ArxObjects
package persistence

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/arxos/arxos/services/arxobject/engine"
	bolt "go.etcd.io/bbolt"
)

const (
	// Bucket names
	objectBucket       = "objects"
	relationshipBucket = "relationships"
	constraintBucket   = "constraints"
	indexBucket        = "indices"
	metadataBucket     = "metadata"
)

// Store provides persistent storage for ArxObjects
type Store struct {
	db       *bolt.DB
	path     string
	mu       sync.RWMutex
	cache    map[uint64]*engine.ArxObject
	cacheHit uint64
	cacheMiss uint64
}

// NewStore creates a new persistent store
func NewStore(dbPath string) (*Store, error) {
	// Ensure directory exists
	dir := filepath.Dir(dbPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create directory: %w", err)
	}
	
	// Open BoltDB
	db, err := bolt.Open(dbPath, 0600, &bolt.Options{
		Timeout:      1 * time.Second,
		NoGrowSync:   false,
		FreelistType: bolt.FreelistArrayType,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}
	
	// Initialize buckets
	err = db.Update(func(tx *bolt.Tx) error {
		buckets := []string{
			objectBucket,
			relationshipBucket,
			constraintBucket,
			indexBucket,
			metadataBucket,
		}
		
		for _, bucket := range buckets {
			if _, err := tx.CreateBucketIfNotExists([]byte(bucket)); err != nil {
				return err
			}
		}
		
		return nil
	})
	
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to create buckets: %w", err)
	}
	
	return &Store{
		db:    db,
		path:  dbPath,
		cache: make(map[uint64]*engine.ArxObject, 10000),
	}, nil
}

// SaveObject persists an ArxObject
func (s *Store) SaveObject(obj *engine.ArxObject) error {
	return s.db.Update(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(objectBucket))
		
		// Serialize object
		data := s.serializeObject(obj)
		
		// Store with ID as key
		key := make([]byte, 8)
		binary.BigEndian.PutUint64(key, obj.ID)
		
		if err := bucket.Put(key, data); err != nil {
			return err
		}
		
		// Update cache
		s.mu.Lock()
		s.cache[obj.ID] = obj
		s.mu.Unlock()
		
		// Update spatial index
		if err := s.updateSpatialIndex(tx, obj); err != nil {
			return err
		}
		
		return nil
	})
}

// LoadObject retrieves an ArxObject by ID
func (s *Store) LoadObject(id uint64) (*engine.ArxObject, error) {
	// Check cache first
	s.mu.RLock()
	if obj, exists := s.cache[id]; exists {
		s.cacheHit++
		s.mu.RUnlock()
		return obj, nil
	}
	s.mu.RUnlock()
	s.cacheMiss++
	
	var obj *engine.ArxObject
	
	err := s.db.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(objectBucket))
		
		key := make([]byte, 8)
		binary.BigEndian.PutUint64(key, id)
		
		data := bucket.Get(key)
		if data == nil {
			return fmt.Errorf("object not found: %d", id)
		}
		
		obj = s.deserializeObject(data)
		return nil
	})
	
	if err != nil {
		return nil, err
	}
	
	// Update cache
	s.mu.Lock()
	s.cache[id] = obj
	s.mu.Unlock()
	
	return obj, nil
}

// LoadAll loads all objects from storage
func (s *Store) LoadAll() ([]*engine.ArxObject, error) {
	var objects []*engine.ArxObject
	
	err := s.db.View(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(objectBucket))
		
		return bucket.ForEach(func(k, v []byte) error {
			obj := s.deserializeObject(v)
			objects = append(objects, obj)
			
			// Update cache
			s.mu.Lock()
			s.cache[obj.ID] = obj
			s.mu.Unlock()
			
			return nil
		})
	})
	
	if err != nil {
		return nil, err
	}
	
	return objects, nil
}

// DeleteObject removes an ArxObject
func (s *Store) DeleteObject(id uint64, softDelete bool) error {
	return s.db.Update(func(tx *bolt.Tx) error {
		bucket := tx.Bucket([]byte(objectBucket))
		
		key := make([]byte, 8)
		binary.BigEndian.PutUint64(key, id)
		
		if softDelete {
			// Mark as deleted but keep data
			data := bucket.Get(key)
			if data == nil {
				return fmt.Errorf("object not found: %d", id)
			}
			
			obj := s.deserializeObject(data)
			obj.Flags &= ^uint8(1) // Clear active flag
			
			return bucket.Put(key, s.serializeObject(obj))
		}
		
		// Hard delete
		if err := bucket.Delete(key); err != nil {
			return err
		}
		
		// Remove from cache
		s.mu.Lock()
		delete(s.cache, id)
		s.mu.Unlock()
		
		// Remove from spatial index
		if err := s.removeSpatialIndex(tx, id); err != nil {
			return err
		}
		
		return nil
	})
}

// QueryRegion finds objects within a spatial region
func (s *Store) QueryRegion(minX, minY, maxX, maxY float32) ([]uint64, error) {
	var ids []uint64
	
	err := s.db.View(func(tx *bolt.Tx) error {
		indexBucket := tx.Bucket([]byte(indexBucket))
		
		// Use spatial index to find candidates
		// This is a simplified grid-based index
		gridMinX := int32(minX / 10) // 10m grid cells
		gridMinY := int32(minY / 10)
		gridMaxX := int32(maxX / 10)
		gridMaxY := int32(maxY / 10)
		
		for gx := gridMinX; gx <= gridMaxX; gx++ {
			for gy := gridMinY; gy <= gridMaxY; gy++ {
				key := makeGridKey(gx, gy)
				data := indexBucket.Get(key)
				
				if data != nil {
					// Decode object IDs in this grid cell
					cellIds := decodeIDList(data)
					ids = append(ids, cellIds...)
				}
			}
		}
		
		return nil
	})
	
	if err != nil {
		return nil, err
	}
	
	// Remove duplicates
	seen := make(map[uint64]bool)
	unique := ids[:0]
	for _, id := range ids {
		if !seen[id] {
			seen[id] = true
			unique = append(unique, id)
		}
	}
	
	return unique, nil
}

// Transaction provides atomic operations
type Transaction struct {
	tx     *bolt.Tx
	store  *Store
	writes map[uint64]*engine.ArxObject
}

// BeginTransaction starts a new transaction
func (s *Store) BeginTransaction() *Transaction {
	tx, _ := s.db.Begin(true)
	return &Transaction{
		tx:     tx,
		store:  s,
		writes: make(map[uint64]*engine.ArxObject),
	}
}

// SaveObject saves an object within a transaction
func (t *Transaction) SaveObject(obj *engine.ArxObject) error {
	t.writes[obj.ID] = obj
	return nil
}

// Commit commits the transaction
func (t *Transaction) Commit() error {
	bucket := t.tx.Bucket([]byte(objectBucket))
	
	// Write all objects
	for id, obj := range t.writes {
		key := make([]byte, 8)
		binary.BigEndian.PutUint64(key, id)
		
		if err := bucket.Put(key, t.store.serializeObject(obj)); err != nil {
			t.tx.Rollback()
			return err
		}
		
		// Update spatial index
		if err := t.store.updateSpatialIndex(t.tx, obj); err != nil {
			t.tx.Rollback()
			return err
		}
	}
	
	if err := t.tx.Commit(); err != nil {
		return err
	}
	
	// Update cache after successful commit
	t.store.mu.Lock()
	for id, obj := range t.writes {
		t.store.cache[id] = obj
	}
	t.store.mu.Unlock()
	
	return nil
}

// Rollback rolls back the transaction
func (t *Transaction) Rollback() error {
	return t.tx.Rollback()
}

// Serialization methods

func (s *Store) serializeObject(obj *engine.ArxObject) []byte {
	// Fixed-size binary format for speed
	// Total: 64 bytes base + variable metadata
	
	size := 64
	if obj.MetadataPtr != nil {
		size += 256 // Reserve space for metadata
	}
	
	buf := make([]byte, size)
	
	// Header (8 bytes)
	binary.BigEndian.PutUint64(buf[0:8], obj.ID)
	
	// Type and flags (4 bytes)
	buf[8] = uint8(obj.Type)
	buf[9] = obj.Precision
	buf[10] = obj.Priority
	buf[11] = obj.Flags
	
	// Geometry (24 bytes)
	binary.BigEndian.PutUint32(buf[12:16], uint32(obj.X))
	binary.BigEndian.PutUint32(buf[16:20], uint32(obj.Y))
	binary.BigEndian.PutUint32(buf[20:24], uint32(obj.Z))
	binary.BigEndian.PutUint16(buf[24:26], uint16(obj.Length))
	binary.BigEndian.PutUint16(buf[26:28], uint16(obj.Width))
	binary.BigEndian.PutUint16(buf[28:30], uint16(obj.Height))
	binary.BigEndian.PutUint16(buf[30:32], uint16(obj.RotationZ))
	
	// Relationships (8 bytes)
	binary.BigEndian.PutUint32(buf[32:36], obj.RelationshipStart)
	binary.BigEndian.PutUint16(buf[36:38], obj.RelationshipCount)
	binary.BigEndian.PutUint16(buf[38:40], obj.ConstraintBits)
	
	// Timestamps (16 bytes)
	binary.BigEndian.PutUint64(buf[40:48], uint64(obj.CreatedAt))
	binary.BigEndian.PutUint64(buf[48:56], uint64(obj.UpdatedAt))
	
	// Version (4 bytes)
	binary.BigEndian.PutUint32(buf[56:60], obj.Version)
	
	// Reserved (4 bytes)
	// buf[60:64] reserved for future use
	
	return buf
}

func (s *Store) deserializeObject(data []byte) *engine.ArxObject {
	if len(data) < 64 {
		return nil
	}
	
	obj := &engine.ArxObject{
		// Header
		ID: binary.BigEndian.Uint64(data[0:8]),
		
		// Type and flags
		Type:      engine.ArxObjectType(data[8]),
		Precision: data[9],
		Priority:  data[10],
		Flags:     data[11],
		
		// Geometry
		X:         int32(binary.BigEndian.Uint32(data[12:16])),
		Y:         int32(binary.BigEndian.Uint32(data[16:20])),
		Z:         int32(binary.BigEndian.Uint32(data[20:24])),
		Length:    int16(binary.BigEndian.Uint16(data[24:26])),
		Width:     int16(binary.BigEndian.Uint16(data[26:28])),
		Height:    int16(binary.BigEndian.Uint16(data[28:30])),
		RotationZ: int16(binary.BigEndian.Uint16(data[30:32])),
		
		// Relationships
		RelationshipStart: binary.BigEndian.Uint32(data[32:36]),
		RelationshipCount: binary.BigEndian.Uint16(data[36:38]),
		ConstraintBits:    binary.BigEndian.Uint16(data[38:40]),
		
		// Timestamps
		CreatedAt: int64(binary.BigEndian.Uint64(data[40:48])),
		UpdatedAt: int64(binary.BigEndian.Uint64(data[48:56])),
		
		// Version
		Version: binary.BigEndian.Uint32(data[56:60]),
	}
	
	// Load metadata if present
	if len(data) > 64 {
		// Parse extended metadata
	}
	
	return obj
}

// Spatial indexing

func (s *Store) updateSpatialIndex(tx *bolt.Tx, obj *engine.ArxObject) error {
	bucket := tx.Bucket([]byte(indexBucket))
	
	// Calculate grid cell
	gridX := obj.X / 10000 // 10m grid cells
	gridY := obj.Y / 10000
	
	key := makeGridKey(gridX, gridY)
	
	// Get existing IDs in this cell
	data := bucket.Get(key)
	ids := decodeIDList(data)
	
	// Add this object's ID if not present
	found := false
	for _, id := range ids {
		if id == obj.ID {
			found = true
			break
		}
	}
	
	if !found {
		ids = append(ids, obj.ID)
	}
	
	// Save updated list
	return bucket.Put(key, encodeIDList(ids))
}

func (s *Store) removeSpatialIndex(tx *bolt.Tx, id uint64) error {
	// This would remove the ID from spatial index
	// Implementation depends on index structure
	return nil
}

func makeGridKey(x, y int32) []byte {
	key := make([]byte, 8)
	binary.BigEndian.PutUint32(key[0:4], uint32(x))
	binary.BigEndian.PutUint32(key[4:8], uint32(y))
	return key
}

func encodeIDList(ids []uint64) []byte {
	buf := make([]byte, 4+len(ids)*8)
	binary.BigEndian.PutUint32(buf[0:4], uint32(len(ids)))
	
	for i, id := range ids {
		binary.BigEndian.PutUint64(buf[4+i*8:4+(i+1)*8], id)
	}
	
	return buf
}

func decodeIDList(data []byte) []uint64 {
	if len(data) < 4 {
		return nil
	}
	
	count := binary.BigEndian.Uint32(data[0:4])
	ids := make([]uint64, count)
	
	for i := uint32(0); i < count; i++ {
		ids[i] = binary.BigEndian.Uint64(data[4+i*8 : 4+(i+1)*8])
	}
	
	return ids
}

// GetStats returns store statistics
func (s *Store) GetStats() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	var dbSize int64
	if info, err := os.Stat(s.path); err == nil {
		dbSize = info.Size()
	}
	
	return map[string]interface{}{
		"cache_size":  len(s.cache),
		"cache_hits":  s.cacheHit,
		"cache_miss":  s.cacheMiss,
		"db_size":     dbSize,
		"db_path":     s.path,
	}
}

// Close closes the store
func (s *Store) Close() error {
	return s.db.Close()
}