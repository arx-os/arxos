# Phase 7: Integration & Polish - Implementation Plan

**Goal:** Wire everything together and make it actually work  
**Status:** Ready to begin  
**Estimated Time:** 4-6 weeks  
**Priority:** CRITICAL

---

## 🎯 **What Phase 7 Means**

**Current Reality:**
```bash
arx bas import file.csv
# Output: "✅ Imported 145 points"
# Reality: Nothing actually happened
```

**Phase 7 Goal:**
```bash
arx bas import file.csv
# Output: "✅ Imported 145 points"
# Reality: ✅ 145 rows in bas_points table
#          ✅ Mapped to rooms automatically
#          ✅ Commit created in Git history
```

---

## 📋 **Implementation Checklist**

### **Week 1: Foundation & First Feature**

**Day 1-2: Database Setup**
- [ ] Create PostgreSQL database
- [ ] Install PostGIS extension
- [ ] Run all migrations (014, 015, 016, 017, 018)
- [ ] Verify all tables created
- [ ] Create test user and organization

```bash
# Create database
createdb arxos_dev
psql arxos_dev -c "CREATE EXTENSION postgis;"

# Run migrations
arx migrate up

# Verify
psql arxos_dev -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
# Should see 107 tables
```

**Day 3-4: Wire BAS Import (First Feature)**
- [ ] Create database connection in main.go
- [ ] Initialize repositories in app.go
- [ ] Create service container
- [ ] Wire BAS import command to use case
- [ ] Test with sample CSV file

```go
// In cmd/arx/main.go
db, err := sql.Open("postgres", connectionString)
postgis.NewBASPointRepository(db)
// etc.
```

**Day 5: Test & Debug BAS Import**
- [ ] Create test CSV file
- [ ] Run `arx bas import test.csv`
- [ ] Verify data in database
- [ ] Fix bugs
- [ ] Document working command

### **Week 2: Branch & Commit Wiring**

**Day 1-2: Wire Branch Operations**
- [ ] Wire `arx branch create`
- [ ] Wire `arx branch list`
- [ ] Wire `arx checkout`
- [ ] Test branch creation flow
- [ ] Verify in database

**Day 3-4: Wire Commit Operations**
- [ ] Wire `arx commit`
- [ ] Wire `arx log`
- [ ] Test commit tracking
- [ ] Verify Git history

**Day 5: Integration Test**
- [ ] Test full workflow: branch → change → commit
- [ ] Verify in database
- [ ] Fix bugs

### **Week 3: PR & Issue Wiring**

**Day 1-2: Wire PR Operations**
- [ ] Wire `arx pr create`
- [ ] Wire `arx pr list`
- [ ] Wire `arx pr approve`
- [ ] Wire `arx pr merge`
- [ ] Test PR workflow

**Day 3-4: Wire Issue Operations**
- [ ] Wire `arx issue create`
- [ ] Wire `arx issue start` (auto-branch/PR)
- [ ] Wire `arx issue resolve`
- [ ] Test issue → branch → PR flow

**Day 5: Integration Test**
- [ ] Test complete CMMS workflow
- [ ] Issue → Start → Commit → Resolve → Merge
- [ ] Verify all tables updated correctly

### **Week 4: HTTP API**

**Day 1-2: API Server Setup**
- [ ] Create HTTP server (Gin or net/http)
- [ ] Add middleware (logging, CORS, auth)
- [ ] Create API routes

```go
// Example structure
/api/v1/
  /buildings
  /equipment
  /issues
  /prs
  /bas
```

**Day 3-4: Wire Endpoints**
- [ ] POST /api/v1/issues (create issue)
- [ ] GET /api/v1/buildings/:id
- [ ] GET /api/v1/equipment/:id
- [ ] GET /api/v1/bas/points
- [ ] POST /api/v1/auth/login

**Day 5: API Testing**
- [ ] Test with Postman/curl
- [ ] Document all endpoints
- [ ] Create OpenAPI spec

### **Week 5: Mobile Integration**

**Day 1-2: Update Mobile App**
- [ ] Add API client to mobile
- [ ] Wire issue creation screen
- [ ] Wire building navigation
- [ ] Wire equipment view

