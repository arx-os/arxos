// Package arxobject implements the high-performance ArxObject service
package arxobject

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/arxos/arxos/pkg/arxobject/v1"
	"github.com/arxos/arxos/services/arxobject/engine"
	"github.com/arxos/arxos/services/arxobject/persistence"
	"github.com/arxos/arxos/services/arxobject/validator"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
)

// Service implements the ArxObject gRPC service
type Service struct {
	arxobjectv1.UnimplementedArxObjectServiceServer
	
	engine     *engine.Engine
	store      *persistence.Store
	validator  *validator.Validator
	
	// Stream management
	streamMu   sync.RWMutex
	streams    map[string]chan *arxobjectv1.ObjectChangeEvent
	
	// Metrics
	metrics    *Metrics
}

// NewService creates a new ArxObject service
func NewService(dbPath string) (*Service, error) {
	// Initialize persistence store
	store, err := persistence.NewStore(dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to create store: %w", err)
	}
	
	// Initialize engine with capacity hint
	eng := engine.NewEngine(100000)
	
	// Load existing objects from store
	if err := loadObjects(eng, store); err != nil {
		return nil, fmt.Errorf("failed to load objects: %w", err)
	}
	
	// Initialize validator
	val := validator.NewValidator()
	
	return &Service{
		engine:    eng,
		store:     store,
		validator: val,
		streams:   make(map[string]chan *arxobjectv1.ObjectChangeEvent),
		metrics:   NewMetrics(),
	}, nil
}

// CreateObject creates a new ArxObject
func (s *Service) CreateObject(ctx context.Context, req *arxobjectv1.CreateObjectRequest) (*arxobjectv1.CreateObjectResponse, error) {
	start := time.Now()
	defer s.metrics.RecordLatency("CreateObject", time.Since(start))
	
	// Validate request
	if req.Type == arxobjectv1.ObjectType_OBJECT_TYPE_UNSPECIFIED {
		return nil, status.Error(codes.InvalidArgument, "object type is required")
	}
	
	if req.Geometry == nil {
		return nil, status.Error(codes.InvalidArgument, "geometry is required")
	}
	
	// Create object in engine
	id := s.engine.CreateObject(
		engine.ArxObjectType(req.Type),
		float32(req.Geometry.X)/1000.0,
		float32(req.Geometry.Y)/1000.0,
		float32(req.Geometry.Z)/1000.0,
	)
	
	// Get created object
	obj, _ := s.engine.GetObject(id)
	
	// Set additional properties
	if req.Properties != nil {
		obj.SetProperties(req.Properties.Values)
	}
	
	if req.Metadata != nil {
		obj.SetMetadata(&engine.Metadata{
			Name:         req.Metadata.Name,
			Description:  req.Metadata.Description,
			Manufacturer: req.Metadata.Manufacturer,
			ModelNumber:  req.Metadata.ModelNumber,
			Tags:         req.Metadata.Tags,
		})
	}
	
	// Persist to store
	if err := s.store.SaveObject(obj); err != nil {
		s.engine.DeleteObject(id)
		return nil, status.Errorf(codes.Internal, "failed to persist object: %v", err)
	}
	
	// Notify streams
	s.notifyStreams(&arxobjectv1.ObjectChangeEvent{
		EventType: "created",
		Object:    s.objectToProto(obj),
		Timestamp: timestamppb.Now(),
	})
	
	s.metrics.IncrementCounter("objects_created")
	
	return &arxobjectv1.CreateObjectResponse{
		Object: s.objectToProto(obj),
	}, nil
}

// GetObject retrieves an ArxObject by ID
func (s *Service) GetObject(ctx context.Context, req *arxobjectv1.GetObjectRequest) (*arxobjectv1.GetObjectResponse, error) {
	start := time.Now()
	defer s.metrics.RecordLatency("GetObject", time.Since(start))
	
	obj, exists := s.engine.GetObject(req.Id)
	if !exists {
		return nil, status.Error(codes.NotFound, "object not found")
	}
	
	response := &arxobjectv1.GetObjectResponse{
		Object: s.objectToProto(obj),
	}
	
	// Include relationships if requested
	if req.IncludeRelationships {
		rels := s.engine.GetRelationships(req.Id)
		response.Relationships = s.relationshipsToProto(rels)
	}
	
	s.metrics.IncrementCounter("objects_retrieved")
	
	return response, nil
}

