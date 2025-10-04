---
name: Bug Report
about: Report a bug in ArxOS
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''

---

## Bug Description

A clear and concise description of what the bug is.

## Reproduction Steps

Steps to reproduce the behavior:
1. Go to '...'
2. Run command '...'
3. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Environment Information

### System Environment
- **OS**: [e.g. macOS 13.0, Ubuntu 20.04, Windows 11]
- **Architecture**: [e.g. x86_64, arm64]
- **Shell**: [e.g. bash, zsh, PowerShell]

### Software Versions
- **Go Version**: [e.g. 1.24.0] (run `go version`)
- **ArxOS Version**: [e.g. v0.1.0] (run `arxos version`)
- **PostGIS Version**: [e.g. PostgreSQL 16.0 with PostGIS 3.4.0]

### Database Configuration
- **Database Type**: [PostgreSQL with PostGIS]
- **Database Version**: [e.g. PostgreSQL 16.0, PostgreSQL 15.4]
- **PostGIS Extensions**: [List enabled extensions]
- **SSL Mode**: [e.g. require, disable, allow]

### Docker Environment (if applicable)
- **Docker Version**: [e.g. Docker Desktop 4.18.0]
- **Docker Compose Version**: [e.g. 2.16.0]
- **Container Images Used**: 
  - ArxOS: [version]  
  - PostGIS: [e.g. postgis/postgis:16-3.4]
  - Redis: [e.g. redis:7-alpine]

### Mobile Environment (if applicable)
- **React Native Version**: [e.g. 0.72.0]
- **iOS Version**: [e.g. iOS 16.0]
- **Android Version**: [e.g. Android 13]
- **Device Type**: [e.g. iPhone 14 Pro, Samsung Galaxy S23]

## Configuration Details

### ArxOS Configuration
```yaml
# Paste relevant parts of your ArxOS configuration
mode: local  # or cloud, hybrid
database:
  type: postgis
  # ... other relevant config
```

### Environment Variables (masked sensitive values)
```bash
# List relevant environment variables
ARXOS_MODE=local
POSTGRES_PASSWORD=***masked***
# ... other relevant variables
```

## Detailed Error Information

### Error Messages
```
Paste the exact error messages here
```

### Logs
<details>
<summary>Show relevant log output</summary>

```
Paste relevant log entries here
Include both ArxOS logs and system logs
Include timestamps
```

</details>

### Stack Trace
```
If applicable, paste the full stack trace here
```

## Context and Additional Information

### When Did This Start?
- [ ] Immediately after installation
- [ ] After updating ArxOS version
- [ ] After changing configuration
- [ ] After updating dependencies
- [ ] Started recently (describe when)
- [ ] Has been happening for a while

### Frequency
- [ ] Always occurs
- [ ] Sometimes occurs (describe when)
- [ ] Rarely occurs (describe triggers)
- [ ] Only occurs in specific situations

### Workaround
- [ ] No workaround known
- [ ] Workaround available (describe below)
- [ ] Issue resolves itself after restart
- [ ] Temporary workaround implemented

```
If workaround available, describe it here
```

### Related Features
Which ArxOS features are affected by this bug?
- [ ] CLI functionality
- [ ] Web API endpoints
- [ ] Database operations
- [ ] Spatial queries
- [ ] File I/O operations
- [ ] Authentication/authorization
- [ ] Mobile app functionality
- [ ] AR/spatial features
- [ ] Cache operations
- [ ] External service integration
- [ ] Other (specify): _________

### Severity Assessment
- [ ] **Critical**: System unusable, data loss risk, security vulnerability
- [ ] **High**: Major feature broken, significant functionality impaired
- [ ] **Medium**: Feature partially working, noticeable impact on usage
- [ ] **Low**: Minor issue, workaround available, cosmetic problem

## Additional Files

### Configuration Files
[If relevant, attach configuration files with sensitive data masked]

### Screenshots
[If applicable, add screenshots to help explain the problem]

### Diagnostic Information
```bash
# Run these commands to help diagnose the issue
arxos version
arxos config show
arxos status

# Database diagnostic info
pg_version
SELECT version(); 
SELECT PostGIS_Version();
```

## Labels and Triage

### Component Affected
- [ ] Core engine
- [ ] CLI interface
- [ ] Web API
- [ ] Database layer
- [ ] Mobile app
- [ ] Testing infrastructure
- [ ] Documentation
- [ ] Deployment/DevOps

### Issue Type
- [ ] Regression (worked in previous version)
- [ ] New issue (never worked)
- [ ] Performance degradation
- [ ] Security vulnerability
- [ ] Data corruption risk
- [ ] External dependency issue

---

**Note for Contributors:**
Please provide as much detail as possible. The more information you provide, the faster we can reproduce and fix the issue.