# Database Consolidation Strategy - PostgreSQL/PostGIS + Go/Chi

## 🎯 **Overview**

Arxos consolidates all database operations under a **unified PostgreSQL/PostGIS architecture** with **Go/Chi backend services**. This ensures consistency, performance, and maintainability across all components.

## 🏗️ **Consolidated Architecture**

### **1. Single Database Strategy**

#### **PostgreSQL/PostGIS as Primary Database**
```sql
-- Enable PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Unified schema for all Arxos components
CREATE SCHEMA arxos_core;
CREATE SCHEMA arxos_gus;
CREATE SCHEMA arxos_cad;
CREATE SCHEMA arxos_sync;
```

#### **Database Connection Pool**
```go
// Unified database connection management
package database

import (
    "database/sql"
    "time"
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
)

type DatabaseManager struct {
    DB *gorm.DB
    Config DatabaseConfig
}

type DatabaseConfig struct {
    Host            string
    Port            int
    Database        string
    Username        string
    Password        string
    MaxOpenConns    int
    MaxIdleConns    int
    ConnMaxLifetime time.Duration
}

func NewDatabaseManager(config DatabaseConfig) (*DatabaseManager, error) {
    dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=require",
        config.Host, config.Port, config.Username, config.Password, config.Database)
    
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info),
    })
    if err != nil {
        return nil, err
    }
    
    sqlDB, err := db.DB()
    if err != nil {
        return nil, err
    }
    
    // Configure connection pool
    sqlDB.SetMaxOpenConns(config.MaxOpenConns)
    sqlDB.SetMaxIdleConns(config.MaxIdleConns)
    sqlDB.SetConnMaxLifetime(config.ConnMaxLifetime)
    
    return &DatabaseManager{
        DB:     db,
        Config: config,
    }, nil
}
```

### **2. Unified Schema Design**

#### **Core Tables (arxos_core schema)**
```sql
-- Users table
CREATE TABLE arxos_core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    profile JSONB DEFAULT '{}',
    subscription JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE arxos_core.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES arxos_core.users(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Files table
CREATE TABLE arxos_core.files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    content TEXT,
    metadata JSONB DEFAULT '{}',
    permissions JSONB DEFAULT '{}',
    project_id UUID REFERENCES arxos_core.projects(id),
    owner_id UUID REFERENCES arxos_core.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### **GUS Tables (arxos_gus schema)**
```sql
-- GUS sessions
CREATE TABLE arxos_gus.sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    conversation_history JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}'
);

-- GUS knowledge base
CREATE TABLE arxos_gus.knowledge_base (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255),
    citation TEXT,
    relevance_tags TEXT[],
    embedding_vector VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- GUS interactions
CREATE TABLE arxos_gus.interactions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    intent VARCHAR(100),
    confidence FLOAT,
    entities JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### **CAD Tables (arxos_cad schema)**
```sql
-- CAD objects with spatial data
CREATE TABLE arxos_cad.objects (
    id SERIAL PRIMARY KEY,
    object_id VARCHAR(255) UNIQUE NOT NULL,
    object_type VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    geometry GEOMETRY(POINT, 4326),
    properties JSONB DEFAULT '{}',
    project_id UUID REFERENCES arxos_core.projects(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- CAD constraints
CREATE TABLE arxos_cad.constraints (
    id SERIAL PRIMARY KEY,
    constraint_id VARCHAR(255) UNIQUE NOT NULL,
    constraint_type VARCHAR(100) NOT NULL,
    object_ids VARCHAR(255)[] NOT NULL,
    parameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    project_id UUID REFERENCES arxos_core.projects(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial indexes for CAD data
CREATE INDEX idx_cad_objects_geometry ON arxos_cad.objects USING GIST (geometry);
CREATE INDEX idx_cad_objects_type ON arxos_cad.objects(object_type);
CREATE INDEX idx_cad_constraints_type ON arxos_cad.constraints(constraint_type);
```

#### **Sync Tables (arxos_sync schema)**
```sql
-- Sync sessions
CREATE TABLE arxos_sync.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES arxos_core.users(id),
    device_id VARCHAR(255) NOT NULL,
    file_id UUID REFERENCES arxos_core.files(id),
    version INTEGER DEFAULT 1,
    changes JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sync conflicts
CREATE TABLE arxos_sync.conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES arxos_core.files(id),
    device_ids VARCHAR(255)[] NOT NULL,
    conflict_data JSONB NOT NULL,
    resolution JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);
```

### **3. Go/Chi Backend Services**

