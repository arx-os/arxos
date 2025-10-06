package types

import (
	"fmt"
	"strings"

	"github.com/google/uuid"
)

// ID represents a unified identifier that supports both UUID and legacy TEXT formats
// This enables gradual migration from TEXT IDs to UUIDs while maintaining backward compatibility
type ID struct {
	UUID   string `json:"uuid" db:"uuid_id"`
	Legacy string `json:"legacy,omitempty" db:"id"`
}

// NewID creates a new ID with a generated UUID
func NewID() ID {
	return ID{
		UUID: uuid.New().String(),
	}
}

// NewIDWithLegacy creates a new ID with both UUID and legacy values
func NewIDWithLegacy(legacy string) ID {
	return ID{
		UUID:   uuid.New().String(),
		Legacy: legacy,
	}
}

// FromString creates an ID from a string, detecting if it's a UUID or legacy format
func FromString(idStr string) ID {
	if idStr == "" {
		return ID{}
	}

	// Check if it's a valid UUID
	if _, err := uuid.Parse(idStr); err == nil {
		return ID{UUID: idStr}
	}

	// Treat as legacy ID
	return ID{Legacy: idStr}
}

// String returns the primary identifier (UUID if available, otherwise legacy)
func (id ID) String() string {
	if id.UUID != "" {
		return id.UUID
	}
	return id.Legacy
}

// IsEmpty returns true if both UUID and Legacy are empty
func (id ID) IsEmpty() bool {
	return id.UUID == "" && id.Legacy == ""
}

// IsValid returns true if at least one identifier is present
func (id ID) IsValid() bool {
	return id.UUID != "" || id.Legacy != ""
}

// IsUUID returns true if the ID has a valid UUID
func (id ID) IsUUID() bool {
	if id.UUID == "" {
		return false
	}
	_, err := uuid.Parse(id.UUID)
	return err == nil
}

// IsLegacy returns true if the ID has a legacy identifier
func (id ID) IsLegacy() bool {
	return id.Legacy != ""
}

// MarshalJSON implements json.Marshaler
func (id ID) MarshalJSON() ([]byte, error) {
	if id.UUID != "" {
		return []byte(fmt.Sprintf(`"%s"`, id.UUID)), nil
	}
	return []byte(fmt.Sprintf(`"%s"`, id.Legacy)), nil
}

// UnmarshalJSON implements json.Unmarshaler
func (id *ID) UnmarshalJSON(data []byte) error {
	str := strings.Trim(string(data), `"`)
	*id = FromString(str)
	return nil
}

// Scan implements sql.Scanner for database scanning
func (id *ID) Scan(value any) error {
	if value == nil {
		*id = ID{}
		return nil
	}

	switch v := value.(type) {
	case string:
		*id = FromString(v)
	case []byte:
		*id = FromString(string(v))
	default:
		return fmt.Errorf("cannot scan %T into ID", value)
	}

	return nil
}

// Value implements driver.Valuer for database storage
func (id ID) Value() (any, error) {
	if id.UUID != "" {
		return id.UUID, nil
	}
	return id.Legacy, nil
}

// Equal compares two IDs for equality
func (id ID) Equal(other ID) bool {
	if id.UUID != "" && other.UUID != "" {
		return id.UUID == other.UUID
	}
	if id.Legacy != "" && other.Legacy != "" {
		return id.Legacy == other.Legacy
	}
	return id.String() == other.String()
}

// ToLegacyMap returns a map for legacy database operations
func (id ID) ToLegacyMap() map[string]any {
	return map[string]any{
		"id":      id.Legacy,
		"uuid_id": id.UUID,
	}
}

// ToUUIDMap returns a map for UUID-based database operations
func (id ID) ToUUIDMap() map[string]any {
	return map[string]any{
		"uuid_id": id.UUID,
		"id":      id.Legacy,
	}
}
