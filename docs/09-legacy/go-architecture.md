# Original Go Architecture

## What We Built Before the Pivot

### System Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Go Backend │────▶│ PostgreSQL  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │   Redis     │
                    └─────────────┘
```

### Core Components

#### Backend (Go + Gin)
```go
package main

import "github.com/gin-gonic/gin"

func main() {
    r := gin.Default()
    
    // API routes
    r.GET("/buildings", GetBuildings)
    r.GET("/buildings/:id/floors", GetFloors)
    r.POST("/objects", CreateObject)
    
    r.Run(":8080")
}
```

#### Database Schema
```sql
CREATE TABLE buildings (
    id UUID PRIMARY KEY,
    name TEXT,
    address TEXT,
    metadata JSONB
);

CREATE TABLE objects (
    id UUID PRIMARY KEY,
    building_id UUID REFERENCES buildings,
    type VARCHAR(50),
    location POINT,
    properties JSONB
);
```

#### Why It Didn't Scale

1. **Database bottleneck** at 10,000 objects
2. **JSON overhead** consumed bandwidth
3. **Internet requirement** excluded many buildings
4. **Complex deployment** scared away users
5. **Vendor-like complexity** defeated the purpose

### Valuable Code Patterns

These patterns were worth preserving:

```go
// Hierarchical navigation
func (b *Building) Path() string {
    return fmt.Sprintf("/%s/%s/floor-%d",
        b.Campus, b.Name, b.CurrentFloor)
}

// Object addressing
func (o *Object) Address() string {
    return fmt.Sprintf("%s/%s/%s",
        o.Building.Path(), o.Room, o.ID)
}
```

---

→ Next: [Lessons Learned](lessons-learned.md)