**Day 3-4: AR Integration**
- [ ] Wire AR object detection (if Phase 5)
- [ ] Wire AR photo capture
- [ ] Test end-to-end mobile flow

**Day 5: Mobile Testing**
- [ ] Test on physical device
- [ ] Test issue creation via mobile
- [ ] Verify in database

### **Week 6: Testing & Polish**

**Day 1-2: End-to-End Testing**
- [ ] Test all CLI commands
- [ ] Test all API endpoints
- [ ] Test mobile app workflows
- [ ] Create test suite

**Day 3-4: Bug Fixes**
- [ ] Fix integration bugs
- [ ] Handle edge cases
- [ ] Add error messages
- [ ] Improve UX

**Day 5: Documentation**
- [ ] Update README
- [ ] Create user guide
- [ ] Create API documentation
- [ ] Create deployment guide

---

## 🔧 **Technical Implementation Details**

### **1. Service Container Pattern**

```go
// In internal/cli/app.go
type ServiceContainer struct {
    // Repositories
    BASPointRepo    domain.BASPointRepository
    BranchRepo      domain.BranchRepository
    IssueRepo       domain.IssueRepository
    PRRepo          domain.PullRequestRepository
    
    // Use Cases
    BASImportUC     *usecase.BASImportUseCase
    BranchUC        *usecase.BranchUseCase
    IssueUC         *usecase.IssueUseCase
    PRUC            *usecase.PullRequestUseCase
    
    // Infrastructure
    DB              *sql.DB
    Logger          domain.Logger
}

func NewServiceContainer(db *sql.DB) *ServiceContainer {
    // Initialize repositories
    basPointRepo := postgis.NewBASPointRepository(db)
    branchRepo := postgis.NewBranchRepository(db)
    // etc.
    
    // Initialize use cases
    basImportUC := usecase.NewBASImportUseCase(
        basPointRepo,
        // ... other dependencies
    )
    
    return &ServiceContainer{
        BASPointRepo: basPointRepo,
        BASImportUC:  basImportUC,
        // etc.
    }
}
```

### **2. Wire CLI Command to Use Case**

```go
// In internal/cli/commands/bas.go
func newBASImportCommand(serviceContext any) *cobra.Command {
    cmd := &cobra.Command{
        Use:   "import <file>",
        Short: "Import BAS points from CSV",
        Args:  cobra.ExactArgs(1),
        RunE: func(cmd *cobra.Command, args []string) error {
            // Cast service context
            services := serviceContext.(*cli.ServiceContainer)
            
            // Get flags
            buildingID, _ := cmd.Flags().GetString("building")
            
            // Call use case
            result, err := services.BASImportUC.ImportBASPoints(
                cmd.Context(),
                domain.ImportBASPointsRequest{
                    FilePath:   args[0],
                    BuildingID: types.FromString(buildingID),
                },
            )
            if err != nil {
                return fmt.Errorf("import failed: %w", err)
            }
            
            // Display results
            fmt.Printf("✅ Import complete\n")
            fmt.Printf("   Points added: %d\n", result.PointsAdded)
            fmt.Printf("   Points mapped: %d\n", result.PointsMapped)
            
            return nil
        },
    }
    
    cmd.Flags().String("building", "", "Building ID (required)")
    return cmd
}
```

### **3. HTTP API Example**

```go
// In cmd/arx-server/main.go
package main

import (
    "github.com/gin-gonic/gin"
    "github.com/arx-os/arxos/internal/api"
)

func main() {
    // Initialize DB and services (same as CLI)
    db := initDB()
    services := cli.NewServiceContainer(db)
    
    // Create HTTP server
    r := gin.Default()
    
    // Register routes
    api.RegisterIssueRoutes(r, services.IssueUC)
    api.RegisterPRRoutes(r, services.PRUC)
    api.RegisterBASRoutes(r, services.BASImportUC)
    
    // Start server
    r.Run(":8080")
}
```

