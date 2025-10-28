# Enterprise Deployment & Onboarding Guide

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Target Audience:** Enterprise customers, System administrators, DevOps teams  
**Status:** Production Ready

---

## Executive Summary

ArxOS Enterprise deployments enable organizations with hundreds to thousands of properties to manage building data with Git-based version control. This guide covers the complete technical architecture, automated onboarding, deployment procedures, and ongoing operations.

**Key Capabilities:**
- Deploy to thousands of properties in hours
- Automated provisioning and configuration
- Zero-downtime updates
- Centralized visibility with distributed data
- Complete audit trail and compliance

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Models](#deployment-models)
4. [Automated Onboarding](#automated-onboarding)
5. [Mobile App Distribution](#mobile-app-distribution)
6. [Central Management](#central-management)
7. [Monitoring & Operations](#monitoring--operations)
8. [Security & Compliance](#security--compliance)
9. [Disaster Recovery](#disaster-recovery)
10. [Scaling Examples](#scaling-examples)

---

## Architecture Overview

### System Components

```
┌────────────────────────────────────────────────────────────┐
│                  Enterprise Architecture                    │
└────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Central Instance                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Git Server (GitLab/GitHub Enterprise)         │ │
│  │  • Authentication (SSO: Azure AD, Okta, Google)      │ │
│  │  • Access Control (group/permission based)            │ │
│  │  • Audit Logging                                        │ │
│  │  • Backup & Restore                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         ArxOS Provisioning Engine                      │ │
│  │  • Property creation automation                        │ │
│  │  • Repository initialization                           │ │
│  │  • User/group assignment                               │ │
│  │  • Permission configuration                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Central Dashboard & Analytics                  │ │
│  │  • Multi-property monitoring                           │ │
│  │  • Activity dashboards                                  │ │
│  │  • Compliance reports                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────┬────────────────────────────────────────────┘
             │
             │ Git Clone/Pull
             │
    ┌────────┴────────┬───────────────┬──────────────┐
    │                 │               │              │
┌───▼──────────┐ ┌───▼─────────┐ ┌───▼──────┐ ┌───▼────────┐
│  Property 1  │ │  Property 2 │ │ Property │ │ Property N │
│              │ │             │ │    3     │ │            │
│ Local Repo   │ │ Local Repo  │ │ Local    │ │ Local Repo │
│              │ │            │ │ Repo     │ │            │
│              │ │            │ │          │ │            │
│ Mobile Apps  │ │ Mobile Apps│ │ Mobile   │ │ Mobile     │
│ (Trades)     │ │ (Trades)   │ │ Apps     │ │ Apps       │
└──────────────┘ └────────────┘ └──────────┘ └────────────┘
   (push)         (push)         (push)       (push)
```

### Core Principles

1. **Git-First Architecture**
   - Every property = One Git repository
   - All changes tracked in Git history
   - Native version control, no custom database

2. **Distributed Data**
   - Each property maintains local copy
   - No single point of failure
   - Works offline

3. **Centralized Control**
   - Single Git server manages all properties
   - Centralized access control
   - Unified monitoring

4. **Zero Vendor Lock-In**
   - All data in YAML files (human-readable)
   - Standard Git operations
   - Easily exportable

---

## Prerequisites

### For ArxOS Team

**Hardware Requirements:**
- Git server with sufficient storage for all properties
- Recommend: GitLab Enterprise server
- Estimated: 1GB per property (3,000 properties = 3TB)

**Software:**
- GitLab Enterprise (or GitHub Enterprise)
- SSO integration capability
- Monitoring tools (Prometheus/Grafana)
- Backup system

**Network:**
- HTTPS endpoint for central Git server
- Load balancing for high availability
- CDN for mobile app distribution (optional)

### For Enterprise Customer (e.g., CBRE)

**Requirements:**
- SSO provider (Azure AD, Okta, etc.)
- MDM solution for mobile deployment (optional)
- Network access to Git server
- Team for on-site support

**Staffing:**
- IT team for initial setup
- Facility managers for property-level operations
- Training leads for user education

---

## Deployment Models

### Model 1: Single-Tenant (Recommended for Enterprises)

**Best For:** Large organizations with internal IT team

```
┌────────────────────────────────────────┐
│       Customer (e.g., CBRE)           │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  GitLab Enterprise Instance      │ │
│  │  • Self-hosted or cloud          │ │
│  │  • URL: git.cbre.com             │ │
│  │  • Auth: CBRE SSO                │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  ArxOS Mobile Apps               │ │
│  │  • White-labeled for CBRE        │ │
│  │  • Deployed via MDM              │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Pros:**
- Full data control
- Custom branding
- Flexible pricing
- No vendor dependency

**Cons:**
- Customer manages infrastructure
- Requires IT resources

### Model 2: Multi-Tenant SaaS (Future)

**Best For:** Smaller organizations, managed service

```
┌────────────────────────────────────────┐
│       ArxOS Cloud Platform              │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Multi-Tenant Git Server         │ │
│  │  • Separate namespaces per org   │ │
│  │  • URL: {org}.arxos.io          │ │
│  │  • Auth: ArxOS SSO              │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Shared ArxOS Mobile Apps        │ │
│  │  • Configures per organization   │ │
│  │  • App Store distribution       │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

**Pros:**
- No infrastructure management
- Faster onboarding
- Lower upfront cost

**Cons:**
- Less customization
- Vendor dependency
- Higher ongoing cost

---

## Automated Onboarding

### Provisioning Workflow

```
Sales/Onboarding Initiated
  ↓
Property List Provided (CSV/JSON)
  ↓
Validated & Transformed
  ↓
Generate Provisioning Plan
  ↓
Batch Create Repositories
  ↓
Set Access Controls
  ↓
Generate Credentials & Assign Users
  ↓
Push Base Configuration
  ↓
Webhook: Repo Ready Notification
  ↓
Notify Customer
```

### Provisioning Script (Python)

```python
#!/usr/bin/env python3
"""
ArxOS Enterprise Provisioning Tool
Creates Git repositories for enterprise deployment
"""

import json
import gitlab
from typing import List, Dict

class ArxOSProvisioning:
    def __init__(self, gitlab_url: str, api_token: str, group_id: int):
        self.gitlab_url = gitlab_url
        self.api_token = api_token
        self.group_id = group_id
        self.gl = gitlab.Gitlab(gitlab_url, private_token=api_token)
        
    def create_property_repo(self, property_config: Dict) -> Dict:
        """
        Create a Git repository for a property
        
        Args:
            property_config: {
                "id": "001",
                "name": "Empire State Tower",
                "location": "Manhattan, NY",
                "manager_email": "manager@cbre.com",
                "region": "NYC",
                "tenant": "CBRE"
            }
        """
        repo_name = f"property-{property_config['id']}"
        
        # 1. Create repository via GitLab API
        repo_url = self._create_gitlab_repo(repo_name)
        
        # 2. Initialize with base files
        self._initialize_repo(repo_url, property_config)
        
        # 3. Set up access controls
        self._configure_access(repo_url, property_config)
        
        # 4. Create hooks for monitoring
        self._setup_webhooks(repo_url)
        
        return {
            "repo_url": repo_url,
            "repo_name": repo_name,
            "status": "ready"
        }
    
    def batch_provision(self, properties: List[Dict]) -> List[Dict]:
        """Provision multiple properties"""
        results = []
        
        for prop in properties:
            try:
                result = self.create_property_repo(prop)
                results.append({"property": prop['id'], "result": result})
            except Exception as e:
                results.append({"property": prop['id'], "error": str(e)})
        
        return results
    
    def _create_gitlab_repo(self, name: str) -> str:
        """Create repository via GitLab API"""
        project = self.gl.projects.create({
            'name': name,
            'namespace_id': self.group_id,
            'visibility': 'private',
            'initialize_with_readme': False
        })
        return project.http_url_to_repo
    
    def _initialize_repo(self, repo_url: str, config: Dict):
        """Initialize repo with base building.yaml"""
        import git
        import yaml
        
        repo = git.Repo.clone_from(repo_url, f"/tmp/{config['id']}", depth=1)
        
        building_data = {
            "building": {
                "id": config['id'],
                "name": config['name'],
                "tenant": config['tenant'],
                "location": config['location'],
                "manager": {
                    "email": config['manager_email']
                },
                "metadata": {
                    "created": "2024-01-15T00:00:00Z",
                    "status": "provisioned"
                }
            },
            "floors": [],
            "equipment": []
        }
        
        with open("building.yaml", 'w') as f:
            yaml.dump(building_data, f)
        
        repo.index.add(['building.yaml'])
        repo.index.commit(f"Initial property setup for {config['name']}")
        repo.remote().push()
    
    def _configure_access(self, repo_url: str, config: Dict):
        """Set up GitLab permissions"""
        # Implementation via GitLab API
        pass
    
    def _setup_webhooks(self, repo_url: str):
        """Configure webhooks for monitoring"""
        pass

# Example usage
if __name__ == "__main__":
    properties = [
        {
            "id": "001",
            "name": "Empire State Tower",
            "location": "Manhattan, NY",
            "manager_email": "jane@cbre.com",
            "region": "NYC",
            "tenant": "CBRE"
        },
        # ... more properties
    ]
    
    provisioner = ArxOSProvisioning(
        gitlab_url="https://git.cbre.com",
        api_token="gl-...",
        group_id=5
    )
    
    results = provisioner.batch_provision(properties)
    print(json.dumps(results, indent=2))
```

### Property Data Model

```yaml
# File: property-metadata.yaml

# Required fields for provisioning
property:
  id: string           # Unique identifier (e.g., "001")
  name: string         # Display name (e.g., "Empire State Tower")
  location: string     # Geographic location
  manager_email: string # Facility manager email
  tenant: string       # Organization name (e.g., "CBRE")

# Optional fields
  region: string       # Operational region
  coordinates:
    lat: float
    lon: float
  building_type: string # e.g., "Office", "Retail", "Industrial"
  sqft: integer        # Square footage

# Access control
  access:
    write:
      - "manager@cbre.com"
      - "technician@cbre.com"
    read:
      - "regional-director@cbre.com"
      - "executive@cbre.com"

# Git configuration
  git:
    repo_url: string
    branch: "main"
```

### Provisioning from CSV

```csv
# File: properties.csv
id,name,location,manager_email,tenant,region,building_type,sqft
001,Empire State Tower,Manhattan NY,manager1@cbre.com,CBRE,NYC,Office,2500000
002,Queens Plaza,Queens NY,manager2@cbre.com,CBRE,NYC,Office,1200000
003,LA Downtown Tower,Los Angeles CA,manager3@cbre.com,CBRE,LA,Office,1800000
```

```python
import csv
import yaml

def csv_to_properties(csv_file: str) -> List[Dict]:
    """Convert CSV to property configuration"""
    properties = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append({
                "id": row['id'],
                "name": row['name'],
                "location": row['location'],
                "manager_email": row['manager_email'],
                "tenant": row['tenant'],
                "region": row.get('region', 'Unknown'),
                "building_type": row.get('building_type', 'Office'),
                "sqft": int(row.get('sqft', 0))
            })
    
    return properties

# Usage
properties = csv_to_properties("properties.csv")
results = provisioner.batch_provision(properties)
```

---

## Mobile App Distribution

### Distribution Models

#### Option 1: MDM Deployment (Recommended for Enterprise)

**Advantages:**
- Centralized control
- Auto-configuration
- Silent updates
- Compliance enforcement

**Implementation:**

```bash
# Package ArxOS for MDM
arxos-mobile package \
  --platform ios \
  --tenant CBRE \
  --config tenant-config.yaml \
  --signing-cert "CBRE-Enterprise.cer" \
  --output arxos-cbre.ipa
```

**MDM Configuration:**
```xml
<?xml version="1.0"?>
<plist version="1.0">
  <dict>
    <key>PayloadIdentifier</key>
    <string>com.cbre.arxos.mobile</string>
    
    <key>PayloadDisplayName</key>
    <string>ArxOS for CBRE</string>
    
    <key>PayloadContent</key>
    <array>
      <dict>
        <key>InstallAction</key>
        <string>Install</string>
        
        <key>Configuration</key>
        <dict>
          <key>tenant</key>
          <string>CBRE</string>
          <key>git_server</key>
          <string>https://git.cbre.com</string>
        </dict>
      </dict>
    </array>
  </dict>
</plist>
```

---

## Central Management

### Dashboard Architecture

```rust
// ArxOS Enterprise Dashboard
// Real-time monitoring of all properties

pub struct EnterpriseDashboard {
    tenant: String,
    git_server: GitServer,
    analytics: AnalyticsEngine,
}

impl EnterpriseDashboard {
    // Get overview of all properties
    pub fn get_overview(&self) -> EnterpriseOverview {
        let stats = self.calculate_stats()?;
        
        EnterpriseOverview {
            total_properties: stats.total_properties,
            active_properties: stats.active_last_24h,
            total_commits: stats.total_commits,
            active_users: stats.active_users,
            top_active_properties: stats.top_10_properties,
            recent_issues: stats.issues_requiring_attention,
            activity_by_region: stats.activity_breakdown,
        }
    }
    
    // Property-specific analytics
    pub fn get_property_details(&self, property_id: &str) -> PropertyDetails {
        let repo = self.git_server.get_repo(property_id)?;
        
        PropertyDetails {
            id: property_id,
            name: repo.metadata.name,
            location: repo.metadata.location,
            manager: repo.metadata.manager,
            commit_count: repo.commit_count(),
            last_updated: repo.last_commit_time(),
            contributors: repo.contributors(),
            rooms: repo.count_rooms(),
            equipment: repo.count_equipment(),
            coverage: repo.calculate_coverage(),
            recent_commits: repo.recent_commits(10),
        }
    }
}
```

### Command-Line Dashboard

```bash
# Enterprise dashboard
arxos dashboard --tenant CBRE

# Output:
┌──────────────────────────────────────────────────────────┐
│  CBRE Enterprise Dashboard                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Overview:                                               │
│  • Total Properties:        3,247                       │
│  • Active (24h):           2,891 (89%)                 │
│  • Total Equipment:         847,392                     │
│  • Total Rooms:             412,846                    │
│                                                          │
│  Activity Today:                                         │
│  • Commits:                1,247                        │
│  • Equipment Added:        847                          │
│  • Equipment Updated:       3,421                       │
│  • Alerts:                 12                          │
│                                                          │
│  Top Active Properties:                                  │
│  1. Manhattan Tower-001    156 commits                 │
│  2. LA Downtown-003       134 commits                 │
│  3. Chicago Willis-004     121 commits                 │
└──────────────────────────────────────────────────────────┘
```

---

## Security & Compliance

### Authentication & Authorization

```
[User Login]
  ↓
┌─────────────────────────┐
│  SSO Provider           │
│  • Azure AD             │
│  • Okta                 │
│  • Google               │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  ArxOS Auth Proxy       │
└───────────┬─────────────┘
            ↓
    ┌───────┴───────┬───────┐
    ↓               ↓       ↓
[Users]       [Git]    [Mobile]
```

### Access Control

```rust
pub struct PropertyPermissions {
    property_id: String,
    readers: Vec<Group>,
    writers: Vec<Group>,
    admins: Vec<String>,
}

impl PropertyPermissions {
    fn check_write_access(&self, user: &User) -> bool {
        if self.writers.contains(&user.group) {
            return true;
        }
        if self.admins.contains(&user.email) {
            return true;
        }
        false
    }
}
```

---

## Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# Daily backup script

BACKUP_DIR="/backups/arxos-enterprise"
DATE=$(date +%Y%m%d)

# 1. Backup all repositories
gitlab-backup create --backup-path="$BACKUP_DIR/$DATE"

# 2. Compress
tar -czf "$BACKUP_DIR/$DATE.tar.gz" "$BACKUP_DIR/$DATE"

# 3. Upload to offsite
aws s3 cp "$BACKUP_DIR/$DATE.tar.gz" s3://cbre-arxos-backups/

# 4. Cleanup (keep 30 days)
find "$BACKUP_DIR" -type f -mtime +30 -delete
```

### RTO/RPO Targets

- **Recovery Time Objective (RTO):** < 2 hours
- **Recovery Point Objective (RPO):** < 1 hour
- **Data retention:** 7 years (compliance)

---

## Scaling Examples

### Example 1: CBRE (Large Enterprise)

**Scale:**
- 3,247 properties
- 15,000+ users
- 50,000+ equipment items

**Deployment:**
```bash
arxos-provisioning provision \
  --file cbre-properties.csv \
  --batch-size 500 \
  --parallel 10 \
  --tenant CBRE

# Created 3,247 repositories in 45 minutes
```

**Infrastructure:**
- 16 CPU, 128GB RAM
- 4TB SSD storage
- 10Gbps network

### Example 2: Regional Chain

**Scale:**
- 500 properties
- 2,000 users
- 15,000 equipment

**Deployment:**
```bash
arxos-provisioning provision \
  --file regional-properties.csv \
  --tenant REGIONAL-CHAIN

# Created 500 repositories in 15 minutes
```

**Infrastructure:**
- 8 CPU, 64GB RAM
- 500GB SSD

---

## Implementation Checklist

### Pre-Engagement
- [ ] Gather property list
- [ ] Confirm tenant details
- [ ] Identify SSO provider
- [ ] Assess infrastructure
- [ ] Define access controls

### Provisioning Phase
- [ ] Import property data
- [ ] Validate data
- [ ] Create repositories
- [ ] Configure permissions
- [ ] Set up webhooks
- [ ] Initialize data

### Mobile Deployment
- [ ] Package apps
- [ ] Configure for tenant
- [ ] Deploy via MDM
- [ ] Test devices
- [ ] Communicate to users

### Go-Live
- [ ] User training
- [ ] Pilot (10-20 properties)
- [ ] Gather feedback
- [ ] Fix issues
- [ ] Full rollout
- [ ] Monitor

---

**Document Version:** 1.0  
**Maintained By:** ArxOS Engineering Team  
**Contact:** enterprise@arxos.com  
**Last Updated:** January 2025

