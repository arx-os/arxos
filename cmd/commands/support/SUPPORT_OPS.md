# Arxos Support Operations Console

## Concept
Every action a user can take in the UI must be executable via CLI for support staff to debug, troubleshoot, and assist users remotely.

## Core Capabilities Needed

### 1. User Context Switching
```bash
# Impersonate user for debugging (with audit log)
arxos support assume-user user@example.com --reason="Ticket #1234"

# View what user sees
arxos support view-as user@example.com building:headquarters

# List user's recent actions
arxos support user-activity user@example.com --last=24h
```

### 2. Job & Process Management
```bash
# View stuck/failed jobs
arxos support jobs --status=failed --last=1h

# Inspect specific job
arxos support job-inspect job_abc123 --verbose

# Retry failed ingestion
arxos support retry-job job_abc123 --step=wall_extraction

# Kill stuck process
arxos support kill-process pid_12345 --force
```

### 3. Data Pipeline Debugging
```bash
# Debug PDF ingestion step-by-step
arxos support debug-ingest massive-building.pdf --step-by-step

# View intermediate processing states
arxos support show-pipeline job_abc123
├── pdf_upload: ✓ completed (2.3s)
├── text_extraction: ✓ completed (5.1s)
├── wall_detection: ✗ failed - OOM error
├── room_detection: - skipped
└── bim_generation: - skipped

# Re-run specific pipeline step with different params
arxos support reprocess job_abc123 --from-step=wall_detection --memory=8G
```

### 4. Performance Diagnostics
```bash
# Profile slow operations
arxos support profile user@example.com --operation=pdf_upload

# Resource usage analysis
arxos support resources job_abc123
Memory: 6.2G / 8G (77%)
CPU: 340% (3.4 cores)
Disk I/O: 124 MB/s
Duration: 2m 34s

# Find bottlenecks
arxos support analyze-performance building:headquarters
Slow queries: 3
Large objects: 42 (>10MB each)
Confidence propagation loops: 2
```

### 5. Data Inspection & Repair
```bash
# View raw ArxObject data
arxos support inspect-raw wall_123 --format=json

# Validate data integrity
arxos support validate-building building:headquarters --deep

# Fix orphaned objects
arxos support repair-orphans --building=headquarters --dry-run

# Recalculate confidence scores
arxos support recalc-confidence building:headquarters:floor:3
```

### 6. Emergency Operations
```bash
# Rollback bad ingestion
arxos support rollback building:headquarters --to="2024-08-23T10:00:00Z"

# Emergency backup
arxos support backup user@example.com --priority=high

# Circuit breaker for failing service
arxos support circuit-break ai_service --duration=5m

# Scale resources for large operation
arxos support scale-resources job_abc123 --cpu=8 --memory=16G
```

### 7. Live Assistance Mode
```bash
# Start co-pilot session with user
arxos support copilot user@example.com
> User is uploading: floor-plan.pdf (324MB)
> Memory spike detected: 4.2G
> Intervention: Increasing memory limit...
> Success: Upload resumed

# Watch user's live session
arxos support shadow user@example.com --stream

# Send in-app message to user
arxos support message user@example.com "We've fixed the issue. Please try again."
```

### 8. Audit & Compliance
```bash
# Every support action is logged
arxos support audit --my-actions --today
10:23:14 - Assumed user john@example.com (Ticket #1234)
10:24:31 - Inspected job_abc123
10:25:45 - Increased memory for job_abc123
10:26:12 - Reprocessed wall_detection step

# Compliance reports
arxos support compliance-check user@example.com
Data retention: Compliant
Access logs: Complete
Validation records: 94% coverage
```

## Implementation Architecture

### Support Command Structure
```
commands/support/
├── assume.go          # User impersonation
├── jobs.go           # Job management
├── debug.go          # Debugging tools
├── performance.go    # Performance analysis
├── repair.go         # Data repair operations
├── emergency.go      # Emergency procedures
├── copilot.go        # Live assistance
└── audit.go          # Audit logging
```

### Required Backend APIs
```go
// Support-only endpoints (require admin auth)
POST   /api/v1/support/assume-user
GET    /api/v1/support/jobs/:id/debug
POST   /api/v1/support/jobs/:id/retry
GET    /api/v1/support/pipeline/:id/state
POST   /api/v1/support/repair/orphans
POST   /api/v1/support/rollback
GET    /api/v1/support/performance/profile
WS     /api/v1/support/copilot/:user
```

### Security Requirements
1. **MFA Required** - All support operations require 2FA
2. **Time-boxed Sessions** - Support access expires after 1 hour
3. **Audit Everything** - Every command logged with reason
4. **Read-only by Default** - Explicit flags for write operations
5. **Customer Consent** - Some operations require user approval

## Advanced Features

### 1. Playbooks
```bash
# Run diagnostic playbook
arxos support playbook diagnose-slow-upload --user=user@example.com

# Custom playbook for common issues
arxos support playbook fix-confidence-propagation --building=headquarters
```

### 2. Smart Suggestions
```bash
arxos support suggest job_abc123
Possible issues detected:
1. PDF file is 324MB (usually <50MB)
   → Try: arxos support reprocess --chunk-size=10MB
2. Complex geometry (42,000 vertices)
   → Try: arxos support simplify-geometry --tolerance=0.01
3. Memory pressure detected
   → Try: arxos support scale-resources --memory=16G
```

### 3. Simulation Mode
```bash
# Test fix without affecting production
arxos support simulate user@example.com --scenario="upload 500MB PDF"
Simulation results:
- Memory required: 12G
- Processing time: ~5 minutes
- Confidence score: 0.72
- Potential issues: 2 (memory, timeout)
```

### 4. Support Dashboard
```bash
# Real-time support dashboard
arxos support dashboard
┌─────────────────────────────────────┐
│ Active Issues         │ Count       │
├─────────────────────────────────────┤
│ Failed Jobs          │ 3           │
│ Slow Queries         │ 7           │
│ High Memory Users    │ 2           │
│ Stuck Pipelines      │ 1           │
└─────────────────────────────────────┘

Top Issues (last hour):
1. OOM errors in PDF processing (4 occurrences)
2. Timeout in confidence propagation (2 occurrences)
3. WebSocket disconnections (12 occurrences)
```

## Training Mode
```bash
# Safe environment for new support staff
arxos support training-mode on
[TRAINING MODE] Commands will be simulated, not executed

arxos support assume-user test@example.com
[TRAINING] Would assume user: test@example.com
[TRAINING] This would require MFA and create audit log
```

## Success Metrics
- Mean Time to Resolution (MTTR) < 15 minutes
- First Contact Resolution > 80%
- Support can resolve without engineering > 90%
- Customer satisfaction > 95%

## What This Enables

1. **24/7 Support** - Anyone can debug issues
2. **No SSH Required** - Everything through CLI
3. **Safe Operations** - Dry-run, rollback, audit
4. **Knowledge Base** - Playbooks for common issues
5. **Proactive Support** - Detect issues before users report
6. **Training Ground** - New support staff can learn safely

This turns Arxos support from reactive to proactive, from manual to automated, from risky to safe.