// UpdateObject updates an existing ArxObject
func (s *Service) UpdateObject(ctx context.Context, req *arxobjectv1.UpdateObjectRequest) (*arxobjectv1.UpdateObjectResponse, error) {
	start := time.Now()
	defer s.metrics.RecordLatency("UpdateObject", time.Since(start))
	
	obj, exists := s.engine.GetObject(req.Id)
	if !exists {
		return nil, status.Error(codes.NotFound, "object not found")
	}
	
	// Update geometry if provided
	if req.Geometry != nil {
		obj.UpdateGeometry(
			float32(req.Geometry.X)/1000.0,
			float32(req.Geometry.Y)/1000.0,
			float32(req.Geometry.Z)/1000.0,
			float32(req.Geometry.Length)/1000.0,
			float32(req.Geometry.Width)/1000.0,
			float32(req.Geometry.Height)/1000.0,
		)
	}
	
	// Update properties if provided
	if req.Properties != nil {
		obj.SetProperties(req.Properties.Values)
	}
	
	// Update metadata if provided
	if req.Metadata != nil {
		obj.SetMetadata(&engine.Metadata{
			Name:         req.Metadata.Name,
			Description:  req.Metadata.Description,
			Manufacturer: req.Metadata.Manufacturer,
			ModelNumber:  req.Metadata.ModelNumber,
			Tags:         req.Metadata.Tags,
		})
	}
	
	// Validate constraints if requested
	var errors []*arxobjectv1.ValidationError
	if req.ValidateConstraints {
		violations := s.validator.ValidateObject(obj)
		for _, v := range violations {
			errors = append(errors, &arxobjectv1.ValidationError{
				Field:    v.Field,
				Message:  v.Message,
				Severity: v.Severity,
			})
		}
		
		if len(errors) > 0 {
			s.metrics.IncrementCounter("validation_failures")
		}
	}
	
	// Persist changes
	if err := s.store.SaveObject(obj); err != nil {
		return nil, status.Errorf(codes.Internal, "failed to persist object: %v", err)
	}
	
	// Notify streams
	s.notifyStreams(&arxobjectv1.ObjectChangeEvent{
		EventType: "updated",
		Object:    s.objectToProto(obj),
		Timestamp: timestamppb.Now(),
	})
	
	s.metrics.IncrementCounter("objects_updated")
	
	return &arxobjectv1.UpdateObjectResponse{
		Object: s.objectToProto(obj),
		Errors: errors,
	}, nil
}

// DeleteObject deletes an ArxObject
func (s *Service) DeleteObject(ctx context.Context, req *arxobjectv1.DeleteObjectRequest) (*arxobjectv1.DeleteObjectResponse, error) {
	start := time.Now()
	defer s.metrics.RecordLatency("DeleteObject", time.Since(start))
	
	_, exists := s.engine.GetObject(req.Id)
	if !exists {
		return nil, status.Error(codes.NotFound, "object not found")
	}
	
	deletedCount := uint32(1)
	
	// Handle cascade deletion
	if req.Cascade {
		// Find and delete dependent objects
		deps := s.engine.GetDependents(req.Id)
		for _, depId := range deps {
			s.engine.DeleteObject(depId)
			s.store.DeleteObject(depId, req.SoftDelete)
			deletedCount++
		}
	}
	
	// Delete from engine
	s.engine.DeleteObject(req.Id)
	
	// Delete from store
	if err := s.store.DeleteObject(req.Id, req.SoftDelete); err != nil {
		return nil, status.Errorf(codes.Internal, "failed to delete object: %v", err)
	}
	
	// Notify streams
	s.notifyStreams(&arxobjectv1.ObjectChangeEvent{
		EventType: "deleted",
		Object:    &arxobjectv1.ArxObject{Id: req.Id},
		Timestamp: timestamppb.Now(),
	})
	
	s.metrics.IncrementCounter("objects_deleted")
	
	return &arxobjectv1.DeleteObjectResponse{
		Success:      true,
		DeletedCount: deletedCount,
	}, nil
}