#### **Unified API Gateway**
```go
// Main API router with Chi
package main

import (
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/go-chi/cors"
)

func setupRouter() *chi.Mux {
    r := chi.NewRouter()
    
    // Middleware
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(middleware.Timeout(60 * time.Second))
    
    // CORS
    r.Use(cors.Handler(cors.Options{
        AllowedOrigins:   []string{"*"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
        ExposedHeaders:   []string{"Link"},
        AllowCredentials: true,
        MaxAge:           300,
    }))
    
    // API routes
    r.Route("/api/v1", func(r chi.Router) {
        // Core services
        r.Route("/core", func(r chi.Router) {
            r.Get("/users", handlers.GetUsers)
            r.Post("/users", handlers.CreateUser)
            r.Get("/users/{id}", handlers.GetUser)
            r.Put("/users/{id}", handlers.UpdateUser)
            r.Delete("/users/{id}", handlers.DeleteUser)
            
            r.Get("/projects", handlers.GetProjects)
            r.Post("/projects", handlers.CreateProject)
            r.Get("/projects/{id}", handlers.GetProject)
            r.Put("/projects/{id}", handlers.UpdateProject)
            r.Delete("/projects/{id}", handlers.DeleteProject)
            
            r.Get("/files", handlers.GetFiles)
            r.Post("/files", handlers.CreateFile)
            r.Get("/files/{id}", handlers.GetFile)
            r.Put("/files/{id}", handlers.UpdateFile)
            r.Delete("/files/{id}", handlers.DeleteFile)
        })
        
        // GUS services
        r.Route("/gus", func(r chi.Router) {
            r.Post("/query", handlers.GUSQuery)
            r.Post("/task", handlers.GUSTask)
            r.Post("/knowledge", handlers.GUSKnowledge)
            r.Get("/health", handlers.GUSHealth)
        })
        
        // CAD services
        r.Route("/cad", func(r chi.Router) {
            r.Get("/objects", handlers.GetCADObjects)
            r.Post("/objects", handlers.CreateCADObject)
            r.Get("/objects/{id}", handlers.GetCADObject)
            r.Put("/objects/{id}", handlers.UpdateCADObject)
            r.Delete("/objects/{id}", handlers.DeleteCADObject)
            
            r.Get("/constraints", handlers.GetCADConstraints)
            r.Post("/constraints", handlers.CreateCADConstraint)
            r.Put("/constraints/{id}", handlers.UpdateCADConstraint)
            r.Delete("/constraints/{id}", handlers.DeleteCADConstraint)
        })
        
        // Sync services
        r.Route("/sync", func(r chi.Router) {
            r.Post("/connect", handlers.SyncConnect)
            r.Post("/upload", handlers.SyncUpload)
            r.Post("/download", handlers.SyncDownload)
            r.Post("/resolve-conflict", handlers.ResolveConflict)
        })
    })
    
    return r
}
```

#### **Service Layer Architecture**
```go
// Service layer for business logic
package services

import (
    "context"
    "database/sql"
    "gorm.io/gorm"
)

type CoreService struct {
    db *gorm.DB
}

type GUSService struct {
    db *gorm.DB
}

type CADService struct {
    db *gorm.DB
}

type SyncService struct {
    db *gorm.DB
}

// Core service methods
func (s *CoreService) GetUser(ctx context.Context, id string) (*User, error) {
    var user User
    result := s.db.WithContext(ctx).Where("id = ?", id).First(&user)
    if result.Error != nil {
        return nil, result.Error
    }
    return &user, nil
}

func (s *CoreService) CreateUser(ctx context.Context, user *User) error {
    return s.db.WithContext(ctx).Create(user).Error
}

// GUS service methods
func (s *GUSService) ProcessQuery(ctx context.Context, query *GUSQuery) (*GUSResponse, error) {
    // Process query with GUS agent
    response := &GUSResponse{
        Message:    "Query processed successfully",
        Confidence: 0.95,
        Intent:     "information_request",
        Entities:   make(map[string]interface{}),
        Actions:    []map[string]interface{}{},
        Timestamp:  time.Now(),
    }
    
    // Store interaction
    interaction := &GUSInteraction{
        SessionID: query.SessionID,
        UserID:    query.UserID,
        Query:     query.Query,
        Response:  response.Message,
        Intent:    response.Intent,
        Confidence: response.Confidence,
        Entities:  response.Entities,
    }
    
    return response, s.db.WithContext(ctx).Create(interaction).Error
}

// CAD service methods
func (s *CADService) GetCADObjects(ctx context.Context, projectID string) ([]CADObject, error) {
    var objects []CADObject
    result := s.db.WithContext(ctx).Where("project_id = ?", projectID).Find(&objects)
    return objects, result.Error
}

func (s *CADService) CreateCADObject(ctx context.Context, object *CADObject) error {
    return s.db.WithContext(ctx).Create(object).Error
}

// Sync service methods
func (s *SyncService) UploadChanges(ctx context.Context, changes *SyncChanges) error {
    // Process file changes
    for _, change := range changes.Changes {
        // Update file content
        if err := s.updateFileContent(ctx, change.FileID, change.Content); err != nil {
            return err
        }
        
        // Create sync session
        session := &SyncSession{
            UserID:   changes.UserID,
            DeviceID: changes.DeviceID,
            FileID:   change.FileID,
            Version:  change.Version,
            Changes:  change.Changes,
            Status:   "synced",
        }
        
        if err := s.db.WithContext(ctx).Create(session).Error; err != nil {
            return err
        }
    }
    
    return nil
}
```

