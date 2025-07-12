# Monitoring and Alerting

## Overview

Comprehensive monitoring and alerting system for the Arxos platform, providing real-time visibility into system health, performance, and security.

## Monitoring Architecture

### Core Components
- **Metrics Collection**: System and application metrics
- **Log Aggregation**: Centralized log collection and analysis
- **Alerting Engine**: Real-time alert generation and delivery
- **Dashboard**: Real-time monitoring dashboards
- **Health Checks**: Service health monitoring

### Monitoring Stack
```json
{
  "metrics": {
    "collector": "Prometheus",
    "storage": "InfluxDB",
    "visualization": "Grafana"
  },
  "logging": {
    "collector": "Fluentd",
    "storage": "Elasticsearch",
    "visualization": "Kibana"
  },
  "alerting": {
    "engine": "AlertManager",
    "notifications": ["email", "slack", "webhook"]
  },
  "health_checks": {
    "endpoints": ["/health", "/ready", "/metrics"],
    "interval": 30,
    "timeout": 10
  }
}
```

## Metrics Collection

### System Metrics
```json
{
  "system": {
    "cpu": {
      "usage_percent": 45.2,
      "load_average": [1.2, 1.1, 0.9],
      "cores": 8
    },
    "memory": {
      "total_gb": 16.0,
      "used_gb": 8.5,
      "available_gb": 7.5,
      "usage_percent": 53.1
    },
    "disk": {
      "total_gb": 500.0,
      "used_gb": 250.0,
      "available_gb": 250.0,
      "usage_percent": 50.0
    },
    "network": {
      "bytes_sent": 1024000,
      "bytes_received": 2048000,
      "packets_sent": 1500,
      "packets_received": 3000
    }
  }
}
```

### Application Metrics
```json
{
  "application": {
    "requests": {
      "total": 15000,
      "per_second": 25.5,
      "successful": 14850,
      "failed": 150,
      "error_rate": 1.0
    },
    "response_time": {
      "average_ms": 125.5,
      "p95_ms": 250.0,
      "p99_ms": 500.0,
      "max_ms": 1000.0
    },
    "database": {
      "connections": 25,
      "queries_per_second": 100.0,
      "slow_queries": 5,
      "connection_errors": 0
    },
    "cache": {
      "hit_rate": 85.5,
      "miss_rate": 14.5,
      "evictions": 10,
      "memory_usage_gb": 2.5
    }
  }
}
```

### Business Metrics
```json
{
  "business": {
    "projects": {
      "total": 150,
      "active": 120,
      "completed": 25,
      "archived": 5
    },
    "symbols": {
      "total": 2500,
      "mechanical": 800,
      "electrical": 700,
      "security": 500,
      "network": 500
    },
    "validations": {
      "total": 5000,
      "passed": 4800,
      "failed": 150,
      "warnings": 50
    },
    "users": {
      "total": 500,
      "active": 450,
      "new_this_month": 25
    }
  }
}
```

## Logging Configuration