// BatchCreateObjects creates multiple objects efficiently
func (s *Service) BatchCreateObjects(ctx context.Context, req *arxobjectv1.BatchCreateObjectsRequest) (*arxobjectv1.BatchCreateObjectsResponse, error) {
	start := time.Now()
	defer s.metrics.RecordLatency("BatchCreateObjects", time.Since(start))
	
	var objects []*arxobjectv1.ArxObject
	var errors []*arxobjectv1.BatchError
	createdCount := uint32(0)
	
	// Start transaction if requested
	var tx *persistence.Transaction
	if req.Transaction {
		tx = s.store.BeginTransaction()
		defer tx.Rollback()
	}
	
	// Create objects
	for i, createReq := range req.Objects {
		// Validate if requested
		if req.ValidateAll {
			// Perform validation
		}
		
		id := s.engine.CreateObject(
			engine.ArxObjectType(createReq.Type),
			float32(createReq.Geometry.X)/1000.0,
			float32(createReq.Geometry.Y)/1000.0,
			float32(createReq.Geometry.Z)/1000.0,
		)
		
		obj, _ := s.engine.GetObject(id)
		
		// Save to store
		var saveErr error
		if tx != nil {
			saveErr = tx.SaveObject(obj)
		} else {
			saveErr = s.store.SaveObject(obj)
		}
		
		if saveErr != nil {
			errors = append(errors, &arxobjectv1.BatchError{
				Index:   uint32(i),
				Message: saveErr.Error(),
			})
			continue
		}
		
		objects = append(objects, s.objectToProto(obj))
		createdCount++
	}
	
	// Commit transaction if used
	if tx != nil && len(errors) == 0 {
		if err := tx.Commit(); err != nil {
			return nil, status.Errorf(codes.Internal, "failed to commit transaction: %v", err)
		}
	}
	
	s.metrics.IncrementCounterBy("objects_created", int(createdCount))
	
	return &arxobjectv1.BatchCreateObjectsResponse{
		Objects:      objects,
		CreatedCount: createdCount,
		Errors:       errors,
	}, nil
}

// QueryRegion finds objects within a 3D region
func (s *Service) QueryRegion(ctx context.Context, req *arxobjectv1.QueryRegionRequest) (*arxobjectv1.QueryRegionResponse, error) {
	start := time.Now()
	defer s.metrics.RecordLatency("QueryRegion", time.Since(start))
	
	if req.Region == nil {
		return nil, status.Error(codes.InvalidArgument, "region is required")
	}
	
	// Query engine
	ids := s.engine.QueryRegion(
		float32(req.Region.Min.X)/1000.0,
		float32(req.Region.Min.Y)/1000.0,
		float32(req.Region.Max.X)/1000.0,
		float32(req.Region.Max.Y)/1000.0,
	)
	
	// Filter by types if specified
	var objects []*arxobjectv1.ArxObject
	for _, id := range ids {
		obj, exists := s.engine.GetObject(id)
		if !exists {
			continue
		}
		
		// Check type filter
		if len(req.Types) > 0 {
			typeMatch := false
			for _, t := range req.Types {
				if arxobjectv1.ObjectType(obj.Type) == t {
					typeMatch = true
					break
				}
			}
			if !typeMatch {
				continue
			}
		}
		
		objects = append(objects, s.objectToProto(obj))
		
		// Apply limit
		if req.Limit > 0 && uint32(len(objects)) >= req.Limit {
			break
		}
	}
	
	s.metrics.IncrementCounter("spatial_queries")
	
	return &arxobjectv1.QueryRegionResponse{
		Objects:    objects,
		TotalCount: uint32(len(ids)),
	}, nil
}

// CheckCollisions detects spatial conflicts
func (s *Service) CheckCollisions(ctx context.Context, req *arxobjectv1.CheckCollisionsRequest) (*arxobjectv1.CheckCollisionsResponse, error) {
	start := time.Now()
	defer s.metrics.RecordLatency("CheckCollisions", time.Since(start))
	
	collisions := s.engine.CheckCollisions(req.ObjectId, req.ClearanceMm)
	
	var results []*arxobjectv1.Collision
	for _, c := range collisions {
		obj, _ := s.engine.GetObject(c.ObjectID)
		results = append(results, &arxobjectv1.Collision{
			ObjectId:    c.ObjectID,
			ObjectType:  arxobjectv1.ObjectType(obj.Type),
			Severity:    c.Severity,
			Description: c.Description,
		})
	}
	
	s.metrics.IncrementCounter("collision_checks")
	
	return &arxobjectv1.CheckCollisionsResponse{
		Collisions: results,
	}, nil
}