```go
// In internal/api/issue_routes.go
func RegisterIssueRoutes(r *gin.Engine, issueUC *usecase.IssueUseCase) {
    issues := r.Group("/api/v1/issues")
    {
        issues.POST("", func(c *gin.Context) {
            var req domain.CreateIssueRequest
            if err := c.BindJSON(&req); err != nil {
                c.JSON(400, gin.H{"error": err.Error()})
                return
            }
            
            issue, err := issueUC.CreateIssue(c.Request.Context(), req)
            if err != nil {
                c.JSON(500, gin.H{"error": err.Error()})
                return
            }
            
            c.JSON(201, issue)
        })
        
        issues.GET("/:id", func(c *gin.Context) {
            // Get issue by ID
        })
    }
}
```

---

## 🧪 **Testing Strategy**

### **Unit Tests**
```bash
# Test individual components
go test ./internal/usecase/...
go test ./internal/infrastructure/...
```

### **Integration Tests**
```bash
# Test CLI commands end-to-end
go test ./tests/integration/...

# Example integration test
func TestBASImportEndToEnd(t *testing.T) {
    // Setup test DB
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)
    
    // Import CSV
    result := runCommand("arx", "bas", "import", "test.csv")
    
    // Verify in DB
    var count int
    db.QueryRow("SELECT COUNT(*) FROM bas_points").Scan(&count)
    assert.Equal(t, 145, count)
}
```

### **API Tests**
```bash
# Test HTTP endpoints
go test ./tests/api/...

# Example API test
func TestCreateIssueAPI(t *testing.T) {
    server := setupTestServer(t)
    
    resp, err := http.Post(
        "http://localhost:8080/api/v1/issues",
        "application/json",
        strings.NewReader(`{"title": "Test Issue"}`),
    )
    
    assert.NoError(t, err)
    assert.Equal(t, 201, resp.StatusCode)
}
```

---

## 📚 **Resources Needed**

### **Software**
- PostgreSQL 14+ with PostGIS
- Go 1.21+
- Git
- Make (optional, for automation)

### **Tools**
- Postman or Insomnia (API testing)
- pgAdmin or DBeaver (database management)
- VS Code with Go extension

### **Time Commitment**
- **Minimum:** 20 hours/week for 4 weeks
- **Ideal:** 30-40 hours/week for 3-4 weeks
- **Alternative:** Get help from mid-level developer (10-20 hours)

---

## ✅ **Success Criteria**

**Phase 7 is complete when:**

1. **All CLI commands work end-to-end**
   ```bash
   ✅ arx bas import file.csv → Data in database
   ✅ arx issue create → Issue in database
   ✅ arx issue start 234 → Branch and PR created
   ✅ arx pr merge 245 → Building state updated
   ```

2. **HTTP API is functional**
   ```bash
   ✅ Mobile app can create issues
   ✅ Mobile app can view buildings/equipment
   ✅ Mobile app can upload photos
   ```

3. **End-to-end workflow works**
   ```bash
   ✅ Custodian reports issue (mobile)
   ✅ System auto-assigns to electrician
   ✅ Electrician starts work (creates branch/PR)
   ✅ Electrician resolves (commits)
   ✅ PR merges automatically
   ✅ Building state updated
   ✅ Full audit trail in Git history
   ```

4. **Documentation is complete**
   ```bash
   ✅ README with quick start
   ✅ API documentation
   ✅ User guide
   ✅ Deployment guide
   ```

---

## 🚀 **Getting Started**

**Right Now:**
```bash
# 1. Review what we built
cd /arxos
ls -la internal/domain/
ls -la internal/usecase/
ls -la internal/cli/commands/

# 2. Read the migrations
cat internal/migrations/014_bas_integration.up.sql
cat internal/migrations/017_issues.up.sql

# 3. Understand one feature end-to-end
# Read: BAS domain → BAS use case → BAS command
# Trace: How would data flow from CLI to database?
```

**This Week:**
```bash
# 1. Setup PostgreSQL with PostGIS
# 2. Create arxos_dev database
# 3. Run migrations
# 4. Start wiring first feature (BAS import)
```

---

**Ready to make ArxOS real? Phase 7 is where vision becomes reality.** 🎯