### Log Format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "arx_svg_parser",
  "component": "api",
  "endpoint": "/api/v1/symbols",
  "method": "GET",
  "user_id": "user_001",
  "request_id": "req_123456",
  "duration_ms": 125.5,
  "status_code": 200,
  "message": "Successfully retrieved 150 symbols",
  "metadata": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "query_params": {"system": "mechanical", "limit": 50}
  }
}
```

### Log Levels
```json
{
  "levels": {
    "DEBUG": {
      "level": 10,
      "description": "Detailed debugging information",
      "examples": ["SQL queries", "Function calls", "Variable values"]
    },
    "INFO": {
      "level": 20,
      "description": "General information about application flow",
      "examples": ["User login", "API requests", "File operations"]
    },
    "WARNING": {
      "level": 30,
      "description": "Warning messages for potentially problematic situations",
      "examples": ["Deprecated features", "Performance issues", "Resource usage"]
    },
    "ERROR": {
      "level": 40,
      "description": "Error messages for serious problems",
      "examples": ["API errors", "Database errors", "Validation failures"]
    },
    "CRITICAL": {
      "level": 50,
      "description": "Critical errors that may cause application failure",
      "examples": ["System crashes", "Database corruption", "Security breaches"]
    }
  }
}
```

### Log Aggregation
```json
{
  "aggregation": {
    "collectors": [
      {
        "name": "fluentd",
        "type": "log_collector",
        "config": {
          "input": {
            "type": "tail",
            "path": "/var/log/arxos/*.log",
            "format": "json"
          },
          "output": {
            "type": "elasticsearch",
            "host": "elasticsearch:9200",
            "index": "arxos-logs"
          }
        }
      }
    ],
    "storage": {
      "elasticsearch": {
        "hosts": ["elasticsearch:9200"],
        "index_pattern": "arxos-logs-*",
        "retention_days": 30
      }
    },
    "visualization": {
      "kibana": {
        "host": "kibana:5601",
        "dashboards": ["application-logs", "error-analysis", "user-activity"]
      }
    }
  }
}
```

## Alerting Configuration

### Alert Rules
```json
{
  "alerts": [
    {
      "name": "high_cpu_usage",
      "description": "CPU usage is above 80%",
      "condition": "cpu_usage > 80",
      "duration": "5m",
      "severity": "warning",
      "notifications": ["email", "slack"],
      "labels": {
        "service": "system",
        "component": "cpu"
      }
    },
    {
      "name": "high_error_rate",
      "description": "Error rate is above 5%",
      "condition": "error_rate > 5",
      "duration": "2m",
      "severity": "critical",
      "notifications": ["email", "slack", "pagerduty"],
      "labels": {
        "service": "application",
        "component": "api"
      }
    },
    {
      "name": "database_connection_errors",
      "description": "Database connection errors detected",
      "condition": "db_connection_errors > 0",
      "duration": "1m",
      "severity": "critical",
      "notifications": ["email", "slack", "pagerduty"],
      "labels": {
        "service": "database",
        "component": "connections"
      }
    },
    {
      "name": "slow_response_time",
      "description": "Average response time is above 500ms",
      "condition": "avg_response_time > 500",
      "duration": "5m",
      "severity": "warning",
      "notifications": ["email", "slack"],
      "labels": {
        "service": "application",
        "component": "performance"
      }
    }
  ]
}
```

### Notification Channels
```json
{
  "notifications": {
    "email": {
      "type": "smtp",
      "config": {
        "host": "smtp.gmail.com",
        "port": 587,
        "username": "alerts@arxos.com",
        "password": "encrypted_password",
        "recipients": ["admin@arxos.com", "ops@arxos.com"]
      }
    },
    "slack": {
      "type": "webhook",
      "config": {
        "url": "https://hooks.slack.com/services/...",
        "channel": "#alerts",
        "username": "Arxos Alerts"
      }
    },
    "pagerduty": {
      "type": "webhook",
      "config": {
        "url": "https://events.pagerduty.com/v2/enqueue",
        "service_key": "service_key_here"
      }
    },
    "webhook": {
      "type": "http",
      "config": {
        "url": "https://api.example.com/webhooks/alerts",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer token_here"
        }
      }
    }
  }
}
```

## Health Checks

### Service Health Checks
```json
{
  "health_checks": {
    "api": {
      "endpoint": "/health",
      "interval": 30,
      "timeout": 10,
      "expected_status": 200,
      "expected_response": {
        "status": "healthy",
        "timestamp": "regex:.*"
      }
    },
    "database": {
      "endpoint": "/health/database",
      "interval": 30,
      "timeout": 5,
      "expected_status": 200,
      "expected_response": {
        "status": "connected",
        "response_time_ms": "number"
      }
    },
    "symbol_library": {
      "endpoint": "/health/symbols",
      "interval": 60,
      "timeout": 10,
      "expected_status": 200,
      "expected_response": {
        "status": "loaded",
        "symbol_count": "number"
      }
    },
    "external_services": {
      "endpoint": "/health/external",
      "interval": 60,
      "timeout": 15,
      "expected_status": 200,
      "expected_response": {
        "status": "all_healthy",
        "services": "object"
      }
    }
  }
}
```

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "api": {
      "status": "healthy",
      "response_time_ms": 5.2,
      "last_check": "2024-01-15T10:29:30Z"
    },
    "database": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "last_check": "2024-01-15T10:29:30Z"
    },
    "symbol_library": {
      "status": "healthy",
      "symbol_count": 2500,
      "last_check": "2024-01-15T10:29:00Z"
    },
    "external_services": {
      "status": "healthy",
      "services": {
        "authentication": "healthy",
        "storage": "healthy",
        "analytics": "healthy"
      },
      "last_check": "2024-01-15T10:29:00Z"
    }
  },
  "system": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 53.1,
    "disk_usage_percent": 50.0,
    "uptime_seconds": 86400
  }
}
```