// StreamObjectChanges streams real-time object changes
func (s *Service) StreamObjectChanges(req *arxobjectv1.StreamObjectChangesRequest, stream arxobjectv1.ArxObjectService_StreamObjectChangesServer) error {
	// Create stream channel
	streamID := fmt.Sprintf("%d", time.Now().UnixNano())
	ch := make(chan *arxobjectv1.ObjectChangeEvent, 100)
	
	s.streamMu.Lock()
	s.streams[streamID] = ch
	s.streamMu.Unlock()
	
	defer func() {
		s.streamMu.Lock()
		delete(s.streams, streamID)
		s.streamMu.Unlock()
		close(ch)
	}()
	
	// Send events to client
	for {
		select {
		case event := <-ch:
			// Filter by type if specified
			if len(req.Types) > 0 {
				typeMatch := false
				for _, t := range req.Types {
					if event.Object.Type == t {
						typeMatch = true
						break
					}
				}
				if !typeMatch {
					continue
				}
			}
			
			// Filter by region if specified
			if req.Region != nil {
				if !s.inRegion(event.Object, req.Region) {
					continue
				}
			}
			
			if err := stream.Send(event); err != nil {
				return err
			}
			
		case <-stream.Context().Done():
			return stream.Context().Err()
		}
	}
}

// Helper methods

func (s *Service) objectToProto(obj *engine.ArxObject) *arxobjectv1.ArxObject {
	return &arxobjectv1.ArxObject{
		Id:        obj.ID,
		Type:      arxobjectv1.ObjectType(obj.Type),
		Geometry: &arxobjectv1.Geometry{
			X:         obj.X,
			Y:         obj.Y,
			Z:         obj.Z,
			Length:    int32(obj.Length),
			Width:     int32(obj.Width),
			Height:    int32(obj.Height),
			RotationZ: int32(obj.RotationZ),
		},
		Precision: arxobjectv1.PrecisionLevel(obj.Precision),
		Priority:  uint32(obj.Priority),
		Active:    obj.Flags&1 != 0,
		Version:   obj.Version,
		CreatedAt: timestamppb.New(time.Unix(obj.CreatedAt, 0)),
		UpdatedAt: timestamppb.New(time.Unix(obj.UpdatedAt, 0)),
	}
}

func (s *Service) relationshipsToProto(rels []*engine.Relationship) []*arxobjectv1.Relationship {
	var result []*arxobjectv1.Relationship
	for _, rel := range rels {
		result = append(result, &arxobjectv1.Relationship{
			Id:       rel.ID,
			SourceId: rel.SourceID,
			TargetId: rel.TargetID,
			Type:     arxobjectv1.RelationshipType(rel.Type),
		})
	}
	return result
}

func (s *Service) notifyStreams(event *arxobjectv1.ObjectChangeEvent) {
	s.streamMu.RLock()
	defer s.streamMu.RUnlock()
	
	for _, ch := range s.streams {
		select {
		case ch <- event:
		default:
			// Channel full, skip
		}
	}
}

func (s *Service) inRegion(obj *arxobjectv1.ArxObject, region *arxobjectv1.BoundingBox) bool {
	return obj.Geometry.X >= region.Min.X &&
		obj.Geometry.X <= region.Max.X &&
		obj.Geometry.Y >= region.Min.Y &&
		obj.Geometry.Y <= region.Max.Y &&
		obj.Geometry.Z >= region.Min.Z &&
		obj.Geometry.Z <= region.Max.Z
}

func loadObjects(eng *engine.Engine, store *persistence.Store) error {
	// Load objects from store into engine
	objects, err := store.LoadAll()
	if err != nil {
		return err
	}
	
	for _, obj := range objects {
		eng.LoadObject(obj)
	}
	
	return nil
}