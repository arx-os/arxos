package models

import (
	"time"
)

// Document represents a construction document
type Document struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	ProjectID   string    `json:"project_id" gorm:"not null"`
	Name        string    `json:"name" gorm:"not null"`
	Description string    `json:"description"`
	Type        string    `json:"type" gorm:"not null"`     // drawing, spec, permit, contract, etc.
	Category    string    `json:"category" gorm:"not null"` // architectural, structural, mechanical, etc.
	Version     string    `json:"version" gorm:"default:'1.0'"`
	Status      string    `json:"status" gorm:"default:'draft'"` // draft, approved, rejected, archived
	FileSize    int64     `json:"file_size"`                     // Size in bytes
	FileType    string    `json:"file_type"`                     // pdf, dwg, rvt, etc.
	FilePath    string    `json:"file_path"`                     // Path to stored file
	UploadedBy  string    `json:"uploaded_by" gorm:"not null"`
	CreatedAt   time.Time `json:"created_at" gorm:"autoCreateTime"`
	UpdatedAt   time.Time `json:"updated_at" gorm:"autoUpdateTime"`

	// Relationships
	Revisions []DocumentRevision `json:"revisions,omitempty" gorm:"foreignKey:DocumentID"`
	Tags      []DocumentTag      `json:"tags,omitempty" gorm:"many2many:document_tags;"`
}

// DocumentRevision represents a revision of a document
type DocumentRevision struct {
	ID         string    `json:"id" gorm:"primaryKey"`
	DocumentID string    `json:"document_id" gorm:"not null"`
	Version    string    `json:"version" gorm:"not null"`
	Changes    string    `json:"changes"` // Description of changes
	FilePath   string    `json:"file_path" gorm:"not null"`
	FileSize   int64     `json:"file_size"`
	UploadedBy string    `json:"uploaded_by" gorm:"not null"`
	CreatedAt  time.Time `json:"created_at" gorm:"autoCreateTime"`
}

// DocumentTag represents a tag for documents
type DocumentTag struct {
	ID   string `json:"id" gorm:"primaryKey"`
	Name string `json:"name" gorm:"uniqueIndex"`
}

// DocumentCreateRequest represents the request to create a new document
type DocumentCreateRequest struct {
	ProjectID   string   `json:"project_id" validate:"required"`
	Name        string   `json:"name" validate:"required"`
	Description string   `json:"description"`
	Type        string   `json:"type" validate:"required"`
	Category    string   `json:"category" validate:"required"`
	Version     string   `json:"version"`
	Tags        []string `json:"tags"`
}

// DocumentUpdateRequest represents the request to update a document
type DocumentUpdateRequest struct {
	Name        *string   `json:"name"`
	Description *string   `json:"description"`
	Type        *string   `json:"type"`
	Category    *string   `json:"category"`
	Status      *string   `json:"status"`
	Tags        *[]string `json:"tags"`
}

// DocumentUploadRequest represents the request to upload a document file
type DocumentUploadRequest struct {
	DocumentID string `json:"document_id" validate:"required"`
	Version    string `json:"version"`
	Changes    string `json:"changes"`
}

// DocumentListResponse represents the response for listing documents
type DocumentListResponse struct {
	Documents []Document `json:"documents"`
	Total     int64      `json:"total"`
	Page      int        `json:"page"`
	Limit     int        `json:"limit"`
}