## Dashboard Configuration

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Arxos Platform Monitoring",
    "version": "1.0.0",
    "panels": [
      {
        "title": "System Overview",
        "type": "stat",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU Usage"
          },
          {
            "expr": "memory_usage_percent",
            "legendFormat": "Memory Usage"
          },
          {
            "expr": "disk_usage_percent",
            "legendFormat": "Disk Usage"
          }
        ]
      },
      {
        "title": "API Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx Errors"
          },
          {
            "expr": "rate(http_requests_total{status=~\"4..\"}[5m])",
            "legendFormat": "4xx Errors"
          }
        ]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(db_queries_total[5m])",
            "legendFormat": "Queries/sec"
          },
          {
            "expr": "histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ],
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    }
  }
}
```

## Performance Monitoring

### Application Performance
```json
{
  "performance": {
    "api": {
      "endpoints": {
        "/api/v1/symbols": {
          "requests_per_second": 25.5,
          "average_response_time_ms": 125.5,
          "p95_response_time_ms": 250.0,
          "error_rate_percent": 1.0
        },
        "/api/v1/projects": {
          "requests_per_second": 10.2,
          "average_response_time_ms": 200.0,
          "p95_response_time_ms": 400.0,
          "error_rate_percent": 0.5
        },
        "/api/v1/validation": {
          "requests_per_second": 5.1,
          "average_response_time_ms": 500.0,
          "p95_response_time_ms": 1000.0,
          "error_rate_percent": 2.0
        }
      }
    },
    "database": {
      "queries": {
        "select_symbols": {
          "calls_per_second": 50.0,
          "average_duration_ms": 10.5,
          "slow_queries_percent": 0.1
        },
        "insert_symbol": {
          "calls_per_second": 5.0,
          "average_duration_ms": 25.0,
          "slow_queries_percent": 0.5
        }
      }
    },
    "cache": {
      "hit_rate_percent": 85.5,
      "miss_rate_percent": 14.5,
      "evictions_per_second": 0.1,
      "memory_usage_gb": 2.5
    }
  }
}
```

### Resource Utilization
```json
{
  "resources": {
    "cpu": {
      "usage_percent": 45.2,
      "load_average": [1.2, 1.1, 0.9],
      "cores": 8,
      "temperature_celsius": 65.0
    },
    "memory": {
      "total_gb": 16.0,
      "used_gb": 8.5,
      "available_gb": 7.5,
      "usage_percent": 53.1,
      "swap_used_gb": 0.0
    },
    "disk": {
      "total_gb": 500.0,
      "used_gb": 250.0,
      "available_gb": 250.0,
      "usage_percent": 50.0,
      "io_operations_per_second": 100.0
    },
    "network": {
      "bytes_sent_per_second": 1024000,
      "bytes_received_per_second": 2048000,
      "packets_sent_per_second": 1500,
      "packets_received_per_second": 3000,
      "error_rate_percent": 0.01
    }
  }
}
```

## Security Monitoring

### Security Events
```json
{
  "security": {
    "authentication": {
      "login_attempts": {
        "total": 1000,
        "successful": 950,
        "failed": 50,
        "rate_per_hour": 25.0
      },
      "failed_logins": {
        "by_ip": {
          "192.168.1.100": 5,
          "10.0.0.50": 3
        },
        "by_user": {
          "unknown_user": 20,
          "test_user": 10
        }
      }
    },
    "authorization": {
      "access_denied": {
        "total": 25,
        "by_endpoint": {
          "/api/v1/admin": 15,
          "/api/v1/users": 10
        }
      },
      "permission_checks": {
        "total": 5000,
        "granted": 4950,
        "denied": 50
      }
    },
    "data_access": {
      "file_access": {
        "total": 10000,
        "read": 8000,
        "write": 1500,
        "delete": 500
      },
      "api_access": {
        "total": 50000,
        "get": 40000,
        "post": 8000,
        "put": 1500,
        "delete": 500
      }
    }
  }
}
```

### Threat Detection
```json
{
  "threats": {
    "suspicious_activity": [
      {
        "timestamp": "2024-01-15T10:30:00Z",
        "type": "brute_force_attack",
        "ip_address": "192.168.1.100",
        "attempts": 50,
        "severity": "high",
        "action": "blocked"
      },
      {
        "timestamp": "2024-01-15T10:25:00Z",
        "type": "unusual_access_pattern",
        "user_id": "user_001",
        "endpoints": ["/api/v1/admin", "/api/v1/users"],
        "severity": "medium",
        "action": "alerted"
      }
    ],
    "vulnerabilities": [
      {
        "timestamp": "2024-01-15T10:20:00Z",
        "type": "sql_injection_attempt",
        "ip_address": "10.0.0.50",
        "payload": "'; DROP TABLE users; --",
        "severity": "critical",
        "action": "blocked"
      }
    ]
  }
}
```

## Incident Response

### Incident Definition
```json
{
  "incident": {
    "id": "inc_001",
    "title": "High CPU Usage Alert",
    "description": "CPU usage has been above 80% for more than 5 minutes",
    "severity": "warning",
    "status": "investigating",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "assigned_to": "ops@arxos.com",
    "metrics": {
      "cpu_usage_percent": 85.2,
      "memory_usage_percent": 60.1,
      "response_time_ms": 300.0
    },
    "actions": [
      {
        "timestamp": "2024-01-15T10:30:00Z",
        "action": "alert_triggered",
        "description": "High CPU usage alert triggered"
      },
      {
        "timestamp": "2024-01-15T10:32:00Z",
        "action": "investigation_started",
        "description": "Ops team started investigation"
      }
    ]
  }
}
```

### Response Procedures
```json
{
  "response_procedures": {
    "high_cpu_usage": {
      "steps": [
        {
          "step": 1,
          "action": "Check system processes",
          "command": "top -p 1",
          "expected_result": "Identify high CPU processes"
        },
        {
          "step": 2,
          "action": "Check application logs",
          "command": "tail -f /var/log/arxos/app.log",
          "expected_result": "Identify application issues"
        },
        {
          "step": 3,
          "action": "Scale resources if needed",
          "command": "docker-compose scale arx-svg-parser=3",
          "expected_result": "Distribute load across instances"
        }
      ],
      "escalation": {
        "after_minutes": 15,
        "contact": "senior-ops@arxos.com"
      }
    },
    "database_errors": {
      "steps": [
        {
          "step": 1,
          "action": "Check database connectivity",
          "command": "curl -f http://localhost:8000/health/database",
          "expected_result": "Verify database status"
        },
        {
          "step": 2,
          "action": "Check database logs",
          "command": "tail -f /var/log/postgresql/postgresql.log",
          "expected_result": "Identify database issues"
        },
        {
          "step": 3,
          "action": "Restart database if needed",
          "command": "sudo systemctl restart postgresql",
          "expected_result": "Restore database service"
        }
      ],
      "escalation": {
        "after_minutes": 5,
        "contact": "dba@arxos.com"
      }
    }
  }
}
``` 