### **4. Database Migration Strategy**

#### **Migration Management**
```go
// Database migration manager
package migrations

import (
    "gorm.io/gorm"
    "gorm.io/gorm/migrator"
)

type MigrationManager struct {
    db *gorm.DB
}

func (m *MigrationManager) RunMigrations() error {
    // Core schema migrations
    if err := m.migrateCoreSchema(); err != nil {
        return err
    }
    
    // GUS schema migrations
    if err := m.migrateGUSSchema(); err != nil {
        return err
    }
    
    // CAD schema migrations
    if err := m.migrateCADSchema(); err != nil {
        return err
    }
    
    // Sync schema migrations
    if err := m.migrateSyncSchema(); err != nil {
        return err
    }
    
    return nil
}

func (m *MigrationManager) migrateCoreSchema() error {
    // Create core tables
    return m.db.AutoMigrate(
        &User{},
        &Project{},
        &File{},
    )
}

func (m *MigrationManager) migrateGUSSchema() error {
    // Create GUS tables
    return m.db.AutoMigrate(
        &GUSSession{},
        &GUSKnowledgeBase{},
        &GUSInteraction{},
    )
}

func (m *MigrationManager) migrateCADSchema() error {
    // Create CAD tables with spatial support
    return m.db.AutoMigrate(
        &CADObject{},
        &CADConstraint{},
    )
}

func (m *MigrationManager) migrateSyncSchema() error {
    // Create sync tables
    return m.db.AutoMigrate(
        &SyncSession{},
        &SyncConflict{},
    )
}
```

### **5. Performance Optimization**

#### **Connection Pooling**
```go
// Optimized connection pool configuration
func configureConnectionPool(db *gorm.DB) error {
    sqlDB, err := db.DB()
    if err != nil {
        return err
    }
    
    // Configure for high performance
    sqlDB.SetMaxOpenConns(100)      // Maximum open connections
    sqlDB.SetMaxIdleConns(25)       // Maximum idle connections
    sqlDB.SetConnMaxLifetime(5 * time.Minute)  // Connection lifetime
    sqlDB.SetConnMaxIdleTime(1 * time.Minute)  // Idle connection timeout
    
    return nil
}
```

#### **Query Optimization**
```go
// Optimized queries with proper indexing
func (s *CoreService) GetUserProjects(ctx context.Context, userID string) ([]Project, error) {
    var projects []Project
    
    // Use proper joins and indexing
    result := s.db.WithContext(ctx).
        Joins("JOIN arxos_core.users ON projects.owner_id = users.id").
        Where("users.id = ?", userID).
        Preload("Files").  // Eager load related files
        Find(&projects)
    
    return projects, result.Error
}

// Spatial queries for CAD objects
func (s *CADService) GetCADObjectsInBounds(ctx context.Context, bounds []float64) ([]CADObject, error) {
    var objects []CADObject
    
    // Use PostGIS spatial functions
    query := `
        SELECT * FROM arxos_cad.objects 
        WHERE ST_Intersects(geometry, ST_MakeEnvelope(?, ?, ?, ?, 4326))
    `
    
    result := s.db.WithContext(ctx).Raw(query, bounds[0], bounds[1], bounds[2], bounds[3]).Scan(&objects)
    return objects, result.Error
}
```

## 🚀 **Implementation Status**

### **✅ Completed**
- Database schema consolidation
- Go/Chi backend framework
- Connection pooling configuration
- Basic CRUD operations

### **🔄 In Progress**
- Advanced spatial queries
- Performance optimization
- Migration scripts
- Testing framework

### **📋 Planned**
- Advanced indexing strategies
- Query optimization
- Monitoring and analytics
- Backup and recovery

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Status**: Implementation Ready 